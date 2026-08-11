"""
Create the Schemasheets for all the enumerations found in the NWSS data dictionary. The enumerations
are found in the "Value Sets" sheet of the Excel data dictionary, and should have been previously
extracted with utils.extract_sheets.

## Example

```python
from odm_linkmlgen.utils.general_utils import extract_sheets
from odm_linkmlgen.nwss.make_nwss_ss_enums import extract_enums

extract_sheets("nwss/NWSS-Data-Dictionary_v5.0.0_2023-07-10.xlsx", ["Value Sets"], "nwss/dictionary")
extract_enums("nwss/dictionary/Value Sets.csv", "nwss/schemasheets")
```
"""

import os
from pathlib import Path
from typing import Annotated

import typer

from odm_linkmlgen.nwss.nwss_utils import (
    group_detailed_enums,
    parse_enums_sheet,
    resolve_slot_enums,
)
from odm_linkmlgen.utils.general_utils import get_logger, read_data_frame
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, rich_markup_mode="rich")

MAIN_HELP = """Extract all enumerations from a NWSS Value Sets sheet and
save them to disk as Schemasheets. One Schemasheet per enum is created."""

METADATA_FILE_HELP = """The Metadata sheet extracted from a NWSS
data dictionary Excel file."""

VALUESETS_FILE_HELP = """The Value Sets sheet extracted from a NWSS
data dictionary Excel file."""

OUTPUT_DIR_HELP = """Directory to save the enum Schemasheets to. They
have the name "enum_{enum_name}.tsv"."""

DETAILED_ENUM_NAMES_HELP = """If specified, then a list of enum
names where we want to use detailed enum names. Detailed enum names are in the
format "enum_name[slot]" where "slot" is the name of the slot whose range is
the enum (ie. each time the enum is used by a slot it uses a different enum
name, eg "vs_yne[stormwater_input]")."""


# Schemasheets headers
headers = {
    "enum": "enum",
    "permissible_value": "permissible_value",
    "description": "description",
}


def extract_enums(
    metadata_file: str | Path,
    valuesets_file: str | Path,
    output_dir: str | Path,
    detailed_enum_names: list[str] | None = None,
):
    """Extract all enumerations from a NWSS Value Sets sheet and save them to disk
    as Schemasheets. One Schemasheet per enum is created.

    Args:
        metadata_file (str | Path): The Metadata sheet extracted from a NWSS
            data dictionary Excel file.
        valuesets_file (str | Path): The Value Sets sheet extracted from a NWSS
            data dictionary Excel file.
        output_dir (str | Path): Directory to save the enum Schemasheets to. They
            have the name "enum_{enum_name}.tsv".
        detailed_enum_names (list[str] | None, optional): If specified, then a list of enum
            names where we want to use detailed enum names. Detailed enum names are in
            the format "enum_name[slot]" where "slot" is the name of the slot whose range
            is the enum (ie. each time the enum is used by a slot it uses a different
            enum name, eg "vs_yne[stormwater_input]"). Defaults to None.
    """
    logger.info(f"Reading and parsing Value Sets file {valuesets_file}")
    valuesets_df = read_data_frame(valuesets_file)
    metadata_df = read_data_frame(metadata_file)

    # Parse the enums sheet, by breaking it up into multiple DataFrames. Each DataFrame
    # has the headers permissible_value, description, and enum (the enum name)
    slot_to_enum_df, all_enums = parse_enums_sheet(valuesets_df)

    # Work out which enumeration each categorical slot uses. This is the same call that
    # make_nwss_ss_classes makes when it assigns the slot ranges, which is what keeps the
    # enumerations generated here and the ranges that refer to them in agreement.
    # log_problems is off because the class extraction step reports them: it is the step
    # whose output is left broken by an unresolved enumeration.
    slot_enums = resolve_slot_enums(
        metadata_df,
        slot_to_enum_df,
        detailed_enum_names=detailed_enum_names,
        log_problems=False,
    )

    # Any enum that appears in the list detailed_enum_names will be duplicated and renamed
    # to include both the enum name and the name of the slot that uses the enum (in square brackets)
    # For example, if detailed_enum_names = ["vs_yne"], then the enum name "vs_yne" will be duplicated
    # and renamed "vs_yne[stormwater_input]", "vs_yne[ext_blank]", etc. The original enum (eg. vs_yne)
    # will be deleted, so only the detailed names exist.
    detailed_enums = group_detailed_enums(slot_enums)
    for enum_name, target_names in detailed_enums.items():
        if enum_name not in all_enums:
            # Nothing to copy the permissible values from. The slots using it keep the
            # detailed range, which make_nwss reports as an undefined range once the
            # schema has been generated.
            logger.error(
                f"Enumeration {enum_name} is used by {len(target_names)} slot(s) but is "
                "not defined in the Value Sets sheet"
            )
            continue
        enum_df = all_enums[enum_name]
        for target_name in target_names:
            cur_enum_df = enum_df.copy()
            cur_enum_df["enum"] = target_name
            all_enums[target_name] = cur_enum_df
        del all_enums[enum_name]

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for enum_name, enum_df in all_enums.items():
        output_file = os.path.join(output_dir, f"enum_{enum_name}.tsv")
        logger.info(f"Saving enum {enum_name} to {output_file}")
        save_schemasheet(enum_df, output_file, headers)


@app.command(help=MAIN_HELP)
def main(
    metadata_file: Annotated[
        Path, typer.Option(show_default=False, help=METADATA_FILE_HELP)
    ],
    valuesets_file: Annotated[
        Path, typer.Option(show_default=False, help=VALUESETS_FILE_HELP)
    ],
    output_dir: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_DIR_HELP)],
    detailed_enum_names: Annotated[
        list[str], typer.Option(show_default=False, help=DETAILED_ENUM_NAMES_HELP)
    ],
):
    """CLI entry point: extract all enumerations from a NWSS Value Sets sheet and save them
    to disk as Schemasheets, one Schemasheet per enum.

    Args:
        metadata_file (Path): The Metadata sheet extracted from a NWSS data dictionary.
        valuesets_file (Path): The Value Sets sheet extracted from a NWSS data dictionary.
        output_dir (Path): Directory to save the enum Schemasheets to.
        detailed_enum_names (list[str]): List of enum names where we want to use the
            per-field (detailed) version of the enumeration.
    """
    logger.info("Making NWSS enums...")
    extract_enums(
        metadata_file=metadata_file,
        valuesets_file=valuesets_file,
        output_dir=output_dir,
        detailed_enum_names=detailed_enum_names,
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
