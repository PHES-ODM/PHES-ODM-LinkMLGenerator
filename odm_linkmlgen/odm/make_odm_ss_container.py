# %%
"""
Create the Container class Schemasheet for ODM. This is the top-level (tree_root) class that contains
all the top-level tables (eg. measures, protocols, etc.)

@TODO: We currently don't have any descriptions or titles for the tables. These should be added.
"""

import pandas as pd
from typing import Union
from pathlib import Path

from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet
from odm_linkmlgen.odm.odm_utils import odm_get_available_class_names

logger = get_logger(__name__)


def extract_container_class(
    parts_file: Union[str, Path], output_file: Union[str, Path]
):
    """Extract and create the Schemasheets file for the top-level Container class. This class
    contains a multivalued slot for each table found in the ODM data dictionary.

    Args:
        parts_file (Union[str, Path]): The ODM data dictionary parts file.
        output_file (Union[str, Path]): The TSV file to save the Container class Schemasheet
            to.
    """
    # First row is for the Container only (ie. no slot is specified)
    df = pd.DataFrame([{"class": "Container", "tree_root": True}])

    parts_df = read_data_frame(parts_file, keep_default_na=False, na_values=[""])

    # Make a row for each ODM class (one slot per class)
    for class_name in odm_get_available_class_names(parts_df):
        row = pd.DataFrame(
            [
                {
                    "class": "Container",
                    "slot": class_name,
                    "range": class_name,
                    "multivalued": True,
                    "inlined_as_list": True,
                    "title": "",
                    "description": "",
                }
            ]
        )
        df = pd.concat([df, row]).reset_index(drop=True)

    # Put the headers in a nice order and add the Schemasheets header
    logger.info("Saving Schemasheets container to 'output_file'")
    save_schemasheet(
        df,
        output_file,
        [
            "class",
            "slot",
            "range",
            "tree_root",
            "multivalued",
            "inlined_as_list",
            "title",
            "description",
        ],
    )


if __name__ == "__main__":
    if "get_ipython" in globals():
        opts = {
            "parts_file": "../../gen/odm_v2/dictionary/parts.csv",
            "output_file": "../../gen/odm_v2/schemasheets/container.tsv",
        }

        logger.info("Making ODM Container class...")

        extract_container_class(**opts)

        logger.info("Finished!")
