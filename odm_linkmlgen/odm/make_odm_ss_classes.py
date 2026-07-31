"""
Creates Schemasheets for all classes (ie. tables) based on the ODM data dictionary parts sheet.
The outputs will be named "class_{table_name}.tsv".
"""

import os
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from odm_linkmlgen.odm.odm_utils import (
    odm_get_available_class_names,
    odm_get_enum_name_from_part_id,
    odm_get_fk_target_class,
    odm_get_header_rows,
    odm_keep_active_rows,
)
from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Create a Schemasheet for all classes (tables) found in the parts
sheet that was extracted from the ODM data dictionary."""

PARTS_FILE_HELP = """The parts sheet (CSV) that was extracted from the ODM data
dictionary."""

OUTPUT_DIR_HELP = """The location to save all the Schemasheets. One Schemasheet
per class is created, with the name \"class_{class_name}.tsv\""""

RECOGNIZED_ENUMS_HELP = """List of all recognized enumeration names."""


# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
headers = {
    "class": "class",
    "partID": "slot",
    "partLabel": "title",
    "identifier": "identifier",
    "required": "required",
    "dataType": "range",
    "partDesc": "description",
    "minValue": "minimum_value",
    "maxValue": "maximum_value",
    "pattern": "pattern",
    "partInstr": "notes",
}

# For mapping the ODM data types to LinkML datatypes
_data_types_map = {
    "varchar": "string",
    "dateTime": "datetime",
    "datetime": "datetime",
    "integer": "integer",
    "float": "float",
    "boolean": "booleanSet",
    "blob": "blob",  # @TODO: How should we deal with blobs? I'm not sure if LinkML has this data type
}


def _extract_pattern(row: pd.Series) -> str | None:
    """Extract the regex pattern to match for validation for the specified row.

    Args:
        row (pd.Series): The row to extract the pattern for.

    Returns:
        str | None: The regex pattern for validation, or None if no pattern required.
    """
    min_length = row["minLength"]
    max_length = row["maxLength"]
    if pd.isna(min_length) and pd.isna(max_length):
        return None

    # Create a string of length min_length to max_length
    min_length = "0" if pd.isna(min_length) else str(int(min_length))
    max_length = "" if pd.isna(max_length) else str(int(max_length))
    pattern = f"^.{{{min_length},{max_length}}}$"
    return pattern


