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
from utils import add_schemasheets_header, save_data_frame

# The full prefixes schemasheet: Column names and values
data = {
    "prefix" : "odmv2",
    "prefix_reference" : "https://onto.phes-odm.org/odmv2/",
}

def make_prefixes(output_file: str):
    """Make the prefixes Schemasheet for ODM v2. This sheet contains all the CURIE prefixes
    used by the dictionary.

    Args:
        output_file (str): The .tsv file to save the prefixes Schemasheet to.
    """
    df = pd.DataFrame(data, columns = data.keys(), index = [0])
    df = add_schemasheets_header(df, {k:k for k in data.keys()})

    print(f"Saving prefixes to '{output_file}'")
    save_data_frame(df, output_file)

if __name__ == "__main__":
    if "get_ipython" in globals():
        class opts:
            output_file = "../odm_v2/schemasheets/prefixes.tsv"
    else:
        args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args.add_argument("--output_file", type=str, help="The file (tsv or csv) to save the Schemasheets prefixes file to", required=True)
        opts = args.parse_args()

    print("Making ODM v2 Prefixes...")
        
    make_prefixes(opts.output_file)

    print("Finished!")