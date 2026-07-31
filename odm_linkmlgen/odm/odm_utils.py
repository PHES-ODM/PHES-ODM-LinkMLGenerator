"""
Utility functions for ODM LinkML Schema Generator, specific to ODM dictionary.
"""

from typing import Union, Any, List, Optional
import pandas as pd
from pathlib import Path

from linkml_runtime.linkml_model.meta import SchemaDefinition

from odm_linkmlgen.utils.general_utils import read_data_frame, get_logger
from odm_linkmlgen.utils.schema_utils import get_ranges_of_slot_defn

logger = get_logger(__name__)

# In the ODM data dictionary, in the parts sheet, each table (eg. samples, sites, measures) has
# a column with the same name as the table. If a row has any of the following _odm_header_tags in that
# column, then the partID for that row is a column header in the ODM table.
_odm_header_tags = [
    "header",  # Regular header
    "fK",  # Foreign key
    "pK",  # Primary key
]

# Enumerations specified in the parts list (that are NOT in the sets list) are identified by rows that
# have "categorical" as the "dataType" and that have an empty "mmaSet" column. The names for
# the enumerations for these rows are created by adding an "s" to the end of the "partID". However, some
# enumeration names do not follow this pattern. The exceptions are listed below, with the "partID" as the
# key and the corresponding enumeration name as the value.
_odm_enum_name_exceptions = {
    "aggragationScale": "aggregationScales",  # TYPO! Should be aggregationScale / Only in parts table
    "class": "classes",  # Add "es" instead of "s"
    "dataTypes": "dataTypes",  # No change
    "measure": "measurements",  # Not sure?
    "missingnessSets": "missingnessSets",  # No change
    "partType": "partType",  # Not sure?
    "qualityFlag": "qualityIndicators",
    "specimenSets": "specimenSets",  # No change
}

# In the ODM data dictionary parts sheet, any column that ends with the string ODM_PARTS_COLUMN_CLASS_TAG begins
# with the name of an ODM class (eg. measuresOrder, protocolStepsOrder, etc). This is used by
# odm_get_available_class_names to extract all the known class names from the data dictionary.
ODM_PARTS_COLUMN_CLASS_TAG = "Order"


def odm_get_available_class_names(headers: Union[pd.DataFrame, List[str]]) -> List[str]:
    """Get a list of all ODM class/table names that are defined in a ODM parts sheet that contains
    the specified headers.

    Args:
        headers (Union[pd.DataFrame, List[str]]): Either a list of all headers in the ODM parts sheet, or the actual
            DataFrame for the parts sheet.

    Returns:
        List[str]: List of all class/table names that the parts sheet defines.
    """
    if isinstance(headers, pd.DataFrame):
        headers = headers.columns
    headers = [
        h[: -len(ODM_PARTS_COLUMN_CLASS_TAG)]
        for h in headers
        if h.endswith(ODM_PARTS_COLUMN_CLASS_TAG)
        and len(h) > len(ODM_PARTS_COLUMN_CLASS_TAG)
    ]
    return headers


