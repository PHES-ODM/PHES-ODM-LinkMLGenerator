# Trigger schema generation from another repository

How to have the ODM v3 LinkML schema in this repository regenerate itself the
moment the data dictionary changes, driven from the repository the dictionary
lives in — normally [PHES-ODM/PHES-ODM](https://github.com/PHES-ODM/PHES-ODM).

The [Generate ODM Schema](../reference/continuous-integration.md#generate-odm-schema)
workflow already accepts a `repository_dispatch` event of type
`dictionary-updated`, so nothing in this repository needs changing. What is
missing is the other half: something in the dictionary repository that fires
that event. This page sets that up.

!!! note "It also runs weekly on its own"

    The workflow is scheduled for Mondays at 07:00 UTC, so the committed schema
    is never more than a week behind the dictionary even with no dispatch at
    all. What this page buys you is *promptness* — the schema regenerates within
    a minute of the dictionary change landing, rather than by the following
    Monday. Set it up if that matters; the schedule is a reasonable fallback if
    it does not.

## Which trigger to use

Two API endpoints will start the workflow from outside this repository. Both
read the two tables from `label` — the branch of PHES-ODM/PHES-ODM the
dictionary is published on — unless the caller names a different branch (or tag,
or SHA) in `dictionary_ref`. They differ in how that ref is passed, and in what
the call means.

| | `repository_dispatch` | `workflow_dispatch` |
| --- | --- | --- |
| Endpoint | `POST /repos/{owner}/{repo}/dispatches` | `POST /repos/{owner}/{repo}/actions/workflows/{file}/dispatches` |
| Dictionary branch | `label`, or a `dictionary_ref` in the payload | `label`, or a `dictionary_ref` input |
| Caller has to know | the event type, `dictionary-updated` | the workflow's file name and its input names |
| Token permission | Contents: write | Actions: write |
| Meaning | "The dictionary changed" — this repository decides what to do about it | "Run this specific workflow with these arguments" |

**Use `repository_dispatch`** for the job this page is about. The dictionary
repository should not have to know the name of a workflow file here, or which
branch the tables are published on — it only announces that something changed,
and a bare dispatch with no payload regenerates from `label`. That is what the
rest of this page uses.

Choosing the ref is *not* what separates the two: a `repository_dispatch`
payload can carry `dictionary_ref` just as well, and
[Generate from another dictionary branch](#generate-from-another-dictionary-branch)
does exactly that. What `workflow_dispatch` adds is that the two arguments are
declared as workflow inputs, so GitHub renders them as a form on the Actions
page and `gh workflow run` takes them as `-f` flags, rather than as free-form
JSON in a `client_payload`. Reach for it when a *person* is driving the run —
generating the schema from a proposed dictionary branch to see what the change
would do, say — rather than a workflow firing it unattended.

## 1. Create a token

A workflow's built-in `GITHUB_TOKEN` is scoped to its own repository, so it
cannot dispatch to this one. The dictionary repository needs a credential that
can.

=== "Fine-grained personal access token"

    Recommended for a first setup. Create it at
    **Settings > Developer settings > Personal access tokens > Fine-grained
    tokens** on the account that will own it, then:

    - **Resource owner**: `PHES-ODM`
    - **Repository access**: Only select repositories → `PHES-ODM-LinkMLGenerator`
    - **Repository permissions**: **Contents → Read and write**
    - **Expiration**: as short as you are willing to renew

    Contents write is what the dispatch endpoint requires. The token needs no
    access to the dictionary repository at all — it is only ever used to talk to
    this one.

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
`.github/workflows/notify-linkmlgenerator.yaml`. It fires only when one of the
two tables the generator actually reads changes on the `label` branch, so
editing `ODM_translations.csv` or a README does not spend a workflow run here.

```yaml
name: Notify LinkML Generator

on:
  push:
    branches: [ label ]
    paths:
      - 'dictionary-tables/ODM_parts_v3.0.0.csv'
      - 'dictionary-tables/ODM_sets_v3.0.0.csv'
  # So the dispatch can also be sent by hand, without touching the tables.
  workflow_dispatch:

jobs:
  notify:
    name: Ask for the ODM v3 schema to be regenerated
    runs-on: ubuntu-latest
    steps:
      - name: Send the dictionary-updated dispatch
        env:
          GH_TOKEN: ${{ secrets.LINKMLGEN_DISPATCH_TOKEN }}
        run: |
          set -euo pipefail
          gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches \
            -f event_type=dictionary-updated
```

`gh` is preinstalled on GitHub-hosted runners, and switches to `POST` on its own
once a field is passed.

That bare dispatch is all the common case needs: it means "the published
dictionary changed", and the workflow reads the `label` branch. To generate from
a different ref, put it in the payload — see
[Generate from another dictionary branch](#generate-from-another-dictionary-branch).

The equivalent with `curl`, if you would rather not depend on `gh`:

```yaml
      - name: Send the dictionary-updated dispatch
        env:
          TOKEN: ${{ secrets.LINKMLGEN_DISPATCH_TOKEN }}
        run: |
          set -euo pipefail
          curl -sSf -X POST \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.github.com/repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches" \
            -d '{"event_type":"dictionary-updated"}'
```

A successful dispatch returns `204 No Content` — an empty response body is what
success looks like, not a sign that nothing happened.

## 4. Check that it worked

Push a change to one of the two tables on `label`, or run **Notify LinkML
Generator** by hand, and then look at the
[Generate ODM Schema runs](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/generate-odm-schema.yaml).
A run should appear within a few seconds, labelled `repository_dispatch`.

From the command line:

```console
gh run list \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    --workflow generate-odm-schema.yaml \
    --limit 5
```

What that run then does is unchanged from any other trigger — it downloads the
two tables from `label`, generates, and commits
[`schemas/odm_v3.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/schemas/odm_v3.yaml)
if the schema changed. Two outcomes are worth knowing about:

- **No commit.** The regenerated schema was byte-identical to the committed one,
  so the dictionary change did not affect the LinkML schema. The run says so in
  its summary. This is a normal, successful outcome.
- **A failed run.** The generator logged an `ERROR`, which means the dictionary
  change introduced a defect the generator could not resolve — most often an
  enumeration a part refers to but nothing defines. Nothing is committed. The
  run's `odm-v3-schema` artifact holds the schema it would have committed, plus
  both intermediate stages and the log, so you can see what the change did. See
  [Troubleshooting](troubleshooting.md).

Neither the dispatch nor its sender is told any of this — `repository_dispatch`
is fire-and-forget, and a `204` means "accepted", not "the schema is fine".
Anyone relying on the schema being regenerated should watch the run, or the
commits to `schemas/`, rather than the dispatch response.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `404 Not Found` | Almost always the token, not the URL — a token without Contents write on the target gets a 404 rather than a 403, so that the endpoint does not confirm the repository exists. Check the repository is in the token's **Repository access** list, and that Contents is **Read and write**. Also check for a typo in the owner/repo. |
| `401 Bad credentials` | The token has expired, or the secret holds a truncated copy of it. Fine-grained tokens expire; reissue and update the secret. |
| `422 Unprocessable Entity` | The request body is malformed, or `event_type` is longer than 100 characters. |
| `204`, but no run appears | Three usual causes. **The event type does not match**: the workflow listens for `dictionary-updated` exactly, and an unmatched type is accepted and silently dropped. **The dispatch used a `GITHUB_TOKEN`**: events sent with the built-in token deliberately do not start new workflow runs, to stop workflows triggering themselves — this is the main reason the setup needs a PAT or an App. **This repository's Actions are disabled**, or scheduled and dispatched runs have been disabled after 60 days of repository inactivity. |
| The run starts but the push fails | Branch protection on `main` rejecting `github-actions[bot]`. This is unrelated to the dispatch — see [Continuous integration](../reference/continuous-integration.md#configuring-it). |
| The dictionary change is not in the generated schema | A dispatch with no `dictionary_ref` reads the `label` branch. If the change is on another branch, the run genuinely regenerated from tables that do not contain it — pass the ref in the payload, as [below](#generate-from-another-dictionary-branch). |
| The run generated a schema but committed nothing | Either the schema was unchanged, or the run read a ref other than `label`, which never commits. The run's log says which. |
| `Refusing the dictionary ref` and a failed run | The `dictionary_ref` in the payload is not the shape of a branch, tag, or SHA. It is checked rather than trusted, because on a dispatch it comes from outside this repository. |

## Generate from another dictionary branch

Useful for seeing what a *proposed* dictionary change would do to the schema
before it is merged. Send a `dictionary_ref` in the dispatch payload:

```console
gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches \
    --input - <<'JSON'
{
  "event_type": "dictionary-updated",
  "client_payload": { "dictionary_ref": "my-dictionary-branch" }
}
JSON
```

`client_payload` is a nested object, so it goes in as raw JSON via `--input`
rather than as `gh api -f` fields; either one makes `gh api` use `POST`. From a
workflow, the ref is usually the branch that was pushed:

```yaml
      - name: Generate from this branch without committing
        env:
          GH_TOKEN: ${{ secrets.LINKMLGEN_DISPATCH_TOKEN }}
          REF: ${{ github.ref_name }}
        run: |
          set -euo pipefail
          jq -n --arg ref "${REF}" \
            '{event_type: "dictionary-updated", client_payload: {dictionary_ref: $ref}}' \
            | gh api repos/PHES-ODM/PHES-ODM-LinkMLGenerator/dispatches --input -
```

!!! important "A non-default ref never commits"

    A run that read anything other than the `label` branch generates the schema
    and uploads it as the `odm-v3-schema` artifact, but does **not** commit it —
    even if the payload asks it to with `"commit": true`. The run logs a notice
    saying so.

    This is what makes it safe to let another repository choose the ref. The
    committed [`schemas/odm_v3.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/schemas/odm_v3.yaml)
    tracks the *published* dictionary, and a token holder cannot make a schema
    from an unmerged branch become the canonical one. The worst a dispatch can
    do is spend a workflow run.

    To publish a schema from a dictionary change, merge the change to `label`
    and let a bare dispatch regenerate from it.

Two other payload fields are read:

| Field | Default | What it does |
| --- | --- | --- |
| `dictionary_ref` | `label` | The branch, tag, or SHA of PHES-ODM/PHES-ODM to read the tables from. Rejected, and the run fails, if it is not the shape of a plain branch, tag, or SHA. |
| `commit` | `true` | Set to `false` to generate from `label` without committing — a dry run of the real thing. |

Anything else in the payload is ignored.

### Or use the workflow_dispatch endpoint

The same two choices are available as `workflow_dispatch`
[inputs](../reference/continuous-integration.md#inputs), which is the better fit
when a person is driving it rather than a workflow. It needs a token with
**Actions: Read and write** instead of Contents write:

```console
gh workflow run generate-odm-schema.yaml \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    -f dictionary_ref=my-dictionary-branch
```

The same rule applies — that run will not commit, because the ref is not
`label`.

## Related

- [Continuous integration](../reference/continuous-integration.md) — what the
  Generate ODM Schema workflow does, its inputs, and its other triggers
- [Roll out a dictionary update](dictionary-workflow.md) — the whole
  dictionary-change process; this page automates the front of step 1
- [Trigger a dictionary rollout from another repository](trigger-rollout-from-another-repository.md)
  — the same arrangement for the whole rollout, not just the schema
- [Generate the ODM schemas](generate-odm-schemas.md) — the same generation run,
  done locally
- [Troubleshooting](troubleshooting.md) — when the regenerated schema is not
  what you expected
