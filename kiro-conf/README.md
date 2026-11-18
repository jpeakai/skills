# Kiro Config

Workspace configuration for [Kiro](https://kiro.dev/), the Kiro counterpart of `codex-conf/`.
`make kiro-setup` copies it into a sibling `<project dir>/.kiro/` when this repo is cloned into a project as `.claude/`.

| Path | Becomes | Purpose |
|------|---------|---------|
| `hooks/tool_coach.json` | `.kiro/hooks/tool_coach.json` | Runs `.claude/hooks/tool_coach.py --harness kiro` before every shell, write and read call |
| `agents/jpai.json` | `.kiro/agents/jpai.json` | Agent profile that loads workspace skills and allows the `codex-conf/rules/` commands |
| (from `../skills/`) | `.kiro/skills/` | Every canonical skill, minus evals and build artefacts |

## Use

```sh
make kiro-setup                     # from <project dir>/.claude/
kiro-cli agent set-default jpai     # optional: make the profile the default
```

Standalone hooks in `.kiro/hooks/` apply to every agent profile, in the IDE and the CLI.
The skills reach the built-in agent too; the `jpai` profile adds the command allowlist.

## Assumptions

- **Hook commands run from the workspace root.** The command uses the relative path `.claude/hooks/tool_coach.py`.
- **Approval stays with Kiro.** A PreToolUse hook cannot block a call that `--trust-all-tools` already approved.
- **Kiro's workspace is the git root.** Kiro resolves `.kiro/` at the enclosing repository, so the project must be its own repo.

Packs installed as Kiro powers carry skills only; see the root [README](../README.md#kiro).
