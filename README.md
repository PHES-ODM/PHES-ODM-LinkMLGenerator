# <img src="img/ODM-logo.png" align="right" alt="" width="180"/> PHES-ODM LinkML Schema Generator

<!-- badges: start -->
[![lint.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml)
[![pytest.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml)
[![docs.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/docs.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/docs.yaml)
<!-- badges: end -->

This repository turns Excel data dictionaries into [LinkML](https://linkml.io/)
schemas for two wastewater surveillance datasets:

- **[PHES-ODM](https://phes-odm.org)** — the Public Health Environmental
  Surveillance Open Data Model (versions 1, 2, and 3+)
- **[CDC NWSS](https://www.cdc.gov/nwss/wastewater-surveillance.html)** — the
  Centers for Disease Control and Prevention National Wastewater Surveillance
  System

The output is a single `.yaml` LinkML schema per dataset (per ODM version, or per
NWSS dictionary type). Those schemas can then be used by any LinkML tool — for
example to validate a data file, or to generate documentation, JSON Schema, SQL
DDL, or Python classes.

## 📖 Documentation

The full documentation for this project is published as a website at
**<https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/>**. It goes well beyond
this README: everything below is a quick start, while the site covers the whole
tool. Start there if you are new to the generator, or if you need a detail this
page does not answer. It is also the place to begin if you are onboarding onto
the project or intend to contribute to the codebase — it explains how the
pipeline is put together, why the source dictionaries are shaped the way they
are, and what each stage of a run produces, which is the background you need
before changing any of it.

The site follows the
[Diátaxis documentation framework](https://diataxis.fr/) — a tutorial to learn
from, how-to guides to work from, reference to look things up in, and
explanation to understand the design.

| Section | Start here if you want to |
| --- | --- |
| [Getting started](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/tutorials/getting-started/) | Install it and generate your first schema, step by step |
| [How-to guides](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/install/) | Generate the ODM or NWSS schemas, call it from Python, or fix a bad schema |
| [Reference](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/reference/cli/) | Look up a CLI option, a pipeline step, or the Python API |
| [Explanation](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/explanation/how-it-works/) | Understand the design, the pipeline, and the source dictionaries |

The Markdown sources are in [docs/](docs/), and the site can be built locally
with `mkdocs serve` — see [Contributing](CONTRIBUTING.md).

## Installation

Requires Python 3.10 or newer.

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

This registers three CLI commands: `odm-linkmlgen-odm`, `odm-linkmlgen-odmv1`,
and `odm-linkmlgen-nwss`. Pass `--help` to any of them, or see the
[CLI reference](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/reference/cli/).

## Generate the ODM schemas

### ODM v1

ODM v1 needs no source Excel file — its Schemasheets are bundled with the
package, so this runs offline in a couple of seconds:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

### ODM v2 and v3

Both versions use the same command; only `--version` and the dictionary change.

**1. Obtain the dictionary.** The official PHES-ODM Excel data dictionary is
**not publicly available** and is not committed to this repository. Contact
[Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a copy.

> [!CAUTION]
> Opening and resaving the dictionary with an older Excel will corrupt it. The
> file relies on the `FILTER` and `XLOOKUP` functions; a version of Excel that
> does not support them will silently destroy those formulas on save, and the
> damage is not recoverable. Use a recent Excel, or a read-only viewer.

**2. Put it where the generator expects it.** Name it `v# ODM dictionary.xlsx`,
where `#` is the version number, and by convention place it in
`odm_linkmlgen/data/odm_v{n}/`:

```console
mkdir -p odm_linkmlgen/data/odm_v2 odm_linkmlgen/data/odm_v3
cp "~/v2 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v2/
cp "~/v3 ODM dictionary.xlsx" odm_linkmlgen/data/odm_v3/
```

Those directories are git-ignored (`/odm_linkmlgen/data/odm_v*/*.xlsx`), so your
copy stays local to your checkout. The location is only a convention — any path
can be passed to `--dictionary-file`.

**3. Generate.**

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
`schemasheets/` directories.

`--version` is a bare version number, and is not just a label: it determines the
generated schema's name (`ODMv3`), id (`https://onto.phes-odm.org/odm/v3`), and
CURIE prefix (`odmv3`), so it must match the dictionary you passed.

**4. Check the result.** Errors in the source dictionary are logged and skipped
rather than raised, so a run that "succeeded" can still have produced a degraded
schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --dictionary-file ... --output-dir ... 2>&1 \
    | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

## Generate the NWSS schemas

NWSS is published as five separate dictionaries, each an Excel workbook producing
its own independent schema. You need only the ones you intend to generate from.

**1. Get the dictionaries.** Three of the five are public — download them from
the CDC's
[Wastewater Surveillance Data Reporting and Analytics](https://archive.cdc.gov/www_cdc_gov/nwss/reporting.html)
page, from the **Data Dictionaries** box. The two restricted dictionaries must be
requested from the CDC directly.

| Dictionary type | CLI option | Publicly available |
| --- | --- | --- |
| NWSS Reporting | `--reporting` | Yes |
| Public Concentration | `--public-concentration` | Yes |
| Public Metric | `--public-metric` | Yes |
| Restricted Raw | `--restricted-raw` | No |
| Restricted Analytics | `--restricted-analytics` | No |

NWSS dictionary files are git-ignored (`/odm_linkmlgen/data/nwss/*.xlsx`), so
nothing is bundled with the repository. Put your copies anywhere and point the
CLI at them; by convention that is `odm_linkmlgen/data/nwss/`.

**2. Apply the manual fixes.** Several published dictionaries contain defects
that must be corrected in Excel before they will process correctly. **These are
defects in the published files, not in the generator**, and the list will
change as the CDC republishes.

- **`restricted_analytics` — no `Value Sets` sheet.** Copy the `Value Sets` sheet
  from the restricted **raw** dictionary into the restricted **analytics**
  workbook. Even then, `pcr_gene_target_agg`, `pcr_target_below_lod`,
  `pcr_target_units`, and `quality_flag` have no enumeration definition anywhere;
  each logs an error and produces a slot with an unresolved range.
- **`restricted_raw` — misnamed value set.** In the `Value Sets` sheet, rename
  `other_norm_units` to `other_norm_unit`, to match the field that uses it.
- **`reporting` — misnamed value set.** No longer needs fixing by hand. Where the
  `Value Sets` sheet and the `Metadata` sheet name different value sets for the
  same field — `ntc_amplify` and `pretreatment` have both done this — the
  generator takes the `Metadata` sheet's name and logs an error identifying the
  field and both candidates. Report it upstream rather than editing the workbook.
- **`public_metric` — invalid permissible values.** In the
  `vs_reporting_jurisdiction` value set, change `Chicago, IL` to `Chicago`,
  change `Houston, TX` to `Houston`, and remove the individual states. Left as
  published, sample data will fail validation against the generated schema.

**3. Generate.** Every dictionary option is optional, and each one you pass
generates one independent schema. Supply only the dictionaries you actually have:

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "odm_linkmlgen/data/nwss/reporting.xlsx" \
    --public-concentration "odm_linkmlgen/data/nwss/public_concentration.xlsx" \
    --public-metric "odm_linkmlgen/data/nwss/public_metric.xlsx"
```

A subdirectory is created per dictionary type, so the reporting run above writes
its schema to `gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml`. There is no
separate command per type — to generate just one, pass just one option.

**4. Check the result.** `ERROR` lines in the log are expected and are not
failures: a bad row is logged and skipped so that it cannot abort the whole run.
But they do mean the schema is degraded, usually with an unresolved range on a
categorical slot. Scan for them:

```console
odm-linkmlgen-nwss --output-dir "gen/nwss" --reporting ... 2>&1 \
    | tee gen/nwss/generate.log
grep ERROR gen/nwss/generate.log
```

An error naming a categorical field almost always means its enumeration is
missing from the `Value Sets` sheet — check the manual fixes above first, since
the published dictionaries are the usual culprit.

What each run leaves on disk, and why the output looks the way it does, is
covered in [Inside an ODM run](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/explanation/odm-runs/)
and [Inside an NWSS run](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/explanation/nwss-runs/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
