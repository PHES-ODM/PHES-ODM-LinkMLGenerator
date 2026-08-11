"""
Utility functions for parsing the sheets of a NWSS data dictionary Excel file.

Two sheet layouts are handled:

- The metadata sheet is a flat list of every field in every table, with no column
  identifying the table. splitup_metadata_sheet splits it into one DataFrame per
  table by using the table boundary convention described in that function.
- The "Value Sets" sheet holds each enumeration in a pair of adjacent columns
  rather than stacked. parse_enums_sheet extracts them, along with the mapping
  from each field to the enumeration it uses.

resolve_slot_enums decides which enumeration each categorical field uses. It is the
single source of truth for that decision: both the enumeration Schemasheets and the
class Schemasheets are built from what it returns, so a field's range can never name
an enumeration that was generated under a different name. It also applies the
per-field naming of an enumeration shared by many fields (eg. "vs_yne" becomes
"vs_yne[stormwater_input]"), so that each field can carry its own permissible value
descriptions.
"""

from itertools import pairwise
from typing import Any, NamedTuple

import pandas as pd

from odm_linkmlgen.utils.general_utils import EMPTY_PERMISSIBLE_VALUE, get_logger

logger = get_logger(__name__)

TABLE_NAME_COL = "_table"
SINGLE_TABLE_NAME = "nwss"


class SlotToEnumColumns:
    """Column names of the DataFrame that maps each slot to the enumeration it uses."""

    SLOT: str = "slot"
    ENUM: str = "enum"


class DictionaryColumns:
    """Column headers used by the sheets of a NWSS data dictionary Excel file."""

    FIELD_NAME: str = "Field Name"
    # Some dictionary versions name the field column "variable name" instead of
    # DictionaryColumns.FIELD_NAME. See field_name_column.
    VARIABLE_NAME: str = "variable name"
    DATA_TYPE: str = "Data Type"
    VALUE_SET: str = "Value Set"
    FIELD: str = "Field"
    VALUE_SET_NAME: str = "Value Set Name"
    DESCRIPTION: str = "Description"
    SUBMISSION_REQUIREMENT: str = "Submission Requirement"


# The DictionaryColumns.DATA_TYPE value that marks a field as categorical, ie. as
# having an enumeration for its range.
CATEGORY_DATA_TYPE = "category"


class SlotEnum(NamedTuple):
    """The enumeration that one categorical slot uses.

    Attributes:
        base (str): The enumeration name as it appears in the data dictionary, and
            so the name of the enumeration to copy the permissible values from
            (eg. "vs_yn").
        name (str): The name to use in the generated schema. This is the detailed,
            per-slot form (eg. "vs_yn[pretreatment]") when base is one of the
            detailed enum names, and identical to base otherwise.
    """

    base: str
    name: str


