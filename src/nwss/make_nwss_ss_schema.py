#%%
"""
Creates the Schemasheets schema table for NWSS, which provides the top-level meta data about the NWSS
schema, such as the id, description of the schema, and the default prefix to use.

## Example

```python
from make_nwss_ss_schema import make_schema

make_schema("nwss/schemasheets/schema.tsv")
```
"""

import pandas as pd
import argparse
from typing import Dict

from utils.general_utils import save_schemasheet, get_logger

logger = get_logger(__name__)

# The default schema metadata schemasheet: Column names and values
# These are updated with values from the data_values dictionary passed to make_schema.
# NWSS has multiple data dictionaries (eg. one for reporting, for metric, and for concentration)
# so the schema metadata will be different for each.
default_data = {
    # "schema" : "NWSS",
    # "id" : "https://www.cdc.gov/nwss/reporting.html",
    # "description" : "National Wastewater Surveillance System (NWSS)",
    # "default_prefix" : "nwss",
}

def make_schema(output_file: str, data_values: Dict={}):
    """Make the schema metadata Schemasheet for NWSS. This sheet contains top-level meta data
    about the NWSS LinkML schema, such as the id, description, and default prefix.

    Args:
        output_file (str): The .tsv file to save the schema Schemasheet to.
        data_values (Dict): Update the default schema data with these values when saving the schema.
            They should be key-value pairs where the key is the Schemasheets header.
    """
    use_data = default_data.copy()
    if data_values is not None:
        use_data.update(data_values)
    
    df = pd.DataFrame(use_data, columns = use_data.keys(), index = [0])
    logger.info(f"Saving schema to '{output_file}'")
    save_schemasheet(df, output_file, use_data.keys())

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            output_file = "../../gen/nwss_reporting/schemasheets/schema.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--output_file", type=str, help="The TSV file to save the Schemasheets schema file to", required=True)
        opts = args.parse_args()

    logger.info("Making NWSS Schema...")
        
    make_schema(opts.output_file)

    logger.info("Finished!")