"""
Create Schemasheets for all enumerations found within the ODM data dictionary sets sheet. This
does NOT include the enumerations whose values are found within the parts sheet (those can be created
with make_odm_ss_enums_from_parts.py).

## Example

```python
from odm_linkmlgen.odm.make_odm_ss_enums_from_sets import extract_sets_enums

extract_sets_enums("odm_v2/dictionary/sets.csv",
                   "odm_v2/dictionary/parts.csv",
                   "odm_v2/schemasheets/enums_sets.tsv")
```
"""

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from odm_linkmlgen.odm.odm_utils import get_dictionary_read_kwargs, odm_keep_active_rows
from odm_linkmlgen.utils.general_utils import (
    EMPTY_PERMISSIBLE_VALUE,
    get_logger,
    read_data_frame,
)
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Create Schemasheets for all enumerations found within the
ODM data dictionary sets sheet. This does NOT include the enumerations whose
values are found within the parts sheet (those can be created with
make_odm_ss_enums_from_parts.py)."""

SETS_FILE_HELP = """The full path and filename to the sets CSV sheet
extracted from the ODM data dictionary."""

PARTS_FILE_HELP = """The parts sheet (CSV) that was extracted from the ODM data
dictionary."""

OUTPUT_FILE_HELP = """The TSV file to save the Schemasheet to."""

# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
# Required schemasheets headers: "enum", "permissible_value", "description", "title"
headers = {
    "setID": "enum",
    "partID": "permissible_value",
    "label": "title",  # Comes from the parts list (NOT the sets list) after joining
    "partDesc": "description",
}

# Reverse mapping: Schemasheets header name → data column name
_headers_by_role = {v: k for k, v in headers.items()}


def get_enum_names_from_sets(df: pd.DataFrame) -> list[str]:
    """Get a list of all enumeration names that are found in the specified sets
    sheet. This does not include the enum names in the parts sheet. For enum
    names from the sets sheet use
    make_odm_ss_enums_from_parts.get_enum_names_from_parts.

    Args:
        df (pd.DataFrame): The sets sheet DataFrame.

    Returns:
        list[str]: A list of all enumeration names, sorted.
    """
    return sorted(df["setID"].unique())


def extract_sets_enums(sets_file: str, parts_file: str, output_file: str) -> list[str]:
    """Create a Schemasheet for all the enumerations found in the ODM data dictionary
    sets sheet. Note that this does not consistute all of the enums found in ODM.
    Additional enumerations that are not found in the sets sheet are extracted from the
    parts sheet by make_odm_ss_enums_from_parts.py.

    Args:
        sets_file (str): The full path and filename to the sets CSV sheet extracted from
            the ODM data dictionary.
        parts_file (str): The full path and filename to the parts CSV sheet extracted from
            the ODM data dictionary.
        output_file (str): The file to save the Schemasheet to. Should be a .tsv file.

    Returns:
        list[str]: List of all enum names extracted.
    """
    sets_df = read_data_frame(sets_file, **get_dictionary_read_kwargs(sets_file))
    parts_df = read_data_frame(parts_file, **get_dictionary_read_kwargs(parts_file))

    # Keep only active status parts
    sets_df = odm_keep_active_rows(sets_df)

    # Get the description (partDesc) and title (label) from the parts list, by joining on partID
    merge_cols = ["partDesc", "label"]
    sets_df = sets_df[[c for c in sets_df.columns if c not in merge_cols]]
    df = sets_df.merge(parts_df[["partID"] + merge_cols], on="partID", how="left")

    # Replace NAs with ""
    for k in headers:
        df.loc[pd.isna(df[k]), k] = ""

    # Drop duplicates, based on both "enum" and "permissible_value" columns
    # For the duplicates, we concatenate the multiple "title" and "description" values so that in
    # the kept duplicate we have all possible titles and descriptions included.
    # eg. If the "MyEnum" enum has multiple blank permissible_values (usually corresponding
    # to "not applicable"), then we will merge them into one. The resulting title might look
    # like "Not applicable / Not a number / Null".
    enum_col = _headers_by_role["enum"]
    permissible_value_col = _headers_by_role["permissible_value"]
    description_col = _headers_by_role["description"]
    title_col = _headers_by_role["title"]
    # Strip leading and trailing whitespace from the columns
    for k in [enum_col, description_col, title_col]:
        df[k] = df[k].str.strip()
    # Using all duplicated rows, we iterate over each of the enumerations (in enum_col)
    duplicated_rows = df.duplicated(
        subset=[enum_col, permissible_value_col], keep=False
    )
    for _, group_df in df[duplicated_rows].groupby(enum_col):
        for _, subgroup_df in group_df.groupby(permissible_value_col):
            # For the current duplicates in the enumeration, concatenate all
            # descriptions and titles so the retained row includes all descriptions and titles
            new_description = " / ".join(subgroup_df[description_col].unique())
            new_title = " / ".join(subgroup_df[title_col].unique())
            df.loc[subgroup_df.index, description_col] = new_description
            df.loc[subgroup_df.index, title_col] = new_title

    # Drop the duplicates
    df = df.drop_duplicates(subset=[enum_col, permissible_value_col], keep="first")

    # Schemasheets treats a blank permissible_value as metadata for the top-level enum rather
    # than an actual permissible value of "". We use EMPTY_PERMISSIBLE_VALUE as a sentinel here
    # and replace it with "" after schema generation in fix_schemasheets_generated_schema.
    df.loc[(df["partID"] == "") | (pd.isna(df["partID"])), "partID"] = (
        EMPTY_PERMISSIBLE_VALUE
    )

    # We now have all the permissible values for each enumeration. We also want to create a row
    # for each enumeration where no permissible value is listed. These are the rows containing
    # top-level enumeration data, ie. the enumeration's title and description, rather than
    # a permissible value title and description.
    enum_names_df = pd.DataFrame({"setID": get_enum_names_from_sets(df)})
    enum_names_df = enum_names_df.merge(
        parts_df[["partID", "label", "partDesc"]],
        left_on="setID",
        right_on="partID",
        how="left",
    )
    enum_names_df = enum_names_df.drop("partID", axis=1)
    enum_order = df["enumeration"].min() - 1
    enum_names_df["enumeration"] = enum_order
    df = pd.concat([df, enum_names_df]).reset_index(drop=True)
    df = df.sort_values(["setID", "enumeration"])
    df.loc[df["enumeration"] == enum_order, "enumeration"] = None

    # Save to disk
    logger.info(f"Saving enums from sets to '{output_file}'")
    save_schemasheet(df, output_file, headers)

    return df["setID"].unique().tolist()


@app.command(help=MAIN_HELP)
def main(
    sets_file: Annotated[Path, typer.Option(show_default=False, help=SETS_FILE_HELP)],
    parts_file: Annotated[Path, typer.Option(show_default=False, help=PARTS_FILE_HELP)],
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
):
    """CLI entry point: create a Schemasheet for all enumerations whose permissible values
    are found within the ODM sets sheet. This does NOT include the enumerations defined in
    the parts sheet (use make_odm_ss_enums_from_parts.py for those).

    Args:
        sets_file (Path): The sets sheet (CSV) that was extracted from the ODM data
            dictionary.
        parts_file (Path): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_file (Path): The TSV file to save the Schemasheet to.
    """
    logger.info("Making ODM from Sets List...")
    extract_sets_enums(
        sets_file=sets_file, parts_file=parts_file, output_file=output_file
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
