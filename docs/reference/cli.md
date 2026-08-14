# Command-line interface

`pip install -e .` registers three commands. Every command also accepts `--help`.

## `odm-linkmlgen-odm`

Generates an ODM v2+ schema. Wraps `odm_linkmlgen.make_odm.make_odm`.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `--version` | str | Yes | The ODM version number, e.g. `2`, `3` |
| `--dictionary-file` | Path | Yes | The Excel data dictionary |
| `--output-dir` | Path | Yes | Where to write all output |

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

Writes `{output_dir}/linkml/odm_v{version}.yaml`, plus the intermediate
`dictionary/` and `schemasheets/` directories.

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
`odm_linkmlgen/data/odm_v1/schemasheets/`. No source Excel file is involved, so
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

Every dictionary option is optional. Each one you pass generates one independent
schema under its own subdirectory; passing none generates nothing.

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

!!! warning "These defaults are not what the top-level generators pass"

    The step CLIs exist for debugging, not as the pipeline's configuration
    surface. Two defaults differ from what `make_odm` and `make_nwss` use, and
    both change the output:

    - `--recognized-enums` is omitted by default, disabling the check that a
      derived ODM enumeration name actually exists.
    - `--single-table` defaults to *off*, but `make_nwss` always passes it.

### ODM steps

| Module | Options |
| --- | --- |
| `make_odm_ss_classes` | `--parts-file`, `--output-dir`, `--recognized-enums` (repeatable) |
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
