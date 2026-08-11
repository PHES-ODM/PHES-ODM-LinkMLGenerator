# PHES-ODM LinkML Schema Generator

This project turns Excel data dictionaries into [LinkML](https://linkml.io/)
schemas for two wastewater surveillance datasets:

- **[PHES-ODM](https://phes-odm.org)** — the Public Health Environmental
  Surveillance Open Data Model (versions 1, 2, and 3+)
- **[CDC NWSS](https://www.cdc.gov/nwss/wastewater-surveillance.html)** — the
  Centers for Disease Control and Prevention National Wastewater Surveillance
  System

The output is a single `.yaml` LinkML schema per dataset — per ODM version, or
per NWSS dictionary type. Those schemas can then be used by any LinkML tool: to
validate a data file, or to generate documentation, JSON Schema, SQL DDL, or
Python classes.

Everything needed to generate every schema is on this page. If you would rather
work through a guided first run, start with
[Getting started](getting-started.md) instead.

## Install

Requires Python 3.10 or newer.

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

This registers three commands:

| Command | Generates |
| --- | --- |
| `odm-linkmlgen-odmv1` | The ODM v1 schema |
| `odm-linkmlgen-odm` | An ODM v2+ schema |
| `odm-linkmlgen-nwss` | One schema per NWSS dictionary type supplied |

Every command accepts `--help`; the full option lists are in the
[CLI reference](reference/cli.md). If `--help` itself crashes, see
[Troubleshooting](troubleshooting.md#installation-problems).

## Generate the ODM schemas

### ODM v1

ODM v1 needs no source Excel file — its Schemasheets are bundled with the
package, so this runs offline in a couple of seconds:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

### Prepare the dictionary for v2 and above

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

### Generate v2 and v3

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
[output layout reference](reference/layouts.md).

`--version` is a bare version number (`2`, `3`, …). It is not just a label: it
determines the generated schema's name (`ODMv3`), id
(`https://onto.phes-odm.org/odm/v3`), and CURIE prefix (`odmv3`), so it must
match the dictionary you passed.

### Check the ODM result

Errors in the source dictionary are logged and skipped rather than raised, so a
run that "succeeded" can still have produced a degraded schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --dictionary-file ... --output-dir ... 2>&1 \
    | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

The symptom to look for in the schema itself is a slot whose range silently fell
back to `string` — that means an enumeration name could not be resolved. See
[Troubleshooting](troubleshooting.md).

If you are generating a version that has not been generated before, work through
[Extending the generator](extending.md#add-support-for-a-new-odm-version) as
well.

## Generate the NWSS schemas

NWSS is published as five separate dictionaries, each an Excel workbook
producing its own independent schema. You need only the ones you intend to
generate from.

### Get the dictionaries

Three of the five are public. Download them from the CDC's
[Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html)
page, from the **Data Dictionaries** box:

| Dictionary type | CLI option | Publicly available |
| --- | --- | --- |
| Main reporting | `--reporting` | Yes |
| Public concentration | `--public-concentration` | Yes |
| Public metric | `--public-metric` | Yes |
| Restricted raw | `--restricted-raw` | No |
| Restricted analytics | `--restricted-analytics` | No |

The two restricted dictionaries must be obtained from the CDC directly.

NWSS dictionary files are git-ignored (`/odm_linkmlgen/data/nwss/*.xlsx`), so
nothing is bundled with the repository. Put your copies anywhere and point the
CLI at them; by convention that is `odm_linkmlgen/data/nwss/`:

```console
mkdir -p odm_linkmlgen/data/nwss
mv ~/Downloads/*.xlsx odm_linkmlgen/data/nwss/reporting.xlsx
```

### Apply the manual fixes

Several published dictionaries contain defects that must be corrected in Excel
before they will process correctly. **These are defects in the published files,
not in the generator** — there is nothing to fix in this repository, and the
list will change as the CDC republishes.

#### `restricted_analytics` — no `Value Sets` sheet

Copy the `Value Sets` sheet from the restricted **raw** dictionary into the
restricted **analytics** workbook.

Even after doing this, some value sets are still missing. The categorical fields
`pcr_gene_target_agg`, `pcr_target_below_lod`, `pcr_target_units`, and
`quality_flag` have no enumeration definition anywhere. Each logs an error
during generation and produces a slot with an unresolved range.

#### `restricted_raw` — misnamed value set

In the `Value Sets` sheet, rename `other_norm_units` to `other_norm_unit`, so it
matches the name of the field that uses it.

#### `reporting` — misnamed value set

No longer needs fixing by hand. Where the `Value Sets` sheet and the `Metadata`
sheet name different value sets for the same field — `ntc_amplify` and
`pretreatment` have both done this — the generator takes the `Metadata` sheet's
name and logs an error identifying the field and both candidates. See
[which enumeration a field uses](data-dictionaries.md#which-enumeration-a-field-uses).
Report it upstream rather than editing the workbook.

#### `public_metric` — invalid permissible values

In the `vs_reporting_jurisdiction` value set:

- change `Chicago, IL` to `Chicago`
- change `Houston, TX` to `Houston`
- remove the individual states from the permissible values

Left as published, sample data will fail validation against the generated
schema.

!!! note "Known limitation"

    Independent of the source files: validation information in the `Value Set`
    column of the metadata sheet is **not yet used** by the generator.

### Generate the NWSS schemas from the dictionaries you have

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

### Check the NWSS result

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

## Where to go

| If you want to | Read |
| --- | --- |
| Install it and see it work, step by step | [Getting started](getting-started.md) |
| Understand an ODM run in more depth | [Generate ODM schemas](odm-schemas.md) |
| Watch the whole pipeline run, stage by stage | [Generate NWSS schemas](nwss-schemas.md) |
| Call it from Python instead of the CLI | [Use it from Python](python-api.md) |
| Work out why a schema is wrong | [Troubleshooting](troubleshooting.md) |
| Understand the design | [How it works](how-it-works.md) |
| Understand the source Excel files | [The source data dictionaries](data-dictionaries.md) |
| Support a new dictionary version | [Extending the generator](extending.md) |
| Change the code or the docs | [Contributing](contributing.md) |
| Look up a CLI option, step, or function | [Reference](reference/cli.md) |
