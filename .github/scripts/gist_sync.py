#!/usr/bin/env python3
"""Synchronize NanoSwarm dev-log code files with GitHub Gists."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath

import yaml

from gist_client import GitHubGistClient, GitHubGistError


REPO_ROOT = Path(__file__).resolve().parents[2]
GIST_ID_RE = re.compile(r"^[0-9a-f]{32}$")
DEVLOG_DIR_RE = re.compile(r"^Devlog_(\d+)$")
COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
CHANGED_CODE_RE = re.compile(
    r"^gamedev/nanoswarm/Devlog_(\d+)/[^/]+\.gd$"
)
CHANGED_MARKDOWN_RE = re.compile(
    r"^gamedev/nanoswarm/Devlog#(\d+) - .+\.md$"
)


class GistSyncError(Exception):
    """Raised when local and remote Gist state cannot be reconciled safely."""


def discover_devlog_dirs(root: Path = REPO_ROOT) -> list[tuple[int, Path]]:
    """Return NanoSwarm dev-log asset directories in numeric order."""
    asset_root = root / "gamedev" / "nanoswarm"
    if not asset_root.is_dir():
        return []

    devlogs = []
    for path in asset_root.iterdir():
        match = DEVLOG_DIR_RE.fullmatch(path.name)
        if path.is_dir() and match:
            devlogs.append((int(match.group(1)), path))
    return sorted(devlogs, key=lambda item: (item[0], item[1].name))


def get_devlog_description(devlog_number: int, root: Path = REPO_ROOT) -> str:
    """Find the matching Markdown title used as the Gist description."""
    markdown_root = root / "gamedev" / "nanoswarm"
    matches = sorted(markdown_root.glob(f"Devlog#{devlog_number} - *.md"))
    if len(matches) != 1:
        if not matches:
            detail = "no matching Markdown file"
        else:
            detail = f"multiple matching Markdown files: {matches}"
        raise GistSyncError(
            f"Cannot determine description for Devlog_{devlog_number}: {detail}."
        )

    stem = matches[0].name.removesuffix(".md").removesuffix(".draft")
    return stem


def read_local_files(devlog_dir: Path) -> dict[str, str]:
    """Read top-level GDScript files, excluding nested files."""
    files = {}
    for path in sorted(devlog_dir.glob("*.gd")):
        if path.is_file():
            files[path.name] = path.read_text(encoding="utf-8")
    return files


def load_metadata(metadata_path: Path) -> dict[str, str]:
    try:
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise GistSyncError(f"Could not read {metadata_path}: {error}") from error

    if not isinstance(metadata, dict):
        raise GistSyncError(f"Invalid Gist metadata in {metadata_path}.")

    gist_id = metadata.get("id")
    url = metadata.get("url")
    description = metadata.get("description")
    if not isinstance(gist_id, str) or not GIST_ID_RE.fullmatch(gist_id):
        raise GistSyncError(f"Invalid Gist ID in {metadata_path}.")
    if not isinstance(url, str) or not url.strip():
        raise GistSyncError(f"Missing Gist URL in {metadata_path}.")
    if not isinstance(description, str) or not description.strip():
        raise GistSyncError(f"Missing Gist description in {metadata_path}.")

    return {"id": gist_id, "url": url, "description": description}


def write_metadata(metadata_path: Path, metadata: dict[str, str]) -> None:
    metadata_path.write_text(
        yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def get_remote_files(gist: dict, gist_id: str) -> dict[str, str]:
    files = gist.get("files")
    if not isinstance(files, dict):
        raise GistSyncError(f"Gist {gist_id} returned an invalid files mapping.")

    remote_files = {}
    for filename, details in files.items():
        if not isinstance(details, dict) or details.get("truncated"):
            raise GistSyncError(
                f"Gist {gist_id} has incomplete content for {filename}."
            )
        content = details.get("content")
        if not isinstance(content, str):
            raise GistSyncError(
                f"Gist {gist_id} has no complete content for {filename}."
            )
        remote_files[filename] = content
    return remote_files


def sync_devlog(
    devlog_number: int,
    devlog_dir: Path,
    root: Path,
    client: GitHubGistClient,
) -> str:
    local_files = read_local_files(devlog_dir)
    if not local_files:
        print(f"Skip {devlog_dir}: no top-level .gd files.")
        return "skipped"

    description = get_devlog_description(devlog_number, root)
    metadata_path = devlog_dir / "gist.yml"

    if not metadata_path.exists():
        gist = client.create_gist(description, local_files, public=False)
        gist_id = gist.get("id") if isinstance(gist, dict) else None
        url = gist.get("html_url") if isinstance(gist, dict) else None
        if not isinstance(gist_id, str) or not GIST_ID_RE.fullmatch(gist_id):
            raise GistSyncError(f"GitHub returned an invalid ID for {devlog_dir}.")
        if not isinstance(url, str) or not url.strip():
            raise GistSyncError(f"GitHub returned no URL for Gist {gist_id}.")

        write_metadata(metadata_path, {
            "id": gist_id,
            "url": url,
            "description": description,
        })
        print(f"Created Gist {gist_id} for {devlog_dir}.")
        return "created"

    metadata = load_metadata(metadata_path)
    gist = client.get_gist(metadata["id"])
    if not isinstance(gist, dict):
        raise GistSyncError(f"GitHub returned invalid data for Gist {metadata['id']}.")

    remote_files = get_remote_files(gist, metadata["id"])
    add_files = {
        name: content for name, content in local_files.items()
        if name not in remote_files
    }
    edit_files = {
        name: content for name, content in local_files.items()
        if name in remote_files and content != remote_files[name]
    }
    delete_files = sorted(set(remote_files) - set(local_files))
    description_changed = gist.get("description") != description

    if not add_files and not edit_files and not delete_files and not description_changed:
        if metadata["description"] != description:
            metadata["description"] = description
            write_metadata(metadata_path, metadata)
        print(f"Unchanged Gist {metadata['id']} for {devlog_dir}.")
        return "unchanged"

    client.update_gist(
        metadata["id"],
        add_files=add_files,
        edit_files=edit_files,
        delete_files=delete_files,
        description=description if description_changed else None,
    )
    if metadata["description"] != description:
        metadata["description"] = description
        write_metadata(metadata_path, metadata)
    print(f"Updated Gist {metadata['id']} for {devlog_dir}.")
    return "updated"


def sync_devlogs(
    devlogs: list[tuple[int, Path]],
    root: Path,
    client: GitHubGistClient | None = None,
) -> dict[str, int]:
    if not any(read_local_files(path) for _, path in devlogs):
        print("No NanoSwarm dev-log .gd files found.")
        return {"created": 0, "updated": 0, "unchanged": 0, "skipped": len(devlogs)}

    if client is None:
        client = GitHubGistClient()

    summary = {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    for number, devlog_dir in devlogs:
        result = sync_devlog(number, devlog_dir, root, client)
        summary[result] += 1
    return summary


def sync_all(root: Path = REPO_ROOT, client: GitHubGistClient | None = None) -> dict[str, int]:
    """Synchronize all discovered NanoSwarm dev-log Gists."""
    return sync_devlogs(discover_devlog_dirs(root), root, client)


def get_changed_paths(root: Path, base: str | None, head: str | None) -> list[str]:
    """List paths changed across the complete push range."""
    if (
        not base
        or not head
        or not COMMIT_RE.fullmatch(base)
        or not COMMIT_RE.fullmatch(head)
        or set(base) == {"0"}
    ):
        raise GistSyncError("Push commit range is missing or unavailable.")

    result = subprocess.run(
        [
            "git", "diff", "--no-renames", "--name-only", "-z",
            base, head, "--", "gamedev/nanoswarm",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        path for path in result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        if path
    ]


def affected_devlog_numbers(changed_paths: list[str], root: Path) -> list[int]:
    """Select dev logs affected by code changes or existing Markdown edits."""
    affected = set()
    for changed_path in changed_paths:
        normalized_path = PurePosixPath(changed_path).as_posix()
        code_match = CHANGED_CODE_RE.fullmatch(normalized_path)
        if code_match:
            affected.add(int(code_match.group(1)))
            continue

        markdown_match = CHANGED_MARKDOWN_RE.fullmatch(normalized_path)
        if markdown_match and (root / Path(*PurePosixPath(normalized_path).parts)).is_file():
            affected.add(int(markdown_match.group(1)))
    return sorted(affected)


def sync_update(
    root: Path,
    base: str | None,
    head: str | None,
    client: GitHubGistClient | None = None,
) -> dict[str, int]:
    """Synchronize affected dev logs, falling back to full sync if needed."""
    try:
        changed_paths = get_changed_paths(root, base, head)
    except (GistSyncError, OSError, subprocess.CalledProcessError) as error:
        print(f"⚠  Could not determine push changes ({error}); falling back to full sync.")
        return sync_all(root, client)

    numbers = affected_devlog_numbers(changed_paths, root)
    if not numbers:
        print("No dev-log code or Markdown changes found in the push range.")
        return {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}

    asset_root = root / "gamedev" / "nanoswarm"
    devlogs = [(number, asset_root / f"Devlog_{number}") for number in numbers]
    return sync_devlogs(devlogs, root, client)


def write_github_summary(
    mode: str,
    summary: dict[str, int] | None = None,
    error: str | None = None,
) -> None:
    """Append a concise result to the Actions run summary when available."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = ["## Gist synchronization", "", f"- Mode: `{mode}`"]
    if error is not None:
        lines.extend([
            "- Result: **Failed**",
            "",
            "```text",
            error,
            "```",
        ])
    else:
        lines.extend([
            "- Result: **Succeeded**",
            "",
            "| Outcome | Count |",
            "| --- | ---: |",
        ])
        for outcome in ("created", "updated", "unchanged", "skipped"):
            lines.append(f"| {outcome.title()} | {(summary or {}).get(outcome, 0)} |")
        if mode == "update":
            lines.extend([
                "",
                "Update mode falls back to full sync if the push range is unavailable; "
                "see the job log for details.",
            ])

    try:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write("\n".join(lines) + "\n")
    except OSError as write_error:
        print(f"Could not write GitHub Actions summary: {write_error}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("full", "update"),
        default="full",
        help="Full reconciliation or only dev logs changed in a Git range.",
    )
    parser.add_argument("--base", help="Previous commit SHA for update mode.")
    parser.add_argument("--head", help="Current commit SHA for update mode.")
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (defaults to the root containing this script).",
    )
    args = parser.parse_args()

    try:
        root = args.root.resolve()
        if args.mode == "update":
            summary = sync_update(root, args.base, args.head)
        else:
            summary = sync_all(root)
    except (GistSyncError, GitHubGistError, ValueError) as error:
        print(f"Gist sync failed: {error}", file=sys.stderr)
        write_github_summary(args.mode, error=str(error))
        return 1

    print(f"Gist sync summary: {summary}")
    write_github_summary(args.mode, summary=summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())