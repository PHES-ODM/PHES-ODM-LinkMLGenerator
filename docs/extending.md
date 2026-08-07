# Extending the generator

Adding a new ODM version or a new NWSS dictionary type. Both are routine; the
work is almost always in the data types and the enumeration names, not in the
pipeline.

## Add support for a new ODM version

Schema-level metadata is templated on the version string, so a new version
usually needs **no code changes at all**:

- `make_odm_ss_schema._data` produces `ODMv{version}` and
  `https://onto.phes-odm.org/odm/v{version}`
- `make_odm_ss_prefixes._data` produces the `odmv{version}` prefix

### The procedure

1. **Obtain the dictionary** and save it as `v{n} ODM dictionary.xlsx` under
   `odm_linkmlgen/data/odm_v{n}/`. Excel dictionaries are git-ignored, so it
   stays local to your checkout. Read
   [Prepare the dictionary](index.md#prepare-the-dictionary-for-v2-and-above)
   first — the file must only ever be opened with a recent version of Excel.

2. **Generate:**

    ```console
    odm-linkmlgen-odm --version {n} \
        --dictionary-file "odm_linkmlgen/data/odm_v{n}/v{n} ODM dictionary.xlsx" \
        --output-dir "gen/odm_v{n}"
    ```

3. **Diff the new schema against the previous version's, and account for every
   change.** This is the actual work. An unexplained difference is a bug, not a
   version difference.

### Where a new version will break

Four things go wrong, in rough order of likelihood.

**New or renamed parts sheet columns.** `extract_class` raises a `RuntimeError`
naming any column it requires but cannot find, so this one announces itself.
A column that became *optional* needs adding to `optional_keep_cols`, as
`fKAliasID` was — v2 dictionaries have no `fKAliasID` column, v3 does.

**New `dataType` values.** *This one fails silently.* An unrecognized data type
passes straight through to the range unchanged, producing a dangling range
rather than an error. Add it to `_data_types_map` in `make_odm_ss_classes`.

**Enumeration names that break the `partID` + `s` convention.** Add them to
`odm_utils._odm_enum_name_exceptions`. The symptom is a slot whose range fell
back to `string`.

**A new table.** Picked up automatically, as long as it has the `{table}`,
`{table}Required`, and `{table}Order` column trio — the generator discovers
tables by scanning for column headers ending in `Order`, and hardcodes no list
of tables. See
[The ODM data dictionary](data-dictionaries.md#discovering-the-tables).

## Add support for a new NWSS dictionary type

### Wire up the type

Add a branch in `make_nwss` for the new type, setting the metadata sheet name
and adding the type to the `dictionary_types` list, along with a new CLI option.

The schema metadata, prefixes, and output directory are all derived from the
type name, so there is nothing else to configure:

| Derived from the type name `foo` | Value |
| --- | --- |
| Output subdirectory | `{output_dir}/nwss_foo/` |
| Schema file | `linkml/nwss_foo.yaml` |
| Schema name | `NWSS_foo` |
| Schema id | `https://onto.phes-odm.org/nwss/foo` |
| Description | `National Wastewater Surveillance System (NWSS-foo)` |
| CURIE prefix | `nwss_foo` → `https://onto.phes-odm.org/nwss/foo/` |

Note the capitalisation: the schema *name* is `NWSS_foo`, while the prefix,
directory, and file name are lower-case `nwss_foo`. These are built in
`make_nwss` as `default_schema_values` and passed down, unlike the ODM
equivalents which are templated inside their own modules.

The enumerations always come from a sheet named `Value Sets`; only the metadata
sheet name varies between types.

### Expect to work on the data types

Then work through `_data_types_validation_info` in `make_nwss_ss_classes`.

NWSS data types are **free-text prose**, not a controlled vocabulary, so a new
dictionary is likely to describe types in words the regex table does not yet
match. This is the substantive part of adding a type, and the most likely place
to need attention when the CDC publishes a new dictionary version generally.

The `@TODO` comments in `_data_types_validation_info` mark patterns that are
known to be too permissive.

Recall the three tiers `_get_range_and_validation_info` works through, since
where a new type falls determines what you need to add:

1. `category` → the range is an enumeration, resolved via the `Field` →
   `Value Set Name` mapping.
2. Otherwise, match the prose against `_data_types_validation_info` for a range
   plus a validation `pattern`.
3. Failing that, a data type containing `#` characters becomes a regex by
   replacing each `#` with `[0-9]`. Anything else is copied through as the range
   unchanged — which is the silent-failure case to watch for.

### Check the source file for defects

Read the
[manual fixes](index.md#apply-the-manual-fixes) the currently published
files need, and check whether the new dictionary needs its own. Misnamed and
missing value sets have been the recurring problem.

## Related

- [Troubleshooting](troubleshooting.md) — when the result is not what you
  expected
- [Pipeline steps](reference/pipeline-steps.md)
- [The source data dictionaries](data-dictionaries.md)
