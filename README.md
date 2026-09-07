# skills

Agent skills published by [jpeak.ai](https://github.com/jpeakai). Each directory under
`skills/` is one skill: a `SKILL.md` carrying YAML frontmatter, plus whatever resources,
scripts and templates it needs.

## Installing

### As a Claude Code plugin marketplace

This repo is a [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces): `.claude-plugin/marketplace.json` registers the whole skill set as one plugin, `jpeak-skills`, defined in `.claude-plugin/plugin.json`.

```
/plugin marketplace add jpeakai/skills
/plugin install jpeak-skills@jpeakai
```

### As a Codex skills/plugin source

This repo also works as a [Codex plugin](https://developers.openai.com/codex/skills) source: `.agents/plugins/marketplace.json` (the repo-scoped marketplace Codex looks for) registers one local plugin defined by `.codex-plugin/plugin.json`, whose `skills` field points at the existing `skills/` directory.

```sh
codex plugin marketplace add jpeakai/skills
codex plugin add jpeak-skills@jpeakai
```

### Manually

Copy or symlink a skill into your agent's skills directory:

```sh
git clone https://github.com/jpeakai/skills.git
ln -s "$PWD/skills/librarian" ~/.claude/skills/librarian
```

## The skills

| Skill | What it does |
|---|---|
| [`agnostic`](skills/agnostic) | Keeps documentation generic by renaming project-, client- or company-specific names to open-source-style placeholders |
| [`cli`](skills/cli) | Playbook for building project-local developer CLIs and the assets they generate — static HTML viewers, workflow templates, stencil diagrams, sticky PR comments |
| [`concise-decisions`](skills/concise-decisions) | Consolidates accumulated ambiguities into a single highest-leverage decision question, answering first from existing decision records |
| [`gooddocs`](skills/gooddocs) | Documentation quality in three modes: audit docs against the reality of the code, write or improve them, or restructure one for readability |
| [`librarian`](skills/librarian) | Repo documentation organisation: ensures the canonical document set exists and every doc lives where its content says it belongs |
| [`mermaidjs-diagrams`](skills/mermaidjs-diagrams) | Renders and analyses Mermaid diagrams in markdown, enforcing visual complexity limits and WCAG colour-contrast requirements |
| [`plan-gap`](skills/plan-gap) | Gap analysis planning: iteratively refines a tiered spec covering execution plan, gaps, decisions, and success and negative measures |
| [`richdocs`](skills/richdocs) | Rich HTML companions to markdown discovery documents, with a vendored draw.io stencil library and an injectable design-tokens brandpack |

## Licence

MIT — see [LICENSE](LICENSE).
