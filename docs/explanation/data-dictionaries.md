# Why the dictionaries are hard to read

The two source dictionaries are irregular in different ways, and **most of the
project's complexity is a response to that**. This page is about what those
irregularities cost, and what they silently break.

[The source data dictionaries](../reference/data-dictionaries.md) describes what
the generator is reading, sheet by sheet and column by column;
[How it works](how-it-works.md) describes what it does with it.

## The ODM dictionary

### A row's meaning comes from its neighbours

Almost everything the generator needs is in the parts sheet, and it is the harder
of the two to read. **A row's meaning is determined by its relationships to other
columns rather than by a single "kind" column.** That one fact accounts for most
of the ODM pipeline's complexity.

Table membership is the clearest case. Rather than a column naming the table a
row belongs to, each ODM table gets its own
[`{table}` / `{table}Required` / `{table}Order` column trio](../reference/data-dictionaries.md#table-membership),
and a row joins the table by carrying a `pK`, `fK`, or `header` tag in the first
of them.

This is a wide, sparse encoding: adding a table adds three columns to the sheet
rather than rows. It is also why the same part can belong to several tables with
different constraints in each, which in turn is why the generated schemas lean so
heavily on LinkML's
[`slot_usage`](how-it-works.md#two-linkml-details-that-show-up-everywhere).

It pays for itself in one place. Because the generator
[discovers tables](../reference/data-dictionaries.md#discovering-the-tables) by
scanning for column headers ending in `Order` rather than from a hardcoded list,
a new table in a new dictionary version is picked up automatically, with no code
change.

### Why enumeration-name derivation needs a safety net

An enumeration defined in the parts sheet has no column naming it: the name is
[derived from the part ID](../reference/data-dictionaries.md#defined-in-the-parts-sheet),
usually by appending an `s`. Deriving a name by string manipulation can obviously
produce a name that nothing defines. `odm_get_enum_name_from_part_id` therefore
takes an optional `recognized_enums` list, and **returns `"string"` when the
derived name is not in it**. So an enumeration that could not be extracted
degrades to an unconstrained string rather than a dangling reference to a
non-existent enumeration.

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

## The NWSS dictionaries

NWSS dictionaries are **less regular than the ODM one**, and some require manual
repair before they can be processed at all — see
[the manual fixes](../how-to/generate-nwss-schemas.md#apply-the-manual-fixes).

### Table boundaries are formatting, not data

The metadata sheet has no column saying which table a row belongs to. Instead,
[a row with an empty `Data Type` cell](../reference/data-dictionaries.md#the-metadata-sheet-has-implicit-table-boundaries)
starts a new table, and its `Field Name` cell holds that table's name.

This is a formatting convention rather than data, which makes it fragile: a stray
value in a `Data Type` cell, or a missing one, silently changes the table
structure. It is worth checking `dictionary/metadata.csv` when a table looks
wrong.

### Data types are prose, not a vocabulary

This is the single most consequential difference from ODM. NWSS describes a
field's type in **free-text English** — "date", "time zone", "NPDES permit
number", "EPA Registry ID", strings of `#` characters — rather than with a
controlled vocabulary, so the generator
[matches that prose against a table of regexes](../reference/data-dictionaries.md#data-types-are-prose-not-a-vocabulary)
rather than looking a type up.

The last of the three tiers is the silent-failure case: an unmatched data type is
copied through as the range unchanged, becoming a dangling range rather than an
error.

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

### Why the `Metadata` sheet wins

A NWSS dictionary names the enumeration for a categorical field in
[two places](../reference/data-dictionaries.md#which-enumeration-a-field-uses) —
the `Metadata` sheet's `Value Set` column, and the `Value Sets` sheet's `Field` →
`Value Set Name` mapping — and they can disagree.

The `Metadata` sheet is the one trusted. It is the more complete of the two —
fields missing from the `Value Sets` sheet mapping are common, the reverse is not
— and in the one documented case of the two disagreeing, the `Metadata` sheet held
the correct name.

That the decision is made in exactly one place, `nwss_utils.resolve_slot_enums`,
matters more than it sounds. When the two steps each resolved the name
independently, a disagreement between the sheets produced a schema where the
enumeration was generated under one name and the range pointed at the other — an
orphan enumeration and a dangling range, in a schema that still loaded without
complaint. `make_nwss` now also checks every range against the finished schema with
`schema_utils.find_undefined_ranges`, and logs an error for any that does not
resolve.
