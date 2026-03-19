#!/usr/bin/env bash
# install.sh — Installer for the "wise" Claude Code skill
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/den-emon/wise-mode/main/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/den-emon/wise-mode/main/install.sh | bash
#
# The entire script is wrapped in main() so that a partial download
# never executes incomplete code.

main() {
    set -euo pipefail

    # ── Configuration ──────────────────────────────────────────────
    REPO_RAW_BASE="https://raw.githubusercontent.com/den-emon/wise-mode/main"
    SKILL_NAME="wise"
    SKILL_DIR=".claude/skills/${SKILL_NAME}"
    FILES=("SKILL.md" "CHECKLISTS.md" "PATTERNS.md")

    # ── Colors (disabled when piped) ──────────────────────────────
    if [ -t 1 ]; then
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[0;33m'
        CYAN='\033[0;36m'
        BOLD='\033[1m'
        RESET='\033[0m'
    else
        RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
    fi

    info()  { printf "${CYAN}[info]${RESET}  %s\n" "$1"; }
    ok()    { printf "${GREEN}[ok]${RESET}    %s\n" "$1"; }
    warn()  { printf "${YELLOW}[warn]${RESET}  %s\n" "$1"; }
    error() { printf "${RED}[error]${RESET} %s\n" "$1" >&2; }

    # ── Preflight checks ─────────────────────────────────────────
    if command -v curl >/dev/null 2>&1; then
        fetch() { curl -fsSL --retry 3 --retry-delay 2 "$1"; }
    elif command -v wget >/dev/null 2>&1; then
        fetch() { wget -qO- --tries=3 "$1"; }
    else
        error "curl or wget is required but neither was found."
        exit 1
    fi

    # ── Detect project root ───────────────────────────────────────
    # Install into the current directory's .claude/skills/wise/
    # Verify we're in a reasonable location (has .git or .claude already)
    if [ -d ".git" ] || [ -d ".claude" ]; then
        PROJECT_ROOT="$(pwd)"
    else
        warn "No .git or .claude directory found in $(pwd)."
        printf "  Install wise skill here anyway? [y/N] "
        read -r answer </dev/tty
        case "$answer" in
            [yY]|[yY][eE][sS]) PROJECT_ROOT="$(pwd)" ;;
            *) error "Aborted. cd into your project root and retry."; exit 1 ;;
        esac
    fi

    TARGET_DIR="${PROJECT_ROOT}/${SKILL_DIR}"

    # ── Check for existing installation ───────────────────────────
    if [ -d "${TARGET_DIR}" ] && [ -f "${TARGET_DIR}/SKILL.md" ]; then
        warn "wise skill already exists at ${TARGET_DIR}"
        printf "  Overwrite? [y/N] "
        read -r answer </dev/tty
        case "$answer" in
            [yY]|[yY][eE][sS]) : ;;
            *) info "Aborted. Existing installation unchanged."; exit 0 ;;
        esac
    fi

    # ── Download to temp dir first (atomic install) ───────────────
    TMPDIR_DOWNLOAD="$(mktemp -d)"
    trap 'rm -rf "${TMPDIR_DOWNLOAD}"' EXIT

    info "Downloading wise skill files..."
    FAIL=0
    for file in "${FILES[@]}"; do
        url="${REPO_RAW_BASE}/.claude/skills/${SKILL_NAME}/${file}"
        dest="${TMPDIR_DOWNLOAD}/${file}"
        if fetch "${url}" > "${dest}" 2>/dev/null; then
            # Basic sanity: file should not be empty
            if [ ! -s "${dest}" ]; then
                error "Downloaded ${file} is empty."
                FAIL=1
            fi
        else
            error "Failed to download ${file} from ${url}"
            FAIL=1
        fi
    done

    if [ "${FAIL}" -ne 0 ]; then
        error "One or more files failed to download. Installation aborted."
        exit 1
    fi

    # ── Verify SKILL.md has expected frontmatter ──────────────────
    if ! head -1 "${TMPDIR_DOWNLOAD}/SKILL.md" | grep -q "^---"; then
        error "SKILL.md does not look like a valid skill file (missing frontmatter)."
        exit 1
    fi

    # ── Install ───────────────────────────────────────────────────
    mkdir -p "${TARGET_DIR}"
    for file in "${FILES[@]}"; do
        cp "${TMPDIR_DOWNLOAD}/${file}" "${TARGET_DIR}/${file}"
    done

    # ── Summary ───────────────────────────────────────────────────
    echo ""
    printf "${BOLD}${GREEN}  wise skill installed successfully!${RESET}\n"
    echo ""
    info "Location: ${TARGET_DIR}/"
    for file in "${FILES[@]}"; do
        echo "    ${TARGET_DIR}/${file}"
    done
    echo ""
    info "Usage: type ${BOLD}/wise${RESET} in Claude Code to activate architect mode."
    echo ""

    # ── Hint: .gitignore ──────────────────────────────────────────
    if [ -f ".gitignore" ]; then
        if ! grep -q "\.claude/" ".gitignore" 2>/dev/null; then
            warn "Consider adding .claude/ to .gitignore if you don't want to track skill files."
        fi
    fi
}

# Run everything inside main() to guard against partial downloads
main "$@"
