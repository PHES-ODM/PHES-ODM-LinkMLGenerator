# Update the documentation

The documentation is built with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme, and published to
GitHub Pages by `.github/workflows/docs.yaml`.

## Build it locally

```console
pip install -r requirements-docs.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000/>. The site rebuilds as you save.

Before pushing, run the same check CI does:

```console
mkdocs build --strict
```

`--strict` turns warnings into failures — broken internal links, pages missing
from the `nav`, and mkdocstrings references that cannot be resolved. If it
passes locally it will pass in CI.

The build does **not** need the runtime dependencies (`linkml`, `pandas`, …)
installed: mkdocstrings uses [griffe](https://mkdocstrings.github.io/griffe/),
which reads the source statically rather than importing it. That is why
`requirements-docs.txt` is separate from `requirements.txt`.

## Where things go

The documentation follows the
[Divio documentation system](https://docs.divio.com/documentation-system/). The
four sections are not four ways of saying the same thing — each answers a
different question, and mixing them is what makes documentation hard to use.
Before adding a page, decide which one it belongs to:

| Section | Answers | Written for someone who is |
| --- | --- | --- |
| `docs/tutorials/` | "Teach me." | Learning, and does not yet know what to ask |
| `docs/how-to/` | "How do I …?" | Working, with a specific goal |
| `docs/explanation/` | "Why is it like this?" | Studying, trying to understand |
| `docs/reference/` | "What are the options for …?" | Looking something up mid-task |

The distinction that matters most in practice: a **tutorial** is a lesson that
must succeed if followed exactly, so it fixes every choice for the reader. A
**how-to guide** assumes competence and covers a real goal, including its
variations. If you find yourself explaining *why* in a how-to guide, that
paragraph belongs in explanation with a link to it.

Reference pages should be dry and complete. Do not put reasoning in them.

## Adding a page

1. Create the Markdown file under the appropriate `docs/` subdirectory.
2. Add it to `nav:` in `mkdocs.yml`. This is required — `--strict` fails on a
   page that exists but is not in the nav.
3. Link to it from the section's `index.md`.
4. Run `mkdocs build --strict`.

## Keeping it in sync with the code

Three things to check when you change the code:

- **Adding or removing a public function.** The
  [API reference](../reference/api/index.md) is generated from the source by
  mkdocstrings, so the signature and docstring update themselves. But the
  grouping pages under `docs/reference/api/` list modules explicitly — a new
  *module* needs adding there.
- **Adding, removing, or reordering a pipeline step.** Update the relevant
  [step reference](../reference/odm-pipeline-steps.md), and the worked example
  in [Re-run a single pipeline step](run-a-single-pipeline-step.md) if it
  applies.
- **Adding or renaming a CLI option.** Update the
  [CLI reference](../reference/cli.md).

Because the API reference is generated from docstrings, the docstrings *are*
documentation. See the docstring conventions in
[Set up a development environment](set-up-a-development-environment.md#code-conventions).

## House style

Markdown is wrapped at **80 columns**, except inside tables, code blocks, and
long URLs.

## How it is deployed

`.github/workflows/docs.yaml` has two jobs:

- **build** — runs on every push and pull request, with `mkdocs build --strict`.
  A pull request that breaks a link fails the check.
- **deploy** — runs only on `main`, publishing to GitHub Pages.

The site is at
<https://phes-odm.github.io/PHES-ODM-LinkMLGenerator/>.

!!! note "One-time repository setting"

    The deploy job uses the GitHub Actions Pages deployment flow, which requires
    **Settings → Pages → Build and deployment → Source** to be set to
    **GitHub Actions**. Until that is done the build job passes and the deploy
    job fails.

You can also trigger a rebuild by hand from the Actions tab — the workflow
declares `workflow_dispatch`.
