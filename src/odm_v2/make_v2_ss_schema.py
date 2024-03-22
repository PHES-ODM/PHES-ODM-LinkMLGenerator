#%%
"""
Creates the Schemasheets schema table, which provides the top-level meta data about the ODM v2
schema, such as the id, description of the schema, and the default prefix to use.

## Example

```python
from make_v2_ss_schema import make_schema

make_schema("odm_v2/schemasheets/schema.tsv")
```
"""

import pandas as pd
import argparse

from utils import save_schemasheet, get_logger

logger = get_logger(__name__)

# The full schema metadata schemasheet: Column names and values
data = {
    "schema" : "ODMv2",
    "id" : "https://onto.phes-odm.org/odm/v2",
    "description" : "Data model for the Public Health Environmental Surveillance Open Data Model, version 2",
    "default_prefix" : "odmv2",
}

def make_schema(output_file: str):
    """Make the schema metadata Schemasheet for ODM v2. This sheet contains top-level meta data
    about the ODM v2 LinkML schema, such as the id, description, and default prefix.

    Args:
        output_file (str): The .tsv file to save the schema Schemasheet to.
    """
    save_schemasheet(data, output_file)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            output_file = "../../odm_v2/schemasheets/schema.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--output_file", type=str, help="The TSV file to save the Schemasheets schema file to", required=True)
        opts = args.parse_args()

    logger.info("Making ODM v2 Schema...")
        
    make_schema(opts.output_file)

    logger.info("Finished!")