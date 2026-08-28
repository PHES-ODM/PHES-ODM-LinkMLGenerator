# Roll out a dictionary update

What to do whenever the ODM data dictionary changes — that is, whenever the
`parts` or `sets` sheets change. It covers regenerating the ODM LinkML schema,
copying that schema to the repositories that need it, and regenerating the
LinkML-Map schemas that the PHES-ODM-Mapper uses.

The [final section](#5-update-phes-odm-validation) covers updating the
validation repository, which does not use the LinkML schema but does use the
`parts` and `sets` sheets.

!!! note "This should eventually be automated"

    These steps should eventually be run by a GitHub Action. We may also want
    to store a single copy of the ODM v3 LinkML schema at a publicly accessible
    location, rather than a copy per repository.

## 1. Generate the LinkML schema

Follow [Generate the ODM schemas](generate-odm-schemas.md). Generating the
schema requires either the `v3 ODM dictionary.xlsx` file, or the `parts.csv`
and `sets.csv` files. The output schema is written to
`gen/odm_v3/linkml/odm_v3.yaml`.

## 2. Upload the schema to the repositories

The LinkML schema should be included at the following locations on GitHub.
Change the paths accordingly if it is the ODM v2 schema:

- [**PHES-ODM-MapGenerator**/odm_map_maker/data/odm_v3/linkml/](https://github.com/PHES-ODM/PHES-ODM-MapGenerator/tree/main/odm_map_maker/data/odm_v3/linkml)
- [**PHES-ODM-Mapper**/odm_map/data/modules/_shared/schemas/](https://github.com/PHES-ODM/PHES-ODM-Mapper/tree/main/odm_map/data/modules/_shared/schemas)
- [**PHES-ODM-Search-MCP**/odm_search_mcp/data/schemas/](https://github.com/PHES-ODM/PHES-ODM-Search-MCP/tree/main/odm_search_mcp/data/schemas)
- [**PHES-ODM-General-Skill**/skills/phes-odm-general/references/](https://github.com/PHES-ODM/PHES-ODM-General-Skill/tree/main/skills/phes-odm-general/references)
- [**PHES-ODM-QPCR-Pipeline**/schemas/](https://github.com/PHES-ODM/PHES-ODM-QPCR-Pipeline/tree/main/schemas)

## 3. Regenerate the LinkML-Map schemas

While the mapping schema files will typically not change when the ODM v3 LinkML
schema changes, it is good to regenerate them just in case. After copying the
latest ODM LinkML schema to the PHES-ODM-MapGenerator repository, follow the
instructions at
[PHES-ODM-MapGenerator](https://github.com/PHES-ODM/PHES-ODM-MapGenerator#generate-the-mappers).
You should generate the mappers for `ODM v1 → ODM v3`, `NWSS reporting → ODM
v3`, and `PHA4GE → ODM v3`. You do not need to generate them with a target of
`ODM v2`, since the same mapper files are used, and mapping to `ODM v2` should
be discouraged.

The generated LinkML-Map schemas will be saved in `gen/odm-v1-to-v3/mappers`,
`gen/nwss-reporting-to-v3/mappers`, and `gen/pha4ge-to-v3/mappers`. These
schemas are required by the PHES-ODM-Mapper repository (see below).

## 4. Copy the LinkML-Map schemas to PHES-ODM-Mapper

The LinkML-Map schemas generated in the previous section should be copied to
the PHES-ODM-Mapper repository. The schemas are all YAML files. Copy them to
the following locations (be sure to delete the previous mappers):

- `gen/odm-v1-to-v3/mappers` → [**PHES-ODM-Mapper**/odm_map/data/modules/odm-v1-to-v3/mappers/](https://github.com/PHES-ODM/PHES-ODM-Mapper/tree/main/odm_map/data/modules/odm-v1-to-v3/mappers)
- `gen/nwss-reporting-to-v3/mappers` → [**PHES-ODM-Mapper**/odm_map/data/modules/nwss-reporting-to-v3/mappers/](https://github.com/PHES-ODM/PHES-ODM-Mapper/tree/main/odm_map/data/modules/nwss-reporting-to-v3/mappers)
- `gen/pha4ge-to-v3/mappers` → [**PHES-ODM-Mapper**/odm_map/data/modules/pha4ge-to-v3/mappers/](https://github.com/PHES-ODM/PHES-ODM-Mapper/tree/main/odm_map/data/modules/pha4ge-to-v3/mappers)

## 5. Update PHES-ODM-Validation

Copy `parts.csv` and `sets.csv` to the appropriate directory on
PHES-ODM-Validation. For version 3.0.1, copy them to
[**PHES-ODM-Validation**/assets/dictionary/v3.0.1/](https://github.com/PHES-ODM/PHES-ODM-Validation/tree/main/assets/dictionary/v3.0.1).

Install the PHES-ODM-Validation library by following its
[installation instructions](https://validate-docs.phes-odm.org/#installation).

Run the `generate_assets.py` script:

```console
python3 src/odm_validation/tools/generate_assets.py
```

The output is in
[assets/validation-schemas](https://github.com/PHES-ODM/PHES-ODM-Validation/tree/main/assets/validation-schemas).
Push all the changes (eg. `schema-v3.0.1.yml`), and be sure to also push the
new `parts.csv` and `sets.csv` files.

## Related

- [Generate the ODM schemas](generate-odm-schemas.md) — the generation step in
  full, including generating from CSV instead of the workbook
- [The source data dictionaries](../reference/data-dictionaries.md) — which
  sheets and columns a dictionary change can affect
- [Troubleshooting](troubleshooting.md) — when the regenerated schema is not
  what you expected
