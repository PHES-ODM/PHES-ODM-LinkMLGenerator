# Generate ODM schemas

The instructions for actually producing the schemas — obtaining the dictionary,
where to put it, and the commands for v1, v2, and v3 — are on the
[home page](index.md#generate-the-odm-schemas). This page covers how an ODM run
differs by version, and the one ODM-specific failure mode worth knowing about in
advance.

## v1 and v2+ are different pipelines

They share a name and nothing else:

| | ODM v1 | ODM v2+ |
| --- | --- | --- |
| Command | `odm-linkmlgen-odmv1` | `odm-linkmlgen-odm` |
| Source | Schemasheets TSVs bundled in the package | An Excel data dictionary you supply |
| Stages run | Stage 3 only | All three |
| Output | `linkml/odm_v1.yaml` and nothing else | `dictionary/`, `schemasheets/`, and `linkml/` |

ODM v1's TSVs are written and maintained by hand, in
`odm_linkmlgen/data/odm_v1/schemasheets/`. They are read in place and never
copied into `--output-dir`. So a change to the v1 schema is an edit to those
TSVs, not to any extraction code — nothing in `odm_linkmlgen/odm/` runs for v1
at all.

For v2 and above, the parts sheet of the Excel dictionary drives everything; how
it encodes the data model is described in
[The source data dictionaries](data-dictionaries.md#the-odm-data-dictionary).
The full v2+ output layout, including the asymmetry in how enumeration TSVs are
grouped, is in the
[output layout reference](reference/layouts.md#odm-v2).

## Enumeration names are derived, not looked up

The ODM-specific thing to know before your first v2+ run: a slot's enumeration
name is *derived* from its `partID` by appending `s`, rather than read from a
column. Names that do not follow that convention have to be listed in
`odm_utils._odm_enum_name_exceptions`.

When derivation fails, the run does not stop. The name simply does not resolve,
the slot's range falls back to `string`, and an error goes to the log — which is
why the [check step](index.md#check-the-odm-result) matters.

## Related

- [Generate the ODM schemas](index.md#generate-the-odm-schemas) — the dictionary
  and the commands
- [Add support for a new ODM version](extending.md#add-support-for-a-new-odm-version)
- [Use it from Python](python-api.md) — the same thing from Python, returning a
  `SchemaDefinition`
- [ODM pipeline steps](reference/pipeline-steps.md#odm-pipeline-steps) — what
  each of the eleven steps does
- [The ODM data dictionary](data-dictionaries.md#the-odm-data-dictionary) — how
  the parts sheet encodes the data model
