#%%
"""
Creates the Schemasheets schema table, which provides the top-level meta data about the ODM
schema, such as the id, description of the schema, and the default prefix to use.

## Example

```python
from make_v2_ss_schema import make_schema

make_schema("odm_v2/schemasheets/schema.tsv")
```
"""

import pandas as pd
import argparse

from utils.general_utils import get_logger
from utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

# The full schema metadata schemasheet: Column names and values
_data = {
    "schema" : "ODMv{version}",
    "id" : "https://onto.phes-odm.org/odm/v{version}",
    "description" : "Data model for the Public Health Environmental Surveillance Open Data Model, version {version}",
    "default_prefix" : "odmv{version}",
}

def get_schema_data(version: str) -> dict:
    """Get the schema metadata (for schemasheets), using the specified version.

    Args:
        version (str): The version (eg. "2", "3")

    Returns:
        dict: The metadata to use for schemasheets.
    """
    d = {}
    for k, v in _data.items():
        if isinstance(v, str):
            v = v.format(version = version)
        d[k] = v
    return d
    

def make_schema(version: str, output_file: str):
    """Make the schema metadata Schemasheet for ODM. This sheet contains top-level meta data
    about the ODM LinkML schema, such as the id, description, and default prefix.

    Args:
        version (str): The version of ODM that the schema is for (eg. "2", "3").
        output_file (str): The .tsv file to save the schema Schemasheet to.
    """
    save_schemasheet(get_schema_data(version), output_file)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            version = "2"
            output_file = "../../gen/odm_v2/schemasheets/schema.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--version", type=str, help="The version of ODM that the LinkML schema is for (eg. \"2\", \"3\")", required=True)
        args.add_argument("--output_file", type=str, help="The TSV file to save the Schemasheets schema file to", required=True)
        opts = args.parse_args()

    logger.info(f"Making ODM v{opts.version} Schema...")
        
    make_schema(opts.version, opts.output_file)

    logger.info("Finished!")