def odm_get_fk_target_class(df: pd.DataFrame, part_id: str) -> Optional[str]:
    """Get the name of the class that the foreign key, that has the part id part_id, is a primary
    key for.

    Args:
        df (pd.DataFrame): The full parts DataFrame. It must contain a row where "partID" is equal
            to part_id, and a column for each class name (ie. each odm_get_available_class_names) where the
            value is "pK" (ignoring case) if part_id is a primary key in that class.
        part_id (str): The part_id to get the class that it is a primary key for.

    Raises:
        ValueError: Either the part_id was not found in df["partID"] or it is a primary key in
            more than one class.

    Returns:
        Optional[str]: The class that the part ID is a primary key for. Or None if it is not
            a primary key.
    """
    # Get the row in df that matches the part_id
    part_id_filt = df["partID"] == part_id
    if part_id_filt.sum() == 0:
        return None
    if part_id_filt.sum() > 1:
        raise ValueError(f"Matched multiple partID rows for partID '{part_id}'")
    
    # Get a DataFrame with columns "variable" and "value", where each row has a class name from odm_get_available_class_names
    # in the "variable" column and the value "pk" in the "value" column if our part_id is a primary key in
    # the class
    class_names = odm_get_available_class_names(df)
    class_values = pd.melt(
        df.loc[part_id_filt, class_names].map(
            lambda x: "" if pd.isna(x) else str(x).lower()
        )
    )

    # Get the row(s) where the value is "pk", we should get 1 or no rows.
    pk_filt = class_values["value"] == "pk"
    all_pks = class_values[pk_filt]["variable"].tolist()
    if len(all_pks) > 1:
        raise ValueError(
            f"Foreign key '{part_id}' is a primary key in multiple tables: {', '.join(all_pks)}"
        )
    if len(all_pks) == 1:
        return all_pks[0]

    # part_id is not a primary key. See if it is an alias for a primary key, and if
    # so return the class that the primary key belongs to. Note that v2 data dictionary
    # does not have an fKAliasID column
    if "fKAliasID" in df.columns:
        fk_alias_id = df.loc[part_id_filt, "fKAliasID"].iloc[0]
        if not pd.isna(fk_alias_id):
            return odm_get_fk_target_class(df, fk_alias_id)
    
    return None


def odm_get_header_rows(
    df: pd.DataFrame,
    tables: Union[str, List[str]],
    header_tags: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    """Retrieve all rows in the DataFrame that correspond to a column in any of the specified
    ODM tables.

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
        header_tags = _odm_header_tags
    if isinstance(header_tags, str):
        header_tags = [header_tags]
    if isinstance(tables, str):
        tables = [tables]
    lower_header_tags = [h.lower() for h in header_tags]
    lower_df = df[tables].map(lambda x: x.lower() if isinstance(x, str) else x)
    is_header = lower_df[tables].isin(lower_header_tags)
    is_header = is_header.sum(axis=1)
    return df[is_header > 0].copy()


def odm_keep_active_rows(
    df: pd.DataFrame,
    status_column: str = "status",
    keep_status: Union[Any, List[Any]] = "active",
) -> pd.DataFrame:
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


def odm_get_enum_name_from_part_id(
    part_id: str, recognized_enums: Optional[List[str]] = None
) -> str:
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
    if part_id in _odm_enum_name_exceptions.keys():
        name = _odm_enum_name_exceptions[part_id]
    else:
        name = f"{part_id}s"
    if recognized_enums is not None and name not in recognized_enums:
        return "string"
    return name


def set_range_of_slot(
    schema: SchemaDefinition,
    class_name: str,
    slot_name: str,
    rng: Union[str, List[str]],
):
    class_defn = schema.classes[class_name]
    slot_defn = class_defn.slot_usage[slot_name]
    if isinstance(rng, str):
        rng = [rng]
    if len(rng) > 1:
        slot_defn.range = None
        slot_defn.any_of = [{"range": r} for r in rng]
    else:
        slot_defn.range = rng[0]


def add_missingness_set(schema: SchemaDefinition, parts_file: Union[str, Path]):
    """Based on the parts sheet of the ODM data dictionary, add the missingness sets
    (ie. genMissingNessSet/nrNAMissingnessSet) to any slot that should have one of these missingness sets.

    Args:
        schema (SchemaDefinition): The schema to modify in place.
        parts_file (Union[str, Path]): The ODM data dictionary parts file.
    """
    parts_df = read_data_frame(parts_file, keep_default_na=False, na_values=[""])
    for class_defn in schema.classes.values():
        # Go through all slot usages
        for slot_defn in class_defn.slot_usage.values():
            rows = parts_df[parts_df["partID"] == slot_defn.name]
            if rows.empty:
                continue
            missingness_set = rows["missingnessSet"].iloc[0]
            if not pd.isna(missingness_set):
                ranges = get_ranges_of_slot_defn(slot_defn)
                # Add the missingness set if it is not already in the range
                if missingness_set not in ranges:
                    ranges.append(missingness_set)
                    set_range_of_slot(schema, class_defn.name, slot_defn.name, ranges)
