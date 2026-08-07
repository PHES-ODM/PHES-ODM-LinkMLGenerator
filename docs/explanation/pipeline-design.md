# How the pipeline is designed

Both the ODM and NWSS generators have the same three stages:

```text
   Excel data dictionary
            │
            │  1. extract_sheets
            ▼
   dictionary/*.csv          One CSV per source sheet
            │
            │  2. the extraction modules (make_*_ss_*.py)
            ▼
   schemasheets/*.tsv        One TSV per class, per enum, plus
            │                container / prefixes / schema metadata
            │  3. make_linkml_schema_from_schemasheets
            ▼
   linkml/<name>.yaml        The final LinkML schema
```

This page explains why. For what each individual step does, see the
[ODM](../reference/odm-pipeline-steps.md) and
[NWSS](../reference/nwss-pipeline-steps.md) step references.

## Stage 1 — extract

`general_utils.extract_sheets` saves the required Excel sheets as CSV files, and
does nothing else. No interpretation happens here.

Two reasons for a stage that appears to do nothing:

- **It keeps the rest of the pipeline free of Excel-specific concerns.** Only one
  function in the project knows that `openpyxl` exists.
- **It makes every later step re-runnable in a second against a fixed input.**
  Parsing a large workbook is slow. Iterating on a transformation while
  re-parsing the source each time is the difference between a fast feedback loop
  and a slow one, and this stage is what buys the fast one.

This stage also handles NA parsing per column, which cannot be deferred. It
matters because ODM part IDs include literal values such as `NA` and `None` —
real permissible values in the data model — that pandas would otherwise read as
missing.

## Stage 2 — transform

A set of small modules each read the CSVs and write Schemasheets TSVs. There is
one module per *kind* of output — classes, enumerations, the container class,
prefixes, and schema metadata.

**This is where all the dataset-specific knowledge lives**, and consequently
where nearly every bug lives. The [debugging guide](../how-to/debug-a-generated-schema.md)
is mostly about this stage for that reason.

Two conventions hold here:

**One Schemasheets concern per module.** A module named `make_*_ss_<thing>`
produces the `<thing>` file and nothing else. Its column-to-LinkML mapping goes
in a module-level `headers` dict, so the mapping is one greppable block rather
than being scattered through the code.

**Every step is both an importable function and a standalone CLI.** Each module
exposes a `typer` app whose `main` command just forwards to the real function.
This is a deliberate design constraint rather than a convenience: keeping every
step independently runnable is what makes the pipeline debuggable, and it should
be preserved when adding a step.

Note that a step's CLI *defaults* are not necessarily what the top-level
generator passes it — `--single-table` and `--recognized-enums` both differ. The
CLIs exist for debugging, not as the pipeline's configuration surface.

## Stage 3 — generate

`schemasheets_utils.make_linkml_schema_from_schemasheets` runs Schemasheets over
every `.tsv` in the directory and returns a `SchemaDefinition`. It then calls
`fix_schemasheets_generated_schema` to correct known Schemasheets shortcomings,
and the ODM pipeline applies one further post-processing step
(`add_missingness_set`) before the YAML is written. Both are covered in
[post-processing workarounds](post-processing-workarounds.md).

The word **every** in "every `.tsv` in the directory" has a consequence worth
knowing. The final stage does not consume a known list of files; it globs. So a
stale TSV left behind by a previous run — from a renamed output, say — will be
silently picked up and merged into the schema. This is why the pipelines begin by
calling `clear_dirs`, and why a partial re-run (which does not) can produce a
schema containing something you thought you had deleted.

## Why the intermediate files are kept

The `dictionary/` and `schemasheets/` files are build artefacts and could be
written to a temporary directory. They are kept on disk because they are the most
useful thing to look at when a generated schema is not what you expected:

- If `dictionary/*.csv` is wrong, the problem is Excel parsing — almost always NA
  handling.
- If `schemasheets/*.tsv` is wrong, the problem is in the extraction modules,
  which is where it usually is.
- If both are right and the YAML is wrong, the problem is Schemasheets or
  post-processing.

That three-way split turns "the schema is wrong" into a specific question in
about a minute, which is the entire return on keeping the files.

## Why errors are logged and skipped, not raised

Errors in the source dictionary are usually logged and skipped rather than
raised, so a single bad row does not abort a whole generation run.
`_get_range_and_validation_info` in the NWSS pipeline is the reference example.

The reasoning is that the source dictionaries are not fully under this project's
control. The published NWSS files contain outright defects, and the ODM
dictionary changes between versions in ways the generator has not seen. A
pipeline that halted on the first surprise would be unusable against real inputs;
one that produces a mostly-correct schema plus a log of what it could not
understand is workable.

The cost is real, and you should know it: **a run that "succeeded" can still have
produced a degraded schema.** The characteristic symptom is a slot whose range
silently fell back to `string`, or an unrecognized data type passed through
unchanged as a dangling range. Always read the log — a clean exit code is not the
same as a clean run.

## Why the two pipelines are not shared

The ODM and NWSS pipelines have the same shape but almost no shared
dataset-specific code. This is not duplication that ought to be factored out; the
source dictionaries genuinely have little in common:

- **ODM** packs table membership, keys, and enumeration membership into
  relationships between the columns of a single parts sheet. Deciding what a row
  *is* requires looking at several other columns.
- **NWSS** lists fields per table in a flat sheet with implicit boundaries, and
  keeps enumerations in a side-by-side column layout.

An abstraction covering both would have to be general enough to express both
encodings, which in practice means it expresses neither clearly. What the two
pipelines *do* share lives in `odm_linkmlgen/utils/`: Excel and CSV I/O,
DataFrame manipulation, Schemasheets file writing, and the schema generation and
post-processing step. That is the part where the two datasets really are doing
the same thing.

Where they diverge in output as well as input:

| | ODM | NWSS |
| --- | --- | --- |
| Classes | One per table | All tables merged into one `nwss` class |
| Extra post-processing | `add_missingness_set` | None |
| Schemas per run | One | One per dictionary type supplied |
