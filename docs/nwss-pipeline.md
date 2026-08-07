# The NWSS pipeline

This page describes how `odm-linkmlgen-nwss` (the
[`make_nwss`](../odm_linkmlgen/make_nwss.py) function) turns the CDC NWSS Excel
data dictionaries into LinkML schemas. Read [Architecture](architecture.md) first
for the concepts and vocabulary used here.

NWSS is published as five separate data dictionaries. `make_nwss` runs the whole
pipeline once per dictionary you supply, producing one independent LinkML schema
each, under its own subdirectory of `--output-dir`:

| Dictionary type | CLI option | Metadata sheet name | Publicly available |
| --- | --- | --- | --- |
| `reporting` | `--reporting` | `Metadata` | Yes |
| `public_concentration` | `--public-concentration` | `Metadata` | Yes |
| `public_metric` | `--public-metric` | `Metadata` | Yes |
| `restricted_raw` | `--restricted-raw` | `Wastewater Metadata` | No |
| `restricted_analytics` | `--restricted-analytics` | `Analytics Data Dictionary` | No |

The enumerations always come from a sheet named `Value Sets`. The dictionary type
also determines the generated schema's name, id, description, and prefix — for
example `nwss_reporting` and `https://onto.phes-odm.org/nwss/reporting`.

## Preparing the NWSS data dictionaries

Download the three public dictionaries from the
[Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html)
page, under "Data Dictionaries". The two restricted dictionaries are not publicly
available. NWSS dictionary files are git-ignored, so nothing is bundled with the
repository — put your copies anywhere and point the CLI at them (by convention,
`odm_linkmlgen/data/nwss/`).

Several dictionaries need manual edits in Excel before they will process
correctly. These are defects in the published files, not in the generator:

- **`restricted_analytics` has no `Value Sets` sheet.** Copy the `Value Sets`
  sheet from the restricted *raw* dictionary into the restricted *analytics*
  workbook. Even after doing this some value sets are still missing, and the
  categorical fields `pcr_gene_target_agg`, `pcr_target_below_lod`,
  `pcr_target_units`, and `quality_flag` have no enumeration definition at all.
  Each of those logs an error and produces a slot with an unresolved range.
- **`restricted_raw` misnames a value set.** In the `Value Sets` sheet, rename
  `other_norm_units` to `other_norm_unit` so it matches the field that uses it.
- **`reporting` misnames a value set.** In the `Value Sets` sheet, change
  `ntc_amplify` from `vs_yne` to `vs_yn`.
- **`public_metric` has invalid permissible values.** In
  `vs_reporting_jurisdiction`, `Chicago, IL` should be `Chicago` and
  `Houston, TX` should be `Houston`. Individual states should also be removed
  from the permissible values. Left as published, sample data fails validation
  against the generated schema.

A modified copy of the restricted analytics dictionary is kept alongside the
original in `odm_linkmlgen/data/nwss/` (suffixed `-MODIFIED`) as a record of
these edits, if you have access to those files.

An outstanding limitation, independent of the source files: validation
information in the `Value Set` column of the metadata sheet is not yet used.

## How the NWSS dictionaries are laid out

**The metadata sheet is a flat list of every field in every table**, with the
tables one after another. There is no column identifying which table a row
belongs to. Instead, after fully blank rows are dropped, each new table starts at
a row with an empty `Data Type` cell, and that row's `Field Name` cell holds the
table name. All rows up to the next such boundary row belong to that table.
`nwss_utils.splitup_metadata_sheet` implements this, adding a `_table` column
(`nwss_utils.TABLE_NAME_COL`) to each table it returns. A sheet with no boundary
row is treated as one table named `nwss` (`nwss_utils.SINGLE_TABLE_NAME`).

The columns the generator reads are listed in `nwss_utils.DictionaryColumns`:
`Field Name`, `Data Type`, `Value Set`, `Field`, `Value Set Name`, `Description`,
and `Submission Requirement`. Some dictionaries use `variable name` instead of
`Field Name`; both are handled.

