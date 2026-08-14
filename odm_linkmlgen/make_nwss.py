"""
Make the NWSS LinkML schemas. One schema is generated per NWSS data dictionary
type, for each type whose Excel data dictionary is supplied, and make_nwss
returns them in a dictionary keyed by the type names below:

- reporting: the main reporting data dictionary
- public_concentration: the public concentration data dictionary
- public_metric: the public metric data dictionary
- restricted_raw: the restricted raw data dictionary (not publicly available)
- restricted_analytics: the restricted analytics data dictionary (not publicly
  available)

IMPORTANT: Several of the published data dictionaries must be edited by hand in
Excel before they can be processed correctly. For example, the restricted
analytics dictionary has no "Value Sets" sheet at all, so it must be copied over
from the restricted raw dictionary. The required fixes and the resulting
limitations are documented in docs/nwss-pipeline.md, under "Preparing the NWSS
data dictionaries".

@TODO: Add validation from the "Value Set" column of the "Metadata" sheet.
"""

import os
from pathlib import Path
from typing import Annotated

import typer
from linkml_runtime.linkml_model.meta import SchemaDefinition

from odm_linkmlgen.nwss.make_nwss_ss_classes import extract_all_classes
from odm_linkmlgen.nwss.make_nwss_ss_container import extract_container_class
from odm_linkmlgen.nwss.make_nwss_ss_enums import extract_enums
from odm_linkmlgen.nwss.make_nwss_ss_prefixes import make_prefixes
from odm_linkmlgen.nwss.make_nwss_ss_schema import make_schema
from odm_linkmlgen.utils.general_utils import clear_dirs, extract_sheets, get_logger
from odm_linkmlgen.utils.schema_utils import find_undefined_ranges
from odm_linkmlgen.utils.schemasheets_utils import make_linkml_schema_from_schemasheets

logger = get_logger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)

MAIN_HELP = """Generate the NWSS LinkML schema."""

OUTPUT_DIR_HELP = """Directory to save all the output, including the generating
                  LinkML schemas, to. A separate subdirectory is created for
                  each dictionary type."""

REPORTING_HELP = """NWSS main data dictionary for reporting (Excel file)"""

PUBLIC_CONCENTRATION_HELP = """NWSS public concentration data dictionary (Excel
                            file)"""

PUBLIC_METRIC_HELP = """NWSS public metric data dictionary (Excel file)"""

RESTRICTED_RAW_HELP = """NWSS restricted raw data dictionary (Excel file)"""

RESTRICTED_ANALYTICS_HELP = """NWSS restricted analytics data dictionary (Excel
                            file)"""


