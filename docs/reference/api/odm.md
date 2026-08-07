# ODM modules

The ODM-specific extraction modules (stage 2 of the pipeline) and their shared
helpers. See [ODM pipeline steps](../odm-pipeline-steps.md) for the order they run
in, and [The ODM data dictionary](../../explanation/the-odm-data-dictionary.md) for
the source conventions they decode.

## `odm_linkmlgen.odm.make_odm_ss_classes`

Creates one Schemasheet per ODM class (table) from the parts sheet, named
`class_{table_name}.tsv`.

Two private module-level tables are worth knowing about: `headers`, the
column-to-LinkML mapping, and `_data_types_map`, the ODM data type to LinkML range
mapping — a new `dataType` in a new dictionary version needs adding to the latter.

::: odm_linkmlgen.odm.make_odm_ss_classes
    options:
      members:
        - extract_class
        - extract_all_classes

## `odm_linkmlgen.odm.make_odm_ss_enums_from_sets`

The enumerations whose permissible values live in the **sets** sheet — the `mmaSet`
enumerations.

::: odm_linkmlgen.odm.make_odm_ss_enums_from_sets
    options:
      members:
        - get_enum_names_from_sets
        - extract_sets_enums

## `odm_linkmlgen.odm.make_odm_ss_enums_from_parts`

The enumerations whose permissible values live in the **parts** sheet — everything
not handled by `extract_sets_enums`.

::: odm_linkmlgen.odm.make_odm_ss_enums_from_parts
    options:
      members:
        - get_enum_names_from_parts
        - extract_parts_enums

## `odm_linkmlgen.odm.make_odm_ss_container`

::: odm_linkmlgen.odm.make_odm_ss_container
    options:
      members:
        - extract_container_class

## `odm_linkmlgen.odm.make_odm_ss_prefixes`

::: odm_linkmlgen.odm.make_odm_ss_prefixes
    options:
      members:
        - get_prefixes_data
        - make_prefixes

## `odm_linkmlgen.odm.make_odm_ss_schema`

::: odm_linkmlgen.odm.make_odm_ss_schema
    options:
      members:
        - get_schema_data
        - make_schema

## `odm_linkmlgen.odm.odm_utils`

Helpers for working with the ODM parts sheet, plus the missingness post-processing
step.

`_odm_enum_name_exceptions` — private, but the table you edit when an enumeration
name does not follow the `partID` + `s` convention. The symptom of a missing entry
is a slot whose range fell back to `string`.

::: odm_linkmlgen.odm.odm_utils
    options:
      members:
        - ODM_PARTS_COLUMN_CLASS_TAG
        - odm_get_available_class_names
        - odm_get_fk_target_class
        - odm_get_header_rows
        - odm_keep_active_rows
        - odm_get_enum_name_from_part_id
        - set_range_of_slot
        - add_missingness_set
