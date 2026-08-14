# Install the generator

Requires Python 3.10 or newer.

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

This registers three commands:

| Command | Generates |
| --- | --- |
| `odm-linkmlgen-odmv1` | The ODM v1 schema |
| `odm-linkmlgen-odm` | An ODM v2+ schema |
| `odm-linkmlgen-nwss` | One schema per NWSS dictionary type supplied |

Every command accepts `--help`; the full option lists are in the
[CLI reference](../reference/cli.md).

To also get `pytest`, `pytest-cov`, and `ruff`, install `requirements-dev.txt`
instead — see [Contributing](contributing.md).

## Next

- [Generate the ODM schemas](generate-odm-schemas.md)
- [Generate the NWSS schemas](generate-nwss-schemas.md)
- [Getting started](../tutorials/getting-started.md) — a guided first run, if
  you would rather work through one
