"""
Make the ODM LinkML schema.
"""

import pandas as pd
from pathlib import Path
from typing import Annotated

import typer
from linkml_runtime.linkml_model.meta import SchemaDefinition

from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes
from odm_linkmlgen.odm.make_odm_ss_container import extract_container_class
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums
from odm_linkmlgen.odm.make_odm_ss_prefixes import make_prefixes
from odm_linkmlgen.odm.make_odm_ss_schema import make_schema
from odm_linkmlgen.odm.odm_utils import add_missingness_set
from odm_linkmlgen.utils.general_utils import (
    clear_dirs,
    extract_sheets,
    get_logger,
    get_na_values,
)
from odm_linkmlgen.utils.schema_utils import find_undefined_ranges
from odm_linkmlgen.utils.schemasheets_utils import (
    make_linkml_schema_from_schemasheets,
    save_schema_definition,
)

logger = get_logger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)

MAIN_HELP = """Make ODM v2 and above LinkML schema, using an ODM data dictionary. The dictionary
is either a single Excel file (--dictionary-file), or its parts and sets sheets already saved
as CSV files (--parts-file and --sets-file)."""

VERSION_HELP = """Version string of ODM to generate the schema for. eg. '2', '3'."""

DICTIONARY_FILE_HELP = """Location of the Excel data dictionary (parts/sets file) for ODM. If
set then the parts file and sets file must NOT be specified."""

OUTPUT_DIR_HELP = """Directory to save the LinkML schema to."""

PARTS_FILE_HELP = """Location of the dictionary parts file in CSV format. If set then the
sets file must also be specified, and the dictionary file must NOT be
specified."""

SETS_FILE_HELP = """Location of the dictionary sets file in CSV format. If set then the
parts file must also be specified, and the dictionary file must NOT be
specified."""


