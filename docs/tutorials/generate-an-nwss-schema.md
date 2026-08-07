# Generate an NWSS schema

In the [first tutorial](generate-your-first-schema.md) you generated the ODM v1
schema, which skips straight to the last stage. This time you will run the
**whole** pipeline: from an Excel workbook, through two stages of intermediate
files, to a LinkML schema — stopping at each stage to look at what it produced.

You will use a CDC NWSS dictionary, because unlike the ODM dictionary the NWSS
ones are published publicly and you can download one right now.

This tutorial assumes you have already installed the package.

## Step 1 — Download a dictionary

Go to the CDC's
[Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html)
page and find the **Data Dictionaries** box. Download the **reporting**
dictionary — an `.xlsx` file.

Put it somewhere convenient. By convention the project keeps dictionaries in
`odm_linkmlgen/data/nwss/`, which is git-ignored so your copy will not be
committed:

```console
mkdir -p odm_linkmlgen/data/nwss
mv ~/Downloads/*.xlsx odm_linkmlgen/data/nwss/reporting.xlsx
```

Before going further, open the workbook and take a look at two sheets:

- **`Metadata`** — one row per field, with its data type, description, and
  whether it is required. Scroll down and notice that several tables are stacked
  one after another in this single flat sheet, with no column saying which table
  a row belongs to.
- **`Value Sets`** — the enumerations. Notice they run *side by side* across the
  sheet in pairs of columns rather than being stacked vertically.

Neither layout is anything LinkML understands. Making sense of them is the work
the pipeline does, and
[The NWSS data dictionaries](../explanation/the-nwss-data-dictionaries.md)
explains how.

## Step 2 — Generate the schema

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "odm_linkmlgen/data/nwss/reporting.xlsx"
```

The final schema lands at
`gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml`.

!!! note "About errors in the log"

    Watch the log for `ERROR` lines. They are expected here and are not
    failures: the published dictionaries contain defects, and the generator's
    convention is to log a bad row and skip it rather than abort a whole run
    over one cell. A single bad row should not cost you the other two thousand
    good ones.

    One defect in the published reporting dictionary is worth fixing before you
    use its schema in earnest — see
    [Prepare the NWSS data dictionaries](../how-to/prepare-the-nwss-dictionaries.md).

## Step 3 — Walk through the three stages

Now look at what the run left behind:

```console
find gen/nwss -type d
```

```text
gen/nwss/nwss_reporting/dictionary/     # Stage 1 output
gen/nwss/nwss_reporting/schemasheets/   # Stage 2 output
gen/nwss/nwss_reporting/linkml/         # Stage 3 output
```

Those three directories *are* the pipeline. Take them in order.

### Stage 1 — Excel becomes CSV

```console
ls gen/nwss/nwss_reporting/dictionary/
```

```text
enums.csv    metadata.csv
```

Two sheets, saved verbatim as CSV. Nothing has been interpreted yet; this stage
exists so that no later step ever has to open an Excel file, and so that you can
re-run a later step in a second instead of re-parsing the workbook each time.

Open `metadata.csv` and find a row where the `Data Type` cell is empty. That row
is a table boundary, and its `Field Name` cell holds the table name — that is
how the flat sheet gets split back into tables.

### Stage 2 — CSV becomes Schemasheets TSV

```console
ls gen/nwss/nwss_reporting/schemasheets/
```

You will see a `classes_nwss.tsv`, a `container.tsv`, a `prefixes.tsv`, a
`schema.tsv`, and one `enum_*.tsv` per enumeration. This is where all the
NWSS-specific knowledge lives, and where nearly every bug lives too.

Look at the class file:

```console
head -3 gen/nwss/nwss_reporting/schemasheets/classes_nwss.tsv
```

The `>` row maps the columns onto LinkML: `slot`, `required`, `description`,
`range`, `pattern`. Now find a row whose `range` is an enumeration name
beginning `vs_`, and one whose `pattern` is a regular expression. Both were
derived from the prose in the dictionary's `Data Type` column — NWSS describes
types in English rather than with a controlled vocabulary, so the generator
matches that prose against a table of regexes. That is
[step 4 of the NWSS pipeline](../reference/nwss-pipeline-steps.md).

Now list the enumerations:

```console
ls gen/nwss/nwss_reporting/schemasheets/ | grep vs_yne | head
```

Rather than one shared `vs_yne` (yes/no/empty) enumeration, there is a separate
one per field that uses it — `vs_yne[stormwater_input]`, `vs_yne[ext_blank]`,
and so on. This is deliberate, and the reasoning is in
[The NWSS data dictionaries](../explanation/the-nwss-data-dictionaries.md#detailed-enumeration-names).

### Stage 3 — TSV becomes LinkML

```console
less gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml
```

Schemasheets read *every* `.tsv` in the directory and merged them into this one
file. Note that there is a single class, `nwss`, holding every field from every
table in the dictionary — the NWSS generator deliberately merges them rather
than producing a class per table.

## Step 4 — Change something and re-run one step

The point of keeping the intermediate files is that you can re-run one stage
without redoing the others. Every step of the pipeline is its own CLI:

```console
python -m odm_linkmlgen.nwss.make_nwss_ss_classes --help
```

Rebuild only the class TSVs, from the CSVs already in `dictionary/`:

```console
python -m odm_linkmlgen.nwss.make_nwss_ss_classes \
    --metadata-file "gen/nwss/nwss_reporting/dictionary/metadata.csv" \
    --enums-file "gen/nwss/nwss_reporting/dictionary/enums.csv" \
    --output-dir "gen/nwss/nwss_reporting/schemasheets" \
    --single-table \
    --detailed-enum-names vs_yne \
    --detailed-enum-names vs_yn
```

The last three options are there because a step's CLI defaults are *not* the
same as the values `make_nwss` passes it. `--single-table` defaults to off, so
without it you would get one class per table instead of the merged `nwss` class
you saw in stage 3. Whenever you re-run a step by hand, check what the top-level
generator passed it — the
[NWSS pipeline steps reference](../reference/nwss-pipeline-steps.md) lists them.

That runs in a moment rather than reprocessing the workbook. It is the loop you
will spend most of your time in when adapting the generator to a new dictionary
— see [Re-run a single pipeline step](../how-to/run-a-single-pipeline-step.md)
and [Debug a generated schema](../how-to/debug-a-generated-schema.md).

## What you learned

- Both pipelines have the **same three stages**: extract Excel to CSV, transform
  CSV into Schemasheets TSVs, run Schemasheets to get one YAML.
- The intermediate files are kept on purpose. When a schema is wrong, they tell
  you *which stage* went wrong, and stage 2 is nearly always the answer.
- **Every step is independently runnable**, as a function and as a CLI. That is
  a design constraint of the project, not an accident.
- Bad rows in a source dictionary are logged and skipped, not raised.

## Next

- [How the pipeline is designed](../explanation/pipeline-design.md) — why three
  stages, and why the ODM and NWSS pipelines share almost no code.
- [Generate an ODM schema](../how-to/generate-an-odm-schema.md) — the same
  thing for ODM v2+, once you have obtained the dictionary.
