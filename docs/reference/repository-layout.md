# Repository layout

Where the source files live in a checkout.

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
│   ├── make_odm_ss_enums_from_sets.py  # Enums defined in the sets file
│   ├── make_odm_ss_enums_from_parts.py # Enums defined in the parts file
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
│   ├── general_utils.py        # DataFrame helpers, CSV/Excel I/O, logging
│   ├── schemasheets_utils.py   # Schemasheets file creation and generation
│   └── schema_utils.py         # SchemaDefinition inspection helpers
│
└── data/               # Bundled source data
    ├── odm_v1/schemasheets/    # Hand-written ODM v1 Schemasheets (stage 2
    │                           # output, so ODM v1 skips stages 1 and 2)
    ├── odm_v2/, odm_v3/        # Where to put the ODM dictionary: the published
    │                           # parts/sets CSV tables, or the Excel workbook
    └── nwss/                   # Where to put the NWSS Excel dictionaries

schemas/                # The one generated schema that IS committed:
│                       # odm_v3.yaml, written by the Generate ODM Schema
│                       # workflow. Everything else the generator produces
│                       # goes to the git-ignored gen/.
│
docs/                   # This documentation
tests/                  # pytest unit tests
.github/
├── workflows/          # CI: lint.yaml, pytest.yaml, docs.yaml,
│                       # generate-odm-schema.yaml and
│                       # rollout-dictionary-update.yaml
├── actions/            # Steps more than one workflow needs: odm-config loads
│                       # the shared settings, generate-odm-schema downloads
│                       # the tables and runs the generator
├── scripts/            # publish_rollout.py, which the rollout workflow uses
│                       # to write its output to other repositories
├── odm-config.env      # Which dictionary is read, which version is generated
└── odm-rollout.yaml    # Where a rollout publishes to
mkdocs.yml              # Documentation site configuration
```

See [Continuous integration](continuous-integration.md) for what each workflow
does, and why `schemas/odm_v3.yaml` is the exception to "no generated output is
committed".

!!! note "No data dictionaries are committed"

    Every `.xlsx` under `data/` is git-ignored, and so is every `.csv` under
    `data/odm_v*/` — the ODM dictionary tables are downloaded from the PHES-ODM
    repository, the ODM workbook is not publicly available, and the NWSS ones
    are downloaded from cdc.gov. See
    [Get the dictionary tables](../how-to/generate-odm-schemas.md#get-the-dictionary-tables)
    and [Get the NWSS dictionaries](../how-to/generate-nwss-schemas.md#get-the-dictionaries).

## The naming convention

Modules under `odm/` and `nwss/` follow the pattern `make_<dataset>_ss_<thing>`,
where **`ss` stands for Schemasheets**. Each such module produces one kind of
Schemasheets file and nothing else, and declares its column-to-LinkML mapping in
a module-level `headers` dict.

The two pipelines are deliberate near-mirrors of each other. They share no
dataset-specific code — see
[why the two pipelines are not shared](../explanation/how-it-works.md#why-the-two-pipelines-are-not-shared).

## Where to look for what

| If you are changing… | Look in |
| --- | --- |
| How a source column maps to LinkML | The `headers` dict in the relevant `make_*_ss_*` module |
| ODM data type → LinkML range | `_data_types_map` in `odm_utils` |
| NWSS data type prose → range + pattern | `_data_types_validation_info` in `make_nwss_ss_classes` |
| How an ODM slot's range is resolved | `odm_get_data_type_of_row` in `odm_utils` (the part's `mmaSet`, else its mapped `dataType`) |
| A NWSS source column name | `DictionaryColumns` in `nwss_utils` |
| Schema name / id / prefix templates | `_data` in `make_odm_ss_schema` and `make_odm_ss_prefixes`; `SCHEMA_VALUES_TEMPLATE` in `make_nwss` |
| CSV or Excel reading | `general_utils` |
| How an ODM dictionary file is read (NA values, `partID`/`label` as strings) | `get_dictionary_read_kwargs` in `odm_utils` |
| Post-generation schema fixes | `schemasheets_utils.fix_schemasheets_generated_schema`, `odm_utils.add_missingness_set` |

## Requirements files

| File | Contents |
| --- | --- |
| `requirements.txt` | Runtime: `pandas`, `linkml`, `schemasheets`, `openpyxl`, `typer` |
| `requirements-dev.txt` | Includes the above, plus `pytest`, `pytest-cov`, `ruff` |
| `requirements-docs.txt` | `mkdocs`, `mkdocs-material`, `mkdocstrings[python]` only |

`requirements-docs.txt` is deliberately independent of the runtime
dependencies: mkdocstrings reads the source statically, so the documentation
builds without `linkml` or `pandas` installed.

## Related

- [Output layout](output-layout.md) — what a generation run writes to
  `--output-dir`
- [Contributing](../how-to/contributing.md) — the dev install, the tests, and
  the code conventions new code is expected to match
