# Generated schemas

The generated LinkML schemas, committed so that they can be read straight out
of this repository without running the generator.

| File | Source dictionary | Kept up to date by |
| --- | --- | --- |
| [`odm_v3.yaml`](odm_v3.yaml) | The currently-published `ODM_parts_v<version>.csv` and `ODM_sets_v<version>.csv` tables, from the [`dictionary-tables/` directory](https://github.com/PHES-ODM/PHES-ODM/tree/main/dictionary-tables) of the PHES-ODM repository | The [Generate ODM Schema](../.github/workflows/generate-odm-schema.yaml) workflow, on a weekly schedule and on every dictionary release |

**These files are generated. Do not edit them by hand** — the next workflow run
will overwrite any manual change. A schema is wrong because the dictionary it
came from is wrong, or because the generator is; fix it there.

The raw URL for the current ODM v3 schema is:

```text
https://raw.githubusercontent.com/PHES-ODM/PHES-ODM-LinkMLGenerator/main/schemas/odm_v3.yaml
```

An archival major version — one whose tables PHES-ODM has moved out of
`dictionary-tables/` into their own folder, such as `archived V2.3 (PATCH)`
for v2.3.0 — is not covered by the schedule above, since there's no live
branch for it to track. Generate one on demand via the Generate ODM Schema
workflow's `dictionary_dir` and `odm_version` inputs (or the matching
`repository_dispatch` client_payload fields), pointed at that folder and its
major version; a human-triggered run commits the result to its own
`schemas/odm_v<version>.yaml`, alongside this file rather than overwriting it.

Every commit to a file here records, in its commit message, the PHES-ODM commit
the dictionary tables were read from, so a schema can always be traced back to
the exact tables that produced it.

Nothing else the generator writes is committed. The intermediate `dictionary/`
and `schemasheets/` stages, and the ODM v1, ODM v2, and NWSS schemas, are all
produced under the git-ignored `gen/` directory by a local run — see
[Generate the ODM schemas](https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/how-to/generate-odm-schemas/).
