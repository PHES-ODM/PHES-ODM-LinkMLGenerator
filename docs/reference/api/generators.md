# Top-level generators

The three CLI entry points. Each orchestrates every processing step of its
pipeline in sequence.

| Module | Installed command | Function form |
| --- | --- | --- |
| `make_odm` | `odm-linkmlgen-odm` | Yes — returns a `SchemaDefinition` |
| `make_odm_v1` | `odm-linkmlgen-odmv1` | No — CLI only |
| `make_nwss` | `odm-linkmlgen-nwss` | Yes |

For the step-by-step account of what each one runs, see
[ODM pipeline steps](../odm-pipeline-steps.md) and
[NWSS pipeline steps](../nwss-pipeline-steps.md).

## `odm_linkmlgen.make_odm`

Generates the ODM v2+ LinkML schema.

::: odm_linkmlgen.make_odm
    options:
      members:
        - make_odm

## `odm_linkmlgen.make_odm_v1`

Generates the ODM v1 schema from the Schemasheets bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/`. No source Excel file is involved, so
this is only the final Schemasheets step.

There is no `make_odm_v1` function — the module is a CLI only. To do the
equivalent from Python, call
[`make_linkml_schema_from_schemasheets`](utils.md#odm_linkmlgen.utils.schemasheets_utils.make_linkml_schema_from_schemasheets)
over the bundled directory; see
[Use the generator as a Python library](../../how-to/use-as-a-python-library.md#odm-v1).

::: odm_linkmlgen.make_odm_v1
    options:
      members: []
      show_source: false

## `odm_linkmlgen.make_nwss`

Runs the full pipeline once per dictionary type supplied. Because it may generate
several schemas in one call, it writes files rather than returning a schema.

::: odm_linkmlgen.make_nwss
    options:
      members:
        - make_nwss
