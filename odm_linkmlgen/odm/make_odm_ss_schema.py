"""
Creates the Schemasheets schema table, which provides the top-level meta data about the ODM
schema, such as the id, description of the schema, and the default prefix to use.

## Example

```python
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema

make_schema("odm_v2/schemasheets/schema.tsv")
```
"""

from pathlib import Path
from typing import Annotated

import typer

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Creates the Schemasheets schema table, which provides the
top-level meta data about the ODM schema, such as the id, description of the
schema, and the default prefix to use."""

VERSION_HELP = """The ODM version number (eg. "2", "3")."""

OUTPUT_FILE_HELP = """The .tsv file to save the schema Schemasheet to."""


# The full schema metadata schemasheet: Column names and values
_data = {
    "schema": "ODMv{version}",
    "id": "https://onto.phes-odm.org/odm/v{version}",
    "description": "Data model for the Public Health Environmental Surveillance Open Data Model, version {version}",
    "default_prefix": "odmv{version}",
}


def get_schema_data(version: str) -> dict:
    """Get the schema metadata (for schemasheets), using the specified version.

    Args:
        version (str): The version (eg. "2", "3")

    Returns:
        dict: The metadata to use for schemasheets.
    """
    d = {}
    for k, v in _data.items():
        if isinstance(v, str):
            v = v.format(version=version)
        d[k] = v
    return d


def make_schema(output_file: str, version: str):
    """Make the schema metadata Schemasheet for ODM. This sheet contains top-level meta data
    about the ODM LinkML schema, such as the id, description, and default prefix.

    Args:
        output_file (str): The .tsv file to save the schema Schemasheet to.
        version (str): The version of ODM that the schema is for (eg. "2", "3").
    """
    if len(_data) > 0:
        save_schemasheet(get_schema_data(version), output_file)


@app.command(help=MAIN_HELP)
def main(
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
    version: Annotated[str, typer.Option(show_default=False, help=VERSION_HELP)],
):
    """CLI entry point: create the Schemasheets schema table, which provides the top-level
    meta data about the ODM schema, such as the id, description, and default prefix.

    Args:
        output_file (Path): The .tsv file to save the schema Schemasheet to.
        version (str): The ODM version number (eg. "2", "3").
    """
    logger.info(f"Making ODM v{version} Schema...")
    make_schema(output_file=output_file, version=version)
    logger.info("Finished!")


if __name__ == "__main__":
    app()