**The `Value Sets` sheet holds enumerations side by side rather than stacked.**
Each enumeration occupies a pair of adjacent columns: the left column's header is
the enumeration name and its first cell reads `Value Set`, and the column to its
right has `Description` in that first cell. `nwss_utils.parse_enums_sheet` finds
enumerations by scanning every adjacent column pair for that signature. The same
sheet also carries a `Field` → `Value Set Name` mapping, which is what tells the
generator which enumeration each categorical field uses.

A permissible value written as `[empty]` in the source is a genuinely empty
value, and is converted to the `<empty>` sentinel described in
[Post-processing workarounds](architecture.md#post-processing-workarounds).

## Two NWSS-specific behaviours

**Single table.** `make_nwss` always sets `single_table=True`, which concatenates
every table in the metadata sheet into one class named `nwss` rather than
generating a class per table. The per-table path exists and is reachable through
the individual step functions and their CLIs (`--no-single-table`), but the
top-level generator does not use it.

**Detailed enumeration names.** `make_nwss` passes
`detailed_enum_names=["vs_yne", "vs_yn"]`. These two enumerations (yes/no and
yes/no/either) are used by many different fields, and their permissible values
need per-field descriptions. So instead of one shared `vs_yne` enumeration, a
separate copy is generated for every field that uses it, named
`vs_yne[<field_name>]` — for example `vs_yne[stormwater_input]` and
`vs_yne[ext_blank]`. The original undifferentiated enumeration is dropped. See
`nwss_utils.get_detailed_enums`.

## The steps

For each supplied dictionary type, `make_nwss` runs the following in order.
Every step is also its own CLI
(`python -m odm_linkmlgen.nwss.make_nwss_ss_classes --help`).

### 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from this dictionary
type's `dictionary/`, `schemasheets/`, and `linkml/` directories, so a stale file
from a previous run cannot leak into the new schema.

### 2. Extract the Excel sheets to CSV

`utils.general_utils.extract_sheets`

Saves the metadata sheet as `dictionary/metadata.csv` and the `Value Sets` sheet
as `dictionary/enums.csv`. The source sheet names depend on the dictionary type,
per the table at the top of this page; the output names do not, so the later steps
are dictionary-type agnostic.

Unlike the ODM pipeline, only a truly empty cell is treated as missing, in every
column (`default_na_values=[""]`).

### 3. Extract the enumerations

`nwss.make_nwss_ss_enums.extract_enums` → `schemasheets/enum_{enum_name}.tsv`

Parses the `Value Sets` sheet into one Schemasheet per enumeration, expanding the
detailed enumeration names described above. This step is skipped when the
dictionary has no `Value Sets` sheet, in which case the schema is generated
without any enumerations.

### 4. Extract the classes

`nwss.make_nwss_ss_classes.extract_all_classes` →
`schemasheets/classes_{table_name}.tsv`

Splits the metadata sheet into tables, then for each table `parse_table_df`
builds the Schemasheets columns:

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

Because NWSS data types are prose rather than a controlled vocabulary, this step
is the most likely place to need attention when a new dictionary version is
published. The `@TODO` comments in `_data_types_validation_info` mark patterns
that are known to be too permissive.

### 5. Extract the Container class

`nwss.make_nwss_ss_container.extract_container_class` →
`schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one multivalued
inlined slot per table. With `single_table=True` that is a single `nwss` slot.

### 6. Write the prefixes Schemasheet

`nwss.make_nwss_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines one CURIE prefix: `nwss_{dictionary_type}` →
`https://onto.phes-odm.org/nwss/{dictionary_type}/`.

### 7. Write the schema metadata Schemasheet

`nwss.make_nwss_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata for this dictionary type: name, id,
description, and default prefix. Unlike the ODM equivalent, the values are passed
in by `make_nwss` rather than built inside the module.

### 8. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets` →
`linkml/nwss_{dictionary_type}.yaml`

Runs Schemasheets over every `.tsv` in `schemasheets/`, applies
`fix_schemasheets_generated_schema` (see
[Post-processing workarounds](architecture.md#post-processing-workarounds)), and
writes the YAML. There is no NWSS equivalent of the ODM missingness
post-processing step.
