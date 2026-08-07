# Add support for a new NWSS dictionary type

## Wire up the type

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

## Expect to work on the data types

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

## Check the source file for defects

Read
[Prepare the NWSS data dictionaries](prepare-the-nwss-dictionaries.md#apply-the-manual-fixes),
which lists the manual Excel fixes the currently published files need, and check
whether the new dictionary needs its own. Misnamed and missing value sets have
been the recurring problem.

## Related

- [NWSS pipeline steps](../reference/nwss-pipeline-steps.md)
- [The NWSS data dictionaries](../explanation/the-nwss-data-dictionaries.md)
- [Debug a generated schema](debug-a-generated-schema.md)
