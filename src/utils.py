"""
Utility functions for ODM and LinkML.
"""

from pathlib import Path
import pandas as pd
import os
import yaml
from glob import glob
from typing import Union, List, Optional, Any
import logging
import sys

from schemasheets.schemamaker import SchemaMaker
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.linkml_model import SlotDefinition
from linkml_runtime.utils.schema_as_dict import schema_as_dict

class Columns:
    SOURCE_TABLE: str = "_sourceTable"
    SOURCE_LOCATION: str = "_sourceLocation"
    SOURCE_VARIABLE: str = "_sourceVariable"
    SOURCE_CATEGORY: str = "_sourceCategory"
    SOURCE_ENUM_NAME: str = "_sourceEnumName"
    
class VariableLocations:
    VARIABLE_CATEGORIES: str = "variableCategories"
    TABLE: str = "Tables"
    VARIABLES: str = "variables"

EMPTY_PERMISSIBLE_VALUE = "<empty>"

def get_logger(name: str, level: Optional[str] = logging.INFO) -> logging.Logger:
    handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    logging.basicConfig(
        handlers=handlers,
        format="%(levelname)s %(asctime)s %(filename)s:%(lineno)d: %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S"
        )

    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger

logger = get_logger(__name__)

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
        logger.info(f"Cleaning directory {d}")
        if os.path.isdir(d):
            for f in os.listdir(d):
                file = Path(d) / f
                if os.path.splitext(file)[1].lower() in extensions:
                    os.remove(file)

def make_linkml_schema(schemasheets_dir: Union[str, Path], output_schema: Union[str, Path]) -> SchemaDefinition:
    """Create a LinkML schema from all the Schemasheets definition files in the
    specified directory.

    Args:
        schemasheets_dir (str): The directory containing all the Schemasheets definition
            files. All .tsv files are used.
        output_schema (str): The YAML file to save the LinkML schema to.

    Returns:
        SchemaDefinition: The generated schema.
    """
    logger.info(f"Making LinkML schema at '{output_schema}' from Schemasheets files in '{schemasheets_dir}'")
    sm = SchemaMaker(use_attributes=False,
                        unique_slots=False,
                        gsheet_id=None,
                        default_name=None,
                        table_config_path=None)
    input_sheets = glob(str(Path(schemasheets_dir) / "*.tsv"))
    schema = sm.create_schema(input_sheets)
    schema = sm.repair_schema(schema)
    fix_schemasheets_generated_schema(schema)
    schema_dict = schema_as_dict(schema)

    if os.path.dirname(output_schema):
        os.makedirs(os.path.dirname(output_schema), exist_ok=True)
    with open(output_schema, "w") as f:
        f.write(yaml.dump(schema_dict, sort_keys=False))
    logger.info(f"LinkML schema saved to '{output_schema}'")
    
    return schema

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
    try:
        logger.info(f"Extracting {'all sheets' if sheets is None else sheets} from file {os.path.basename(file)}...")
        dfs = pd.read_excel(file, sheet_name = sheets)
    except ValueError as e:
        logger.info(f"Could not read sheets {sheets} from {os.path.basename(file)}, trying again")
        dfs = pd.read_excel(file, sheet_name = None)
        dfs = { k: v for k, v in dfs.items() if k in sheets }
        missing = list(set(sheets) - set(dfs.keys()))
        logger.info(f"Loaded all sheets except for {missing}")

    # Save all extracted sheets to disk
    for sheet_name, df in dfs.items():
        output_file = Path(output_dir) / f"{sheet_name}.csv"
        logger.info(f"Saving sheet {sheet_name} to {output_file}")
        df.to_csv(output_file, index=False)

def choose_ignore_case_value(val: str, allowable_values: List[str], lowercase_allowable_values: Optional[List[str]] = None, return_same_if_missing: Optional[bool]=True) -> str:
    """Convert a value to match the capitalization of the same value in allowable_values.

    Args:
        val (str): The value to change the capitalization of.
        allowable_values (List[str]): A list of all allowable values that val may take on. If val matches
            any of these values (ignoring case), then we use the matching value in allowable_values.
        lowercase_allowable_values (Optional[List[str]], optional): All values in allowable_values but in
            lowercase. This is optional, if not specified then we will calculate this ourselves. Specifying
            this is simply to improve performance, so if this function is called many times we can calculate
            lowercase_allowable_values once outside of this function then pass it in for each call. 
            Defaults to None.
        return_same_if_missing (Optional[bool], optional): If True and val is not found in 
            allowable_values (ignoring case)/lowercase_allowable_values then val is returned unchanged. If
            False and val is not found the None is returned. Defaults to True.

    Returns:
        str: The value with the correct capitalization. If a match is not found in allowable_values then
            the value is returned unchanged.
    """
    if not isinstance(val, str):
        return val

    # Calculate lowercase_allowable_values if required
    if lowercase_allowable_values is None:
        lowercase_allowable_values = [v.lower() for v in allowable_values]

    # Find the match in allowable_values and return it
    lower_val = val.lower()
    if lower_val in lowercase_allowable_values:
        return allowable_values[lowercase_allowable_values.index(lower_val)]
    if return_same_if_missing:
        return val
    
    return None

def fix_schemasheets_generated_schema(schema: SchemaDefinition):
    """Do some fixing up of a Schemasheets-generated schema (generated by SchemaMaker). This is
    to account for errors or deficiencies in Schemasheets, and should hopefully in the long-term
    be eliminated. This includes:
    
    - Converting minimum_value and maximum_value for slots to numbers (Schemasheets makes them
    strings, which causes problems by downstream LinkML tools).
    - Replacing any permissible_value equal to EMPTY_PERMISSIBLE_VALUE with "". Schemasheets
    treats a blank permissible_value in a Schemasheets row as info for the top-level enum,
    rather than for a permissible value of the enum equal to "".

    Args:
        schema (SchemaDefinition): The schema
    """
    # Replace any permissible_value equal to EMPTY_PERMISSIBLE_VALUE to be blank.
    # Schemasheets uses a blank permissible_value to represent a row for the top-level
    # enum (ie. descriptions and titles associated with the enum) rather than a permissible
    # value of an enum. This makes it impossible to create a blank permissible value (eg.
    # for values representing not-applicable, NA, etc). To work around this, we've defined
    # an empty permissible value tag of EMPTY_PERMISSIBLE_VALUE that we replace with "" here.
    for enum_definition in schema.enums.values():
        if EMPTY_PERMISSIBLE_VALUE in enum_definition.permissible_values:
            enum_definition.permissible_values = { ("" if k == EMPTY_PERMISSIBLE_VALUE else k) : v for k, v in enum_definition.permissible_values.items() }
            
    # Schemasheets improperly sets minimum_value and maximum_value as strings, which can cause
    # problems downstream such as with the LinkML validator. We convert them to floats or integers
    # here.
    def _make_number(key: str, slot_definition: SlotDefinition):
        val = slot_definition[key]
        if pd.isna(val):
            return
        try:
            float_val = float(val)
            val = int(float_val) if float_val == int(float_val) else float_val
        except:
            logger.warning(f"Unrecognized {key}: {val} of type {type(val)}, using None")
            val = None
        slot_definition[key] = val
    for class_definition in schema.classes.values():
        for slot_definition in class_definition.slot_usage.values():
            _make_number("minimum_value", slot_definition)
            _make_number("maximum_value", slot_definition)