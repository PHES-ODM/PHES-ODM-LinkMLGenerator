# Generate the ODM schemas

Everything needed to produce an ODM schema — for v1, v2, or v3 — is on this
page. [Install the generator](install.md) first.

## ODM v1

ODM v1 needs no source Excel file — its Schemasheets are bundled with the
package, so this runs offline in a couple of seconds:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

## Prepare the dictionary for v2 and above

ODM v2 and v3 use the same command; only `--version` and the dictionary change.
Both read the official PHES-ODM Excel data dictionary.

**Obtain the file.** The dictionary is **not publicly available** and is not
committed to this repository. Contact
[Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a copy.

!!! danger "Opening and resaving with an older Excel will corrupt the workbook"

    The dictionary relies on the `FILTER` and `XLOOKUP` functions, which older
    versions of Excel do not support. Opening the file in such a version and
    saving it silently destroys those formulas, and the damage is not
    recoverable from the saved file.

    Use a recent version of Excel. If you only need to *look* at the file, use a
    viewer that will not write to it.

**Save it in the right place.** Name it `v# ODM dictionary.xlsx`, where `#` is
the version number. By convention it goes in `odm_linkmlgen/data/odm_v{n}/`:

```console
mkdir -p odm_linkmlgen/data/odm_v2 odm_linkmlgen/data/odm_v3
cp "~/v2 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v2/
cp "~/v3 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v3/
```

Those directories are git-ignored (`/odm_linkmlgen/data/odm_v*/*.xlsx`), so your
copy stays local to your checkout and cannot be committed by accident. The
convention is only a convention — you can pass any path to `--dictionary-file`.

## Generate v2 and v3

```console
odm-linkmlgen-odm \
    --version 2 \
    --dictionary-file "odm_linkmlgen/data/odm_v2/v2 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v2"

odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The schemas are written to `gen/odm_v2/linkml/odm_v2.yaml` and
`gen/odm_v3/linkml/odm_v3.yaml`, alongside the intermediate `dictionary/` and
`schemasheets/` directories described in the
[output layout reference](../reference/output-layout.md).

`--version` is a bare version number (`2`, `3`, …). It is not just a label: it
determines the generated schema's name (`ODMv3`), id
(`https://onto.phes-odm.org/odm/v3`), and CURIE prefix (`odmv3`), so it must
match the dictionary you passed.

## Check the ODM result

Errors in the source dictionary are logged and skipped rather than raised, so a
run that "succeeded" can still have produced a degraded schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --dictionary-file ... --output-dir ... 2>&1 \
    | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

If you are generating a version that has not been generated before, work through
[Extend the generator](extending.md#add-support-for-a-new-odm-version) as well.

## Related

- [Inside an ODM run](../explanation/odm-runs.md) — what the run left on disk,
  and how v1 and v2+ differ
- [The ODM data dictionary](../explanation/data-dictionaries.md#the-odm-data-dictionary)
  — how the parts sheet encodes the data model
- [Use it from Python](python-api.md) — the same thing from Python, returning a
  `SchemaDefinition`
- [Troubleshooting](troubleshooting.md) — when the result is not what you
  expected
