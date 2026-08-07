# Explanation

Background and design reasoning. These pages are for understanding *why* the
project is shaped the way it is — they are not instructions, and you do not need
to read them to use the generator.

If you want to get something done, go to the
[how-to guides](../how-to/index.md). If you want to look something up, go to
[reference](../reference/index.md).

## The concepts

- **[LinkML and Schemasheets](linkml-and-schemasheets.md)** — what the two
  technologies are, the handful of LinkML features this project leans on, and
  what a Schemasheets TSV actually is. Start here; the other pages assume this
  vocabulary.

## The design

- **[How the pipeline is designed](pipeline-design.md)** — why there are three
  stages, why the intermediate files are kept on disk, why every step is
  independently runnable, and why the two dataset pipelines share almost no
  code.

- **[Post-processing workarounds](post-processing-workarounds.md)** — two
  Schemasheets limitations that are corrected after generation, and the
  conventions earlier in the pipeline that exist to support them.

## The source data

The two source dictionaries are irregular in different ways, and most of the
project's complexity is a response to that.

- **[The ODM data dictionary](the-odm-data-dictionary.md)** — how one flat
  "parts" sheet encodes tables, columns, keys, and enumerations through
  relationships between columns rather than an explicit kind.

- **[The NWSS data dictionaries](the-nwss-data-dictionaries.md)** — flat
  metadata sheets with implicit table boundaries, enumerations laid out
  side-by-side, free-text data types, and why enumerations get split per field.
