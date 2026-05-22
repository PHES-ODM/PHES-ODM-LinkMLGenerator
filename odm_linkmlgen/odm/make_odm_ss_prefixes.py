"""
Creates the Schemasheets prefixes table, which defines all prefixes used by the ODM schema.

## Example

```python
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes

make_prefixes("odm_v2/schemasheets/prefixes.tsv")
```
"""

from typing import Annotated
from pathlib import Path
import typer

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Creates the Schemasheets prefixes table, which defines
all prefixes used by the ODM schema."""

VERSION_HELP = """The ODM version number (eg. "2", "3")."""

OUTPUT_FILE_HELP = """The .tsv file to save the prefixes Schemasheet to."""

# The full prefixes schemasheet: Column names and values
_data = {
    "prefix": "odmv{version}",
    "prefix_reference": "https://onto.phes-odm.org/odm/v{version}/",
}


def get_prefixes_data(version: str) -> dict:
    """Get the prefixes metadata (for schemasheets), using the specified version.

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


def make_prefixes(version: str, output_file: str):
    """Make the prefixes Schemasheet for ODM. This sheet contains all the CURIE prefixes
    used by the dictionary.

    Args:
        version (str): The ODM version number (eg. "2", "3").
        output_file (str): The .tsv file to save the prefixes Schemasheet to.
    """
    if len(_data) > 0:
        save_schemasheet(get_prefixes_data(version), output_file)


@app.command(help=MAIN_HELP)
def main(
    version: Annotated[str, typer.Option(show_default=False, help=VERSION_HELP)],
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
):
    logger.info(f"Making ODM v{version} Prefixes...")
    make_prefixes(version=version, output_file=output_file)
    logger.info("Finished!")


if __name__ == "__main__":
    app()
