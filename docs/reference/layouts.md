# Output and repository layout

## Output layout

Every generator writes up to three subdirectories inside the `--output-dir` you
give it, one per pipeline stage:

```text
<output_dir>/
├── dictionary/     # Stage 1: intermediate CSVs extracted from the source Excel file
├── schemasheets/   # Stage 2: intermediate TSVs (the input to Schemasheets)
└── linkml/         # Stage 3: the final LinkML YAML schema
```

The `dictionary/` and `schemasheets/` files are intermediate build artefacts.
They are kept on disk deliberately — see
[why the intermediate files are kept](../how-it-works.md#why-the-intermediate-files-are-kept)
and [Troubleshooting](../troubleshooting.md#a-generated-schema-is-wrong).

All three directories are cleared of `.csv`, `.tsv`, and `.yaml` files by
`clear_dirs` at the start of a full run. A
[partial re-run](../python-api.md#re-run-a-single-step) does not clear anything.

### ODM v2+

For `--output-dir gen/odm_v3 --version 3`:

```text
gen/odm_v3/
├── dictionary/
│   ├── parts.csv
│   └── sets.csv
├── schemasheets/
│   ├── class_{class_name}.tsv    # One per ODM table
│   ├── enums_sets.tsv            # All enums defined in the sets sheet
│   ├── enums_parts.tsv           # All enums defined in the parts sheet
│   ├── container.tsv
│   ├── prefixes.tsv
│   └── schema.tsv
└── linkml/
    └── odm_v3.yaml
```

Note the asymmetry in how enumerations are grouped: **one TSV per class**, but
**one TSV per enumeration source sheet**, holding every enumeration from it.

### ODM v1

ODM v1 produces only the schema. Its Schemasheets are read in place from
`odm_linkmlgen/data/odm_v1/schemasheets/` and are not copied:

```text
gen/odm_v1/
└── linkml/
    └── odm_v1.yaml
```

### NWSS

`make_nwss` creates **a subdirectory per dictionary type**, each with its own
full set of three stage directories. For
`--output-dir gen/nwss --reporting ...`:

```text
gen/nwss/
└── nwss_reporting/
    ├── dictionary/
    │   ├── metadata.csv          # The metadata sheet, whatever it was named
    │   └── enums.csv             # The "Value Sets" sheet
    ├── schemasheets/
    │   ├── classes_nwss.tsv      # Single merged class (single_table=True)
    │   ├── enum_{enum_name}.tsv  # One per enumeration
    │   ├── container.tsv
    │   ├── prefixes.tsv
    │   └── schema.tsv
    └── linkml/
        └── nwss_reporting.yaml
```

Two things to note:

- The `dictionary/` CSV names are **fixed** at `metadata.csv` and `enums.csv`,
  even though the source sheet names vary by dictionary type. This is what keeps
  the later steps dictionary-type agnostic.
- There is normally **one** `classes_*.tsv`, named `classes_nwss.tsv`, because
  `make_nwss` always merges every table into a single class. Running the step by
  hand without `--single-table` produces one per table instead.

Enumeration file names include the per-field expansion where it applies, so you
will see `enum_vs_yne[stormwater_input].tsv` and similar rather than a single
`enum_vs_yne.tsv`.

## Repository layout

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

docs/                   # This documentation
tests/                  # pytest unit tests
.github/workflows/      # CI: lint.yaml, pytest.yaml, docs.yaml
mkdocs.yml              # Documentation site configuration
```

!!! note "No Excel dictionaries are committed"

    Every `.xlsx` under `data/` is git-ignored — the ODM dictionary is not
    publicly available, and the NWSS ones are downloaded from cdc.gov. You must
    obtain them yourself; see
    [Prepare the ODM dictionary](../index.md#prepare-the-dictionary-for-v2-and-above)
    and [Get the NWSS dictionaries](../index.md#get-the-dictionaries).

### The naming convention

Modules under `odm/` and `nwss/` follow the pattern `make_<dataset>_ss_<thing>`,
where **`ss` stands for Schemasheets**. Each such module produces one kind of
Schemasheets file and nothing else, and declares its column-to-LinkML mapping in
a module-level `headers` dict.

The two pipelines are deliberate near-mirrors of each other. They share no
dataset-specific code — see
[why the two pipelines are not shared](../how-it-works.md#why-the-two-pipelines-are-not-shared).

### Where to look for what

| If you are changing… | Look in |
| --- | --- |
| How a source column maps to LinkML | The `headers` dict in the relevant `make_*_ss_*` module |
| ODM data type → LinkML range | `_data_types_map` in `make_odm_ss_classes` |
| NWSS data type prose → range + pattern | `_data_types_validation_info` in `make_nwss_ss_classes` |
| An ODM enumeration name that won't resolve | `_odm_enum_name_exceptions` in `odm_utils` |
| A NWSS source column name | `DictionaryColumns` in `nwss_utils` |
| Schema name / id / prefix templates | `_data` in `make_odm_ss_schema` and `make_odm_ss_prefixes`; `default_schema_values` in `make_nwss` |
| Excel or CSV reading | `general_utils` |
| Post-generation schema fixes | `schemasheets_utils.fix_schemasheets_generated_schema`, `odm_utils.add_missingness_set` |

### Requirements files

| File | Contents |
| --- | --- |
| `requirements.txt` | Runtime: `pandas`, `linkml`, `schemasheets`, `openpyxl`, `typer` |
| `requirements-dev.txt` | Includes the above, plus `pytest`, `pytest-cov`, `ruff` |
| `requirements-docs.txt` | `mkdocs`, `mkdocs-material`, `mkdocstrings[python]` only |

`requirements-docs.txt` is deliberately independent of the runtime
dependencies: mkdocstrings reads the source statically, so the documentation
builds without `linkml` or `pandas` installed.
