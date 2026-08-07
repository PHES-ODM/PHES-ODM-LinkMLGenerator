# Install the package

Requires **Python 3.10 or newer**.

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

`pip install -e .` installs `odm_linkmlgen` in editable mode and registers three
commands:

| Command | Generates |
| --- | --- |
| `odm-linkmlgen-odm` | An ODM v2+ schema |
| `odm-linkmlgen-odmv1` | The ODM v1 schema |
| `odm-linkmlgen-nwss` | One schema per NWSS dictionary type supplied |

Pass `--help` to any of them for the available options, or see the
[CLI reference](../reference/cli.md).

## Check the installation

Generate the ODM v1 schema, which needs no source Excel file:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

A file should appear at `gen/odm_v1/linkml/odm_v1.yaml`.

## Troubleshooting

**`command not found`** — the virtual environment is not active. Run
`source .env/bin/activate`.

**`--help` crashes with `Parameter.make_metavar() missing 1 required positional
argument: 'ctx'`** — your `typer` is older than 0.16.0, which is the first
release compatible with `click` 8.2+. `requirements.txt` pins this, so
re-running `pip install -r requirements.txt` in the active environment fixes it.

## Installing for development

To also get `pytest`, `pytest-cov`, and `ruff`, install
`requirements-dev.txt` instead — see
[Set up a development environment](set-up-a-development-environment.md).

## Next

You now need a source data dictionary for anything other than ODM v1:

- [Prepare the ODM data dictionary](prepare-the-odm-dictionary.md)
- [Prepare the NWSS data dictionaries](prepare-the-nwss-dictionaries.md)
