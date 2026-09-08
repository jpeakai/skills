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

# Codex copies a plugin into its cache and drops symlink entries, so a
# symlinked skill would install as an empty directory with no error. Assert the
# clone carries real files before either harness sees it.
symlinks="$(find "$CLONE/plugins" -type l | wc -l | tr -d ' ')"
check "$([ "$symlinks" -eq 0 ] && echo 0 || echo 1)" "clone has no symlinks under plugins/" "$symlinks found"

for p in "${PLUGINS[@]}"; do
    n="$(find "$CLONE/plugins/$p/skills" -name SKILL.md | wc -l | tr -d ' ')"
    check "$([ "$n" -gt 0 ] && echo 0 || echo 1)" "$p carries $n real SKILL.md files in the clone"
done

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

# Isolation: no skill root may point outside the sandbox. Compare against the
# fully resolved path — on macOS $TMPDIR is /var/... while Codex reports the
# /private/var/... realpath, which would otherwise read as a false leak.
SANDBOX_REAL="$(cd "$SANDBOX" && pwd -P)"
leaked="$(echo "$prompt" | grep -oE '`r[0-9]+` = `[^`]*`' | grep -v "$SANDBOX_REAL" || true)"
if [ -n "$leaked" ]; then
    bad "Codex sandbox is isolated" "external skill roots: $leaked"
else
    ok "Codex sandbox is isolated from global skills"
fi

# -------------------------------------------------- installed hook contract
# Both harnesses invoke the hook the same way: PreToolUse event JSON on stdin,
# a decision on stdout. Run the copy that was actually installed, from each
# sandbox's own cache, so this tests the shipped artifact rather than the
# working tree. (This proves the installed hook honours the contract; it does
# not drive a live session, which would need a model call.)
echo
echo "Installed hook honours the PreToolUse contract"
payload='{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"'"$SANDBOX"'"}'

claude_hook="$(find "$CLAUDE_CONFIG_DIR" -path '*jpai-essentials*/hooks/tool_coach.py' 2>/dev/null | head -1)"
if [ -n "$claude_hook" ]; then
    decision="$(echo "$payload" | python3 "$claude_hook" 2>&1)"
    echo "$decision" | grep -q '"permissionDecision"'
    check $? "Claude-installed hook returns a permissionDecision" "$decision"
    echo "$decision" | grep -q '"deny"'
    check $? "Claude-installed hook denies a deletion"
else
    bad "Claude-installed hook found" "no tool_coach.py under $CLAUDE_CONFIG_DIR"
fi

codex_hook="$(find "$CODEX_SANDBOX_HOME" -path '*jpai-essentials*/hooks/tool_coach.py' 2>/dev/null | head -1)"
if [ -n "$codex_hook" ]; then
    decision="$(echo "$payload" | python3 "$codex_hook" 2>&1)"
    echo "$decision" | grep -q '"permissionDecision"'
    check $? "Codex-installed hook returns a permissionDecision" "$decision"
    echo "$decision" | grep -q '"deny"'
    check $? "Codex-installed hook denies a deletion"
else
    bad "Codex-installed hook found" "no tool_coach.py under $CODEX_SANDBOX_HOME"
fi

# ------------------------------------------------------------------- summary
echo
echo "$((pass + fail)) checks run — $pass passed, $fail failed."
echo "Sandbox kept for inspection: $SANDBOX"
[ "$fail" -eq 0 ] || exit 1
