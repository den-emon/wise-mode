#!/usr/bin/env bash
# =============================================================================
# ai_review.sh — Independent code review via claude -p
#
# Usage:
#   bash ai_review.sh [--diff-file <path>] [--context "<summary>"] [--lang <language>]
#
# If --diff-file is not provided, runs `git diff` in the current directory.
# Output: JSON review result to stdout.
#
# Requires: claude CLI (Claude Code)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

DIFF_FILE=""
CONTEXT="No additional context."
LANG="unknown"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --diff-file)  DIFF_FILE="$2"; shift 2 ;;
    --context)    CONTEXT="$2"; shift 2 ;;
    --lang)       LANG="$2"; shift 2 ;;
    *)            shift ;;
  esac
done

# --- Prerequisite check -------------------------------------------------------

if ! command -v claude &>/dev/null; then
  echo '{"error":"claude CLI not found","findings":[],"score":0}' >&2
  exit 1
fi

# --- Collect diff --------------------------------------------------------------

if [ -n "$DIFF_FILE" ] && [ -f "$DIFF_FILE" ]; then
  DIFF_CONTENT=$(cat "$DIFF_FILE")
else
  DIFF_CONTENT=$(git diff 2>/dev/null || git diff HEAD 2>/dev/null || echo "")
fi

if [ -z "$DIFF_CONTENT" ]; then
  echo '{"error":"No diff content found","findings":[],"score":0}' >&2
  exit 1
fi

# Truncate very large diffs to stay within context limits
DIFF_LINES=$(echo "$DIFF_CONTENT" | wc -l)
if [ "$DIFF_LINES" -gt 2000 ]; then
  DIFF_CONTENT=$(echo "$DIFF_CONTENT" | head -2000)
  DIFF_CONTENT="${DIFF_CONTENT}

... (truncated: ${DIFF_LINES} total lines. Review focused on first 2000 lines.)"
fi

# --- Load system prompt --------------------------------------------------------

PROMPT_FILE="${SKILL_DIR}/references/reviewer_prompt.md"

if [ ! -f "$PROMPT_FILE" ]; then
  echo '{"error":"reviewer_prompt.md not found","findings":[],"score":0}' >&2
  exit 1
fi

# Extract the content between ```text and ``` fences
SYSTEM_PROMPT=$(sed -n '/^```text$/,/^```$/p' "$PROMPT_FILE" | sed '1d;$d')

if [ -z "$SYSTEM_PROMPT" ]; then
  echo '{"error":"Failed to extract system prompt from reviewer_prompt.md","findings":[],"score":0}' >&2
  exit 1
fi

# --- Build message and invoke claude -p ----------------------------------------

USER_MSG="Review the following diff for a ${LANG} project.

Context: ${CONTEXT}

\`\`\`diff
${DIFF_CONTENT}
\`\`\`"

TMPFILE=$(mktemp /tmp/ai-review-XXXXXX.txt)
CLAUDE_ERR=$(mktemp /tmp/ai-review-err-XXXXXX.txt)
trap 'rm -f "$TMPFILE" "$CLAUDE_ERR"' EXIT INT TERM

echo "$USER_MSG" > "$TMPFILE"

RESPONSE=""

# Helper: emit a JSON error to stderr using python3 to safely escape strings
emit_error() {
  python3 -c "import json,sys; print(json.dumps({'error':sys.argv[1],'findings':[],'score':0}))" "$1" >&2
}

# Try --system-prompt first; fall back to inline prefix if unsupported
if RESPONSE=$(claude -p --system-prompt "$SYSTEM_PROMPT" < "$TMPFILE" 2>"$CLAUDE_ERR"); then
  : # success
else
  EXIT_CODE=$?
  STDERR_MSG=$(cat "$CLAUDE_ERR" 2>/dev/null || true)

  # Only fall back if the error looks like an unsupported-flag issue
  # For auth/network errors, fail immediately
  if echo "$STDERR_MSG" | grep -qi "auth\|unauthorized\|network\|connect\|timeout"; then
    emit_error "claude -p failed (exit ${EXIT_CODE}): ${STDERR_MSG}"
    exit 1
  fi

  # Fallback: embed system prompt in message
  COMBINED="<s>${SYSTEM_PROMPT}</s>

${USER_MSG}"
  echo "$COMBINED" > "$TMPFILE"
  if ! RESPONSE=$(claude -p < "$TMPFILE" 2>"$CLAUDE_ERR"); then
    STDERR_MSG=$(cat "$CLAUDE_ERR" 2>/dev/null || true)
    emit_error "claude -p invocation failed: ${STDERR_MSG}"
    exit 1
  fi
fi

# --- Parse JSON from response --------------------------------------------------

python3 -c "
import json, sys, re

raw = sys.stdin.read().strip()

# Attempt 1: parse raw response directly
try:
    d = json.loads(raw)
    # claude -p --output-format json wraps in {'result': '...'}
    if 'result' in d and isinstance(d['result'], str):
        inner = d['result'].strip()
        inner = re.sub(r'^\`\`\`json?\s*', '', inner)
        inner = re.sub(r'\s*\`\`\`$', '', inner)
        try:
            parsed = json.loads(inner)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            sys.exit(0)
        except:
            pass
    if 'score' in d or 'findings' in d:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        sys.exit(0)
except:
    pass

# Attempt 2: find JSON object in free text
match = re.search(r'\{[\s\S]*\}', raw)
if match:
    try:
        parsed = json.loads(match.group())
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        sys.exit(0)
    except:
        pass

# Give up
print(json.dumps({
    'error': 'Failed to parse review response',
    'raw_preview': raw[:300],
    'findings': [],
    'score': 0
}, ensure_ascii=False, indent=2))
" <<< "$RESPONSE"