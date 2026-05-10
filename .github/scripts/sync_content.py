#!/usr/bin/env python3
"""
sync_content.py
───────────────
Scans the repo root for content folders, infers Hugo front-matter
(title, date, series) for every markdown file found, and writes the
result into site/content/.  Images and other assets are copied unchanged.

A "content folder" is any root-level directory that is NOT in EXCLUDED_DIRS
below.  To add a new section (e.g. "writing/"), just create the folder and
start writing — nothing else needs updating.

Usage (always run from the repo root):
    python .github/scripts/sync_content.py          # sync all
    python .github/scripts/sync_content.py --list   # print discovered folders, one per line
"""

import os
import re
import sys
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

# Directories at the repo root that are NOT content folders.
# Everything else is treated as a content source automatically.
EXCLUDED_DIRS = {
    "site",        # the Hugo project itself
    ".github",     # CI / scripts
    ".git",        # git internals
    ".vscode",     # editor config
    "node_modules",
}

SITE_CONTENT = Path("site") / "content"

# Extensions copied into site/content/ without modification
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4"}

# ──────────────────────────────────────────────────────────────────────────────


def discover_content_folders(root: Path) -> list[Path]:
    """
    Return all root-level directories that should be treated as content sources.
    Excludes dotfolders and anything listed in EXCLUDED_DIRS.
    """
    folders = []
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue
        if item.name in EXCLUDED_DIRS:
            continue
        folders.append(item)
    return folders


def get_first_commit_date(filepath: Path) -> str:
    """Return the ISO-8601 datetime of the first git commit for this file."""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", str(filepath)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return datetime.now(timezone.utc).isoformat()

    if result.returncode != 0:
        return datetime.now(timezone.utc).isoformat()

    lines = result.stdout.strip().splitlines()
    if lines:
        return lines[0]
    return datetime.now(timezone.utc).isoformat()


def stem_to_title(stem: str) -> str:
    """
    'Devlog1-starting'  → 'Devlog1 Starting'
    'my_cool_project'   → 'My Cool Project'
    """
    return re.sub(r"[-_]+", " ", stem).strip().title()


def build_frontmatter(title: str, date: str, series: str | None) -> str:
    lines = ["+++"]
    lines.append(f'title  = "{title}"')
    lines.append(f'date   = "{date}"')
    if series:
        lines.append(f'series = ["{series}"]')
    lines.append("+++")
    return "\n".join(lines) + "\n\n"


def sync_markdown(src: Path) -> None:
    """Inject front-matter and write to the mirrored site/content/ path."""
    parts = src.parts  # e.g. ("gamedev", "nanoswarm", "Devlog1-starting.md")

    # Series: the first subfolder below the category, if one exists
    series = parts[1] if len(parts) >= 3 else None

    frontmatter = build_frontmatter(
        title=stem_to_title(src.stem),
        date=get_first_commit_date(src),
        series=series,
    )
    dest = SITE_CONTENT / Path(*parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(frontmatter + src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  ✔  {src}  →  {dest}")


def copy_asset(src: Path) -> None:
    dest = SITE_CONTENT / Path(*src.parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  ✔  {src}  →  {dest}  [asset]")


def wipe_generated_folders(folders: list[Path]) -> None:
    """Remove previously generated output to prevent stale files."""
    for folder in folders:
        target = SITE_CONTENT / folder.name
        if target.exists():
            shutil.rmtree(target)
            print(f"  🗑  cleared {target}/")


def sync_all() -> None:
    root = Path(".")
    folders = discover_content_folders(root)

    if not folders:
        print("No content folders found — nothing to sync.")
        return

    print(f"→ Discovered content folders: {[f.name for f in folders]}")

    print("── Clearing stale output ─────────────────────────────────────────")
    wipe_generated_folders(folders)

    print("── Syncing ───────────────────────────────────────────────────────")
    for folder in folders:
        items = list(folder.rglob("*"))
        if not items:
            print(f"  (skip) {folder.name}/ is empty")
            continue
        for item in items:
            if not item.is_file():
                continue
            if item.suffix == ".md":
                sync_markdown(item)
            elif item.suffix.lower() in ASSET_EXTENSIONS:
                copy_asset(item)

    print("── Done ──────────────────────────────────────────────────────────")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    if "--list" in sys.argv:
        # Print discovered folder names, space-separated — used by the workflow
        folders = discover_content_folders(Path("."))
        print(" ".join(f.name for f in folders))
    else:
        sync_all()
