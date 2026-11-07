# Handoff Plan — Automated GitHub Gist Synchronization



Architecture agreed

Implementation pending



This checkpoint captures the decisions we've made, the current working state, and the implementation steps needed to resume later.

The objective is to automate publishing code snippets from your game-dev blog as GitHub Gists, while keeping the original Markdown files independent of Hugo and GitHub-specific publishing details.

## 1. Current project state

### Repository structure

Your current content structure is:

```
repository/
├── gamedev/
│   ├── _index.md
│   ├── nanoswarm/
│   │   ├── devlog_1/
│   │   │   └── some_image.png
│   │   ├── devlog_2/
│   │   │   └── some_other_image.png
│   │   ├── devlog#1.md
│   │   └── devlog#2.md
│   └── blog_post.md
│
├── projects/
│   ├── _index.md
│   └── project_writeup.md
│
├── site/
│   └── {hugo_site_files_here}
│
└── .github/
    ├── scripts/
    │   ├── gist_client.py
    │   └── sync_content.py
    └── workflows/
        └── gist-crud.yml
```

### Existing scripts

`gist_client.py`

A reusable Python client for the GitHub Gist API.

Implemented operations:

- Create a Gist.
- Retrieve a Gist.
- Update a Gist, supporting file additions, edits and deletions.
- Delete a Gist.

It uses the `GIST_TOKEN` environment variable.

`sync_content.py`

Already working. It:

- Discovers root-level content folders.
- Generates Hugo front matter.
- Rewrites relative image references to `/images/...`.
- Copies images into `site/static/images/`.
- Writes processed Markdown into `site/content/`.
- Removes previously generated content and image folders before syncing.

It is invoked from the repository root:

```
python .github/scripts/sync_content.py
```

It also supports:

```
python .github/scripts/sync_content.py --list
```

GitHub Actions

The manually triggered Gist CRUD proof of concept has been implemented and tested. It uses the Python client and supports create, read, update and delete operations.

The Python import issue has been resolved by setting:

```
PYTHONPATH: ${{ github.workspace }}/.github/scripts
```

The client is now imported directly:

```
from gist_client import GitHubGistClient, GitHubGistError
```

## 2. Agreed architecture

The central decision is to keep the responsibilities separated.

| Component         | Responsibility                                                         |
| ----------------- | ---------------------------------------------------------------------- |
| `gist_client.py`  | Low-level GitHub API operations                                        |
| `gist_sync.py`    | Discover code files, compare local and remote state, synchronize Gists |
| `gist.yml`        | Per-dev-log Gist metadata                                              |
| `sync_content.py` | Publish content and rewrite code references                            |
| GitHub Actions    | Orchestrate synchronization and publishing                             |

The intended processing pipeline:

GitHub Action

Manual full sync or automatic update sync

gist_sync.py

Discover code, create/update Gists, write metadata

sync_content.py

Copy content, rewrite image references and Gist references

Hugo site

Processed Markdown and published assets

Persist metadata

Commit changed gist.yml files to the repository

The original Markdown files are never modified.

## 3. Gist organization and metadata

### One Gist per dev log

Each dev log gets one Gist containing all its `.gd` files.

The code files will be located directly in the top level of the corresponding asset folder. No recursive discovery is needed.

Example:

```
gamedev/
    nanoswarm/
        devlog_1/
            some_image.png
            movement_controller.gd
            targeting.gd
            gist.yml
```

### Metadata file

Each asset folder gets its own `gist.yml`.

Proposed initial format:

```
id: "abc123..."
url: "https://gist.github.com/yourusername/abc123..."
description: "NanoSwarm - Devlog #1"
```

Decisions:

- Metadata belongs alongside the dev log's assets.
- The Gist ID is the essential identifier.
- The local `.gd` files are the source of truth.
- The Gist's contents should be reconciled against those local files.
- No automatic Gist deletion when a folder becomes empty.
- Metadata should be committed back to Git when changed.
- GitHub username should be stored centrally, not repeated in every metadata file.

Implementation note: Python's standard library has no YAML parser. Add PyYAML to the GitHub Actions environment to read and write `gist.yml`.

## 4. Markdown reference replacement

This is an important correction from the earlier discussion:

The actual Markdown reference is a normal Markdown link, without a blockquote.

For example, the original article contains:

```
[Movement controller](devlog_10/movement_controller.gd)
```

During the publishing process, `sync_content.py` transforms it into:

```
{{< gist user="YOUR_GITHUB_USERNAME" id="GIST_ID" file="movement_controller.gd" >}}
```

This uses your existing Hugo `gist` shortcode.

### Replacement rules

- Only `.gd` references are replaced.
- The original Markdown is never changed.
- The transformation happens only in the copied Markdown under `site/content/`.
- The local file must exist.
- The corresponding `gist.yml` must exist and contain a valid Gist ID.
- If validation fails, print a warning and leave the original reference unchanged.
- The replacement uses the filename, not the full local path, as the Gist's `file` parameter.

