"""
Utility functions for ODM LinkML Schema Generator, specific to ODM dictionary.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from linkml_runtime.linkml_model.meta import SchemaDefinition

from odm_linkmlgen.utils.general_utils import get_logger, get_na_values, read_data_frame
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

# For mapping the ODM data types (in dataType column) to LinkML datatypes
_data_types_map = {
    "varchar": "string",
    "dateTime": "datetime",
    "datetime": "datetime",
    "date": "date",
    "integer": "integer",
    "float": "float",
    "boolean": "booleanSet",
    "categorical": "string",
    "blob": "blob",  # @TODO: How should we deal with blobs? I'm not sure if LinkML has this data type
}

# The ODM data dictionary columns that need NA values of their own, and the NA values to use
# for them (see get_dictionary_read_kwargs). Only a truly empty cell counts as missing in these
# columns, because values such as "NA", "None", and "null" are real ODM parts. Every other
# column keeps Pandas' default NA strings.
_dictionary_na_values = {"partID": "", "label": ""}

# In the ODM data dictionary parts sheet, any column that ends with the string ODM_PARTS_COLUMN_CLASS_TAG begins
# with the name of an ODM class (eg. measuresOrder, protocolStepsOrder, etc). This is used by
# odm_get_available_class_names to extract all the known class names from the data dictionary.
ODM_PARTS_COLUMN_CLASS_TAG = "Order"


def odm_get_available_class_names(headers: pd.DataFrame | list[str]) -> list[str]:
    """Get a list of all ODM class/table names that are defined in a ODM parts sheet that contains
    the specified headers.

    Args:
        headers (pd.DataFrame | list[str]): Either a list of all headers in the ODM parts sheet, or the actual
            DataFrame for the parts sheet.

    Returns:
        list[str]: List of all class/table names that the parts sheet defines.
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


def odm_get_fk_target_class(df: pd.DataFrame, part_id: str) -> str | None:
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
        str | None: The class that the part ID is a primary key for. Or None if it is not
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
        if fk_alias_id == part_id:
            raise ValueError(f"Value under fkAliasID for part ID '{part_id}' must be different than the partID")
        elif not pd.isna(fk_alias_id):
            return odm_get_fk_target_class(df, fk_alias_id)

    return None


