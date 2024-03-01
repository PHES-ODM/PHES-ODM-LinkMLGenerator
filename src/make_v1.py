#%%
"""
Make the ODMv1 LinkML schema.

Configurable paths (defaults are recommended):

- output_dir: The directory where the final odm_v1.yaml LinkML schema file
- schemasheets_dir: The directory where all the manually created Schemasheets are for ODM v1
"""

from pathlib import Path

from utils import make_linkml_schema

output_dir = Path("../odm_v1")
schemasheets_dir = output_dir / "schemasheets"

# Make the schema
linkml_schema = output_dir / "linkml" / "odm_v1.yaml"
make_linkml_schema(schemasheets_dir, linkml_schema)