# NWSS pipeline steps

The eight steps `odm-linkmlgen-nwss` (`odm_linkmlgen.make_nwss.make_nwss`) runs
**per dictionary type supplied**, in order, to turn a CDC NWSS Excel data
dictionary into a LinkML schema. Each type gets its own independent schema under
its own subdirectory.

Every step is also its own CLI — see
[Re-run a single pipeline step](../how-to/run-a-single-pipeline-step.md).

## What `make_nwss` passes down

These values are fixed by `make_nwss` rather than being configurable, and they
differ from the step CLIs' defaults:

| Value | Set to |
| --- | --- |
| `single_table` | `True` — always merges every table into one class named `nwss` |
| `detailed_enum_names` | `["vs_yne", "vs_yn"]` |
| Value Sets sheet name | `Value Sets`, for every dictionary type |
| Metadata sheet name | Varies by type (see below) |

| Dictionary type | CLI option | Metadata sheet name | Publicly available |
| --- | --- | --- | --- |
| `reporting` | `--reporting` | `Metadata` | Yes |
| `public_concentration` | `--public-concentration` | `Metadata` | Yes |
| `public_metric` | `--public-metric` | `Metadata` | Yes |
| `restricted_raw` | `--restricted-raw` | `Wastewater Metadata` | No |
| `restricted_analytics` | `--restricted-analytics` | `Analytics Data Dictionary` | No |

The dictionary type also determines the schema's name, id, description, and
prefix — see the [CLI reference](cli.md#odm-linkmlgen-nwss).

## Summary

| # | Module / function | Output |
| --- | --- | --- |
| 1 | `utils.general_utils.clear_dirs` | — |
| 2 | `utils.general_utils.extract_sheets` | `dictionary/metadata.csv`, `dictionary/enums.csv` |
| 3 | `nwss.make_nwss_ss_enums.extract_enums` | `schemasheets/enum_{enum_name}.tsv` |
| 4 | `nwss.make_nwss_ss_classes.extract_all_classes` | `schemasheets/classes_{table_name}.tsv` |
| 5 | `nwss.make_nwss_ss_container.extract_container_class` | `schemasheets/container.tsv` |
| 6 | `nwss.make_nwss_ss_prefixes.make_prefixes` | `schemasheets/prefixes.tsv` |
| 7 | `nwss.make_nwss_ss_schema.make_schema` | `schemasheets/schema.tsv` |
| 8 | `utils.schemasheets_utils.make_linkml_schema_from_schemasheets` | `linkml/nwss_{dictionary_type}.yaml` |

There is **no NWSS equivalent of the ODM missingness post-processing step**, so
the pipeline is eight steps rather than eleven.

## 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from this dictionary type's
`dictionary/`, `schemasheets/`, and `linkml/` directories, so a stale file from a
previous run cannot leak into the new schema. Step 8 consumes every `.tsv` in the
directory, not a known list.

## 2. Extract the Excel sheets to CSV

`utils.general_utils.extract_sheets`

Saves the metadata sheet as `dictionary/metadata.csv` and the `Value Sets` sheet as
`dictionary/enums.csv`.

The **source** sheet names depend on the dictionary type, per the table above; the
**output** names do not. That is what keeps every later step dictionary-type
agnostic.

Unlike the ODM pipeline, only a truly empty cell is treated as missing, in every
column (`default_na_values=[""]`).

## 3. Extract the enumerations

`nwss.make_nwss_ss_enums.extract_enums` → `schemasheets/enum_{enum_name}.tsv`

Parses the `Value Sets` sheet into one Schemasheet per enumeration, expanding the
[detailed enumeration names](../explanation/the-nwss-data-dictionaries.md#detailed-enumeration-names)
— so `vs_yne` becomes `enum_vs_yne[stormwater_input].tsv` and one file per other
field that uses it, and the undifferentiated original is dropped.

This step is **skipped when the dictionary has no `Value Sets` sheet**, in which
case the schema is generated without any enumerations at all.

## 4. Extract the classes

`nwss.make_nwss_ss_classes.extract_all_classes` → `schemasheets/classes_{table_name}.tsv`

Splits the metadata sheet into tables, then for each table `parse_table_df` builds
the Schemasheets columns:

- **`slot`** from `Field Name` (or `variable name`).
- **`required`** — true when `Submission Requirement` reads `required`.
- **`description`** from `Description`.
- **`range`** and **`pattern`** from `Data Type`, via
  `_get_range_and_validation_info`. This is the substantive part of the step and
  works in three tiers:

    1. A `Data Type` of `category` means the range is an enumeration. The
       enumeration name comes from the `Field` → `Value Set Name` mapping in the
       `Value Sets` sheet, falling back to the row's own `Value Set` column. A
       categorical field with no enumeration anywhere logs an error and leaves the
       range unresolved.
    2. Otherwise the `Data Type` is matched against the regex table
       `_data_types_validation_info`, which maps NWSS's free-text data type
       descriptions onto a LinkML range plus a validation `pattern`. This is how
       types such as `date`, `time`, `time zone`, `ZIP code`, `NPDES permit
       number`, `EPA Registry ID`, and `jurisdiction id` acquire their regexes.
    3. Failing that, a `Data Type` containing `#` characters is converted into a
       regex by replacing each `#` with `[0-9]`. Anything else is copied through as
       the range unchanged.

With `single_table=True` — which `make_nwss` always sets — every table is
concatenated into a single class named `nwss`, producing one `classes_nwss.tsv`.

Because NWSS data types are prose rather than a controlled vocabulary, **this step
is the most likely place to need attention when a new dictionary version is
published.** The `@TODO` comments in `_data_types_validation_info` mark patterns
that are known to be too permissive.

## 5. Extract the Container class

`nwss.make_nwss_ss_container.extract_container_class` → `schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one multivalued
inlined slot per table. With `single_table=True` that is a single `nwss` slot.

## 6. Write the prefixes Schemasheet

`nwss.make_nwss_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines one CURIE prefix: `nwss_{dictionary_type}` →
`https://onto.phes-odm.org/nwss/{dictionary_type}/`.

## 7. Write the schema metadata Schemasheet

`nwss.make_nwss_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata for this dictionary type: name, id, description,
and default prefix.

Unlike the ODM equivalent, **the values are passed in by `make_nwss`** (as
`default_schema_values`) rather than being built inside the module. `make_schema`
takes a `data_values` dict that overrides its own defaults.

## 8. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets` →
`linkml/nwss_{dictionary_type}.yaml`

Runs Schemasheets over every `.tsv` in `schemasheets/`, applies
`fix_schemasheets_generated_schema` (see
[post-processing workarounds](../explanation/post-processing-workarounds.md)), and
writes the YAML.

## Related

- [The NWSS data dictionaries](../explanation/the-nwss-data-dictionaries.md) — the
  source layouts steps 3 and 4 are decoding
- [Prepare the NWSS data dictionaries](../how-to/prepare-the-nwss-dictionaries.md)
  — the manual Excel fixes the published files need
- [Output layout](output-layout.md)
- [Python API: NWSS modules](api/nwss.md)
