# The ODM pipeline

This page describes how `odm-linkmlgen-odm` (the
[`make_odm`](../odm_linkmlgen/make_odm.py) function) turns an ODM v2+ Excel data
dictionary into a LinkML schema. Read [Architecture](architecture.md) first for
the concepts and vocabulary used here.

ODM v1 does not use this pipeline. Its Schemasheets TSVs are hand-written and
bundled at `odm_linkmlgen/data/odm_v1/schemasheets/`, so `odm-linkmlgen-odmv1`
only runs the final Schemasheets step over them.

## Preparing the ODM data dictionary

The dictionary is not publicly available and is not committed to this repository
(the Excel files under `odm_linkmlgen/data/odm_v*/` are git-ignored). Contact
[Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a copy.

Save it as `v# ODM dictionary.xlsx`, where `#` is the version number (for example
`v3 ODM dictionary.xlsx`). By convention it goes in
`odm_linkmlgen/data/odm_v{n}/`, but you can pass any path to
`--dictionary-file`.

> **Use a recent version of Excel to open this file.** The workbook relies on the
> `FILTER` and `XLOOKUP` functions, which older versions of Excel do not
> support. Opening and resaving it with an older version will corrupt the
> workbook.

## How the parts sheet encodes the data model

Almost everything the generator needs is in the **parts** sheet, one row per
"part". A row's meaning comes from the combination of its columns, so it is worth
knowing the conventions before reading the steps below.

The columns that carry the most meaning are:

| Column | Meaning |
| --- | --- |
| `partID` | The name of the part: a table, a column, an enumeration, or a permissible value. |
| `partType` | For a permissible value, the name of the enumeration it belongs to. |
| `status` | Only rows with `active` are used; everything else is deprecated and skipped. |
| `dataType` | The part's type. `categorical` means its range is an enumeration. |
| `mmaSet` | For a categorical part, the name of its enumeration when that enumeration is defined in the **sets** sheet. Empty when the enumeration is instead defined in the parts sheet. |
| `missingnessSet` | A missingness enumeration that must be accepted alongside the part's normal range. |
| `label`, `partDesc` | The part's title and description. |
| `minValue`, `maxValue`, `minLength`, `maxLength` | Numeric and string-length bounds. |
| `fKAliasID` | For a foreign key that is an alias, the part ID it is an alias of. Absent from v2 dictionaries. |

**Table membership.** Each ODM table has a column in the parts sheet named after
the table, plus companion `{table}Required` and `{table}Order` columns. A row
belongs to a table when the table's column contains one of three tags:

- `pK` — the row is the table's primary key
- `fK` — the row is a foreign key in the table
- `header` — the row is an ordinary column of the table

So every column of the `measures` table has `pK`, `fK`, or `header` in the parts
sheet column named `measures`, and its position in the table comes from
`measuresOrder`.

**Discovering the tables.** The generator does not hardcode the list of ODM
tables. `odm_utils.odm_get_available_class_names` finds them by scanning the parts
sheet column headers for any name ending in `Order` (the value of
`odm_utils.ODM_PARTS_COLUMN_CLASS_TAG`) and stripping that suffix, so
`measuresOrder` implies a table named `measures`.

**Enumerations.** A part whose `dataType` is `categorical` has an enumeration as
its range, and that enumeration is defined in one of two places:

- If `mmaSet` is set, the permissible values are in the **sets** sheet and
  `mmaSet` holds the enumeration's name.
- If `mmaSet` is empty, the enumeration is defined in the parts sheet itself: its
  permissible values are the rows whose `partType` equals the enumeration's name.
  The name is derived from the part ID, usually by appending an `s`
  (`sampleType` → `sampleTypes`). A handful of part IDs do not follow that
  pattern and are listed in `odm_utils._odm_enum_name_exceptions`; the derivation
  is done by `odm_utils.odm_get_enum_name_from_part_id`.

## The steps

`make_odm` runs the following in order. Every step is also its own CLI, so you
can re-run any one of them against the CSVs already in `dictionary/` — see
[Running the steps by hand](#running-the-steps-by-hand).

### 1. Clear the output directories

`utils.general_utils.clear_dirs`

Deletes any existing `.csv`, `.tsv`, and `.yaml` files from `dictionary/`,
`schemasheets/`, and `linkml/`, so that a stale file from a previous run cannot
leak into the new schema. This matters because the final step consumes *every*
`.tsv` in `schemasheets/` rather than a known list of files.

### 2. Extract the Excel sheets to CSV

`utils.general_utils.extract_sheets`

Saves the **parts** and **sets** sheets as `dictionary/parts.csv` and
`dictionary/sets.csv`.

The `na_values` argument is set so that only a truly empty cell counts as missing
in the `partID` column. Without it, pandas would read part IDs such as `NA`,
`None`, and `null` — which are real permissible values in the ODM — as missing
values.

### 3. Extract the enumerations defined in the sets sheet

`odm.make_odm_ss_enums_from_sets.extract_sets_enums` →
`schemasheets/enums_sets.tsv`

Takes the active rows of the sets sheet, where `setID` is the enumeration name
and `partID` is a permissible value, and joins the parts sheet on `partID` to
pick up each value's `label` (title) and `partDesc` (description).

Two details are worth noting:

- **Duplicate values are merged.** When the same permissible value appears more
  than once within one enumeration, the rows are collapsed into one and their
  titles and descriptions are joined with ` / `. This mostly affects
  enumerations with several blank permissible values, producing a merged title
  such as `Not applicable / Not a number / Null`.
- **A top-level row is added per enumeration**, carrying the enumeration's own
  title and description rather than a permissible value's. Schemasheets treats a
  row with no permissible value as metadata for the enumeration itself, which is
  also why an intentionally empty permissible value must be written as the
  `<empty>` sentinel — see
  [Post-processing workarounds](architecture.md#post-processing-workarounds).

The function returns the list of enumeration names it extracted.

### 4. Extract the enumerations defined in the parts sheet

`odm.make_odm_ss_enums_from_parts.extract_parts_enums` →
`schemasheets/enums_parts.tsv`

Handles the enumerations that step 3 does not: those with an empty `mmaSet`. It
finds them by taking the active header rows (`pK`, `fK`, or `header` in any
table) whose `dataType` is `categorical` and whose `mmaSet` is empty, and
deriving an enumeration name from each part ID. For each name it then collects:

- the top-level row, where `partID` equals the enumeration name, and
- every permissible value, which is any row whose `partType` equals the
  enumeration name.

It also returns the list of enumeration names it extracted. `make_odm` combines
the names from steps 3 and 4, de-duplicated, and passes the result to step 5 as
`recognized_enums`.

### 5. Extract one Schemasheet per class

`odm.make_odm_ss_classes.extract_all_classes` →
`schemasheets/class_{class_name}.tsv`

For every table discovered in the parts sheet, `extract_class` builds one
Schemasheet. This is the largest step. Per table it:

1. Keeps the rows that are a `pK`, `fK`, or `header` for that table, and of those
   only the ones with `active` status.
2. Renames the table-specific columns to generic ones: `{table}` →
   `headerType`, `{table}Required` → `required`, `{table}Order` → `order`. A
   missing column raises a `RuntimeError`, except for `fKAliasID`, which is
   optional because v2 dictionaries do not have it.
3. Sets `required` to true where the original value was `mandatory`.
4. Maps `dataType` to a LinkML range via `_data_types_map` (for example
   `varchar` → `string`, `boolean` → `booleanSet`).
5. Resolves categorical ranges to an enumeration name: from `mmaSet` when it is
   set, otherwise derived from the part ID. A derived name that is not in
   `recognized_enums` falls back to `string`, so an enumeration that could not
   be extracted degrades to an unconstrained string rather than a dangling
   reference.
6. Marks primary keys as LinkML `identifier`s.
7. Resolves each foreign key's range to the class it points at, using
   `odm_utils.odm_get_fk_target_class`. That function looks for the class in
   which the part ID is the primary key, and if the part ID is not itself a
   primary key it follows `fKAliasID` and tries again.
8. Converts `minLength`/`maxLength` into a LinkML `pattern` regex of the form
   `^.{min,max}$`, since LinkML has no direct string-length constraint.
9. Sorts the rows by `order`, and appends a final row carrying the table's own
   title and description.

### 6. Extract the Container class

`odm.make_odm_ss_container.extract_container_class` → `schemasheets/container.tsv`

Builds the top-level `Container` class, marked `tree_root`, with one slot per ODM
table. Each slot is multivalued and inlined as a list, with the table's class as
its range — so a data file is a set of named tables, each holding a list of rows.

### 7. Write the prefixes Schemasheet

`odm.make_odm_ss_prefixes.make_prefixes` → `schemasheets/prefixes.tsv`

Defines the CURIE prefixes used by the schema. For ODM this is a single prefix
per version: `odmv{version}` → `https://onto.phes-odm.org/odm/v{version}/`.

### 8. Write the schema metadata Schemasheet

`odm.make_odm_ss_schema.make_schema` → `schemasheets/schema.tsv`

Defines the schema-level metadata: name (`ODMv{version}`), id
(`https://onto.phes-odm.org/odm/v{version}`), description, and default prefix.

### 9. Run Schemasheets

`utils.schemasheets_utils.make_linkml_schema_from_schemasheets`

Runs Schemasheets over every `.tsv` in `schemasheets/` and returns a
`SchemaDefinition`, then applies `fix_schemasheets_generated_schema` to correct
the known Schemasheets shortcomings described in
[Post-processing workarounds](architecture.md#post-processing-workarounds).

### 10. Add the missingness sets

`odm.odm_utils.add_missingness_set`

Some ODM slots must accept a missingness enumeration (for example
`genMissingnessSet` or `nrNAMissingnessSet`) in addition to their normal range,
so that a value can be reported as missing for a documented reason. The parts
sheet records this in the `missingnessSet` column, but no Schemasheets column
expresses it, so it is applied afterwards directly on the `SchemaDefinition`.

For every slot usage whose part has a `missingnessSet`, that enumeration is added
to the slot's ranges. A slot that ends up with more than one range is written as
LinkML `any_of` rather than a single `range` — see `odm_utils.set_range_of_slot`.

### 11. Save the schema

`utils.schemasheets_utils.save_schema_definition` →
`linkml/odm_v{version}.yaml`

Serialises the `SchemaDefinition` to YAML. `make_odm` also returns the
`SchemaDefinition` to its caller.

## Running the steps by hand

The following reproduces `make_odm` exactly, and is the starting point for
experimenting with an individual step:

```python
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.odm.odm_utils import add_missingness_set
from odm_linkmlgen.utils.general_utils import clear_dirs, extract_sheets
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
    save_schema_definition,
)

version = "3"
dictionary_file = f"odm_linkmlgen/data/odm_v{version}/v{version} ODM dictionary.xlsx"
output_dir = f"gen/odm_v{version}"
dictionary_dir = f"{output_dir}/dictionary"
schemasheets_dir = f"{output_dir}/schemasheets"
linkml_dir = f"{output_dir}/linkml"
parts_file = f"{dictionary_dir}/parts.csv"
sets_file = f"{dictionary_dir}/sets.csv"

# 1. Remove any stale csv/tsv/yaml files from a previous run
clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

# 2. Extract the sheets from Excel to CSV. The na_values argument keeps partID
#    values such as "NA" and "None" as literal strings rather than NA values.
extract_sheets(
    dictionary_file,
    ["parts", "sets"],
    dictionary_dir,
    na_values={"parts": {"partID": ""}, "sets": {"partID": ""}},
)

# 3 & 4. Extract the enumerations, first from the sets sheet (the mmaSet enums),
#        then the remaining ones from the parts sheet
all_enums = extract_sets_enums(
    sets_file, parts_file, f"{schemasheets_dir}/enums_sets.tsv"
)
all_enums += extract_parts_enums(parts_file, f"{schemasheets_dir}/enums_parts.tsv")
all_enums = list(dict.fromkeys(all_enums))

# 5. Extract the classes (one Schemasheet per ODM table)
extract_all_classes(parts_file, schemasheets_dir, recognized_enums=all_enums)

# 6, 7, 8. Container class, prefixes, and schema metadata
extract_container_class(parts_file, f"{schemasheets_dir}/container.tsv")
make_prefixes(f"{schemasheets_dir}/prefixes.tsv", version)
make_schema(f"{schemasheets_dir}/schema.tsv", version)

# 9. Run Schemasheets over all the generated TSV files
schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

# 10. Add the missingness enumerations
add_missingness_set(schema, parts_file)

# 11. Save the final LinkML schema
save_schema_definition(schema, f"{linkml_dir}/odm_v{version}.yaml")
```

Each step is also a CLI. For example, to rebuild only the class Schemasheets from
an existing `parts.csv`:

```console
python -m odm_linkmlgen.odm.make_odm_ss_classes \
    --parts-file "gen/odm_v3/dictionary/parts.csv" \
    --output-dir "gen/odm_v3/schemasheets"
```

When run this way `--recognized-enums` is omitted, which disables the check in
step 5: every derived enumeration name is used as-is, so the resulting
Schemasheets can reference enumerations that no other Schemasheet defines. Pass
the enumeration names explicitly if that matters for what you are testing.
