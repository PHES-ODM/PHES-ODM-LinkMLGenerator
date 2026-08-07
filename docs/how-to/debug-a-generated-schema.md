# Debug a generated schema

The intermediate CSV and TSV files are the whole point of the three-stage
layout: when the final YAML is wrong, they tell you *which stage* went wrong.
Work through them in order.

## 1. Check `dictionary/*.csv`

Did the sheet extract as expected?

The usual problem here is **NA handling**: a value such as `NA`, `None`, or
`null` was read as an empty cell. These are real permissible values in the ODM,
not missing data. `extract_sheets` takes per-column `na_values` for exactly this
reason — see [step 2 of the ODM pipeline](../reference/odm-pipeline-steps.md).

## 2. Check `schemasheets/*.tsv`

**This is where nearly all bugs live.** Find the file for the class or
enumeration in question and look at the row:

- Is the `>` header row mapping the columns you expect?
- Is the `range` the enumeration name you expected, or did it silently fall back
  to `string`?

A range that fell back to `string` means the enumeration name could not be
resolved. For ODM that is usually an enumeration name that does not follow the
`partID` + `s` convention and is missing from
`odm_utils._odm_enum_name_exceptions`.

## 3. Re-run only the step you are working on

Against the CSVs already in `dictionary/`, rather than rebuilding from Excel:

```console
python -m odm_linkmlgen.odm.make_odm_ss_classes \
    --parts-file "gen/odm_v3/dictionary/parts.csv" \
    --output-dir "gen/odm_v3/schemasheets"
```

Two things to know about partial re-runs:

- **`clear_dirs` only runs at the start of a full pipeline.** A partial re-run
  leaves the other TSVs in place — which is what you want when iterating, but it
  also means a renamed output can leave an orphan TSV behind that Schemasheets
  will still pick up.
- **A step's CLI defaults are not what the top-level generator passes it.** See
  [Re-run a single pipeline step](run-a-single-pipeline-step.md).

## 4. Check the final YAML for post-processing symptoms

If the TSVs look right but the YAML does not, suspect the post-processing stage.
Three symptoms and their causes:

| Symptom in the YAML | Cause |
| --- | --- |
| A `permissible_value` of `<empty>` that was not converted to `""` | `fix_schemasheets_generated_schema` |
| A `minimum_value` or `maximum_value` still quoted as a string | `fix_schemasheets_generated_schema` |
| A missing `any_of` where a missingness set was expected | `odm_utils.add_missingness_set` |

All three are explained in
[Post-processing workarounds](../explanation/post-processing-workarounds.md).

## Diffing against a known-good schema

When changing an extraction module, the most reliable check is to regenerate and
diff, since the extraction modules and the end-to-end pipelines are not covered
by automated tests:

```console
cp gen/odm_v3/linkml/odm_v3.yaml /tmp/odm_v3.before.yaml
# ... make your change ...
odm-linkmlgen-odm --version 3 --dictionary-file ... --output-dir "gen/odm_v3"
diff /tmp/odm_v3.before.yaml gen/odm_v3/linkml/odm_v3.yaml
```

Account for every line of the diff. An unexplained change is a bug, in the old
output or the new one.

## Related

- [Output layout](../reference/output-layout.md)
- [Post-processing workarounds](../explanation/post-processing-workarounds.md)
- [Set up a development environment](set-up-a-development-environment.md)
