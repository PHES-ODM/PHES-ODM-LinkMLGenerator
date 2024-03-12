#%%
"""
Creates Schemasheets for all classes (ie. tables) based on the ODM v2 data dictionary parts sheet.
The outputs will be named "class_{table_name}.tsv".

@TODO: We currently don't have any descriptions or titles for the classes. These should be added.

## Example

```python
from make_v2_ss_classes import extract_all_classes

extract_all_classes("odm_v2/dictionary/parts.csv", "odm_v2/schemasheets")
```
"""

from pathlib import Path
import pandas as pd
import os
import argparse
from typing import Tuple

from utils import add_schemasheets_header, save_data_frame, order_columns, get_logger
from odm_v2.v2_utils import v2_keep_active_rows, v2_get_enum_name_from_part_id, v2_get_header_rows, v2_class_names

logger = get_logger(__name__)

# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
headers = {
    "class" : "class",
    "partID" : "slot",
    "partLabel" : "title",
    "identifier" : "identifier",
    "required" : "required",
    "dataType" : "range",
    "partDesc" : "description",
    "minValue" : "minimum_value",
    "maxValue" : "maximum_value",
    "pattern" : "pattern",
    "partInstr" : "notes",
}

# For mapping the ODM v2 data types to LinkML datatypes
_data_types_map = {
    "varchar" : "string",
    "dateTime" : "datetime",
    "datetime" : "datetime",
    "integer" : "integer",
    "float" : "float",
    "boolean" : "booleanSet",
    "blob" : "blob",            # @TODO: How should we deal with blobs? I'm not sure if LinkML has this data type
}

def _extract_pattern(row: pd.Series) -> str:
    """Extract the regex pattern to match for validation for the specified row.

    Args:
        row (pd.Series): The row to extract the pattern for.

    Returns:
        str: The regex pattern for validation, or None if no pattern required.
    """
    min_length = row["minLength"]
    max_length = row["maxLength"]
    if pd.isna(min_length) and pd.isna(max_length):
        return None
    
    # Create a string of length min_length to max_length
    min_length = "0" if pd.isna(min_length) else str(int(min_length))
    max_length = "" if pd.isna(max_length) else str(int(max_length))
    pattern = "^.{%s,%s}$" % (min_length, max_length)
    return pattern

def extract_class(df: pd.DataFrame, class_name: str, output_dir: str) -> Tuple[str, pd.DataFrame]:
    """Create a Schemasheet for the specified class name using the data in a
    DataFrame loaded from the parts sheet of the ODM v2 data dictionary.

    Args:
        df (pd.DataFrame): The parts sheet of the ODM v2 data dictionary.
        class_name (str): The name of the class (ie. table) to extract.
        output_dir (str): The location to save the Schemasheet. The actual
            Schemasheet will be named "class_{class_name}.tsv".

    Returns:
        List[str, pd.DataFrame]: The full path and file name to the saved Schemasheet as
            well as the DataFrame of the Schemasheet.
    """
    
    # Get all rows in the table that correspond to a header in the parts sheet (ie. rows identified
    # as a primary key, foreign key, or header)
    table_df = v2_get_header_rows(df, class_name)
    
    # Only keep rows that are marked as "active" under the "status" column
    table_df = v2_keep_active_rows(table_df)

    # Select the columns of interest, and rename some of the columns
    table_output_df = table_df[["partID", "partLabel", "partDesc", "partType", "partInstr", "mmaSet", f"{class_name}", f"{class_name}Required", f"{class_name}Order", "dataType", "minValue", "maxValue", "minLength", "maxLength"]].copy()
    columns = list(table_output_df.columns)
    columns[columns.index(class_name)] = "headerType"
    columns[columns.index(f"{class_name}Required")] = "required"
    columns[columns.index(f"{class_name}Order")] = "order"
    table_output_df.columns = columns

    # Set "required" field (ie. row has the value "mandatory" in the "required" column)
    table_output_df["required"] = table_output_df["required"].isin(["mandatory"])

    # Set the dataType (range) by mapping the values in the "dataType" column to
    # the data types recognized by LinkML (eg. map varchar to string)
    for k, v in _data_types_map.items():
        table_output_df.loc[table_output_df["dataType"] == k, "dataType" ] = v

    # Set the dataType for enumerations that have an mmaSet (the data type/enumeration is the value in "mmaSet")
    mmaset_filt = ~pd.isna(table_output_df["mmaSet"])
    table_output_df.loc[mmaset_filt, "dataType"] = table_output_df.loc[mmaset_filt, "mmaSet"]

    # Set the dataType for remaining enumerations that are categorical (ie. the ones that do not have an mmaSet that was set previously)
    # The enumeration names are a variant of the value found in the partID column (eg. we often just need to add an "s" to
    # the end of the partID column, see utils.v2_get_enum_name_from_part_id)
    categorical_filt = (~mmaset_filt) & (table_output_df["dataType"] == "categorical")
    table_output_df.loc[categorical_filt, "dataType"] = table_output_df.loc[categorical_filt, "partID"].apply(v2_get_enum_name_from_part_id)

    # Set identifiers (primary keys)
    table_output_df["identifier"] = table_output_df["headerType"] == "pK"
    
    # Set the regex "pattern" where required
    table_output_df["pattern"] = table_output_df.apply(_extract_pattern, axis=1)

    # Sort by "order" column
    table_output_df = table_output_df.sort_values("order")

    # Set the table name for all the rows (class). We're only working with one table name
    # at a time, so they're all the same.
    table_output_df["class"] = class_name

    # Reorder the columns, according to the order in the headers dictionary. Any column
    # not in the headers dictionary is placed at the end.
    table_output_df = order_columns(table_output_df, headers.keys())
    
    # Add Schemasheets headers
    table_output_df = add_schemasheets_header(table_output_df, headers = headers)

    # Save to disk
    output_file = Path(output_dir) / f"class_{class_name}.tsv"
    logger.info(f"Saving classes to {output_file}")
    save_data_frame(table_output_df, output_file, index=False)
    
    return output_file, table_output_df

def extract_all_classes(parts_file: str, output_dir: str):
    """Create a Schemasheet for all classes (tables) found in the parts sheet that was
    extracted from the ODM v2 data dictionary.

    Args:
        parts_file (str): The parts sheet (CSV) that was extracted from the ODM v2 data
            dictionary.
        output_dir (str): The location to save all the Schemasheets. One Schemasheet per
            class is created, with the name "class_{class_name}.tsv" 
    """
    if not output_dir:
        output_dir = os.path.dirname(parts_file)

    df = pd.read_csv(parts_file)

    for class_name in v2_class_names:
        logger.info(f"Processing table {class_name}...")
        extract_class(df, class_name, output_dir)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            parts_file = "../../odm_v2/dictionary/parts.csv"
            output_dir = "../../odm_v2/schemasheets"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--parts_file", type=str, help="Input ODM v2 parts file to extract the classes from", required=True)
        args.add_argument("--output_dir", type=str, help="The directory to save the Schemasheets classes files. If not specified then the directory of the input file is used.", required=False)
        opts = args.parse_args()

    logger.info("Making ODM v2 Classes...")

    extract_all_classes(opts.parts_file, opts.output_dir)

    logger.info("Finished!")
