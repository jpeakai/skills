#!/usr/bin/env python3
"""PreToolUse coaching hook, portable across Claude Code and Codex CLI.

Vendored from neozenith/agentic-dotfiles (MIT licensed,
https://github.com/neozenith/agentic-dotfiles); the only local change in logic
is the `AskUserQuestion` check. It is portable because the payload it reads and
the JSON it prints are wire-compatible with both agents' PreToolUse hook
contract (same event/field names; Codex additionally sets `CLAUDE_PLUGIN_ROOT`
for exactly this kind of out-of-the-box compatibility).

Reads the PreToolUse event JSON on stdin and, when a tool call breaks one of
this repo's working agreements, emits a `deny` decision whose *reason* is a
coaching message telling the model what to do INSTEAD. That turns a dead-end
denial into a redirect, so the model stops retrying near-miss variants of a
blocked command.

Two kinds of check, in this order:

1. **Structural checks** (this file). Derived from the command's argv rather
   than from a regex, because they need shell structure to be accurate:
   - *No deletions.* Commands that unlink a path destroy evidence. Move the
     path into the project-local tmp/ instead.
   - *No out-of-project scratch space.* System temp roots and any `scratchpad/`
     outside the project are invisible to the person reviewing the work.
     Applies to Bash commands and to the path arguments of `Write` / `Edit` /
     `NotebookEdit` / `Read`.
   - *One question at a time, always answerable with reasoning.* An
     `AskUserQuestion` call must ask exactly one question, put the recommended
     option first, include an explicit `Other:` option, and give every option
     a preview so the user can attach notes to whichever one they pick.
2. **Pattern rules** (`tool_coach_rules.json`). Regexes matched against the
   Bash command string, for tool-choice coaching: inline interpreter snippets,
   bare interpreters, manual import-path injection, the timeout binary. Edit
   that file to add a rule; no code change needed.

Heredoc bodies are stripped before every command check. A heredoc body is data
being written, not a command being run, so scanning it produces pure false
positives: writing a *document about* a blocked command would otherwise be
blocked by the very rule the document describes.

Contract (Claude Code hooks):
  exit 0 + JSON body  -> decision applied (we emit deny + reason).
  exit 0 + no output  -> no opinion; normal permission flow proceeds.
  exit 1              -> non-blocking error; the first stderr line is shown to
      the model and execution continues.

We FAIL LOUD, never open: a broken rules file surfaces on every call until it
is fixed, rather than silently disabling the guard. exit 1 is non-blocking by
the contract above, so a broken hook cannot wedge the session either way.

Stdlib only (json, os, re, shlex, sys, pathlib) so it has zero install/venv
dependencies and starts fast on every call.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

# -- Configuration --------------------------------------------------------
RULES_PATH = Path(__file__).with_name("tool_coach_rules.json")

# Commands whose whole purpose is to remove a path.
DELETE_COMMANDS = {"rm", "rmdir", "unlink", "shred"}

# Wrappers that may precede the real command word.
COMMAND_PREFIXES = {
    "sudo",
    "time",
    "command",
    "builtin",
    "nohup",
    "xargs",
    "env",
    "exec",
}

# Shell operators that end one command segment and start the next.
SEGMENT_SEPARATORS = {"&&", "||", "|", "&", ";", "(", ")", "{", "}", "\n"}

# Absolute roots that live outside any project checkout. Held as relative names
# and prefixed below so this file stays editable through its own guard, which
# would otherwise flag its own configuration as an out-of-project path.
FORBIDDEN_ROOTS = tuple(
    "/" + name
    for name in ("private/tmp", "private/var/folders", "var/folders", "tmp", "var/tmp")
)

# Tools that name a filesystem path in their input rather than a shell command.
TOOLS_WITH_PATHS = {"Write", "Edit", "NotebookEdit", "Read"}

# The escape-hatch option every question must offer, matched on its label.
OTHER_LABEL = re.compile(r"^\s*Other\b", re.IGNORECASE)

HEREDOC_START = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

DELETE_GUIDANCE = """\
Deleting is not allowed in this project. Never remove a file; move it aside so it stays auditable.

Use the project-local tmp/ instead:

    mkdir -p tmp/_archived/<short-reason>
    mv <path> tmp/_archived/<short-reason>/

Why: a deleted file leaves no evidence of what was discarded or why, and it cannot be reviewed or restored. A moved file can be both. Keep your hands above the table.

If the intent was to replace a file, write the new content over it directly. That is an edit, not a delete, and it needs no move.
If the intent was to clear build or cache output, prefer the project's `make` clean target.
If the file was already staged for deletion, run `git restore --staged --worktree <path>` first, then move it."""

SCRATCH_GUIDANCE = """\
Working outside the project directory is not allowed. That path is invisible to the person reviewing this work.

