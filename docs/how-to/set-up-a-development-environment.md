# Set up a development environment

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements-dev.txt
pip install -e . --no-deps
```

`requirements-dev.txt` includes `requirements.txt`, plus `pytest`,
`pytest-cov`, and `ruff`.

Python 3.10 or newer is required, and **CI runs on 3.10**, so avoid syntax and
standard-library features newer than that.

## Tests

```console
pytest                        # all tests
pytest -v                     # one line per test
pytest tests/test_odm_utils.py
pytest --cov=odm_linkmlgen
```

Tests live in `tests/`, one module per source module under test, and are run in
CI by `.github/workflows/pytest.yaml`.

### What is and is not covered

The tests cover the **pure helper functions** — `general_utils`, `schema_utils`,
`odm_utils`, and `nwss_utils` — by constructing small DataFrames inline.

The extraction modules and the two end-to-end pipelines are **not** covered,
because both depend on Excel dictionaries that cannot be committed (NWSS) or are
large and awkward to fixture (ODM). If you change an extraction module, verify
it by regenerating the schema and diffing the output — see
[Debug a generated schema](debug-a-generated-schema.md).

### Writing new tests

Follow the existing style: plain `assert`, no fixtures unless shared, grouped
under a `# --- function_name ---` comment, and named
`test_<function>_<behaviour>`.

## Linting and formatting

Ruff handles both, with its default configuration — there is no `[tool.ruff]`
section in `pyproject.toml`.

CI runs these two checks via `.github/workflows/lint.yaml`, and both must pass:

```console
ruff check          # lint
ruff format --diff  # formatting check, shows what would change
```

To apply fixes locally:

```console
ruff check --fix
ruff format
```

## Building the documentation

```console
pip install -r requirements-docs.txt
mkdocs serve
```

See [Update the documentation](update-the-documentation.md).

## Code conventions

The codebase is consistent about the following, and new code should match.

**Google-style docstrings on every module, function, and class**, with `Args:`,
`Returns:`, and `Raises:` sections including types. This project has full
docstring coverage; keep it that way — the
[API reference](../reference/api/index.md) is generated from these docstrings,
so a missing one is a hole in the published documentation.

When a docstring names a constant, use the symbol rather than its literal value
(`DictionaryColumns.DATA_TYPE`, not `"Data Type"`), so the documentation cannot
drift from the code.

**Type annotations on every signature**, using the `X | None` form rather than
`Optional[X]`.

**Logging, not printing.** Every module starts with
`logger = get_logger(__name__)` and logs the files it reads and writes at
`INFO`. Errors in the source dictionary are usually logged and skipped rather
than raised, so that a single bad row does not abort a whole generation run —
see `_get_range_and_validation_info` for the pattern.

**Constants over literals for source-dictionary column names.** NWSS column
names live in `nwss_utils.DictionaryColumns`; ODM tags live in module-level
constants in `odm_utils`. Both dictionaries change between versions, and a named
constant gives you one place to update.

**One Schemasheets concern per module.** A module named `make_*_ss_<thing>`
produces the `<thing>` Schemasheets file and nothing else. Its column-to-LinkML
mapping goes in a module-level `headers` dict.

**Every step is both a function and a CLI.** Each extraction module exposes a
`typer` app with a `main` command that just forwards to the real function.
Option help text goes in `SCREAMING_CASE` module constants (`OUTPUT_DIR_HELP`,
…) so the signature stays readable. Keeping every step independently runnable is
what makes the pipeline debuggable, so preserve it when adding a step.

## Related

- [How the pipeline is designed](../explanation/pipeline-design.md)
- [Repository layout](../reference/repository-layout.md)
- [Add support for a new ODM version](add-an-odm-version.md)
- [Add support for a new NWSS dictionary type](add-an-nwss-dictionary-type.md)
