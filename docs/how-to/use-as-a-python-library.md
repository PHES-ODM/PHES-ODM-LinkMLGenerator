# Use the generator as a Python library

Every generator is a plain function as well as a CLI command. Use the function
form when you want the `SchemaDefinition` object back rather than just a file on
disk.

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

There is no `make_odm_v1` function, only the CLI. To do the equivalent from
Python, run the final Schemasheets step over the bundled TSVs yourself:

```python
from pathlib import Path

import odm_linkmlgen
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
)

schemasheets_dir = (
    Path(odm_linkmlgen.__file__).parent / "data" / "odm_v1" / "schemasheets"
)
schema = make_linkml_schema_from_schemasheets(
    schemasheets_dir, "gen/odm_v1/linkml/odm_v1.yaml"
)
```

## NWSS

```python
from odm_linkmlgen.make_nwss import make_nwss

make_nwss(
    output_dir="gen/nwss",
    reporting="path/to/reporting.xlsx",
)
```

Pass one keyword argument per dictionary type you have (`reporting`,
`public_concentration`, `public_metric`, `restricted_raw`,
`restricted_analytics`). Because it may generate several schemas in one call, it
writes files rather than returning a single schema.

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

## Running the individual steps

Every step of both pipelines is independently importable. See
[Re-run a single pipeline step](run-a-single-pipeline-step.md), which includes a
worked example reproducing `make_odm` step by step.

## Related

- [Python API reference](../reference/api/index.md) — every module and function,
  generated from the source
