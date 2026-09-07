# hooks/

A `PreToolUse` guardrail hook, wired once and shared by both ecosystems this
repo publishes a plugin for: **Claude Code** and **Codex CLI**.

## What it does

**`tool_coach.py`** reads the PreToolUse event on stdin and, when a tool call
breaks one of this repo's working agreements, returns a `deny` decision whose
*reason* is a coaching message saying what to do instead. A plain "permission
denied" teaches nothing and invites the model to retry near-miss variants; a
redirect ends the loop in one turn.

| Check | Kind | Applies to |
|-------|------|------------|
| No deletions | structural | Bash |
| No out-of-project scratch space | structural | Bash, Write, Edit, NotebookEdit, Read |
| Tool-choice coaching (inline `-c` snippets, bare interpreters, manual `PYTHONPATH`, the `timeout` binary) | pattern rules in `tool_coach_rules.json` | Bash |

Structural checks parse the command into argv with `shlex`, so they catch
wrapped and indirect forms a regex misses: `sudo`, `xargs`, an absolute
`/bin/` path, an env-var prefix, a pipeline, `git rm`, `find -delete`. Pattern
rules live in the JSON file and need no code change to add. Heredoc bodies
are stripped before any check runs, so writing *documentation about* a
blocked command is never itself blocked. Full behaviour and rationale are in
the module docstrings of `tool_coach.py` and `tool_coach_rules.json`.

Stdlib only (`json`, `os`, `re`, `shlex`, `sys`, `pathlib`) — nothing to
install, no virtualenv to resolve, on every call in either agent.

## Provenance

`tool_coach.py`, `tool_coach_rules.json`, `test_tool_coach.py` and
`conftest.py` are vendored, unmodified in logic, from
[`neozenith/agentic-dotfiles`](https://github.com/neozenith/agentic-dotfiles)
(MIT licensed) — only doc comments were added here to note that origin and
this file (`hooks/README.md`) plus `hooks.json` are new. All credit for the
hook's design and test suite belongs to that repo.

## What's portable, and why

This directory is the plugin-facing, ecosystem-agnostic core: two stdlib
Python scripts and a JSON rules file. Neither reads a Claude- or
Codex-specific API — they only read the hook's stdin JSON and print a JSON
decision to stdout, using field names ( `tool_name`, `tool_input`, `cwd` on
the way in; `hookSpecificOutput.{hookEventName,permissionDecision,
permissionDecisionReason}` on the way out) that turn out to be the *same*
wire shape in both agents for `PreToolUse` today. That's the "portable" part.

The wiring is `hooks/hooks.json`, one file registering the script against
the `PreToolUse` event with a matcher — and it, too, is shared verbatim:

```jsonc
// hooks/hooks.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|NotebookEdit|Read",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/tool_coach.py\"",
            "timeout": 10,
            "statusMessage": "Checking the call against this project's working agreements…"
          }
        ]
      }
    ]
  }
}
```

### Claude Code

This is the documented plugin convention: a plugin's `hooks/hooks.json` is
auto-discovered at the plugin root and merged into the session's hook
config when the plugin is enabled — no reference from `plugin.json` needed,
the same way `skills/` is auto-discovered. `${CLAUDE_PLUGIN_ROOT}` resolves
to this plugin's install directory. (Confirmed against
[Claude Code plugin docs](https://code.claude.com/docs/en/plugins) and
[hooks reference](https://code.claude.com/docs/en/hooks), September 2026.)

### Codex CLI

Codex CLI ships its own hooks engine (`codex-rs/hooks`, `codex-rs/plugin`,
`codex-rs/config::hook_config` in
[`openai/codex`](https://github.com/openai/codex)) that mirrors Claude
Code's `PreToolUse` contract closely enough to be wire-compatible:

- Same event name (`PreToolUse`), same handler shape
  (`{"type": "command", "command", "timeout", "statusMessage"}`).
- Same output shape: `hookSpecificOutput.hookEventName` /
  `.permissionDecision` (`allow` / `deny` / `ask`) /
  `.permissionDecisionReason` — verified against Codex's own generated JSON
  Schema fixture (`codex-rs/hooks/schema/generated/pre-tool-use.command.output.schema.json`
  at commit `1e66885a`).
- Codex's hook-command executor explicitly sets **`CLAUDE_PLUGIN_ROOT`** in
  the child process environment alongside its own `PLUGIN_ROOT`, with the
  code comment *"For OOTB compat with existing plugins that use this env
  var"* (`codex-rs/hooks/src/engine/*`). That is a deliberate
  interoperability decision on Codex's side, not an assumption made here.
- The plugin manifest loader (`codex-rs/plugin/src/manifest.rs`) accepts a
  `hooks` path in `.codex-plugin/plugin.json` pointing at a `hooks/hooks.json`
  file — the exact same path this repo already uses for Claude Code.

`.codex-plugin/plugin.json` in this repo declares
`"hooks": "./hooks/hooks.json"` on that basis, so the one file above wires
the one script into both agents.

**Caveat — read before relying on this in a pinned CLI version.** This was
established by reading Codex's own source in the `openai/codex` repository
(commit `1e66885a`, September 2026), not from stable public documentation —
`developers.openai.com/codex` is where OpenAI's own docs point for the
authoritative schema and it was not reachable from this environment while
researching. The bundled `plugin-creator` skill shipped inside that same
Codex checkout (`codex-rs/skills/src/assets/samples/plugin-creator/scripts/validate_plugin.py`)
has a `--with-hooks` scaffold flag but its `allowed_keys` set for
`plugin.json` does not yet list `hooks` — a sign this surface is still
actively moving. If your installed Codex CLI doesn't pick up
`.codex-plugin/plugin.json`'s `hooks` field, this hook will simply not be
wired for Codex until that catches up; nothing else in this repo depends on
it.

### What is Claude-only

Nothing in the *hook itself* is Claude-only — that was the point of vendoring
stdlib-only scripts with no framework calls. The Claude-only piece, if
anything ends up being one, is exactly the wiring surface above: whether a
given Codex CLI build actually reads `.codex-plugin/plugin.json`'s `hooks`
field yet. If it doesn't, install the same two files directly instead (see
below) — that path never depends on plugin-manifest support.

## Install

### As part of this repo's plugins (recommended)

Already wired — see the root [README](../README.md#installing). Installing
`jpeak-skills` as a Claude Code plugin, or `jpeak-skills` as a Codex plugin,
brings this hook with it.

### Standalone, in any other project

Claude Code (`.claude/settings.json`, or a project's own `hooks/hooks.json`
if it's itself a plugin):

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|NotebookEdit|Read",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/tool_coach.py\"",
            "timeout": 10,
            "statusMessage": "Checking the call against this project's working agreements…"
          }
        ]
      }
    ]
  }
}
```

Copy `tool_coach.py` and `tool_coach_rules.json` to `.claude/hooks/` in the
target repo (adjust the path in `command` to match).

## Failure behaviour

Fail **loud**, never open. A missing or malformed rules file prints one line
to stderr and exits 1, which the hook contract treats as a non-blocking
error: the model sees the message, the call proceeds, and the breakage stays
visible until it is fixed.

## Tests

```sh
pytest hooks/test_tool_coach.py
# or, with uv (the test file's PEP-723 header declares pytest itself):
uv run --no-project hooks/test_tool_coach.py --cov=tool_coach --cov-report=term-missing
```

52 cases, no mocks, real payloads through the real decision path.
