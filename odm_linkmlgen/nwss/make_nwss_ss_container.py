"""
Create the Container class Schemasheet for NWSS. This is the top-level (tree_root) class that contains
all the top-level tables (eg. measures, protocols, etc.)
"""

from typing import Union, Optional, Annotated
from pathlib import Path
import typer

from odm_linkmlgen.utils.general_utils import read_data_frame, get_logger
from odm_linkmlgen.utils.schemasheets_utils import make_container_schemasheet
from odm_linkmlgen.nwss.nwss_utils import splitup_metadata_sheet, SINGLE_TABLE_NAME

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Extract and create the Schemasheets file for the top-level
Container class. This class contains a multivalued slot for each table found in
the NWSS data dictionary."""

METADATA_FILE_HELP = """The path to the Metadata sheet extracted from the
NWSS data dictionary."""

OUTPUT_FILE_HELP = """The TSV file to save the Container class Schemasheet to."""

SINGLE_TABLE_HELP = """If set then merge all classes into a single class called
nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate."""


def extract_container_class(
    metadata_file: Union[str, Path],
    output_file: Union[str, Path],
    single_table: Optional[bool] = False,
):
    """Extract and create the Schemasheets file for the top-level Container class. This class
    contains a multivalued slot for each table found in the NWSS data dictionary.

    Args:
        metadata_file (Union[str, Path]): The path to the Metadata sheet extracted from the
            NWSS data dictionary.
        output_file (Union[str, Path]): The TSV file to save the Container class Schemasheet to.
        single_table (Optional[bool]): If True then merge all classes into a single class called
            nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate. Defaults to False.
    """
    metadata_df = read_data_frame(metadata_file)
    all_tables = splitup_metadata_sheet(metadata_df)
    class_names = [SINGLE_TABLE_NAME] if single_table else list(all_tables.keys())
    class_titles = {name: name for name in class_names}
    make_container_schemasheet(class_names, output_file, class_titles=class_titles)


@app.command(help=MAIN_HELP)
def main(
    metadata_file: Annotated[
        Path, typer.Option(show_default=False, help=METADATA_FILE_HELP)
    ],
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
    single_table: Annotated[
        bool, typer.Option(show_default=True, help=SINGLE_TABLE_HELP)
    ] = False,
):
    logger.info("Making NWSS Container class...")
    extract_container_class(
        metadata_file=metadata_file, output_file=output_file, single_table=single_table
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
