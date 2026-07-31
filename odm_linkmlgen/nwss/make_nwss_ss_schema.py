"""
Creates the Schemasheets schema table for NWSS, which provides the top-level meta data about the NWSS
schema, such as the id, description of the schema, and the default prefix to use.

## Example

```python
from odm_linkmlgen.nwss.make_nwss_ss_schema import make_schema

make_schema("nwss/schemasheets/schema.tsv")
```
"""

import pandas as pd
from typing import Dict, Annotated, Union
import typer
from pathlib import Path

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Make the schema metadata Schemasheet for NWSS. This sheet
            contains top-level meta data about the NWSS LinkML schema, such as
            the id, description, and default prefix."""

OUTPUT_FILE_HELP = """The .tsv file to save the schema Schemasheet to."""

DICTIONARY_TYPE_HELP = """The dictionary type for this NWSS shema file. NWSS
has multiple formats, --dictionary-type identifies the format. (can be
"public_concentration", "public_metric", "reporting", "restricted_analytics",
or "restricted_raw")"""


# The default schema metadata schemasheet: Column names and values
# These are updated with values from the data_values dictionary passed to make_schema.
# NWSS has multiple data dictionaries (eg. one for reporting, for metric, and for concentration)
# so the schema metadata will be different for each.
default_data = {
    # "schema" : "NWSS",
    # "id" : "https://www.cdc.gov/nwss/reporting.html",
    # "description" : "National Wastewater Surveillance System (NWSS)",
    # "default_prefix" : "nwss",
}


def make_schema(output_file: Union[str, Path], data_values: Dict = {}):
    """Make the schema metadata Schemasheet for NWSS. This sheet contains top-level meta data
    about the NWSS LinkML schema, such as the id, description, and default prefix.

    Args:
        output_file (str): The .tsv file to save the schema Schemasheet to.
        data_values (Dict): Update the default schema data with these values when saving the schema.
            They should be key-value pairs where the key is the Schemasheets header.
    """
    use_data = default_data.copy()
    if data_values is not None:
        use_data.update(data_values)

    df = pd.DataFrame(use_data, columns=use_data.keys(), index=[0])
    logger.info(f"Saving schema to '{output_file}'")
    save_schemasheet(df, output_file, use_data.keys())


@app.command(help=MAIN_HELP)
def main(
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
    dictionary_type: Annotated[
        str, typer.Option(show_default=False, help=DICTIONARY_TYPE_HELP)
    ],
):
    """CLI entry point: make the schema metadata Schemasheet for NWSS, which contains the
    top-level meta data about the schema (id, description, and default prefix). The metadata
    is derived from dictionary_type, since each NWSS dictionary gets its own schema.

    Args:
        output_file (Path): The .tsv file to save the schema Schemasheet to.
        dictionary_type (str): The dictionary type for this NWSS schema file.
    """
    data_values = {
        "schema": f"NWSS_{dictionary_type}",
        "id": f"https://onto.phes-odm.org/nwss/{dictionary_type}",
        "description": f"National Wastewater Surveillance System (NWSS-{dictionary_type})",
        "default_prefix": f"nwss_{dictionary_type}",
    }
    logger.info("Making NWSS Schema...")
    make_schema(output_file=output_file, data_values=data_values)
    logger.info("Finished!")


if __name__ == "__main__":
    app()