@app.command(help=MAIN_HELP)
def make_odm(
    version: Annotated[str, typer.Option(show_default=False, help=VERSION_HELP)],
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
    dictionary_file: Annotated[
        Path | None, typer.Option(show_default=False, help=DICTIONARY_FILE_HELP)
    ] = None,
    parts_file: Annotated[
        Path | None, typer.Option(show_default=False, help=PARTS_FILE_HELP)
    ] = None,
    sets_file: Annotated[
        Path | None, typer.Option(show_default=False, help=SETS_FILE_HELP)
    ] = None,
) -> SchemaDefinition | None:
    """Generate the LinkML schema for ODM.

    The data dictionary is supplied either as a single Excel file (dictionary_file), or as its
    parts and sets sheets already saved as CSV files (parts_file and sets_file). Exactly one of
    those two forms must be given: the CSV form is for regenerating a schema from the
    "{output_dir}/dictionary" files of a previous run, or from a dictionary that is maintained
    as CSV rather than as a workbook. Either way, the parts and sets are (re)written to
    "{output_dir}/dictionary" and every later step reads them from there.

    Args:
        version (str): The ODM version number we are making (eg. "2", "3")
        output_dir (Path): Location to save all output. The LinkML schema output is
            saved to "{output_dir}/linkml/odm_v{version}.yaml"
        dictionary_file (Path, optional): Location of the Excel data dictionary (parts/sets file)
            for ODM. If set then parts_file and sets_file must not be. Defaults to None.
        parts_file (Path, optional): Location of the dictionary parts file in CSV format. If set
            then sets_file must be set too, and dictionary_file must not be. Defaults to None.
        sets_file (Path, optional): Location of the dictionary sets file in CSV format. If set
            then parts_file must be set too, and dictionary_file must not be. Defaults to None.

    Returns:
        SchemaDefinition: The generated ODM LinkML schema definition, or None if the data
            dictionary files were not specified correctly (an error is logged in that case).
    """
    # Some paths
    output_dir = Path(output_dir)
    dictionary_dir = output_dir / "dictionary"
    schemasheets_dir = output_dir / "schemasheets"
    linkml_dir = output_dir / "linkml"

    # Clean up the output directories (ie. delete old csv, tsv, and yaml files)
    clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

    # The dictionary is either one Excel file or the two CSV files, never both and never
    # neither. This is logged and returned on rather than raised, the same as every other
    # input problem the pipeline reports.
    if dictionary_file is not None and (
        parts_file is not None or sets_file is not None
    ):
        logger.error(
            "Only one of dictionary_file or parts_file/sets_file must be specified"
        )
        return None
    elif dictionary_file is None and (parts_file is None or sets_file is None):
        logger.error("Both of parts_file and sets_file must be set")
        return None

    # Extract or copy the parts and sets tabs. Either way they end up at the same two paths
    # under dictionary_dir, so every step after this one has a single input to read.
    target_parts_file = dictionary_dir / "parts.csv"
    target_sets_file = dictionary_dir / "sets.csv"
    # Only a truly empty partID cell counts as missing: part IDs such as "NA", "None", and
    # "null" are real ODM parts that Pandas would otherwise read as missing values.
    na_values = {"parts": {"partID": ""}, "sets": {"partID": ""}}
    if dictionary_file is not None:
        # Extract the parts and sets sheets from the Excel ODM data dictionary file
        extract_sheets(
            dictionary_file,
            ["parts", "sets"],
            dictionary_dir,
            na_values=na_values,
        )
    else:
        # The CSV files are already the sheets, so there is nothing to extract. Load and
        # re-save them with the same na_values the Excel path uses, so that the copies under
        # dictionary_dir are parsed identically to an extracted sheet.
        parts_df = pd.read_csv(
            parts_file,
            na_values=get_na_values(parts_file, na_values=na_values["parts"]),
            keep_default_na=False,
        )
        sets_df = pd.read_csv(
            sets_file,
            na_values=get_na_values(sets_file, na_values=na_values["sets"]),
            keep_default_na=False,
        )
        dictionary_dir.mkdir(parents=True, exist_ok=True)
        parts_df.to_csv(target_parts_file, index=False)
        sets_df.to_csv(target_sets_file, index=False)
    parts_file = target_parts_file
    sets_file = target_sets_file

    # Extract all enums from the sets sheet (and save as a schemasheet)
    extract_sets_enums(sets_file, parts_file, schemasheets_dir / "enums_sets.tsv")

    # Extract all enums from the parts sheet (except for the mmaSet enums, which were extracted
    # above by extract_sets_enums) (and save as a schemasheet)
    extract_parts_enums(parts_file, schemasheets_dir / "enums_parts.tsv")

    # Extract all classes from the parts sheet (and save as a schemasheet)
    extract_all_classes(parts_file, schemasheets_dir)

    # Extract the Container class, which is the top-level LinkML class containing all
    # the tables.
    extract_container_class(parts_file, schemasheets_dir / "container.tsv")

    # Make the prefixes schemasheet
    make_prefixes(schemasheets_dir / "prefixes.tsv", version)

    # Make the schema definition schemasheet
    make_schema(schemasheets_dir / "schema.tsv", version)

    # Run Schemasheets to make the final LinkML schema
    schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

    # Add genMissingnessSet to all ranges where an enum must be paired with genMissingnessSet
    add_missingness_set(schema, parts_file)

    # Save the schema to disk
    save_schema_definition(schema, linkml_dir / f"odm_v{version}.yaml")

    # Report any slot left pointing at an element the schema does not define. The
    # schema is still written: this is reported the same way as every other data
    # dictionary defect, so that one bad part does not cost you the whole run. This
    # runs after add_missingness_set, so the ranges it checks are the final ones,
    # including the any_of pairings that step introduces.
    undefined_ranges = find_undefined_ranges(schema)
    for slot_name, ranges in undefined_ranges.items():
        logger.error(
            f"Slot {slot_name} has a range the schema does not define: "
            f"{', '.join(ranges)}. This usually means an enumeration named by the "
            "parts or sets sheet was never generated."
        )
    if undefined_ranges:
        logger.error(
            f"ODM v{version}: {len(undefined_ranges)} slot(s) have an undefined range, "
            "so the generated schema is not usable as it stands."
        )

    return schema


if __name__ == "__main__":
    app()
