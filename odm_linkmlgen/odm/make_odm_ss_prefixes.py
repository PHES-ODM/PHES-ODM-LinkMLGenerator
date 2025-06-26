# %%
"""
Creates the Schemasheets prefixes table, which defines all prefixes used by the ODM schema.

## Example

```python
from make_odm_ss_prefixes import make_prefixes

make_prefixes("odm_v2/schemasheets/prefixes.tsv")
```
"""

import argparse

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

# The full prefixes schemasheet: Column names and values
_data = {
    "prefix": "odmv{version}",
    "prefix_reference": "https://onto.phes-odm.org/odm/v{version}/",
}


def get_prefixes_data(version: str) -> dict:
    """Get the prefixes metadata (for schemasheets), using the specified version.

    Args:
        version (str): The version (eg. "2", "3")

    Returns:
        dict: The metadata to use for schemasheets.
    """
    d = {}
    for k, v in _data.items():
        if isinstance(v, str):
            v = v.format(version=version)
        d[k] = v
    return d


def make_prefixes(version: str, output_file: str):
    """Make the prefixes Schemasheet for ODM. This sheet contains all the CURIE prefixes
    used by the dictionary.

    Args:
        version (str): The ODM version number (eg. "2", "3").
        output_file (str): The .tsv file to save the prefixes Schemasheet to.
    """
    save_schemasheet(get_prefixes_data(version), output_file)


if __name__ == "__main__":
    if "get_ipython" in globals():

        class opts:
            output_file = "../../gen/odm_v2/schemasheets/prefixes.tsv"
    else:
        args = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        args.add_argument(
            "--version",
            type=str,
            help='The version of ODM that the LinkML schema is for (eg. "2", "3")',
            required=True,
        )
        args.add_argument(
            "--output_file",
            type=str,
            help="The TSV file to save the Schemasheets prefixes file to",
            required=True,
        )
        opts = args.parse_args()

    logger.info(f"Making ODM v{opts.version} Prefixes...")

    make_prefixes(opts.version, opts.output_file)

    logger.info("Finished!")
