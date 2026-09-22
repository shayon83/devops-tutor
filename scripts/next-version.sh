#!/usr/bin/env bash
# Derives the next semantic version from Conventional Commits since the last
# release tag, and prints it (without a leading "v") on stdout.
#
#   <type>!: ... or a "BREAKING CHANGE:" body line  -> major
#   feat: ...                                       -> minor
#   anything else                                   -> patch
#
# Usage:
#   scripts/next-version.sh [auto|patch|minor|major]
#
# Exits 1 with a message when there is nothing to release, so the release
# workflow stops instead of cutting an empty tag.
set -euo pipefail

bump=${1:-auto}
case "$bump" in
  auto | patch | minor | major) ;;
  *)
    echo "usage: $0 [auto|patch|minor|major]" >&2
    exit 2
    ;;
esac

# Only tags that look like a version. `--sort=-v:refname` puts the highest
# first, so a tag made out of order cannot rewind the series.
last_tag=$(git tag --list 'v[0-9]*' --sort=-v:refname | head -n1)

if [ -z "$last_tag" ]; then
  base="0.0.0"
  range=""
else
  base="${last_tag#v}"
  range="${last_tag}..HEAD"
fi

# Tolerate a two-component tag such as the repo's existing v1.0.
case "$base" in
  *.*.*) ;;
  *.*) base="${base}.0" ;;
  *) base="${base}.0.0" ;;
esac

IFS='.' read -r major minor patch <<<"$base"

# %B is the whole message, so a "BREAKING CHANGE:" in the body is visible too.
# No separator is needed: every pattern below is line-anchored.
if [ -n "$range" ]; then
  commits=$(git log --format='%B' "$range")
else
  commits=$(git log --format='%B')
fi

if [ -z "${commits//[$'\n'[:space:]]/}" ]; then
  echo "nothing to release: no commits since ${last_tag:-the start of history}" >&2
  exit 1
fi

if [ "$bump" = "auto" ]; then
  if grep -qE '^[a-z]+(\([^)]*\))?!:' <<<"$commits" || grep -qE '^BREAKING[ -]CHANGE:' <<<"$commits"; then
    bump=major
  elif grep -qE '^feat(\([^)]*\))?:' <<<"$commits"; then
    bump=minor
  else
    bump=patch
  fi
fi

case "$bump" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
esac

echo "${major}.${minor}.${patch}"
