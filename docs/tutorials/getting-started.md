# Getting started

Install the generator, produce a complete LinkML schema for **ODM v3**, and look
at what it contains.

ODM v3 is the current version of the model, and it is the right place to start
for a second reason: it runs the whole three-stage pipeline and leaves every
stage's output on disk, so one run shows you the entire machine.

You will need:

- **Python 3.10 or newer.** Check with `python3 --version`.
- **The ODM v3 Excel data dictionary.** It is not public and is not in this
  repository; step 2 explains how to get it.

## 1. Install the package

Clone the repository and install it into a virtual environment:

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

The last line installs the package in editable mode and registers three
commands:

| Command | Generates |
| --- | --- |
| `odm-linkmlgen-odm` | An ODM v2+ schema — what this tutorial uses |
| `odm-linkmlgen-odmv1` | The legacy ODM v1 schema |
| `odm-linkmlgen-nwss` | One schema per NWSS dictionary type supplied |

Confirm the first one is on your path:

```console
odm-linkmlgen-odm --help
```

You should see a usage message listing `--version`, `--dictionary-file`, and
`--output-dir`. If instead you get `command not found`, the virtual environment
is probably not active — re-run `source .env/bin/activate`. For other
installation problems, see
[Troubleshooting](../how-to/troubleshooting.md#installation-problems).

To also get `pytest`, `pytest-cov`, and `ruff`, install `requirements-dev.txt`
instead — see [Contributing](../how-to/contributing.md).

## 2. Get the data dictionary

Everything from ODM v2 onwards is generated from the official PHES-ODM Excel
data dictionary. It is **not publicly available** — contact
[Mathew Thomson](mailto:matthomson@ohri.ca) for a copy.

!!! danger "Opening and resaving with an older Excel will corrupt the workbook"

    The dictionary relies on the `FILTER` and `XLOOKUP` functions, which older
    versions of Excel do not support. Opening the file in such a version and
    saving it silently destroys those formulas, and the damage is not
    recoverable from the saved file. Use a recent version of Excel, or a viewer
    that will not write to the file.

By convention the file goes in `odm_linkmlgen/data/odm_v3/`, named
`v3 ODM dictionary.xlsx`:

```console
mkdir -p odm_linkmlgen/data/odm_v3
cp "~/v3 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v3/
```

That directory is git-ignored, so your copy cannot be committed by accident. The
convention is only a convention — you can pass any path to `--dictionary-file`.

## 3. Generate the schema

Run the generator, telling it which version it is reading and where to put its
output:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

It takes on the order of fifteen seconds and produces several thousand `INFO`
lines. Almost all of them come from Schemasheets and LinkML themselves and are
noise — the thousands of `Mismatch between slot_name_mapping key ...` lines and
the pandas `DtypeWarning` about mixed types are both normal. The line that
matters is near the end:

```text
INFO ... schemasheets_utils.py:84: LinkML schema saved to 'gen/odm_v3/linkml/odm_v3.yaml'
```

Every module in this project logs the files it reads and writes at `INFO`, which
is what makes a failed run diagnosable.

`--version` is not just a label. It sets the generated schema's name (`ODMv3`),
its id (`https://onto.phes-odm.org/odm/v3`), its CURIE prefix (`odmv3`), and the
output file name, so it has to match the dictionary you passed.

### Check the run before trusting the result

A defect in the source dictionary is logged and skipped rather than raised, so a
run that "succeeded" can still have produced a degraded schema. Keep the log and
scan it:

```console
odm-linkmlgen-odm --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3" 2>&1 | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

A clean run prints nothing. Anything it does print is described in
[Troubleshooting](../how-to/troubleshooting.md#a-generated-schema-is-wrong).

## 4. Look at what was produced

List the output directory:

```console
find gen/odm_v3 -type d
```

```text
gen/odm_v3/dictionary/     # Stage 1 output
gen/odm_v3/schemasheets/   # Stage 2 output
gen/odm_v3/linkml/         # Stage 3 output
```

Those three directories *are* the pipeline: Excel becomes CSV, CSV becomes
Schemasheets TSV, and Schemasheets TSV becomes LinkML. Take them in order. The
full inventory is in the
[output layout reference](../reference/output-layout.md#odm-v2).

### Stage 1 — the dictionary, as CSV

```console
ls gen/odm_v3/dictionary/
```

```text
parts.csv    sets.csv
```

Two sheets of the workbook, saved verbatim. Nothing has been interpreted yet.
This stage exists so that no later step ever has to open an Excel file, and so
that you can [re-run a later step](../how-to/python-api.md#re-run-a-single-step)
in a second instead of re-parsing the workbook each time.

`parts.csv` is the data model: one row per part, and — after the descriptive
columns — a group of three columns per ODM table (`samples`, `samplesRequired`,
`samplesOrder`, then the same triple for every other table). A part belongs to a
table when its cell in that table's first column is filled in, and the value
there (`pK`, `fK`, `header`) says what role it plays. That is how one flat sheet
encodes twenty-six tables. `sets.csv` is the enumerations: one row per
membership, `setID` naming the enumeration and `partID` the permissible value.

### Stage 2 — Schemasheets

```console
ls gen/odm_v3/schemasheets/
```

Thirty-one files: one `class_*.tsv` per ODM table — `class_samples.tsv`,
`class_sites.tsv`, and so on — plus `enums_sets.tsv`, `enums_parts.tsv`,
`container.tsv`, `prefixes.tsv`, and `schema.tsv`. Note the asymmetry: one file
per class, but only one file per enumeration *source sheet*, each holding every
enumeration from it.

This is where all the ODM-specific knowledge lives. Look at one:

```console
head -3 gen/odm_v3/schemasheets/class_samples.tsv
```

The **first** row is an ordinary column header, named after whatever the source
dictionary called things. The row beginning with `>` is what makes the file a
Schemasheet: it maps each column onto an element of the LinkML metamodel. Here
`partID` becomes a `slot`, `dataType` becomes its `range`, and `partDesc`
becomes its `description`. Trailing columns mapped to `ignore` — `partType`,
`mmaSet`, `headerType`, `order`, `minLength`, `maxLength` — are carried along
for readability, having already done their work upstream. See
[How it works](../explanation/how-it-works.md#schemasheets) for the full story.

The third row is the first real slot, `sampleID`, and it shows two of the
translations the generator does: its `pattern` of `^.{0,30}$` was built from the
part's `minLength` and `maxLength`, because LinkML has no string-length
constraint, and its `identifier` cell is `True` because the parts sheet marked
it `pK`. Further down the file, `protocolID` has a `range` of `protocols` — a
foreign key resolved to the class it points at — and `purpose` has a `range` of
`purposeSet`, a categorical resolved to an enumeration name.
[Inside an ODM run](../explanation/odm-runs.md) goes through the rest.

### Stage 3 — the schema

```console
less gen/odm_v3/linkml/odm_v3.yaml
```

Schemasheets read *every* `.tsv` in that directory and merged them into this one
file — around 19,700 lines for v3. It opens with schema-level metadata —
`name: ODMv3`, an `id`, `prefixes`, and a `default_range` — and then three
sections worth finding:

- **`enums:`** — 180 named sets of permissible values.
- **`slots:`** — 294 columns. Most of the interesting detail is not here but
  under each class's `slot_usage:`, because the same slot name can appear in
  several tables with different constraints.
- **`classes:`** — one entry per ODM table, plus a `Container` class marked
  `tree_root: true`. The tree root is the entry point to a data file: it holds
  one `multivalued`, `inlined_as_list` slot per table, so an ODM data file is a
  set of named tables, each holding a list of rows. Jump to it with:

    ```console
    grep -n -B12 "tree_root" gen/odm_v3/linkml/odm_v3.yaml
    ```

One thing in the file came from no TSV at all:

```console
grep -A3 "any_of" gen/odm_v3/linkml/odm_v3.yaml | head -8
```

A slot written as `any_of: [string, genMissingnessSet]` had a plain `string`
range in stage 2. The second range was added afterwards, straight onto the
schema object, because the parts sheet records it in a `missingnessSet` column
that no Schemasheets column can express.

## 5. Do something with the schema

The schema is now an ordinary LinkML artefact, and every LinkML tool will accept
it. If you have `linkml` installed — you do, it came in with `requirements.txt`
— try converting it to JSON Schema:

```console
gen-json-schema gen/odm_v3/linkml/odm_v3.yaml > gen/odm_v3/odm_v3.schema.json
```

Or validate a data file against it:

```console
linkml-validate --schema gen/odm_v3/linkml/odm_v3.yaml your_data.yaml
```

That is the point of the project: it does not validate or convert anything
itself. It produces one schema, and the LinkML ecosystem does the rest.

## What you now know

- The generator's job is to turn a data dictionary into **one LinkML YAML file**,
  and then get out of the way — validation, conversion, and documentation are
  all done by other LinkML tools.
- It gets there in **three stages**, each leaving its output in `--output-dir`:
  the Excel sheets as CSV, then Schemasheets TSVs, then the schema.
- The middle stage is where the work happens. **Schemasheets TSVs**, whose `>`
  header rows map spreadsheet columns onto the LinkML metamodel, are what turns
  a dictionary's own vocabulary into LinkML's.
- Dictionary defects are **logged, not raised**, so scanning the log for `ERROR`
  is part of the run rather than an optional extra.

## Next

- [Inside an ODM run](../explanation/odm-runs.md) — the same run, in more
  detail, and how the legacy v1 pipeline differs
- [Generate the ODM schemas](../how-to/generate-odm-schemas.md) — the commands
  on their own, for v1, v2, and v3
- [Generate the NWSS schemas](../how-to/generate-nwss-schemas.md) — from a CDC
  dictionary you can download right now, walked through in
  [Inside an NWSS run](../explanation/nwss-runs.md)
- [Use it from Python](../how-to/python-api.md) — the same thing from Python,
  returning a `SchemaDefinition`