### Where to implement it

In `sync_content.py`, introduce a new function:

```
def rewrite_gist_refs(content: str, src_file: Path) -> str:    ...
```

And integrate it into `sync_markdown()`:

```
body = src.read_text(encoding="utf-8")body = rewrite_image_refs(body, src)body = rewrite_gist_refs(body, src)
```

The new function should:

1. Find Markdown links pointing to `.gd` files.
2. Resolve their paths relative to the original Markdown file.
3. Identify the corresponding dev-log asset folder.
4. Load its `gist.yml`.
5. Validate the local file and metadata.
6. Replace the Markdown link with the Hugo shortcode.

An additional safety check should ensure the resolved file is directly inside its expected asset folder, preventing `../` references from accidentally accessing another dev log's files.

## 5. Gist synchronization script

New file:

```
.github/scripts/gist_sync.py
```

This script will reuse `gist_client.py`.

It should be responsible for:

- Discovering dev-log asset folders.
- Finding top-level `.gd` files.
- Loading and updating `gist.yml`.
- Comparing local files against the remote Gist.
- Creating Gists when necessary.
- Updating existing Gists when contents differ.
- Removing remote files that no longer exist locally.
- Avoiding unnecessary API calls when nothing has changed.

### Synchronization logic

For each dev log:

```
Does the folder contain .gd files?
    |
    +-- No --> Do not create or delete a Gist.
    |
    +-- Yes
          |
          v
    Does gist.yml exist?
          |
          +-- No --> Create Gist and write metadata.
          |
          +-- Yes
                 |
                 v
           Retrieve existing Gist
                 |
                 v
           Compare local and remote files
                 |
                 +-- No differences --> Skip update
                 |
                 +-- Differences --> Update Gist
```

A missing or invalid remote Gist ID should be handled explicitly. The script should report the error rather than silently create a replacement Gist, which could leave duplicate Gists behind.

## 6. Two synchronization modes

Both modes use the same `gist_sync.py` synchronization logic. They differ only in how they select which dev logs to process.

### Mode A — Full sync

Manual execution

Triggered manually through GitHub Actions.

It should:

1. Discover all dev-log asset folders.
2. Check every folder for `.gd` files.
3. Create missing Gists.
4. Update existing Gists when necessary.
5. Write/update metadata files.
6. Run `sync_content.py`.
7. Continue with the existing Hugo publishing/deployment process.
8. Commit changed metadata files back to the repository.

This serves as the reconciliation and recovery mechanism.

### Mode B — Update sync

Automatic Git push

Triggered when changes are pushed to the repository.

Instead of scanning every dev log, it should:

1. Identify changed files between the previous and current commit.
2. Determine which dev-log asset folders are affected.
3. Include changes to both `.gd` files and Markdown references.
4. Synchronize only the affected dev logs.
5. Run `sync_content.py`.
6. Continue with the existing publishing/deployment process.
7. Commit changed metadata files back to the repository.

Important cases to handle:

- New `.gd` file: add it to the Gist.
- Modified `.gd` file: update it.
- Deleted `.gd` file: remove it from the Gist.
- Renamed `.gd` file: treat as deletion plus addition.
- New dev log: initialize its Gist if code files exist.
- Markdown-only change: include the relevant dev log if its references need to be processed.
- Multiple commits in one push: compare the complete push range, not just the latest commit.
- Missing previous commit or unavailable history: fall back to full sync.

Use sufficient Git history in the workflow, such as:

```
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

## 7. GitHub Actions changes

The existing CRUD proof-of-concept workflow should remain available as a testing/debugging tool until the new system is stable.

Introduce a separate workflow, for example:

```
.github/workflows/sync-content.yml
```

It should support both triggers:

```
on:
  push:
  workflow_dispatch:
```

The manual trigger should select full sync.

The push trigger should select update sync.

### Environment and permissions

The workflow will need:

```
permissions:
  contents: write
```

And:

```
env:
  PYTHONPATH: ${{ github.workspace }}/.github/scripts
  GIST_TOKEN: ${{ secrets.GIST_TOKEN }}
```

Install dependencies:

```
- name: Install dependencies
  run: pip install PyYAML
```

The exact Python version should match the version used by your existing CRUD action (currently Python 3.12).

### Workflow execution order

```
Checkout repository
        |
        v
Set up Python
        |
        v
Install dependencies
        |
        v
Determine sync mode
        |
        v
Run gist_sync.py
        |
        v
Run sync_content.py
        |
        v
Build/deploy Hugo site
        |
        v
