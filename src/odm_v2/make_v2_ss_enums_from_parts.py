#%%
"""
Create Schemasheets for all enumerations found within the ODM v2 data dictionary parts sheet. This
does NOT include the enumerations found within the sets sheet (those can be created with
make_v2_ss_enums_from_sets.py).

## Example

```python
from make_v2_ss_enums_from_parts import extract_parts_enums

extract_parts_enums("odm_v2/dictionary/parts.csv", "odm_v2/schemasheets/enums_parts.tsv")
```
"""

import pandas as pd
import argparse

from utils import add_schemasheets_header, save_data_frame, get_logger
from odm_v2.v2_utils import v2_keep_active_rows, v2_class_names, v2_get_header_rows, v2_get_enum_name_from_part_id

logger = get_logger(__name__)

# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
# Required schemasheets headers: "enum", "permissible_value", "description"
headers = {
    "partType" : "enum",
    "partID" : "permissible_value",
    "partDesc" : "description",
    "partLabel" : "title",
}

def extract_parts_enums(parts_file: str, output_file: str):
    """Create a Schemasheet for all enumerations found in the parts sheet of the ODM v2
    data dictionary. This does not include any enums that are found in the sets sheet
    (see make_v2_ss_enums_from_sets.py for extracting enums from the sets sheet)/

    Args:
        parts_file (str): The full path and filename for the CSV parts sheet extracted
            from the ODM v2 data dictionary.
        output_file (str): The TSV file to save the Schemasheet to.
    """
    df = pd.read_csv(parts_file)

    # Use only active rows (indicated in the "status" column)
    df = v2_keep_active_rows(df)

    # Get all enum names by getting the partID of categorical variables that are headers (pK, fK, or header) 
    # and do not have an mmaSet. Once we have all the header rows, we get the enumeration name based on the 
    # partID. We do not extract the ones with mmaSet set, since those are fully defined in the sets
    # sheet, not the parts sheet (see make_v2_ss_enums_from_sets.py).
    headers_df = v2_get_header_rows(df, v2_class_names)
    filt = headers_df["dataType"].isin(["categorical"])
    filt = filt & pd.isna(headers_df["mmaSet"])
    enum_source_names = sorted(headers_df[filt]["partID"].unique())
    enum_names = [v2_get_enum_name_from_part_id(name) for name in enum_source_names]
    
    # Get all rows for all enums. We only keep the columns in keep_columns.
    # Each row (or enum value) should be an "input" for at least one class.
    # "partType" matches the enum name (corresponds to a permissible value of the enum)
    # OR: "partID" matches the enum name (corresponds to the top-level enum)
    keep_columns = [ 
        "partType",
        "partID",
        "partLabel",
        "shortName",
        "partDesc",
        "partInstr",
    ]
    output_df = pd.DataFrame()
    is_input = df[v2_class_names].isin(["input"])
    is_input = is_input.sum(axis=1)
    input_df = df[is_input > 0]
    for enum_name in enum_names:
        # Get the top-level enum row (where the partID is the same as the enum_name)
        enum_toplevel_df = input_df[input_df["partID"] == enum_name][keep_columns].copy()
        enum_toplevel_df["partID"] = ""
        enum_toplevel_df["partType"] = enum_name
        # Get all rows where the part is a member of the enumeration (by checking the partType column)
        enum_df = input_df[input_df["partType"] == enum_name][keep_columns].copy()
        # Add the top-level enum row and the enum values rows to our final DataFrame
        output_df = pd.concat([output_df, enum_toplevel_df, enum_df])
        
    # Add Schemasheets headers
    output_df = add_schemasheets_header(output_df, headers)

    # Save to disk
    logger.info(f"Saving enums from parts to '{output_file}'")
    save_data_frame(output_df, output_file, index=False)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            parts_file = "../../odm_v2/dictionary/parts.csv"
            output_file = "../../odm_v2/schemasheets/enums_parts.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--parts_file", type=str, help="Input ODM v2 parts file to extract the enums from", required=True)
        args.add_argument("--output_file", type=str, help="The TSV file to save the extracted enums to", required=True)
        opts = args.parse_args()
        
    logger.info("Making ODM v2 Enums from Parts List...")
    
    extract_parts_enums(opts.parts_file, opts.output_file)

    logger.info("Finished!")
