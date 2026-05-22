"""
Utility functions for ODM and LinkML.
"""

from pathlib import Path
import pandas as pd
from pandas._libs.parsers import STR_NA_VALUES
import os
import inspect
from typing import Union, List, Optional, Any, Dict, Callable
import logging
import sys

from linkml_runtime import SchemaView

EMPTY_PERMISSIBLE_VALUE = "<empty>"

logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    format="%(levelname)s %(asctime)s %(filename)s:%(lineno)d: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str, level: Optional[int] = logging.INFO) -> logging.Logger:
    """Get the logger with the specified name. The name can be any arbitrary string, for example:

        logger = get_logger(__name__)

    Args:
        name (str): The name to give to the logger.
        level (Optional[int], optional): The logging level of the logger. Defaults to logging.INFO.

    Returns:
        logging.Logger: The logging object.
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger


logger = get_logger(__name__)


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


def save_data_frame(
    df: pd.DataFrame, output_file: Union[str, Path], strip: bool = True, **kwargs
):
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
    df.to_csv(
        output_file,
        sep="\t" if os.path.splitext(output_file)[1] in [".tsv", ".txt"] else ",",
        **kwargs,
    )


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
    """Strip whitespace from all strings in the DataFrame."""
    return df.map(lambda x: x.strip() if isinstance(x, str) else x)


def clear_dirs(
    dirs: Union[Union[str, Path], List[Union[str, Path]]],
    extensions: Union[str, List[str]] = None,
):
    """Remove all TSV, CSV, and YAML files in all the specified directories.

    Args:
        dirs (Union[Union[str, Path], List[Union[str, Path]]]): One or more directories to clean.
        extensions (Union[str, List[str]]): One or more extensions. All files with these
            extensions found in the directories are deleted. These are case-insensitive and
            should be prefixed by a dot. If None then [".tsv", ".csv", ".yaml"] is used.
            (Defaults to None)
    """
    extensions = extensions or [".tsv", ".csv", ".yaml"] 
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


def extract_sheets(
    file: Union[str, Path],
    sheets: Union[str, List[str]],
    output_dir: Optional[Union[str, Path]] = None,
    output_names: Union[str, List[str]] = None,
    na_values: Dict[str, Dict[str, Union[str, List[str]]]] = None,
    default_na_values: List[str] = STR_NA_VALUES,
    read_excel_kwargs: Dict[str, Any] = None,
):
    """Extract the specified sheets from Excel file and save them as separate CSV files.

    Args:
        file (Union[str, Path]): The Excel file to extract sheets from.
        sheets (Union[str, List[str]]): The sheets to extract. If None or empty then all sheets are
            extracted.
        output_dir (Optional[Union[str, Path]], optional): The output directory to save the extracted sheets to.
            If empty then the sheets are saved to the same directory as the input file. The file names
            will be the sheet name (as specified in sheets) with a csv extension. Defaults to None.
        output_names (Union[str, List[str]], optional): The names of the files to save, each index matching
            the same index in sheets. Extensions are ignored, all files will be CSV files. If None then
            the names will be the same as the sheet names in the sheets parameter.
        na_values (Dict[str, Dict[str, Union[str, List[str]]]], optional): If specified, then perform special
            parsing for NA values. The keys specify the sheet names in the Excel file. The values are dictionaries
            where the key is a column name in the sheet and the values are a list of strings that should be mapped
            to NA (empty) values. If any column is missing from na_values then default_na_values is used for the
            column. These values will override the values in read_excel_kwargs.
        default_na_values (List[str], optional): If na_values is specified, then use these string values to
            represent NA values when extracting the sheet for any columns that aren't specified in na_values.
            Defaults to pandas._libs.parsers.STR_NA_VALUES. These values will override the values in
            read_excel_kwargs.
        read_excel_kwargs (Dict[str, Any]): Dictionary of kwargs values to pass to Pandas read_excel function.
    """
    # Create output directory
    if not output_dir:
        output_dir = os.path.dirname(file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not read_excel_kwargs:
        read_excel_kwargs = {}

    read_excel_kwargs = select_func_kwargs(pd.read_excel, read_excel_kwargs)

    # Load all sheets from Excel file.
    if isinstance(sheets, str):
        sheets = [sheets]
    if isinstance(output_names, str):
        output_names = [output_names]
    if na_values is None:
        na_values = {}

    # Load all the sheet names and columns from the file. We load 0 rows for each sheet,
    # since we only need to get the sheet names and the column names. This allows us to
    # load the sheets one at a time while specifying the sheet-specific na_values.
    pre_dfs = pd.read_excel(file, sheet_name=None, nrows=0, **read_excel_kwargs)
    if sheets is None or len(sheets) == 0:
        sheets = list(pre_dfs.keys())

    # Load all sheets one at a time, using the specified na_values
    dfs = {}
    for sheet in sheets:
        if sheet not in pre_dfs.keys():
            logger.error(f"Sheet '{sheet}' does not exist in Excel file: {file}")
            continue
        pre_df = pre_dfs[sheet]

        # Prepare the kwargs for pd.read_excel
        cur_na_values = na_values.get(sheet, {})
        cur_na_values = {
            c: cur_na_values.get(c, default_na_values) for c in pre_df.columns
        }
        cur_kwargs = read_excel_kwargs.copy()
        cur_kwargs["keep_default_na"] = False
        cur_kwargs["na_values"] = cur_na_values

        df = pd.read_excel(file, sheet_name=sheet, **cur_kwargs)
        dfs[sheet] = df

    # Save all extracted sheets to disk
    for sheet_name, df in dfs.items():
        output_name = sheet_name
        if output_names is not None:
            output_name = output_names[sheets.index(sheet_name)]
            output_name = os.path.splitext(output_name)[0]
        output_file = Path(output_dir) / f"{output_name}.csv"
        logger.info(f"Saving sheet {sheet_name} to {output_file}")
        df.to_csv(output_file, index=False)


def choose_ignore_case_value(
    val: str,
    allowable_values: List[str],
    lowercase_allowable_values: Optional[List[str]] = None,
    return_same_if_missing: Optional[bool] = True,
) -> str:
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


def get_class_name_from_file_name(
    file_name: Union[str, Path], schema: Optional[SchemaView] = None
) -> str:
    """Get the LinkML class name based on a data file name. Data files are named as "class_name[...].ext".

    Args:
        file_name (Union[str, Path]): The file name to extract the class name from.
        schema (Optional[SchemaView], optional): If set, then we correct the capitalization of the class name
            based on the classes found in this schema. Defaults to None.

    Returns:
        str: The class name for the data file.
    """
    base_name = os.path.splitext(os.path.basename(file_name))[0]
    class_name = base_name.split("[")[0]
    if schema is not None:
        class_name = choose_ignore_case_value(
            class_name, list(schema.all_classes().keys())
        )
    return class_name


def expand_multi_rows(df: pd.DataFrame, columns: Union[List[str], str]) -> pd.DataFrame:
    """For all specified columns in the DataFrame df, over all rows, make duplicate rows whenever
    a column value has a semi-colon (;) in it, with each new row having the different values when
    splitting the original values by semi-colons.

    If multiple columns are specified, then the values we select when splitting all the values in all
    the columns by semi-colons match by index for each new row. If a column doesn't have enough indices
    when split by semi-colons, then the last item is selected. For example, the following table:

    | Name                       | Favorite color       | Species      |
    |----------------------------|----------------------|--------------|
    | Spatophen;Diblodex;Matimer | Pink;Periwinkle      | Homo sapien  |

    Would be expanded to:

    | Name                       | Favorite color       | Species      |
    |----------------------------|----------------------|--------------|
    | Spatophen                  | Pink                 | Homo sapien  |
    | Diblodex                   | Periwinkle           | Homo sapien  |
    | Matimer                    | Periwinkle           | Homo sapien  |

    Args:
        df (pd.DataFrame): The DataFrame to expand. A copy is made and the original left unchanged.
        columns (Union[List[str], str]): The columns to expand. We will search for SEP_TAG in all of
            these columns (in all rows).

    Returns:
        pd.DataFrame: The expanded DataFrame.
    """
    SEP_TAG = ";"

    if isinstance(columns, str):
        columns = [columns]

    # Keep rows where any of the columns have multiple values (ie. a string with SEP_TAG in it)
    # so we expand them.
    multi_df = df[
        df[columns].astype(str).map(lambda x: SEP_TAG in x).any(axis="columns")
    ].copy()

    # Split all column strings along the string SEP_TAG
    multi_df[columns] = multi_df[columns].map(
        lambda x: [x.strip() for x in x.split(SEP_TAG)] if not pd.isna(x) else [""]
    )

    if multi_df.empty:
        return df.copy()

    # Determine the maximum number of multiple values
    max_multi = int(multi_df[columns].map(lambda x: len(x)).max(axis=None))

    # Remove all original rows that had multiple values specified. We'll expand these removed
    # rows below and then readd the expanded rows to the DataFrame.
    df = df[~df.index.isin(multi_df.index)]

    def _select_element(i: int, arr: List) -> str:
        # Select element number i in arr. If i is out of bounds then select the last element.
        if len(arr) > i:
            val = arr[i]
        else:
            val = arr[-1]
        return val

    split_rows_dfs = []
    for i in range(max_multi):
        # Keep any row where at least one of the columns has i+1 or more values
        new_rows_df = multi_df[
            multi_df[columns].map(lambda x: len(x) > i).sum(axis=1) > 0
        ].copy()
        # Select the ith element
        new_rows_df[columns] = new_rows_df[columns].map(lambda x: _select_element(i, x))
        split_rows_dfs.append(new_rows_df)

    df = pd.concat([df, *split_rows_dfs]).reset_index(drop=True)

    return df


def rename_items(items: List[str], renames: Dict[str, str]) -> List[str]:
    """Rename the string items in the list according to the renames dictionary. The keys of the
    dictionary are the original names and the values are the new values to rename them to. A copy of
    items is made, the original is left unmodified.

    Args:
        items (List[str]): The list of items that is the target of the renaming.
        renames (Dict[str, str]): Dictionary specifying how to rename the values in items. The keys
            are the original item values, and the values are what to rename them to.

    Returns:
        List[str]: The renamed items. The order of the items is maintained, and a copy is
            made with the original left unchanged.
    """
    items = list(items).copy()
    for orig, target in renames.items():
        items[items.index(orig)] = target
    return items


def select_func_kwargs(func: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Only select the keyword arguments in the dictionary that are acceptable arguments
    for the function.

    Args:
        func (Callable): The function to get the keyword arguments for.
        kwargs (Dict[str, Any]): The keyword arguments to select from.

    Returns:
        Dict[str, Any]: A dictionary which is a copy of kwargs where only the keys that
            exist as arguments to the function func are present.
    """
    args, _, _, _, kwonlyargs, *_ = inspect.getfullargspec(func)
    all_args = set(list(args) + list(kwonlyargs))
    existing_keywords = all_args.intersection(set(kwargs.keys()))
    kwargs = {k: kwargs[k] for k in existing_keywords}
    return kwargs
