# ODM pipeline steps

The eleven steps `odm-linkmlgen-odm` (`odm_linkmlgen.make_odm.make_odm`) runs, in
order, to turn an ODM v2+ Excel data dictionary into a LinkML schema.

Every step is also its own CLI, so any one can be re-run against the CSVs already
in `dictionary/` — see
[Re-run a single pipeline step](../how-to/run-a-single-pipeline-step.md), which
includes a Python example reproducing all eleven.

!!! note "ODM v1 does not use this pipeline"

    Its Schemasheets TSVs are hand-written and bundled at
    `odm_linkmlgen/data/odm_v1/schemasheets/`, so `odm-linkmlgen-odmv1` runs only
    step 9's equivalent over them.

## Summary

| # | Module / function | Output |
| --- | --- | --- |
| 1 | `utils.general_utils.clear_dirs` | — |
| 2 | `utils.general_utils.extract_sheets` | `dictionary/parts.csv`, `dictionary/sets.csv` |
| 3 | `odm.make_odm_ss_enums_from_sets.extract_sets_enums` | `schemasheets/enums_sets.tsv` |
| 4 | `odm.make_odm_ss_enums_from_parts.extract_parts_enums` | `schemasheets/enums_parts.tsv` |
| 5 | `odm.make_odm_ss_classes.extract_all_classes` | `schemasheets/class_{class_name}.tsv` |
| 6 | `odm.make_odm_ss_container.extract_container_class` | `schemasheets/container.tsv` |
| 7 | `odm.make_odm_ss_prefixes.make_prefixes` | `schemasheets/prefixes.tsv` |
| 8 | `odm.make_odm_ss_schema.make_schema` | `schemasheets/schema.tsv` |
| 9 | `utils.schemasheets_utils.make_linkml_schema_from_schemasheets` | A `SchemaDefinition` |
| 10 | `odm.odm_utils.add_missingness_set` | — (mutates the schema) |
| 11 | `utils.schemasheets_utils.save_schema_definition` | `linkml/odm_v{version}.yaml` |

## 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from `dictionary/`,
`schemasheets/`, and `linkml/`, so that a stale file from a previous run cannot
leak into the new schema.

This matters because step 9 consumes **every** `.tsv` in `schemasheets/` rather
than a known list of files.

## 2. Extract the Excel sheets to CSV

`utils.general_utils.extract_sheets`

Saves the **parts** and **sets** sheets as `dictionary/parts.csv` and
`dictionary/sets.csv`.

The `na_values` argument is set so that **only a truly empty cell counts as
missing** in the `partID` column. Without it, pandas would read part IDs such as
`NA`, `None`, and `null` — which are real permissible values in the ODM — as
missing values.

## 3. Extract the enumerations defined in the sets sheet

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
  [post-processing workarounds](../explanation/post-processing-workarounds.md).

Returns the list of enumeration names it extracted.
`make_odm_ss_enums_from_sets.get_enum_names_from_sets` retrieves the same names
from a sets sheet DataFrame without extracting anything.

## 4. Extract the enumerations defined in the parts sheet

`odm.make_odm_ss_enums_from_parts.extract_parts_enums` → `schemasheets/enums_parts.tsv`

Handles the enumerations step 3 does not: those with an empty `mmaSet`. Their
names are the distinct values of the parts sheet's `partType` column, retrieved by
`get_enum_names_from_parts`. For each name it collects:

- the top-level row, where `partID` equals the enumeration name, and
- every permissible value, which is any row whose `partType` equals the
  enumeration name.

Also returns the list of enumeration names it extracted.

**`make_odm` combines the names from steps 3 and 4, de-duplicated, and passes the
result to step 5 as `recognized_enums`.**

## 5. Extract one Schemasheet per class

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
4. Maps `dataType` to a LinkML range via `_data_types_map` — for example
   `varchar` → `string`, `boolean` → `booleanSet`.
5. Resolves categorical ranges to an enumeration name: from `mmaSet` when it is
   set, otherwise derived from the part ID. **A derived name that is not in
   `recognized_enums` falls back to `string`**, so an enumeration that could not
   be extracted degrades to an unconstrained string rather than a dangling
   reference.
6. Marks primary keys as LinkML `identifier`s.
7. Resolves each foreign key's range to the class it points at, using
   `odm_utils.odm_get_fk_target_class`. That function looks for the class in which
   the part ID is the primary key, and if the part ID is not itself a primary key
   it follows `fKAliasID` and tries again.
8. Converts `minLength`/`maxLength` into a LinkML `pattern` regex of the form
   `^.{min,max}$`, since LinkML has no direct string-length constraint.
9. Sorts the rows by `order`, and appends a final row carrying the table's own
   title and description.

## 6. Extract the Container class

`odm.make_odm_ss_container.extract_container_class` → `schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one slot per ODM
table. Each slot is multivalued and inlined as a list, with the table's class as
its range — so a data file is a set of named tables, each holding a list of rows.

## 7. Write the prefixes Schemasheet

`odm.make_odm_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines the CURIE prefixes used by the schema. For ODM this is a single prefix per
version: `odmv{version}` → `https://onto.phes-odm.org/odm/v{version}/`.

## 8. Write the schema metadata Schemasheet

`odm.make_odm_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata: name (`ODMv{version}`), id
(`https://onto.phes-odm.org/odm/v{version}`), description, and default prefix.

Both this and step 7 template their values on the version string inside their own
modules, which is why a new ODM version usually needs no code change.

## 9. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets`

Runs Schemasheets over **every** `.tsv` in `schemasheets/` and returns a
`SchemaDefinition`, then applies `fix_schemasheets_generated_schema` to correct
the known Schemasheets shortcomings described in
[post-processing workarounds](../explanation/post-processing-workarounds.md).

## 10. Add the missingness sets

`odm.odm_utils.add_missingness_set`

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet` — in addition to their normal range, so a value can be
reported as missing for a documented reason. The parts sheet records this in the
`missingnessSet` column, but no Schemasheets column expresses it, so it is applied
afterwards directly on the `SchemaDefinition`.

For every slot usage whose part has a `missingnessSet`, that enumeration is added
to the slot's ranges. A slot that ends up with more than one range is written as
LinkML `any_of` rather than a single `range` — see `odm_utils.set_range_of_slot`.

## 11. Save the schema

`utils.schemasheets_utils.save_schema_definition` → `linkml/odm_v{version}.yaml`

Serialises the `SchemaDefinition` to YAML. `make_odm` also returns the
`SchemaDefinition` to its caller.

## Related

- [The ODM data dictionary](../explanation/the-odm-data-dictionary.md) — the
  source conventions steps 3–5 are decoding
- [Output layout](output-layout.md)
- [Python API: ODM modules](api/odm.md)
