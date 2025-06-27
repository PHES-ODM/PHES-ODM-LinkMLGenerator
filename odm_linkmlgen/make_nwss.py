# %%
"""
Make the NWSS LinkML schemas. There are three schemas:

- NWSS reporting data dictionary
- NWSS public concentration data dictionary
- NWSS public metric data dictionary

@TODO:
- Add validation from "Value Set" column of "Metadata" sheet
- For public metric: vs_reporting_jurisdiction has some incorrect values that fails validation on sample data:
    - "Chicago, IL" should be "Chicago"
    - "Houston, TX" should be "Houston"
    - Should also remove States from other permissible values

IMPORTANT: For restricted_analytics dictionary type: Must copy the "Value Sets" tab from the restricted raw data dictionary to
the restricted analytics data dictionary, since restricted analytics does not have the "Value Sets" tab
IMPORTANT: Even when copying "Value Sets" tab to restricted_analytics, we are missing value sets
IMPROTANT: For restricted_raw: The value set other_norm_units should be other_norm_unit
IMPORTANT: For restricted_analytics: categorical slots pcr_gene_target_agg, pcr_target_below_lod, pcr_target_units,
and quality_flag do not have enumeration definition in "Value Sets" tab.
IMPORTANT: In reporting: Changed ntc_amplify in "Value Sets" tab from vs_yne to vs_yn
"""

from pathlib import Path
import os
import typer
from typing import Annotated

from odm_linkmlgen.utils.general_utils import extract_sheets, get_logger, clear_dirs
from odm_linkmlgen.utils.schemasheets_utils import make_linkml_schema_from_schemasheets
from odm_linkmlgen.nwss.make_nwss_ss_enums import extract_enums
from odm_linkmlgen.nwss.make_nwss_ss_schema import make_schema
from odm_linkmlgen.nwss.make_nwss_ss_classes import extract_all_classes
from odm_linkmlgen.nwss.make_nwss_ss_container import extract_container_class
from odm_linkmlgen.nwss.make_nwss_ss_prefixes import make_prefixes

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
    output_dir: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)
    ],
    reporting: Annotated[
        Path, typer.Option(show_default=False, help=REPORTING_HELP)
    ] = None,
    public_concentration: Annotated[
        Path, typer.Option(show_default=False, help=PUBLIC_CONCENTRATION_HELP)
    ] = None,
    public_metric: Annotated[
        Path, typer.Option(show_default=False, help=PUBLIC_METRIC_HELP)
    ] = None,
    restricted_raw: Annotated[
        Path, typer.Option(show_default=False, help=RESTRICTED_RAW_HELP)
    ] = None,
    restricted_analytics: Annotated[
        Path, typer.Option(show_default=False, help=RESTRICTED_ANALYTICS_HELP)
    ] = None,
):
    """Make the NWSS LinkML Schemas for various NWSS data dictionaries. A separate schema is created for each
    of the dictionary types whose Excel data dictionaries are specified by the supplied parameters. Any parameter
    of None will skip that dictionary type.

    All data dictionaries except for the restricted ones are available at https://www.cdc.gov/nwss/reporting.html.
    The restricted ones are not publicly available.

    Args:
        output_dir (Union[str, Path]): Location to save the outputs for each dictionary type to. A subdirectory for each
            dictionary type will be created. The final LinkML schemas will be located in these subdirectories.
        reporting (Union[str, Path], optional): Path to reporting data dictionary Excel file. Defaults to None.
        public_concentration (Union[str, Path], optional): Path to public concentration data dictionary Excel file. Defaults to None.
        public_metric (Union[str, Path], optional): Path to public metric data dictionary Excel file. Defaults to None.
        restricted_raw (Union[str, Path], optional): Path to restricted raw data dictionary Excel file. Defaults to None.
        restricted_analytics (Union[str, Path], optional): Path to restricted analytics data dictionary Excel file. Defaults to None.
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

        if dictionary_type == "reporting":
            pass
        elif dictionary_type == "public_concentration":
            pass
        elif dictionary_type == "public_metric":
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
        make_linkml_schema_from_schemasheets(
            schemasheets_dir, linkml_dir / f"nwss_{dictionary_type}.yaml"
        )

    logger.info("Finished!")


if __name__ == "__main__":
    if "get_ipython" in globals():
        opts = {
            "output_dir": "../gen/",
            "reporting": "data/nwss/NWSS-Data-Dictionary_v5.0.0_2023-07-10.xlsx",
            "public_concentration": "data/nwss/NWSS-Public-Concentration-Data-Dictionary-v1.0.xlsx",
            "public_metric": "data/nwss/NWSS-Public-Metric-Data-Dictionary-v2.0.xlsx",
            "restricted_raw": "data/nwss/NWSS Restricted Raw Data Set - Data Dictionary v4.0.0_2023-06-02[66].xlsx",
            "restricted_analytics": None,  # "data/nwss/NWSS Restricted Analytics Data Set - Data Dictionary v4.0.0_2023-06-02[78]-MODIFIED.xlsx",
        }
        make_nwss(**opts)
    else:
        app()