Use the project-local tmp/ instead:

    mkdir -p tmp/
    # then write scratch files, intermediate output and helper scripts under tmp/

Why: scratch files under a system temp root or an out-of-project scratchpad cannot be inspected, diffed or audited alongside the change they support. Keep your hands above the table.

tmp/ is already gitignored, so nothing scratch will be committed."""

QUESTION_GUIDANCE = """\
Ask the user one question at a time, and let every answer carry its reasoning.

Re-issue the call with this shape:

    AskUserQuestion({ questions: [{            // exactly ONE question
      header: "<≤12 chars>",
      question: "<the decision, with enough context to answer it cold>",
      multiSelect: false,                      // previews only work single-select
      options: [
        { label: "<option> (Recommended)", description: "...", preview: "..." },  // recommended FIRST
        { label: "<alternative>",          description: "...", preview: "..." },
        { label: "Other: none of these fit", description: "Describe your own answer in the notes",
          preview: "None of the suggested options fit.\\nUse the notes to describe what you want instead." }
      ]
    }]})

The rules, and why each one matters:

    - One question per call. The answer to one question should shape the next; a batch forces every answer before the first has propagated.
    - Recommended option first. The user reads the suggestion before the alternatives, and accepting it is the cheapest path.
    - An explicit `Other:` option, always. When no suggestion fits, the user needs a way to say so that is part of the question itself.
    - A preview on EVERY option, including `Other:`. The preview pane is what exposes the notes field, so the user can pick an option and "yes, and..." it with their reasoning. An option without a preview cannot carry notes.

Ask the questions you dropped in later turns, after this answer is in."""


# -- Hook I/O -------------------------------------------------------------
def fail(msg: str) -> int:
    """Print one actionable line to stderr and signal a non-blocking error."""
    print(f"tool_coach: {msg}", file=sys.stderr)
    return 1


def deny(reason: str) -> None:
    """Emit the deny decision. The reason is what the model reads and acts on."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


# -- Pattern rules --------------------------------------------------------
def load_rules(rules_path: Path) -> list[dict]:
    """Parse and compile the pattern rules, raising on anything malformed."""
    if not rules_path.exists():
        raise FileNotFoundError(
            f"rules file not found at {rules_path} - create it or remove the "
            f"tool_coach hook from settings.json"
        )
    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{rules_path} is not valid JSON: {exc}") from exc

    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError(f'{rules_path} must contain a top-level "rules" array')

    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or "pattern" not in rule or "message" not in rule:
            raise ValueError(
                f'rule #{i} in {rules_path} must be an object with "pattern" and "message" keys'
            )
        # Compile eagerly so a bad regex fails loud here, not silently at match time.
        try:
            rule["_compiled"] = re.compile(rule["pattern"])
        except re.error as exc:
            raise ValueError(
                f"rule '{rule.get('name', i)}' has an invalid regex {rule['pattern']!r}: {exc}"
            ) from exc
    return rules


def match_rule(command: str, rules: list[dict]) -> dict | None:
    """The first pattern rule this command trips, or None. Order matters."""
    for rule in rules:
        if rule["_compiled"].search(command):
            return rule
    return None


# -- Shell parsing --------------------------------------------------------
def strip_heredocs(command: str) -> str:
    """Remove heredoc bodies, keeping the command lines that surround them.

    Everything between a heredoc's opening line and its closing delimiter is
    data written to a file or a pipe, not a command the shell will execute, so
    no check should read it.
    """
    lines = command.split("\n")
    kept: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        kept.append(line)
        delimiters = [m.group(2) for m in HEREDOC_START.finditer(line)]
        i += 1
        for delimiter in delimiters:
            while i < len(lines) and lines[i].strip() != delimiter:
                i += 1
            i += 1  # skip the closing delimiter line itself
    return "\n".join(kept)


def split_segments(command: str) -> list[list[str]]:
    """Split a shell command into argv lists, one per pipeline/list segment.

    `shlex` with punctuation_chars keeps quoted paths intact while still
    tokenising the shell operators as their own words, so a pipeline into a
    deletion is seen as two segments. Lines are split first, because shlex
    treats a newline as plain whitespace and would otherwise let a command on
    its own line hide inside the previous one. Falls back to a naive split on
    unbalanced quotes, because a guard that over-approximates beats one that
    crashes on odd input.
    """
    tokens: list[str] = []
    for line in command.split("\n"):
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            tokens.extend(lexer)
        except ValueError:
            tokens.extend(line.split())
        tokens.append("\n")

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SEGMENT_SEPARATORS:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def head_of(segment: list[str]) -> str | None:
    """The command word of a segment, skipping env assignments and wrappers."""
    seen_prefix = False
    for token in segment:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token):
            continue  # FOO=bar prefix
        if Path(token).name in COMMAND_PREFIXES:
            seen_prefix = True
            continue
        if seen_prefix and token.startswith("-"):
            continue  # a wrapper's own flags, for example xargs -0
        return token
    return None


