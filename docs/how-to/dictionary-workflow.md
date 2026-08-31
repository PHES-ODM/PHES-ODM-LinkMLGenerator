# Roll out a dictionary update

What to do whenever the ODM data dictionary changes — that is, whenever the
`parts` or `sets` tables change. It covers regenerating the ODM LinkML schema,
copying that schema to the repositories that need it, and regenerating the
LinkML-Map schemas that the PHES-ODM-Mapper uses.

The [final section](#5-update-phes-odm-validation) covers updating the
validation repository, which does not use the LinkML schema but does use the
`parts` and `sets` tables.

!!! tip "Step 1 is automated"

    The
    [Generate ODM Schema](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/generate-odm-schema.yaml)
    GitHub Action already does step 1 for ODM v3, and commits the result to
    [`schemas/odm_v3.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/schemas/odm_v3.yaml).
    Once the dictionary change has been merged into the PHES-ODM repository,
    take the schema from there rather than generating it yourself — see
    [Let the GitHub Action generate it](#let-the-github-action-generate-it)
    below. Steps 2 to 5 are still manual.

    The action can also be fired by the PHES-ODM repository itself, so that a
    dictionary change regenerates the schema without anyone asking — see
    [Trigger generation from another repository](trigger-from-another-repository.md).

## 1. Generate the LinkML schema

### Let the GitHub Action generate it

The **Generate ODM Schema** workflow regenerates the ODM v3 schema from the
published `ODM_parts_v3.0.0.csv` and `ODM_sets_v3.0.0.csv` tables and commits it
to `schemas/odm_v3.yaml`. It runs weekly, on any change to the generator itself,
and on demand — so as soon as the dictionary change is on the `label` branch of
[PHES-ODM/PHES-ODM](https://github.com/PHES-ODM/PHES-ODM/tree/label/dictionary-tables),
you can pick the schema up instead of generating it.

Trigger it from the
[Actions tab](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/generate-odm-schema.yaml)
with **Run workflow**, or from the command line:

```console
gh workflow run generate-odm-schema.yaml \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator
```

Two optional inputs are available:

| Input | Default | What it does |
| --- | --- | --- |
| `dictionary_ref` | `label` | The branch, tag, or commit of PHES-ODM/PHES-ODM to read the tables from. Point it at a branch to see what a proposed dictionary change would do to the schema — a run that read anything but `label` uploads the schema but does not commit it. |
| `commit` | checked | Uncheck to generate the schema and upload it as a run artifact without committing it. |

The run fails, and commits nothing, if the generator logged an `ERROR` — the
same check [step 3 of Generate the ODM schemas](generate-odm-schemas.md) asks
you to do by hand. Either way the schema and both intermediate stages are
uploaded as the run's `odm-v3-schema` artifact, so a schema you did not expect
can be inspected without a local run.

Once it has run, `schemas/odm_v3.yaml` on `main` is the schema to copy in step
2:

```console
curl -L -O \
    "https://raw.githubusercontent.com/PHES-ODM/PHES-ODM-LinkMLGenerator/main/schemas/odm_v3.yaml"
```

### Or generate it locally

Needed for ODM v2, and for a dictionary change that is not on the `label`
branch yet. Follow [Generate the ODM schemas](generate-odm-schemas.md), using
the updated `ODM_parts_v3.0.0.csv` and `ODM_sets_v3.0.0.csv` dictionary tables —
the same files the change was made to. (The `v3 ODM dictionary.xlsx` workbook can
be used instead, via `--dictionary-file`, if that is the form the update reached
you in.) The output schema is written to `gen/odm_v3/linkml/odm_v3.yaml`.

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

Copy the parts and sets tables — as `parts.csv` and `sets.csv`, which is what
the run's own `gen/odm_v3/dictionary/` directory already holds them as — to the
appropriate directory on PHES-ODM-Validation. For version 3.0.1, copy them to
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
  full, including where the published dictionary tables live
- [Continuous integration](../reference/continuous-integration.md) — the
  **Generate ODM Schema** workflow, and the other three workflows
- [Trigger generation from another repository](trigger-from-another-repository.md)
  — have the PHES-ODM repository fire step 1 itself when the tables change
- [The source data dictionaries](../reference/data-dictionaries.md) — which
  tables and columns a dictionary change can affect
- [Troubleshooting](troubleshooting.md) — when the regenerated schema is not
  what you expected
