"""Publish the products of a dictionary rollout to their destinations.

Reads .github/odm-rollout.yaml, copies each product built by the Roll Out
Dictionary Update workflow to the location that configuration gives it, and
commits the result.

There are two modes, and the configuration chooses between them:

staged
    `staging.repo` is set. One repository is cloned, and every product is
    written into it at <staging.dir>/<owner>/<repo>/<the path it was meant
    for>. No target repository is contacted at all, so a staged run cannot
    overwrite anything anywhere. This is the mode to use while the published
    dictionary tables are behind the current dictionary, since a schema
    generated from them is older than the files already committed to the
    targets.

live
    `staging.repo` is empty. Each target repository is cloned and written to
    for real. Refused unless --allow-live is passed, so that clearing the
    staging repository by accident is not enough to start overwriting files.

Both modes commit nothing when a destination is already identical to what was
built, so re-running after an unchanged dictionary is a no-op.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


def run(args, cwd=None, capture=False):
    """Run a command, raising if it fails."""
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def clone(repo, branch, dest, token):
    """Clone one repository at its tip, shallowly.

    The token goes in the URL rather than in a header, and the URL is never
    printed: git redacts it in its own output, and nothing here echoes the
    command.
    """
    url = f"https://x-access-token:{token}@github.com/{repo}.git"
    args = ["git", "clone", "--depth", "1"]
    if branch:
        args += ["--branch", branch]
    args += [url, str(dest)]
    print(f"Cloning {repo}" + (f" ({branch})" if branch else ""))
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
    run(["git", "config", "user.name", BOT_NAME], cwd=dest)
    run(["git", "config", "user.email", BOT_EMAIL], cwd=dest)
    return run(["git", "symbolic-ref", "--short", "HEAD"], cwd=dest, capture=True)


def clear_dir(path):
    """Empty a directory, leaving the directory itself in place."""
    if not path.is_dir():
        return
    for entry in sorted(path.iterdir()):
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def check_products(products_dir, targets):
    """Fail before anything is cloned if a product is missing or empty.

    Every product comes from a job that has already succeeded, so a missing
    one means the workflow was changed without the configuration being
    changed with it. Better to say so than to publish a partial rollout.
    """
    problems = []
    for target in targets:
        product = target["product"]
        src = products_dir / product.rstrip("/")
        if product.endswith("/"):
            if not src.is_dir():
                problems.append(f"{target['name']}: no directory {product}")
            elif not any(f.is_file() for f in src.iterdir()):
                problems.append(f"{target['name']}: {product} holds no files")
        elif not src.is_file():
            problems.append(f"{target['name']}: no file {product}")
    if problems:
        raise SystemExit(
            "These targets have nothing to publish, so nothing was published:\n  "
            + "\n  ".join(problems)
        )


def copy_product(products_dir, target, dest_dir):
    """Copy one target's product into dest_dir, returning the file names.

    A product ending in a slash is a directory, and every file directly in it
    is copied; anything else is a single file. Subdirectories are not copied:
    no product has any, and silently flattening one would be worse than
    failing on it later.
    """
    product = target["product"]
    src = products_dir / product.rstrip("/")

    if product.endswith("/"):
        if not src.is_dir():
            raise SystemExit(f"{target['name']}: no product directory {src}")
        files = sorted(f for f in src.iterdir() if f.is_file())
        if not files:
            raise SystemExit(f"{target['name']}: product directory {src} is empty")
        if target.get("replace"):
            clear_dir(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, dest_dir / f.name)
        return [f.name for f in files]

    if not src.is_file():
        raise SystemExit(f"{target['name']}: no product file {src}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / src.name)
    return [src.name]


def commit_and_push(repo, checkout, branch, message, body):
    """Commit everything in a checkout and push it, or report no change."""
    run(["git", "add", "--all"], cwd=checkout)
    status = run(["git", "status", "--porcelain"], cwd=checkout, capture=True)
    if not status:
        print(f"{repo}: already up to date, nothing to commit.")
        return False
    run(["git", "commit", "-m", message, "-m", body], cwd=checkout)
    run(["git", "push", "origin", f"HEAD:{branch}"], cwd=checkout)
    print(f"{repo}: pushed to {branch}.")
    return True


def manifest(config, args, rows):
    """Describe a staged run, for the staging repository to carry with it."""
    staging = config["staging"]
    lines = [
        f"# Staged ODM v{args.odm_version} dictionary rollout",
        "",
        "Built by the Roll Out Dictionary Update workflow of "
        "PHES-ODM/PHES-ODM-LinkMLGenerator. Nothing here has been published: "
        "every file below is a preview of what the run would have written to "
        "the repository and path it is filed under.",
        "",
        f"- Dictionary: `{args.dictionary_repo}@{args.dictionary_ref}` "
        f"(`{args.dictionary_sha}`)",
        f"- Run: {args.run_url}",
        "",
        "| Product | Would have been written to | Files |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        target, files = row
        dest = f"`{target['repo']}/{target['path']}`"
        lines.append(f"| `{target['product']}` | {dest} | {len(files)} |")
    lines.append("")
    lines.append(
        f"Everything under `{staging['dir']}/` is replaced by each run, so it "
        "is always one run's output."
    )
    lines.append("")
    return "\n".join(lines)


def summarise(rows, destination, staged):
    """Write the run summary GitHub shows on the run page."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    where = "staged in" if staged else "published to"
    lines = [
        f"### Rollout {where} `{destination}`",
        "",
        "| Product | Destination | Files |",
        "| --- | --- | --- |",
    ]
    for target, files in rows:
        lines.append(
            f"| `{target['product']}` | `{target['repo']}/{target['path']}` "
            f"| {len(files)} |"
        )
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


