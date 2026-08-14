# Inside an NWSS run

The instructions for actually producing the schemas — obtaining the
dictionaries, the manual fixes the published files need, and the commands — are
in [Generate the NWSS schemas](../how-to/generate-nwss-schemas.md). This page
covers what a run leaves behind and why the output looks the way it does.

## What the output looks like

Two NWSS-specific behaviours will surprise you if you are not expecting them:

- **One class, not one per table.** `make_nwss` always merges every table in the
  metadata sheet into a single class named `nwss`.
- **Per-field enumerations.** `vs_yne` and `vs_yn` are expanded into one
  enumeration per field that uses them — `vs_yne[stormwater_input]`, and so on.

Both are deliberate; the reasoning is in
[Why the dictionaries are hard to read](data-dictionaries.md#two-nwss-behaviours-that-will-surprise-you).

## Watch the three stages

Unlike ODM v1, a NWSS run exercises the whole pipeline, and it leaves each
stage's output on disk. This is the fastest way to see how the generator
actually works:

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
[step 4 of the NWSS pipeline](../reference/pipeline-steps.md#nwss-4-extract-the-classes).

### Stage 3 — TSV becomes LinkML

```console
less gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml
```

Schemasheets reads *every* `.tsv` in the directory and merges them into this one
file.

## Related

- [Generate the NWSS schemas](../how-to/generate-nwss-schemas.md) — the
  dictionaries, the manual fixes, and the commands
- [NWSS pipeline steps](../reference/pipeline-steps.md#nwss-pipeline-steps)
- [The NWSS data dictionaries](../reference/data-dictionaries.md#the-nwss-data-dictionaries)
- [Extending the generator](../how-to/extending.md#add-support-for-a-new-nwss-dictionary-type)
