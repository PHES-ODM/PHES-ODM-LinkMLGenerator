#%%

from pathlib import Path
import pandas as pd
import os
import argparse
from typing import Tuple, List

def convert(file: str, output_dir: str = None) -> Tuple[str, pd.DataFrame]:
    """Convert the specified file to a JSON data file. The file should be a tsv, csv, or txt
    file (txt files are treated as tab-separated).

    Args:
        file (str): The file to convert to a JSON data file.
        output_dir (str): The directory to save the converted data file to. If empty
            then save to the same location as the input file.

    Returns:
        Tuple[str, pd.DataFrame]: A tuple of (new file name, data frame). The DataFrame
            is the contents of the file with any required processing performed (eg.
            putting dates and datetimes into the correct string format) 
    """
    ext = os.path.splitext(file)[1].lower()
    if ext in [".tsv", ".txt"]:
        sep = "\t"
    else:
        sep = ","

    if not output_dir:
        output_dir = os.path.dirname(file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    output_file = "%s.json" % os.path.splitext(os.path.basename(file))[0]
    output_file = Path(output_dir) / output_file
    
    print(f"Creating {output_file} from {file}")
    df = pd.read_csv(file, sep=sep)
    
    for col in df.columns:
        if df[col].dtype != object:
            continue
        try:
            # First try to parse a date without time, then convert back to a string
            # recognizable by linkml as a date
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
        except Exception:
            try:
                # Try to prase a date with time in ISO8601 format, then convert back to a string
                # recognizable by linkml as a datetime
                df[col] = pd.to_datetime(df[col], format="ISO8601", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            except Exception:
                ...
        
        # Convert bools (True/False) to strings ('true'/'false')
        for col in df.columns:
            if df[col].dtype == bool:
                df[col] = df[col].astype(str)
                df.loc[df[col] == "True", col] = "true"
                df.loc[df[col] == "False", col] = "false"
    
    df.to_json(output_file, orient="records")
    return output_file, df

def convert_directory(directory: str, output_dir: str = None) -> List[Tuple[str, pd.DataFrame]]:
    """Convert all files with extension tsv, txt or csv to JSON data files. txt files are
    treated as tab-separated.

    Args:
        directory (str): Convert all tsv, txt, and csv files in this directory.
        output_dir (str): Output directory to save the convert data files to. If empty
            then save to the same directory as the input files.

    Returns:
        List[Tuple[str, pd.DataFrame]]: List of tuples of (file name, data frame), where the
            file names are the output files and the data frames are the DataFrames used to
            create the output file. The DataFrames are loaded from the input files with
            some additional cleaning.
    """
    dfs = []
    for f in os.listdir(directory):
        if os.path.splitext(f)[1].lower() in [ ".tsv", ".txt", ".csv" ]:
            output_file, df = convert(Path(directory) / f, output_dir=output_dir)
            dfs.append([output_file, df])
    return dfs

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            # directory = Path("../../odm_v2_data/csv")
            # directory = Path("../../odm_v1_data/centreau_qc/csv")
            # file = ""
            output_dir = Path("../../odm_v2_data/json")
            # output_dir = Path("../../odm_v1_data/centreau_qc/json")
            directory = None
            # file = Path("../../odm_v1_data/centreau_qc/csv/Site.csv")
            file = Path("../../odm_v2_data/csv/addresses_b.csv")
            # output_dir = ""
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--directory", type=str, help="Convert all csv, txt, and tsv files in this directory to JSON data files. txt files are treated as tab-separated", required=False)
        args.add_argument("--file", type=str, help="Convert this file to a JSON data file. Must be a csv, txt, or tsv file. txt files are treated as tab separated", required=False)
        args.add_argument("--output_dir", type=str, help="Save results to this directory. If empty then use the same directory as the input files.", required=False)
        opts = args.parse_args()
        
    if opts.file:
        convert(opts.file, output_dir=opts.output_dir)
    if opts.directory:
        convert_directory(opts.directory, output_dir=opts.output_dir)

    print("Finished!")
