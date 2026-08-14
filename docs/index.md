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

To install it and generate a schema right now, go to
[Install the generator](how-to/install.md).

## How this documentation is organized

It follows the [Diátaxis documentation framework](https://diataxis.fr/), which
splits documentation into four kinds. Each answers a different question, so
start with the one that matches what you need.

### [Tutorial](tutorials/getting-started.md) — *learning*

A guided first run, start to finish. Read it once, in order.

- [Getting started](tutorials/getting-started.md) — install the generator,
  produce the ODM v3 schema, and look at what it contains

### [How-to guides](how-to/install.md) — *doing*

Steps for one task, assuming you already know roughly what you are doing.

| Guide | For |
| --- | --- |
| [Install the generator](how-to/install.md) | Getting the commands onto your path |
| [Generate the ODM schemas](how-to/generate-odm-schemas.md) | v1, v2, and v3, and the dictionary they need |
| [Generate the NWSS schemas](how-to/generate-nwss-schemas.md) | The five CDC dictionaries, and the manual fixes they need |
| [Use it from Python](how-to/python-api.md) | Calling the generators, and re-running a single step |
| [Troubleshooting](how-to/troubleshooting.md) | Working out why a generated schema is wrong |
| [Extending the generator](how-to/extending.md) | Supporting a new ODM version or NWSS dictionary type |
| [Contributing](how-to/contributing.md) | Changing the code or the documentation |

### [Reference](reference/cli.md) — *looking up*

Dry, complete descriptions of what is there.

| Page | Describes |
| --- | --- |
| [Command-line interface](reference/cli.md) | Every command and option |
| [Pipeline steps](reference/pipeline-steps.md) | What each step of both pipelines reads and writes |
| [Output layout](reference/output-layout.md) | Where a generation run writes every file |
| [Repository layout](reference/repository-layout.md) | Where the source files live, and which one to change |
| [The source data dictionaries](reference/data-dictionaries.md) | Which sheets and columns the generator reads |
| [Python API](reference/api.md) | Signatures and docstrings, generated from the source |

### [Explanation](explanation/how-it-works.md) — *understanding*

Background and design reasoning. Not needed to use the generator, but it is what
makes the rest of the project make sense.

| Page | Explains |
| --- | --- |
| [How it works](explanation/how-it-works.md) | LinkML, Schemasheets, the three-stage pipeline, and the post-processing workarounds |
| [Inside an ODM run](explanation/odm-runs.md) | What an ODM run leaves on disk, and how v1 and v2+ differ |
| [Inside an NWSS run](explanation/nwss-runs.md) | What an NWSS run leaves on disk, and why the output looks the way it does |
| [Why the dictionaries are hard to read](explanation/data-dictionaries.md) | What the two Excel files' irregularities cost, and what they silently break |
