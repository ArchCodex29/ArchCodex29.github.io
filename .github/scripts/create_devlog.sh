#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    printf 'Usage: %s <number> <title>\n' "$0" >&2
    exit 2
fi

number="$1"
title="$2"

if [[ ! "$number" =~ ^[0-9]+$ ]]; then
    printf 'Devlog number must contain digits only: %s\n' "$number" >&2
    exit 2
fi

if [[ -z "${title//[[:space:]]/}" || "$title" =~ [[:cntrl:]] ]]; then
    printf 'Devlog title must be a non-empty single line.\n' >&2
    exit 2
fi

if [[ "$title" =~ ^[[:space:]] || "$title" =~ [[:space:]]$ || "$title" == *. ]]; then
    printf 'Devlog title cannot start or end with whitespace or end with a period.\n' >&2
    exit 2
fi

case "$title" in
    *'<'*|*'>'*|*':'*|*'"'*|*'/'*|*'\'*|*'|'*|*'?'*|*'*'*)
        printf 'Devlog title contains a character that is unsafe in a filename.\n' >&2
        exit 2
        ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../.." && pwd)"
content_dir="$repo_root/gamedev/nanoswarm"
template_path="$content_dir/Devlog.md.template"
post_path="$content_dir/Devlog#$number - $title.md"
asset_path="$content_dir/Devlog_$number"

if [[ ! -f "$template_path" ]]; then
    printf 'Template not found: %s\n' "$template_path" >&2
    exit 1
fi

if [[ -e "$post_path" || -L "$post_path" || -e "$asset_path" || -L "$asset_path" ]]; then
    printf 'Refusing to overwrite an existing post or asset folder for Devlog #%s.\n' "$number" >&2
    exit 1
fi

temporary_path="$(mktemp "$content_dir/.Devlog-$number.XXXXXX")"
trap 'rm -f -- "$temporary_path"' EXIT
{
    printf '# %s\n' "$title"
    tail -n +2 "$template_path"
} > "$temporary_path"

mkdir -- "$asset_path"
if ! mv -- "$temporary_path" "$post_path"; then
    rmdir -- "$asset_path"
    printf 'Could not create post: %s\n' "$post_path" >&2
    exit 1
fi
trap - EXIT

printf 'Created %s\nCreated %s/\n' "$post_path" "$asset_path"
