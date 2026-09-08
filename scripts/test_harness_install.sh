#!/usr/bin/env bash
# End-to-end install test for both harnesses, in throwaway sandboxes.
#
# Structural validation (scripts/validate_plugins.py) proves the files are
# shaped right. This proves the two agents actually accept them: it clones the
# repo at HEAD into a temp directory — so the test runs against a fresh
# checkout, and symlinks are exercised as a consumer would get them — then
# installs both plugins into a config directory that has nothing else in it.
#
# Isolation is the point. Neither harness may see this project or the
# developer's globally installed plugins and skills:
#   Claude Code  CLAUDE_CONFIG_DIR   replaces ~/.claude
#   Codex        CODEX_HOME          replaces ~/.codex
#                HOME                also replaced, because Codex reads
#                                    personal skills from ~/.agents/skills,
#                                    which CODEX_HOME does not cover
#
# Usage: scripts/test_harness_install.sh [sandbox-dir]
# Exit codes: 0 both harnesses accepted and loaded both plugins, 1 otherwise.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX="${1:-${TMPDIR:-/tmp}/jpai-skills-harness-test-$(date +%Y%m%d-%H%M%S)}"
CLONE="$SANDBOX/checkout"
PLUGINS=(jpai-essentials jpai-delivery)

# Skills that must appear in each plugin, to prove symlinks resolved after clone.
ESSENTIALS_SKILLS=(librarian gooddocs mermaidjs-diagrams richdocs concise-decisions agnostic)
DELIVERY_SKILLS=(plan-gap concise-decisions)

pass=0
fail=0

ok()   { echo "  ok   $1"; pass=$((pass + 1)); }
bad()  { echo "  FAIL $1${2:+ — $2}"; fail=$((fail + 1)); }
check() { if [ "$1" = "0" ]; then ok "$2"; else bad "$2" "${3:-}"; fi; }

echo "Sandbox: $SANDBOX"
mkdir -p "$SANDBOX"

# ---------------------------------------------------------------- fresh clone
echo
echo "Cloning HEAD into the sandbox (proves a consumer's checkout works)"
git clone --quiet --no-hardlinks "$REPO" "$CLONE" 2>/dev/null
check $? "git clone"

# A clone is where a symlink-composed layout would break if links were absolute
# or pointed outside the repo, so re-assert resolution on the clone itself.
dangling=0
while IFS= read -r link; do
    [ -e "$link" ] || { dangling=$((dangling + 1)); echo "        dangling: ${link#"$CLONE"/}"; }
done < <(find "$CLONE/plugins" -type l)
check "$([ "$dangling" -eq 0 ] && echo 0 || echo 1)" "every symlink resolves in the clone" "$dangling dangling"

# ------------------------------------------------------------------- Claude
echo
echo "Claude Code — isolated CLAUDE_CONFIG_DIR"
export CLAUDE_CONFIG_DIR="$SANDBOX/claude-config"
mkdir -p "$CLAUDE_CONFIG_DIR"

out="$(claude plugin marketplace add "$CLONE" 2>&1)"
check $? "marketplace add" "$(echo "$out" | tail -2)"

for p in "${PLUGINS[@]}"; do
    out="$(claude plugin install "$p@jpeakai" 2>&1)"
    check $? "install $p" "$(echo "$out" | tail -2)"
done

listing="$(claude plugin list 2>&1)"
for p in "${PLUGINS[@]}"; do
    echo "$listing" | grep -q "$p"
    check $? "$p appears in plugin list"
done

# `plugin details` is the component inventory: it is what proves the skills and
# the hook were discovered through the symlinks, not merely that files copied.
for p in "${PLUGINS[@]}"; do
    details="$(claude plugin details "$p" 2>&1)"
    if [ "$p" = "jpai-essentials" ]; then want=("${ESSENTIALS_SKILLS[@]}"); else want=("${DELIVERY_SKILLS[@]}"); fi
    for s in "${want[@]}"; do
        echo "$details" | grep -q "$s"
        check $? "$p: skill $s discovered"
    done
    echo "$details" | grep -qiE 'hook'
    check $? "$p: hook discovered"
done

# Isolation: the sandbox must not have picked up the developer's own plugins.
echo "$listing" | grep -qE 'ce-|twg|databricks'
if [ $? -eq 0 ]; then bad "Claude sandbox is isolated" "global plugins leaked in"; else ok "Claude sandbox is isolated from global plugins"; fi

# --------------------------------------------------------------------- Codex
echo
echo "Codex — isolated HOME + CODEX_HOME"
CODEX_SANDBOX_HOME="$SANDBOX/codex-home"
CODEX_FAKE_HOME="$SANDBOX/fake-home"
mkdir -p "$CODEX_SANDBOX_HOME" "$CODEX_FAKE_HOME"
codex_env=(env HOME="$CODEX_FAKE_HOME" CODEX_HOME="$CODEX_SANDBOX_HOME")

out="$("${codex_env[@]}" codex plugin marketplace add "$CLONE" 2>&1)"
check $? "marketplace add" "$(echo "$out" | tail -2)"

for p in "${PLUGINS[@]}"; do
    out="$("${codex_env[@]}" codex plugin add "$p@jpeakai" 2>&1)"
    check $? "install $p" "$(echo "$out" | tail -2)"
done

listing="$("${codex_env[@]}" codex plugin list 2>&1)"
for p in "${PLUGINS[@]}"; do
    echo "$listing" | grep -q "$p.*installed"
    check $? "$p installed and enabled"
done

# `debug prompt-input` renders exactly what the model would see, with no model
# call — the cheapest proof that a skill actually loaded rather than merely
# being present on disk.
prompt="$(cd "$SANDBOX" && "${codex_env[@]}" codex debug prompt-input 2>/dev/null)"
for s in "${ESSENTIALS_SKILLS[@]}" "${DELIVERY_SKILLS[@]}"; do
    echo "$prompt" | grep -q "$s:"
    check $? "skill $s is in the model-visible prompt"
done

# Isolation: no skill root may point outside the sandbox.
leaked="$(echo "$prompt" | grep -oE '`r[0-9]+` = `[^`]*`' | grep -v "$SANDBOX" || true)"
if [ -n "$leaked" ]; then
    bad "Codex sandbox is isolated" "external skill roots: $leaked"
else
    ok "Codex sandbox is isolated from global skills"
fi

# ------------------------------------------------------------------- summary
echo
echo "$((pass + fail)) checks run — $pass passed, $fail failed."
echo "Sandbox kept for inspection: $SANDBOX"
[ "$fail" -eq 0 ] || exit 1
