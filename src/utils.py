"""
Utility functions for ODM LinkML Schema Generator.
"""

from pathlib import Path
import pandas as pd
import os
import yaml
from glob import glob
from typing import Union, List, Optional

from schemasheets.schemamaker import SchemaMaker
from linkml_runtime.utils.schema_as_dict import schema_as_dict

def add_schemasheets_header(df: pd.DataFrame, headers: dict) -> pd.DataFrame:
    """Insert Schemasheets header line. This is the line that starts with ">" and is
    inserted as the first row (immediately below the existing Pands column names).

    Args:
        df (pd.DataFrame): The DataFrame to add the Schemasheets headers to.
        headers (dict): The Schemasheets headers to add. The keys are names for
            the existing df column names. The values are the Schemasheet
            headers to add in the matching column. Note that ">" will be added
            automatically to the first header. Any DataFrame column not found
            in this dictionary will receive the Schemasheet header "ignore".

    Returns:
        pd.DataFrame: The DataFrame with the new Schemasheet header as the first row.
            A copy of the DataFrame is made.
    """
    df = df.copy().reset_index(drop=True)
    df.loc[-1] = [""] * len(df.columns)
    df.index = df.index + 1
    df = df.sort_index()
    for idx, col in enumerate(df.columns):
        new_header = headers.get(col, None) or "ignore"
        if idx == 0:
            new_header = f"> {new_header}"
        df.loc[0, col] = new_header
    return df

def order_columns(df: pd.DataFrame, column_order: List[str]) -> pd.DataFrame:
    """Order the columns in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to order the columns of.
        column_order (List[str]): The order of the columns. Any column in df not found in this
            list are put at the end.

    Returns:
        pd.DataFrame: A copy of the DataFrame ordered by column.
    """
    columns = list(column_order) + [c for c in df.columns if c not in column_order]
    return df[columns].copy()

def save_data_frame(df: pd.DataFrame, output_file: Union[str, Path], strip: bool = True, **kwargs):
    """Save a Pandas DataFrame to disk as a TSV or CSV, using the correct separator for the
    file extension.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_file (Union[str, Path]): The output file to save to. If the extension is ".tsv" or ".txt" then tab
            delimeters are used. Any other extension will have comma delimeters.
        strip (bool): If True then strip leading and trailing whitespace from all string values
            in the DataFrame. (Defaults to True)
        **kwargs: Additional key-word arguments to pass to df.to_csv.
    """
    if strip:
        df = strip_whitespace(df)
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, sep="\t" if os.path.splitext(output_file)[1] in [".tsv", ".txt"] else ",", **kwargs)
    
def read_data_frame(file: str, **kwargs) -> pd.DataFrame:
    """Read a Pandas DataFrom from disk, using the correct separator based on the file extension.

    Args:
        file (str): The file to read. If the extension is ".tsv" or ".txt" then tab
            delimeters are used. Any other extension will have comma delimeters.
        **kwargs: Additional key-word arguments passed to pd.read_csv.

    Returns:
        pd.DataFrame: The DataFrame loaded from the file.
    """
    ext = os.path.splitext(file)[1].lower()
    if ext in [".tsv", ".txt"]:
        sep = "\t"
    else:
        sep = ","
    df = pd.read_csv(file, sep=sep, **kwargs)
    return df

def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all strings in the DataFrame.
    """
    return df.map(lambda x: x.strip() if isinstance(x, str) else x)

def clear_dirs(dirs: Union[Union[str, Path], List[Union[str, Path]]], extensions: Union[str, List[str]] = [".tsv", ".csv", ".yaml"]):
    """Remove all TSV, CSV, and YAML files in all the specified directories.

    Args:
        dirs (Union[Union[str, Path], List[Union[str, Path]]]): One or more directories to clean.
        extensions (Union[str, List[str]]): One or more extensions. All files with these
            extensions found in the directories are deleted. These are case-insensitive and
            should be prefixed by a dot.
            (Defaults to [".tsv", ".csv", ".yaml"])
    """
    if isinstance(extensions, str):
        extensions = [extensions]
    extensions = [e.lower() for e in extensions]
    if isinstance(dirs, (str, Path)):
        dirs = [dirs]
    for d in dirs:
        print(f"Cleaning directory {d}")
        if os.path.isdir(d):
            for f in os.listdir(d):
                file = Path(d) / f
                if os.path.splitext(file)[1].lower() in extensions:
                    os.remove(file)

def make_linkml_schema(schemasheets_dir: Union[str, Path], output_schema: Union[str, Path]):
    """Create a LinkML schema from all the Schemasheets definition files in the
    specified directory.

    Args:
        schemasheets_dir (str): The directory containing all the Schemasheets definition
            files. All .tsv files are used.
        output_schema (str): The YAML file to save the LinkML schema to.
    """
    print(f"Making LinkML schema at '{output_schema}' from Schemasheets files in '{schemasheets_dir}'")
    sm = SchemaMaker(use_attributes=False,
                        unique_slots=False,
                        gsheet_id=None,
                        default_name=None,
                        table_config_path=None)
    input_sheets = glob(str(Path(schemasheets_dir) / "*.tsv"))
    schema = sm.create_schema(input_sheets)
    schema = sm.repair_schema(schema)
    schema_dict = schema_as_dict(schema)

    if os.path.dirname(output_schema):
        os.makedirs(os.path.dirname(output_schema), exist_ok=True)
    with open(output_schema, "w") as f:
        f.write(yaml.dump(schema_dict, sort_keys=False))
    print(f"LinkML schema saved to '{output_schema}'")

def extract_sheets(file: Union[str, Path], sheets: List[str], output_dir: Optional[Union[str, Path]] = None):
    """Extract the specified sheets from Excel file and save them as separate CSV files.

    Args:
        file (Union[str, Path]): The Excel file to extract sheets from.
        sheets (List[str]): The sheets to extract. If None or empty then all sheets are
            extracted.
        output_dir (Optional[Union[str, Path]], optional): The output directory to save the extracted sheets to.
            If empty then the sheets are saved to the same directory as the input file. The file names
            will be the sheet name (as specified in sheets) with a csv extension. Defaults to None.
    """
    # Create output directory
    if not output_dir:
        output_dir = os.path.dirname(file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load all sheets from Excel file.
    if isinstance(sheets, str):
        sheets = [sheets]
    if sheets is None or len(sheets) == 0:
        sheets = None
    print(f"Extracting {'all sheets' if sheets is None else sheets} from file '{os.path.basename(file)}'...")
    dfs = pd.read_excel(file, sheet_name = sheets)

    # Save all extracted sheets to disk
    for sheet_name, df in dfs.items():
        output_file = Path(output_dir) / f"{sheet_name}.csv"
        print(f"Saving sheet {sheet_name} to {output_file}")
        df.to_csv(output_file, index=False)
