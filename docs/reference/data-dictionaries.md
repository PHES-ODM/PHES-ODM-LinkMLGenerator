# The source data dictionaries

What the generator reads out of the two source Excel workbooks: which sheets,
which columns, and how each encodes its data model.

Why they are shaped this way, and what that shape costs, is in
[Why the dictionaries are hard to read](../explanation/data-dictionaries.md).
[How it works](../explanation/how-it-works.md) describes what the generator does
with what it reads.

## The ODM data dictionary

The PHES-ODM data dictionary is an Excel workbook that authoritatively defines
every table, field, and permissible value in the ODM. The generator reads two of
its sheets:

- **parts** — one row per "part". A part can be a table, a column, an
  enumeration, or a permissible value of an enumeration. This sheet defines all
  classes and slots, along with their data types and constraints.
- **sets** — the permissible values for many (not all) of the enumerations.

### The columns that carry meaning

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

### Table membership

Each ODM table has a column in the parts sheet **named after the table**, plus
companion `{table}Required` and `{table}Order` columns. A row belongs to a table
when the table's column contains one of three tags:

- `pK` — the row is the table's primary key
- `fK` — the row is a foreign key in the table
- `header` — the row is an ordinary column of the table

So every column of the `measures` table has `pK`, `fK`, or `header` in the parts
sheet column named `measures`, and its position in the table comes from
`measuresOrder`.

