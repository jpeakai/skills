# skills

Agent skills published by [jpeak.ai](https://github.com/jpeakai). Each directory under
`skills/` is one skill: a `SKILL.md` carrying YAML frontmatter, plus whatever resources,
scripts and templates it needs.

## Installing

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
