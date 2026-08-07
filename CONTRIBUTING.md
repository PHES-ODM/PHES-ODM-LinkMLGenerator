# Contributing

Development guide for the PHES-ODM LinkML Schema Generator. Read the
[README](README.md) first for installation, and
[Architecture](docs/architecture.md) for how the code is organised.

## Development setup

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements-dev.txt
pip install -e . --no-deps
```

`requirements-dev.txt` includes `requirements.txt`, plus `pytest`, `pytest-cov`,
and `ruff`. Python 3.10 or newer is required, and CI runs on 3.10, so avoid
syntax and standard-library features newer than that.

## Tests

```console
pytest              # all tests
pytest -v           # one line per test
pytest tests/test_odm_utils.py
pytest --cov=odm_linkmlgen
```

Tests live in [tests/](tests/), one module per source module under test, and are
run in CI by [.github/workflows/pytest.yaml](.github/workflows/pytest.yaml).

They cover the pure helper functions — `general_utils`, `schema_utils`,
`odm_utils`, and `nwss_utils` — by constructing small DataFrames inline. The
extraction modules and the two end-to-end pipelines are not covered by automated
tests, because both depend on Excel dictionaries that cannot be committed (NWSS)
or that are large and awkward to fixture (ODM). If you change an extraction
module, verify it by regenerating the schema and diffing the output; see
[Debugging a generated schema](#debugging-a-generated-schema).

New tests follow the existing style: plain `assert`, no fixtures unless shared,
grouped under a `# --- function_name ---` comment, and named
`test_<function>_<behaviour>`.

## Linting and formatting

Ruff handles both, with its default configuration (there is no `[tool.ruff]`
section in `pyproject.toml`). CI runs the two checks below via
[.github/workflows/lint.yaml](.github/workflows/lint.yaml), and both must pass:

```console
ruff check          # lint
ruff format --diff  # formatting check, shows what would change
```

To apply fixes locally:

```console
ruff check --fix
ruff format
```

## Code conventions

The codebase is consistent about the following, and new code should match.

**Google-style docstrings on every module, function, and class**, with `Args:`,
`Returns:`, and `Raises:` sections including types. This project has full
docstring coverage; keep it that way. When a docstring names a constant, use the
symbol rather than its literal value (`DictionaryColumns.DATA_TYPE`, not
`"Data Type"`), so the documentation cannot drift from the code.

**Type annotations on every signature**, using the `X | None` form rather than
`Optional[X]`.

**Logging, not printing.** Every module starts with
`logger = get_logger(__name__)`, and logs the files it reads and writes at
`INFO`. Errors in the source dictionary are usually logged and skipped rather
than raised, so a single bad row does not abort a whole generation run — see
`_get_range_and_validation_info` for the pattern.

**Constants over literals for source-dictionary column names.** NWSS column names
live in `nwss_utils.DictionaryColumns`; ODM tags live in module-level constants
in `odm_utils`. Both dictionaries change between versions, and a named constant
gives you one place to update.

**One Schemasheets concern per module.** A module named `make_*_ss_<thing>`
produces the `<thing>` Schemasheets file and nothing else. Its column-to-LinkML
mapping goes in a module-level `headers` dict.

**Every step is both a function and a CLI.** Each extraction module exposes a
`typer` app with a `main` command that just forwards to the real function. Option
help text goes in `SCREAMING_CASE` module constants (`OUTPUT_DIR_HELP`, …) so the
signature stays readable. Keeping every step independently runnable is what makes
the pipeline debuggable, so preserve it when adding a step.

## Debugging a generated schema

The intermediate CSV and TSV files are the point of the three-stage layout —
when the final YAML is wrong, they tell you which stage went wrong.

1. **Check `dictionary/*.csv`.** Did the sheet extract as expected? The usual
   problem here is NA handling: a value such as `NA`, `None`, or `null` read as
   an empty cell. `extract_sheets` takes per-column `na_values` for exactly this
   reason.
2. **Check `schemasheets/*.tsv`.** This is where nearly all bugs live. Find the
   file for the class or enumeration in question and look at the row. Is the `>`
   header row mapping the columns you expect? Is the `range` the enumeration name
   you expected, or did it silently fall back to `string`?
