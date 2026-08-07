# LinkML and Schemasheets

This project sits between two existing technologies. Understanding what each one
does makes the rest of the design obvious.

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

Schemasheets does the rest. This is why the pipeline is shaped the way it is —
see [How the pipeline is designed](pipeline-design.md).

## Why not generate the YAML directly?

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
which is what [post-processing](post-processing-workarounds.md) is for.
