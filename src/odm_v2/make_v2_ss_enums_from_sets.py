#%%
"""
Create Schemasheets for all enumerations found within the ODM v2 data dictionary sets sheet. This
does NOT include the enumerations whose values are found within the parts sheet (those can be created
with make_v2_ss_enums_from_parts.py).

## Example

```python
from make_v2_ss_enums_from_sets import extract_sets_enums

extract_sets_enums("odm_v2/dictionary/sets.csv", 
                   "odm_v2/dictionary/parts.csv", 
                   "odm_v2/schemasheets/enums_sets.tsv")
```
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import argparse

from utils import add_schemasheets_header, save_data_frame, order_columns, get_logger, EMPTY_PERMISSIBLE_VALUE
from odm_v2.v2_utils import v2_keep_active_rows

logger = get_logger(__name__)

# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
# Required schemasheets headers: "enum", "permissible_value", "description", "title"
headers = {
    "setID": "enum",
    "partID": "permissible_value",
    "partLabel": "title",   # Comes from the parts list (NOT the sets list) after joining
    "partDesc": "description",
}

def extract_sets_enums(sets_file: str, parts_file: str, output_file: str):
    """Create a Schemasheet for all the enumerations found in the ODM v2 data dictionary
    sets sheet. Note that this does not consistute all of the enums found in ODM v2.
    Additional enumerations that are not found in the sets sheet are extracted from the
    parts sheet by make_v2_ss_enums_from_parts.py.

    Args:
        sets_file (str): The full path and filename to the sets CSV sheet extracted from
            the ODM v2 data dictionary.
        parts_file (str): The full path and filename to the parts CSV sheet extracted from
            the ODM v2 data dictionary.
        output_file (str): The file to save the Schemasheet to. Should be a .tsv file.
    """
    df = pd.read_csv(sets_file)
    parts_df = pd.read_csv(parts_file)

    # Keep only active status parts
    df = v2_keep_active_rows(df)

    # Get the description (partDesc) and title (partLabel) from the parts list, by joining on partID
    df = df.merge(parts_df[["partID", "partDesc", "partLabel"]], on="partID", how="left")

    # Replace NAs with ""
    for k in headers.keys():
        df.loc[pd.isna(df[k]), k] = ""

    # Drop duplicates, based on both "enum" and "permissible_value" columns
    # For the duplicates, we concatenate the multiple "title" and "description" values so that in
    # the kept duplicate we have all possible titles and descriptions included.
    # eg. If the "MyEnum" enum has multiple blank permissible_values (usually corresponding
    # to "not applicable"), then we will merge them into one. The resulting title might look
    # like "Not applicable / Not a number / Null".
    enum_col = [k for k, v in headers.items() if v == "enum"][0]
    permissible_value_col = [k for k, v in headers.items() if v == "permissible_value"][0]
    description_col = [k for k, v in headers.items() if v == "description"][0]
    title_col =  [k for k, v in headers.items() if v == "title"][0]
    # Strip leading and trailing whitespace from the columns
    for k in [enum_col, description_col, title_col]:
        df[k] = df[k].str.strip()
    # Using all duplicated rows, we iterate over each of the enumerations (in enum_col)
    duplicated_rows = df.duplicated(subset = [enum_col, permissible_value_col], keep = False)
    for _, group_df in df[duplicated_rows].groupby(enum_col):
        for _, subgroup_df in group_df.groupby(permissible_value_col):
            # For the current duplicates in the enumeration, concatenate all
            # descriptions and titles so the retained row includes all descriptions and titles
            new_description = " / ".join(subgroup_df[description_col].unique())
            new_title = " / ".join(subgroup_df[title_col].unique())
            df.loc[subgroup_df.index, description_col] = new_description
            df.loc[subgroup_df.index, title_col] = new_title
    
    # Drop the duplicates
    df = df.drop_duplicates(subset = [enum_col, permissible_value_col], keep = "first")
    
    # @TODO: Once we figure out how to have blank permissible values, remove this. At the
    # moment Schemasheets treats blank permissible values as corresponding to details about
    # the upper level enum, rather than a value of the enum. After generating the schema
    # with Schemasheets in utils.make_linkml_schema, we edit the schema in 
    # utils.fix_schemasheets_generated_schemato replace permissible values equal to EMPTY_PERMISSIBLE_VALUE with "".
    # Drop blank partIDs. 
    # df.loc[df["partID"] == "", "partID"] = None        
    # df = df.dropna(axis = 0, subset="partID")
    df.loc[(df["partID"] == "") | (pd.isna(df["partID"])), "partID"] = EMPTY_PERMISSIBLE_VALUE
    
    # We now have all the permissible values for each enumeration. We also want to create a row
    # for each enumeration where no permissible value is listed. These are the rows containing
    # top-level enumeration data, ie. the enumeration's title and description, rather than
    # a permissible value title and description.
    enum_names_df = pd.DataFrame({ "setID" : list(df["setID"].unique())})
    enum_names_df = enum_names_df.merge(parts_df[["partID", "partLabel", "partDesc"]], left_on="setID", right_on="partID", how="left")
    enum_names_df = enum_names_df.drop("partID", axis=1)
    enum_order = df["enumeration"].min() - 1
    enum_names_df["enumeration"] = enum_order
    df = pd.concat([df, enum_names_df]).reset_index(drop=True)
    df = df.sort_values(["setID", "enumeration"])
    df.loc[df["enumeration"] == enum_order, "enumeration"] = None
    
    # Order the columns
    df = order_columns(df, headers.keys())
    
    # Add schemasheets headers
    df = add_schemasheets_header(df, headers)

    # Save to disk
    logger.info(f"Saving enums from sets to '{output_file}'")
    save_data_frame(df, output_file, index=False)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            sets_file = "../../odm_v2/dictionary/sets.csv"
            parts_file = "../../odm_v2/dictionary/parts.csv"
            output_file = "../../odm_v2/schemasheets/enums_sets.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--sets_file", type=str, help="Input ODM v2 sets file to extract the enums from", required=True)
        args.add_argument("--parts_file", type=str, help="Input ODM v2 parts file. This file contains additional info about the enum, such as the top-level description.", required=True)
        args.add_argument("--output_file", type=str, help="The TSV file to save the extracted enums to", required=True)
        opts = args.parse_args()
        
    logger.info("Making ODM v2 from Sets List...")
    
    extract_sets_enums(opts.sets_file, opts.parts_file, opts.output_file)

    logger.info("Finished!")