def splitup_metadata_sheet(
    df: pd.DataFrame, single_table: bool = False
) -> dict[str, pd.DataFrame]:
    """Split the flat Metadata sheet of a NWSS data dictionary into one DataFrame per table.

    The Metadata sheet lists every table one after another. Once fully blank rows are dropped,
    each new table starts at a row with an empty DictionaryColumns.DATA_TYPE value, and that
    row holds the table name in the DictionaryColumns.FIELD_NAME column. All rows up to (but
    excluding) the next such row belong to that table. If no boundary row is found then the
    whole sheet is treated as a single table named SINGLE_TABLE_NAME.

    A TABLE_NAME_COL column, containing the table name, is added to each returned DataFrame.

    Args:
        df (pd.DataFrame): The Metadata sheet to split up.
        single_table (bool, optional): If True then all the tables are concatenated into a
            single table named SINGLE_TABLE_NAME. Defaults to False.

    Raises:
        ValueError: The same table name appears more than once in the Metadata sheet.

    Returns:
        dict[str, pd.DataFrame]: The tables, keyed by table name. Empty if df has no rows.
    """
    df = df.dropna(axis=0, how="all").reset_index(drop=True)

    if df.empty:
        return {}

    all_tables = {}

    # Get the table boundaries. After dropping empty rows (done previously), each new table occurs
    # whever an empty value is found in the DictionaryColumns.DATA_TYPE column. The rows with the empty values
    # contain the table name in the DictionaryColumns.FIELD_NAME column. All rows up to but excluding the next
    # empty value define that table.
    table_boundaries = list(df.index[pd.isna(df[DictionaryColumns.DATA_TYPE])]) + [
        df.index[-1] + 1
    ]

    if len(table_boundaries) <= 1:
        # The DataFrame is a single table
        table_name = SINGLE_TABLE_NAME
        df[TABLE_NAME_COL] = table_name
        return {table_name: df}

    # Split up the DataFrame along the table boundaries. The table name is the value in
    # the DictionaryColumns.FIELD_NAME column at the top of each table boundary.
    for cur_index, next_index in pairwise(table_boundaries):
        # Get table name and extract the table
        cur_table_name = df.loc[cur_index, DictionaryColumns.FIELD_NAME]
        cur_table_df = df.loc[cur_index + 1 : next_index - 1]

        if cur_table_name in all_tables:
            raise ValueError(
                f"Table {cur_table_name} has already been parsed in the Metadata sheet"
            )

        # Add the TABLE_NAME_COL and save the table
        cur_table_df = cur_table_df.reset_index(drop=True).copy()
        cur_table_df[TABLE_NAME_COL] = cur_table_name
        all_tables[cur_table_name] = cur_table_df

    if single_table:
        all_df = pd.concat(all_tables.values()).reset_index(drop=True)
        all_df[TABLE_NAME_COL] = SINGLE_TABLE_NAME
        all_tables = {SINGLE_TABLE_NAME: all_df}

    return all_tables


