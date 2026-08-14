# Use it from Python

Every generator is a plain function as well as a CLI command, and so is every
individual pipeline step. Use the function form when you want the
`SchemaDefinition` object back rather than just a file on disk, or when you are
iterating on one step of the pipeline.

For the full signatures see the [Python API reference](reference/api.md).

## ODM v2+

```python
from odm_linkmlgen.make_odm import make_odm

schema = make_odm(
    version="3",
    dictionary_file="path/to/v3 ODM dictionary.xlsx",
    output_dir="gen/odm_v3",
)
```

Returns a `linkml_runtime.linkml_model.meta.SchemaDefinition`, *in addition to*
writing `gen/odm_v3/linkml/odm_v3.yaml`. The intermediate `dictionary/` and
`schemasheets/` files are written too — the function is not a pure in-memory
path.

## ODM v1

```python
from odm_linkmlgen.make_odm_v1 import make_odm_v1

schema = make_odm_v1(output_dir="gen/odm_v1")
```

Returns a `SchemaDefinition`, *in addition to* writing
`gen/odm_v1/linkml/odm_v1.yaml`. There is no source Excel file — the
Schemasheets TSVs are bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/` and are read in place, so no
`dictionary/` or `schemasheets/` files are written to `output_dir`.

## NWSS

```python
from odm_linkmlgen.make_nwss import make_nwss

schemas = make_nwss(
    output_dir="gen/nwss",
    reporting="path/to/reporting.xlsx",
    public_metric="path/to/public_metric.xlsx",
)

reporting_schema = schemas["reporting"]
```

Pass one keyword argument per dictionary type you have (`reporting`,
`public_concentration`, `public_metric`, `restricted_raw`,
`restricted_analytics`). Because it may generate several schemas in one call, it
returns a `dict` of them keyed by dictionary type rather than a single schema —
alongside writing `gen/nwss/nwss_{type}/linkml/nwss_{type}.yaml` for each. Only
the types you supplied are keys, so iterate the result rather than assuming a
particular one is there:

```python
for dictionary_type, schema in schemas.items():
    print(dictionary_type, len(schema.classes))
```

## Inspecting a generated schema

`odm_linkmlgen.utils.schema_utils` has read-only helpers for working with the
result, which handle the `slot_usage` and `any_of` shapes this project's schemas
make heavy use of.

These take a `SchemaView`, not the `SchemaDefinition` that `make_odm` returns,
so wrap it first:

```python
from linkml_runtime import SchemaView

from odm_linkmlgen.utils.schema_utils import get_ranges_of_slot, get_slot_definition

view = SchemaView(schema)  # or SchemaView("gen/odm_v3/linkml/odm_v3.yaml")

# The fully induced slot definition, with slot_usage overrides applied
slot = get_slot_definition("measures", "siteID", view)

# The range(s) of a slot, unpacking any_of into a list
ranges = get_ranges_of_slot("measures", "siteID", view)
```

Note the argument order: the class and slot names come first, and the schema
last.

`get_ranges_of_slot` is the one to reach for rather than reading `.range`
directly: a slot that accepts a missingness enumeration alongside its normal
range is written as `any_of`, and has no `range` at all. Both helpers raise on
an unknown class or slot unless you pass `exception_on_error=False`.

## Re-run a single step

Every step of both pipelines is both an importable function and a standalone
CLI. Re-running one step against the CSVs already in `dictionary/` takes a
moment, where rebuilding from Excel takes far longer — this is the loop to work
in when adapting the generator to a new dictionary.

### From the command line

```console
python -m odm_linkmlgen.odm.<module> --help
python -m odm_linkmlgen.nwss.<module> --help
```

For example, rebuild only the ODM class Schemasheets:

```console
python -m odm_linkmlgen.odm.make_odm_ss_classes \
    --parts-file "gen/odm_v3/dictionary/parts.csv" \
    --output-dir "gen/odm_v3/schemasheets"
```

Then re-run the final Schemasheets stage over the result. The
[pipeline steps reference](reference/pipeline-steps.md) lists every module, its
inputs, and its outputs.

!!! warning "A step's CLI defaults are not what the top-level generator passes"

    Running a step by hand does not reproduce what `make_odm` or `make_nwss` did
    unless you pass the same arguments. Two that catch people out:

    - **`--recognized-enums`** (ODM classes) is omitted by default, which
        disables the check that a derived enumeration name actually exists. Every
        derived name is then used as-is, so the TSVs can reference enumerations
        that no other Schemasheet defines.
    - **`--single-table`** (NWSS classes) defaults to *off*, but `make_nwss`
        always passes it. Without it you get one class per table instead of the
        merged `nwss` class.

!!! warning "`clear_dirs` only runs at the start of a full pipeline"

    A partial re-run leaves the other TSVs in place. That is what you want when
    iterating — but it also means that if you rename an output, the orphaned
    old TSV stays on disk and Schemasheets will still pick it up. Delete stale
    files by hand, or do a full run to clear them.

### From Python

The best starting point for experimenting with an individual step is the source
of `make_odm` itself:

[odm_linkmlgen/make_odm.py on GitHub](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/odm_linkmlgen/make_odm.py)

Read it step-by-step alongside the
[pipeline steps reference](reference/pipeline-steps.md), which describes what
each step reads and writes. Then, rather than calling `make_odm`, copy its body
into a script of your own and work in that: comment out the steps you are not
interested in, change the arguments a step is given, or drop your own code in
between two of them.

Because every step reads and writes files, the ones you comment out are already
accounted for by the outputs left on disk from your last full run — so
commenting out everything before the step you are working on is the fastest way
to iterate on it.

The equivalent for NWSS is
[odm_linkmlgen/make_nwss.py](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/odm_linkmlgen/make_nwss.py),
whose body is the same idea wrapped in a loop over the dictionary types.
