# <img src="img/ODM-logo.png" align="right" alt="" width="180"/> PHES-ODM LinkML Schema Generator

<!-- badges: start -->
[![lint.yaml](https://github.com/Big-Life-Lab/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml/badge.svg)](https://github.com/Big-Life-Lab/PHES-ODM-LinkMLGenerator/actions/workflows/lint.yaml)
[![pytest.yaml](https://github.com/Big-Life-Lab/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml/badge.svg)](https://github.com/Big-Life-Lab/PHES-ODM-LinkMLGenerator/actions/workflows/pytest.yaml)
<!-- badges: end -->

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

Save the file as `v# ODM dictionary.xlsx` where `#` is the version number (e.g., `v3 ODM dictionary.xlsx`). Use a recent version of Excel to open this file; older versions do not support the FILTER and XLOOKUP functions it relies on, and resaving with an older version will corrupt the workbook.

To generate the schema:

```console
odm-linkmlgen-odm \
    --version 3 \
    --dictionary-file "path/to/v3 ODM dictionary.xlsx" \
    --output-dir "gen/odm_v3"
```

The final LinkML schema will be saved to `gen/odm_v3/linkml/odm_v3.yaml`.

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
    version="3",
    dictionary_file="path/to/v3 ODM dictionary.xlsx",
    output_dir="gen/odm_v3",
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
from odm_linkmlgen.utils.general_utils import clear_dirs, extract_sheets
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.odm.odm_utils import add_missingness_set
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
    save_schema_definition,
)

version = "3"
dictionary_file = f"path/to/v{version} ODM dictionary.xlsx"
output_dir = f"gen/odm_v{version}"
dictionary_dir = f"{output_dir}/dictionary"
schemasheets_dir = f"{output_dir}/schemasheets"
linkml_dir = f"{output_dir}/linkml"
parts_file = f"{dictionary_dir}/parts.csv"
sets_file = f"{dictionary_dir}/sets.csv"

# 1. Remove any stale csv/tsv/yaml files from a previous run
clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

# 2. Extract sheets from Excel to CSV. The na_values argument keeps partID values
#    such as "NA" and "None" as literal strings instead of empty (NA) values.
extract_sheets(
    dictionary_file,
    ["parts", "sets"],
    dictionary_dir,
    na_values={"parts": {"partID": ""}, "sets": {"partID": ""}},
)

# 3. Extract enumerations, first from the sets sheet (including the mmaSet enums),
#    then the remaining ones from the parts sheet
all_enums = extract_sets_enums(
    sets_file, parts_file, f"{schemasheets_dir}/enums_sets.tsv"
)
all_enums += extract_parts_enums(parts_file, f"{schemasheets_dir}/enums_parts.tsv")
all_enums = list(dict.fromkeys(all_enums))

# 4. Extract classes (one schemasheet per ODM table)
extract_all_classes(parts_file, schemasheets_dir, recognized_enums=all_enums)

# 5. Extract Container class, prefixes, and schema metadata
extract_container_class(parts_file, f"{schemasheets_dir}/container.tsv")
make_prefixes(f"{schemasheets_dir}/prefixes.tsv", version)
make_schema(f"{schemasheets_dir}/schema.tsv", version)

# 6. Run Schemasheets over all the generated TSV files
schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

# 7. Add genMissingnessSet to all ranges where an enum must be paired with it
add_missingness_set(schema, parts_file)

# 8. Save the final LinkML schema
save_schema_definition(schema, f"{linkml_dir}/odm_v{version}.yaml")
```

---

## Module Reference

### Top-level generators

#### `odm_linkmlgen.make_odm`

Top-level CLI and function for generating the ODM v2+ LinkML schema. Orchestrates all processing steps in sequence.

- `make_odm` — runs the full pipeline for one ODM version and returns the `SchemaDefinition`

#### `odm_linkmlgen.make_odm_v1`

CLI for generating the ODM v1 schema from the bundled Schemasheets files.

#### `odm_linkmlgen.make_nwss`

Top-level CLI for generating all NWSS LinkML schemas. Iterates over each requested dictionary type and runs the full pipeline for each.

- `make_nwss` — runs the full pipeline for every dictionary type that was supplied

### ODM processing steps

Each of these modules is both an importable function and a standalone CLI (`python -m odm_linkmlgen.odm.<module> --help`).

#### `odm_linkmlgen.odm.make_odm_ss_classes`

Creates one Schemasheet per ODM class (table) from the parts sheet, named `class_{table_name}.tsv`.

- `extract_class` — builds the Schemasheet DataFrame for a single class
- `extract_all_classes` — builds and saves a Schemasheet for every class in the parts sheet

#### `odm_linkmlgen.odm.make_odm_ss_enums_from_sets`

- `extract_sets_enums` — extracts the enumerations whose permissible values live in the sets sheet (including the `mmaSet` enums) and returns their names

#### `odm_linkmlgen.odm.make_odm_ss_enums_from_parts`

- `extract_parts_enums` — extracts the enumerations whose permissible values live in the parts sheet (everything not handled by `extract_sets_enums`) and returns their names

#### `odm_linkmlgen.odm.make_odm_ss_container`

- `extract_container_class` — builds the top-level `tree_root` Container class Schemasheet, with one multivalued slot per ODM table

#### `odm_linkmlgen.odm.make_odm_ss_prefixes`

- `get_prefixes_data` — returns the CURIE prefixes used by the schema for a given ODM version
- `make_prefixes` — writes the prefixes Schemasheet

#### `odm_linkmlgen.odm.make_odm_ss_schema`

- `get_schema_data` — returns the schema-level metadata (id, name, description, default prefix) for a given ODM version
- `make_schema` — writes the schema metadata Schemasheet

### NWSS processing steps

Each of these modules is both an importable function and a standalone CLI (`python -m odm_linkmlgen.nwss.<module> --help`).

#### `odm_linkmlgen.nwss.make_nwss_ss_classes`

- `parse_table_df` — prepares the metadata rows of a single NWSS table for Schemasheets processing
- `extract_all_classes` — saves a Schemasheet per NWSS table (or a single merged class when `single_table` is set)

#### `odm_linkmlgen.nwss.make_nwss_ss_enums`

- `extract_enums` — extracts every enumeration from a NWSS "Value Sets" sheet, one Schemasheet per enum

#### `odm_linkmlgen.nwss.make_nwss_ss_container`

- `extract_container_class` — builds the top-level Container class Schemasheet for NWSS

#### `odm_linkmlgen.nwss.make_nwss_ss_prefixes`

- `make_prefixes` — writes the prefixes Schemasheet for a given NWSS dictionary type

#### `odm_linkmlgen.nwss.make_nwss_ss_schema`

- `make_schema` — writes the schema metadata Schemasheet for a given NWSS dictionary type

### Shared helpers

#### `odm_linkmlgen.odm.odm_utils`

Shared helpers for working with the ODM parts sheet:

- `odm_get_available_class_names` — discovers all class/table names by inspecting column headers (any header ending in `ODM_PARTS_COLUMN_CLASS_TAG`)
- `odm_get_fk_target_class` — for a foreign key part ID, returns the class that part ID is the primary key of, or `None` if the part ID is unknown or is not a key. Falls back to the optional `fKAliasID` column when the part ID is an alias for a primary key (v2 dictionaries have no `fKAliasID` column)
- `odm_get_header_rows` — filters the parts sheet to rows that define a column in a given table (pK, fK, header)
- `odm_keep_active_rows` — removes deprecated/inactive rows
- `odm_get_enum_name_from_part_id` — derives the enumeration name from a part ID, falling back to `string` for unrecognized enums
- `set_range_of_slot` — sets a slot usage's range, emitting `any_of` when more than one range is given
- `add_missingness_set` — post-processes the schema to add missingness enumerations to slots that require them

#### `odm_linkmlgen.nwss.nwss_utils`

Shared helpers for working with NWSS metadata sheets:

- `splitup_metadata_sheet` — splits a flat metadata sheet into per-table DataFrames
- `parse_enums_sheet` — extracts enumeration definitions from the NWSS "Value Sets" sheet
- `get_detailed_enums` — identifies per-field variants of shared enumerations

#### `odm_linkmlgen.utils.general_utils`

General-purpose utilities:

- `get_logger` — returns a configured logger, used by every module
- `extract_sheets` — extracts named sheets from an Excel file to CSV with per-column NA handling
- `clear_dirs` — removes stale CSV/TSV/YAML files from output directories
- `save_data_frame` / `read_data_frame` — CSV/TSV I/O that auto-detects separators from file extension
- `order_columns` — reorders DataFrame columns to a preferred order
- `strip_whitespace` — strips surrounding whitespace from every string in a DataFrame
- `expand_multi_rows` — expands semicolon-delimited values in a DataFrame into multiple rows
- `get_class_name_from_file_name` — extracts a class name from a data file name
- `choose_ignore_case_value` — normalizes a value's capitalization to match a list of allowable values
- `rename_items` — renames the items of a list using a mapping
- `select_func_kwargs` — filters a kwargs dictionary down to the arguments a function accepts

#### `odm_linkmlgen.utils.schemasheets_utils`

Utilities for creating and consuming Schemasheets files:

- `save_schemasheet` — writes a DataFrame as a Schemasheets-formatted TSV (adds the `> header` row)
- `add_schemasheets_header` — inserts the `>`-prefixed Schemasheets header row into a DataFrame
- `make_container_schemasheet` — builds the top-level Container class TSV
- `make_linkml_schema_from_schemasheets` — runs Schemasheets over all TSV files in a directory and returns a `SchemaDefinition`
- `save_schema_definition` — serializes a `SchemaDefinition` to YAML
- `fix_schemasheets_generated_schema` — post-processes a Schemasheets-generated schema to correct known Schemasheets limitations (e.g. minimum/maximum values stored as strings, empty permissible value sentinel)

#### `odm_linkmlgen.utils.schema_utils`

Helpers for inspecting a `SchemaDefinition`:

- `get_slot_definition` — returns the fully induced slot definition for a class+slot pair
- `get_ranges_of_slot` / `get_ranges_of_slot_defn` — extracts the range(s) of a slot, handling both `range` and `any_of` patterns
