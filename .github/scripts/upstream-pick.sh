#!/usr/bin/env bash
# Cherry-pick the pending upstream commits that apply cleanly onto the
# current branch (started from the fork's main). Used by upstream-sync.yml.
#
# Usage: upstream-pick.sh <fork-ref> <upstream-ref> <upstream-url>
#
# Pending means what the Upstream watch lists: no commit with the same
# patch-id on the fork, no "(cherry picked from commit <sha>)" trailer naming
# it, not in .github/upstream-ignore.txt, not a merge commit.
# - Release commits ("chore: Release v...") and commits that only touch
#   README.md or .github/workflows/ are not picked; they are added to
#   .github/upstream-ignore.txt instead.
# - README.md and .github/workflows/ changes are left out of every pick: the
#   fork has its own README, and GITHUB_TOKEN cannot push workflow changes.
# - A commit that does not apply cleanly is skipped and stays pending.
# Writes picked.md and skipped.md (Markdown lists) in the current directory.
set -euo pipefail

FORK=$1
UPSTREAM=$2
UPSTREAM_URL=$3
IGNORE=.github/upstream-ignore.txt
KEEP_FORK=(README.md .github/workflows)

{
  git log "$FORK" --format=%B |
    sed -n 's/.*(cherry picked from commit \([0-9a-f]\{40\}\)).*/\1/p'
  if [ -f "$IGNORE" ]; then
    grep -oE '^[0-9a-f]{40}' "$IGNORE" || true
  fi
} | sort -u >taken.txt

: >picked.md
: >skipped.md
: >ignored.txt

while read -r sha; do
  grep -qx "$sha" taken.txt && continue
  [ "$(git rev-list --no-walk --count --min-parents=2 "$sha")" = 0 ] || continue

  subject=$(git show -s --format=%s "$sha")
  line=$(git show -s --format="- [\`%h\`]($UPSTREAM_URL/commit/%H) %s" "$sha")

  case "$subject" in
    "chore: Release v"*)
      echo "$sha release ${subject#chore: Release }" | sed 's/ \[skip ci\]//' >>ignored.txt
      continue
      ;;
  esac

  if ! git cherry-pick --no-commit "$sha" >/dev/null 2>&1; then
    git reset -q --hard HEAD
    git cherry-pick --quit 2>/dev/null || true
    echo "$line (does not apply cleanly)" >>skipped.md
    continue
  fi

  dropped=false
  for path in "${KEEP_FORK[@]}"; do
    if ! git diff --cached --quiet -- "$path"; then
      dropped=true
      git restore --source=HEAD --staged --worktree -- "$path" 2>/dev/null ||
        { git rm -rq --cached -- "$path" && rm -rf -- "$path"; }
    fi
  done

  if git diff --cached --quiet; then
    git reset -q --hard HEAD
    echo "$sha README or workflows only: the fork keeps its own" >>ignored.txt
    continue
  fi

  {
    # Command substitution drops the message's trailing blank lines.
    printf '%s\n' "$(git show -s --format=%B "$sha")"
    echo
    if [ "$dropped" = true ]; then
      echo "Upstream README.md and workflow changes left out: the fork keeps its own."
      echo
    fi
    echo "(cherry picked from commit $sha)"
  } >msg.txt
  git commit -q --no-verify \
    --author="$(git show -s --format='%an <%ae>' "$sha")" \
    --date="$(git show -s --format=%aI "$sha")" \
    -F msg.txt
  rm -f msg.txt
  echo "$line" >>picked.md
done < <(git cherry "$FORK" "$UPSTREAM" | sed -n 's/^+ //p')

if [ -s ignored.txt ]; then
  {
    echo
    echo "# Added by the Upstream sync workflow."
    cat ignored.txt
  } >>"$IGNORE"
  git add "$IGNORE"
  git commit -q --no-verify -m "ci: Ignore upstream release and README-only commits"
fi
rm -f taken.txt ignored.txt
