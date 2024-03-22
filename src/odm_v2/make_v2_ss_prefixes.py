#%%
"""
Creates the Schemasheets prefixes table, which defines all prefixes used by the ODM v2 schema.

## Example

```python
from make_v2_ss_prefixes import make_prefixes

make_prefixes("odm_v2/schemasheets/prefixes.tsv")
```
"""

import pandas as pd
import argparse

from utils import save_schemasheet, get_logger

logger = get_logger(__name__)

# The full prefixes schemasheet: Column names and values
data = {
    "prefix" : "odmv2",
    "prefix_reference" : "https://onto.phes-odm.org/odm/v2/",
}

def make_prefixes(output_file: str):
    """Make the prefixes Schemasheet for ODM v2. This sheet contains all the CURIE prefixes
    used by the dictionary.

    Args:
        output_file (str): The .tsv file to save the prefixes Schemasheet to.
    """
    save_schemasheet(data, output_file)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            output_file = "../../odm_v2/schemasheets/prefixes.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--output_file", type=str, help="The TSV file to save the Schemasheets prefixes file to", required=True)
        opts = args.parse_args()

    logger.info("Making ODM v2 Prefixes...")
        
    make_prefixes(opts.output_file)

    logger.info("Finished!")