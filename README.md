# <img src="img/ODM-logo.png" align="right" alt="" width="180"/> PHES-ODM LinkML Schema Generator

<!-- badges: start -->
[![lint.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml)
[![pytest.yaml](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml/badge.svg)](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml)
<!-- badges: end -->

This repository turns Excel data dictionaries into [LinkML](https://linkml.io/)
schemas for two wastewater surveillance datasets:

- **[PHES-ODM](https://phes-odm.org)** — the Public Health Environmental
  Surveillance Open Data Model (versions 1, 2, and 3+)
- **[CDC NWSS](https://www.cdc.gov/nwss/wastewater-surveillance.html)** — the
  Centers for Disease Control and Prevention National Wastewater Surveillance
  System

The output is a single `.yaml` LinkML schema per dataset (per ODM version, or
per NWSS dictionary type). Those schemas can then be used by any LinkML tool —
for example to validate a data file, or to generate documentation, JSON Schema,
SQL DDL, or Python classes.

## Documentation

New to the project? Read in this order:

1. **This page** — install the package and generate a schema.
2. **[Architecture](docs/architecture.md)** — the concepts (LinkML,
   Schemasheets, data dictionaries), how the pipeline is put together, and where
   everything lives in the repository.
3. **[ODM pipeline](docs/odm-pipeline.md)** /
   **[NWSS pipeline](docs/nwss-pipeline.md)** — a step-by-step account of what
   each generator does, and the source-file quirks you need to know about.
4. **[Module reference](docs/module-reference.md)** — every module and its
   public functions.
5. **[Contributing](CONTRIBUTING.md)** — dev environment, tests, linting, and
   how to add support for a new ODM version or NWSS dictionary type.

---

## Installation

Requires Python 3.10 or newer.

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip3 install -r requirements.txt
pip3 install -e .
```

The `pip install -e .` step installs the `odm_linkmlgen` package in editable
mode and registers three CLI commands: `odm-linkmlgen-odm`,
`odm-linkmlgen-odmv1`, and `odm-linkmlgen-nwss`. Pass `--help` to any of them to
see the available options.

---

## Quick start

### ODM v1

ODM v1 is simple and its Schemasheets files are already bundled with this
repository, so no source Excel file is needed:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`.

### ODM v2 and above

ODM v2+ is generated from the official ODM Excel data dictionary. That file is
**not publicly available** and is not committed to this repository — contact
[Mathew Thomson](mailto:matthomson@ohri.ca) to obtain a copy. Read
[Preparing the ODM data dictionary](docs/odm-pipeline.md#preparing-the-odm-data-dictionary)
before you open or save the file, as an older version of Excel will corrupt it.

By convention the dictionary goes in `odm_linkmlgen/data/odm_v{n}/` (git-ignored),
but any path works:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "odm_linkmlgen/data/odm_v3/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The schema is written to `gen/odm_v3/linkml/odm_v3.yaml`.

### CDC NWSS

NWSS is published as five separate data dictionaries, each producing its own
LinkML schema:

| Dictionary type | CLI option | Publicly available |
| --- | --- | --- |
| Main reporting | `--reporting` | Yes |
| Public concentration | `--public-concentration` | Yes |
| Public metric | `--public-metric` | Yes |
| Restricted raw | `--restricted-raw` | No |
| Restricted analytics | `--restricted-analytics` | No |

Download the public dictionaries from the
[Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html)
page (the "Data Dictionaries" box). Supply only the dictionaries you have —
every option is optional, and each one you pass generates one schema. Some
dictionaries need manual fixes first; see
[Preparing the NWSS data dictionaries](docs/nwss-pipeline.md#preparing-the-nwss-data-dictionaries).

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "path/to/reporting.xlsx" \
    --public-concentration "path/to/public_concentration.xlsx" \
    --public-metric "path/to/public_metric.xlsx"
```

A subdirectory is created per dictionary type, so the reporting schema above
ends up at `gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml`.

### Output layout

Every generator writes three subdirectories inside the `--output-dir` you give
it:

```text
<output_dir>/
├── dictionary/     # Intermediate CSV files extracted from the source Excel file
├── schemasheets/   # Intermediate TSV files (the input to Schemasheets)
└── linkml/         # The final LinkML YAML schema
```

The `dictionary/` and `schemasheets/` files are intermediate build artefacts.
They are kept on disk because they are the most useful thing to look at when a
generated schema is not what you expected — see
[Debugging a generated schema](CONTRIBUTING.md#debugging-a-generated-schema).

---

## Using as a Python library

Each generator is a plain function as well as a CLI command.

### ODM v2+

```python
from odm_linkmlgen.make_odm import make_odm

schema = make_odm(
    version="3",
    dictionary_file="path/to/v3 ODM dictionary.xlsx",
    output_dir="gen/odm_v3",
)
```

`make_odm` returns a `linkml_runtime.linkml_model.meta.SchemaDefinition` object,
in addition to writing the YAML file to disk.

### ODM v1

```python
from pathlib import Path

import odm_linkmlgen
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
)

schemasheets_dir = (
    Path(odm_linkmlgen.__file__).parent / "data" / "odm_v1" / "schemasheets"
)
schema = make_linkml_schema_from_schemasheets(
    schemasheets_dir, "gen/odm_v1/linkml/odm_v1.yaml"
)
```

### NWSS

```python
from odm_linkmlgen.make_nwss import make_nwss

make_nwss(
    output_dir="gen/nwss",
    reporting="path/to/reporting.xlsx",
)
```

### Running the individual steps

Every step of both pipelines is independently importable, and is also its own
CLI (`python -m odm_linkmlgen.odm.make_odm_ss_classes --help`). This is useful
when you want to re-run one step against already-extracted CSVs instead of
rebuilding from Excel. See [ODM pipeline](docs/odm-pipeline.md) for a worked
example that reproduces `make_odm` step by step, and
[Module reference](docs/module-reference.md) for the full list of functions.

---

## Running the tests

```console
pip install -r requirements-dev.txt
pytest
```

See [Contributing](CONTRIBUTING.md) for the full development workflow, including
linting and formatting.
