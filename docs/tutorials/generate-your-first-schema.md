# Generate your first schema

In this tutorial you will install the generator and produce a complete LinkML
schema for **ODM v1**, then look at what it contains.

ODM v1 is the right place to start because it needs no source Excel file: its
Schemasheets files are already bundled with the repository, so the whole thing
runs offline in a couple of seconds.

You will need Python 3.10 or newer. Check with:

```console
python3 --version
```

## Step 1 — Install the package

Clone the repository and install it into a virtual environment:

```console
git clone git@github.com:PHES-ODM/PHES-ODM-LinkMLGenerator.git
cd PHES-ODM-LinkMLGenerator
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

The last line installs the package in editable mode and registers three
commands. Confirm one of them is on your path:

```console
odm-linkmlgen-odmv1 --help
```

You should see a usage message listing `--output-dir`. If instead you get
`command not found`, the virtual environment is probably not active — re-run
`source .env/bin/activate`.

## Step 2 — Generate the schema

Run the generator, telling it where to put its output:

```console
odm-linkmlgen-odmv1 --output-dir "gen/odm_v1"
```

You will see a long stream of `INFO` lines. Most of them come from Schemasheets
and LinkML themselves and are noise — lines about a `Mismatch between
slot_name_mapping key ...` are normal and can be ignored. The two lines that
matter are the last two:

```text
INFO ... schemasheets_utils.py:84: LinkML schema saved to '.../gen/odm_v1/linkml/odm_v1.yaml'
INFO ... make_odm_v1.py:43: Finished!
```

Every module in this project logs the files it reads and writes at `INFO`, which
is what makes a failed run diagnosable.

## Step 3 — Look at what was produced

List the output directory:

```console
find gen/odm_v1 -type f
```

Exactly one file:

```text
gen/odm_v1/
└── linkml/
    └── odm_v1.yaml
```

That is all ODM v1 produces. The generator read its Schemasheets TSVs straight
out of the installed package — they are never copied into `--output-dir`. A full
ODM v2+ or NWSS run writes two more directories alongside `linkml/`, holding the
intermediate files of the earlier stages; the
[output layout reference](../reference/output-layout.md) describes them.

### The input side

Look at the Schemasheets file the generator read, in the package itself:

```console
head -3 odm_linkmlgen/data/odm_v1/schemasheets/classes.tsv
```

The **first** row is an ordinary column header, named after whatever the source
data dictionary called things. The rows beginning with `>` are what make the
file a Schemasheet: they map each column onto an element of the LinkML
metamodel. Here `tableName` becomes a LinkML `class`, `variableName` becomes a
`slot`, and `variableType` becomes its `range`. Columns mapped to `ignore` are
dropped. See
[LinkML and Schemasheets](../explanation/linkml-and-schemasheets.md) for the
full story.

These particular TSVs are written and maintained by hand, which is why ODM v1
needs no Excel file. For every other dataset the generator *builds* files like
these from a source dictionary — that is essentially the whole job.

### The output side

Now open the generated schema:

```console
less gen/odm_v1/linkml/odm_v1.yaml
```

It opens with schema-level metadata — `name: ODMv1`, an `id`, `prefixes`, and a
`default_range` — and then three sections worth finding:

- **`enums:`** — the named sets of permissible values.
- **`slots:`** — the columns. Most of the interesting detail is not here but
  under each class's `slot_usage:`, because the same slot name can appear in
  several tables with different constraints.
- **`classes:`** — one entry per ODM table, plus a `Container` class marked
  `tree_root: true`. The tree root is the entry point to a data file: it holds
  one `multivalued`, `inlined_as_list` slot per table, so an ODM data file is a
  set of named tables, each holding a list of rows. Jump to it with:

    ```console
    grep -n -B12 "tree_root" gen/odm_v1/linkml/odm_v1.yaml
    ```

## Step 4 — Do something with the schema

The schema is now an ordinary LinkML artefact, and every LinkML tool will accept
it. If you have `linkml` installed — you do, it came in with
`requirements.txt` — try converting it to JSON Schema:

```console
gen-json-schema gen/odm_v1/linkml/odm_v1.yaml > gen/odm_v1/odm_v1.schema.json
```

Or validate a data file against it:

```console
linkml-validate --schema gen/odm_v1/linkml/odm_v1.yaml your_data.yaml
```

That is the point of the project: it does not validate or convert anything
itself. It produces one schema, and the LinkML ecosystem does the rest.

## What you learned

- The generator's job is to turn a data dictionary into **one LinkML YAML file**,
  and then get out of the way — validation, conversion, and documentation are
  all done by other LinkML tools.
- It gets there via **Schemasheets TSVs**, whose `>` header rows map spreadsheet
  columns onto the LinkML metamodel.
- ODM v1 is the special case: its TSVs are written by hand and bundled with the
  package, so only the final stage runs. Every other dataset generates its TSVs
  from an Excel dictionary first.

## Next

[Generate an NWSS schema](generate-an-nwss-schema.md) runs the complete
pipeline, starting from an Excel dictionary you download yourself.
