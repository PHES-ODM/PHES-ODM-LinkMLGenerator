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

**<https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/>**

The documentation follows the
[Divio system](https://docs.divio.com/documentation-system/) — four sections,
each answering a different question:

| Section | Start here if you want to |
| --- | --- |
| [Tutorials](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/tutorials/) | Learn the project by generating a schema end to end |
| [How-to guides](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/) | Do a specific job: generate, debug, or add a dictionary version |
| [Explanation](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/explanation/) | Understand the design and the source data dictionaries |
| [Reference](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/reference/) | Look up a CLI option, a pipeline step, or the Python API |

New to the project? Go straight to
[Generate your first schema](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/tutorials/generate-your-first-schema/).

The Markdown sources are in [docs/](docs/), and the site can be built locally
with `mkdocs serve` — see
[Update the documentation](docs/how-to/update-the-documentation.md).

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

## Quick start

ODM v1 needs no source Excel file — its Schemasheets are bundled with the
package:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`.

For **ODM v2+** and **NWSS** you first need a source Excel dictionary. Neither is
committed to this repository: the ODM dictionary is not publicly available, and
the NWSS dictionaries are downloaded from cdc.gov and need manual fixes before
use.

- [Prepare the ODM data dictionary](docs/how-to/prepare-the-odm-dictionary.md) →
  [Generate an ODM schema](docs/how-to/generate-an-odm-schema.md)
- [Prepare the NWSS data dictionaries](docs/how-to/prepare-the-nwss-dictionaries.md)
  → [Generate NWSS schemas](docs/how-to/generate-nwss-schemas.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
