# Contributing

Thanks for contributing to the PHES-ODM LinkML Schema Generator.

The full development guide lives in the documentation site, so that it sits
alongside the rest of the project's guides rather than drifting apart from them:

**→ [Contributing](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/contributing/)**

It covers the dev install, running the tests, linting, the code conventions new
code is expected to match, and how to work on the documentation itself.

## Quick start

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements-dev.txt
pip install -e . --no-deps
```

Before opening a pull request, run what CI runs:

```console
ruff check              # lint
ruff format --diff      # formatting
pytest                  # tests
mkdocs build --strict   # documentation (needs requirements-docs.txt)
```

Python 3.10 or newer is required, and **CI runs on 3.10**, so avoid syntax and
standard-library features newer than that.

## Other guides you are likely to need

| Task | Guide |
| --- | --- |
| Work out why a generated schema is wrong | [Troubleshooting](docs/troubleshooting.md) |
| Re-run one pipeline step while iterating | [Use it from Python](docs/python-api.md#re-run-a-single-step) |
| Support a new ODM version or NWSS dictionary type | [Extending the generator](docs/extending.md) |
| Understand why the code is shaped this way | [How it works](docs/how-it-works.md) |

## A note on testing

The tests cover the pure helper functions only. The extraction modules and the
two end-to-end pipelines are **not** covered, because both depend on Excel
dictionaries that cannot be committed (NWSS) or are large and awkward to fixture
(ODM).

So if you change an extraction module, verify it by regenerating the schema and
diffing the output against the previous version, and account for every line of
the diff. See [Troubleshooting](docs/troubleshooting.md).

## Documentation changes

The site is deliberately small: one page per topic, plus a `docs/reference/`
directory for dry lookup material. Prefer adding a section to an existing page
over adding a new page, and keep instructions and reasoning apart — a "why"
paragraph usually belongs in `how-it-works.md` or `data-dictionaries.md` with a
link to it. A new page must be added to `nav:` in `mkdocs.yml`.

Markdown is wrapped at 80 columns, except inside tables, code blocks, and long
URLs.
