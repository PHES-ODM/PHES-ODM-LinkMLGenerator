"""
Generate LinkML schemas for the PHES-ODM and CDC NWSS data models.

Each generator converts an Excel data dictionary into a LinkML YAML schema in
three stages: extract the required Excel sheets to CSV, convert those CSVs into
LinkML Schemasheets TSV files, then run Schemasheets to produce the final schema.

The top-level generators are:

- make_odm.make_odm: ODM v2 and above, from an ODM Excel data dictionary.
- make_odm_v1.make_odm_v1: ODM v1, from the Schemasheets files bundled in
  data/odm_v1.
- make_nwss.make_nwss: the CDC NWSS data dictionaries.

The odm and nwss subpackages hold the per-dataset conversion steps, and utils
holds the shared Excel/CSV, DataFrame, and Schemasheets helpers. See the docs
directory of the repository for details.
"""
