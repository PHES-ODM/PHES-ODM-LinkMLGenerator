# Contributing

## Set up a development environment

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

Before opening a pull request, run what CI runs:

```console
ruff check              # lint
ruff format --diff      # formatting
pytest                  # tests
mkdocs build --strict   # documentation (needs requirements-docs.txt)
```

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
[Troubleshooting](troubleshooting.md#diffing-against-a-known-good-schema).

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

## Code conventions

The codebase is consistent about the following, and new code should match.

**Google-style docstrings on every module, function, and class**, with `Args:`,
`Returns:`, and `Raises:` sections including types. This project has full
docstring coverage; keep it that way — the
[API reference](../reference/api.md) is generated from these docstrings, so a
missing one is a hole in the published documentation.

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

## Working on the documentation

The documentation is built with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme, and published to
GitHub Pages by `.github/workflows/docs.yaml`.

### Build it locally

```console
pip install -r requirements-docs.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000/>. The site rebuilds as you save.

Before pushing, run the same check CI does:

```console
mkdocs build --strict
```

`--strict` turns warnings into failures — broken internal links, pages missing
from the `nav`, and mkdocstrings references that cannot be resolved. If it
passes locally it will pass in CI.

The build does **not** need the runtime dependencies (`linkml`, `pandas`, …)
installed: mkdocstrings uses [griffe](https://mkdocstrings.github.io/griffe/),
which reads the source statically rather than importing it. That is why
`requirements-docs.txt` is separate from `requirements.txt`.

### Where things go

The site follows the
[Divio documentation framework](https://docs.divio.com/documentation-system/),
which is what the four directories under `docs/` are. **A new page belongs to
exactly one of them**, decided by what the reader is doing when they open it:

| Directory | Is for | Holds |
| --- | --- | --- |
| `tutorials/` | *Learning.* One guided run, read once, in order | `getting-started.md` — install, and the ODM v1 walkthrough |
| `how-to/` | *Doing.* Steps for one task, for a reader who already knows roughly what they want | Installing, generating the ODM and NWSS schemas, the Python API, troubleshooting, extending, contributing |
| `reference/` | *Looking up.* Dry, complete, no narrative | CLI options, pipeline steps, the output and repository layouts, the generated API |
| `explanation/` | *Understanding.* Background and design reasoning | `how-it-works.md`, `odm-runs.md`, `nwss-runs.md`, `data-dictionaries.md` |

`index.md` is the site's front door and belongs to no section: it says what the
project is, and links into the four.

The two rules that keep the split honest:

- **Commands live in `how-to/` only.** `how-to/generate-odm-schemas.md` and
  `how-to/generate-nwss-schemas.md` hold every generation command, and are kept
  deliberately in sync with the same sections of the repository `README.md` —
  change both together. `explanation/odm-runs.md` and
  `explanation/nwss-runs.md` describe what those runs produce and why, and must
  not duplicate the commands.
- **Reasoning lives in `explanation/` only.** A "why" paragraph in a how-to page
  usually belongs in `explanation/how-it-works.md` or
  `explanation/data-dictionaries.md`, with a link to it. Reference pages stay
  dry.

The site is otherwise deliberately small. Prefer adding a section to an existing
page over adding a new page — a page that would be shorter than a screen belongs
inside one of its neighbours.

A new page must be added to `nav:` in `mkdocs.yml` — `--strict` fails on a page
that exists but is not in the nav.

### Keeping it in sync with the code

Three things to check when you change the code:

- **Adding or removing a public function.** The
  [API reference](../reference/api.md) is generated from the source by
  mkdocstrings, so the signature and docstring update themselves. But the page
  lists modules explicitly — a new *module* needs adding there.
- **Adding, removing, or reordering a pipeline step.** Update
  [Pipeline steps](../reference/pipeline-steps.md), including the step count in
  its introduction.
- **Adding or renaming a CLI option.** Update the
  [CLI reference](../reference/cli.md).

Because the API reference is generated from docstrings, the docstrings *are*
documentation.

### House style

Markdown is wrapped at **80 columns**, except inside tables, code blocks, and
long URLs.

### How it is deployed

`.github/workflows/docs.yaml` has two jobs:

- **build** — runs on every push and pull request, with `mkdocs build --strict`.
  A pull request that breaks a link fails the check.
- **deploy** — runs only on `main`, publishing to GitHub Pages.

The site is at <https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/>.

!!! note "One-time repository setting"

    The deploy job uses the GitHub Actions Pages deployment flow, which requires
    **Settings → Pages → Build and deployment → Source** to be set to
    **GitHub Actions**. Until that is done the build job passes and the deploy
    job fails.

You can also trigger a rebuild by hand from the Actions tab — the workflow
declares `workflow_dispatch`.
