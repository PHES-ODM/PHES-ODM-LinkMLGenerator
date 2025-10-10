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

from typing import Annotated
from pathlib import Path
import typer

from odm_linkmlgen.utils.general_utils import get_logger
from odm_linkmlgen.utils.schemasheets_utils import save_schemasheet

logger = get_logger(__name__)

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich"
)

MAIN_HELP = """Make the prefixes Schemasheet for NWSS, with the specified
--dictionary-type. This sheet contains all the CURIE prefixes used by the
dictionary."""

OUTPUT_FILE_HELP = """The .tsv file to save the prefixes Schemasheet to."""

DICTIONARY_TYPE_HELP = """The dictionary type for this NWSS prefixes file. NWSS has
multiple formats, dictionary_type identifies the format. (can be
"public_concentration", "public_metric", "reporting", "restricted_analytics",
or "restricted_raw")"""


# The full prefixes schemasheet: Column names and values
data = {
    "prefix": "nwss_{dictionary_type}",
    "prefix_reference": "https://onto.phes-odm.org/nwss/{dictionary_type}/",
}


def make_prefixes(output_file: Path, dictionary_type: str):
    """Make the prefixes Schemasheet for NWSS, with the specified dictionary_type. This sheet contains all the
    CURIE prefixes used by the dictionary.

    Args:
        output_file (Path): The .tsv file to save the prefixes Schemasheet to.
        dictionary_type (str): The dictionary type for this NWSS prefixes file. NWSS has multiple formats,
            dictionary_type identifies the format. (can be "public_concentration", "public_metric", "reporting",
            "restricted_analytics", or "restricted_raw")
    """
    cur_data = data.copy()
    for k, v in cur_data.items():
        cur_data[k] = v.format(dictionary_type=dictionary_type)
    save_schemasheet(cur_data, output_file)

@app.command(help=MAIN_HELP)
def main(
    output_file: Annotated[Path, typer.Option(show_default=False, help=OUTPUT_FILE_HELP)], 
    dictionary_type: Annotated[str, typer.Option(show_default=False, help=DICTIONARY_TYPE_HELP)]
):
    logger.info(f"Making NWSS Prefixes for {dictionary_type}...")
    make_prefixes(
        output_file=output_file,
        dictionary_type=dictionary_type
    )
    logger.info("Finished!")


if __name__ == "__main__":
    app()
