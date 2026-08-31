# Trigger a dictionary rollout from another repository

How to have the whole [dictionary rollout](automate-dictionary-rollout.md) —
the ODM v3 LinkML schema, the LinkML-Map schemas, and the PHES-ODM-Validation
assets — run from the repository the dictionary lives in, normally
[PHES-ODM/PHES-ODM](https://github.com/PHES-ODM/PHES-ODM).

The [Roll Out Dictionary Update](../reference/continuous-integration.md#roll-out-dictionary-update)
workflow already accepts a `repository_dispatch` event of type
`dictionary-rollout`, so nothing in this repository needs changing. What is
missing is the other half: something in the dictionary repository that fires
that event. This page sets that up.

This is the same arrangement as
[Trigger generation from another repository](trigger-from-another-repository.md),
one workflow along. That page dispatches step 1 of the rollout; this one
dispatches all of it, publish included.

!!! warning "A rollout writes to another repository, and there is no schedule behind it"

    Two differences from the schema dispatch are worth knowing before you set
    this up.

    **It publishes.** A run does not commit to this repository at all — it
    writes its products to wherever
    [`.github/odm-rollout.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/.github/odm-rollout.yaml)
    says, which today is a staging repository rather than the real ones. That
    makes a dispatched run safe to review, but it is still a push to somewhere.

    **Nothing runs it on its own.** The schema workflow is scheduled weekly, so
    a dispatch there only buys promptness. The rollout workflow is manual and
    dispatch only, deliberately, so a dispatch is the *only* thing that makes
    it run unattended.

## Before you start

The rollout needs `ROLLOUT_TOKEN` to exist as a secret **in this repository**,
and the staging repository to exist. Dispatching does not change that — a
dispatched run fails in its publish step exactly as a manual one would. If it
has not been done, do
[Set it up](automate-dictionary-rollout.md#set-it-up) first.

Keep the two tokens straight; they are different credentials living in
different places:

| Token | Lives in | Lets something |
| --- | --- | --- |
| `LINKMLGEN_DISPATCH_TOKEN` | The dictionary repository | Ask this repository to run the workflow |
| `ROLLOUT_TOKEN` | This repository | Let the run write its products where they go |

## Which trigger to use

Two API endpoints will start the workflow from outside this repository. They
differ in how the arguments are passed, and in what the call means.

| | `repository_dispatch` | `workflow_dispatch` |
| --- | --- | --- |
| Endpoint | `POST /repos/{owner}/{repo}/dispatches` | `POST /repos/{owner}/{repo}/actions/workflows/{file}/dispatches` |
| Dictionary branch | `label`, or a `dictionary_ref` in the payload | `label`, or a `dictionary_ref` input |
| Caller has to know | the event type, `dictionary-rollout` | the workflow's file name and its input names |
| Token permission | Contents: write | Actions: write |
| `allow_live` | Ignored, always | Available |
| Meaning | "The dictionary changed — roll it out" | "Run this specific workflow with these arguments" |

**Use `repository_dispatch`** for the job this page is about, for the same
reason as the schema dispatch: the dictionary repository should not have to
know the name of a workflow file here, and a bare dispatch with no payload
rolls out from `label`.

The one thing `repository_dispatch` cannot do is turn on `allow_live`, the
switch that lets a run write to the real target repositories rather than to
staging. The workflow drops it on any event other than `workflow_dispatch` and
logs a notice saying so. That is on purpose: whether to overwrite files in
PHES-ODM-Mapper and PHES-ODM-Validation is a decision made here, by someone who
can see the configuration, and not something a token holder elsewhere can
trigger.

## 1. Create a token

A workflow's built-in `GITHUB_TOKEN` is scoped to its own repository, so it
cannot dispatch to this one. The dictionary repository needs a credential that
can.

!!! tip "If you already set up the schema dispatch, reuse that token"

    Both dispatches hit the same endpoint on the same repository and need the
    same permission, so `LINKMLGEN_DISPATCH_TOKEN` works for this one unchanged.
    Skip to [step 3](#3-add-the-dispatching-workflow).

=== "Fine-grained personal access token"

    Recommended for a first setup. Create it at
    **Settings > Developer settings > Personal access tokens > Fine-grained
    tokens** on the account that will own it, then:

    - **Resource owner**: `PHES-ODM`
    - **Repository access**: Only select repositories → `PHES-ODM-LinkMLGenerator`
    - **Repository permissions**: **Contents → Read and write**
    - **Expiration**: as short as you are willing to renew

    Contents write is what the dispatch endpoint requires. The token needs no
    access to the dictionary repository, to the staging repository, or to any
    rollout target — it is only ever used to say "something changed" to this
    one.

=== "GitHub App"

    Better for something long-lived, because an installation token is minted
    per run and there is no expiry date to be caught out by. Create an App
    owned by the `PHES-ODM` organisation with **Contents: Read and write**,
    install it on `PHES-ODM-LinkMLGenerator`, and mint a token in the workflow
    with
    [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token).
    The App's ID and private key are the two secrets you store instead of a PAT.

=== "Classic personal access token"

    Works, but grants far more than this needs — the `repo` scope covers every
    repository the account can reach. Use it only if fine-grained tokens are
    unavailable to you. `public_repo` is enough while this repository is public.

!!! warning "The token is a write credential for this repository"

    Contents write on `PHES-ODM-LinkMLGenerator` is enough to push to it.
    Anyone who can edit a workflow in the dictionary repository, or open a
    branch there that a workflow runs on, can potentially use the secret. Keep
    the token scoped to this one repository, and do not expose it to workflows
    triggered by pull requests from forks.

## 2. Store it as a secret in the dictionary repository

In **PHES-ODM/PHES-ODM > Settings > Secrets and variables > Actions**, add a
repository secret:

| Name | Value |
| --- | --- |
| `LINKMLGEN_DISPATCH_TOKEN` | The token from step 1 |

An organisation secret works too, and saves repeating this if other PHES-ODM
repositories come to need the same thing.

## 3. Add the dispatching workflow

Commit this to the dictionary repository as
`.github/workflows/roll-out-dictionary.yaml`.

```yaml
name: Roll Out Dictionary

# Asks PHES-ODM-LinkMLGenerator to regenerate the schema, the LinkML-Map
# schemas and the validation assets from this dictionary, and publish them.
on:
  # Deliberate rather than automatic: a rollout publishes downstream, so it is
  # run when the dictionary is ready to be rolled out, not on every edit.
  workflow_dispatch:
    inputs:
      dictionary_ref:
        description: 'Branch, tag, or SHA to roll out. Defaults to the published branch.'
        required: false
        default: ''
      publish:
        description: 'Publish the result, rather than building it and stopping.'
        type: boolean
        default: true

jobs:
  roll-out:
    name: Ask for a dictionary rollout
    runs-on: ubuntu-latest
    steps:
      - name: Send the dictionary-rollout dispatch
        env:
          GH_TOKEN: ${{ secrets.LINKMLGEN_DISPATCH_TOKEN }}
          REF: ${{ inputs.dictionary_ref }}
          PUBLISH: ${{ inputs.publish }}
        run: |
          set -euo pipefail
          # client_payload is a nested object, so it goes in as raw JSON via
          # --input rather than as `gh api -f` fields. An empty ref is dropped
          # rather than sent, so the run falls back to the published branch.
          jq -n --arg ref "${REF}" --argjson publish "${PUBLISH}" \
            '{
               event_type: "dictionary-rollout",
               client_payload: ({publish: $publish}
                 + (if $ref == "" then {} else {dictionary_ref: $ref} end))
             }' \
            | gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches --input -
```

`gh` and `jq` are both preinstalled on GitHub-hosted runners, and `gh api`
switches to `POST` on its own once a body is passed. A successful dispatch
returns `204 No Content` — an empty response body is what success looks like,
not a sign that nothing happened.

The simplest possible version, if you want no arguments at all, is a bare
dispatch. It rolls out `label` and publishes:

```yaml
      - name: Send the dictionary-rollout dispatch
        env:
          GH_TOKEN: ${{ secrets.LINKMLGEN_DISPATCH_TOKEN }}
        run: |
          set -euo pipefail
          gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches \
            -f event_type=dictionary-rollout
```

### Firing it on a push instead

The schema dispatch fires on every push to the two dictionary tables, and you
*can* do the same here by adding the same trigger:

```yaml
on:
  push:
    branches: [ label ]
    paths:
      - 'dictionary-tables/ODM_parts_v3.0.0.csv'
      - 'dictionary-tables/ODM_sets_v3.0.0.csv'
```

Think about it before you do. Regenerating a schema on every table edit costs
one workflow run and commits nothing if nothing changed; rolling out on every
table edit publishes an intermediate state of the dictionary to every
downstream repository. Runs are queued rather than cancelled — the workflow
takes a `concurrency` group so two rollouts cannot push at once — so a series
of pushes becomes a series of full rollouts, each publishing over the last.

If you do want it automatic, a release or a tag is usually the better signal,
because it fires when the dictionary is declared ready rather than while it is
being edited:

```yaml
on:
  release:
    types: [ published ]
```

A middle course is to fire on push with `"publish": false`, which builds
everything and uploads the artifacts without writing to any repository — a
continuous check that the current tables still roll out cleanly. See
[What to put in the payload](#what-to-put-in-the-payload).

## 4. Check that it worked

Run **Roll Out Dictionary** in the dictionary repository, then look at the
[Roll Out Dictionary Update runs](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/rollout-dictionary-update.yaml).
A run should appear within a few seconds, labelled `repository_dispatch`.

From the command line:

```console
gh run list \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    --workflow rollout-dictionary-update.yaml \
    --limit 5
```

What that run then does is unchanged from any other trigger — the four jobs
described in
[What one run does](automate-dictionary-rollout.md#what-one-run-does). Three
outcomes are worth knowing about:

- **A commit in the staging repository.** The normal, successful outcome while
  publishing is staged. Everything under `rollout/` is one run's output, and
  `MANIFEST.md` records which dictionary commit it read and which run produced
  it. See [Review a staged run](automate-dictionary-rollout.md#review-a-staged-run).
- **No commit anywhere.** The products were identical to what is already
  published, so nothing changed. The run's summary says so, and this is a
  normal, successful outcome.
- **A failed run.** Which job failed says what broke: `schema` means the
  generator logged an `ERROR` — usually an enumeration a part refers to but
  nothing defines; `mappers` or `validation` means the dictionary change broke
  something downstream of the schema; `publish` means the products were built
  but could not be written. Nothing is published unless every generation job
  succeeded. The `dictionary-rollout-products` artifact holds the whole tree
  the run would have published, and `generator-log` holds the generator's log.

Neither the dispatch nor its sender is told any of this — `repository_dispatch`
is fire-and-forget, and a `204` means "accepted", not "the rollout worked".
Anyone relying on the rollout should watch the run, or the commits to the
staging repository, rather than the dispatch response.

## What to put in the payload

A bare dispatch rolls out the `label` branch and publishes. Three fields are
read from `client_payload`, and anything else in it is ignored:

| Field | Default | What it does |
| --- | --- | --- |
| `dictionary_ref` | `label` | The branch, tag, or SHA of PHES-ODM/PHES-ODM to read the tables from. Rejected, and the run fails, if it is not the shape of a plain branch, tag, or SHA. |
| `publish` | `true` | Send JSON `false` to build everything and stop. No repository is contacted, and the products are still uploaded as the `dictionary-rollout-products` artifact. |
| `allow_live` | — | Read, then discarded on any event but `workflow_dispatch`. A dispatch can never make a run write to the real target repositories. |

Send `publish` as a JSON boolean rather than a string. The workflow treats
anything that is not exactly `true` as "do not publish", so `"yes"` quietly
turns publishing off.

A dry run of a proposed dictionary branch, then, is both fields together:

```console
gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches \
    --input - <<'JSON'
{
  "event_type": "dictionary-rollout",
  "client_payload": {
    "dictionary_ref": "my-dictionary-branch",
    "publish": false
  }
}
JSON
```

!!! note "A non-default ref still publishes"

    This differs from the schema workflow, which refuses to commit anything
    generated from a ref other than `label`. The rollout has no such rule,
    because it publishes nothing to this repository — its output goes to the
    staging repository, where replacing one run's preview with another's is the
    point.

    So a dispatch naming a branch produces a *staged* rollout of that branch,
    which is exactly what you want for seeing what a proposed dictionary change
    would do to everything downstream. Once `staging.repo` is cleared and live
    runs are possible, remember that this protection is not there and pair a
    branch ref with `"publish": false`.

### Or use the workflow_dispatch endpoint

The same choices are [inputs](automate-dictionary-rollout.md#run-it) of the
workflow, which is the better fit when a person is driving it rather than a
workflow, and the only way to pass `allow_live`. It needs a token with
**Actions: Read and write** instead of Contents write:

```console
gh workflow run rollout-dictionary-update.yaml \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    -f dictionary_ref=my-dictionary-branch \
    -f publish=false
```

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `404 Not Found` | Almost always the token, not the URL — a token without Contents write on the target gets a 404 rather than a 403, so that the endpoint does not confirm the repository exists. Check the repository is in the token's **Repository access** list, and that Contents is **Read and write**. Also check for a typo in the owner/repo. |
| `401 Bad credentials` | The token has expired, or the secret holds a truncated copy of it. Fine-grained tokens expire; reissue and update the secret. |
| `422 Unprocessable Entity` | The request body is malformed, or `event_type` is longer than 100 characters. |
| `204`, but no run appears | Three usual causes. **The event type does not match**: the workflow listens for `dictionary-rollout` exactly — `dictionary-updated` is the *schema* workflow — and an unmatched type is accepted and silently dropped. **The dispatch used a `GITHUB_TOKEN`**: events sent with the built-in token deliberately do not start new workflow runs, which is the main reason this needs a PAT or an App. **This repository's Actions are disabled**, or dispatched runs have been disabled after 60 days of repository inactivity. |
| The run is queued behind another | Expected. Rollouts share a `concurrency` group and are queued rather than cancelled, so that a run which has already built everything is not thrown away. |
| `Refusing the dictionary ref` and a failed `schema` job | The `dictionary_ref` in the payload is not the shape of a branch, tag, or SHA. It is checked rather than trusted, because on a dispatch it comes from outside this repository. |
| `ROLLOUT_TOKEN is empty` in the publish job | The secret is missing from **this** repository. The dispatch token in the dictionary repository is a different credential and does not stand in for it — see [Before you start](#before-you-start). |
| The publish job fails on the staging repository | `ROLLOUT_TOKEN` has expired, or lacks Contents write on the repository named in `staging.repo`, or that repository does not exist. A dispatched run has exactly the same requirements as a manual one. |
| `allow_live is ignored on a repository_dispatch event` | Working as intended. Live publishing is only reachable from a `workflow_dispatch` run started here. |
| Everything built, nothing published | `publish` was sent as something other than JSON `true`. A string, or a missing field where you meant to send `true`, both read as "do not publish". |
| The dictionary change is not in the rollout | A dispatch with no `dictionary_ref` reads the `label` branch. If the change is on another branch, the run genuinely rolled out tables that do not contain it. |

## Related

- [Automate a dictionary rollout](automate-dictionary-rollout.md) — setting the
  workflow up, reviewing a staged run, and publishing for real later
- [Trigger generation from another repository](trigger-from-another-repository.md)
  — the same arrangement for the schema workflow alone
- [Continuous integration](../reference/continuous-integration.md#roll-out-dictionary-update)
  — what the rollout workflow is made of, and where it publishes
- [Roll out a dictionary update](dictionary-workflow.md) — the manual process
  this dispatch automates end to end
- [Troubleshooting](troubleshooting.md) — when the regenerated schema is not
  what you expected
