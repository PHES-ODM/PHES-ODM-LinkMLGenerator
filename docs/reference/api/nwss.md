# NWSS modules

The NWSS-specific extraction modules (stage 2 of the pipeline) and their shared
helpers. See [NWSS pipeline steps](../nwss-pipeline-steps.md) for the order they run
in, and
[The NWSS data dictionaries](../../explanation/the-nwss-data-dictionaries.md) for
the source layouts they decode.

## `odm_linkmlgen.nwss.make_nwss_ss_classes`

Builds the Schemasheet(s) for the NWSS tables, resolving ranges and validation
patterns from the dictionary's free-text `Data Type` column.

`_data_types_validation_info` — private, but the regex table that maps NWSS's
prose data type descriptions onto LinkML ranges and validation patterns. This is
the main thing to work on when a new dictionary version is published; its `@TODO`
comments mark patterns known to be too permissive.

::: odm_linkmlgen.nwss.make_nwss_ss_classes
    options:
      members:
        - parse_table_df
        - extract_all_classes

## `odm_linkmlgen.nwss.make_nwss_ss_enums`

Extracts every enumeration from a NWSS `Value Sets` sheet, one Schemasheet per
enumeration, expanding
[detailed enumeration names](../../explanation/the-nwss-data-dictionaries.md#detailed-enumeration-names).

::: odm_linkmlgen.nwss.make_nwss_ss_enums
    options:
      members:
        - extract_enums

## `odm_linkmlgen.nwss.make_nwss_ss_container`

::: odm_linkmlgen.nwss.make_nwss_ss_container
    options:
      members:
        - extract_container_class

## `odm_linkmlgen.nwss.make_nwss_ss_prefixes`

::: odm_linkmlgen.nwss.make_nwss_ss_prefixes
    options:
      members:
        - make_prefixes

## `odm_linkmlgen.nwss.make_nwss_ss_schema`

Unlike the ODM equivalent, the metadata values are supplied by the caller
(`make_nwss`) rather than templated inside the module.

::: odm_linkmlgen.nwss.make_nwss_ss_schema
    options:
      members:
        - make_schema

## `odm_linkmlgen.nwss.nwss_utils`

Helpers for working with NWSS metadata and `Value Sets` sheets.

`DictionaryColumns` is where every NWSS source column name lives — the one place
to update when a dictionary renames a column.

::: odm_linkmlgen.nwss.nwss_utils
    options:
      members:
        - TABLE_NAME_COL
        - SINGLE_TABLE_NAME
        - DictionaryColumns
        - SlotToEnumColumns
        - splitup_metadata_sheet
        - parse_enums_sheet
        - get_detailed_enums
