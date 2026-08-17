# How it works

Background and design reasoning. You do not need this page to use the
generator, but it is what makes the rest of the project make sense.

## LinkML

[LinkML](https://linkml.io/) (Linked Data Modeling Language) is an open standard
for describing data schemas. A LinkML schema is a YAML file that defines:

- **classes** — equivalent to tables in ODM and NWSS
- **slots** — equivalent to columns or fields
- **enumerations** — named sets of permissible values
- **ranges** — the type of a slot: a built-in type (`string`, `integer`,
  `float`, …), an enumeration, or another class, which is how foreign keys are
  expressed

Constraints such as `required`, `pattern` (a regular expression),
`minimum_value`, and `maximum_value` are attached to slots.

**A single schema file is the final product of this repository.** That is worth
stating plainly, because it bounds the project's scope: the generator does not
validate data, convert data, or produce documentation. It produces one YAML
file, and the LinkML ecosystem — `linkml-validate`, `gen-json-schema`,
`gen-doc`, `gen-python`, and the rest — does everything downstream. Anything a
LinkML tool already does is deliberately not this project's job.

### Two LinkML details that show up everywhere

**`tree_root`** — the one class that acts as the entry point to a data file.
Both pipelines generate a `Container` class marked as the tree root, holding one
multivalued slot per table. So a data file is a set of named tables, each
holding a list of rows.

**`slot_usage`** — a per-class override of a slot. This one explains a lot about
what the generated schemas look like. Because the same slot name — `siteID`, say
— can appear in several ODM tables with different constraints, most of the
generated detail lands in `slot_usage` on the class rather than on the top-level
slot definition. If you go looking for a slot's real range in `slots:` and find
almost nothing there, that is why.

## Schemasheets

[LinkML Schemasheets](https://github.com/linkml/schemasheets) generates a LinkML
schema from a set of spreadsheet-style TSV files. Each TSV describes part of the
schema, and Schemasheets merges them all into one YAML file.

A Schemasheets TSV has two header rows. The first is an ordinary column header,
which can be named anything — in practice, whatever the source dictionary called
the column. The second starts with `>` and maps each column onto an element of
the LinkML metamodel. Any column mapped to `ignore` is dropped:

```text
partID      label       partDesc        dataType
> slot      title       description     range
siteID      Site ID     The site ID     string
```

That is the whole idea. The `>` row is the adapter between "whatever this
spreadsheet happens to call things" and "what LinkML calls things".

Schemasheets can do rather more than the above — a `vmap:` in a further header
row remaps cell values, for instance, which is how the bundled ODM v1 sheets
turn `Primary Key` into a LinkML `identifier`.

## Where this project fits

This project **never writes those TSVs by hand**.

Well — with one exception. ODM v1's Schemasheets are hand-written and bundled at
`odm_linkmlgen/data/odm_v1/schemasheets/`, which is why generating the v1 schema
needs no Excel file and runs only the final stage.

For everything else, the generator converts the source Excel dictionaries into
Schemasheets TSVs, which is what nearly all the code in `odm_linkmlgen/` does.
The `>` header row is added by
`odm_linkmlgen.utils.schemasheets_utils.add_schemasheets_header`, and each
extraction module declares its own column-to-LinkML mapping in a module-level
`headers` dictionary.

So the project's actual job is narrower than "generate a LinkML schema". It is:

> Read an irregular Excel data dictionary, and write out a set of regular TSV
> files that Schemasheets can understand.

### Why not generate the YAML directly?

The generator could construct a `SchemaDefinition` in memory and serialise it,
skipping Schemasheets entirely. Going via TSVs buys two things:

- **An inspectable intermediate.** The TSVs are a flat, greppable,
  diffable representation of what the generator understood the dictionary to
  say, sitting exactly at the boundary between dataset-specific interpretation
  and generic schema construction. When a schema is wrong, that boundary is
  where you want to look.
- **Someone else maintains the schema construction.** Mapping spreadsheet
  columns onto the LinkML metamodel is a solved problem with an upstream
  maintainer.

The cost is that Schemasheets' limitations become this project's limitations,
which is what [post-processing](#post-processing-workarounds) is for.

## The three-stage pipeline

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

For what each individual step does, see the
[pipeline steps reference](../reference/pipeline-steps.md).

### Stage 1 — extract

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

### Stage 2 — transform

A set of small modules each read the CSVs and write Schemasheets TSVs. There is
one module per *kind* of output — classes, enumerations, the container class,
prefixes, and schema metadata.

**This is where all the dataset-specific knowledge lives**, and consequently
where nearly every bug lives. The
[troubleshooting guide](../how-to/troubleshooting.md#a-generated-schema-is-wrong)
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
generator passes it — `--detailed-enum-names` is empty by default, but
`make_nwss` always passes `vs_yne` and `vs_yn`. The CLIs exist for debugging, not
as the pipeline's configuration surface.

### Stage 3 — generate

`schemasheets_utils.make_linkml_schema_from_schemasheets` runs Schemasheets over
every `.tsv` in the directory and returns a `SchemaDefinition`. It then calls
`fix_schemasheets_generated_schema` to correct known Schemasheets shortcomings,
and the ODM pipeline applies one further post-processing step
(`add_missingness_set`) before the YAML is written. Both are covered
[below](#post-processing-workarounds).

The word **every** in "every `.tsv` in the directory" has a consequence worth
knowing. The final stage does not consume a known list of files; it globs. So a
stale TSV left behind by a previous run — from a renamed output, say — will be
silently picked up and merged into the schema. This is why the pipelines begin by
calling `clear_dirs`, and why a partial re-run (which does not) can produce a
schema containing something you thought you had deleted.

### Why the intermediate files are kept

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

### Why errors are logged and skipped, not raised

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

### Why the two pipelines are not shared

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
| Classes | One per table | All tables merged into one `nwss` class by default |
| Extra post-processing | `add_missingness_set` | None |
| Schemas per run | One | One per dictionary type supplied |

## Post-processing workarounds

Going via Schemasheets means inheriting Schemasheets' limitations. Three things
are therefore corrected *after* generation, working directly on the
`SchemaDefinition` rather than on the TSVs.

Two of them matter because each has a **matching convention earlier in the
pipeline**. If you only know about one half, the other half looks like a bug.

`schemasheets_utils.fix_schemasheets_generated_schema` runs as part of
`make_linkml_schema_from_schemasheets`, so both pipelines get the first three
fixes below.

### Empty permissible values

Both dictionaries need genuinely empty permissible values — an enumeration where
`""` is a legitimate choice, used for "not applicable" and similar.

Schemasheets cannot express this. It treats a blank `permissible_value` cell as
**metadata for the enumeration itself** rather than as a permissible value equal
to `""`. That behaviour is relied on elsewhere: it is exactly how the extraction
modules attach an enumeration's own title and description, by writing a row with
no permissible value.

So the two meanings collide, and the pipeline splits them apart by convention:

1. The extraction modules write the sentinel
   `general_utils.EMPTY_PERMISSIBLE_VALUE` — the literal string `<empty>` — where
   a genuinely empty permissible value is meant.
2. A truly blank cell keeps its Schemasheets meaning: enumeration-level metadata.
3. Post-processing replaces every `<empty>` with `""`.

NWSS sources spell this `[empty]` in the `Value Sets` sheet, which the NWSS
extraction converts to the `<empty>` sentinel on the way through.

!!! warning "The symptom"

    A `permissible_value` of `<empty>` surviving into the final YAML means step 3
    did not run, or ran before that value was added. The sentinel is never
    supposed to be visible in the output.

### Numeric bounds as strings

Schemasheets emits `minimum_value` and `maximum_value` as **strings**, which
breaks downstream LinkML tools — the validator among them, which is one of the
main things anyone wants to do with these schemas.

Post-processing converts them to `int` or `float`.

!!! warning "The symptom"

    A `minimum_value` still quoted as a string in the final YAML.

### Comma-separated multi-range strings

The same function also splits a comma-separated `range` string into a list, for
slots that accept more than one range. This is a convenience for the extraction
modules, which can write multiple ranges into one cell rather than needing a
Schemasheets construct for it.

### Missingness sets (ODM only)

`odm_utils.add_missingness_set` is applied by the ODM pipeline after
`make_linkml_schema_from_schemasheets`, and has no NWSS equivalent.

Some ODM slots must accept a missingness enumeration — `genMissingnessSet`,
`nrNAMissingnessSet` — **in addition to** their normal range, so a value can be
reported as missing for a documented reason. The parts sheet records this in its
`missingnessSet` column.

No Schemasheets column expresses "add this range as well", so it cannot be done
in stage 2 at all. For every slot usage whose part has a `missingnessSet`, that
enumeration is added to the slot's ranges afterwards.

A slot that ends up with more than one range is written as LinkML **`any_of`**
rather than a single `range` — see `odm_utils.set_range_of_slot`.

!!! warning "The symptom"

    A missing `any_of` where a missingness set was expected.

This is also why an ODM slot may have **no `range` key at all**, and why
`schema_utils.get_ranges_of_slot` exists: it unpacks both shapes, where reading
`.range` directly would return `None` for exactly the slots that are most
interesting. Prefer it in any code consuming these schemas.

### Why not fix Schemasheets instead?

For the numeric bounds, upstream is the right place, and a fix there would let
that workaround be deleted. The empty-permissible-value collision is more
awkward: blank-cell-means-enumeration-metadata is deliberate Schemasheets
behaviour that this project depends on, so there is no fix that does not need
*some* sentinel convention on one side or the other.
