"""
Create the Container class Schemasheet for ODM. This is the top-level (tree_root) class that contains
all the top-level tables (eg. measures, protocols, etc.)
"""

from pathlib import Path
from typing import Annotated

import typer

from odm_linkmlgen.odm.odm_utils import (
    get_dictionary_read_kwargs,
    odm_get_available_class_names,
)
from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import make_container_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Create the Container class Schemasheet for ODM. This is the
top-level (tree_root) class that contains all the top-level tables (eg.
measures, protocols, etc.)"""

PARTS_FILE_HELP = """The parts sheet (CSV) that was extracted from the ODM data
dictionary."""

OUTPUT_FILE_HELP = """The TSV file to save the Container class Schemasheet to."""


def extract_container_class(parts_file: str | Path, output_file: str | Path):
    """Extract and create the Schemasheets file for the top-level Container class. This class
    contains a multivalued slot for each table found in the ODM data dictionary.

    Args:
        parts_file (str | Path): The ODM data dictionary parts file.
        output_file (str | Path): The TSV file to save the Container class Schemasheet to.
    """
    parts_df = read_data_frame(parts_file, **get_dictionary_read_kwargs(parts_file))
    class_names = odm_get_available_class_names(parts_df)
    logger.info(f"Saving Schemasheets container to {output_file}")
    make_container_schemasheet(class_names, output_file)


@app.command(help=MAIN_HELP)
def main(
    parts_file: Annotated[Path, typer.Option(show_default=False, help=PARTS_FILE_HELP)],
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
):
    """CLI entry point: create the Container class Schemasheet for ODM, the top-level
    (tree_root) class that contains all the ODM tables.

    Args:
        parts_file (Path): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_file (Path): The TSV file to save the Container class Schemasheet to.
    """
    logger.info("Making ODM Container class...")
    extract_container_class(parts_file=parts_file, output_file=output_file)
    logger.info("Finished!")


if __name__ == "__main__":
    app()