def extract_class(
    df: pd.DataFrame, class_name: str, output_dir: str, recognized_enums: list[str]
) -> tuple[str, pd.DataFrame]:
    """Create a Schemasheet for the specified class name using the data in a
    DataFrame loaded from the parts sheet of the ODM data dictionary.

    Args:
        df (pd.DataFrame): The parts sheet of the ODM data dictionary.
        class_name (str): The name of the class (ie. table) to extract.
        output_dir (str): The location to save the Schemasheet. The actual
            Schemasheet will be named "class_{class_name}.tsv".
        recognized_enums (list[str]): List of all recognized enumeration names.

    Returns:
        tuple[str, pd.DataFrame]: The full path and file name to the saved Schemasheet as
            well as the DataFrame of the Schemasheet.
    """

    # Get all rows in the table that correspond to a header in the parts sheet (ie. rows identified
    # as a primary key, foreign key, or header)
    table_df = odm_get_header_rows(df, class_name)

    # Only keep rows that are marked as "active" under the "status" column
    table_df = odm_keep_active_rows(table_df)

    # Select the columns of interest, and rename some of the columns
    keep_cols = [
        "partID",
        "partLabel",
        "partDesc",
        "partType",
        "partInstr",
        "fKAliasID",
        "mmaSet",
        f"{class_name}",
        f"{class_name}Required",
        f"{class_name}Order",
        "dataType",
        "minValue",
        "maxValue",
        "minLength",
        "maxLength",
    ]
    # These columns are in keep_cols, but are optional (ie. we don't raise an exception if the
    # column doesn't exist in table_df; should be a subset of keep_cols)
    optional_keep_cols = [
        "fKAliasID",
    ]
    missing_cols = [
        c for c in set(keep_cols) - set(optional_keep_cols) if c not in table_df.columns
    ]
    if len(missing_cols) > 0:
        raise RuntimeError(
            f"Missing columns in parts sheet for class {class_name}: {', '.join(missing_cols)}"
        )
    table_output_df = table_df[[c for c in keep_cols if c in table_df.columns]].copy()
    columns = list(table_output_df.columns)
    columns[columns.index(class_name)] = "headerType"
    columns[columns.index(f"{class_name}Required")] = "required"
    columns[columns.index(f"{class_name}Order")] = "order"
    table_output_df.columns = columns

    # Cast "order" to floats
    table_output_df["order"] = table_output_df["order"].astype(float)

    # Set "required" field (ie. row has the value "mandatory" in the "required" column)
    table_output_df["required"] = table_output_df["required"].isin(["mandatory"])

    # Set the dataType (range) by mapping the values in the "dataType" column to
    # the data types recognized by LinkML (eg. map varchar to string)
    for k, v in _data_types_map.items():
        table_output_df.loc[table_output_df["dataType"] == k, "dataType"] = v

    # Set the dataType for enumerations that have an mmaSet (the data type/enumeration is the value in "mmaSet")
    mmaset_filt = ~pd.isna(table_output_df["mmaSet"])
    table_output_df.loc[mmaset_filt, "dataType"] = table_output_df.loc[
        mmaset_filt, "mmaSet"
    ]

    # Set the dataType for remaining enumerations that are categorical (ie. the ones that do not have an mmaSet that was set previously)
    # The enumeration names are a variant of the value found in the partID column (eg. we often just need to add an "s" to
    # the end of the partID column, see utils.odm_get_enum_name_from_part_id)
    categorical_filt = (~mmaset_filt) & (table_output_df["dataType"] == "categorical")
    table_output_df.loc[categorical_filt, "dataType"] = table_output_df.loc[
        categorical_filt, "partID"
    ].apply(
        lambda part_id: odm_get_enum_name_from_part_id(
            part_id, recognized_enums=recognized_enums
        )
    )

    # Set identifiers (primary keys)
    table_output_df["identifier"] = (
        table_output_df["headerType"].astype(str).str.lower() == "pk"
    )

    # Look for all foreign keys, change the dataType to be the class name of the class the foreign key points to
    fk_filt = table_output_df["headerType"].astype(str).str.lower() == "fk"
    for idx in table_output_df.loc[fk_filt, "partID"].index:
        fk_name = table_output_df.loc[idx, "partID"]
        fk_target = odm_get_fk_target_class(df, fk_name)
        if fk_target is not None:
            table_output_df.loc[idx, "dataType"] = fk_target

    # Set the regex "pattern" where required
    table_output_df["pattern"] = table_output_df.apply(_extract_pattern, axis=1)

    # Sort by "order" column
    table_output_df = table_output_df.sort_values("order")

    # Add the description and title of the class
    class_info = df[df["partID"] == class_name][["partLabel", "partDesc"]].to_dict(
        orient="records"
    )[0]
    class_info_df = pd.DataFrame(class_info, index=[max(table_output_df.index) + 1])
    table_output_df = pd.concat([table_output_df, class_info_df])

    # Set the table name for all the rows (class). We're only working with one table name
    # at a time, so they're all the same.
    table_output_df["class"] = class_name

    # Save to disk
    output_file = Path(output_dir) / f"class_{class_name}.tsv"
    logger.info(f"Saving classes to {output_file}")
    save_schemasheet(table_output_df, output_file, headers)

    return output_file, table_output_df


def extract_all_classes(parts_file: str, output_dir: str, recognized_enums: list[str]):
    """Create a Schemasheet for all classes (tables) found in the parts sheet that was
    extracted from the ODM data dictionary.

    Args:
        parts_file (str): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_dir (str): The location to save all the Schemasheets. One Schemasheet per
            class is created, with the name "class_{class_name}.tsv"
        recognized_enums (list[str]): List of all recognized enumeration names.
    """
    if not output_dir:
        output_dir = os.path.dirname(parts_file)

    df = read_data_frame(parts_file, keep_default_na=False, na_values=[""])

    for class_name in odm_get_available_class_names(df):
        logger.info(f"Processing table {class_name}...")
        extract_class(df, class_name, output_dir, recognized_enums=recognized_enums)


@app.command(help=MAIN_HELP)
def main(
    parts_file: Annotated[Path, typer.Option(show_default=False, help=PARTS_FILE_HELP)],
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
    recognized_enums: Annotated[
        list[str] | None, typer.Option(show_default=False, help=RECOGNIZED_ENUMS_HELP)
    ] = None,
):
    """CLI entry point: create a Schemasheet for every class (table) found in the ODM
    parts sheet.

    Args:
        parts_file (Path): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_dir (Path): The location to save all the Schemasheets to. One Schemasheet
            is saved per class.
        recognized_enums (list[str] | None, optional): List of all recognized enumeration names.
            Defaults to None.
    """
    logger.info("Making ODM Classes...")
    extract_all_classes(
        parts_file=parts_file, output_dir=output_dir, recognized_enums=recognized_enums
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
