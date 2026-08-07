# Module reference

Every module and public function in `odm_linkmlgen`. Each function's own
docstring is the authoritative description of its arguments and return value —
this page exists to tell you which module to look in.

For how these fit together, see [Architecture](architecture.md), and the
[ODM](odm-pipeline.md) and [NWSS](nwss-pipeline.md) pipeline pages.

Every module under `odm/` and `nwss/` is both an importable module and a
standalone CLI:

```console
python -m odm_linkmlgen.odm.<module> --help
python -m odm_linkmlgen.nwss.<module> --help
```

## Top-level generators

### `odm_linkmlgen.make_odm`

CLI and function for generating the ODM v2+ LinkML schema. Orchestrates every
processing step in sequence.

- `make_odm` — runs the full pipeline for one ODM version and returns the
  `SchemaDefinition`

Installed as the `odm-linkmlgen-odm` command.

### `odm_linkmlgen.make_odm_v1`

CLI for generating the ODM v1 schema from the Schemasheets files bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/`. No source Excel file is involved, so
this is only the final Schemasheets step.

Installed as the `odm-linkmlgen-odmv1` command.

### `odm_linkmlgen.make_nwss`

CLI and function for generating the NWSS LinkML schemas. Runs the full pipeline
once per dictionary type supplied.

- `make_nwss` — runs the full pipeline for every dictionary type that was given a
  file

Installed as the `odm-linkmlgen-nwss` command.

## ODM processing steps

### `odm_linkmlgen.odm.make_odm_ss_classes`

Creates one Schemasheet per ODM class (table) from the parts sheet, named
`class_{table_name}.tsv`.

- `extract_class` — builds and saves the Schemasheet for a single class, and
  returns its path and DataFrame
- `extract_all_classes` — builds and saves a Schemasheet for every class in the
  parts sheet

Module-level data worth knowing about: `headers` (the column-to-LinkML mapping)
and `_data_types_map` (ODM data type to LinkML range).

### `odm_linkmlgen.odm.make_odm_ss_enums_from_sets`

- `extract_sets_enums` — extracts the enumerations whose permissible values live
  in the sets sheet (the `mmaSet` enumerations) and returns their names

### `odm_linkmlgen.odm.make_odm_ss_enums_from_parts`

- `extract_parts_enums` — extracts the enumerations whose permissible values live
  in the parts sheet (everything not handled by `extract_sets_enums`) and returns
  their names

### `odm_linkmlgen.odm.make_odm_ss_container`

- `extract_container_class` — builds the top-level `tree_root` Container class
  Schemasheet, with one multivalued slot per ODM table

### `odm_linkmlgen.odm.make_odm_ss_prefixes`

- `get_prefixes_data` — returns the CURIE prefixes used by the schema for a given
  ODM version
- `make_prefixes` — writes the prefixes Schemasheet

### `odm_linkmlgen.odm.make_odm_ss_schema`

- `get_schema_data` — returns the schema-level metadata (name, id, description,
  default prefix) for a given ODM version
- `make_schema` — writes the schema metadata Schemasheet

## NWSS processing steps

### `odm_linkmlgen.nwss.make_nwss_ss_classes`

- `parse_table_df` — prepares one NWSS table's metadata rows for Schemasheets
  processing, resolving ranges and validation patterns
- `extract_all_classes` — saves a Schemasheet per NWSS table, or a single merged
  class when `single_table` is set

Module-level data worth knowing about: `_data_types_validation_info`, the regex
table that maps NWSS's free-text data type descriptions onto LinkML ranges and
validation patterns.

### `odm_linkmlgen.nwss.make_nwss_ss_enums`

- `extract_enums` — extracts every enumeration from a NWSS `Value Sets` sheet,
  one Schemasheet per enumeration, expanding detailed enumeration names

### `odm_linkmlgen.nwss.make_nwss_ss_container`

- `extract_container_class` — builds the top-level `tree_root` Container class
  Schemasheet for NWSS

### `odm_linkmlgen.nwss.make_nwss_ss_prefixes`

- `make_prefixes` — writes the prefixes Schemasheet for a given NWSS dictionary
  type

### `odm_linkmlgen.nwss.make_nwss_ss_schema`

- `make_schema` — writes the schema metadata Schemasheet from the values supplied
  by the caller

## Dataset-specific helpers

### `odm_linkmlgen.odm.odm_utils`

Helpers for working with the ODM parts sheet.

- `odm_get_available_class_names` — discovers all class/table names by inspecting
  the column headers (any header ending in `ODM_PARTS_COLUMN_CLASS_TAG`)
- `odm_get_fk_target_class` — for a foreign key part ID, returns the class that
  part ID is the primary key of, or `None` if the part ID is unknown or is not a
  key. Falls back to the optional `fKAliasID` column when the part ID is an alias
  for a primary key (v2 dictionaries have no `fKAliasID` column)
- `odm_get_header_rows` — filters the parts sheet to the rows that define a column
  in a given table (`pK`, `fK`, or `header`)
- `odm_keep_active_rows` — removes deprecated/inactive rows
- `odm_get_enum_name_from_part_id` — derives the enumeration name from a part ID,
  falling back to `string` for unrecognized enumerations
- `set_range_of_slot` — sets a slot usage's range, emitting `any_of` when more
  than one range is given
- `add_missingness_set` — post-processes the schema to add missingness
  enumerations to the slots that require them
- `ODM_PARTS_COLUMN_CLASS_TAG` — the column-header suffix (`Order`) that marks a
  parts sheet column as belonging to a class

### `odm_linkmlgen.nwss.nwss_utils`

Helpers for working with NWSS metadata and `Value Sets` sheets.

- `splitup_metadata_sheet` — splits a flat metadata sheet into per-table
  DataFrames, adding a `TABLE_NAME_COL` column to each
- `parse_enums_sheet` — extracts the enumeration definitions and the
  field-to-enumeration mapping from a `Value Sets` sheet
- `get_detailed_enums` — maps each shared enumeration name to its per-field
  variants (for example `vs_yne` → `vs_yne[stormwater_input]`)
- `DictionaryColumns` — the column names used by NWSS dictionary sheets
- `SlotToEnumColumns` — the column names of the slot-to-enumeration mapping
  DataFrame
- `TABLE_NAME_COL` — the name of the table column added by
  `splitup_metadata_sheet`
- `SINGLE_TABLE_NAME` — the class name used when all tables are merged into one

## Shared utilities

### `odm_linkmlgen.utils.general_utils`

DataFrame, file I/O, and logging helpers. Dataset-agnostic.

- `get_logger` — returns a configured logger, used by every module
- `extract_sheets` — extracts named sheets from an Excel file to CSV, with
  per-column NA handling
- `clear_dirs` — removes stale CSV/TSV/YAML files from output directories
- `save_data_frame` / `read_data_frame` — CSV/TSV I/O that picks the separator
  from the file extension
- `order_columns` — reorders DataFrame columns to a preferred order
- `strip_whitespace` — strips surrounding whitespace from every string in a
  DataFrame
- `expand_multi_rows` — expands semicolon-delimited values in a DataFrame into
  multiple rows
- `get_class_name_from_file_name` — extracts a class name from a data file name
- `choose_ignore_case_value` — normalizes a value's capitalization to match a
  list of allowable values
- `rename_items` — renames the items of a list using a mapping
- `select_func_kwargs` — filters a kwargs dictionary down to the arguments a
  function accepts
- `EMPTY_PERMISSIBLE_VALUE` — the `<empty>` sentinel used for a permissible value
  of `""`, replaced by `fix_schemasheets_generated_schema`

### `odm_linkmlgen.utils.schemasheets_utils`

Creating Schemasheets files and turning them into a schema.

- `save_schemasheet` — writes a DataFrame as a Schemasheets-formatted TSV,
  ordering the columns and adding the `>` header row
- `add_schemasheets_header` — inserts the `>`-prefixed Schemasheets header row
  into a DataFrame
- `make_container_schemasheet` — builds the top-level Container class TSV, shared
  by both pipelines
- `make_linkml_schema_from_schemasheets` — runs Schemasheets over all the TSV
  files in a directory, applies `fix_schemasheets_generated_schema`, and returns a
  `SchemaDefinition`
- `save_schema_definition` — serializes a `SchemaDefinition` to YAML
- `fix_schemasheets_generated_schema` — post-processes a Schemasheets-generated
  schema to correct known Schemasheets limitations: numeric bounds stored as
  strings, the empty-permissible-value sentinel, and comma-separated multi-range
  strings

### `odm_linkmlgen.utils.schema_utils`

Read-only helpers for inspecting a generated schema. Useful when writing tools
that consume the output.

- `get_slot_definition` — returns the fully induced slot definition for a
  class-and-slot pair, including any `slot_usage` overrides
- `get_ranges_of_slot` — extracts the range(s) of one or more slots in a class
- `get_ranges_of_slot_defn` — extracts the range(s) from slot definitions
  directly, handling both `range` and `any_of`
