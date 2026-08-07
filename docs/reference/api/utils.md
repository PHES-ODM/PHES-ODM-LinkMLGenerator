# Shared utilities

Dataset-agnostic helpers under `odm_linkmlgen/utils/`. This is everything the ODM
and NWSS pipelines genuinely have in common — see
[why the two pipelines are not shared](../../explanation/pipeline-design.md#why-the-two-pipelines-are-not-shared).

## `odm_linkmlgen.utils.general_utils`

DataFrame, file I/O, and logging helpers.

`extract_sheets` is stage 1 of both pipelines. Its `na_values` argument is the one
to reach for when a literal value such as `NA` or `None` is being read as missing
data — a real problem for ODM part IDs.

`EMPTY_PERMISSIBLE_VALUE` is the `<empty>` sentinel written where a permissible
value of `""` is meant, and replaced by `fix_schemasheets_generated_schema`. See
[post-processing workarounds](../../explanation/post-processing-workarounds.md).

::: odm_linkmlgen.utils.general_utils
    options:
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

## `odm_linkmlgen.utils.schemasheets_utils`

Creating Schemasheets files and turning them into a schema — stage 3 of both
pipelines.

Note that `make_linkml_schema_from_schemasheets` runs Schemasheets over **every**
`.tsv` in the directory it is given, not a known list of files, so a stale TSV will
be silently included.

::: odm_linkmlgen.utils.schemasheets_utils
    options:
      members:
        - save_schemasheet
        - add_schemasheets_header
        - make_container_schemasheet
        - make_linkml_schema_from_schemasheets
        - save_schema_definition
        - fix_schemasheets_generated_schema

## `odm_linkmlgen.utils.schema_utils`

Read-only helpers for inspecting a generated schema. Useful when writing tools that
consume the output.

These take a `SchemaView` as their **third** argument, not the `SchemaDefinition`
that `make_odm` returns — wrap it first. See
[Use the generator as a Python library](../../how-to/use-as-a-python-library.md#inspecting-a-generated-schema).

Prefer `get_ranges_of_slot` over reading `.range` directly: a slot that accepts a
missingness enumeration alongside its normal range is written as `any_of` and has
no `range` at all.

::: odm_linkmlgen.utils.schema_utils
    options:
      members:
        - get_slot_definition
        - get_ranges_of_slot
        - get_ranges_of_slot_defn
