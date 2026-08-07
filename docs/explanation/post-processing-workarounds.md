# Post-processing workarounds

Going via Schemasheets means inheriting Schemasheets' limitations. Three things
are therefore corrected *after* generation, working directly on the
`SchemaDefinition` rather than on the TSVs.

Two of them matter because each has a **matching convention earlier in the
pipeline**. If you only know about one half, the other half looks like a bug.

## In `fix_schemasheets_generated_schema`

`schemasheets_utils.fix_schemasheets_generated_schema` runs as part of
`make_linkml_schema_from_schemasheets`, so both pipelines get it.

### Empty permissible values

Both dictionaries need genuinely empty permissible values — an enumeration where
`""` is a legitimate choice, used for "not applicable" and similar.

Schemasheets cannot express this. It treats a blank `permissible_value` cell as
**metadata for the enumeration itself** rather than as a permissible value equal
to `""`. That behaviour is relied on elsewhere: it is exactly how the extraction
modules attach an enumeration's own title and description, by writing a row with
no permissible value.

So the two meanings collide, and the pipeline splits them apart by convention:

1. The extraction modules write the sentinel
   `general_utils.EMPTY_PERMISSIBLE_VALUE` — the literal string `<empty>` — where
   a genuinely empty permissible value is meant.
2. A truly blank cell keeps its Schemasheets meaning: enumeration-level metadata.
3. Post-processing replaces every `<empty>` with `""`.

NWSS sources spell this `[empty]` in the `Value Sets` sheet, which the NWSS
extraction converts to the `<empty>` sentinel on the way through.

!!! warning "The symptom"

    A `permissible_value` of `<empty>` surviving into the final YAML means step 3
    did not run, or ran before that value was added. The sentinel is never
    supposed to be visible in the output.

### Numeric bounds as strings

Schemasheets emits `minimum_value` and `maximum_value` as **strings**, which
breaks downstream LinkML tools — the validator among them, which is one of the
main things anyone wants to do with these schemas.

Post-processing converts them to `int` or `float`.

!!! warning "The symptom"

    A `minimum_value` still quoted as a string in the final YAML.

### Comma-separated multi-range strings

The same function also splits a comma-separated `range` string into a list, for
slots that accept more than one range. This is a convenience for the extraction
modules, which can write multiple ranges into one cell rather than needing a
Schemasheets construct for it.

## In `add_missingness_set` (ODM only)

`odm_utils.add_missingness_set` is applied by the ODM pipeline after
`make_linkml_schema_from_schemasheets`, and has no NWSS equivalent.

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet` — **in addition to** their normal range, so a value can be
reported as missing for a documented reason. The parts sheet records this in its
`missingnessSet` column.

No Schemasheets column expresses "add this range as well", so it cannot be done
in stage 2 at all. For every slot usage whose part has a `missingnessSet`, that
enumeration is added to the slot's ranges afterwards.

A slot that ends up with more than one range is written as LinkML **`any_of`**
rather than a single `range` — see `odm_utils.set_range_of_slot`.

!!! warning "The symptom"

    A missing `any_of` where a missingness set was expected.

### The knock-on effect on reading schemas

This is why an ODM slot may have **no `range` key at all**, and why
`schema_utils.get_ranges_of_slot` exists: it unpacks both shapes, where reading
`.range` directly would return `None` for exactly the slots that are most
interesting. Prefer it in any code consuming these schemas.

## Why not fix Schemasheets instead?

For the numeric bounds, upstream is the right place, and a fix there would let
that workaround be deleted. The empty-permissible-value collision is more
awkward: blank-cell-means-enumeration-metadata is deliberate Schemasheets
behaviour that this project depends on, so there is no fix that does not need
*some* sentinel convention on one side or the other.

## Related

- [How the pipeline is designed](pipeline-design.md) — where stage 3 sits
- [Debug a generated schema](../how-to/debug-a-generated-schema.md) — the
  symptoms above, as a checklist
- [LinkML and Schemasheets](linkml-and-schemasheets.md) — why the project goes
  via TSVs at all
