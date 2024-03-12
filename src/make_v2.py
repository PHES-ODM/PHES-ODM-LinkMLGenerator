#%%
"""
Make the ODMv2 LinkML schema.

@TODO:
- collNumPer has minValue "1:1". Currently this is converted to NA. Should use pattern ^[1-9][0-9]*\\.[1-9][0-9]*$

Configurable paths (defaults are recommended):

- excel_file: The full ODM v2 data dictionary (should contain a parts and sets sheet)
- output_dir: The directory to save all intermediary files and the final odm_v2.yaml LinkML schema file.
"""

from pathlib import Path

from utils import clear_dirs, extract_sheets, make_linkml_schema, get_logger
from make_v2_ss_classes import extract_all_classes
from make_v2_ss_enums_from_parts import extract_parts_enums
from make_v2_ss_enums_from_sets import extract_sets_enums
from make_v2_ss_prefixes import make_prefixes
from make_v2_ss_schema import make_schema
from make_v2_ss_container import extract_container_class

excel_file = Path("../odm_v2/v2 ODM dictionary.xlsx")
output_dir = Path("../odm_v2")

# Some paths
dictionary_dir = output_dir / "dictionary"
schemasheets_dir = output_dir / "schemasheets"
linkml_dir = output_dir / "linkml"
parts_file = dictionary_dir / "parts.csv"
sets_file = dictionary_dir / "sets.csv"

logger = get_logger(__name__)

# Clean up the output directories (ie. delete old csv, tsv, and yaml files)
clear_dirs([dictionary_dir, schemasheets_dir, linkml_dir])

# Extract the parts and sets sheets from the Excel ODM v2 data dictionary file
extract_sheets(excel_file, ["parts", "sets"], dictionary_dir)

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

logger.info("Finished!")
