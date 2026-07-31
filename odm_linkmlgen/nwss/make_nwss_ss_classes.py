import os
import re
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
import typer

from odm_linkmlgen.nwss.nwss_utils import (
    TABLE_NAME_COL,
    DictionaryColumns,
    SlotToEnumColumns,
    parse_enums_sheet,
    splitup_metadata_sheet,
)
from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Extract all classes from the Metadata file extracted from 
a NWSS data dictionary Excel file, and save all the classes as Schemasheets to
the output_dir. The saved Schemasheets files are named
\"classes_{table_name}.tsv\""""

METADATA_FILE_HELP = """The Metadata sheet extracted from a NWSS data dictionary
Excel file."""

ENUMS_FILE_HELP = """The enums (Value Sets) sheet extracted from a NWSS data
dictionary Excel file."""

OUTPUT_DIR_HELP = """The directory to save all the class Schemasheets files to. One
file per NWSS class is saved."""

SINGLE_TABLE_HELP = """If set then merge all classes into a single class called
nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate."""

DETAILED_ENUM_NAMES_HELP = """If specified, then a list of enum names where we want
to use detailed enum names. Detailed enum names are in the format
"enum_name[slot]" where "slot" is the name of the slot whose range is the enum
(ie. each time the enum is used by a slot it uses a different enum name, eg
"vs_yne[stormwater_input]")."""

headers = {
    "class": "class",
    "slot": "slot",
    "range": "range",
    "required": "required",
    "description": "description",
    "pattern": "pattern",
}

# If DictionaryColumns.DATA_TYPE for a row matches a key in _data_types_validation_info, then use the corresponding values in the dictionary
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
) -> dict[str, Any]:
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
            enums_df, then we try to get the enum name from the DictionaryColumns.VALUE_SET column in the row.

    Returns:
        dict[str, Any]: Key-value pairs to set for the slot usage corresponding to the row.
    """
    results = {}

    # For category data types, use the enum found in DictionaryColumns.VALUE_SET
    if row[DictionaryColumns.DATA_TYPE] == "category":
        val = None
        slot_name = row["slot"]
        # First try to get the enum name from enums_df
        if enums_df is not None:
            enums_row = enums_df[enums_df[SlotToEnumColumns.SLOT] == slot_name]
            if len(enums_row) > 0:
                val = enums_row[SlotToEnumColumns.ENUM].iloc[0].strip()
        # If we did not get the enum name from enums_df then try to get it from the DictionaryColumns.VALUE_SET column
        if val is None and DictionaryColumns.VALUE_SET in row.index:
            val = row[DictionaryColumns.VALUE_SET]
            if isinstance(val, (str)):
                val = val.strip("[] ").split(":")[1].strip()
            else:
                val = None
        if pd.isna(val):
            logger.error(f"No enumeration for categorical slot {slot_name}")
            # raise ValueError(f"No enumeration for categorical slot {slot_name}")
        results["range"] = val
        return results

    # See if any custom regex matches occur with _data_types_validation_info.
    # If the key (pattern) matches row[DictionaryColumns.DATA_TYPE], then the returned
    # info is the value of _data_types_validation_info.
    for pattern, dict in _data_types_validation_info.items():
        if re.match(pattern, row[DictionaryColumns.DATA_TYPE]) is not None:
            for k, v in dict.items():
                results[k] = v
            return results

    if "#" in row[DictionaryColumns.DATA_TYPE]:
        # If there are # symbols in the DictionaryColumns.DATA_TYPE, then convert the #'s to
        # [0-9] regex matches.
        val = row[DictionaryColumns.DATA_TYPE]
        val = val[val.index("#") : val.rindex("#") + 1]
        val = val.replace("#", "[0-9]")
        results["range"] = "string"
        results["pattern"] = val
    else:
        # Copy the DictionaryColumns.DATA_TYPE to the "range" unchanged
        results["range"] = row[DictionaryColumns.DATA_TYPE]

    return results


def parse_table_df(
    df: pd.DataFrame,
    enums_df: pd.DataFrame | None = None,
    detailed_enum_names: list[str] | None = None,
) -> pd.DataFrame:
    """Given the DataFrame extracted from a NWSS data dictionary metadata sheet, that
    represents a single table in NWSS, set all the columns used by Schemasheets and
    prepare the table for Schemasheets processing.

    Args:
        df (pd.DataFrame): The DataFrame representing a single table in NWSS. We will
            make a copy of this and modify it to be a proper Schemasheets table.
        enums_df (pd.DataFrame | None): An optional DataFrame with the columns
            SlotToEnumColumns.SLOT and SlotToEnumColumns.ENUM, where the slot is a categorical
            column name in NWSS and the enum is the name of the enum assigned to the slot.
            the name of the enumeration to assign to the slot. If None then
            we assume that the enum name is found in the DictionaryColumns.VALUE_SET column of
            df.
        detailed_enum_names (list[str] | None, optional): If specified, then a list of enum
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
    if DictionaryColumns.SUBMISSION_REQUIREMENT in df.columns:
        df["required"] = df[DictionaryColumns.SUBMISSION_REQUIREMENT].map(
            lambda x: isinstance(x, str) and x.strip(" .").lower() in ["required"]
        )
    else:
        df["required"] = False

    # Add description
    df["description"] = df[DictionaryColumns.DESCRIPTION]

    # Add validation and range info
    results = [
        _get_range_and_validation_info(row, enums_df) for _, row in df.iterrows()
    ]
    all_keys = {k for vals in results for k in vals}
    for k in all_keys:
        df[k] = [vals.get(k) for vals in results]

    if detailed_enum_names is not None and len(detailed_enum_names) > 0:
        for enum_name in detailed_enum_names:
            filt = df["range"] == enum_name
            df.loc[filt, "range"] = df.loc[filt].apply(
                lambda x, enum_name=enum_name: f"{enum_name}[{x['slot']}]", axis=1
            )

    return df


