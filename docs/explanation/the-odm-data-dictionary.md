# The ODM data dictionary

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
of the ODM pipeline's complexity, so it is worth understanding before reading the
[step reference](../reference/odm-pipeline-steps.md).

## The columns that carry meaning

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

## Table membership

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
[`slot_usage`](linkml-and-schemasheets.md#two-linkml-details-that-show-up-everywhere).

### Discovering the tables

The generator **does not hardcode the list of ODM tables.**
`odm_utils.odm_get_available_class_names` finds them by scanning the parts sheet
column headers for any name ending in `Order` — the value of
`odm_utils.ODM_PARTS_COLUMN_CLASS_TAG` — and stripping that suffix. So
`measuresOrder` implies a table named `measures`.

The payoff is that a new table in a new dictionary version is picked up
automatically, with no code change, as long as it has the full
`{table}` / `{table}Required` / `{table}Order` trio. See
[Add support for a new ODM version](../how-to/add-an-odm-version.md).

## Enumerations

A part whose `dataType` is `categorical` has an enumeration as its range. That
enumeration is defined in one of two places, and which one determines how the
generator finds its name and values:

### Defined in the sets sheet

If `mmaSet` is set, the permissible values are in the **sets** sheet and `mmaSet`
holds the enumeration's name directly. Nothing needs deriving. In the sets sheet,
`setID` is the enumeration name and `partID` is a permissible value.

### Defined in the parts sheet

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

### Why derivation needs a safety net

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

## Missingness sets

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet`, and so on — *in addition to* their normal range, so that a
value can be reported as missing for a documented reason rather than just being
absent.

The parts sheet records this in the `missingnessSet` column. No Schemasheets
column expresses "add this range as well", so it is applied afterwards, directly
on the `SchemaDefinition`, by `odm_utils.add_missingness_set`. A slot that ends up
with more than one range is written as LinkML `any_of` rather than a single
`range` — which is why reading `.range` directly on an ODM slot is unreliable, and
why `schema_utils.get_ranges_of_slot` exists.

## Related

- [ODM pipeline steps](../reference/odm-pipeline-steps.md) — what each step does
  with all of the above
- [Prepare the ODM data dictionary](../how-to/prepare-the-odm-dictionary.md) —
  obtaining the file, and the Excel version warning
- [Post-processing workarounds](post-processing-workarounds.md)
