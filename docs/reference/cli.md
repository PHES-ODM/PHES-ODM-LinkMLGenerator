# Command-line interface

`pip install -e .` registers three commands. Every command also accepts `--help`.

## `odm-linkmlgen-odm`

Generates an ODM v2+ schema. Wraps `odm_linkmlgen.make_odm.make_odm`.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `--version` | str | Yes | The ODM version number, e.g. `3`, `2` |
| `--output-dir` | Path | Yes | Where to write all output |
| `--parts-file` | Path | See below | The parts table, as CSV |
| `--sets-file` | Path | See below | The sets table, as CSV |
| `--dictionary-file` | Path | See below | The Excel data dictionary |

The dictionary is given in **exactly one** of two forms: both `--parts-file` and
`--sets-file`, or `--dictionary-file`. Giving both forms, or neither, or only one
half of the CSV pair, logs an error and generates nothing.

The CSV form takes the two dictionary tables directly, and is the usual one: the
PHES-ODM project publishes the dictionary as CSV, and this is also what you want
when re-running against the `dictionary/` CSVs of a previous run.

```console
odm-linkmlgen-odm \
    --version 3 \
    --parts-file "odm_linkmlgen/data/odm_v3/ODM_parts_v3.0.0.csv" \
    --sets-file "odm_linkmlgen/data/odm_v3/ODM_sets_v3.0.0.csv" \
    --output-dir "gen/odm_v3"
```

!!! warning "Do not point the CSV form at the run's own output directory"

    Step 1 clears `dictionary/` before the files are read, so
    `--parts-file gen/odm_v3/dictionary/parts.csv` with
    `--output-dir gen/odm_v3` deletes its own input. Write to a different
    `--output-dir`, or keep the inputs outside it as above.

The Excel form takes the workbook that both sheets live in:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

Writes `{output_dir}/linkml/odm_v{version}.yaml`, plus the intermediate
`dictionary/` and `schemasheets/` directories. Both forms write
`dictionary/parts.csv` and `dictionary/sets.csv` — the CSV form copies them
rather than extracting them — so every later step has the same input either
way.

`--version` is not merely a label. It determines:

| Derived value | Template |
| --- | --- |
| Schema name | `ODMv{version}` |
| Schema id | `https://onto.phes-odm.org/odm/v{version}` |
| Description | `Data model for the Public Health Environmental Surveillance Open Data Model, version {version}` |
| CURIE prefix | `odmv{version}` → `https://onto.phes-odm.org/odm/v{version}/` |
| Output file name | `odm_v{version}.yaml` |

## `odm-linkmlgen-odmv1`

Generates the ODM v1 schema from the Schemasheets bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/`. No data dictionary is involved, so
only the final Schemasheets step runs.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `--output-dir` | Path | Yes | Where to write the schema |

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

Writes `{output_dir}/linkml/odm_v1.yaml` and nothing else — the bundled
Schemasheets are read in place and are not copied into `--output-dir`.

## `odm-linkmlgen-nwss`

Generates one schema per dictionary type supplied. Wraps
`odm_linkmlgen.make_nwss.make_nwss`.

| Option | Type | Required | Metadata sheet read |
| --- | --- | --- | --- |
| `--output-dir` | Path | Yes | — |
| `--reporting` | Path | No | `Metadata` |
| `--public-concentration` | Path | No | `Metadata` |
| `--public-metric` | Path | No | `Metadata` |
| `--restricted-raw` | Path | No | `Wastewater Metadata` |
| `--restricted-analytics` | Path | No | `Analytics Data Dictionary` |
| `--single-table` / `--no-single-table` | bool | No (default on) | — |

Every dictionary option is optional. Each one you pass generates one independent
schema under its own subdirectory; passing none generates nothing.

`--single-table`, on by default, merges every table in the metadata sheet into a
single class named `nwss`. Pass `--no-single-table` to get one class per table
instead.

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "path/to/reporting.xlsx" \
    --public-metric "path/to/public_metric.xlsx"
```

Writes `{output_dir}/nwss_{dictionary_type}/linkml/nwss_{dictionary_type}.yaml`
per type. Derived values per type:

| Derived value | Template |
| --- | --- |
| Schema name | `NWSS_{dictionary_type}` |
| Schema id | `https://onto.phes-odm.org/nwss/{dictionary_type}` |
| Description | `National Wastewater Surveillance System (NWSS-{dictionary_type})` |
| CURIE prefix | `nwss_{dictionary_type}` → `https://onto.phes-odm.org/nwss/{dictionary_type}/` |

The enumerations always come from a sheet named `Value Sets`, regardless of type.

## Per-step module CLIs

Every extraction module is also a standalone CLI, for re-running one step against
already-extracted CSVs:

```console
python -m odm_linkmlgen.odm.<module> --help
python -m odm_linkmlgen.nwss.<module> --help
```

!!! warning "One default is not what the top-level generator passes"

    The step CLIs exist for debugging, not as the pipeline's configuration
    surface. `--detailed-enum-names` defaults to *empty* on
    `make_nwss_ss_classes`, but `make_nwss` always passes `vs_yne` and `vs_yn`,
    which changes the output: without them the shared enumerations are used
    rather than the per-field (detailed) copies.

### ODM steps

| Module | Options |
| --- | --- |
| `make_odm_ss_classes` | `--parts-file`, `--output-dir` |
| `make_odm_ss_enums_from_sets` | `--sets-file`, `--parts-file`, `--output-file` |
| `make_odm_ss_enums_from_parts` | `--parts-file`, `--output-file` |
| `make_odm_ss_container` | `--parts-file`, `--output-file` |
| `make_odm_ss_prefixes` | `--output-file`, `--version` |
| `make_odm_ss_schema` | `--output-file`, `--version` |

### NWSS steps

| Module | Options |
| --- | --- |
| `make_nwss_ss_classes` | `--metadata-file`, `--enums-file`, `--output-dir`, `--single-table` / `--no-single-table`, `--detailed-enum-names` (repeatable) |
| `make_nwss_ss_enums` | `--metadata-file`, `--valuesets-file`, `--output-dir`, `--detailed-enum-names` (repeatable, required) |
| `make_nwss_ss_container` | `--metadata-file`, `--output-file`, `--single-table` / `--no-single-table` |
| `make_nwss_ss_prefixes` | `--output-file`, `--dictionary-type` |
| `make_nwss_ss_schema` | `--output-file`, `--dictionary-type` |

Note that `make_nwss_ss_classes` takes `--enums-file` while
`make_nwss_ss_enums` takes `--valuesets-file` for the same file.

Repeatable options are passed once per value:

```console
--detailed-enum-names vs_yne --detailed-enum-names vs_yn
```

## Related

- [Re-run a single step](../how-to/python-api.md#re-run-a-single-step)
- [Pipeline steps](pipeline-steps.md)
- [Python API](api.md)
