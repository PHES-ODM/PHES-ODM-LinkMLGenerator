# %%
"""
Create the Container class Schemasheet for NWSS. This is the top-level (tree_root) class that contains
all the top-level tables (eg. measures, protocols, etc.)
"""

import argparse
import pandas as pd
from typing import Union, Optional
from pathlib import Path

from odm_linkmlgen.utils.general_utils import read_data_frame, get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet
from odm_linkmlgen.nwss.nwss_utils import splitup_metadata_sheet, SINGLE_TABLE_NAME

logger = get_logger(__name__)


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
        output_file (Union[str, Path]): The TSV file to save the Container class Schemasheet
            to.
        single_table (Optional[bool]): If True then merge all classes into a single class called
            nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate. Defaults to False.
    """
    # Load and parse the Metadata file
    metadata_df = read_data_frame(metadata_file)
    all_tables = splitup_metadata_sheet(metadata_df)

    # First row is for the Container only (ie. no slot is specified)
    # We'll append all the top-level table slots after this first row.
    df = pd.DataFrame([{"class": "Container", "tree_root": True}])

    # Make a row for each ODM class (one slot per class)
    class_names = [SINGLE_TABLE_NAME] if single_table else all_tables.keys()
    for class_name in class_names:
        row = pd.DataFrame(
            [
                {
                    "class": "Container",
                    "slot": class_name,
                    "range": class_name,
                    "multivalued": True,
                    "inlined_as_list": True,
                    "title": class_name,
                    "description": "",
                }
            ]
        )
        df = pd.concat([df, row]).reset_index(drop=True)

    # Put the columns in a nice order
    columns = [
        "class",
        "slot",
        "range",
        "tree_root",
        "multivalued",
        "inlined_as_list",
        "title",
        "description",
    ]
    columns = columns + [c for c in df.columns if c not in columns]
    save_schemasheet(df, output_file, columns)


if __name__ == "__main__":
    if "get_ipython" in globals():

        class opts:
            metadata_file = "../../gen/nwss_reporting/dictionary/metadata.csv"
            output_file = "../../gen/nwss_reporting/schemasheets/container.tsv"
    else:
        args = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        args.add_argument(
            "--metadata_file",
            type=str,
            help="Input Metadata sheet from the NWSS data dictionary",
            required=True,
        )
        args.add_argument(
            "--output_file",
            type=str,
            help="The TSV file to save the container class Schemasheet to",
            required=True,
        )
        opts = args.parse_args()

    logger.info("Making NWSS Container class...")

    extract_container_class(opts.metadata_file, opts.output_file)

    logger.info("Finished!")
