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

import pandas as pd
from typing import List, Annotated
import typer
from pathlib import Path

from odm_linkmlgen.utils.general_utils import (
    get_logger,
    read_data_frame,
    EMPTY_PERMISSIBLE_VALUE,
)
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet
from odm_linkmlgen.odm.odm_utils import odm_keep_active_rows

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
    "partLabel": "title",  # Comes from the parts list (NOT the sets list) after joining
    "partDesc": "description",
}

# Reverse mapping: Schemasheets header name → data column name
_headers_by_role = {v: k for k, v in headers.items()}


def extract_sets_enums(sets_file: str, parts_file: str, output_file: str) -> List[str]:
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
        List[str]: List of all enum names extracted.
    """
    df = read_data_frame(sets_file, keep_default_na=False, na_values=[""])
    parts_df = read_data_frame(parts_file, keep_default_na=False, na_values=[""])

    # Keep only active status parts
    df = odm_keep_active_rows(df)

    # Get the description (partDesc) and title (partLabel) from the parts list, by joining on partID
    df = df.merge(
        parts_df[["partID", "partDesc", "partLabel"]], on="partID", how="left"
    )

    # Replace NAs with ""
    for k in headers.keys():
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
    enum_names_df = pd.DataFrame({"setID": list(df["setID"].unique())})
    enum_names_df = enum_names_df.merge(
        parts_df[["partID", "partLabel", "partDesc"]],
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
    logger.info("Making ODM from Sets List...")
    extract_sets_enums(
        sets_file=sets_file, parts_file=parts_file, output_file=output_file
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
