#!/usr/bin/env bash
# Independent code review with the OpenAI Codex CLI (work policy rule 5).
#
#   scripts/codex_review.sh                # review uncommitted changes (staged, unstaged, untracked)
#   scripts/codex_review.sh <commit-sha>   # review one commit
#
# Feeds the diff, CLAUDE.md and AGENTS.md to Codex over stdin. The built-in `codex exec review` is
# not used because on Windows its sandbox rejects the shell commands it needs to read the repo
# (verified 2026-09-10, codex-cli 0.154); piping the payload needs no shell at all. Read-only sandbox.
# Exit status: 0 = review produced; 2 = nothing to review; 3 = collection failed or Codex did not answer.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 3
fail() { echo "codex_review: $*" >&2; exit 3; }
[ -r AGENTS.md ] && [ -r CLAUDE.md ] || fail "AGENTS.md or CLAUDE.md missing: the reviewer brief is required"
if [ $# -eq 0 ]; then
  staged=$(git diff --cached) || fail "git diff --cached failed"      # index vs HEAD: what a commit would take
  unstaged=$(git diff) || fail "git diff failed"                       # worktree vs index
  diff="$staged"$'
'"$unstaged"
  list=$(mktemp) || fail "mktemp failed"
  git ls-files --others --exclude-standard -z > "$list" || fail "git ls-files failed"
  # NUL-delimited names are read from a file: command substitution would drop the NULs.
  while IFS= read -r -d '' f; do
    d=$(git diff --no-index -- /dev/null "$f"); rc=$?
    [ "$rc" -le 1 ] || fail "could not diff untracked file: $f"
    diff="$diff"$'\n'"$d"
  done < "$list"
  rm -f "$list"
  title="uncommitted changes"
else
  diff=$(git show "$1") || fail "git show $1 failed"
  title="commit $1"
fi
[ -n "${diff//[[:space:]]/}" ] || { echo "nothing to review"; exit 2; }
out=$({
  echo "Review the following ${title} against the project brief (AGENTS.md) and the project rules (CLAUDE.md) that follow the diff. You cannot read the repository; everything you need is in this message."
  echo "Output: findings first, most severe first, one per line: severity | file:line | what is wrong | what to do."
  echo "Then a two-line verdict: merge / fix first. Under 400 words unless the diff is large."
  echo; echo "=== diff ==="; echo "$diff"
  echo; echo "=== AGENTS.md ==="; cat AGENTS.md
  echo; echo "=== CLAUDE.md ==="; cat CLAUDE.md
} | codex exec --sandbox read-only - 2>&1)
rc=$?
answer=$(sed -n '/^codex$/,$p' <<<"$out" | grep -v -E "^codex$|^mcp:|ERROR codex_core|^tokens used")
if [ "$rc" -ne 0 ] || [ -z "${answer//[[:space:]]/}" ]; then
  echo "Codex review unavailable (exit $rc). Full output:" >&2
  echo "$out" >&2
  exit 3
fi
echo "$answer"
