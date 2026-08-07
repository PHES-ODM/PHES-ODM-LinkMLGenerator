# PHES-ODM LinkML Schema Generator

This project turns Excel data dictionaries into [LinkML](https://linkml.io/)
schemas for two wastewater surveillance datasets:

- **[PHES-ODM](https://phes-odm.org)** — the Public Health Environmental
  Surveillance Open Data Model (versions 1, 2, and 3+)
- **[CDC NWSS](https://www.cdc.gov/nwss/wastewater-surveillance.html)** — the
  Centers for Disease Control and Prevention National Wastewater Surveillance
  System

The output is a single `.yaml` LinkML schema per dataset — per ODM version, or
per NWSS dictionary type. Those schemas can then be used by any LinkML tool: to
validate a data file, or to generate documentation, JSON Schema, SQL DDL, or
Python classes.

## Where to start

This documentation follows the [Divio documentation
system](https://docs.divio.com/documentation-system/), which splits writing into
four kinds. Each answers a different question, so pick the one that matches what
you are doing right now.

<div class="grid cards" markdown>

- :material-school: **[Tutorials](tutorials/index.md)**

    ---

    *Learning-oriented.* Start here if the project is new to you. Follow along
    from an empty checkout to a generated schema you can open and read.

    [Generate your first schema →](tutorials/generate-your-first-schema.md)

- :material-wrench: **[How-to guides](how-to/index.md)**

    ---

    *Goal-oriented.* Recipes for a specific job you already know you need to do:
    generate an ODM v3 schema, debug an unexpected result, add support for a new
    dictionary version.

    [Browse the guides →](how-to/index.md)

- :material-lightbulb: **[Explanation](explanation/index.md)**

    ---

    *Understanding-oriented.* Background and design reasoning: what LinkML and
    Schemasheets are, why the pipeline has three stages, and why the two
    dataset pipelines share so little code.

    [Read the background →](explanation/index.md)

- :material-book-open-variant: **[Reference](reference/index.md)**

    ---

    *Information-oriented.* Dry descriptions of what exists: the CLI commands,
    the output layout, every pipeline step in order, and the full Python API
    generated from the source.

    [Look something up →](reference/index.md)

</div>

## The short version

Install the package and generate the ODM v1 schema, which needs no external
files:

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .

odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

The schema is written to `gen/odm_v1/linkml/odm_v1.yaml`. For anything else —
ODM v2+, or NWSS — you first need a source Excel dictionary; see
[Prepare the ODM data dictionary](how-to/prepare-the-odm-dictionary.md) or
[Prepare the NWSS data dictionaries](how-to/prepare-the-nwss-dictionaries.md).

## Contributing

Development setup, tests, linting, and code conventions are in
[Set up a development environment](how-to/set-up-a-development-environment.md).
