# Generate the ODM schemas

Everything needed to produce an ODM schema is on this page.
[Install the generator](install.md) first.

The dictionary the generator reads is the pair of **CSV dictionary tables** the
PHES-ODM project publishes — a parts file and a sets file. They are public, so
nothing has to be requested from anyone, and they are what the rest of this page
uses. The Excel data dictionary is still accepted; that is a
[short note at the end](#generate-from-the-excel-dictionary-instead).

**ODM v3 is the current version of the model** and is what you almost certainly
want. v2 is generated the same way from its own pair of files, and v1 is a
separate command with no dictionary at all.

## Get the dictionary tables

The v3 tables live in the
[`dictionary-tables/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/label/dictionary-tables)
of the PHES-ODM repository, on the `label` branch. Two of the files there are
the ones the generator needs:

| File | Holds |
| --- | --- |
| `ODM_parts_v3.0.0.csv` | The **parts** table — every table, column, enumeration, and permissible value in the model |
| `ODM_sets_v3.0.0.csv` | The **sets** table — the permissible values of most of the enumerations |

The other files in that directory (`ODM_countries.csv`, `ODM_translations.csv`,
and so on) are not read by the generator.

By convention they go in `odm_linkmlgen/data/odm_v3/` — the same place the Excel
dictionary would go, and `odm_v{n}/` for any other version. Every `.csv` and
`.xlsx` under `odm_linkmlgen/data/odm_v*/` is git-ignored, so your copies stay
local to your checkout and cannot be committed by accident:

```console
mkdir -p odm_linkmlgen/data/odm_v3
curl -L -o odm_linkmlgen/data/odm_v3/ODM_parts_v3.0.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/label/dictionary-tables/ODM_parts_v3.0.0.csv"
curl -L -o odm_linkmlgen/data/odm_v3/ODM_sets_v3.0.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/label/dictionary-tables/ODM_sets_v3.0.0.csv"
```

The location is only a convention — any path can be passed to `--parts-file` and
`--sets-file`, including the `dictionary/parts.csv` and `dictionary/sets.csv` a
previous run wrote.

## Generate the ODM v3 schema

```console
odm-linkmlgen-odm \
    --version 3 \
    --parts-file "odm_linkmlgen/data/odm_v3/ODM_parts_v3.0.0.csv" \
    --sets-file "odm_linkmlgen/data/odm_v3/ODM_sets_v3.0.0.csv" \
    --output-dir "gen/odm_v3"
```

The schema is written to `gen/odm_v3/linkml/odm_v3.yaml`, alongside the
intermediate `dictionary/` and `schemasheets/` directories described in the
[output layout reference](../reference/output-layout.md).

The two files are copied into `{output_dir}/dictionary/` as `parts.csv` and
`sets.csv`, and every step that reads them there applies the ODM dictionary's
own NA handling — the same handling the Excel path uses — so the run is
identical from there on.

`--version` is a bare version number (`2`, `3`, …). It is not just a label: it
determines the generated schema's name (`ODMv3`), id
(`https://onto.phes-odm.org/odm/v3`), and CURIE prefix (`odmv3`), so it must
match the dictionary tables you passed.

!!! warning "`--output-dir` must not be where the CSVs are read from"

    The first step clears `dictionary/`. So passing
    `--parts-file gen/odm_v3/dictionary/parts.csv` together with
    `--output-dir gen/odm_v3` deletes its own input before it can be read. Keep
    the inputs outside the output directory, as above, or write to a different
    `--output-dir`.

    Pass one form or the other, never both, and never only one half of the CSV
    pair — anything else logs an error and generates nothing.

## Generate the ODM v2 schema

Same command, with `--version 2` and the v2 tables. ODM v2 is superseded by v3;
generate it only if something you maintain still needs it.

The v2 tables are in the
[`archived V2.3 (PATCH)/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/v2.3.0/archived%20V2.3%20%28PATCH%29)
of the PHES-ODM repository, on the `v2.3.0` branch — `ODM_parts_v2.3.0.csv` and
`ODM_sets_v2.3.0.csv`. Earlier v2 releases have their own `Archived V2.x/`
directories on `main`, with the version in each file name.

```console
mkdir -p odm_linkmlgen/data/odm_v2
curl -L -o odm_linkmlgen/data/odm_v2/ODM_parts_v2.3.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/v2.3.0/archived%20V2.3%20(PATCH)/ODM_parts_v2.3.0.csv"
curl -L -o odm_linkmlgen/data/odm_v2/ODM_sets_v2.3.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/v2.3.0/archived%20V2.3%20(PATCH)/ODM_sets_v2.3.0.csv"

odm-linkmlgen-odm \
    --version 2 \
    --parts-file "odm_linkmlgen/data/odm_v2/ODM_parts_v2.3.0.csv" \
    --sets-file "odm_linkmlgen/data/odm_v2/ODM_sets_v2.3.0.csv" \
    --output-dir "gen/odm_v2"
```

The schema is written to `gen/odm_v2/linkml/odm_v2.yaml`.

## Check the ODM result

Errors in the source dictionary are logged and skipped rather than raised, so a
run that "succeeded" can still have produced a degraded schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --parts-file ... --sets-file ... \
    --output-dir "gen/odm_v3" 2>&1 | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

A clean run prints nothing.

If you are generating a version that has not been generated before, work through
[Extend the generator](extending.md#add-support-for-a-new-odm-version) as well.

## ODM v1

ODM v1 needs no dictionary at all — its Schemasheets are bundled with the
package, so this runs offline in a couple of seconds:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

## Generate from the Excel dictionary instead

The same schema can be generated from the official PHES-ODM Excel data
dictionary, by passing `--dictionary-file` in place of the `--parts-file` /
`--sets-file` pair. Everything downstream is the same: the workbook's parts and
sets sheets are extracted to `{output_dir}/dictionary/`, and the run continues
from there.

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The workbook is **not publicly available** and is not committed to this
repository. Contact [Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a copy.
By convention it goes in `odm_linkmlgen/data/odm_v{n}/` — the same directory as
the CSV tables — named `v{n} ODM dictionary.xlsx`, and is git-ignored there just
as they are.

!!! danger "Opening and resaving with an older Excel will corrupt the workbook"

    The dictionary relies on the `FILTER` and `XLOOKUP` functions, which older
    versions of Excel do not support. Opening the file in such a version and
    saving it silently destroys those formulas, and the damage is not
    recoverable from the saved file.

    Use a recent version of Excel. If you only need to *look* at the file, use a
    viewer that will not write to it. The published CSV tables above avoid this
    hazard entirely, which is one reason they are the recommended input.

## Related

- [Inside an ODM run](../explanation/odm-runs.md) — what the run left on disk,
  and how v1 and v2+ differ
- [The ODM data dictionary](../reference/data-dictionaries.md#the-odm-data-dictionary)
  — how the parts table encodes the data model
- [Roll out a dictionary update](dictionary-workflow.md) — what to do after the
  dictionary tables change
- [Use it from Python](python-api.md) — the same thing from Python, returning a
  `SchemaDefinition`
- [Troubleshooting](troubleshooting.md) — when the result is not what you
  expected
