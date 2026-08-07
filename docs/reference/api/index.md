# Python API

Signatures and docstrings for every public function in `odm_linkmlgen`,
**generated from the source** — so they cannot drift from the code.

Private names (those beginning with `_`) are excluded. Several are nonetheless
worth knowing about, because they are the tables you edit when adapting the
generator to a new dictionary; they are listed in
[where to look for what](../repository-layout.md#where-to-look-for-what).

## The pages

| Page | Contents |
| --- | --- |
| [Top-level generators](generators.md) | `make_odm`, `make_odm_v1`, `make_nwss` — the three CLI entry points |
| [ODM modules](odm.md) | The ODM extraction steps and `odm_utils` |
| [NWSS modules](nwss.md) | The NWSS extraction steps and `nwss_utils` |
| [Shared utilities](utils.md) | `general_utils`, `schemasheets_utils`, `schema_utils` |

## Two things to know before reading

**Every module under `odm/` and `nwss/` is both an importable module and a
standalone CLI:**

```console
python -m odm_linkmlgen.odm.<module> --help
python -m odm_linkmlgen.nwss.<module> --help
```

Each exposes a `typer` app whose `main` command forwards to the real function.
`main` is the CLI adapter, not the API — call the underlying function. See the
[CLI reference](../cli.md) for the option names.

**Docstrings are the documentation.** The project maintains full Google-style
docstring coverage precisely because these pages are generated from it, so a
missing docstring is a hole in the published documentation. See the
[docstring conventions](../../how-to/set-up-a-development-environment.md#code-conventions).

## Related

- [Use the generator as a Python library](../../how-to/use-as-a-python-library.md)
  — worked examples
- [Re-run a single pipeline step](../../how-to/run-a-single-pipeline-step.md) — a
  Python example reproducing the whole ODM pipeline
- [Repository layout](../repository-layout.md)
