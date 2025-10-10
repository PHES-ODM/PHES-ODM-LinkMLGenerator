"""
Make the ODM LinkML schema.
"""

from pathlib import Path
from typing import Annotated
import typer
from enum import Enum

from linkml_runtime.linkml_model.meta import SchemaDefinition

from odm_linkmlgen.utils.general_utils import clear_dirs, extract_sheets, get_logger
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
    save_schema_definition,
)
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.odm_utils import add_missingness_set

logger = get_logger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)

MAIN_HELP = """Make ODM v2 and above LinkML schema, using an ODM data dictionary file (Excel file)."""

VERSION_HELP = """Version string of ODM to generate the schema for. eg. '2', '3'."""

DICTIONARY_FILE_HELP = """Location of the Excel data dictionary (parts file) for ODM."""

OUTPUT_DIR_HELP = """Directory to save the LinkML schema to."""

MISSINGNESS_METHOD_HELP = """How to include the missingness set. If
'multi_range' then add the missingness set to a
slot's range by changing the range to a list. If
'merge' then combine the missingness set with the
permissible values of enumerations."""


class MissingnessMethods(str, Enum):
    multi_range = "multi_range"
    merge = "merge"


@app.command(help=MAIN_HELP)
def make_odm(
    version: Annotated[str, typer.Option(show_default=False, help=VERSION_HELP)],
    dictionary_file: Annotated[
        Path, typer.Option(show_default=False, help=DICTIONARY_FILE_HELP)
    ],
    output_dir: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)
    ],
    missingness_method: Annotated[
        MissingnessMethods, typer.Option(help=MISSINGNESS_METHOD_HELP)
    ] = MissingnessMethods.multi_range,
) -> SchemaDefinition:
    """Generate the LinkML schema for ODM.

    Args:
        version (str): The ODM version number we are making (eg. "2", "3")
        dictionary_file (Path): Location of the Excel data dictionary (parts file) for ODM.
        output_dir (Path): Location to save all output. The LinkML schema output is
            saved to "{output_dir}/linkml/odm_v{version}.yaml"
        missingness_method (str): How to include the missingness set. If 'multi_range' then add the missingness
            set to a slot's range by changing the range to a list. If 'merge' then combine the missingness set
            with the permissible values of enumerations.

    Returns:
        SchemaDefinition: The generated ODM LinkML schema definition.
    """
    # Some paths
    output_dir = Path(output_dir)
    dictionary_dir = output_dir / "dictionary"
    schemasheets_dir = output_dir / "schemasheets"
    linkml_dir = output_dir / "linkml"
    parts_file = dictionary_dir / "parts.csv"
    sets_file = dictionary_dir / "sets.csv"

    # Clean up the output directories (ie. delete old csv, tsv, and yaml files)
    clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

    # Extract the parts and sets sheets from the Excel ODM data dictionary file
    extract_sheets(
        dictionary_file,
        ["parts", "sets"],
        dictionary_dir,
        na_values={"parts": {"partID": ""}, "sets": {"partID": ""}},
    )

    # Extract all enums from the sets sheet (and save as a schemasheet)
    all_enums = extract_sets_enums(
        sets_file, parts_file, schemasheets_dir / "enums_sets.tsv"
    )

    # Extract all enums from the parts sheet (except for the mmaSet enums, which were extracted
    # above by extract_sets_enums) (and save as a schemasheet)
    all_enums += extract_parts_enums(parts_file, schemasheets_dir / "enums_parts.tsv")

    all_enums = list(dict.fromkeys(all_enums))

    # Extract all classes from the parts sheet (and save as a schemasheet)
    extract_all_classes(parts_file, schemasheets_dir, recognized_enums=all_enums)

    # Extract the Container class, which is the top-level LinkML class containing all
    # the tables.
    extract_container_class(parts_file, schemasheets_dir / "container.tsv")

    # Make the prefixes schemasheet
    make_prefixes(version, schemasheets_dir / "prefixes.tsv")

    # Make the schema definition schemasheet
    make_schema(version, schemasheets_dir / "schema.tsv")

    # Run Schemasheets to make the final LinkML schema
    schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

    # Add genMissingnessSet to all ranges where an enum must be paired with genMissingnessSet
    add_missingness_set(
        schema,
        dictionary_file=dictionary_file,
        lists_sheet="lists",
        method=missingness_method,
    )

    # Save the schema to disk
    save_schema_definition(schema, linkml_dir / f"odm_v{version}.yaml")

    return schema


if __name__ == "__main__":
    app()