def extract_all_classes(
    metadata_file: str | Path,
    enums_file: str | Path,
    output_dir: str | Path,
    single_table: bool | None = False,
    detailed_enum_names: list[str] | None = None,
):
    """Extract all classes from the Metadata file extracted from a NWSS data dictionary
    Excel file, and save all the classes as Schemasheets to the output_dir. The
    saved Schemasheets files are named "classes_{table_name}.tsv".

    Args:
        metadata_file (str | Path): The Metadata sheet extracted from a NWSS
            data dictionary Excel file.
        enums_file (str | Path): The enums (Value Sets) sheet extracted from a NWSS
            data dictionary Excel file.
        output_dir (str | Path): The directory to save all the class
            Schemasheets files to. One file per NWSS class is saved.
        single_table (bool | None): If True then merge all classes into a single class called
            nwss_utils.SINGLE_TABLE_NAME, otherwise keep all classes separate. Defaults to False.
        detailed_enum_names (list[str] | None, optional): If specified, then a list of enum
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


@app.command(help=MAIN_HELP)
def main(
    metadata_file: Annotated[
        Path, typer.Option(show_default=False, help=METADATA_FILE_HELP)
    ],
    enums_file: Annotated[Path, typer.Option(show_default=False, help=ENUMS_FILE_HELP)],
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
    single_table: Annotated[
        bool, typer.Option(show_default=True, help=SINGLE_TABLE_HELP)
    ] = False,
    detailed_enum_names: Annotated[
        list[str] | None,
        typer.Option(show_default=False, help=DETAILED_ENUM_NAMES_HELP),
    ] = None,
):
    """CLI entry point: extract all classes from the Metadata sheet of a NWSS data dictionary
    and save each one as a Schemasheet.

    Args:
        metadata_file (Path): The Metadata sheet extracted from a NWSS data dictionary.
        enums_file (Path): The enums (Value Sets) sheet extracted from a NWSS data dictionary.
        output_dir (Path): The directory to save all the class Schemasheets files to. One
            Schemasheet is saved per class.
        single_table (bool, optional): If set then merge all classes into a single class.
            Defaults to False.
        detailed_enum_names (list[str] | None, optional): List of enum names where we want to use the
            per-field (detailed) version of the enumeration. Defaults to None.
    """
    logger.info("Making NWSS classes...")
    extract_all_classes(
        metadata_file=metadata_file,
        enums_file=enums_file,
        output_dir=output_dir,
        single_table=single_table,
        detailed_enum_names=detailed_enum_names,
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
