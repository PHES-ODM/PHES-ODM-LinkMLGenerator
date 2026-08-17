# Python API

Signatures and docstrings for every public function in `odm_linkmlgen`,
**generated from the source** — so they cannot drift from the code. For worked
examples, see [Use it from Python](../how-to/python-api.md).

Private names (those beginning with `_`) are excluded. Several are nonetheless
worth knowing about, because they are the tables you edit when adapting the
generator to a new dictionary; they are listed in
[where to look for what](repository-layout.md#where-to-look-for-what).

**Every module under `odm/` and `nwss/` is both an importable module and a
standalone CLI:**

```console
python -m odm_linkmlgen.odm.<module> --help
python -m odm_linkmlgen.nwss.<module> --help
```

Each exposes a `typer` app whose `main` command forwards to the real function.
`main` is the CLI adapter, not the API — call the underlying function. See the
[CLI reference](cli.md) for the option names.

## Top-level generators

The three CLI entry points. Each orchestrates every processing step of its
pipeline in sequence — see [Pipeline steps](pipeline-steps.md).

| Module | Installed command | Function form |
| --- | --- | --- |
| `make_odm` | `odm-linkmlgen-odm` | Yes — returns a `SchemaDefinition` |
| `make_odm_v1` | `odm-linkmlgen-odmv1` | Yes — returns a `SchemaDefinition` |
| `make_nwss` | `odm-linkmlgen-nwss` | Yes — returns a `dict` of schemas |

### `odm_linkmlgen.make_odm`

Generates the ODM v2+ LinkML schema.

::: odm_linkmlgen.make_odm
    options:
      heading_level: 4
      members:
        - make_odm

### `odm_linkmlgen.make_odm_v1`

Generates the ODM v1 schema from the Schemasheets bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/`. No source Excel file is involved, so
this is only the final Schemasheets step.

::: odm_linkmlgen.make_odm_v1
    options:
      heading_level: 4
      members:
        - make_odm_v1

### `odm_linkmlgen.make_nwss`

Runs the full pipeline once per dictionary type supplied. Because it may
generate several schemas in one call, it returns them as a `dict` keyed by
dictionary type (`"reporting"`, `"public_concentration"`, …) rather than as a
single schema.

::: odm_linkmlgen.make_nwss
    options:
      heading_level: 4
      members:
        - make_nwss

## ODM modules

The ODM-specific extraction modules (stage 2 of the pipeline) and their shared
helpers. See
[The ODM data dictionary](data-dictionaries.md#the-odm-data-dictionary)
for the source conventions they decode.

### `odm_linkmlgen.odm.make_odm_ss_classes`

Creates one Schemasheet per ODM class (table) from the parts sheet, named
`class_{table_name}.tsv`.

One module-level table is worth knowing about: `headers`, the column-to-LinkML
mapping. The ODM data type to LinkML range mapping lives in `odm_utils`, in
`_data_types_map` — a new `dataType` in a new dictionary version needs adding
there.

::: odm_linkmlgen.odm.make_odm_ss_classes
    options:
      heading_level: 4
      members:
        - extract_class
        - extract_all_classes

### `odm_linkmlgen.odm.make_odm_ss_enums_from_sets`

The enumerations whose permissible values live in the **sets** sheet — the `mmaSet`
enumerations.

::: odm_linkmlgen.odm.make_odm_ss_enums_from_sets
    options:
      heading_level: 4
      members:
        - get_enum_names_from_sets
        - extract_sets_enums

### `odm_linkmlgen.odm.make_odm_ss_enums_from_parts`

The enumerations whose permissible values live in the **parts** sheet — everything
not handled by `extract_sets_enums`.

::: odm_linkmlgen.odm.make_odm_ss_enums_from_parts
    options:
      heading_level: 4
      members:
        - get_enum_names_from_parts
        - extract_parts_enums

### `odm_linkmlgen.odm.make_odm_ss_container`

::: odm_linkmlgen.odm.make_odm_ss_container
    options:
      heading_level: 4
      members:
        - extract_container_class

### `odm_linkmlgen.odm.make_odm_ss_prefixes`

::: odm_linkmlgen.odm.make_odm_ss_prefixes
    options:
      heading_level: 4
      members:
        - get_prefixes_data
        - make_prefixes

### `odm_linkmlgen.odm.make_odm_ss_schema`

::: odm_linkmlgen.odm.make_odm_ss_schema
    options:
      heading_level: 4
      members:
        - get_schema_data
        - make_schema

### `odm_linkmlgen.odm.odm_utils`

Helpers for working with the ODM parts sheet, plus the missingness post-processing
step.

`odm_get_data_type_of_row` resolves a parts row's LinkML range. The part's
`mmaSet` wins — that is a categorical part's enumeration name — and otherwise
the part's `dataType` is mapped through the private `_data_types_map`, which is
where a new dictionary version's new data type needs adding. Anything unmapped —
an unrecognized `dataType` and a `categorical` part with an empty `mmaSet` alike
— falls back to `string`, so a slot whose range reads `string` unexpectedly is
the symptom of one of those two.

::: odm_linkmlgen.odm.odm_utils
    options:
      heading_level: 4
      members:
        - ODM_PARTS_COLUMN_CLASS_TAG
        - odm_get_available_class_names
        - odm_get_fk_target_class
        - odm_get_header_rows
        - odm_keep_active_rows
        - odm_get_data_type_of_row
        - set_range_of_slot
        - add_missingness_set

## NWSS modules

The NWSS-specific extraction modules (stage 2 of the pipeline) and their shared
helpers. See
[The NWSS data dictionaries](data-dictionaries.md#the-nwss-data-dictionaries)
for the source layouts they decode.

### `odm_linkmlgen.nwss.make_nwss_ss_classes`

Builds the Schemasheet(s) for the NWSS tables, resolving ranges and validation
patterns from the dictionary's free-text `Data Type` column.

`_data_types_validation_info` — private, but the regex table that maps NWSS's
prose data type descriptions onto LinkML ranges and validation patterns. This is
the main thing to work on when a new dictionary version is published; its `@TODO`
comments mark patterns known to be too permissive.

::: odm_linkmlgen.nwss.make_nwss_ss_classes
    options:
      heading_level: 4
      members:
        - parse_table_df
        - extract_all_classes

### `odm_linkmlgen.nwss.make_nwss_ss_enums`

Extracts every enumeration from a NWSS `Value Sets` sheet, one Schemasheet per
enumeration, expanding
[detailed enumeration names](../explanation/data-dictionaries.md#detailed-enumeration-names).

::: odm_linkmlgen.nwss.make_nwss_ss_enums
    options:
      heading_level: 4
      members:
        - extract_enums

### `odm_linkmlgen.nwss.make_nwss_ss_container`

::: odm_linkmlgen.nwss.make_nwss_ss_container
    options:
      heading_level: 4
      members:
        - extract_container_class

### `odm_linkmlgen.nwss.make_nwss_ss_prefixes`

::: odm_linkmlgen.nwss.make_nwss_ss_prefixes
    options:
      heading_level: 4
      members:
        - make_prefixes

### `odm_linkmlgen.nwss.make_nwss_ss_schema`

Unlike the ODM equivalent, the metadata values are supplied by the caller
(`make_nwss`, from its module-level `SCHEMA_VALUES_TEMPLATE` dict)
rather than templated inside the module.

::: odm_linkmlgen.nwss.make_nwss_ss_schema
    options:
      heading_level: 4
      members:
        - make_schema

### `odm_linkmlgen.nwss.nwss_utils`

Helpers for working with NWSS metadata and `Value Sets` sheets.

`DictionaryColumns` is where every NWSS source column name lives — the one place
to update when a dictionary renames a column.

::: odm_linkmlgen.nwss.nwss_utils
    options:
      heading_level: 4
      members:
        - TABLE_NAME_COL
        - SINGLE_TABLE_NAME
        - CATEGORY_DATA_TYPE
        - DictionaryColumns
        - SlotToEnumColumns
        - SlotEnum
        - splitup_metadata_sheet
        - parse_enums_sheet
        - field_name_column
        - parse_value_set_reference
        - resolve_slot_enums
        - group_detailed_enums

## Shared utilities

Dataset-agnostic helpers under `odm_linkmlgen/utils/`. This is everything the ODM
and NWSS pipelines genuinely have in common — see
[why the two pipelines are not shared](../explanation/how-it-works.md#why-the-two-pipelines-are-not-shared).

### `odm_linkmlgen.utils.general_utils`

DataFrame, file I/O, and logging helpers.

`extract_sheets` is stage 1 of both pipelines. Its `na_values` argument is the one
to reach for when a literal value such as `NA` or `None` is being read as missing
data — a real problem for ODM part IDs.

`EMPTY_PERMISSIBLE_VALUE` is the `<empty>` sentinel written where a permissible
value of `""` is meant, and replaced by `fix_schemasheets_generated_schema`. See
[post-processing workarounds](../explanation/how-it-works.md#post-processing-workarounds).

::: odm_linkmlgen.utils.general_utils
    options:
      heading_level: 4
      members:
        - EMPTY_PERMISSIBLE_VALUE
        - get_logger
        - extract_sheets
        - clear_dirs
        - save_data_frame
        - read_data_frame
        - order_columns
        - strip_whitespace
        - expand_multi_rows
        - get_class_name_from_file_name
        - choose_ignore_case_value
        - rename_items
        - select_func_kwargs

### `odm_linkmlgen.utils.schemasheets_utils`

Creating Schemasheets files and turning them into a schema — stage 3 of both
pipelines.

Note that `make_linkml_schema_from_schemasheets` runs Schemasheets over **every**
`.tsv` in the directory it is given, not a known list of files, so a stale TSV will
be silently included.

::: odm_linkmlgen.utils.schemasheets_utils
    options:
      heading_level: 4
      members:
        - save_schemasheet
        - add_schemasheets_header
        - make_container_schemasheet
        - make_linkml_schema_from_schemasheets
        - save_schema_definition
        - fix_schemasheets_generated_schema

### `odm_linkmlgen.utils.schema_utils`

Read-only helpers for inspecting a generated schema. Useful when writing tools that
consume the output.

The per-slot lookups take a `SchemaView` as their **third** argument, not the
`SchemaDefinition` that `make_odm` returns — wrap it first. See
[Use it from Python](../how-to/python-api.md#inspecting-a-generated-schema).
`find_undefined_ranges` is the exception and accepts either, as its only argument.

Prefer `get_ranges_of_slot` over reading `.range` directly: a slot that accepts a
missingness enumeration alongside its normal range is written as `any_of` and has
no `range` at all.

`find_undefined_ranges` answers a question LinkML will not: whether every range in
the schema names something the schema actually defines. Loading a schema does not
resolve its ranges, so a slot pointing at an enumeration that was never generated
loads without complaint and fails only in whatever consumes it. Both `make_odm`
and `make_nwss` run this after generating a schema and log an error per offending
slot.

::: odm_linkmlgen.utils.schema_utils
    options:
      heading_level: 4
      members:
        - get_slot_definition
        - get_ranges_of_slot
        - get_ranges_of_slot_defn
        - find_undefined_ranges