The same part can belong to several tables with different constraints in each —
see
[a row's meaning comes from its neighbours](../explanation/data-dictionaries.md#a-rows-meaning-comes-from-its-neighbours).

#### Discovering the tables

The generator **does not hardcode the list of ODM tables.**
`odm_utils.odm_get_available_class_names` finds them by scanning the parts sheet
column headers for any name ending in `Order` — the value of
`odm_utils.ODM_PARTS_COLUMN_CLASS_TAG` — and stripping that suffix. So
`measuresOrder` implies a table named `measures`.

A new table in a new dictionary version is therefore picked up automatically,
with no code change, as long as it has the full
`{table}` / `{table}Required` / `{table}Order` trio. See
[Extending the generator](../how-to/extending.md#add-support-for-a-new-odm-version).

### Enumerations

A part whose `dataType` is `categorical` has an enumeration as its range. That
enumeration is defined in one of two places, and which one determines how the
generator finds its name and values.

#### Defined in the sets sheet

If `mmaSet` is set, the permissible values are in the **sets** sheet and `mmaSet`
holds the enumeration's name directly. Nothing needs deriving. In the sets sheet,
`setID` is the enumeration name and `partID` is a permissible value.

#### Defined in the parts sheet

If `mmaSet` is empty, the enumeration is defined in the parts sheet itself: its
permissible values are the rows whose `partType` equals the enumeration's name.
This is `partType`'s only job — it is how a permissible-value row says which
enumeration it belongs to.

Here the name must be **derived from the part ID**, usually by appending an `s`
(`sampleType` → `sampleTypes`). A handful of part IDs do not follow that pattern
and are listed in `odm_utils._odm_enum_name_exceptions` — `class` → `classes`,
`qualityFlag` → `qualityIndicators`, `aggragationScale` → `aggregationScales`
(the source has a typo), and several that need no change at all. The derivation
is done by `odm_utils.odm_get_enum_name_from_part_id`, which returns `string`
when the derived name is not one it recognizes — see
[why derivation needs a safety net](../explanation/data-dictionaries.md#why-enumeration-name-derivation-needs-a-safety-net).

### Missingness sets

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet`, and so on — *in addition to* their normal range, so that a
value can be reported as missing for a documented reason rather than just being
absent.

The parts sheet records this in the `missingnessSet` column. No Schemasheets
column expresses "add this range as well", so it is applied afterwards, directly
on the `SchemaDefinition`, by `odm_utils.add_missingness_set` — see
[post-processing workarounds](../explanation/how-it-works.md#missingness-sets-odm-only).

## The NWSS data dictionaries

NWSS is published as **five separate dictionaries**, each an Excel workbook, each
producing its own independent LinkML schema. `make_nwss` runs the whole pipeline
once per dictionary you supply.

| Dictionary type | Metadata sheet name | Publicly available |
| --- | --- | --- |
| `reporting` | `Metadata` | Yes |
| `public_concentration` | `Metadata` | Yes |
| `public_metric` | `Metadata` | Yes |
| `restricted_raw` | `Wastewater Metadata` | No |
| `restricted_analytics` | `Analytics Data Dictionary` | No |

Only the metadata sheet name varies. The enumerations always come from a sheet
named `Value Sets`. The dictionary type also determines the generated schema's
name, id, description, and prefix — `nwss_reporting` and
`https://onto.phes-odm.org/nwss/reporting`, for example.

Each workbook has two sheets of interest:

- a **metadata** sheet — one row per field, listing its data type, description,
  and whether it is required
- a **`Value Sets`** sheet — the enumerations and their permissible values, plus a
  mapping from each field to the value set it uses

Some of the published files require manual repair before they can be processed
at all — see
[the manual fixes](../how-to/generate-nwss-schemas.md#apply-the-manual-fixes).

### The metadata sheet has implicit table boundaries

The metadata sheet is a flat list of every field in every table, with the tables
one after another. **There is no column identifying which table a row belongs
to.**

Instead, after fully blank rows are dropped, each new table starts at a row with
an empty `Data Type` cell, and that row's `Field Name` cell holds the table name.
All rows up to the next such boundary row belong to that table.

`nwss_utils.splitup_metadata_sheet` implements this, adding a `_table` column
(`nwss_utils.TABLE_NAME_COL`) to each table it returns. A sheet with no boundary
row at all is treated as one table named `nwss`
(`nwss_utils.SINGLE_TABLE_NAME`).

The columns the generator reads are listed in `nwss_utils.DictionaryColumns`:
`Field Name`, `Data Type`, `Value Set`, `Field`, `Value Set Name`, `Description`,
and `Submission Requirement`. Some dictionaries use `variable name` instead of
`Field Name`; both are handled.

### The `Value Sets` sheet runs side to side

The enumerations are laid out **side by side rather than stacked**. Each
enumeration occupies a pair of adjacent columns:

- the left column's header is the enumeration name, and its first cell reads
  `Value Set`
- the column to its right has `Description` in that first cell

`nwss_utils.parse_enums_sheet` finds enumerations by scanning every adjacent
column pair for that signature — there is no list of enumerations to read, so
they are discovered structurally.

The same sheet also carries a `Field` → `Value Set Name` mapping, which is what
tells the generator which enumeration each categorical field uses.

A permissible value written as `[empty]` in the source is a genuinely empty value,
and is converted to the `<empty>` sentinel described in
[post-processing workarounds](../explanation/how-it-works.md#empty-permissible-values).

### Data types are prose, not a vocabulary

NWSS describes a field's type in **free-text English** — "date", "time zone",
"NPDES permit number", "EPA Registry ID", strings of `#` characters — rather than
with a controlled vocabulary.

So `_get_range_and_validation_info` in `make_nwss_ss_classes` works in three
tiers:

1. A `Data Type` of `category` means the range is an enumeration, whose name is
   resolved by `nwss_utils.resolve_slot_enums` — see
   [which enumeration a field uses](#which-enumeration-a-field-uses) below. A
   categorical field with no enumeration anywhere logs an error and leaves the
   range unresolved.
2. Otherwise the prose is matched against the regex table
   `_data_types_validation_info`, which maps each description onto a LinkML range
   plus a validation `pattern`. This is how `date`, `time`, `time zone`,
   `ZIP code`, `NPDES permit number`, `EPA Registry ID`, and `jurisdiction id`
   acquire their regexes.
3. Failing that, a `Data Type` containing `#` characters becomes a regex by
   replacing each `#` with `[0-9]`. Anything else is copied through as the range
   unchanged.

What that costs, and why tier 3 is the one to watch, is in
[Data types are prose, not a vocabulary](../explanation/data-dictionaries.md#data-types-are-prose-not-a-vocabulary).

### Which enumeration a field uses

A NWSS dictionary names the enumeration for a categorical field in **two places**,
and they can disagree:

| Source | Looks like |
| --- | --- |
| The `Metadata` sheet's `Value Set` column | `[See Value Sets: vs_yn]` |
| The `Value Sets` sheet's `Field` → `Value Set Name` mapping | `vs_yne` |

**The `Metadata` sheet wins.** A disagreement is a defect in the published
dictionary, so it is logged as an error naming both candidates and the one
chosen. If you see it, report it upstream; you do not need to edit the workbook.

`nwss_utils.resolve_slot_enums` makes this decision, and is the **only** place it
is made. Both the enumeration Schemasheets (`make_nwss_ss_enums`) and the slot
ranges that refer to them (`make_nwss_ss_classes`) are built from what it
returns.

Why the `Metadata` sheet is the one trusted, and what went wrong when the two
steps resolved the name independently, is in
[Why the `Metadata` sheet wins](../explanation/data-dictionaries.md#why-the-metadata-sheet-wins).
