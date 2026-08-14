# Generate the NWSS schemas

NWSS is published as five separate dictionaries, each an Excel workbook
producing its own independent schema. You need only the ones you intend to
generate from. [Install the generator](install.md) first.

## Get the dictionaries

Three of the five are public. Download them from the CDC's
[Wastewater Surveillance Data Reporting and Analytics](https://archive.cdc.gov/www_cdc_gov/nwss/reporting.html)
page, from the **Data Dictionaries** box:

| Dictionary type | CLI option | Publicly available |
| --- | --- | --- |
| NWSS Reporting | `--reporting` | Yes |
| Public Concentration | `--public-concentration` | Yes |
| Public Metric | `--public-metric` | Yes |
| Restricted Raw | `--restricted-raw` | No |
| Restricted Analytics | `--restricted-analytics` | No |

The two restricted dictionaries must be obtained from the CDC directly.

NWSS dictionary files are git-ignored (`/odm_linkmlgen/data/nwss/*.xlsx`), so
nothing is bundled with the repository. Put your copies anywhere and point the
CLI at them; by convention that is `odm_linkmlgen/data/nwss/`.

## Apply the manual fixes

Several published dictionaries contain defects that must be corrected in Excel
before they will process correctly. **These are defects in the published files,
not in the generator**, and the list will change as the CDC republishes.

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

No longer needs fixing by hand. Where the `Value Sets` sheet and the `Metadata`
sheet name different value sets for the same field — `ntc_amplify` and
`pretreatment` have both done this — the generator takes the `Metadata` sheet's
name and logs an error identifying the field and both candidates. See
[which enumeration a field uses](../reference/data-dictionaries.md#which-enumeration-a-field-uses).
Report it upstream rather than editing the workbook.

### `public_metric` — invalid permissible values

In the `vs_reporting_jurisdiction` value set:

- change `Chicago, IL` to `Chicago`
- change `Houston, TX` to `Houston`
- remove the individual states from the permissible values

Left as published, sample data will fail validation against the generated
schema.

!!! note "Known limitation"

    Independent of the source files: validation information in the `Value Set`
    column of the metadata sheet is **not yet used** by the generator.

## Generate the schemas from the dictionaries you have

Every dictionary option is optional, and each one you pass generates one
independent schema. Supply only the dictionaries you actually have:

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "odm_linkmlgen/data/nwss/reporting.xlsx" \
    --public-concentration "odm_linkmlgen/data/nwss/public_concentration.xlsx" \
    --public-metric "odm_linkmlgen/data/nwss/public_metric.xlsx"
```

A subdirectory is created per dictionary type, so the reporting run above writes
its schema to:

```text
gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml
```

There is no separate command per type — to generate just one, pass just one
option.

## Check the NWSS result

`ERROR` lines in the log are expected and are not failures: a bad row is logged
and skipped so that it cannot abort the whole run. But they do mean the schema
is degraded, usually with an unresolved range on a categorical slot. Scan for
them:

```console
odm-linkmlgen-nwss --output-dir "gen/nwss" --reporting ... 2>&1 \
    | tee gen/nwss/generate.log
grep ERROR gen/nwss/generate.log
```

An error naming a categorical field almost always means its enumeration is
missing from the `Value Sets` sheet — check the
[manual fixes](#apply-the-manual-fixes) first, since the published dictionaries
are the usual culprit.

## Related

- [Inside an NWSS run](../explanation/nwss-runs.md) — what the run left on disk,
  and why the output looks the way it does
- [The NWSS data dictionaries](../reference/data-dictionaries.md#the-nwss-data-dictionaries)
- [Use it from Python](python-api.md) — the same thing from Python, returning a
  `SchemaDefinition` per dictionary type
- [Troubleshooting](troubleshooting.md) — when the result is not what you
  expected
