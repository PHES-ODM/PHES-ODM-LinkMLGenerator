# Generate NWSS schemas

First [prepare the dictionaries](prepare-the-nwss-dictionaries.md), including
the manual Excel fixes several of them need.

## Generate

Every dictionary option is optional, and each one you pass generates one
independent schema. Supply only the dictionaries you actually have:

```console
odm-linkmlgen-nwss \
    --output-dir "gen/nwss" \
    --reporting "path/to/reporting.xlsx" \
    --public-concentration "path/to/public_concentration.xlsx" \
    --public-metric "path/to/public_metric.xlsx"
```

| Dictionary type | CLI option |
| --- | --- |
| Main reporting | `--reporting` |
| Public concentration | `--public-concentration` |
| Public metric | `--public-metric` |
| Restricted raw | `--restricted-raw` |
| Restricted analytics | `--restricted-analytics` |

A subdirectory is created per dictionary type, so the reporting run above writes
its schema to:

```text
gen/nwss/nwss_reporting/linkml/nwss_reporting.yaml
```

## Generate just one

There is no separate command per type — pass one option:

```console
odm-linkmlgen-nwss --output-dir "gen/nwss" --reporting "path/to/reporting.xlsx"
```

## Check the result

`ERROR` lines in the log are expected and are not failures: a bad row is logged
and skipped so that it cannot abort the whole run. But they do mean the schema
is degraded, usually with an unresolved range on a categorical slot. Scan for
them:

```console
odm-linkmlgen-nwss --output-dir "gen/nwss" --reporting ... 2>&1 \
    | tee gen/nwss/generate.log
grep ERROR gen/nwss/generate.log
```

An error naming a categorical field almost always means its enumeration is
missing from the `Value Sets` sheet — check the
[manual fixes](prepare-the-nwss-dictionaries.md#apply-the-manual-fixes) first,
since the published dictionaries are the usual culprit.

## What the output looks like

Two NWSS-specific behaviours will surprise you if you are not expecting them:

- **One class, not one per table.** `make_nwss` always merges every table in the
  metadata sheet into a single class named `nwss`.
- **Per-field enumerations.** `vs_yne` and `vs_yn` are expanded into one
  enumeration per field that uses them — `vs_yne[stormwater_input]`, and so on.

Both are deliberate; the reasoning is in
[The NWSS data dictionaries](../explanation/the-nwss-data-dictionaries.md).

## Related

- [NWSS pipeline steps](../reference/nwss-pipeline-steps.md)
- [Add support for a new NWSS dictionary type](add-an-nwss-dictionary-type.md)
