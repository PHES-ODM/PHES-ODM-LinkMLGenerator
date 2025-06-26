# %%

import os
import argparse
from typing import Union, Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import re
import os

from odm_linkmlgen.nwss.nwss_utils import (
    SlotToEnumColumns,
    TABLE_NAME_COL,
    splitup_metadata_sheet,
    parse_enums_sheet,
)
from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

headers = {
    "class": "class",
    "slot": "slot",
    "range": "range",
    "required": "required",
    "description": "description",
    "pattern": "pattern",
}

# If "Data Type" for a row matches a key in _data_types_validation_info, then use the corresponding values in the dictionary
# for the slot
_data_types_validation_info = {
    r"^date ": {
        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",  # [yyyy]-[mm]-[dd]
        "range": "string",
    },
    r"^time,": {
        "pattern": "^[0-2]?[0-9]:[0-5][0-9](:[0-5][0-9])?$",  # [hh]:[mm] @TODO: Do not allow h:mm (must be hh:mm), and do not allow seconds
        "range": "string",
    },
    r"^time zone": {
        "pattern": "^(UTC|utc)[+|-][0-1][0-9]:[0-5][0-9]$",  # UTC-[hh]:[mm] @TODO: Only allow capital UTC
        "range": "string",
    },
    r"^NPDES permit number": {
        "pattern": "^[A-Za-z]{2}[0-9]{7}$|^-1$",  # <2-letter abbreviation><#######>, [NPDES permit number];  -1 if not permitted
        "range": "string",
    },
    r"^jurisdiction id": {
        "pattern": "^[0-9A-Za-z_\\-\\.]{1,20}$",  # a string 20 characters or less, containing only numbers, English alphabetic characters, underscores, and hyphens; white space is not allowed; not case sensitive
        "range": "string",  # @TODO: Do not allow dots in pattern
    },
    r"^list \(comma-separated integers\)": {
        # "pattern" : "^",                                # @TODO: Make regular expression for this
        "range": "string",
    },
    r"list \(comma-separated strings\)": {
        # "pattern" : "^",                                # @TODO: Make regular expression for this
        "range": "string",
    },
    r"^ZIP code": {
        "pattern": "^[0-9]{5}$",  # #####
        "range": "string",
    },
    r"^\<#####-###-##-##-##\>": {  # site_id
        "pattern": "^[0-9]{5}-[0-9]{3}-[0-9]{2}-[0-9]{2}-[0-9]{2}$",  # <#####-###-##-##-##>
        "range": "string",
    },
    r"^EPA Registry ID": {
        "pattern": "^[0-9]{12}$|^-1$",  # <############>, [EPA Registry ID]; -1 if not registered with EPA
        "range": "string",
    },
}


def _get_range_and_validation_info(
    row: pd.Series, enums_df: pd.DataFrame
) -> Dict[str, Any]:
    """Get the range and validation info for a row in the NWSS data dictionary (metadata sheet).
    The returned dictionary can contain multiple keys that should be set for the slot usage
    to enable validation for the row. For example, it may contain "minimum_value", "maximum_value",
    "pattern", or other values to set.

    Args:
        row (pd.Series): The row from the NWSS metadata sheet of the data dictionary.
        enums_df (pd.DataFrame): A DataFrame containing the columns SlotToEnumColumns.SLOT (to
            specify a categorical slot name in NWSS) and SlotToEnumColumns.ENUM (to specify the enum to
            assign to the slot). This is to get an enumeration name for the current slot if
            applicable. If enums_df is None, or if an enum for the current slot is not found in
            enums_df, then we try to get the enum name from the "Value Set" column in the row.

    Returns:
        Dict[str, Any]: Key-value pairs to set for the slot usage corresponding to the row.
    """
    results = {}

    # For category data types, use the enum found in "Value Set"
    if row["Data Type"] == "category":
        val = None
        slot_name = row["slot"]
        # First try to get the enum name from enums_df
        if enums_df is not None:
            enums_row = enums_df[enums_df[SlotToEnumColumns.SLOT] == slot_name]
            if len(enums_row) > 0:
                val = enums_row[SlotToEnumColumns.ENUM].iloc[0].strip()
        # If we did not get the enum name from enums_df then try to get it from the "Value Set" column
        if val is None and "Value Set" in row.index:
            val = row["Value Set"]
            val = val.strip("[] ").split(":")[1].strip()
        if val is None:
            # logger.error(f"No enumeration for categorical slot {slot_name}")
            raise ValueError(f"No enumeration for categorical slot {slot_name}")
        results["range"] = val
        return results

    # See if any custom regex matches occur with _data_types_validation_info.
    # If the key (pattern) matches row["Data Type"], then the returned
    # info is the value of _data_types_validation_info.
    for pattern, dict in _data_types_validation_info.items():
        if re.match(pattern, row["Data Type"]) is not None:
            for k, v in dict.items():
                results[k] = v
            return results

    if "#" in row["Data Type"]:
        # If there are # symbols in the "Data Type", then convert the #'s to
        # [0-9] regex matches.
        val = row["Data Type"]
        val = val[val.index("#") : val.rindex("#") + 1]
        val = val.replace("#", "[0-9]")
        results["range"] = "string"
        results["pattern"] = val
    else:
        # Copy the "Data Type" to the "range" unchanged
        results["range"] = row["Data Type"]

    return results