def find_delete_verb(command: str) -> str | None:
    """Return the deletion verb this command would run, or None."""
    for segment in split_segments(command):
        head = head_of(segment)
        if head is None:
            continue
        name = Path(head).name  # an absolute path collapses to its basename
        if name in DELETE_COMMANDS:
            return name
        rest = segment[segment.index(head) + 1 :]
        if name == "git" and "rm" in rest[:3]:
            return "git rm"
        if name == "find":
            if "-delete" in rest:
                return "find -delete"
            if "-exec" in rest and any(Path(t).name in DELETE_COMMANDS for t in rest):
                return "find -exec"
    return None


# -- Out-of-project paths -------------------------------------------------
def project_root(payload: dict) -> Path:
    """Where the project lives: the harness env var, else the call's cwd."""
    raw = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    return Path(raw).resolve()


def is_outside(raw: str, root: Path) -> bool:
    """True when this path is scratch space the reviewer cannot see."""
    candidate = Path(raw)
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate

    if resolved == root or root in resolved.parents:
        return False  # inside the project, always fine

    text = str(resolved)
    if any(text == r or text.startswith(r + "/") for r in FORBIDDEN_ROOTS):
        return True
    return "scratchpad" in resolved.parts


def outside_paths(command: str, root: Path) -> list[str]:
    """Absolute paths in the command that sit outside the project."""
    return [
        token
        for token in re.findall(r"[^\s'\"`]+", command)
        if token.startswith("/") and is_outside(token, root)
    ]


# -- Questions to the user ------------------------------------------------
def question_problems(tool_input: dict) -> list[str]:
    """Every way this AskUserQuestion call breaks the rules, in reading order.

    All of them are reported at once, so the model can fix the call in a
    single retry rather than discovering the rules one denial at a time. A
    batched call still has each question's options checked, so the retry that
    splits the batch does not trip over a second round of problems.
    """
    questions = [q for q in tool_input.get("questions") or [] if isinstance(q, dict)]
    problems: list[str] = []
    if len(questions) != 1:
        problems.append(
            f"{len(questions)} questions in one call: ask exactly one, so its answer can shape the next question"
        )

    for question in questions:
        # Name the question only when there is more than one to tell apart.
        where = f'"{question.get("header", "?")}": ' if len(questions) > 1 else ""
        options = [o for o in question.get("options") or [] if isinstance(o, dict)]
        labels = [str(o.get("label", "")) for o in options]

        if any("(Recommended)" in label for label in labels[1:]):
            problems.append(f"{where}the recommended option is not first")

        if not any(OTHER_LABEL.match(label) for label in labels):
            problems.append(f'{where}no "Other:" option for when none of the suggestions fit')

        no_notes = [label for label, o in zip(labels, options) if not str(o.get("preview") or "").strip()]
        if no_notes:
            shown = ", ".join(f'"{label}"' for label in no_notes)
            problems.append(f"{where}no preview, so no notes field, on: {shown}")

        if question.get("multiSelect"):
            problems.append(f"{where}multiSelect is true: previews, and so notes, only work single-select")

    return problems


# -- Decision -------------------------------------------------------------
def decide(payload: dict, rules: list[dict], root: Path) -> str | None:
    """The deny reason for this tool call, or None to stay out of the way."""
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool == "Bash":
        command = strip_heredocs(tool_input.get("command", "") or "")
        if not command.strip():
            return None

        verb = find_delete_verb(command)
        if verb is not None:
            return f"Blocked: `{verb}` deletes a path.\n\n{DELETE_GUIDANCE}"

        strays = outside_paths(command, root)
        if strays:
            shown = "\n".join(f"  {p}" for p in sorted(set(strays))[:5])
            return f"Blocked: this command touches paths outside the project:\n{shown}\n\n{SCRATCH_GUIDANCE}"

        rule = match_rule(command, rules)
        if rule is not None:
            return str(rule["message"])

    elif tool in TOOLS_WITH_PATHS:
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if target and is_outside(target, root):
            return f"Blocked: `{target}` is outside the project.\n\n{SCRATCH_GUIDANCE}"

    elif tool == "AskUserQuestion":
        problems = question_problems(tool_input)
        if problems:
            shown = "\n".join(f"  - {p}" for p in problems)
            return f"Blocked: this question cannot be answered one at a time with reasoning:\n{shown}\n\n{QUESTION_GUIDANCE}"

    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0  # nothing to inspect

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return fail(f"could not parse hook stdin as JSON: {exc}")

    try:
        rules = load_rules(RULES_PATH)
    except (FileNotFoundError, ValueError) as exc:
        return fail(str(exc))

    reason = decide(payload, rules, project_root(payload))
    if reason is not None:
        deny(reason)
    return 0  # exit 0 either way: with JSON => applied, without => no opinion


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
