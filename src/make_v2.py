#%%
"""
Make the ODMv2 LinkML schema.
"""

from pathlib import Path
import argparse
from typing import Union

from linkml_runtime.linkml_model.meta import SchemaDefinition

from utils.general_utils import clear_dirs, extract_sheets, get_logger
from utils.schemasheets_utils import make_linkml_schema_from_schemasheets, save_schema_definition
from odm_v2.make_v2_ss_classes import extract_all_classes
from odm_v2.make_v2_ss_enums_from_parts import extract_parts_enums
from odm_v2.make_v2_ss_enums_from_sets import extract_sets_enums
from odm_v2.make_v2_ss_prefixes import make_prefixes
from odm_v2.make_v2_ss_schema import make_schema
from odm_v2.make_v2_ss_container import extract_container_class
from odm_v2.v2_utils import add_missingness_set

logger = get_logger(__name__)

def make_v2(dictionary_file: Union[str, Path], output_dir: Union[str, Path]) -> SchemaDefinition:
    """Generate the LinkML schema for ODM v2.

    Args:
        dictionary_file (Union[str, Path]): Location of the Excel data dictionary (parts file) for ODM v2.
        output_dir (Union[str, Path]): Location to save all output. The LinkML schema output is
            saved to "{output_dir}/linkml/odm_v2.yaml"

    Returns:
        SchemaDefinition: The generated ODM v2 LinkML schema definition.
    """
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
    extract_sheets(dictionary_file, ["parts", "sets"], dictionary_dir, na_values = { "parts" : { "partID" : "" }, "sets" : { "partID" : "" }})

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
    schema = make_linkml_schema_from_schemasheets(schemasheets_dir)

    # Add genMissingnessSet to all ranges where an enum must be paired with genMissingnessSet
    add_missingness_set(schema, dictionary_file=dictionary_file, lists_sheet = "lists")
 
    # Save the schema to disk
    save_schema_definition(schema, linkml_dir / "odm_v2.yaml")
    
    return schema

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            dictionary_file = "../gen/odm_v2/v2 ODM dictionary.xlsx"
            output_dir = "../gen/odm_v2"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--dictionary_file", type=str, help="The Excel ODM v2 data dictionary file", required=True)
        args.add_argument("--output_dir", type=str, help="Directory to save all results to", required=True)
        opts = args.parse_args()

    make_v2(dictionary_file=opts.dictionary_file, output_dir=opts.output_dir)

    logger.info("Finished!")