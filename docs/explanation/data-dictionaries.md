# The source data dictionaries

The two source dictionaries are irregular in different ways, and **most of the
project's complexity is a response to that**. This page describes what the
generator is reading; [How it works](how-it-works.md) describes what it does
with it.

## The ODM data dictionary

The PHES-ODM data dictionary is an Excel workbook that authoritatively defines
every table, field, and permissible value in the ODM. The generator reads two of
its sheets:

- **parts** — one row per "part". A part can be a table, a column, an
  enumeration, or a permissible value of an enumeration. This sheet defines all
  classes and slots, along with their data types and constraints.
- **sets** — the permissible values for many (not all) of the enumerations.

Almost everything the generator needs is in the parts sheet, and it is the harder
of the two to read. **A row's meaning is determined by its relationships to other
columns rather than by a single "kind" column.** That one fact accounts for most
of the ODM pipeline's complexity.

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

This is a wide, sparse encoding: adding a table adds three columns to the sheet
rather than rows. It is also why the same part can belong to several tables with
different constraints in each, which in turn is why the generated schemas lean so
heavily on LinkML's
[`slot_usage`](how-it-works.md#two-linkml-details-that-show-up-everywhere).

#### Discovering the tables

The generator **does not hardcode the list of ODM tables.**
`odm_utils.odm_get_available_class_names` finds them by scanning the parts sheet
column headers for any name ending in `Order` — the value of
`odm_utils.ODM_PARTS_COLUMN_CLASS_TAG` — and stripping that suffix. So
`measuresOrder` implies a table named `measures`.

The payoff is that a new table in a new dictionary version is picked up
automatically, with no code change, as long as it has the full
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
is done by `odm_utils.odm_get_enum_name_from_part_id`.

#### Why derivation needs a safety net

Deriving a name by string manipulation can obviously produce a name that nothing
defines. `odm_get_enum_name_from_part_id` therefore takes an optional
`recognized_enums` list, and **returns `"string"` when the derived name is not in
it**. So an enumeration that could not be extracted degrades to an unconstrained
string rather than a dangling reference to a non-existent enumeration.

That is a deliberate trade, and it has a cost you need to know about: the failure
is silent. `make_odm` collects the names actually extracted from both sheets — via
`get_enum_names_from_sets` and `get_enum_names_from_parts`, which read `setID` and
`partType` respectively — de-duplicates them, and passes the result as
`recognized_enums`. **A slot whose range unexpectedly reads `string` is the
symptom of a missing exception entry**, and it is the first thing to look for when
a new dictionary version produces a surprising schema.

Note that this check is only as good as the list it is given. Running the class
extraction step by hand without `--recognized-enums` disables it entirely, and
every derived name is then used as-is.

### Missingness sets

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet`, and so on — *in addition to* their normal range, so that a
value can be reported as missing for a documented reason rather than just being
absent.

The parts sheet records this in the `missingnessSet` column. No Schemasheets
column expresses "add this range as well", so it is applied afterwards, directly
on the `SchemaDefinition`, by `odm_utils.add_missingness_set` — see
[post-processing workarounds](how-it-works.md#missingness-sets-odm-only).

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

NWSS dictionaries are **less regular than the ODM one**, and some require manual
repair before they can be processed at all — see
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

This is a formatting convention rather than data, which makes it fragile: a stray
value in a `Data Type` cell, or a missing one, silently changes the table
structure. It is worth checking `dictionary/metadata.csv` when a table looks
wrong.

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
[post-processing workarounds](how-it-works.md#empty-permissible-values).

### Data types are prose, not a vocabulary

This is the single most consequential difference from ODM. NWSS describes a
field's type in **free-text English** — "date", "time zone", "NPDES permit
number", "EPA Registry ID", strings of `#` characters — rather than with a
controlled vocabulary.

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

Tier 3's last clause is the silent-failure case: an unmatched data type becomes a
dangling range rather than an error.

Because the source is prose, **this is the most likely place to need attention
when a new dictionary version is published** — a new file may describe a familiar
type in unfamiliar words. The `@TODO` comments in `_data_types_validation_info`
mark patterns that are known to be too permissive.

### Two NWSS behaviours that will surprise you

#### Everything is one class

`make_nwss` always sets `single_table=True`, which concatenates every table in the
metadata sheet into **one class named `nwss`** rather than generating a class per
table.

The per-table path exists and is reachable through the individual step functions
and their CLIs (`--no-single-table`), but the top-level generator does not use it.
If you re-run the class extraction step by hand and get several classes, this is
why — the CLI default is off.

#### Detailed enumeration names

`make_nwss` passes `detailed_enum_names=["vs_yne", "vs_yn"]`, and the effect is
visible all over the generated schema: instead of one shared `vs_yne`
enumeration, there is a separate copy per field that uses it —
`vs_yne[stormwater_input]`, `vs_yne[ext_blank]`, and so on. The original
undifferentiated enumeration is dropped.

The reason is a downstream constraint rather than anything about NWSS itself.
`vs_yne` (yes/no/empty) and `vs_yn` (yes/no) are used by many different fields,
and **LinkML-Map allows only one mapping per enumeration range** — but the correct
mapping differs from field to field even when the range is identical. Two columns
that both have the `vs_yne` range may need their values mapped differently, and a
single shared enumeration gives the mapper no way to express that.

Giving each field its own enumeration name solves it, and has a secondary
benefit: each copy can carry its own per-field permissible value descriptions.

### Which enumeration a field uses

A NWSS dictionary names the enumeration for a categorical field in **two places**,
and they can disagree:

| Source | Looks like |
| --- | --- |
| The `Metadata` sheet's `Value Set` column | `[See Value Sets: vs_yn]` |
| The `Value Sets` sheet's `Field` → `Value Set Name` mapping | `vs_yne` |

**The `Metadata` sheet wins.** It is the more complete of the two — fields missing
from the `Value Sets` sheet mapping are common, the reverse is not — and in the one
documented case of the two disagreeing, the `Metadata` sheet held the correct name.

A disagreement is a defect in the published dictionary, so it is logged as an error
naming both candidates and the one chosen. If you see it, report it upstream; you do
not need to edit the workbook.

`nwss_utils.resolve_slot_enums` makes this decision, and is the **only** place it is
made. Both the enumeration Schemasheets (`make_nwss_ss_enums`) and the slot ranges
that refer to them (`make_nwss_ss_classes`) are built from what it returns.

That matters more than it sounds. When the two steps each resolved the name
independently, a disagreement between the sheets produced a schema where the
enumeration was generated under one name and the range pointed at the other — an
orphan enumeration and a dangling range, in a schema that still loaded without
complaint. `make_nwss` now also checks every range against the finished schema with
`schema_utils.find_undefined_ranges`, and logs an error for any that does not
resolve.