def odm_get_header_rows(
    df: pd.DataFrame,
    tables: str | list[str],
    header_tags: str | list[str] | None = None,
) -> pd.DataFrame:
    """Retrieve all rows in the DataFrame that correspond to a column in any of the specified
    ODM tables.

    This corresponds to rows that are either a primary key, a foreign key, or a header in any
    of the tables. Note that to determine if a row is a column, the DataFrame df must
    have a column with the same name as the table.

    Args:
        df (pd.DataFrame): The DataFrame to retrieve the rows from.
        tables (str | list[str]): The table name(s) to retrieve the rows for. For each
            table name a column with that name must be present in df.
        header_tags (str | list[str] | None): The header tags (ie. header types) to search for.
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
    keep_status: Any | list[Any] = "active",
) -> pd.DataFrame:
    """Keep only rows that have an "active" status. Status is specified in a single column in the
    DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to filter, retrieving only active rows.
        status_column (str, optional): The column name that contains each row's status. Defaults to "status".
        keep_status (Any | list[Any], optional): The string(s) that indicate an active status. Defaults to "active".

    Returns:
        pd.DataFrame: df filtered to only have active status rows. A copy of the DataFrame is made before
            returning.
    """
    if not isinstance(keep_status, (list, tuple)):
        keep_status = [keep_status]
    keep_filt = df[status_column].str.strip().isin(keep_status)
    df = df[keep_filt]
    return df.copy()


def odm_get_data_type_of_row(row: pd.Series) -> str:
    """Get the LinkML range (data type) for a single row of the ODM parts sheet.

    The "mmaSet" column takes precedence: if the row names an enumeration then that
    enumeration is the row's range. Otherwise the row's ODM "dataType" is mapped to
    the equivalent LinkML data type (eg. "varchar" becomes "string").

    Args:
        row (pd.Series): A row of the ODM parts sheet. It must have an "mmaSet" and a
            "dataType" column.

    Returns:
        str: The LinkML range for the row. This is the row's enumeration name if it has
            one, otherwise the LinkML data type that the row's ODM "dataType" maps to.
            An ODM data type with no LinkML equivalent (including "categorical", which is
            only meaningful together with an "mmaSet") falls back to "string".
    """
    if pd.isna(row["mmaSet"]):
        return _data_types_map.get(row["dataType"], "string")
    else:
        return row["mmaSet"]


def set_range_of_slot(
    schema: SchemaDefinition,
    class_name: str,
    slot_name: str,
    rng: str | list[str],
):
    """Set the range of a slot usage in the schema, in place.

    Args:
        schema (SchemaDefinition): The schema to modify in place.
        class_name (str): The name of the class that has the slot usage to modify.
        slot_name (str): The name of the slot usage to set the range of.
        rng (str | list[str]): The range(s) to set. A single range is set as the slot's
            range. Multiple ranges are set as any_of (and the slot's range is cleared), which is
            how LinkML represents a slot that accepts more than one range.
    """
    class_defn = schema.classes[class_name]
    slot_defn = class_defn.slot_usage[slot_name]
    if isinstance(rng, str):
        rng = [rng]
    if len(rng) > 1:
        slot_defn.range = None
        slot_defn.any_of = [{"range": r} for r in rng]
    else:
        slot_defn.range = rng[0]


def add_missingness_set(schema: SchemaDefinition, parts_file: str | Path):
    """Based on the parts sheet of the ODM data dictionary, add the missingness sets
    (ie. genMissingNessSet/nrNAMissingnessSet) to any slot that should have one of these missingness sets.

    Args:
        schema (SchemaDefinition): The schema to modify in place.
        parts_file (str | Path): The ODM data dictionary parts file.
    """
    parts_df = read_data_frame(parts_file, **get_dictionary_read_kwargs(parts_file))
    for class_defn in schema.classes.values():
        # Go through all slot usages
        for slot_defn in class_defn.slot_usage.values():
            # Primary keys identify the row, so they cannot take on the missingness set. Every
            # other slot can, including a required one: "required" says a value must be given,
            # not that the value cannot be a documented missingness reason.
            if slot_defn.identifier:
                continue
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


def get_dictionary_read_kwargs(file: str | Path) -> dict:
    """Build the Pandas kwargs to read an ODM data dictionary file with.

    Every read of a dictionary file needs the same two corrections, so they are built in
    one place here rather than repeated at each read:

    - Only a truly empty partID or label cell counts as missing. Values such as "NA",
      "None", and "null" are real ODM parts that Pandas would otherwise read as missing
      data. Every other column keeps Pandas' default NA strings — get_na_values is what
      expands that into the per-column mapping, which is why keep_default_na is False.
    - A partID and a label are always wanted as strings. Pandas would otherwise type a
      column of "TRUE"/"FALSE" values as boolean, and a column of digits as a number,
      neither of which matches the part ID written in the dictionary. The converters
      coerce both columns back to strings, writing a boolean as "TRUE"/"FALSE" so that a
      part read from the Excel workbook matches the same part read from a CSV sheet.

    The two overlap in the partID and label columns, and which one wins is Pandas' choice,
    not ours: pd.read_excel applies the NA values first, so an empty cell arrives as NA,
    while pd.read_csv hands the raw text to the converter and skips NA parsing for a
    converted column, so an empty cell arrives as "". Code that tests one of these two
    columns for emptiness has to allow for both.

    Args:
        file (str | Path): The dictionary file the kwargs are for, either the Excel
            (".xlsx") data dictionary or one of the ".csv" sheets extracted from it. Only
            the file's sheet names and header rows are read, so this is cheap to call
            before the real read.

    Returns:
        dict: The keep_default_na, na_values, and converters kwargs for reading the file.
            na_values follows get_na_values: for a CSV file it is keyed by column name and
            the whole dictionary can be passed straight to read_data_frame (or pd.read_csv).
            For an Excel file it is keyed by sheet name instead, which is a shape no single
            Pandas call takes, so it goes to extract_sheets' own na_values argument —
            extract_sheets reads one sheet at a time — and only the remaining kwargs are
            passed on as its read_excel_kwargs.

    Raises:
        ValueError: The file has an extension other than ".xlsx" or ".csv" (raised by
            get_na_values).
    """

    def _to_string_converter(v: Any) -> str:
        """Convert one cell value read from the dictionary to a string.

        Args:
            v (Any): The value Pandas parsed the cell as.

        Returns:
            str: The value as a string. A boolean becomes "TRUE"/"FALSE", which is how the
                dictionary itself writes it, rather than Python's "True"/"False".
        """
        if isinstance(v, bool):
            return str(v).upper()
        return str(v)

    na_values = _dictionary_na_values
    if Path(file).suffix.lower() == ".xlsx":
        # get_na_values keys its overrides by sheet name for an Excel file, so give the same
        # column overrides to every sheet of the workbook. A sheet that has no partID or
        # label column simply ignores them, which is why the sheet names do not need to be
        # known here.
        with pd.ExcelFile(file) as excel_file:
            na_values = {
                sheet: _dictionary_na_values for sheet in excel_file.sheet_names
            }

    return {
        "keep_default_na": False,
        "na_values": get_na_values(file, na_values=na_values),
        "converters": {"partID": _to_string_converter, "label": _to_string_converter},
    }
