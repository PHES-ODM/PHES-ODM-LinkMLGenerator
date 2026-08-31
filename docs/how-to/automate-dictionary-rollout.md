# Automate a dictionary rollout

The **Roll Out Dictionary Update** workflow does every generation step of
[Roll out a dictionary update](dictionary-workflow.md) in one run: it
regenerates the ODM v3 LinkML schema, the LinkML-Map schemas that the
PHES-ODM-Mapper reads, and the PHES-ODM-Validation assets, and publishes all of
it in the shape the manual process would have put it in.

!!! warning "It publishes to a staging repository, not to the real ones"

    The dictionary tables published on the `label` branch of
    [PHES-ODM/PHES-ODM](https://github.com/PHES-ODM/PHES-ODM/tree/label/dictionary-tables)
    are **behind the current dictionary**. A schema generated from them is
    therefore older than the `odm_v3.yaml` files already committed to the
    repositories that consume it, and the same is true of the LinkML-Map
    schemas on PHES-ODM-Mapper and the assets on PHES-ODM-Validation. A run
    that wrote to those repositories today would replace newer files with older
    ones.

    So it does not write to them. Every file goes to one staging repository
    instead, filed under the repository and path it was meant for, which makes
    a run reviewable without being destructive. See
    [Publish for real, later](#publish-for-real-later) for what changes when
    the published tables catch up.

## What one run does

| Job | Manual step | What it does |
| --- | --- | --- |
| Generate the schema | 1 | Downloads the parts and sets tables at one commit and runs `odm-linkmlgen-odm`, failing if the generator logged an `ERROR`. Produces the schema and the normalised `parts.csv` and `sets.csv`. |
| Regenerate the LinkML-Map schemas | 3 | Checks PHES-ODM-MapGenerator out, replaces its copy of the ODM schema with the one just generated, and generates the three mappings. |
| Regenerate the validation assets | 5 (first half) | Checks PHES-ODM-Validation out, puts the tables in `assets/dictionary/v3.0.1/`, and runs `generate_assets.py`. |
| Publish | 2, 4, 5 (second half) | Writes every product to the destination [`.github/odm-rollout.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/.github/odm-rollout.yaml) gives it, and commits. |

The three generation jobs each need a different Python environment — this
repository's, the map generator's, and the validation library's — which is why
they are separate jobs rather than steps of one.

Step 1 is also the job of the [Generate ODM Schema](../reference/continuous-integration.md#generate-odm-schema)
workflow, and both run it through the same
`.github/actions/generate-odm-schema` action, so the schema a rollout publishes
is generated exactly the way the committed one is.

## Set it up

Three one-time things. Only the first two involve anything outside this
repository.

### 1. Create the staging repository

Anywhere you can push to. The workflow only ever writes under one directory in
it, so an otherwise empty repository is fine, and a private one is fine too.

```console
gh repo create PHES-ODM/PHES-ODM-RolloutStaging \
    --private \
    --description "Staged output of the PHES-ODM-LinkMLGenerator dictionary rollout" \
    --add-readme
```

If you name it something else, change `staging.repo` in
[`.github/odm-rollout.yaml`](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/blob/main/.github/odm-rollout.yaml)
to match. Set `staging.branch` too if its default branch is not `main`.

### 2. Create a token that can write to it

A workflow's own `GITHUB_TOKEN` is scoped to the repository it runs in and
cannot write to another one at all, so a rollout needs a token of its own. A
fine-grained personal access token, from **Settings > Developer settings >
Personal access tokens > Fine-grained tokens**:

- **Repository access**: only select repositories → the staging repository.
  Nothing else. While the rollout is staged, that is the only repository it
  ever contacts, and a token that cannot reach the others cannot damage them
  even if the configuration is changed by mistake.
- **Permissions**: Repository permissions → Contents → **Read and write**.
- **Expiration**: whatever your organisation requires. The workflow fails with
  a clear error when the token has expired.

### 3. Add it as a secret

In this repository, **Settings > Secrets and variables > Actions > New
repository secret**, named `ROLLOUT_TOKEN`:

```console
gh secret set ROLLOUT_TOKEN \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator \
    --body "github_pat_..."
```

## Run it

From the
[Actions tab](https://github.com/PHES-ODM/PHES-ODM-LinkMLGenerator/actions/workflows/rollout-dictionary-update.yaml)
with **Run workflow**, or:

```console
gh workflow run rollout-dictionary-update.yaml \
    --repo PHES-ODM/PHES-ODM-LinkMLGenerator
```

| Input | Default | What it does |
| --- | --- | --- |
| `dictionary_ref` | `label` | The branch, tag, or commit of PHES-ODM/PHES-ODM to read the tables from. Point it at a branch to see what a proposed dictionary change would do to everything downstream, not just to the schema. |
| `publish` | checked | Uncheck to build everything and stop. The products are still uploaded as the `dictionary-rollout-products` artifact, and no repository is touched. |
| `allow_live` | unchecked | Only does anything once `staging.repo` has been cleared. See [Publish for real, later](#publish-for-real-later). |

A `repository_dispatch` of type `dictionary-rollout` runs it too, and may carry
`dictionary_ref` and `publish` in its `client_payload` — the same arrangement
[Trigger generation from another repository](trigger-from-another-repository.md)
sets up for the schema workflow. `allow_live` is deliberately ignored on a
dispatch: whether to write to the real repositories is a decision made here.

Runs are queued rather than cancelled, since a run that has already built
everything is not worth throwing away.

## Review a staged run

The staging repository holds one directory, and each run replaces all of it, so
what is in it is always one run's output:

```text
rollout/
├── MANIFEST.md
└── PHES-ODM/
    ├── PHES-ODM-MapGenerator/
    │   └── odm_map_maker/data/odm_v3/linkml/odm_v3.yaml
    ├── PHES-ODM-Mapper/
    │   └── odm_map/data/modules/
    │       ├── _shared/schemas/odm_v3.yaml
    │       ├── odm-v1-to-v3/mappers/…
    │       ├── nwss-reporting-to-v3/mappers/…
    │       └── pha4ge-to-v3/mappers/…
    └── …
```

Every path under `rollout/` is `<owner>/<repo>/<the path in that repo>`, so
what a file would replace is the file at the same path in the repository it is
filed under. `MANIFEST.md` records which dictionary commit the run read, which
run produced it, and a row per destination; the run's own summary on the Actions
page says the same thing.

Because each run replaces the directory, `git log` on the staging repository is
a history of rollouts, and `git diff` between two of its commits is the diff
between two dictionary states — across the schema, the mappers, and the
validation assets at once.

## Add a destination

One entry under `targets` in `.github/odm-rollout.yaml`:

```yaml
  - name: Some other repository's schema
    repo: PHES-ODM/PHES-ODM-Something
    path: path/to/schemas
    product: schema/odm_v3.yaml
```

`repo` and `path` are the real destination — they are what a live run writes
to, and what a staged run uses to file the product. `product` names one of the
things a run builds:

| Product | What it is |
| --- | --- |
| `schema/odm_v3.yaml` | The generated ODM v3 LinkML schema |
| `dictionary/` | `parts.csv` and `sets.csv`, normalised by the generator — not byte-identical to the published tables |
| `mappers/odm-v1-to-v3/` | The LinkML-Map schemas for one mapping |
| `mappers/nwss-reporting-to-v3/` | " |
| `mappers/pha4ge-to-v3/` | " |
| `validation/validation-schemas/` | What `generate_assets.py` wrote to `assets/validation-schemas/` |
| `validation/odm/` | The table-name files it wrote to `assets/odm/` |

A trailing slash means a directory, and every file in it is copied. Add
`replace: true` for a directory whose old contents should be deleted first —
which is what the mapper destinations do, so that a mapping which stops
producing a file stops shipping it.

Adding a mapping is an entry under `map_generator.mappers` plus a `targets`
entry naming its `product`. Nothing in the workflow needs to change for either.

## Publish for real, later

Once the tables on the `label` branch are current, and not before:

1. Check that they are. The point of the staging repository is that this is
   easy to see: a staged run whose schema is *newer* than the committed
   `odm_v3.yaml` files is the signal.
2. Extend `ROLLOUT_TOKEN` to the target repositories, with Contents write.
   PHES-ODM-QPCR-Pipeline is private, so it needs granting explicitly.
3. Clear `staging.repo` in `.github/odm-rollout.yaml` — set it to `''`.
4. Run the workflow with **allow_live** checked.

Step 4 is a separate switch from step 3 on purpose. A configuration edit is not
enough to start overwriting other repositories: the publisher refuses a live
run without `allow_live` and says so, so an accidental or partial edit fails
loudly instead of publishing.

A live run clones each target repository, copies the products into it, and
commits and pushes to its default branch — one commit per repository, and no
commit at all where nothing changed.

## What it does not do

- **Open pull requests.** It commits directly, for the same reason the schema
  workflow does: the files are build output, and reviewing them line by line is
  not useful. The staging repository is where a rollout gets reviewed.
- **Run the mapper validator.** PHES-ODM-MapGenerator's
  [checks on the generated mappers](https://github.com/PHES-ODM/PHES-ODM-MapGenerator#check-the-generated-mappers)
  are advisory rather than pass/fail, so they are still a manual read.
- **Cover ODM v1, ODM v2, or NWSS.** Same reason as the schema workflow: v2 is
  superseded, and the NWSS dictionaries are Excel workbooks, two of them not
  public.
- **Work out which validation dictionary version to write.** `v3.0.1` is
  configured, in `validation.dictionary_version`. PHES-ODM-Validation decides
  which versions to generate assets for by listing the directories under
  `assets/dictionary/`, so that setting is what makes it generate anything for
  ODM v3 at all — and it regenerates every other version's assets in the same
  run, which is what the manual process pushes too.

## Related

- [Roll out a dictionary update](dictionary-workflow.md) — the manual process
  this workflow automates, and the only description of what each step is for
- [Continuous integration](../reference/continuous-integration.md) — this
  workflow and the four others, and the shared configuration they read
- [Trigger generation from another repository](trigger-from-another-repository.md)
  — dispatching a run from the PHES-ODM repository
- [Troubleshooting](troubleshooting.md) — when the regenerated schema is not
  what you expected
