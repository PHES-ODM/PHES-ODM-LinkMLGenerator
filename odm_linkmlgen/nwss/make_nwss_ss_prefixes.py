# %%
"""
Creates the Schemasheets prefixes table, which defines all prefixes used by a NWSS schema.
There are multiple types of NWSS schemas, defined by the dictionary_type parameter to
make_prefixes.

## Example

```python
from odm_linkmlgen.nwss.make_nwss_ss_prefixes import make_prefixes

make_prefixes("odm_v2/schemasheets/prefixes.tsv", dictionary_type="reporting")
```
"""

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

# The full prefixes schemasheet: Column names and values
data = {
    "prefix": "nwss_{dictionary_type}",
    "prefix_reference": "https://onto.phes-odm.org/nwss/{dictionary_type}/",
}


def make_prefixes(output_file: str, dictionary_type: str):
    """Make the prefixes Schemasheet for NWSS, with the specified dictionary_type. This sheet contains all the
    CURIE prefixes used by the dictionary.

    Args:
        output_file (str): The .tsv file to save the prefixes Schemasheet to.
        dictionary_type (str): The dictionary type for this NWSS prefixes file. NWSS has multiple formats,
            dictionary_type identifies the format. (can be "public_concentration", "public_metric", "reporting",
            "restricted_analytics", or "restricted_raw")
    """
    cur_data = data.copy()
    for k, v in cur_data.items():
        cur_data[k] = v.format(dictionary_type=dictionary_type)
    save_schemasheet(cur_data, output_file)


if __name__ == "__main__":
    if "get_ipython" in globals():
        opts = {
            "output_file": "../../gen/nwss_reporting/schemasheets/prefixes.tsv",
            "dictionary_type": "reporting",
        }

        logger.info(f"Making NWSS Prefixes for {opts['dictionary_type']}...")

        make_prefixes(**opts)

        logger.info("Finished!")