def parse_table_df(
    df: pd.DataFrame,
    enums_df: Optional[pd.DataFrame] = None,
    detailed_enum_names: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Given the DataFrame extracted from a NWSS data dictionary metadata sheet, that
    represents a single table in NWSS, set all the columns used by Schemasheets and
    prepare the table for Schemasheets processing.

    Args:
        df (pd.DataFrame): The DataFrame representing a single table in NWSS. We will
            make a copy of this and modify it to be a proper Schemasheets table.
        enums_df (Optional[pd.DataFrame]): An optional DataFrame with the columns
            SlotToEnumColumns.SLOT and SlotToEnumColumns.ENUM, where the slot is a categorical
            column name in NWSS and the enum is the name of the enum assigned to the slot.
            the name of the enumeration to assign to the slot. If None then
            we assume that the enum name is found in the "Value Set" column of
            df.
        detailed_enum_names (Optional[List[str]], optional): If specified, then a list of enum
            names where we want to use detailed enum names. Detailed enum names are in
            the format "enum_name[slot]" where "slot" is the name of the slot whose range
            is the enum (ie. each time the enum is used by a slot it uses a different
            enum name, eg "vs_yne[stormwater_input]"). Defaults to None.

    Returns:
        pd.DataFrame: The copied and modified DataFrame. This DataFrame does not contain
            the Schemasheets headers.
    """
    df = df.copy()

    df["class"] = df[TABLE_NAME_COL]
    df["slot"] = df["Field Name"] if "Field Name" in df.columns else df["variable name"]
    df["pattern"] = ""

    # Parse required column
    if "Submission Requirement" in df.columns:
        df["required"] = df["Submission Requirement"].map(
            lambda x: x.strip(" .").lower() in ["required"]
        )
    else:
        df["required"] = False

    # Add description
    df["description"] = df["Description"]

    # Add validation and range info
    for idx, row in df.iterrows():
        vals = _get_range_and_validation_info(row, enums_df)
        for k, v in vals.items():
            if k not in df.columns:
                df[k] = None
        df.loc[idx, vals.keys()] = vals

    if detailed_enum_names is not None and len(detailed_enum_names) > 0:
        for enum_name in detailed_enum_names:
            filt = df["range"] == enum_name
            df.loc[filt, "range"] = df.loc[filt].apply(
                lambda x: f"{enum_name}[{x['slot']}]", axis=1
            )

    return df


def extract_all_classes(
    metadata_file: Union[str, Path],
    enums_file: Union[str, Path],
    output_dir: Union[str, Path],
    single_table: Optional[bool] = False,
    detailed_enum_names: Optional[List[str]] = None,
):
    """Extract all classes from the Metadata file extracted from a NWSS data dictionary
    Excel file, and save all the classes as Schemasheets to the output_dir. The
    saved Schemasheets files are named "classes_{table_name}.tsv".

    Args:
        metadata_file (Union[str, Path]): The Metadata sheet extracted from a NWSS
            data dictionary Excel file.
        enums_file (Union[str, Path]): The enums (Value Sets) sheet extracted from a NWSS
            data dictionary Excel file.
        output_dir (Union[str, Path]): The directory to save all the class
            Schemasheets files to. One file per NWSS class is saved.
        single_table (Optional[bool]): If True then merge all classes into a single class called
            nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate. Defaults to False.
        detailed_enum_names (Optional[List[str]], optional): If specified, then a list of enum
            names where we want to use detailed enum names. Detailed enum names are in
            the format "enum_name[slot]" where "slot" is the name of the slot whose range
            is the enum (ie. each time the enum is used by a slot it uses a different
            enum name, eg "vs_yne[stormwater_input]"). Defaults to None
    """
    enums_df = read_data_frame(enums_file) if enums_file else None
    if enums_df is not None:
        enums_df, _ = parse_enums_sheet(enums_df)
    df = read_data_frame(metadata_file)
    all_tables = splitup_metadata_sheet(df, single_table=single_table)

    # Go through all the tables and parse them
    for table_name, table_df in all_tables.items():
        # Parse the table
        logger.info(f"Parsing class {table_name}")
        cur_df = parse_table_df(
            table_df, enums_df=enums_df, detailed_enum_names=detailed_enum_names
        )

        output_file = os.path.join(output_dir, f"classes_{table_name}.tsv")
        logger.info(f"Saving class to {output_file}")
        save_schemasheet(cur_df, output_file, headers)


if __name__ == "__main__":
    if "get_ipython" in globals():

        class opts:
            metadata_file = "../../gen/nwss_reporting/dictionary/metadata.csv"
            enums_file = "../../gen/nwss_reporting/dictionary/enums.csv"
            output_dir = "../../gen/nwss_reporting/schemasheets"
            single_table = True
            detailed_enum_names = ["vs_yne"]
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
            "--enums_file",
            type=str,
            help="Input enums (Value Sets) sheet from the NWSS data dictionary",
            required=False,
        )
        args.add_argument(
            "--output_dir",
            type=str,
            help="Directory to save the Schemasheets classes files to",
            required=True,
        )
        args.add_argument(
            "--single_table",
            action="store_true",
            help="If set then merge all classes into a single class, otherwise keep them as separate classes",
        )
        args.add_argument(
            "--detailed_enum_names",
            type=str,
            nargs="+",
            help="Convert these enums to use detailed names. For each slot that uses one of these enums, we will use a different enum name for the slot. eg. Instead of vs_yne, we would use enum names like vs_yne[stormwater_input]",
            required=False,
        )
        opts = args.parse_args()

    logger.info("Making NWSS enums...")

    extract_all_classes(
        opts.metadata_file,
        opts.enums_file,
        opts.output_dir,
        single_table=opts.single_table,
        detailed_enum_names=opts.detailed_enum_names,
    )

    logger.info("Finished!")