@app.command(help=MAIN_HELP)
def make_nwss(
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
    reporting: Annotated[
        Path | None, typer.Option(show_default=False, help=REPORTING_HELP)
    ] = None,
    public_concentration: Annotated[
        Path | None, typer.Option(show_default=False, help=PUBLIC_CONCENTRATION_HELP)
    ] = None,
    public_metric: Annotated[
        Path | None, typer.Option(show_default=False, help=PUBLIC_METRIC_HELP)
    ] = None,
    restricted_raw: Annotated[
        Path | None, typer.Option(show_default=False, help=RESTRICTED_RAW_HELP)
    ] = None,
    restricted_analytics: Annotated[
        Path | None, typer.Option(show_default=False, help=RESTRICTED_ANALYTICS_HELP)
    ] = None,
) -> dict[str, SchemaDefinition]:
    """Make the NWSS LinkML Schemas for various NWSS data dictionaries. A separate schema is created for each
    of the dictionary types whose Excel data dictionaries are specified by the supplied parameters. Any parameter
    of None will skip that dictionary type.

    All data dictionaries except for the restricted ones are available at
    https://archive.cdc.gov/www_cdc_gov/nwss/reporting.html. The restricted ones are not publicly available.

    See the documentation for details on preparing the NWSS data dictionaries, there are special steps
    required to process them before running this function.

    Args:
        output_dir (Path): Location to save the outputs for each dictionary type to. A subdirectory for each
            dictionary type will be created. The final LinkML schemas will be located in these subdirectories.
        reporting (Path | None, optional): Path to reporting data dictionary Excel file. Defaults to None.
        public_concentration (Path | None, optional): Path to public concentration data dictionary Excel file. Defaults to None.
        public_metric (Path | None, optional): Path to public metric data dictionary Excel file. Defaults to None.
        restricted_raw (Path | None, optional): Path to restricted raw data dictionary Excel file. Defaults to None.
        restricted_analytics (Path | None, optional): Path to restricted analytics data dictionary Excel file. Defaults to None.

    Returns:
        dict[str, SchemaDefinition]: The generated LinkML schema definitions, keyed by
            dictionary type (eg. "reporting", "public_concentration"). Only the
            dictionary types whose Excel data dictionaries were supplied are present, so
            the dictionary is empty if no data dictionary was passed at all.
    """
    dictionary_types = []
    if reporting:
        dictionary_types.append(("reporting", reporting))
    if public_concentration:
        dictionary_types.append(("public_concentration", public_concentration))
    if public_metric:
        dictionary_types.append(("public_metric", public_metric))
    if restricted_raw:
        dictionary_types.append(("restricted_raw", restricted_raw))
    if restricted_analytics:
        dictionary_types.append(("restricted_analytics", restricted_analytics))

    schemas: dict[str, SchemaDefinition] = {}

    for dictionary_type, metadata_excel_file in dictionary_types:
        if not dictionary_type or not metadata_excel_file:
            continue
        cur_output_dir = Path(output_dir) / f"nwss_{dictionary_type}"

        default_schema_values = {
            "schema": f"NWSS_{dictionary_type}",
            "id": f"https://onto.phes-odm.org/nwss/{dictionary_type}",
            "description": f"National Wastewater Surveillance System (NWSS-{dictionary_type})",
            "default_prefix": f"nwss_{dictionary_type}",
        }

        enums_excel_file = metadata_excel_file
        detailed_enum_names = ["vs_yne", "vs_yn"]
        source_metadata_sheet_name = "Metadata"
        source_value_sets_sheet_name = "Value Sets"
        single_table = True

        if dictionary_type in ("reporting", "public_concentration", "public_metric"):
            # These dictionary types use the default sheet names set above
            pass
        elif dictionary_type == "restricted_raw":
            source_metadata_sheet_name = "Wastewater Metadata"
        elif dictionary_type == "restricted_analytics":
            source_metadata_sheet_name = "Analytics Data Dictionary"
        else:
            raise ValueError(f"Unrecognized dictionary type {dictionary_type}")

        logger.info(f"Making NWSS schema for {dictionary_type}")

        dictionary_dir = cur_output_dir / "dictionary"
        schemasheets_dir = cur_output_dir / "schemasheets"
        linkml_dir = cur_output_dir / "linkml"

        metadata_file = dictionary_dir / "metadata.csv"
        enums_file = dictionary_dir / "enums.csv"

        # Clean up the output directories (ie. delete old csv, tsv, and yaml files)
        clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

        # Extract the metadata and Value Sets (enums) sheets from the data dictionary
        if metadata_excel_file == enums_excel_file:
            # Extract metadata and value sets from single file.
            extract_sheets(
                metadata_excel_file,
                [source_metadata_sheet_name, source_value_sets_sheet_name],
                dictionary_dir,
                output_names=[
                    os.path.basename(metadata_file),
                    os.path.basename(enums_file),
                ],
                na_values={},
                default_na_values=[""],
            )
        else:
            # Extract metadata and value sets from separate files.
            extract_sheets(
                metadata_excel_file,
                [source_metadata_sheet_name],
                dictionary_dir,
                output_names=[os.path.basename(metadata_file)],
                na_values={},
                default_na_values=[""],
            )
            extract_sheets(
                enums_excel_file,
                [source_value_sets_sheet_name],
                dictionary_dir,
                output_names=[os.path.basename(enums_file)],
                na_values={},
                default_na_values=[""],
            )

        # Extract the enumerations from the Value Set. Sometimes there are no enumerations in the metadata.
        if os.path.exists(enums_file):
            extract_enums(
                metadata_file,
                enums_file,
                schemasheets_dir,
                detailed_enum_names=detailed_enum_names,
            )

        # Extract the classes (tables) from the meta data.
        extract_all_classes(
            metadata_file,
            enums_file if os.path.exists(enums_file) else None,
            schemasheets_dir,
            single_table=single_table,
            detailed_enum_names=detailed_enum_names,
        )

        # Make the Container Schemasheet
        extract_container_class(
            metadata_file, schemasheets_dir / "container.tsv", single_table=single_table
        )

        # Make the prefixes Schemasheet
        make_prefixes(
            schemasheets_dir / "prefixes.tsv", dictionary_type=dictionary_type
        )

        # Make the schema Schemasheet
        make_schema(schemasheets_dir / "schema.tsv", data_values=default_schema_values)

        # Run Schemasheets to make the final LinkML schema
        schema = make_linkml_schema_from_schemasheets(
            schemasheets_dir, linkml_dir / f"nwss_{dictionary_type}.yaml"
        )
        schemas[dictionary_type] = schema

        # Report any slot left pointing at an element the schema does not define. The
        # schema is still written: this is reported the same way as every other data
        # dictionary defect, so that one bad field does not cost you the whole run.
        undefined_ranges = find_undefined_ranges(schema)
        for slot_name, ranges in undefined_ranges.items():
            logger.error(
                f"Slot {slot_name} has a range the schema does not define: "
                f"{', '.join(ranges)}. For a categorical field this usually means its "
                "enumeration is missing from the Value Sets sheet of the data dictionary."
            )
        if undefined_ranges:
            logger.error(
                f"{dictionary_type}: {len(undefined_ranges)} slot(s) have an undefined "
                "range, so the generated schema is not usable as it stands."
            )

    logger.info("Finished!")

    return schemas


if __name__ == "__main__":
    app()