Commit changed gist.yml files
```

One important deployment consideration: if Hugo deployment currently runs in a separate workflow triggered by a push, the metadata commit made with the standard `GITHUB_TOKEN` will not normally trigger that workflow. Therefore, the new workflow should invoke the build/deployment process itself, or integrate with your existing deployment workflow in another way.

Metadata commits should be conditional, so no commit is created when nothing changed.

# 8. Step-by-step implementation roadmap

This is the order I'd follow when resuming. Each step should be implemented and tested before moving to the next.

## Phase 1 — Gist synchronization logic

Foundation already working

Step 1.1 — Review existing Gist client

- Confirm `gist_client.py` is in `.github/scripts/`.
- Confirm CRUD operations still work.
- No architectural changes expected.

Step 1.2 — Create `gist_sync.py`

- Add dev-log discovery.
- Find top-level `.gd` files.
- Load/write `gist.yml`.
- Implement full synchronization.
- Reuse the existing client.

Step 1.3 — Test locally

- Test Gist creation.
- Test editing a file.
- Test adding a file.
- Test deleting a file.
- Test unchanged files (no API update).
- Test metadata persistence.
- Test invalid Gist IDs and empty folders.

## Phase 2 — Hugo content integration

Pending

Step 2.1 — Modify `sync_content.py`

- Add `rewrite_gist_refs()`.
- Read per-dev-log metadata.
- Replace `.gd` Markdown links with Hugo shortcodes.
- Preserve original Markdown.
- Add warnings for invalid references.

Step 2.2 — Test publishing transformation

- Create a test dev log with multiple `.gd` files.
- Add references to those files in Markdown.
- Run `sync_content.py`.
- Inspect generated Markdown under `site/content/`.
- Confirm shortcode output is correct.
- Confirm images and existing front matter still work.
- Confirm original Markdown is unchanged.

## Phase 3 — Full sync GitHub Action

Pending

Step 3.1 — Create the new workflow

- Add manual `workflow_dispatch`.
- Configure checkout and Python.
- Install PyYAML.
- Configure `GIST_TOKEN` and `PYTHONPATH`.

Step 3.2 — Run full synchronization

- Run `gist_sync.py` in full mode.
- Run `sync_content.py`.
- Integrate Hugo build/deployment.
- Commit changed `gist.yml` files.

Step 3.3 — Test manually

- First execution creates Gists.
- Second execution makes no unnecessary changes.
- Modify code and run again.
- Delete code and run again.
- Verify metadata commits.

## Phase 4 — Incremental synchronization

Pending

Step 4.1 — Add Git change detection

- Determine previous/current commits.
- Identify affected dev-log folders.
- Handle added, modified, deleted and renamed files.
- Include Markdown-only changes.

Step 4.2 — Add update mode to `gist_sync.py`

- Accept affected folders as input.
- Reuse the same synchronization function as full mode.

Step 4.3 — Enable push trigger

- Configure automatic update sync.
- Fall back to full sync when the Git diff cannot be determined.
- Test multiple commits in one push.
- Verify metadata commits do not trigger an infinite loop.

## Phase 5 — Cleanup and hardening

Pending

- Add useful logging and GitHub Actions summaries.
- Add dry-run support if useful.
- Ensure failures stop the publishing process.
- Avoid concurrent sync runs using workflow concurrency controls.
- Document how to recover a missing or deleted Gist.
- Retain the manual full-sync action as a recovery mechanism.

## 9. Decisions deliberately left open

These are not blockers for the initial implementation, but should be revisited when relevant.

| Topic                    | Current position                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| Gist visibility          | Reuse the existing client's visibility option; settle the default before implementation                 |
| Gist description         | Generate from the dev-log identity                                                                      |
| Empty Gist folders       | Don't automatically delete remote Gists                                                                 |
| Missing remote Gist      | Report an error; don't silently recreate                                                                |
| Duplicate code filenames | Not an issue under the one-Gist-per-dev-log, top-level-only rule                                        |
| YAML library             | PyYAML                                                                                                  |
| GitHub username          | Central configuration                                                                                   |
| Binary files             | Only `.gd` files are synchronized                                                                       |
| Workflow concurrency     | Add during hardening                                                                                    |
| Hugo deployment          | Integrate into the new workflow rather than relying on a push-triggered workflow after metadata commits |

## 10. First task when resuming

I'd resume at Phase 1, Step 1.2: implementing `gist_sync.py`.

The first implementation should focus exclusively on full synchronization. No Git diff logic, no new GitHub Action, and no changes to `sync_content.py` yet.

That gives us a manageable test:

1. Create one test asset folder with two `.gd` files.
2. Run the script.
3. Confirm it creates one Gist and one `gist.yml`.
4. Modify one file and add another.
5. Run again and confirm the same Gist is updated.
6. Run once more without changes and confirm no API update occurs.

Once that works, we move to the publishing transformation.

The guiding principle for the whole project: each stage should be independently testable, and we should only connect the stages once their individual behavior is reliable. That keeps the automation maintainable and avoids turning your weekly publishing routine into another project of its own.