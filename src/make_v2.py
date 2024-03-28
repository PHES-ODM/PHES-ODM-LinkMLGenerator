#%%
"""
Make the ODMv2 LinkML schema.

Be sure that excel_file points to the ODM v2 data dictionary.

@TODO:
- collNumPer has minValue "1:1". Currently this is converted to NA. Should use pattern ^[1-9][0-9]*\\.[1-9][0-9]*$
- relationshipID: Has partType equal to "sampleRelSet, protocolRelSet": Is found in both sampleRelationships and protocolRelationships tables
- origin: Is categorical, but no origins set (maybe should have mmaSet equal to originSet?)
"""

from pathlib import Path
import argparse
from typing import Union

from utils import clear_dirs, extract_sheets, make_linkml_schema, get_logger
from odm_v2.make_v2_ss_classes import extract_all_classes
from odm_v2.make_v2_ss_enums_from_parts import extract_parts_enums
from odm_v2.make_v2_ss_enums_from_sets import extract_sets_enums
from odm_v2.make_v2_ss_prefixes import make_prefixes
from odm_v2.make_v2_ss_schema import make_schema
from odm_v2.make_v2_ss_container import extract_container_class

logger = get_logger(__name__)

def make_v2(dictionary_file: Union[str, Path], output_dir: Union[str, Path]):
    # Some paths
    output_dir = Path(output_dir)
    dictionary_dir = output_dir / "dictionary"
    schemasheets_dir = output_dir / "schemasheets"
    linkml_dir = output_dir / "linkml"
    parts_file = dictionary_dir / "parts.csv"
    sets_file = dictionary_dir / "sets.csv"

    # Clean up the output directories (ie. delete old csv, tsv, and yaml files)
    clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

    # Extract the parts and sets sheets from the Excel ODM v2 data dictionary file
    extract_sheets(dictionary_file, ["parts", "sets"], dictionary_dir)

    # Extract all classes from the parts sheet (and save as a schemasheet)
    extract_all_classes(parts_file, schemasheets_dir)

    # Extract the Container class, which is the top-level LinkML class containing all
    # the tables.
    extract_container_class(schemasheets_dir / "container.tsv")

    # Extract all enums from the sets sheet (and save as a schemasheet)
    extract_sets_enums(sets_file, parts_file, schemasheets_dir / "enums_sets.tsv")

    # Extract all enums from the parts sheet (except for the mmaSet enums, which were extracted
    # above by extract_sets_enums) (and save as a schemasheet)
    extract_parts_enums(parts_file, schemasheets_dir / "enums_parts.tsv")

    # Make the prefixes schemasheet
    make_prefixes(schemasheets_dir / "prefixes.tsv")

    # Make the schema definition schemasheet
    make_schema(schemasheets_dir / "schema.tsv")

    # Run Schemasheets to make the final LinkML schema
    make_linkml_schema(schemasheets_dir, linkml_dir / "odm_v2.yaml")

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            dictionary_file = "../odm_v2/v2 ODM dictionary.xlsx"
            output_dir = "../odm_v2"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--dictionary_file", type=str, help="The Excel ODM v2 data dictionary file", required=True)
        args.add_argument("--output_dir", type=str, help="Directory to save all results to", required=True)
        opts = args.parse_args()

    make_v2(dictionary_file=opts.dictionary_file, output_dir=opts.output_dir)

    logger.info("Finished!")