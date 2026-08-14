# Output layout

Every generator writes up to three subdirectories inside the `--output-dir` you
give it, one per pipeline stage:

```text
<output_dir>/
├── dictionary/     # Stage 1: intermediate CSVs extracted from the source Excel file
├── schemasheets/   # Stage 2: intermediate TSVs (the input to Schemasheets)
└── linkml/         # Stage 3: the final LinkML YAML schema
```

The `dictionary/` and `schemasheets/` files are intermediate build artefacts.
They are kept on disk deliberately — see
[why the intermediate files are kept](../explanation/how-it-works.md#why-the-intermediate-files-are-kept)
and [Troubleshooting](../how-to/troubleshooting.md#a-generated-schema-is-wrong).

All three directories are cleared of `.csv`, `.tsv`, and `.yaml` files by
`clear_dirs` at the start of a full run. A
[partial re-run](../how-to/python-api.md#re-run-a-single-step) does not clear
anything.

## ODM v2+

For `--output-dir gen/odm_v3 --version 3`:

```text
gen/odm_v3/
├── dictionary/
│   ├── parts.csv
│   └── sets.csv
├── schemasheets/
│   ├── class_{class_name}.tsv    # One per ODM table
│   ├── enums_sets.tsv            # All enums defined in the sets sheet
│   ├── enums_parts.tsv           # All enums defined in the parts sheet
│   ├── container.tsv
│   ├── prefixes.tsv
│   └── schema.tsv
└── linkml/
    └── odm_v3.yaml
```

Note the asymmetry in how enumerations are grouped: **one TSV per class**, but
**one TSV per enumeration source sheet**, holding every enumeration from it.

## ODM v1

ODM v1 produces only the schema. Its Schemasheets are read in place from
`odm_linkmlgen/data/odm_v1/schemasheets/` and are not copied:

```text
gen/odm_v1/
└── linkml/
    └── odm_v1.yaml
```

## NWSS

`make_nwss` creates **a subdirectory per dictionary type**, each with its own
full set of three stage directories. For
`--output-dir gen/nwss --reporting ...`:

```text
gen/nwss/
└── nwss_reporting/
    ├── dictionary/
    │   ├── metadata.csv          # The metadata sheet, whatever it was named
    │   └── enums.csv             # The "Value Sets" sheet
    ├── schemasheets/
    │   ├── classes_nwss.tsv      # Single merged class (single_table=True)
    │   ├── enum_{enum_name}.tsv  # One per enumeration
    │   ├── container.tsv
    │   ├── prefixes.tsv
    │   └── schema.tsv
    └── linkml/
        └── nwss_reporting.yaml
```

Two things to note:

- The `dictionary/` CSV names are **fixed** at `metadata.csv` and `enums.csv`,
  even though the source sheet names vary by dictionary type. This is what keeps
  the later steps dictionary-type agnostic.
- There is normally **one** `classes_*.tsv`, named `classes_nwss.tsv`, because
  `make_nwss` always merges every table into a single class. Running the step by
  hand without `--single-table` produces one per table instead.

Enumeration file names include the per-field expansion where it applies, so you
will see `enum_vs_yne[stormwater_input].tsv` and similar rather than a single
`enum_vs_yne.tsv`.

## Related

- [Repository layout](repository-layout.md) — where the source files live
- [Pipeline steps](pipeline-steps.md) — what writes each of these files
