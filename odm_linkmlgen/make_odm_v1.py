"""
Make the ODMv1 LinkML schema.
"""

import os
from pathlib import Path
from typing import Annotated

import typer

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schema_utils import find_undefined_ranges
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
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
):
    """CLI entry point: generate the ODM v1 LinkML schema from the bundled Schemasheets
    files in SCHEMASHEETS_DIR.

    Args:
        output_dir (Path): Directory to save the ODM v1 schema to. The schema is saved to
            "{output_dir}/linkml/odm_v1.yaml".
    """
    # Make the schema
    linkml_schema = output_dir / "linkml" / "odm_v1.yaml"
    schema = make_linkml_schema_from_schemasheets(SCHEMASHEETS_DIR, linkml_schema)

    # Report any slot left pointing at an element the schema does not define. The
    # schema is still written, matching how make_odm and make_nwss report the same
    # problem. Here the source is the bundled Schemasheets rather than a data
    # dictionary, so this catches an editing mistake in them rather than an upstream
    # defect.
    undefined_ranges = find_undefined_ranges(schema)
    for slot_name, ranges in undefined_ranges.items():
        logger.error(
            f"Slot {slot_name} has a range the schema does not define: "
            f"{', '.join(ranges)}. This usually means an enumeration named by the "
            "bundled Schemasheets was never generated."
        )
    if undefined_ranges:
        logger.error(
            f"ODM v1: {len(undefined_ranges)} slot(s) have an undefined range, so the "
            "generated schema is not usable as it stands."
        )

    logger.info("Finished!")


if __name__ == "__main__":
    app()