def parse_enums_sheet(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Parse the enums (Value Sets) sheet of a NWSS data dictionary Excel file, by extracting
    all enumerations, their names and permissible values, and returning each enum as a separate
    DataFrame that have the headers "enum", "permissible_value", and "description".

    Args:
        df (pd.DataFrame): The Value Sets sheet extracted from a NWSS data dictionary file.

    Returns:
        tuple[pd.DataFrame, dict[str, pd.DataFrame]]: The first pd.DataFrame of the tuple
            has a SlotToEnumColumns.SLOT column listing a field in the NWSS data dictionary, and a
            SlotToEnumColumns.ENUM column listing the enumeration name assigned to the slot.
            The returned dictionary contains the enum names as a key, and the corresponding
            Schemasheets DataFrame as the values.

    """
    logger.info("Parsing all enumerations")

    # Drop empty columns
    df = df.dropna(axis=1, how="all")

    # The DictionaryColumns.FIELD and DictionaryColumns.VALUE_SET_NAME maps the Field name in the data dictionary to
    # the enum name that that field uses.
    fields_df = df[[DictionaryColumns.FIELD, DictionaryColumns.VALUE_SET_NAME]].copy()
    fields_df.columns = [SlotToEnumColumns.SLOT, SlotToEnumColumns.ENUM]
    fields_df = fields_df.dropna(axis=0, how="all")

    # Extract all enums: Iterate over columns and first row
    # The column will indicate the enum name, although there are many unnamed columns.
    # In the first row below the enum name columns, there should be a DictionaryColumns.VALUE_SET column
    # (indicating the enum's allowable values) and in the next column a "Description" column.
    all_enums = {}
    for enum_value_col, desc_col in zip(df.columns[0:-1], df.columns[1:]):
        if (
            str(df.loc[0, enum_value_col]).strip().lower()
            != DictionaryColumns.VALUE_SET.lower()
            or str(df.loc[0, desc_col]).strip().lower()
            != DictionaryColumns.DESCRIPTION.lower()
        ):
            continue

        # Found an enum value and description column pair, extract them and clean up the column names
        enum_name = enum_value_col
        enum_df = (
            df[[enum_value_col, desc_col]]
            .drop(index=0)
            .dropna(axis=0, how="all")
            .reset_index(drop=True)
            .copy()
        )
        enum_df.columns = ["permissible_value", "description"]

        # Replace [empty] with blank string
        enum_df.loc[enum_df["permissible_value"] == "[empty]", "permissible_value"] = (
            EMPTY_PERMISSIBLE_VALUE
        )

        # Add the enum name to the DataFrame
        enum_df["enum"] = enum_name

        # Save the DataFrame to return from the function
        all_enums[enum_name] = enum_df

    return fields_df, all_enums


def field_name_column(df: pd.DataFrame) -> str | None:
    """Get the name of the column holding the field names in a Metadata sheet.

    Dictionary versions disagree on what to call it: most use
    DictionaryColumns.FIELD_NAME, some use DictionaryColumns.VARIABLE_NAME.

    Args:
        df (pd.DataFrame): The Metadata sheet to inspect.

    Returns:
        str | None: The column name, or None if the sheet has neither column.
    """
    for column in (DictionaryColumns.FIELD_NAME, DictionaryColumns.VARIABLE_NAME):
        if column in df.columns:
            return column
    return None


def parse_value_set_reference(value: Any) -> str | None:
    """Get the enumeration name out of a Metadata sheet DictionaryColumns.VALUE_SET cell.

    The cell references the enumeration in prose rather than naming it directly, as
    in "[See Value Sets: vs_yn]", which yields "vs_yn".

    Args:
        value (Any): The cell value. Anything that is not a string (eg. a NaN for a
            non-categorical field) yields None.

    Returns:
        str | None: The referenced enumeration name, or None if the cell does not
            contain one.
    """
    if not isinstance(value, str):
        return None
    # Everything after the colon is the enum name. A cell without a colon is not a
    # value set reference at all.
    text = value.strip("[] ")
    if ":" not in text:
        return None
    return text.split(":")[1].strip() or None


def resolve_slot_enums(
    metadata_df: pd.DataFrame,
    slot_to_enum_df: pd.DataFrame | None = None,
    detailed_enum_names: list[str] | None = None,
    log_problems: bool = True,
) -> dict[str, SlotEnum]:
    """Decide which enumeration each categorical slot uses, for every categorical slot
    in a Metadata sheet. eg:

        {
            "pretreatment": SlotEnum(base="vs_yn", name="vs_yn[pretreatment]"),
            "sample_matrix": SlotEnum(base="vs_sample_matrix", name="vs_sample_matrix"),
            ...
        }

    A NWSS data dictionary names the enumeration for a field in two places, and they
    can disagree:

    - the Metadata sheet's DictionaryColumns.VALUE_SET column, as a reference such as
      "[See Value Sets: vs_yn]"
    - the "Value Sets" sheet's DictionaryColumns.FIELD to DictionaryColumns.VALUE_SET_NAME
      mapping, supplied here as slot_to_enum_df

    **The Metadata sheet wins.** It is the more complete of the two — fields missing
    from the "Value Sets" sheet mapping are common, the reverse is not — and in the one
    documented instance of the two disagreeing (the ntc_amplify defect, see the NWSS
    manual fixes in the documentation) the Metadata sheet held the correct name. A
    disagreement is a defect in the published dictionary, so it is logged.

    This is the only place the decision is made. Generating the enumerations and
    generating the slot ranges that refer to them both go through here, so a range
    cannot end up naming an enumeration that was generated under the other sheet's name.

    Args:
        metadata_df (pd.DataFrame): The Metadata sheet extracted from a NWSS data
            dictionary. May be one table's worth of rows rather than the whole sheet.
        slot_to_enum_df (pd.DataFrame | None, optional): The DictionaryColumns.FIELD to
            DictionaryColumns.VALUE_SET_NAME mapping from the "Value Sets" sheet, as
            returned by parse_enums_sheet, with the columns SlotToEnumColumns.SLOT and
            SlotToEnumColumns.ENUM. Used only where the Metadata sheet does not name an
            enumeration. Defaults to None.
        detailed_enum_names (list[str] | None, optional): Enumerations that should be
            given a detailed, per-slot name (eg. "vs_yne[stormwater_input]") rather than
            being shared between every slot that uses them. Defaults to None.
        log_problems (bool, optional): If True then log an error for a categorical slot
            with no enumeration, and for a slot whose two sources disagree. Set False
            when calling from a step that is not the one responsible for reporting them,
            so that a problem is not logged twice per run. Defaults to True.

    Returns:
        dict[str, SlotEnum]: The enumeration for each categorical slot, keyed by slot
            name. A categorical slot with no enumeration in either source is absent.
    """
    resolved: dict[str, SlotEnum] = {}

    slot_column = field_name_column(metadata_df)
    if slot_column is None or DictionaryColumns.DATA_TYPE not in metadata_df.columns:
        return resolved

    # The "Value Sets" sheet mapping, as a plain lookup.
    sheet_enums: dict[str, str] = {}
    if slot_to_enum_df is not None and not slot_to_enum_df.empty:
        for slot, enum in zip(
            slot_to_enum_df[SlotToEnumColumns.SLOT],
            slot_to_enum_df[SlotToEnumColumns.ENUM],
        ):
            if isinstance(slot, str) and isinstance(enum, str) and enum.strip():
                sheet_enums[slot.strip()] = enum.strip()

    has_value_set_column = DictionaryColumns.VALUE_SET in metadata_df.columns
    categories = metadata_df[
        metadata_df[DictionaryColumns.DATA_TYPE] == CATEGORY_DATA_TYPE
    ]

    for _, row in categories.iterrows():
        slot_name = row[slot_column]
        if not isinstance(slot_name, str) or not slot_name.strip():
            continue
        slot_name = slot_name.strip()

        metadata_enum = (
            parse_value_set_reference(row[DictionaryColumns.VALUE_SET])
            if has_value_set_column
            else None
        )
        sheet_enum = sheet_enums.get(slot_name)

        if (
            log_problems
            and metadata_enum is not None
            and sheet_enum is not None
            and metadata_enum != sheet_enum
        ):
            logger.error(
                f"Categorical slot {slot_name} is assigned two different enumerations by "
                f"the data dictionary: the Metadata sheet says '{metadata_enum}' and the "
                f"Value Sets sheet says '{sheet_enum}'. Using '{metadata_enum}'. This is a "
                "defect in the data dictionary and should be corrected at the source."
            )

        base = metadata_enum or sheet_enum
        if base is None:
            if log_problems:
                logger.error(f"No enumeration for categorical slot {slot_name}")
            continue

        name = (
            f"{base}[{slot_name}]"
            if detailed_enum_names and base in detailed_enum_names
            else base
        )
        resolved[slot_name] = SlotEnum(base=base, name=name)

    return resolved


def group_detailed_enums(slot_enums: dict[str, SlotEnum]) -> dict[str, list[str]]:
    """Group resolved slot enumerations by the enumeration they are copied from, for
    those that were given a detailed, per-slot name. eg:

        {
            "vs_yne" : [ "vs_yne[stormwater_input]", "vs_yne[influent_equilibrated]" ],
            ...
        }

    Args:
        slot_enums (dict[str, SlotEnum]): The resolved enumerations, as returned by
            resolve_slot_enums.

    Returns:
        dict[str, list[str]]: The detailed enumeration names to generate, keyed by the
            name of the enumeration to copy the permissible values from. Enumerations
            that were not given a detailed name are not included.
    """
    grouped: dict[str, list[str]] = {}
    for slot_enum in slot_enums.values():
        if slot_enum.name == slot_enum.base:
            continue
        names = grouped.setdefault(slot_enum.base, [])
        if slot_enum.name not in names:
            names.append(slot_enum.name)
    return grouped
