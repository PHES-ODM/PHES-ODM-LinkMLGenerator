#%%
"""
Create the Container class Schemasheet for ODM v2. This is the top-level (tree_root) class that contains
all the top-level tables (eg. measures, protocols, etc.)

@TODO: We currently don't have any descriptions or titles for the tables. These should be added.
"""

import argparse
import pandas as pd
from typing import Union
from pathlib import Path

from utils import save_data_frame, add_schemasheets_header, order_columns, get_logger
from odm_v2.v2_utils import v2_class_names

logger = get_logger(__name__)

def extract_container_class(output_file: Union[str, Path]):
    """Extract and create the Schemasheets file for the top-level Container class. This class
    contains a multivalued slot for each table found in the ODM v2 data dictionary.

    Args:
        output_file (Union[str, Path]): The TSV file to save the Container class Schemasheet
            to.
    """
    # First row is for the Container only (ie. no slot is specified)
    df = pd.DataFrame([{ "class" : "Container", "tree_root" : True }])

    # Make a row for each ODM v2 class (one slot per class)
    for class_name in v2_class_names:
        row = pd.DataFrame([{
            "class" : "Container",
            "slot" : class_name,
            "range" : class_name,
            "multivalued" : True,
            "inlined_as_list" : True,
            "title" : "",
            "description" : "",
        }])
        df = pd.concat([df, row]).reset_index(drop=True)
        
    # Put the headers in a nice order and add the Schemasheets header
    df = order_columns(df, ["class", "slot", "range", "tree_root", "multivalued", "inlined_as_list", "title", "description"])
    df = add_schemasheets_header(df, { c : c for c in df.columns })
    
    save_data_frame(df, output_file, index=False)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            output_file = "../../odm_v2/schemasheets/container.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--output_file", type=str, help="The TSV file to save the container class Schemasheet to", required=True)
        opts = args.parse_args()

    logger.info("Making ODM v2 Container class...")

    extract_container_class(opts.output_file)

    logger.info("Finished!")
