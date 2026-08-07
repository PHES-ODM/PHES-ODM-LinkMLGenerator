# Prepare the NWSS data dictionaries

NWSS is published as five separate dictionaries. You need only the ones you
intend to generate schemas from.

## Download the public dictionaries

Three of the five are public. Download them from the CDC's
[Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html)
page, from the **Data Dictionaries** box:

| Dictionary type | Publicly available |
| --- | --- |
| Main reporting | Yes |
| Public concentration | Yes |
| Public metric | Yes |
| Restricted raw | No |
| Restricted analytics | No |

The two restricted dictionaries must be obtained from the CDC directly.

NWSS dictionary files are git-ignored (`/odm_linkmlgen/data/nwss/*.xlsx`), so
nothing is bundled with the repository. Put your copies anywhere and point the
CLI at them; by convention that is `odm_linkmlgen/data/nwss/`.

## Apply the manual fixes

Several published dictionaries contain defects that must be corrected in Excel
before they will process correctly. **These are defects in the published files,
not in the generator** — there is nothing to fix in this repository, and the
list will change as the CDC republishes.

### `restricted_analytics` — no `Value Sets` sheet

Copy the `Value Sets` sheet from the restricted **raw** dictionary into the
restricted **analytics** workbook.

Even after doing this, some value sets are still missing. The categorical fields
`pcr_gene_target_agg`, `pcr_target_below_lod`, `pcr_target_units`, and
`quality_flag` have no enumeration definition anywhere. Each logs an error
during generation and produces a slot with an unresolved range.

### `restricted_raw` — misnamed value set

In the `Value Sets` sheet, rename `other_norm_units` to `other_norm_unit`, so it
matches the name of the field that uses it.

### `reporting` — misnamed value set

In the `Value Sets` sheet, change `ntc_amplify` from `vs_yne` to `vs_yn`.

### `public_metric` — invalid permissible values

In the `vs_reporting_jurisdiction` value set:

- change `Chicago, IL` to `Chicago`
- change `Houston, TX` to `Houston`
- remove the individual states from the permissible values

Left as published, sample data will fail validation against the generated
schema.

## Known limitation

Independent of the source files: validation information in the `Value Set`
column of the metadata sheet is **not yet used** by the generator.

## Next

[Generate NWSS schemas](generate-nwss-schemas.md).