def publish_staged(config, args, token):
    """Write every product into the staging repository."""
    staging = config["staging"]
    checkout = args.work_dir / "staging"
    branch = clone(staging["repo"], staging.get("branch"), checkout, token)

    # The whole directory goes first, so that what is left is one run's output
    # and not a merge of this run with an older one — a product that stopped
    # being built should stop appearing.
    root = checkout / staging["dir"]
    clear_dir(root)
    root.mkdir(parents=True, exist_ok=True)

    rows = []
    for target in config["targets"]:
        dest = root / target["repo"] / target["path"]
        files = copy_product(args.products_dir, target, dest)
        print(f"{target['name']}: {len(files)} file(s) -> {dest.relative_to(checkout)}")
        rows.append((target, files))

    (root / "MANIFEST.md").write_text(manifest(config, args, rows))

    body = (
        f"Generated from {args.dictionary_repo}@{args.dictionary_ref} "
        f"({args.dictionary_sha}).\n\n"
        f"Staged only: nothing was written to the target repositories. "
        f"Run: {args.run_url}"
    )
    commit_and_push(
        staging["repo"],
        checkout,
        branch,
        f"Stage the ODM v{args.odm_version} dictionary rollout",
        body,
    )
    summarise(rows, staging["repo"], staged=True)


def publish_live(config, args, token):
    """Write each product to the repository it is actually meant for."""
    if not args.allow_live:
        raise SystemExit(
            "staging.repo is empty, so this run would write to the target "
            "repositories, but allow_live was not set. Set it deliberately, "
            "or restore staging.repo in .github/odm-rollout.yaml."
        )

    by_repo = {}
    for target in config["targets"]:
        by_repo.setdefault(target["repo"], []).append(target)

    rows = []
    for repo, targets in by_repo.items():
        checkout = args.work_dir / repo.replace("/", "__")
        branch = clone(repo, None, checkout, token)
        for target in targets:
            dest = checkout / target["path"]
            files = copy_product(args.products_dir, target, dest)
            print(f"{target['name']}: {len(files)} file(s) -> {repo}/{target['path']}")
            rows.append((target, files))
        body = (
            f"Generated from {args.dictionary_repo}@{args.dictionary_ref} "
            f"({args.dictionary_sha}).\n\nRun: {args.run_url}"
        )
        commit_and_push(
            repo,
            checkout,
            branch,
            f"Update the ODM v{args.odm_version} schema and generated assets",
            body,
        )
    summarise(rows, "their target repositories", staged=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--products-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--odm-version", required=True)
    parser.add_argument("--dictionary-repo", required=True)
    parser.add_argument("--dictionary-ref", required=True)
    parser.add_argument("--dictionary-sha", required=True)
    parser.add_argument("--run-url", default="")
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("ROLLOUT_TOKEN", "")
    if not token:
        raise SystemExit(
            "ROLLOUT_TOKEN is empty. A rollout writes to another repository, "
            "which the workflow's own token cannot do — see "
            "docs/how-to/automate-dictionary-rollout.md."
        )

    config = yaml.safe_load(args.config.read_text())
    check_products(args.products_dir, config["targets"])
    args.work_dir.mkdir(parents=True, exist_ok=True)

    if config.get("staging", {}).get("repo"):
        publish_staged(config, args, token)
    else:
        publish_live(config, args, token)


if __name__ == "__main__":
    sys.exit(main())
