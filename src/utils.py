"""
Utility functions for ODM v2 Schema Generator.
"""

from pathlib import Path
import pandas as pd
import os
import yaml
from glob import glob
from typing import Union, Any, List, Optional

from schemasheets.schemamaker import SchemaMaker
from linkml_runtime.utils.schema_as_dict import schema_as_dict

# All known table names in ODM v2 (in LinkML they are called classes).
class_names = [
    "protocolSteps",
    "protocolRelationships",
    "measures",
    "measureSets",
    "datasets",
    "sites",
    "samples",
    "addresses",
    "contacts",
    "organizations",
    "instruments",
    "polygons",
    "languages",
    "translations",
    "parts",
    "sets",
    "qualityReports",
    "sampleRelationships",
    "protocols",
    "countries",
    "zones",
    "wideNames",
]

# In the ODM v2 data dictionary, in the parts sheet, each table (eg. samples, sites, measures) has
# a column with the same name as the table. If a row has any of the following _header_tags in that
# column, then the partID for that row is a column header in the ODM v2 table.
_header_tags = [
    "header",   # Regular header
    "fK",       # Foreign key
    "pK",       # Primary key
]

# Enumerations specified in the parts list (that are NOT in the sets list) are identified by rows that
# have "categorical" as the "dataType" and that have an empty "mmaSet" column. The names for
# the enumerations for these rows are created by adding an "s" to the end of the "partID". However, some
# enumeration names do not follow this pattern. The exceptions are listed below, with the "partID" as the 
# key and the corresponding enumeration name as the value.
_enum_name_exceptions = {
    "aggragationScale" : "aggregationScales",        # TYPO! Should be aggregationScale / Only in parts table
    "class" : "classes",                             # Add "es" instead of "s"
    "dataTypes" : "dataTypes",                       # No change
    "measure" : "measurements",                      # Not sure?
    "missingnessSets" : "missingnessSets",           # No change
    "partType" : "partType",                         # Not sure?
    "qualityFlag" : "qualityIndicators",
    "specimenSets" : "specimenSets",                 # No change
}

def get_header_rows(df: pd.DataFrame, tables: Union[str, List[str]]) -> pd.DataFrame:
    """Retrieve all rows in the DataFrame that correspond to a column in any of the specified
    ODM v2 tables.
    
    This corresponds to rows that are either a primary key, a foreign key, or a header in any
    of the tables. Note that to determine if a row is a column, the DataFrame df must
    have a column with the same name as the table.

    Args:
        df (pd.DataFrame): The DataFrame to retrieve the rows from.
        tables (Union[str, List[str]]): The table name(s) to retrieve the rows for. For each
            table name a column with that name must be present in df.

    Returns:
        pd.DataFrame: df filtered to only include the rows that specify a column in at least
            one of the tables. A copy of the DataFrame is made.
    """
    if isinstance(tables, str):
        tables = [tables]
    lower_header_tags = [h.lower() for h in _header_tags]
    lower_df = df[tables].map(lambda x: x.lower() if isinstance(x, str) else x)
    is_header = lower_df[tables].isin(lower_header_tags)
    is_header = is_header.sum(axis=1)
    return df[is_header > 0].copy()

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

def keep_active_rows(df: pd.DataFrame, status_column: str = "status", keep_status: Union[Any, List[Any]] = "active") -> pd.DataFrame:
    """Keep only rows that have an "active" status. Status is specified in a single column in the
    DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to filter, retrieving only active rows.
        status_column (str, optional): The column name that contains each row's status. Defaults to "status".
        keep_status (Union[Any, List[Any]], optional): The string(s) that indicate an active status. Defaults to "active".

    Returns:
        pd.DataFrame: df filtered to only have active status rows. A copy of the DataFrame is made before
            returning.
    """
    if not isinstance(keep_status, (list, tuple)):
        keep_status = [keep_status]
    keep_filt = df[status_column].str.strip().isin(keep_status)
    df = df[keep_filt]
    return df.copy()

def save_data_frame(df: pd.DataFrame, output_file: str, strip: bool = True):
    """Save a Pandas DataFrame to disk as a TSV or CSV, using the correct separator for the
    file extension.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_file (str): The output file to save to. If the extension is ".tsv" then tab
            delimeters are used. Any other extension will have comma delimeters.
        strip (bool): If True then strip leading and trailing whitespace from all string values
            in the DataFrame. (Defaults to True)
    """
    if strip:
        df = strip_whitespace(df)
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, sep="\t" if os.path.splitext(output_file)[1] in [".tsv"] else ",")
    
def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all strings in the DataFrame.
    """
    return df.map(lambda x: x.strip() if isinstance(x, str) else x)

def get_enum_name_from_part_id(part_id: str) -> str:
    """Get the enumeration name for the specified part ID.

    Args:
        part_id (str): The partID to get the enumeration name for. This is typically equal
            to the partID with a trailing "s", but there are some exceptions.

    Returns:
        str: The enumeration name (for the partID)
    """
    if part_id in _enum_name_exceptions.keys():
        name = _enum_name_exceptions[part_id]
    else:
        name = f"{part_id}s"
    return name

def clean_dirs(dirs: Union[str, List[str]], extensions: Union[str, List[str]] = [".tsv", ".csv", ".yaml"]):
    """Remove all TSV, CSV, and YAML files in all the specified directories.

    Args:
        dirs (Union[str, List[str]]): One or more directories to clean.
        extensions (Union[str, List[str]]): One or more extensions. All files with these
            extensions found in the directories are deleted. These are case-insensitive and
            should be prefixed by a dot.
            (Defaults to [".tsv", ".csv", ".yaml"])
    """
    if isinstance(extensions, str):
        extensions = [extensions]
    extensions = [e.lower() for e in extensions]
    if isinstance(dirs, str):
        dirs = [dirs]
    for d in dirs:
        print(f"Cleaning directory {d}")
        if os.path.isdir(d):
            for f in os.listdir(d):
                file = Path(d) / f
                if os.path.splitext(file)[1].lower() in extensions:
                    os.remove(file)

def make_linkml_schema(schemasheets_dir: str, output_schema: str):
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

def extract_sheets(file: str, sheets: List[str], output_dir: Optional[str] = None):
    """Extract the specified sheets from Excel file and save them as separate CSV files.

    Args:
        file (str): The Excel file to extract sheets from.
        sheets (List[str]): The sheets to extract. If None or empty then all sheets are
            extracted.
        output_dir (Optional[str], optional): The output directory to save the extracted sheets to.
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
