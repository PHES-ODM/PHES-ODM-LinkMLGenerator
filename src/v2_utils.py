"""
Utility functions for ODM LinkML Schema Generator, specific to ODM v2 dictionary.
"""

from typing import Union, Any, List, Optional
import pandas as pd

# All known table names in ODM v2 (in LinkML they are called classes).
v2_class_names = [
    "protocolSteps",
    "protocolRelationships",
    "measures",
    "measureSets",
    "datasets",
    "sites",
    "samples",
    "addresses",
    "contacts",
    "organizations",
    "instruments",
    "polygons",
    "languages",
    "translations",
    "parts",
    "sets",
    "qualityReports",
    "sampleRelationships",
    "protocols",
    "countries",
    "zones",
    "wideNames",
]

# In the ODM v2 data dictionary, in the parts sheet, each table (eg. samples, sites, measures) has
# a column with the same name as the table. If a row has any of the following _v2_header_tags in that
# column, then the partID for that row is a column header in the ODM v2 table.
_v2_header_tags = [
    "header",   # Regular header
    "fK",       # Foreign key
    "pK",       # Primary key
]

# Enumerations specified in the parts list (that are NOT in the sets list) are identified by rows that
# have "categorical" as the "dataType" and that have an empty "mmaSet" column. The names for
# the enumerations for these rows are created by adding an "s" to the end of the "partID". However, some
# enumeration names do not follow this pattern. The exceptions are listed below, with the "partID" as the 
# key and the corresponding enumeration name as the value.
_v2_enum_name_exceptions = {
    "aggragationScale" : "aggregationScales",        # TYPO! Should be aggregationScale / Only in parts table
    "class" : "classes",                             # Add "es" instead of "s"
    "dataTypes" : "dataTypes",                       # No change
    "measure" : "measurements",                      # Not sure?
    "missingnessSets" : "missingnessSets",           # No change
    "partType" : "partType",                         # Not sure?
    "qualityFlag" : "qualityIndicators",
    "specimenSets" : "specimenSets",                 # No change
}

def v2_get_header_rows(df: pd.DataFrame, tables: Union[str, List[str]], header_tags: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
    """Retrieve all rows in the DataFrame that correspond to a column in any of the specified
    ODM v2 tables.
    
    This corresponds to rows that are either a primary key, a foreign key, or a header in any
    of the tables. Note that to determine if a row is a column, the DataFrame df must
    have a column with the same name as the table.

    Args:
        df (pd.DataFrame): The DataFrame to retrieve the rows from.
        tables (Union[str, List[str]]): The table name(s) to retrieve the rows for. For each
            table name a column with that name must be present in df.
        header_tags (Optional[Union[str, List[str]]]): The header tags (ie. header types) to search for.
            This can be "fK" (for foreign key), "pK" (for primary key), and/or "header" (for a regular
            non-key header). These are case-insensitive. If None then all of these header types are
            retrieved. Defaults to None.

    Returns:
        pd.DataFrame: df filtered to only include the rows that specify a column in at least
            one of the tables. A copy of the DataFrame is made.
    """
    if header_tags is None:
        header_tags = _v2_header_tags
    if isinstance(header_tags, str):
        header_tags = [header_tags]
    if isinstance(tables, str):
        tables = [tables]
    lower_header_tags = [h.lower() for h in header_tags]
    lower_df = df[tables].map(lambda x: x.lower() if isinstance(x, str) else x)
    is_header = lower_df[tables].isin(lower_header_tags)
    is_header = is_header.sum(axis=1)
    return df[is_header > 0].copy()

def v2_keep_active_rows(df: pd.DataFrame, status_column: str = "status", keep_status: Union[Any, List[Any]] = "active") -> pd.DataFrame:
    """Keep only rows that have an "active" status. Status is specified in a single column in the
    DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to filter, retrieving only active rows.
        status_column (str, optional): The column name that contains each row's status. Defaults to "status".
        keep_status (Union[Any, List[Any]], optional): The string(s) that indicate an active status. Defaults to "active".

    Returns:
        pd.DataFrame: df filtered to only have active status rows. A copy of the DataFrame is made before
            returning.
    """
    if not isinstance(keep_status, (list, tuple)):
        keep_status = [keep_status]
    keep_filt = df[status_column].str.strip().isin(keep_status)
    df = df[keep_filt]
    return df.copy()

def v2_get_enum_name_from_part_id(part_id: str) -> str:
    """Get the enumeration name for the specified part ID.

    Args:
        part_id (str): The partID to get the enumeration name for. This is typically equal
            to the partID with a trailing "s", but there are some exceptions.

    Returns:
        str: The enumeration name (for the partID)
    """
    if part_id in _v2_enum_name_exceptions.keys():
        name = _v2_enum_name_exceptions[part_id]
    else:
        name = f"{part_id}s"
    return name

