# Re-run a single pipeline step

Every step of both pipelines is both an importable function and a standalone
CLI. Re-running one step against the CSVs already in `dictionary/` takes a
moment, where rebuilding from Excel takes far longer — this is the loop to work
in when adapting the generator to a new dictionary.

## From the command line

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
[ODM](../reference/odm-pipeline-steps.md) and
[NWSS](../reference/nwss-pipeline-steps.md) step references list every module,
its inputs, and its outputs.

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

## From Python

The following reproduces `make_odm` exactly, and is the starting point for
experimenting with an individual step:

```python
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.odm.odm_utils import add_missingness_set
from odm_linkmlgen.utils.general_utils import clear_dirs, extract_sheets
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
    save_schema_definition,
)

version = "3"
dictionary_file = f"odm_linkmlgen/data/odm_v{version}/v{version} ODM dictionary.xlsx"
output_dir = f"gen/odm_v{version}"
dictionary_dir = f"{output_dir}/dictionary"
schemasheets_dir = f"{output_dir}/schemasheets"
linkml_dir = f"{output_dir}/linkml"
parts_file = f"{dictionary_dir}/parts.csv"
sets_file = f"{dictionary_dir}/sets.csv"

# 1. Remove any stale csv/tsv/yaml files from a previous run
clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

# 2. Extract the sheets from Excel to CSV. The na_values argument keeps partID
#    values such as "NA" and "None" as literal strings rather than NA values.
extract_sheets(
    dictionary_file,
    ["parts", "sets"],
    dictionary_dir,
    na_values={"parts": {"partID": ""}, "sets": {"partID": ""}},
)

# 3 & 4. Extract the enumerations, first from the sets sheet (the mmaSet enums),
#        then the remaining ones from the parts sheet
all_enums = extract_sets_enums(
    sets_file, parts_file, f"{schemasheets_dir}/enums_sets.tsv"
)
all_enums += extract_parts_enums(parts_file, f"{schemasheets_dir}/enums_parts.tsv")
all_enums = list(dict.fromkeys(all_enums))

# 5. Extract the classes (one Schemasheet per ODM table)
extract_all_classes(parts_file, schemasheets_dir, recognized_enums=all_enums)

# 6, 7, 8. Container class, prefixes, and schema metadata
extract_container_class(parts_file, f"{schemasheets_dir}/container.tsv")
make_prefixes(f"{schemasheets_dir}/prefixes.tsv", version)
make_schema(f"{schemasheets_dir}/schema.tsv", version)

# 9. Run Schemasheets over all the generated TSV files
schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

# 10. Add the missingness enumerations
add_missingness_set(schema, parts_file)

# 11. Save the final LinkML schema
save_schema_definition(schema, f"{linkml_dir}/odm_v{version}.yaml")
```

To experiment with one step, comment out the ones before it — their outputs are
already on disk from the last full run.

## Related

- [Debug a generated schema](debug-a-generated-schema.md)
- [Python API reference](../reference/api/index.md)
- [How the pipeline is designed](../explanation/pipeline-design.md) — why every
  step is independently runnable
