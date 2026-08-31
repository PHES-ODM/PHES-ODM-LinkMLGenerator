# Continuous integration

The four GitHub Actions workflows in
[`.github/workflows/`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/tree/main/.github/workflows).
Three of them check the repository; the fourth generates the ODM v3 schema and
commits it.

| Workflow | File | Runs on | Does |
| --- | --- | --- | --- |
| Lint and Format | `lint.yaml` | Push to `main`, pull request | `ruff check` and `ruff format --diff` |
| Tests | `pytest.yaml` | Push to `main`, pull request | `pytest tests/` |
| Documentation | `docs.yaml` | Push to `main`, pull request, manual | `mkdocs build --strict`, then deploys to GitHub Pages from `main` |
| Generate ODM Schema | `generate-odm-schema.yaml` | Weekly, manual, repository dispatch, push or pull request touching the generator | Regenerates and commits `schemas/odm_v3.yaml` |

## Generate ODM Schema

Regenerates the ODM v3 LinkML schema from the published dictionary tables and
commits it to
[`schemas/odm_v3.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/schemas/odm_v3.yaml),
which is the copy other repositories should read. It is the automated form of
[step 1 of Roll out a dictionary update](../how-to/dictionary-workflow.md#1-generate-the-linkml-schema).

### What it does

1. Resolves the requested ref of
   [PHES-ODM/PHES-ODM](https://github.com/PHES-ODM/PHES-ODM) to a commit SHA,
   and downloads `ODM_parts_v3.0.0.csv` and `ODM_sets_v3.0.0.csv` from
   `dictionary-tables/` **at that SHA** — so the two tables cannot come from
   different commits if the branch moves mid-run.
2. Runs `odm-linkmlgen-odm --version 3`, teeing the log to `gen/generate.log`.
3. Fails the run if the log holds an `ERROR`. This is the check
   [step 3 of Generate the ODM schemas](../how-to/generate-odm-schemas.md) asks
   you to do by hand, and it matters here for the same reason: a defect in the
   source dictionary is logged and skipped rather than raised, so a run can exit
   0 having produced a degraded schema. A `WARNING` is surfaced as an annotation
   but is not fatal.
4. Uploads the schema, both intermediate stages, and the log as the
   `odm-v3-schema` artifact — on every run, including failed ones and pull
   requests.
5. Copies the schema to `schemas/odm_v3.yaml` and commits it, if it changed.

### When it runs

| Trigger | Why |
| --- | --- |
| `schedule`, Mondays 07:00 UTC | The dictionary is in another repository, which cannot notify this one. The schedule bounds how stale the committed schema can get at a week. |
| `workflow_dispatch` | To pick a dictionary change up immediately, or to generate from another branch of the dictionary repository. |
| `repository_dispatch`, type `dictionary-updated` | So the PHES-ODM repository — or anything else holding a token for this one — can request a regeneration the moment the tables change. It may carry `dictionary_ref` and `commit` in its `client_payload`. See [Trigger generation from another repository](../how-to/trigger-from-another-repository.md). |
| `push` to `main` touching `odm_linkmlgen/**` or `requirements.txt` | The other half of the problem: the same dictionary produces a different schema once the generator changes. |
| `pull_request` touching the same paths | Proves a generator change still produces a clean schema before it reaches `main`. Commits nothing; the artifact is there to diff. |

### Inputs

A caller can make two choices. They reach the run either as
`workflow_dispatch` inputs or as `repository_dispatch` `client_payload` fields,
and the **Resolve the dictionary ref and whether to commit** step settles both
into a single answer the later steps read.

| Input | Default | What it does |
| --- | --- | --- |
| `dictionary_ref` | `label` | The branch, tag, or commit of PHES-ODM/PHES-ODM to read the tables from. Held to the shape of a plain branch, tag, or SHA — the run fails rather than passing anything else on to the API, because on a dispatch this comes from outside the repository. |
| `commit` | `true` | Set false to generate and upload the artifact without committing. |

```console
gh workflow run generate-odm-schema.yaml \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    -f dictionary_ref=some-dictionary-branch \
    -f commit=false
```

An input wins over the same field in a payload, and both fall back to the
defaults above.

#### Only the published dictionary is ever committed

A run that read any ref other than `DICTIONARY_REF_DEFAULT` (`label`) generates
the schema and uploads it, but **never commits it** — even when `commit` is
explicitly true. So `dictionary_ref` is for inspecting what a proposed
dictionary change would do, and the committed schema always came from the
published tables.

That is also what makes it safe for another repository to choose the ref: a
token holder cannot make a schema built from an unmerged branch become the
canonical one. Pull requests never commit either, for the same reason.

Whether to commit is therefore decided in one place and exposed as the resolve
step's `commit` output, which the commit step's `if` reads. Resolving it in
shell rather than in a GitHub expression is deliberate: an absent value arrives
as the empty string, and a GitHub expression compares the empty string equal to
`false`, so `inputs.commit != false` is false on a schedule and
`inputs.commit || payload.commit` silently discards an explicit `false`.

To fire the repository dispatch from another repository or a script:

```console
gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches \
    -f event_type=dictionary-updated
```

This needs a token with Contents write on this repository — a `GITHUB_TOKEN`
will not do, both because it is scoped to its own repository and because events
it sends deliberately do not start workflow runs.
[Trigger generation from another repository](../how-to/trigger-from-another-repository.md)
sets that up end to end, including sending a `dictionary_ref` in the
`client_payload`.

### Why it commits rather than opening a pull request

The schema is a build artefact, not authored content: reviewing it line by line
is not useful, and a pull request nobody merges leaves the committed copy stale,
which is the problem this workflow exists to solve. The `ERROR` check is what
stands in for review. A run that regenerates an unchanged schema commits
nothing — the generator writes no timestamps, so identical inputs produce an
identical file, and the weekly run is a no-op most weeks.

### What it does not do

Only ODM v3 is generated and committed. ODM v1, ODM v2, and the NWSS schemas
are still local runs — v2 is superseded, and the NWSS dictionaries are Excel
workbooks, two of them not public. Steps 2 to 5 of
[Roll out a dictionary update](../how-to/dictionary-workflow.md) — copying the
schema to the consuming repositories, and regenerating the LinkML-Map schemas
and the validation assets — are also still manual.

### Configuring it

The paths and versions are environment variables rather than literals in the
steps, so retargeting the workflow does not mean rewriting it.

Most of them are shared, because any other workflow driving part of the
dictionary rollout needs the same answers — which dictionary is read, which ODM
version is generated, and where the schema is committed. Those live in
[`.github/odm-config.env`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/.github/odm-config.env):

| Variable | Default |
| --- | --- |
| `ODM_VERSION` | `3` |
| `DICTIONARY_REPO` | `PHES-ODM/PHES-ODM` |
| `DICTIONARY_DIR` | `dictionary-tables` |
| `PARTS_CSV` | `ODM_parts_v3.0.0.csv` |
| `SETS_CSV` | `ODM_sets_v3.0.0.csv` |
| `DICTIONARY_REF_DEFAULT` | `label` |
| `SCHEMA_PATH` | `schemas/odm_v3.yaml` |

One is this workflow's own scratch space, and stays in its `env` block:

| Variable | Default |
| --- | --- |
| `DOWNLOAD_DIR` | `gen/dictionary-download` |

The dictionary tables are downloaded under `gen/`, which is git-ignored, so the
only thing a run adds to the working tree is the schema itself. `DOWNLOAD_DIR`
must not be the `--output-dir`, which the generator clears before reading from
it.

The commit needs `contents: write`, which the workflow grants to its own job.
If **Settings > Actions > General > Workflow permissions** is set to
"Read repository contents and packages permissions", that job-level grant is
still honoured, but branch protection on `main` is not: a protected `main`
rejects the push unless `github-actions[bot]` is allowed to bypass it.

### Sharing the configuration with another workflow

`.github/odm-config.env` is a dotenv file — one `NAME=VALUE` per line, no
quoting, `#` for a comment. A workflow reads it by checking the repository out
and then using the local composite action, which loads every setting into the
environment of the steps after it and fails the job if a line is neither a
setting nor a comment:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Load the shared ODM configuration
    uses: ./.github/actions/odm-config

  - run: echo "Reading ${DICTIONARY_REPO}/${DICTIONARY_DIR}/${PARTS_CSV}"
```

The step has to come before the first step that reads a setting, and after the
checkout that puts the file on disk. A setting is then available both as a shell
variable, as above, and as `${{ env.PARTS_CSV }}` in a later step's `with:`.

GitHub offers no way to share these at the point where a workflow is parsed, so
a value needed in `on:`, `concurrency:`, or a `workflow_dispatch` input default
cannot come from the file — those are read before any step runs. That is why the
`dictionary_ref` input repeats `label` as its default literally rather than
reading `DICTIONARY_REF_DEFAULT`; the two have to be changed together.

## Related

- [Roll out a dictionary update](../how-to/dictionary-workflow.md) — the whole
  dictionary-change process, of which this workflow is the first step
- [Generate the ODM schemas](../how-to/generate-odm-schemas.md) — the same
  generation run, done locally
- [Output layout](output-layout.md) — what the run writes to `--output-dir`
- [Contributing](../how-to/contributing.md) — running the lint and the tests
  locally before they run in CI
