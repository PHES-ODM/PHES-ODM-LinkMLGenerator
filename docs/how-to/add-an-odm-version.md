# Add support for a new ODM version

Schema-level metadata is templated on the version string, so a new version
usually needs **no code changes at all**:

- `make_odm_ss_schema._data` produces `ODMv{version}` and
  `https://onto.phes-odm.org/odm/v{version}`
- `make_odm_ss_prefixes._data` produces the `odmv{version}` prefix

## The procedure

1. **Obtain the dictionary** and save it as `v{n} ODM dictionary.xlsx` under
   `odm_linkmlgen/data/odm_v{n}/`. Excel dictionaries are git-ignored, so it
   stays local to your checkout. Read
   [Prepare the ODM data dictionary](prepare-the-odm-dictionary.md) first — the
   file must only ever be opened with a recent version of Excel.

2. **Generate:**

    ```console
    odm-linkmlgen-odm --version {n} \
        --dictionary-file "odm_linkmlgen/data/odm_v{n}/v{n} ODM dictionary.xlsx" \
        --output-dir "gen/odm_v{n}"
    ```

3. **Diff the new schema against the previous version's, and account for every
   change.** This is the actual work. An unexplained difference is a bug, not a
   version difference.

## Where a new version will break

Four things go wrong, in rough order of likelihood.

### New or renamed parts sheet columns

`extract_class` raises a `RuntimeError` naming any column it requires but cannot
find, so this one announces itself.

A column that became *optional* needs adding to `optional_keep_cols`, as
`fKAliasID` was — v2 dictionaries have no `fKAliasID` column, v3 does.

### New `dataType` values

**This one fails silently.** An unrecognized data type passes straight through
to the range unchanged, producing a dangling range rather than an error. Add it
to `_data_types_map` in `make_odm_ss_classes`.

### Enumeration names that break the `partID` + `s` convention

Add them to `odm_utils._odm_enum_name_exceptions`. The symptom is a slot whose
range fell back to `string`.

### A new table

Picked up automatically, as long as it has the `{table}`, `{table}Required`, and
`{table}Order` column trio — the generator discovers tables by scanning for
column headers ending in `Order`, and hardcodes no list of tables. See
[The ODM data dictionary](../explanation/the-odm-data-dictionary.md).

## Related

- [Debug a generated schema](debug-a-generated-schema.md)
- [ODM pipeline steps](../reference/odm-pipeline-steps.md)
