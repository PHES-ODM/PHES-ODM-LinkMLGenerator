# <img src="img/ODM-logo.png" align="right" alt="" width="180"/> PHES-ODM LinkML Schema Generator

<!-- badges: start -->
[![lint.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml)
[![pytest.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml)
[![docs.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/docs.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/docs.yaml)
<!-- badges: end -->

This repository turns data dictionaries into [LinkML](https://linkml.io/)
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
<https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/>. It goes well beyond
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

**ODM v3 is the current version of the model**, and the dictionary it is
generated from is the pair of CSV dictionary tables the PHES-ODM project
publishes — a parts file and a sets file. They are public, and they are the
recommended input. The Excel data dictionary is still accepted; see
[Generate from the Excel dictionary](#generate-from-the-excel-dictionary-instead)
at the end of this section.

**1. Get the dictionary tables.** The v3 tables are in the
[`dictionary-tables/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/label/dictionary-tables)
of the PHES-ODM repository, on the `label` branch. Two of the files there are
the ones the generator reads: `ODM_parts_v3.0.0.csv` (the parts table) and
`ODM_sets_v3.0.0.csv` (the sets table).

```console
mkdir -p odm_linkmlgen/data/odm_v3
curl -L -o odm_linkmlgen/data/odm_v3/ODM_parts_v3.0.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/label/dictionary-tables/ODM_parts_v3.0.0.csv"
curl -L -o odm_linkmlgen/data/odm_v3/ODM_sets_v3.0.0.csv \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM/label/dictionary-tables/ODM_sets_v3.0.0.csv"
```

By convention the tables go in `odm_linkmlgen/data/odm_v{n}/`, where every
`.csv` and `.xlsx` is git-ignored, so the downloads cannot be committed by
accident. The location is only a convention — any path can be passed to
`--parts-file` and `--sets-file`.

**2. Generate.**

```console
odm-linkmlgen-odm \
    --version 3 \
    --parts-file "odm_linkmlgen/data/odm_v3/ODM_parts_v3.0.0.csv" \
    --sets-file "odm_linkmlgen/data/odm_v3/ODM_sets_v3.0.0.csv" \
    --output-dir "gen/odm_v3"
```

The schema is written to `gen/odm_v3/linkml/odm_v3.yaml`, alongside the
intermediate `dictionary/` and `schemasheets/` directories. The two CSVs are
copied into `{output-dir}/dictionary/`, and that directory is cleared before
they are read — so `--output-dir` must not be the directory the CSVs are read
from, or they are deleted before the run can use them.

`--version` is a bare version number, and is not just a label: it determines the
generated schema's name (`ODMv3`), id (`https://onto.phes-odm.org/odm/v3`), and
CURIE prefix (`odmv3`), so it must match the dictionary you passed.

**3. Check the result.** Errors in the source dictionary are logged and skipped
rather than raised, so a run that "succeeded" can still have produced a degraded
schema. Scan the log:

```console
odm-linkmlgen-odm --version 3 --parts-file ... --sets-file ... \
    --output-dir "gen/odm_v3" 2>&1 | tee gen/odm_v3/generate.log
grep -E "ERROR|WARNING" gen/odm_v3/generate.log
```

### ODM v2

Same command with `--version 2` and the v2 tables, which are in the
[`archived V2.3 (PATCH)/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/v2.3.0/archived%20V2.3%20%28PATCH%29)
of the PHES-ODM repository, on the `v2.3.0` branch. ODM v2 is superseded by v3 —
generate it only if something you maintain still needs it.

```console
odm-linkmlgen-odm \
    --version 2 \
    --parts-file "odm_linkmlgen/data/odm_v2/ODM_parts_v2.3.0.csv" \
    --sets-file "odm_linkmlgen/data/odm_v2/ODM_sets_v2.3.0.csv" \
    --output-dir "gen/odm_v2"
```

### ODM v1

ODM v1 needs no dictionary at all — its Schemasheets are bundled with the
package, so this runs offline in a couple of seconds:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. That is the only file
produced — ODM v1 skips the extract and transform stages entirely.

### Generate from the Excel dictionary instead

The same schemas can be generated from the official PHES-ODM Excel data
dictionary, by passing `--dictionary-file` in place of the `--parts-file` /
`--sets-file` pair — one form or the other, never both:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The workbook is **not publicly available** and is not committed to this
repository. Contact [Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a
copy, and by convention put it in `odm_linkmlgen/data/odm_v{n}/`, the same
directory as the CSV tables and git-ignored the same way, so your copy stays
local to your checkout.

> [!CAUTION]
> Opening and resaving the dictionary with an older Excel will corrupt it. The
> file relies on the `FILTER` and `XLOOKUP` functions; a version of Excel that
> does not support them will silently destroy those formulas on save, and the
> damage is not recoverable. Use a recent Excel, or a read-only viewer. The
> published CSV tables avoid this hazard entirely.

See [Generate the ODM schemas](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/generate-odm-schemas/)
for all of the above in full.

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
