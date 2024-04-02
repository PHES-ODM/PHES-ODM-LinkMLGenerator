from typing import Dict, Tuple, List, Optional
import pandas as pd

from utils import get_logger

logger = get_logger(__name__)

TABLE_NAME_COL = "_table"
SINGLE_TABLE_NAME = "nwss"

class SlotToEnumColumns:
    SLOT: str = "slot"
    ENUM: str = "enum"
    
def splitup_metadata_sheet(df: pd.DataFrame, single_table: bool = False) -> Dict[str, pd.DataFrame]:
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    
    all_tables = {}
    
    # Get the table boundaries. After dropping empty rows (done previously), each new table occurs
    # whever an empty value is found in the "Data Type" column. The rows with the empty values
    # contain the table name in the "Field Name" column. All rows up to but excluding the next
    # empty value define that table.
    table_boundaries = list(df.index[pd.isna(df["Data Type"])]) + [df.index[-1]]
    
    if len(table_boundaries) <= 1:
        # The DataFrame is a single table
        table_name = SINGLE_TABLE_NAME
        df[TABLE_NAME_COL] = table_name
        return { table_name : df }
    
    # Split up the DataFrame along the table boundaries. The table name is the value in
    # the "Field Name" column at the top of each table boundary.
    for cur_index, next_index in zip(table_boundaries[0:-1], table_boundaries[1:]):
        # Get table name and extract the table
        cur_table_name = df.loc[cur_index, "Field Name"]
        cur_table_df = df.loc[cur_index+1:next_index-1]
        
        if cur_table_name in all_tables:
            raise ValueError(f"Table {cur_table_name} has already been parsed in the Metadata sheet")
        
        # Add the TABLE_NAME_COL and save the table
        cur_table_df = cur_table_df.reset_index(drop=True).copy()
        cur_table_df[TABLE_NAME_COL] = cur_table_name
        all_tables[cur_table_name] = cur_table_df

    if single_table:
        all_df = pd.concat(all_tables.values()).reset_index(drop=True)
        all_df[TABLE_NAME_COL] = SINGLE_TABLE_NAME
        all_tables = { SINGLE_TABLE_NAME: all_df }

    return all_tables

def parse_enums_sheet(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Parse the enums (Value Sets) sheet of a NWSS data dictionary Excel file, by extracting
    all enumerations, their names and permissible values, and returning each enum as a separate
    DataFrame that have the headers "enum", "permissible_value", and "description".

    Args:
        df (pd.DataFrame): The Value Sets sheet extracted from a NWSS data dictionary file.

    Returns:
        Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]: The first pd.DataFrame of the tuple
            has a SlotToEnumColumns.SLOT column listing a field in the NWSS data dictionary, and a
            SlotToEnumColumns.ENUM column listing the enumeration name assigned to the slot.
            The returned dictionary contains the enum names as a key, and the corresponding
            Schemasheets DataFrame as the values.
            
    """
    logger.info(f"Parsing all enumerations")
    
    # Drop empty columns
    df = df.dropna(axis=1, how="all")
    
    # The "Field" and "Value Set Name" maps the Field name in the data dictionary to
    # the enum name that that field uses.
    fields_df = df[["Field", "Value Set Name"]].copy()
    fields_df.columns = [SlotToEnumColumns.SLOT, SlotToEnumColumns.ENUM]
    fields_df = fields_df.dropna(axis=0, how="all")

    # Extract all enums: Iterate over columns and first row
    # The column will indicate the enum name, although there are many unnamed columns.
    # In the first row below the enum name columns, there should be a "Value Set" column
    # (indicating the enum's allowable values) and in the next column a "Description" column.
    all_enums = {}
    for enum_value_col, desc_col  in zip(df.columns[0:-1], df.columns[1:]):
        if str(df.loc[0, enum_value_col]).strip().lower() != "value set" or str(df.loc[0, desc_col]).strip().lower() != "description":
            continue
        
        # Found an enum value and description column pair, extract them and clean up the column names
        enum_name = enum_value_col
        enum_df = df[[enum_value_col, desc_col]].drop(index=0).dropna(axis=0, how="all").reset_index(drop=True).copy()        
        enum_df.columns = ["permissible_value", "description"]

        # Replace [empty] with blank string
        # @TODO: Schemasheets doesn't allow empty permissible_values, it treats an empty one as being
        # a row for the top-level enumeration, rather than a value of the enumeration
        # enum_df["permissible_value"] = enum_df["permissible_value"].map(lambda x: "" if x == "[empty]" else x)
        
        # Add the enum name to the DataFrame
        enum_df["enum"] = enum_name
        
        # Save the DataFrame to return from the function
        all_enums[enum_name] = enum_df

    return fields_df, all_enums            

def get_detailed_enums(metadata_df: pd.DataFrame, detailed_enum_names: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Get a dictionary that maps all non-detailed enum names to all of the detailed versions of the enum
    names. eg:
    
        {
            "vs_yne" : [ "vs_yne[stormwater_input]", "vs_yne[influent_equilibrated]" ],
            ...
        }

    Args:
        metadata_df (pd.DataFrame): The Metadata sheet extracted from a NWSS data dictionary.
        detailed_enum_names (Optional[List[str]], optional): A list of all enums that should
            be converted to detailed enum names. Defaults to None.

    Returns:
        Dict[str, List[str]]: A dictionary that maps non-detailed enum names to a list of all
            detailed enum names used for that enum in the Metadata.
    """
    if "Value Set" not in metadata_df.columns:
        return {}
    
    # Get all categorical rows
    categories = metadata_df[metadata_df["Data Type"] == "category"].copy()
    # Extract the (non-detailed) enum names used for each row
    categories["Value Set"] = categories["Value Set"].map(lambda x: x.strip("[] ").split(":")[1].strip())
    
    def _get_detailed_enum(row: pd.Series, detailed_enum_names: List[str]) -> str:
        """Get the enumeration name from the row, making the name detailed if required
        """
        if row["Value Set"] in detailed_enum_names:
            return f"{row['Value Set']}[{row['Field Name']}]"
        return None
    
    enum_map = {}
    for _, row in categories.iterrows():
        # Get the enum name for the current row and its detailed name
        # eg. enum name is vs_yne and detailed name is vs_yne[stormwater_input]
        enum_name = row["Value Set"]
        detailed_enum_name = _get_detailed_enum(row, detailed_enum_names)
        
        # If there is a detailed name, then add it to the enum_map that maps regular enum name
        # to detailed enum names.
        if detailed_enum_name:
            if enum_name not in enum_map:
                enum_map[enum_name] = []
            if detailed_enum_name not in enum_map[enum_name]:
                enum_map[enum_name].append(detailed_enum_name)
    return enum_map    

