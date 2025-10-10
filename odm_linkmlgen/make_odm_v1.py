"""
Make the ODMv1 LinkML schema.
"""

import os
from typing import Annotated
from pathlib import Path
import typer

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import make_linkml_schema_from_schemasheets

logger = get_logger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)

MAIN_HELP = """Generate the ODM v1 LinkML Schema."""

OUTPUT_DIR_HELP = """Directory to save the ODM v1 schema to."""

SCHEMASHEETS_DIR = Path(os.path.dirname(__file__)) / "data" / "odm_v1" / "schemasheets"


@app.command(help=MAIN_HELP)
def main(
    output_dir: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)
    ],
):
    # Make the schema
    linkml_schema = output_dir / "linkml" / "odm_v1.yaml"
    make_linkml_schema_from_schemasheets(SCHEMASHEETS_DIR, linkml_schema)

    logger.info("Finished!")


if __name__ == "__main__":
    app()
