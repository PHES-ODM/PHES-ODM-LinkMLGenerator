# <img src="img/ODM-logo.png" align="right" alt="" width="180"/> PHES-ODM LinkML Schema Generator

This repository generates [LinkML](https://linkml.io/) schemas for two public health datasets:

- **[PHES-ODM](https://phes-odm.org)** — The Public Health Environmental Surveillance Open Data Model (versions 1, 2, and 3+)
- **[CDC NWSS](https://www.cdc.gov/nwss/wastewater-surveillance.html)** — The Centers for Disease Control and Prevention National Wastewater Surveillance System

## Background: Key Concepts

### LinkML

[LinkML](https://linkml.io/) (Linked Data Modeling Language) is an open standard for describing data schemas. A LinkML schema defines classes (tables), slots (columns/fields), and enumerations (allowed value sets), along with types, ranges, patterns, and other constraints. The output of this project is a `.yaml` file that conforms to the LinkML specification.

### Schemasheets

[LinkML Schemasheets](https://github.com/linkml/schemasheets) is a tool that generates a LinkML schema from a set of spreadsheet-style TSV files. Each TSV file defines part of the schema (a class, an enumeration, etc.) using a structured tabular format. This project converts ODM and NWSS Excel data dictionaries into a collection of Schemasheets TSV files, and then calls Schemasheets to produce the final LinkML YAML schema.

### ODM Data Dictionary

The PHES-ODM data dictionary is an Excel workbook that authoritatively defines all tables, fields, and allowed values for the ODM. The generator reads two sheets from this workbook:

- **parts** — defines all classes (tables) and slots (fields), including data types, constraints, and enumeration membership.
- **sets** — defines many of the enumeration value sets.

### Processing pipeline

For each supported dataset, the generator:

1. Extracts the relevant sheets from the source Excel file to CSV.
2. Processes the CSVs to produce a collection of Schemasheets TSV files (one per class, plus files for enumerations, prefixes, and schema metadata).
3. Runs Schemasheets to combine the TSV files into a single LinkML YAML schema.

---

## Repository Structure

```
odm_linkmlgen/          # Main Python package
│
├── make_odm.py         # CLI entry point for ODM v2+ schema generation
├── make_odm_v1.py      # CLI entry point for ODM v1 schema generation
├── make_nwss.py        # CLI entry point for NWSS schema generation
│
├── odm/                # ODM-specific processing modules
│   ├── odm_utils.py                   # Shared ODM dictionary helpers
│   ├── make_odm_ss_classes.py         # Extract class/table Schemasheets
│   ├── make_odm_ss_container.py       # Extract Container class Schemasheet
│   ├── make_odm_ss_enums_from_sets.py # Extract enum Schemasheets from sets sheet
│   ├── make_odm_ss_enums_from_parts.py# Extract enum Schemasheets from parts sheet
│   ├── make_odm_ss_prefixes.py        # Generate prefixes Schemasheet
│   └── make_odm_ss_schema.py          # Generate schema metadata Schemasheet
│
├── nwss/               # NWSS-specific processing modules
│   ├── nwss_utils.py                  # Shared NWSS dictionary helpers
│   ├── make_nwss_ss_classes.py        # Extract class Schemasheets from NWSS metadata
│   ├── make_nwss_ss_container.py      # Extract Container class Schemasheet
│   ├── make_nwss_ss_enums.py          # Extract enum Schemasheets from Value Sets sheet
│   ├── make_nwss_ss_prefixes.py       # Generate prefixes Schemasheet
│   └── make_nwss_ss_schema.py         # Generate schema metadata Schemasheet
│
└── utils/              # Shared utility modules
    ├── general_utils.py        # DataFrame helpers, file I/O, logging
    ├── schema_utils.py         # LinkML schema inspection helpers
    └── schemasheets_utils.py   # Schemasheets file creation and schema generation

tests/                  # pytest unit tests
```

### Output layout

Each generator writes its output to a directory you specify. Inside that directory, three subdirectories are created:

```
<output_dir>/
├── dictionary/     # Intermediate CSV files extracted from the source Excel file
├── schemasheets/   # Intermediate TSV files (input to Schemasheets)
└── linkml/         # Final LinkML YAML schema
```

---

## Installation

Clone the repository and create a virtual environment:

```console
git clone git@github.com:Big-Life-Lab/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip3 install -r requirements.txt
pip3 install -e .
```

The `pip install -e .` step installs the `odm_linkmlgen` package in editable mode and registers three CLI commands: `odm-linkmlgen-odm`, `odm-linkmlgen-odmv1`, and `odm-linkmlgen-nwss`.

---

## Running the Unit Tests

Install the dev dependencies, then run `pytest` from the repository root:

```console
pip install -e ".[dev]"
pytest
```

To see per-test output add the `-v` flag:

```console
pytest -v
```

---

## Generating the ODM v1 LinkML Schema

ODM v1 is simple and its Schemasheets are already bundled with this repository. To generate the schema, run:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The final schema will be saved to `gen/odm_v1/linkml/odm_v1.yaml`.

---

## Generating the ODM v2+ LinkML Schema

ODM v2 and above is generated from the official ODM Excel data dictionary. Since this file is not publicly available, contact [Mathew Thomson](mailto:matthomson@ohri.ca) to obtain it.

Save the file as `v# ODM dictionary.xlsx` where `#` is the version number (e.g., `v2 ODM dictionary.xlsx`). Use a recent version of Excel to open this file; older versions do not support the FILTER and XLOOKUP functions it relies on, and resaving with an older version will corrupt the workbook.

To generate the schema:

```console
odm-linkmlgen-odm \
    --version 2 \
    --dictionary-file "path/to/v2 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v2"
```

The final LinkML schema will be saved to `gen/odm_v2/linkml/odm_v2.yaml`.

For a detailed description of every processing step performed by the generator, see [Generating the ODM LinkML Schema](make_odm.md).

---

## Generating the CDC NWSS LinkML Schemas

The CDC NWSS data is published in five separate data dictionaries, each generating its own LinkML schema:

| Dictionary type | Description |
|---|---|
| `reporting` | Main reporting data dictionary |
| `public_concentration` | Public concentration data dictionary |
| `public_metric` | Public metric data dictionary |
| `restricted_raw` | Restricted raw data dictionary (not publicly available) |
| `restricted_analytics` | Restricted analytics data dictionary (not publicly available) |

Download the publicly available Excel dictionaries from the [Wastewater Surveillance Data Reporting and Analytics](https://www.cdc.gov/nwss/reporting.html) page ("Data Dictionaries" box). Omit any `--restricted-*` options if you do not have access to those files.

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "path/to/reporting.xlsx" \
    --public-concentration "path/to/public_concentration.xlsx" \
    --public-metric "path/to/public_metric.xlsx" \
    --restricted-raw "path/to/restricted_raw.xlsx" \
    --restricted-analytics "path/to/restricted_analytics.xlsx"
```

A separate subdirectory is created for each dictionary type under `--output-dir`. The final schema for each type is located at, for example, `gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml`.

---

## Using as a Python Library

The three main generator functions can also be called programmatically:

### ODM v2+

```python
from odm_linkmlgen.make_odm import make_odm

schema = make_odm(
    version="2",
    dictionary_file="path/to/v2 ODM dictionary.xlsx",
    output_dir="gen/odm_v2",
)
```

`make_odm` returns a `linkml_runtime.linkml_model.meta.SchemaDefinition` object.

### ODM v1

```python
from odm_linkmlgen.utils.schemasheets_utils import make_linkml_schema_from_schemasheets
import os
from pathlib import Path

schemasheets_dir = Path(os.path.dirname(__file__)) / "odm_linkmlgen" / "data" / "odm_v1" / "schemasheets"
schema = make_linkml_schema_from_schemasheets(schemasheets_dir, "gen/odm_v1/linkml/odm_v1.yaml")
```

### Individual processing steps (ODM)

Each processing step is independently importable if you need finer-grained control:

```python
from odm_linkmlgen.utils.general_utils import extract_sheets
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.utils.schemasheets_utils import make_linkml_schema_from_schemasheets

# 1. Extract sheets from Excel to CSV
extract_sheets("v2 ODM dictionary.xlsx", ["parts", "sets"], "gen/odm_v2/dictionary")

# 2. Extract enumerations
all_enums  = extract_sets_enums("gen/odm_v2/dictionary/sets.csv",
                                "gen/odm_v2/dictionary/parts.csv",
                                "gen/odm_v2/schemasheets/enums_sets.tsv")
all_enums += extract_parts_enums("gen/odm_v2/dictionary/parts.csv",
                                 "gen/odm_v2/schemasheets/enums_parts.tsv")

# 3. Extract classes
extract_all_classes("gen/odm_v2/dictionary/parts.csv",
                    "gen/odm_v2/schemasheets",
                    recognized_enums=all_enums)

# 4. Extract Container class, prefixes, and schema metadata
extract_container_class("gen/odm_v2/dictionary/parts.csv",
                        "gen/odm_v2/schemasheets/container.tsv")
make_prefixes("gen/odm_v2/schemasheets/prefixes.tsv", version="2")
make_schema("gen/odm_v2/schemasheets/schema.tsv", version="2")

# 5. Generate the final LinkML schema
schema = make_linkml_schema_from_schemasheets("gen/odm_v2/schemasheets",
                                              "gen/odm_v2/linkml/odm_v2.yaml")
```

---

## Module Reference

### `odm_linkmlgen.make_odm`

Top-level CLI and function for generating the ODM v2+ LinkML schema. Orchestrates all processing steps in sequence.

### `odm_linkmlgen.make_odm_v1`

CLI for generating the ODM v1 schema from the bundled Schemasheets files.

### `odm_linkmlgen.make_nwss`

Top-level CLI for generating all NWSS LinkML schemas. Iterates over each requested dictionary type and runs the full pipeline for each.

### `odm_linkmlgen.odm.odm_utils`

Shared helpers for working with the ODM parts sheet, including:
- `odm_get_available_class_names` — discovers all class/table names by inspecting column headers
- `odm_get_header_rows` — filters the parts sheet to rows that define a column in a given table (pK, fK, header)
- `odm_keep_active_rows` — removes deprecated/inactive rows
- `odm_get_enum_name_from_part_id` — derives the enumeration name from a part ID
- `add_missingness_set` — post-processes the schema to add missingness enumerations to slots that require them

### `odm_linkmlgen.nwss.nwss_utils`

Shared helpers for working with NWSS metadata sheets, including:
- `splitup_metadata_sheet` — splits a flat metadata sheet into per-table DataFrames
- `parse_enums_sheet` — extracts enumeration definitions from the NWSS "Value Sets" sheet
- `get_detailed_enums` — identifies per-field variants of shared enumerations

### `odm_linkmlgen.utils.general_utils`

General-purpose utilities:
- `extract_sheets` — extracts named sheets from an Excel file to CSV with per-column NA handling
- `clear_dirs` — removes stale CSV/TSV/YAML files from output directories
- `save_data_frame` / `read_data_frame` — CSV/TSV I/O that auto-detects separators from file extension
- `expand_multi_rows` — expands semicolon-delimited values in a DataFrame into multiple rows
- `get_class_name_from_file_name` — extracts a class name from a data file name

### `odm_linkmlgen.utils.schemasheets_utils`

Utilities for creating and consuming Schemasheets files:
- `save_schemasheet` — writes a DataFrame as a Schemasheets-formatted TSV (adds the `> header` row)
- `make_container_schemasheet` — builds the top-level Container class TSV
- `make_linkml_schema_from_schemasheets` — runs Schemasheets over all TSV files in a directory and returns a `SchemaDefinition`
- `save_schema_definition` — serializes a `SchemaDefinition` to YAML
- `fix_schemasheets_generated_schema` — post-processes a Schemasheets-generated schema to correct known Schemasheets limitations (e.g. minimum/maximum values stored as strings, empty permissible value sentinel)

### `odm_linkmlgen.utils.schema_utils`

Helpers for inspecting a `SchemaDefinition`:
- `get_slot_definition` — returns the fully induced slot definition for a class+slot pair
- `get_ranges_of_slot` / `get_ranges_of_slot_defn` — extracts the range(s) of a slot, handling both `range` and `any_of` patterns