3. **Re-run only the step you are working on**, against the CSVs already in
   `dictionary/`, instead of rebuilding from Excel each time:

   ```console
   python -m odm_linkmlgen.odm.make_odm_ss_classes \
       --parts-file "gen/odm_v3/dictionary/parts.csv" \
       --output-dir "gen/odm_v3/schemasheets"
   ```

   Note that `clear_dirs` runs only at the start of the full pipeline, so a
   partial re-run leaves the other TSVs in place. That is what you want when
   iterating, but it also means a renamed output can leave an orphan TSV behind
   that Schemasheets will still pick up.
4. **Check the final YAML** for symptoms of the post-processing steps: a
   `permissible_value` of `<empty>` that was not converted, a `minimum_value`
   still quoted as a string, or a missing `any_of` where a missingness set was
   expected. All three are handled in
   `schemasheets_utils.fix_schemasheets_generated_schema` and
   `odm_utils.add_missingness_set`.

## Adding support for a new ODM version

Schema-level metadata is templated on the version string, so a new version
usually needs no code changes at all:

- `make_odm_ss_schema._data` produces `ODMv{version}` and
  `https://onto.phes-odm.org/odm/v{version}`
- `make_odm_ss_prefixes._data` produces the `odmv{version}` prefix

So the steps are:

1. Obtain the dictionary and save it as `v{n} ODM dictionary.xlsx` under
   `odm_linkmlgen/data/odm_v{n}/`. Excel dictionaries are git-ignored, so it
   stays local to your checkout. See
   [Preparing the ODM data dictionary](docs/odm-pipeline.md#preparing-the-odm-data-dictionary)
   — the file must be opened only with a recent version of Excel.
2. Run `odm-linkmlgen-odm --version {n} --dictionary-file ... --output-dir ...`.
3. Diff the new schema against the previous version's and account for every
   change.

Where a new version will break, and what to check:

- **New or renamed parts sheet columns.** `extract_class` raises a
  `RuntimeError` naming any column it requires but cannot find. A column that
  became optional needs adding to `optional_keep_cols`, as `fKAliasID` was.
- **New `dataType` values.** An unrecognized data type passes through to the
  range unchanged, producing a dangling range rather than an error. Add it to
  `_data_types_map`.
- **Enumeration names that do not follow the `partID` + `s` convention.** Add
  them to `odm_utils._odm_enum_name_exceptions`. The symptom is a slot whose
  range fell back to `string`.
- **A new table.** Picked up automatically, as long as it has the `{table}`,
  `{table}Required`, and `{table}Order` column trio.

## Adding support for a new NWSS dictionary type

Add a branch in `make_nwss` for the new type, setting the metadata sheet name and
adding the type to the `dictionary_types` list along with a new CLI option. The
schema metadata, prefixes, and output directory are all derived from the type
name.

Then work through `_data_types_validation_info` in `make_nwss_ss_classes`: NWSS
data types are free-text prose, so a new dictionary is likely to describe types in
words the regex table does not yet match. Also read
[Preparing the NWSS data dictionaries](docs/nwss-pipeline.md#preparing-the-nwss-data-dictionaries),
which lists the manual Excel fixes the published files currently need — check
whether the new dictionary needs its own.

## Updating the documentation

Documentation lives in [docs/](docs/), indexed from the
[README](README.md#documentation):

| File | Contents |
| --- | --- |
| [README.md](README.md) | What the project is, install, quick start, library use |
| [docs/architecture.md](docs/architecture.md) | Concepts, pipeline shape, repository layout |
| [docs/odm-pipeline.md](docs/odm-pipeline.md) | The ODM generator, step by step |
| [docs/nwss-pipeline.md](docs/nwss-pipeline.md) | The NWSS generator, step by step |
| [docs/module-reference.md](docs/module-reference.md) | Every module and its public functions |
| CONTRIBUTING.md | This page |

Two things to keep in sync when you change the code:

- Adding or removing a public function means updating
  [docs/module-reference.md](docs/module-reference.md).
- Adding, removing, or reordering a pipeline step means updating the relevant
  pipeline page, including the worked example in
  [odm-pipeline.md](docs/odm-pipeline.md#running-the-steps-by-hand) if it applies.

Markdown is wrapped at 80 columns, except inside tables, code blocks, and long
URLs.
