# Generate an ODM schema

## ODM v1

ODM v1's Schemasheets are bundled with the package, so no source Excel file is
needed:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

## ODM v2 and above

First [prepare the data dictionary](prepare-the-odm-dictionary.md). Then:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The schema is written to `gen/odm_v3/linkml/odm_v3.yaml`, alongside the
intermediate `dictionary/` and `schemasheets/` directories described in the
[output layout reference](../reference/output-layout.md).

`--version` is a bare version number (`2`, `3`, …). It is not just a label: it
determines the generated schema's name (`ODMv3`), id
(`https://onto.phes-odm.org/odm/v3`), and CURIE prefix (`odmv3`), so it must
match the dictionary you passed.

## Check the result

Errors in the source dictionary are logged and skipped rather than raised, so a
run that "succeeded" can still have produced a degraded schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --dictionary-file ... --output-dir ... 2>&1 \
    | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

The symptom to look for in the schema itself is a slot whose range silently fell
back to `string` — that means an enumeration name could not be resolved. See
[Debug a generated schema](debug-a-generated-schema.md).

If you are generating a version that has not been generated before, work through
[Add support for a new ODM version](add-an-odm-version.md) as well.

## Related

- [Use the generator as a Python library](use-as-a-python-library.md) — the same
  thing from Python, returning a `SchemaDefinition`
- [ODM pipeline steps](../reference/odm-pipeline-steps.md) — what each of the
  eleven steps does
- [The ODM data dictionary](../explanation/the-odm-data-dictionary.md) — how the
  parts sheet encodes the data model
