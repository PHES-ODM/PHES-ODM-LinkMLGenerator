"""
Creates Schemasheets for all classes (ie. tables) based on the ODM data dictionary parts sheet.
The outputs will be named "class_{table_name}.tsv".

@TODO: We currently don't have any descriptions or titles for the classes. These should be added.

## Example

```python
from odm_linkmlgen.odm.make_odm_ss_classes import extract_all_classes

extract_all_classes("odm_v2/dictionary/parts.csv", "odm_v2/schemasheets")
```
"""

from typing import Tuple, Optional, List, Annotated
from pathlib import Path
import pandas as pd
import os
import typer

from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet
from odm_linkmlgen.odm.odm_utils import (
    odm_keep_active_rows,
    odm_get_enum_name_from_part_id,
    odm_get_header_rows,
    odm_get_available_class_names,
)

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


def get_fk_target_class(df: pd.DataFrame, part_id: str) -> Optional[str]:
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

    # Get the row(s) where the value is "pk", we should get 0 or no rows.
    fk_name_filt = class_values["value"] == "pk"
    all_pks = class_values[fk_name_filt]["variable"].tolist()
    if len(all_pks) == 0:
        logger.warning(f"Foreign key '{part_id}' is not a primary key in any table")
        return None
    if len(all_pks) > 1:
        raise ValueError(
            f"Foreign key '{part_id}' is a primary key in multiple tables: {', '.join(all_pks)}"
        )

    return all_pks[0]


def extract_class(
    df: pd.DataFrame, class_name: str, output_dir: str, recognized_enums: List[str]
) -> Tuple[str, pd.DataFrame]:
    """Create a Schemasheet for the specified class name using the data in a
    DataFrame loaded from the parts sheet of the ODM data dictionary.

    Args:
        df (pd.DataFrame): The parts sheet of the ODM data dictionary.
        class_name (str): The name of the class (ie. table) to extract.
        output_dir (str): The location to save the Schemasheet. The actual
            Schemasheet will be named "class_{class_name}.tsv".
        recognized_enums (List[str]): List of all recognized enumeration names.

    Returns:
        Tuple[str, pd.DataFrame]: The full path and file name to the saved Schemasheet as
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
    missing_cols = [c for c in keep_cols if c not in table_df.columns]
    if len(missing_cols) > 0:
        raise RuntimeError(
            f"Missing columns in parts sheet for class {class_name}: {', '.join(missing_cols)}"
        )
    table_output_df = table_df[keep_cols].copy()
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
        fk_target = get_fk_target_class(df, fk_name)
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


def extract_all_classes(parts_file: str, output_dir: str, recognized_enums: List[str]):
    """Create a Schemasheet for all classes (tables) found in the parts sheet that was
    extracted from the ODM data dictionary.

    Args:
        parts_file (str): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_dir (str): The location to save all the Schemasheets. One Schemasheet per
            class is created, with the name "class_{class_name}.tsv"
        recognized_enums (List[str]): List of all recognized enumeration names.
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
        List[str], typer.Option(show_default=False, help=RECOGNIZED_ENUMS_HELP)
    ] = None,
):
    logger.info("Making ODM Classes...")
    extract_all_classes(
        parts_file=parts_file, output_dir=output_dir, recognized_enums=recognized_enums
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
