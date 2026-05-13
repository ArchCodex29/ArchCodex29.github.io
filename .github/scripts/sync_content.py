#!/usr/bin/env python3
"""
sync_content.py
───────────────
Scans the repo root for content folders, infers Hugo front-matter
(title, date, series) for every markdown file found, rewrites relative
image references to absolute static paths, copies images to
site/static/images/, and writes the processed markdown to site/content/.

A "content folder" is any root-level directory that is NOT in EXCLUDED_DIRS.
To add a new section (e.g. "writing/"), just create the folder and start
writing — nothing else needs updating.

Usage (always run from the repo root):
    python .github/scripts/sync_content.py          # sync all
    python .github/scripts/sync_content.py --list   # print discovered folders, space-separated
"""

import os
import re
import sys
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

EXCLUDED_DIRS = {
    "site",
    ".github",
    ".git",
    ".vscode",
    "node_modules",
}

SITE_CONTENT       = Path("site") / "content"
SITE_STATIC_IMAGES = Path("site") / "static" / "images"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4"}

# Matches standard markdown image syntax: ![alt text](path/to/image.png)
# Also captures optional title:           ![alt](path "title")
MD_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(\s+"[^"]*")?\)')

# ──────────────────────────────────────────────────────────────────────────────


def discover_content_folders(root: Path) -> list[Path]:
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
    result = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", str(filepath)],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    if lines:
        return lines[0]
    return datetime.now(timezone.utc).isoformat()


def stem_to_title(stem: str) -> str:
    return re.sub(r"[-_]+", " ", stem).strip().title()


def build_frontmatter(title: str, date: str, series: str | None, draft: str | None) -> str:
    lines = ["+++"]
    lines.append(f'title  = "{title}"')
    lines.append(f'date   = "{date}"')
    if series:
        lines.append(f'series = ["{series}"]')
    if draft:
        lines.append(f'draft  = true')
    lines.append("+++")
    return "\n".join(lines) + "\n\n"


def copy_image(src: Path) -> None:
    """
    Copy an image to site/static/images/, mirroring the source path.

    gamedev/nanoswarm/cover.png
        → site/static/images/gamedev/nanoswarm/cover.png
        → served at /images/gamedev/nanoswarm/cover.png
    """
    dest = SITE_STATIC_IMAGES / Path(*src.parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  ✔  {src}  →  {dest}  [image]")


def rewrite_image_refs(content: str, src_file: Path) -> str:
    """
    Rewrite relative image references in markdown to absolute /images/... URLs
    and copy the image files to site/static/images/.

    Example (file is gamedev/nanoswarm/devlog0.md):
        ![cover](cover.png)
        → ![cover](/images/gamedev/nanoswarm/cover.png)

    References that are already absolute URLs or absolute paths are left alone.
    Missing files emit a warning and are left unchanged.
    """
    repo_root = Path(".").resolve()

    def replace(match: re.Match) -> str:
        alt   = match.group(1)
        ref   = match.group(2)
        title = match.group(3) or ""

        # Leave absolute URLs and already-absolute paths untouched
        if ref.startswith(("http://", "https://", "/")):
            return match.group(0)

        # Resolve relative to the markdown file's directory
        img_src = (src_file.parent / ref).resolve()

        try:
            repo_relative = img_src.relative_to(repo_root)
        except ValueError:
            print(f"  ⚠  image path escapes repo root, skipping: {ref}")
            return match.group(0)

        if not img_src.exists():
            print(f"  ⚠  image not found, reference left unchanged: {img_src}")
            return match.group(0)

        # Copy the image to site/static/images/
        copy_image(repo_relative)

        # Rewrite the reference to an absolute URL
        new_url = "/images/" + "/".join(repo_relative.parts)
        return f"![{alt}]({new_url}{title})"

    return MD_IMAGE_RE.sub(replace, content)


def sync_markdown(src: Path) -> None:
    """
    Process one markdown file:
      1. Infer and prepend front-matter
      2. Rewrite relative image refs → absolute /images/... URLs
      3. Copy referenced images to site/static/images/
      4. Write the result to site/content/
    """
    parts  = src.parts
    series = parts[1] if len(parts) >= 3 else None
    
    is_draft = src.suffixes == ['.draft', '.md']

    stem = src.name.removesuffix('.draft.md') if is_draft else src.stem

    # For _index.md, use the containing folder name as the title
    if src.name == "_index.md":
        title = stem_to_title(src.parent.name)
    else:
        title = stem_to_title(stem)

    frontmatter = build_frontmatter(
        title=title,
        date=get_first_commit_date(src),
        series=series,
        draft=is_draft
    )

    body = src.read_text(encoding="utf-8")
    body = rewrite_image_refs(body, src)

    # dest = SITE_CONTENT / Path(*parts)
    dest_name = src.name.removesuffix('.draft.md') + '.md' if is_draft else src.name
    dest = SITE_CONTENT / Path(*parts[:-1]) / dest_name

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(frontmatter + body, encoding="utf-8")
    print(f"  ✔  {src}  →  {dest}")


def wipe_generated_folders(folders: list[Path]) -> None:
    """
    Remove previously generated output under both site/content/ and
    site/static/images/ so stale files don't survive renames or deletes.
    """
    for folder in folders:
        for target in [
            SITE_CONTENT       / folder.name,
            SITE_STATIC_IMAGES / folder.name,
        ]:
            if target.exists():
                shutil.rmtree(target)
                print(f"  🗑  cleared {target}/")


def sync_all() -> None:
    root    = Path(".")
    folders = discover_content_folders(root)

    if not folders:
        print("No content folders found — nothing to sync.")
        return

    print(f"→ Discovered: {[f.name for f in folders]}")

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
                # Handles both content writing and referenced-image copying
                sync_markdown(item)
            elif item.suffix.lower() in IMAGE_EXTENSIONS:
                # Also copy images that aren't referenced in any markdown file
                # (e.g. assets used in front-matter, og:image, future use)
                copy_image(item)

    print("── Done ──────────────────────────────────────────────────────────")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    if "--list" in sys.argv:
        folders = discover_content_folders(Path("."))
        print(" ".join(f.name for f in folders))
    else:
        sync_all()
