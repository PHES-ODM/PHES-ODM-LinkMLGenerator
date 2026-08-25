# Inside an ODM run

The instructions for actually producing the schemas — obtaining the dictionary,
where to put it, and the commands for v1, v2, and v3 — are in
[Generate the ODM schemas](../how-to/generate-odm-schemas.md). This page covers
how an ODM run differs by version, and the one ODM-specific failure mode worth
knowing about in advance.

## v1 and v2+ are different pipelines

They share a name and nothing else:

| | ODM v1 | ODM v2+ |
| --- | --- | --- |
| Command | `odm-linkmlgen-odmv1` | `odm-linkmlgen-odm` |
| Source | Schemasheets TSVs bundled in the package | An Excel data dictionary you supply |
| Stages run | Stage 3 only | All three |
| Output | `linkml/odm_v1.yaml` and nothing else | `dictionary/`, `schemasheets/`, and `linkml/` |

ODM v1's TSVs are written and maintained by hand, in
`odm_linkmlgen/data/odm_v1/schemasheets/`. They are read in place and never
copied into `--output-dir`. So a change to the v1 schema is an edit to those
TSVs, not to any extraction code — nothing in `odm_linkmlgen/odm/` runs for v1
at all.

For v2 and above, the parts sheet of the Excel dictionary drives everything; how
it encodes the data model is described in
[The source data dictionaries](../reference/data-dictionaries.md#the-odm-data-dictionary).
The full v2+ output layout, including the asymmetry in how enumeration TSVs are
grouped, is in the
[output layout reference](../reference/output-layout.md#odm-v2).

## Watch the three stages

A v2+ run exercises the whole pipeline, and it leaves each stage's output on
disk. This is the fastest way to see how the generator actually works — v1 is no
use for it, since it starts at stage 3. Take v3 as the example:

```console
find gen/odm_v3 -type d
```

```text
gen/odm_v3/dictionary/     # Stage 1 output
gen/odm_v3/schemasheets/   # Stage 2 output
gen/odm_v3/linkml/         # Stage 3 output
```

Those three directories *are* the pipeline. Take them in order.

### Stage 1 — Excel becomes CSV

```console
ls gen/odm_v3/dictionary/
```

```text
parts.csv    sets.csv
```

Two sheets, saved verbatim as CSV. Nothing has been interpreted yet; this stage
exists so that no later step ever has to open an Excel file, and so that you can
[re-run a later step](../how-to/python-api.md#re-run-a-single-step) in a second
instead of re-parsing the workbook each time.

`parts.csv` is the data model. One row per part, and — after the descriptive
columns — a group of three columns per ODM table: `samples`, `samplesRequired`,
`samplesOrder`, then the same triple for every other table. A part belongs to a
table when its cell in that table's first column is filled in, and the value
there (`pK`, `fK`, `header`) says what role it plays. That is how one flat sheet
encodes twenty-six tables.

`sets.csv` is the enumerations: one row per membership, with `setID` naming the
enumeration and `partID` the permissible value in it.

Search `parts.csv` for a `partID` of `NA` or `null`. Both are there, as literal
text — they are real ODM parts, and reading them as missing values is exactly
what [step 2's `na_values`](../reference/pipeline-steps.md#odm-2-extract-or-copy-the-dictionary-sheets-to-csv)
prevents.

### Stage 2 — CSV becomes Schemasheets TSV

```console
ls gen/odm_v3/schemasheets/
```

You will see one `class_*.tsv` per ODM table — `class_samples.tsv`,
`class_sites.tsv`, and so on — plus `enums_sets.tsv`, `enums_parts.tsv`,
`container.tsv`, `prefixes.tsv`, and `schema.tsv`. Note the asymmetry: one file
per class, but only one file per enumeration *source sheet*, each holding every
enumeration from it.

This is where all the ODM-specific knowledge lives. Look at a class file:

```console
head -3 gen/odm_v3/schemasheets/class_samples.tsv
```

The `>` row maps the columns onto LinkML: `class`, `slot`, `title`,
`identifier`, `required`, `range`, `description`, `pattern`. Several trailing
columns map to `ignore` — `partType`, `mmaSet`, `headerType`, `order`,
`minLength`, `maxLength` are carried along for readability, having already done
their work in
[step 5](../reference/pipeline-steps.md#odm-5-extract-one-schemasheet-per-class).
Four things in that file are worth finding:

- `protocolID` has a `range` of `protocols` — a foreign key resolved to the
  class it points at, not to a data type.
- `purpose` has a `range` of `purposeSet` — a categorical resolved to an
  enumeration name, read from the part's `mmaSet` column. The `mmaSet` column is
  carried through to the TSV as well, so you can see where the range came from.
- `sampleID` has a `pattern` of `^.{0,30}$`, built from the part's `minLength`
  and `maxLength`, because LinkML has no string-length constraint.
- The final row has an empty `slot` cell. It carries the table's own title and
  description rather than a slot's.

### Stage 3 — TSV becomes LinkML

```console
less gen/odm_v3/linkml/odm_v3.yaml
```

Schemasheets reads *every* `.tsv` in the directory and merges them into this one
file — roughly twenty thousand lines for v3.

One thing in it came from no TSV at all:

```console
grep -A3 "any_of" gen/odm_v3/linkml/odm_v3.yaml | head -8
```

A slot written as `any_of: [string, genMissingnessSet]` had a plain `string`
range in stage 2 (just `string`). The second range (`genMissingnessSet`) was
added afterwards, straight onto the `SchemaDefinition`, by [step
10](../reference/pipeline-steps.md#odm-10-add-the-missingness-sets) — the parts
sheet records it in a `missingnessSet` column that no Schemasheets column can
express.

## Enumeration names come from the dictionary

The ODM-specific thing to know before your first v2+ run: a categorical slot's
enumeration name is read from the part's `mmaSet` column in the parts sheet, and
the dictionary is the only authority on it. The generator does not derive, guess,
or patch names.

The consequence is that a part the dictionary marks `categorical` but leaves
without an `mmaSet` cannot be resolved, and the run does not stop for it. The
slot's range falls back to `string`, so the schema still loads — which is why the
[check step](../how-to/generate-odm-schemas.md#check-the-odm-result) matters, and
why an unexpected `string` range is worth chasing back to the dictionary.

## Related

- [Generate the ODM schemas](../how-to/generate-odm-schemas.md) — the dictionary
  and the commands
- [Add support for a new ODM version](../how-to/extending.md#add-support-for-a-new-odm-version)
- [Use it from Python](../how-to/python-api.md) — the same thing from Python,
  returning a `SchemaDefinition`
- [ODM pipeline steps](../reference/pipeline-steps.md#odm-pipeline-steps) — what
  each of the eleven steps does
- [The ODM data dictionary](../reference/data-dictionaries.md#the-odm-data-dictionary)
  — how the parts sheet encodes the data model
