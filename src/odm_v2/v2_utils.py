"""
Utility functions for ODM LinkML Schema Generator, specific to ODM v2 dictionary.
"""

from typing import Union, Any, List, Optional, Dict
import pandas as pd
import re
import openpyxl
from pathlib import Path

from linkml_runtime.linkml_model.meta import SchemaDefinition

from utils.general_utils import get_logger

logger = get_logger(__name__)

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

def v2_get_enum_name_from_part_id(part_id: str, recognized_enums: Optional[List[str]] = None) -> str:
    """Get the enumeration name for the specified part ID.

    Args:
        part_id (str): The partID to get the enumeration name for. This is typically equal
            to the partID with a trailing "s", but there are some exceptions.
        recognized_enums (Optional[List[str]]): If not None then a list of recognized enumeration
            names. If the calculated enum name exists in this list then the enum name is returned,
            otherwise the value "string" is returned (ie. the data type is a string, rather than an enum).

    Returns:
        str: The enumeration name (for the partID)
    """
    if part_id in _v2_enum_name_exceptions.keys():
        name = _v2_enum_name_exceptions[part_id]
    else:
        name = f"{part_id}s"
    if recognized_enums is not None and name not in recognized_enums:
        return "string"
    return name

def get_multi_enums_from_dictionary(dictionary_file: str, lists_sheet: str) -> Dict[str, List[str]]:
    """From the ODM v2 data dictionary (the "lists" sheet), get all enumeration names that should
    always be combined with other enumerations. For example, the "fractionSet" enumeration should always
    be combined with the "genMissingnessSet" enumeration, so that missing values (eg. NA, nan, nr, etc).
    
    The returned value has keys for an enumeration name and the corresponding value being a list
    of enumeration names that the source enumeration should take on. The list will include
    the source enumeration (ie. the key) plus optionally additional enumerations that should be included.
    
    For example:
    
        {
            "fractionSet" : [ "fractionSet", "genMissingnessSet" ],
            "sampleRelSet" : [ "sampleRelSet" ],
        }

    Args:
        dictionary_file (str): The path to the ODM v2 data dictionary Excel file.
        lists_sheet (str): The name of the sheet that contains all lists (typically "lists"). This sheet
            contains formulas for creating lists for various enumerations, along with optional
            missingness enumerations.

    Returns:
        Dict[str, List[str]]: Dictionary mapping enumeration names to lists of enumerations names.
    """
    # Get the formulas for all lists.
    # The formulas are similar to:
    # =UNIQUE(_xlfn._xlws.FILTER(parts!B:B, ((parts!C:C = "classes")*(parts!AE:AE = "input"))+(parts!C:C = "missingness")))
    # =UNIQUE(_xlfn._xlws.FILTER(sets!D:D,(sets!A:A="purposeSet")+(sets!A:A = "genMissingnessSet")))
    # We get all strings enclosed in quotes (as a list of strings), remove the "input" strings, and rename "missingness" to
    # "genMissingnessSet".
    # From the results, the first string that is not "genMissingnessSet" becomes the source enum
    # name (ie. the key in the returned dictionary), while the full results becomes the target enum
    # name (ie. the value in the returned dictionary).
    wb = openpyxl.load_workbook(dictionary_file, read_only=True, data_only=False)
    ws = wb[lists_sheet]
    df = pd.DataFrame(ws.values)
    
    enum_maps = {}
    for formula in df.iloc[1]:
        if not hasattr(formula, "text"):
            continue
        
        # Extract all strings enclosed in quotes from the formula. These will be
        # the enum names that we will process
        txt = formula.text
        res = re.findall("\"([^\"]*)\"", txt)
        
        if res is not None:
            # Go through the results, replace "missingness" with "genMissingnessSet",
            # and find the first string that is not "genMissingnessSet"
            # We also correct capitalization of "genMissingnessSet", since Excel
            # treats strings as case-insensitive.
            non_missing_enum = None
            for idx in range(len(res)):
                if res[idx].lower() in ["genmissingnessset", "missingness"]:
                    res[idx] = "genMissingnessSet"
                elif non_missing_enum is None:
                    non_missing_enum = res[idx]
            # Remove "input"
            if "input" in res:
                res.remove("input")
            # Save to the map
            enum_maps[non_missing_enum] = res

    return enum_maps

def map_enum_ranges(schema: SchemaDefinition, enum_maps: Dict[str, List[str]], method: str = "multi_range"):
    """Change the specified enumerations in the schema so that they always occur with one or more other
    enumerations, or so that they are merged with one or more other enumerations.
    
    The enumerations to change are the keys of enum_maps, the values are lists of enumerations that
    include the key enumeration as well as all other enumerations it should be grouped with. How the
    grouping occurs depends on the method parameter.
    
    This is typically done to add missingness enumerations to other enumerations.

    Args:
        schema (SchemaDefinition): The SchemaDefinition to change.
        enum_maps (Dict[str, List[str]]): The enum mappings. For example:
            {
                "fractionSet" : [ "fractionSet", "genMissingnessSet" ],
                "sampleRelSet" : [ "sampleRelSet" ],
            }
        method (str, Optional): If "multi_range" then for any slot that has a range equal to an
            enumeration in enum_maps.keys(), we change the slot's range so that it is equal to the
            list of enumerations in enum_maps' value.
            If "merge" then for any enumeration found in enum_maps.keys(), we merge it with all
            enumerations found in enum_maps' value. Defaults to "multi_range".
    """
    if not enum_maps:
        return
    
    if method == "multi_range":
        # Go through all classes
        for class_defn in schema.classes.values():
            # Go through all slot usages
            for slot_defn in class_defn.slot_usage.values():
                # If the slot's range (rng) is a key in enum_maps, then change the range to
                # be equal to enum_maps[rng]
                rng = slot_defn.range
                if rng in enum_maps:
                    slot_defn.range = enum_maps[rng]
    elif method == "merge":
        # Go through all items in enum_maps
        for enum_name, enum_target_ranges in enum_maps.items():
            if enum_name not in schema.enums:
                logger.warning(f"Unrecognized enumeration name '{enum_name}' for in enum maps for collapsing enumerations")
                continue
            cur_enum = schema.enums[enum_name]
            for new_enum_name in enum_target_ranges:
                if new_enum_name == enum_name:
                    continue
                new_enum = schema.enums[new_enum_name]
                cur_enum.permissible_values.update(new_enum.permissible_values)
    else:
        raise ValueError(f"Unrecognized method '{method}' in map_enum_ranges")

def add_missingness_set(schema: SchemaDefinition, dictionary_file: Union[str, Path], lists_sheet: str = "lists", method: str = "multi_range"):
    """Using the ODM v2 data dictionary, add the genMissingnessSet to any slot range that has an
    enumeration that should be paired with genMissingnessSet.

    Args:
        schema (SchemaDefinition): The schema to modify in place.
        dictionary_file (Union[str, Path]): The ODM v2 data dictionary, in Excel format.
        lists_sheet (str, optional): The sheet in the dictionary_file that contains the lists of values for the enumerations
            that are optionally paired with the missingness set. Defaults to "lists".
        method (str, Optional): If "multi_range" then we add the missingness set to slots by changing
            the slot's range to a list that includes the original range and the missingness set.
            If "merge" then we modify the enumerations directly so that they include the permissible values
            found in the missingness set. Defaults to "multi_range".
    """
    enum_maps = get_multi_enums_from_dictionary(dictionary_file, lists_sheet = lists_sheet)
    map_enum_ranges(schema, enum_maps=enum_maps, method=method)
