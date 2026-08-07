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
    odm_get_available_class_names,
    odm_get_enum_name_from_part_id,
    odm_get_header_rows,
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
    df = read_data_frame(parts_file, keep_default_na=False, na_values=[""])

    # Use only active rows (indicated in the "status" column)
    df = odm_keep_active_rows(df)

    # Get all enum names by getting the partID of categorical variables that are headers (pK, fK, or header)
    # and do not have an mmaSet. Once we have all the header rows, we get the enumeration name based on the
    # partID. We do not extract the ones with mmaSet set, since those are fully defined in the sets
    # sheet, not the parts sheet (see make_odm_ss_enums_from_sets.py).
    class_names = odm_get_available_class_names(df)
    headers_df = odm_get_header_rows(df, class_names)
    filt = headers_df["dataType"].isin(["categorical"])
    filt = filt & pd.isna(headers_df["mmaSet"])
    enum_source_names = sorted(headers_df[filt]["partID"].unique())
    enum_names = [odm_get_enum_name_from_part_id(name) for name in enum_source_names]

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
