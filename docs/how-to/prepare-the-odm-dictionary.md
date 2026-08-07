# Prepare the ODM data dictionary

The ODM v2+ generator reads the official PHES-ODM Excel data dictionary. This
guide covers obtaining it and saving it safely.

ODM v1 needs none of this — its Schemasheets are bundled with the package.

## Obtain the file

The dictionary is **not publicly available** and is not committed to this
repository. Contact [Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a
copy.

## Save it in the right place

Name it `v# ODM dictionary.xlsx`, where `#` is the version number — for example
`v3 ODM dictionary.xlsx`.

By convention it goes in `odm_linkmlgen/data/odm_v{n}/`:

```console
mkdir -p odm_linkmlgen/data/odm_v3
cp "~/v3 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v3/
```

That directory is git-ignored (`/odm_linkmlgen/data/odm_v*/*.xlsx`), so your
copy stays local to your checkout and cannot be committed by accident. The
convention is only a convention — you can pass any path to `--dictionary-file`.

## Do not open it with an old version of Excel

!!! danger "Opening and resaving with an older Excel will corrupt the workbook"

    The dictionary relies on the `FILTER` and `XLOOKUP` functions, which older
    versions of Excel do not support. Opening the file in such a version and
    saving it silently destroys those formulas, and the damage is not
    recoverable from the saved file.

    Use a recent version of Excel. If you only need to *look* at the file, use a
    viewer that will not write to it.

## Next

[Generate an ODM schema](generate-an-odm-schema.md).
