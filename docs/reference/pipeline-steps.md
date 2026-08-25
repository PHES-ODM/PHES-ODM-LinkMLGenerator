# Pipeline steps

Every step of both pipelines in order, with its module, its inputs, and its
outputs. For why the pipeline is shaped this way, see
[How it works](../explanation/how-it-works.md#the-three-stage-pipeline).

Every step is also its own CLI, so any one can be re-run against the CSVs already
in `dictionary/` — see
[Re-run a single step](../how-to/python-api.md#re-run-a-single-step), which
shows how to work from the source of `make_odm` to experiment with an individual
step.

## ODM pipeline steps

The eleven steps `odm-linkmlgen-odm` (`odm_linkmlgen.make_odm.make_odm`) runs, in
order, to turn an ODM v2+ data dictionary into a LinkML schema. The dictionary is
either an Excel workbook or its parts and sets sheets already saved as CSV, which
changes step 2 only.

!!! note "ODM v1 does not use this pipeline"

    Its Schemasheets TSVs are hand-written and bundled at
    `odm_linkmlgen/data/odm_v1/schemasheets/`, so
    `odm-linkmlgen-odmv1` (`odm_linkmlgen.make_odm_v1.make_odm_v1`) runs only
    step 9's equivalent over them, followed by the same undefined-range check as
    step 11. There is no data dictionary behind it, so that check is guarding the
    bundled TSVs against an editing mistake rather than an upstream defect.

| # | Module / function | Output |
| --- | --- | --- |
| 1 | `utils.general_utils.clear_dirs` | — |
| 2 | `utils.general_utils.extract_sheets`, or a copy through `utils.general_utils.get_na_values` | `dictionary/parts.csv`, `dictionary/sets.csv` |
| 3 | `odm.make_odm_ss_enums_from_sets.extract_sets_enums` | `schemasheets/enums_sets.tsv` |
| 4 | `odm.make_odm_ss_enums_from_parts.extract_parts_enums` | `schemasheets/enums_parts.tsv` |
| 5 | `odm.make_odm_ss_classes.extract_all_classes` | `schemasheets/class_{class_name}.tsv` |
| 6 | `odm.make_odm_ss_container.extract_container_class` | `schemasheets/container.tsv` |
| 7 | `odm.make_odm_ss_prefixes.make_prefixes` | `schemasheets/prefixes.tsv` |
| 8 | `odm.make_odm_ss_schema.make_schema` | `schemasheets/schema.tsv` |
| 9 | `utils.schemasheets_utils.make_linkml_schema_from_schemasheets` | A `SchemaDefinition` |
| 10 | `odm.odm_utils.add_missingness_set` | — (mutates the schema) |
| 11 | `utils.schemasheets_utils.save_schema_definition` | `linkml/odm_v{version}.yaml` |

### ODM 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from `dictionary/`,
`schemasheets/`, and `linkml/`, so that a stale file from a previous run cannot
leak into the new schema.

This matters because step 9 consumes **every** `.tsv` in `schemasheets/` rather
than a known list of files.

### ODM 2. Extract or copy the dictionary sheets to CSV

`utils.general_utils.extract_sheets`, or `utils.general_utils.get_na_values`

Saves the **parts** and **sets** sheets as `dictionary/parts.csv` and
`dictionary/sets.csv`. Which of the two paths runs depends on how the dictionary
was given:

| Given | What runs |
| --- | --- |
| `--dictionary-file` (Excel) | `extract_sheets` extracts the two sheets |
| `--parts-file` and `--sets-file` (CSV) | The two files are read and re-saved under `dictionary/` |

Either way the rest of the pipeline reads the same two paths, so the input form
is invisible from step 3 onwards. See the
[CLI reference](cli.md#odm-linkmlgen-odm) for which form to pass.

The `na_values` argument is set so that **only a truly empty cell counts as
missing** in the `partID` column. Without it, pandas would read part IDs such as
`NA`, `None`, and `null` — which are real permissible values in the ODM — as
missing values.

Both paths get that from `general_utils.get_na_values`, which reads only the
header row of the file and returns the NA values for **every** column: the
`partID` override for `partID`, and pandas' own defaults for the rest. That
completeness is what lets both paths read with `keep_default_na=False` — which
switches pandas' defaults off wholesale — without losing NA parsing everywhere
else. `extract_sheets` calls it per sheet of the workbook; the CSV path calls it
per file.

### ODM 3. Extract the enumerations defined in the sets sheet

`odm.make_odm_ss_enums_from_sets.extract_sets_enums` → `schemasheets/enums_sets.tsv`

Takes the active rows of the sets sheet, where `setID` is the enumeration name and
`partID` is a permissible value, and joins the parts sheet on `partID` to pick up
each value's `label` (title) and `partDesc` (description).

Two details:

- **Duplicate values are merged.** When the same permissible value appears more
  than once within one enumeration, the rows are collapsed into one and their
  titles and descriptions are joined with ` / `. This mostly affects enumerations
  with several blank permissible values, producing a merged title such as
  `Not applicable / Not a number / Null`.
- **A top-level row is added per enumeration**, carrying the enumeration's own
  title and description rather than a permissible value's. Schemasheets treats a
  row with no permissible value as metadata for the enumeration itself — which is
  also why an intentionally empty permissible value must be written as the
  `<empty>` sentinel. See
  [post-processing workarounds](../explanation/how-it-works.md#post-processing-workarounds).

Returns the list of enumeration names it extracted.
`make_odm_ss_enums_from_sets.get_enum_names_from_sets` retrieves the same names
from a sets sheet DataFrame without extracting anything.

### ODM 4. Extract the enumerations defined in the parts sheet

`odm.make_odm_ss_enums_from_parts.extract_parts_enums` → `schemasheets/enums_parts.tsv`

Handles the enumerations step 3 does not: those with an empty `mmaSet`. Their
names are the distinct values of the parts sheet's `partType` column, retrieved by
`get_enum_names_from_parts`. For each name it collects:

- the top-level row, where `partID` equals the enumeration name, and
- every permissible value, which is any row whose `partType` equals the
  enumeration name.

Also returns the list of enumeration names it extracted.

Steps 3 and 4 both return their names for the caller's convenience, but `make_odm`
does not need them: step 5 resolves a slot's enumeration from the part's own row
in the parts sheet, so the two enumeration steps and the class step are
independent.

### ODM 5. Extract one Schemasheet per class

`odm.make_odm_ss_classes.extract_all_classes` → `schemasheets/class_{class_name}.tsv`

For every table discovered in the parts sheet, `extract_class` builds one
Schemasheet. **This is the largest step.** Per table it:

1. Keeps the rows that are a `pK`, `fK`, or `header` for that table, and of those
   only the ones with `active` status.
2. Renames the table-specific columns to generic ones: `{table}` → `headerType`,
   `{table}Required` → `required`, `{table}Order` → `order`. A missing column
   raises a `RuntimeError`, except for `fKAliasID`, which is optional because v2
   dictionaries do not have it.
3. Sets `required` to true where the original value was `mandatory`.
4. Resolves each row's LinkML range with `odm_utils.odm_get_data_type_of_row`.
   The part's `mmaSet` wins, so a categorical range becomes the enumeration name
   the dictionary gives it; otherwise `dataType` is mapped through
   `odm_utils._data_types_map` — for example `varchar` → `string`, `boolean` →
   `booleanSet`. **Anything unmapped falls back to `string`**: both a
   `categorical` part with no `mmaSet` and a `dataType` missing from the map
   degrade to an unconstrained string rather than a dangling reference.
5. Marks primary keys as LinkML `identifier`s.
6. Resolves each foreign key's range to the class it points at, using
   `odm_utils.odm_get_fk_target_class`. That function looks for the class in which
   the part ID is the primary key, and if the part ID is not itself a primary key
   it follows `fKAliasID` and tries again.
7. Converts `minLength`/`maxLength` into a LinkML `pattern` regex of the form
   `^.{min,max}$`, since LinkML has no direct string-length constraint.
8. Sorts the rows by `order`, and appends a final row carrying the table's own
   title and description.

### ODM 6. Extract the Container class

`odm.make_odm_ss_container.extract_container_class` → `schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one slot per ODM
table. Each slot is multivalued and inlined as a list, with the table's class as
its range — so a data file is a set of named tables, each holding a list of rows.

### ODM 7. Write the prefixes Schemasheet

`odm.make_odm_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines the CURIE prefixes used by the schema. For ODM this is a single prefix per
version: `odmv{version}` → `https://onto.phes-odm.org/odm/v{version}/`.

### ODM 8. Write the schema metadata Schemasheet

`odm.make_odm_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata: name (`ODMv{version}`), id
(`https://onto.phes-odm.org/odm/v{version}`), description, and default prefix.

Both this and step 7 template their values on the version string inside their own
modules, which is why a new ODM version usually needs no code change.

### ODM 9. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets`

Runs Schemasheets over **every** `.tsv` in `schemasheets/` and returns a
`SchemaDefinition`, then applies `fix_schemasheets_generated_schema` to correct
the known Schemasheets shortcomings described in
[post-processing workarounds](../explanation/how-it-works.md#post-processing-workarounds).

### ODM 10. Add the missingness sets

`odm.odm_utils.add_missingness_set`

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet` — in addition to their normal range, so a value can be
reported as missing for a documented reason. The parts sheet records this in the
`missingnessSet` column, but no Schemasheets column expresses it, so it is applied
afterwards directly on the `SchemaDefinition`.

For every slot usage whose part has a `missingnessSet`, that enumeration is added
to the slot's ranges. A slot that ends up with more than one range is written as
LinkML `any_of` rather than a single `range` — see `odm_utils.set_range_of_slot`.

### ODM 11. Save the schema

`utils.schemasheets_utils.save_schema_definition` → `linkml/odm_v{version}.yaml`

Serialises the `SchemaDefinition` to YAML. `make_odm` also returns the
`SchemaDefinition` to its caller.

`make_odm` then checks the finished schema with
`schema_utils.find_undefined_ranges` and logs an error for every slot whose range
names something the schema does not define — usually an enumeration named by the
parts or sets sheet that was never generated. This is a check rather than a step:
the schema is written either way. It runs after step 10 so that the ranges it
sees are the final ones, including the `any_of` pairings that step introduces.
The NWSS pipeline runs the same check, for the same reason — LinkML does not
resolve ranges when a schema is loaded, so without it a schema that no tool can
actually use still looks like a clean run.

## NWSS pipeline steps

The eight steps `odm-linkmlgen-nwss` (`odm_linkmlgen.make_nwss.make_nwss`) runs
**per dictionary type supplied**, in order. Each type gets its own independent
schema under its own subdirectory.

There is **no NWSS equivalent of the ODM missingness post-processing step**, so
the pipeline is eight steps rather than eleven.

### What `make_nwss` passes down

`single_table` is passed straight through from `make_nwss`'s own
`single_table` parameter (`--single-table` / `--no-single-table`), which defaults
to `True`. The remaining values are fixed by `make_nwss` rather than being
configurable, and `detailed_enum_names` differs from the step CLIs' default:

| Value | Set to |
| --- | --- |
| `single_table` | Caller's value — `True` by default, merging every table into one class named `nwss` |
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

### NWSS 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from this dictionary type's
`dictionary/`, `schemasheets/`, and `linkml/` directories, so a stale file from a
previous run cannot leak into the new schema. Step 8 consumes every `.tsv` in the
directory, not a known list.

### NWSS 2. Extract the Excel sheets to CSV

`utils.general_utils.extract_sheets`

Saves the metadata sheet as `dictionary/metadata.csv` and the `Value Sets` sheet as
`dictionary/enums.csv`.

The **source** sheet names depend on the dictionary type, per the table above; the
**output** names do not. That is what keeps every later step dictionary-type
agnostic.

Unlike the ODM pipeline, only a truly empty cell is treated as missing, in every
column (`default_na_values=[""]`).

### NWSS 3. Extract the enumerations

`nwss.make_nwss_ss_enums.extract_enums` → `schemasheets/enum_{enum_name}.tsv`

Parses the `Value Sets` sheet into one Schemasheet per enumeration, expanding the
[detailed enumeration names](../explanation/data-dictionaries.md#detailed-enumeration-names)
— so `vs_yne` becomes `enum_vs_yne[stormwater_input].tsv` and one file per other
field that uses it, and the undifferentiated original is dropped.

Which fields those are comes from `nwss_utils.resolve_slot_enums`, the same
function step 4 uses to set the ranges, so the enumerations written here and the
ranges that name them cannot disagree. This step passes `log_problems=False`: an
unresolved enumeration is reported by step 4, whose output is the one left broken
by it.

This step is **skipped when the dictionary has no `Value Sets` sheet**, in which
case the schema is generated without any enumerations at all.

### NWSS 4. Extract the classes

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
       enumeration name — including its detailed per-slot form where that applies
       — is resolved by `nwss_utils.resolve_slot_enums`, which prefers the row's
       own `Value Set` column and falls back to the `Field` → `Value Set Name`
       mapping in the `Value Sets` sheet. The enumeration step calls the same
       function, which is what keeps a range and the enumeration it names in
       agreement. See
       [which enumeration a field uses](data-dictionaries.md#which-enumeration-a-field-uses).
       A categorical field with no enumeration anywhere logs an error and leaves
       the range unresolved.
    2. Otherwise the `Data Type` is matched against the regex table
       `_data_types_validation_info`, which maps NWSS's free-text data type
       descriptions onto a LinkML range plus a validation `pattern`. This is how
       types such as `date`, `time`, `time zone`, `ZIP code`, `NPDES permit
       number`, `EPA Registry ID`, and `jurisdiction id` acquire their regexes.
    3. Failing that, a `Data Type` containing `#` characters is converted into a
       regex by replacing each `#` with `[0-9]`. Anything else is copied through as
       the range unchanged.

With `single_table=True` — the default — every table is concatenated into a
single class named `nwss`, producing one `classes_nwss.tsv`. With
`single_table=False` each table gets its own `classes_{table_name}.tsv`.

Because NWSS data types are prose rather than a controlled vocabulary, **this step
is the most likely place to need attention when a new dictionary version is
published.** The `@TODO` comments in `_data_types_validation_info` mark patterns
that are known to be too permissive.

### NWSS 5. Extract the Container class

`nwss.make_nwss_ss_container.extract_container_class` → `schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one multivalued
inlined slot per table. With `single_table=True` — the default — that is a single
`nwss` slot.

### NWSS 6. Write the prefixes Schemasheet

`nwss.make_nwss_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines one CURIE prefix: `nwss_{dictionary_type}` →
`https://onto.phes-odm.org/nwss/{dictionary_type}/`.

### NWSS 7. Write the schema metadata Schemasheet

`nwss.make_nwss_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata for this dictionary type: name, id, description,
and default prefix.

Unlike the ODM equivalent, **the values are passed in by `make_nwss`** rather
than being built inside the module. They come from the module-level
`SCHEMA_VALUES_TEMPLATE` dict in `make_nwss`, whose values are
`{dictionary_type}` format templates interpolated per type into the
`schema_values` dict handed to this step. `make_schema` takes a
`data_values` dict that overrides its own defaults.

### NWSS 8. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets` →
`linkml/nwss_{dictionary_type}.yaml`

Runs Schemasheets over every `.tsv` in `schemasheets/`, applies
`fix_schemasheets_generated_schema` (see
[post-processing workarounds](../explanation/how-it-works.md#post-processing-workarounds)),
and writes the YAML.

`make_nwss` then checks the finished schema with
`schema_utils.find_undefined_ranges` and logs an error for every slot whose range
names something the schema does not define. This is a check rather than a step: the
schema is written either way. It exists because LinkML does not resolve ranges when
a schema is loaded, so without it a schema that no tool can actually use still looks
like a clean run.
