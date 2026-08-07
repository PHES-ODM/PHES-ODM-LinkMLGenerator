# Architecture

This page explains the concepts the project is built on, the shape of the
pipeline, and where each piece of it lives in the repository. Read it before the
[ODM pipeline](odm-pipeline.md) or [NWSS pipeline](nwss-pipeline.md) pages, which
assume the vocabulary below.

## Key concepts

### LinkML

[LinkML](https://linkml.io/) (Linked Data Modeling Language) is an open standard
for describing data schemas. A LinkML schema is a YAML file that defines:

- **classes** — equivalent to tables in ODM and NWSS
- **slots** — equivalent to columns or fields
- **enumerations** — named sets of permissible values
- **ranges** — the type of a slot: a built-in type (`string`, `integer`,
  `float`, …), an enumeration, or another class (which is how foreign keys are
  expressed)

Constraints such as `required`, `pattern` (a regular expression),
`minimum_value`, and `maximum_value` are attached to slots. A single schema file
is the final product of this repository.

Two LinkML details show up repeatedly in the code:

- **`tree_root`** — the one class that acts as the entry point to a data file.
  Both pipelines generate a `Container` class marked as the tree root, holding
  one multivalued slot per table.
- **`slot_usage`** — a per-class override of a slot. Because the same slot name
  (for example `siteID`) can appear in several ODM tables with different
  constraints, most of the generated detail lands in `slot_usage` rather than on
  the top-level slot definition.

### Schemasheets

[LinkML Schemasheets](https://github.com/linkml/schemasheets) generates a LinkML
schema from a set of spreadsheet-style TSV files. Each TSV describes part of the
schema, and Schemasheets merges them all into one YAML file.

A Schemasheets TSV has two header rows. The first is an ordinary column header,
which can be named anything. The second starts with `>` and maps each column to
a LinkML metamodel element. Any column mapped to `ignore` is dropped. For
example:

```text
partID      label       partDesc        dataType
> slot      title       description     range
siteID      Site ID     The site ID     string
```

This project never writes those TSVs by hand. It converts the source Excel
dictionaries into them, which is what nearly all the code in `odm_linkmlgen/`
does. The `>` header row is added by
`odm_linkmlgen.utils.schemasheets_utils.add_schemasheets_header`, and each
extraction module declares its own column-to-LinkML mapping in a module-level
`headers` dictionary.

### The ODM data dictionary

The PHES-ODM data dictionary is an Excel workbook that authoritatively defines
every table, field, and permissible value in the ODM. The generator reads two of
its sheets:

- **parts** — one row per "part". A part can be a table, a column, an
  enumeration, or a permissible value of an enumeration; which one it is depends
  on the row's other columns. This sheet defines all classes and slots, along
  with their data types and constraints.
- **sets** — the permissible values for many (not all) of the enumerations.

The parts sheet is the harder of the two to read, because a row's meaning is
determined by its relationships to other columns rather than by a single "kind"
column. The [ODM pipeline](odm-pipeline.md) page describes the specific
conventions.

### The NWSS data dictionaries

Each NWSS dictionary is an Excel workbook with two sheets of interest:

- a **metadata** sheet — one row per field, listing its data type, description,
  and whether it is required. The sheet name differs between dictionary types
  (`Metadata`, `Wastewater Metadata`, or `Analytics Data Dictionary`).
- a **Value Sets** sheet — the enumerations and their permissible values, plus a
  mapping from each field to the value set it uses.

NWSS dictionaries are less regular than the ODM one, and some require manual
fixes before they can be processed. See
[Preparing the NWSS data dictionaries](nwss-pipeline.md#preparing-the-nwss-data-dictionaries).

## The pipeline

Both pipelines have the same three stages:

```text
   Excel data dictionary
            │
            │  1. extract_sheets
            ▼
   dictionary/*.csv          One CSV per source sheet
            │
            │  2. the extraction modules (make_*_ss_*.py)
            ▼
   schemasheets/*.tsv        One TSV per class, per enum, plus
            │                container / prefixes / schema metadata
            │  3. make_linkml_schema_from_schemasheets
            ▼
   linkml/<name>.yaml        The final LinkML schema
```

**Stage 1 — extract.** `general_utils.extract_sheets` saves the required Excel
sheets as CSV files. Working from CSV keeps the rest of the pipeline free of
Excel-specific concerns and makes each later step independently re-runnable
against a fixed input. This stage also handles NA parsing per column, which
matters because ODM part IDs include literal values such as `NA` and `None` that
pandas would otherwise read as missing values.

**Stage 2 — transform.** A set of small modules each read the CSVs and write
Schemasheets TSVs. There is one module per kind of output — classes,
enumerations, the container class, prefixes, and schema metadata — and every one
of them is both an importable function and a standalone CLI. This is where all
the dataset-specific knowledge lives.

**Stage 3 — generate.** `schemasheets_utils.make_linkml_schema_from_schemasheets`
runs Schemasheets over every `.tsv` in the directory and returns a
`SchemaDefinition`. It then calls `fix_schemasheets_generated_schema` to correct
known Schemasheets shortcomings, and the ODM pipeline applies one further
post-processing step (`add_missingness_set`) before the YAML is written.

### Post-processing workarounds

Two Schemasheets limitations are worked around after generation, in
`schemasheets_utils.fix_schemasheets_generated_schema`. Both are worth knowing
about, because each one has a matching convention earlier in the pipeline:

- **Empty permissible values.** Schemasheets treats a blank `permissible_value`
  cell as metadata for the enumeration itself rather than as a permissible value
  equal to `""`. Both dictionaries need genuinely empty permissible values (used
  for "not applicable" and similar), so the extraction modules write the
  sentinel `general_utils.EMPTY_PERMISSIBLE_VALUE` (`<empty>`) instead, and
  post-processing replaces it with `""`.
- **Numeric bounds as strings.** Schemasheets emits `minimum_value` and
  `maximum_value` as strings, which breaks downstream LinkML tools such as the
  validator. Post-processing converts them to `int` or `float`.

The same function also splits a comma-separated `range` string into a list, for
slots that accept more than one range.

## Repository structure

```text
odm_linkmlgen/          # The Python package
│
├── make_odm.py         # CLI + function: ODM v2+ schema generation
├── make_odm_v1.py      # CLI: ODM v1 schema generation
├── make_nwss.py        # CLI + function: NWSS schema generation
│
├── odm/                # ODM-specific extraction modules (stage 2)
│   ├── odm_utils.py                    # Shared ODM parts-sheet helpers
│   ├── make_odm_ss_classes.py          # One Schemasheet per ODM table
│   ├── make_odm_ss_container.py        # The tree_root Container class
│   ├── make_odm_ss_enums_from_sets.py  # Enums defined in the sets sheet
│   ├── make_odm_ss_enums_from_parts.py # Enums defined in the parts sheet
│   ├── make_odm_ss_prefixes.py         # CURIE prefixes
│   └── make_odm_ss_schema.py           # Schema-level metadata
│
├── nwss/               # NWSS-specific extraction modules (stage 2)
│   ├── nwss_utils.py                   # Shared NWSS sheet-parsing helpers
│   ├── make_nwss_ss_classes.py         # Schemasheet(s) for the NWSS tables
│   ├── make_nwss_ss_container.py       # The tree_root Container class
│   ├── make_nwss_ss_enums.py           # Enums from the Value Sets sheet
│   ├── make_nwss_ss_prefixes.py        # CURIE prefixes
│   └── make_nwss_ss_schema.py          # Schema-level metadata
│
├── utils/              # Dataset-agnostic utilities
│   ├── general_utils.py        # DataFrame helpers, Excel/CSV I/O, logging
│   ├── schemasheets_utils.py   # Schemasheets file creation and generation
│   └── schema_utils.py         # SchemaDefinition inspection helpers
│
└── data/               # Bundled source data
    ├── odm_v1/schemasheets/    # Hand-written ODM v1 Schemasheets (stage 2
    │                           # output, so ODM v1 skips stages 1 and 2)
    ├── odm_v2/, odm_v3/        # Where to put the ODM Excel dictionaries
    └── nwss/                   # Where to put the NWSS Excel dictionaries
                                # (all Excel dictionaries are git-ignored, so
                                # you must obtain them yourself — see README)

docs/                   # This documentation
tests/                  # pytest unit tests
```

The `odm/` and `nwss/` module names follow a convention: `make_<dataset>_ss_*`,
where `ss` stands for Schemasheets. Each such module produces one kind of
Schemasheets file.

For the functions each module exposes, see the
[Module reference](module-reference.md).

## Why the two pipelines are not shared

The ODM and NWSS pipelines have the same shape but almost no shared
dataset-specific code, because the source dictionaries have little in common:
ODM packs table membership, keys, and enumeration membership into relationships
between columns of one parts sheet, while NWSS lists fields per table in a flat
sheet and keeps enumerations in a side-by-side column layout. What they do share
lives in `odm_linkmlgen/utils/`: Excel and CSV I/O, DataFrame manipulation,
Schemasheets file writing, and the schema generation and post-processing step.
