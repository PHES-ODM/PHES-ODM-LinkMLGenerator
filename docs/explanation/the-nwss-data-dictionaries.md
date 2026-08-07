# The NWSS data dictionaries

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
[Prepare the NWSS data dictionaries](../how-to/prepare-the-nwss-dictionaries.md).

## The metadata sheet has implicit table boundaries

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

## The `Value Sets` sheet runs side to side

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
[post-processing workarounds](post-processing-workarounds.md).

## Data types are prose, not a vocabulary

This is the single most consequential difference from ODM. NWSS describes a
field's type in **free-text English** — "date", "time zone", "NPDES permit
number", "EPA Registry ID", strings of `#` characters — rather than with a
controlled vocabulary.

So `_get_range_and_validation_info` in `make_nwss_ss_classes` works in three
tiers:

1. A `Data Type` of `category` means the range is an enumeration. The name comes
   from the `Field` → `Value Set Name` mapping, falling back to the row's own
   `Value Set` column. A categorical field with no enumeration anywhere logs an
   error and leaves the range unresolved.
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

## Two behaviours that will surprise you

### Everything is one class

`make_nwss` always sets `single_table=True`, which concatenates every table in the
metadata sheet into **one class named `nwss`** rather than generating a class per
table.

The per-table path exists and is reachable through the individual step functions
and their CLIs (`--no-single-table`), but the top-level generator does not use it.
If you re-run the class extraction step by hand and get several classes, this is
why — the CLI default is off.

### Detailed enumeration names

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

See `nwss_utils.get_detailed_enums`.

## Related

- [NWSS pipeline steps](../reference/nwss-pipeline-steps.md)
- [Prepare the NWSS data dictionaries](../how-to/prepare-the-nwss-dictionaries.md)
  — the manual Excel fixes the published files need
- [Add support for a new NWSS dictionary type](../how-to/add-an-nwss-dictionary-type.md)
