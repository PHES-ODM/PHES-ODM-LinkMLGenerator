"""
Create Schemasheets for all enumerations found within the ODM data dictionary parts sheet. This
does NOT include the enumerations found within the sets sheet (those can be created with
make_odm_ss_enums_from_sets.py).

## Example

```python
from odm_linkmlgen.odm.make_odm_ss_enums_from_parts import extract_parts_enums

extract_parts_enums("odm_v2/dictionary/parts.csv", "odm_v2/schemasheets/enums_parts.tsv")
```
"""

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from odm_linkmlgen.odm.odm_utils import (
    get_dictionary_read_kwargs,
    odm_keep_active_rows,
)
from odm_linkmlgen.utils.general_utils import (
    EMPTY_PERMISSIBLE_VALUE,
    get_logger,
    read_data_frame,
)
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Create Schemasheets for all enumerations found within the ODM
data dictionary parts sheet. This does NOT include the enumerations found
within the sets sheet (those can be created with
make_odm_ss_enums_from_sets.py)."""

PARTS_FILE_HELP = """The parts sheet (CSV) that was extracted from the ODM data
dictionary."""

OUTPUT_FILE_HELP = """The TSV file to save the Schemasheet to."""

# For mapping the columns in our final DataFrame to columns recognized by Schemasheets
# Required schemasheets headers: "enum", "permissible_value", "description"
headers = {
    "partType": "enum",
    "partID": "permissible_value",
    "partDesc": "description",
    "label": "title",
}


def get_enum_names_from_parts(df: pd.DataFrame) -> list[str]:
    """Get a list of all enumeration names that are found in the specified parts
    sheet. This does not include the enum names in the sets sheet. For enum
    names from the sets sheet use
    make_odm_ss_enums_from_sets.get_enum_names_from_sets.

    Args:
        df (pd.DataFrame): The parts sheet DataFrame.

    Returns:
        list[str]: A list of all enumeration names, sorted.
    """
    return sorted(df["partType"].unique())


def extract_parts_enums(parts_file: str, output_file: str) -> list[str]:
    """Create a Schemasheet for all enumerations found in the parts sheet of the ODM
    data dictionary. This does not include any enums that are found in the sets sheet
    (see make_odm_ss_enums_from_sets.py for extracting enums from the sets sheet)/

    Args:
        parts_file (str): The full path and filename for the CSV parts sheet extracted
            from the ODM data dictionary.
        output_file (str): The TSV file to save the Schemasheet to.

    Returns:
        list[str]: List of all enum names extracted.
    """
    df = read_data_frame(parts_file, **get_dictionary_read_kwargs(parts_file))

    # Use only active rows (indicated in the "status" column)
    df = odm_keep_active_rows(df)

    # "partType" contains the enumeration names
    enum_names = get_enum_names_from_parts(df)

    # Get all rows for all enums. We only keep the columns in keep_columns.
    # Each row (or enum value) should be an "input" for at least one class.
    # "partType" matches the enum name (corresponds to a permissible value of the enum)
    # OR: "partID" matches the enum name (corresponds to the top-level enum)
    keep_columns = [
        "partType",
        "partID",
        "label",
        # "shortName",
        "partDesc",
        "partInstr",
    ]
    output_df = pd.DataFrame()
    input_df = df
    for enum_name in enum_names:
        # Get the top-level enum row (where the partID is the same as the enum_name)
        enum_toplevel_df = input_df[input_df["partID"] == enum_name][
            keep_columns
        ].copy()
        enum_toplevel_df["partID"] = ""
        enum_toplevel_df["partType"] = enum_name
        # Get all rows where the part is a member of the enumeration (by checking the partType column)
        enum_df = input_df[input_df["partType"] == enum_name][keep_columns].copy()
        enum_df.loc[
            (enum_df["partID"] == "") | (pd.isna(enum_df["partID"])), "partID"
        ] = EMPTY_PERMISSIBLE_VALUE

        # Add the top-level enum row and the enum values rows to our final DataFrame
        output_df = pd.concat([output_df, enum_toplevel_df, enum_df])

    # Save to disk
    logger.info(f"Saving enums from parts to '{output_file}'")
    save_schemasheet(output_df, output_file, headers)

    return output_df["partType"].unique().tolist()


@app.command(help=MAIN_HELP)
def main(
    parts_file: Annotated[Path, typer.Option(show_default=False, help=PARTS_FILE_HELP)],
    output_file: Annotated[
        Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)
    ],
):
    """CLI entry point: create a Schemasheet for all enumerations whose permissible values
    are found within the ODM parts sheet. This does NOT include the enumerations defined in
    the sets sheet (use make_odm_ss_enums_from_sets.py for those).

    Args:
        parts_file (Path): The parts sheet (CSV) that was extracted from the ODM data
            dictionary.
        output_file (Path): The TSV file to save the Schemasheet to.
    """
    logger.info("Making ODM Enums from Parts List...")
    extract_parts_enums(parts_file=parts_file, output_file=output_file)
    logger.info("Finished!")


if __name__ == "__main__":
    app()
