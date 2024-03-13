#%%
"""
Make the ODMv1 LinkML schema.
"""

from pathlib import Path

from utils import make_linkml_schema, get_logger

# The directory to save the final odm_v1.yaml LinkML schema file to
output_dir = Path("../odm_v1")
# The directory where all the manually created Schemasheets are for ODM v1
schemasheets_dir = output_dir / "schemasheets"

logger = get_logger(__name__)

# Make the schema
linkml_schema = output_dir / "linkml" / "odm_v1.yaml"
make_linkml_schema(schemasheets_dir, linkml_schema)

logger.info("Finished!")