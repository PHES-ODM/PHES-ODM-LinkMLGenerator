# Contributing

Thanks for contributing to the PHES-ODM LinkML Schema Generator.

The full development guide lives in the documentation site, so that it sits
alongside the rest of the project's how-to guides rather than drifting apart from
them:

**→ [Set up a development environment](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/set-up-a-development-environment/)**

It covers the dev install, running the tests, linting, and the code conventions
new code is expected to match.

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
| Work out why a generated schema is wrong | [Debug a generated schema](docs/how-to/debug-a-generated-schema.md) |
| Re-run one pipeline step while iterating | [Re-run a single pipeline step](docs/how-to/run-a-single-pipeline-step.md) |
| Support a new ODM version | [Add support for a new ODM version](docs/how-to/add-an-odm-version.md) |
| Support a new NWSS dictionary type | [Add support for a new NWSS dictionary type](docs/how-to/add-an-nwss-dictionary-type.md) |
| Change the documentation | [Update the documentation](docs/how-to/update-the-documentation.md) |
| Understand why the code is shaped this way | [How the pipeline is designed](docs/explanation/pipeline-design.md) |

## A note on testing

The tests cover the pure helper functions only. The extraction modules and the
two end-to-end pipelines are **not** covered, because both depend on Excel
dictionaries that cannot be committed (NWSS) or are large and awkward to fixture
(ODM).

So if you change an extraction module, verify it by regenerating the schema and
diffing the output against the previous version, and account for every line of
the diff. See
[Debug a generated schema](docs/how-to/debug-a-generated-schema.md).

## Documentation changes

The documentation follows the
[Divio system](https://docs.divio.com/documentation-system/): tutorials, how-to
guides, explanation, and reference are four distinct kinds of writing. Before
adding a page, check which one it belongs to — the
[documentation guide](docs/how-to/update-the-documentation.md#where-things-go)
has a table for this.

Markdown is wrapped at 80 columns, except inside tables, code blocks, and long
URLs.
