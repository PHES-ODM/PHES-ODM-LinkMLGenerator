# Generated schemas

The generated LinkML schemas, committed so that they can be read straight out
of this repository without running the generator.

| File | Source dictionary | Kept up to date by |
| --- | --- | --- |
| [`odm_v3.yaml`](odm_v3.yaml) | The published `ODM_parts_v3.0.0.csv` and `ODM_sets_v3.0.0.csv` tables, from the [`dictionary-tables/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/label/dictionary-tables) of the PHES-ODM repository | The [Generate ODM Schema](../.github/workflows/generate-odm-schema.yaml) workflow |

**These files are generated. Do not edit them by hand** — the next workflow run
will overwrite any manual change. A schema is wrong because the dictionary it
came from is wrong, or because the generator is; fix it there.

The raw URL for the current ODM v3 schema is:

```text
https://raw.githubusercontent.com/PHES-ODM/PHES-ODM-LinkMLGenerator/main/schemas/odm_v3.yaml
```

Every commit to a file here records, in its commit message, the PHES-ODM commit
the dictionary tables were read from, so a schema can always be traced back to
the exact tables that produced it.

Nothing else the generator writes is committed. The intermediate `dictionary/`
and `schemasheets/` stages, and the ODM v1, ODM v2, and NWSS schemas, are all
produced under the git-ignored `gen/` directory by a local run — see
[Generate the ODM schemas](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/generate-odm-schemas/).
