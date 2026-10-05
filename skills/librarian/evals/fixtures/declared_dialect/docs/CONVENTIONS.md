# Documentation conventions

## Dialect

- **Flavour:** standard
- **Docs taxonomy:** flat topic files under `docs/`, kebab-case
- **Glossary:** GLOSSARY.md at root
- **ADR layout:** single-file `ADRs.md` log at root. This is deliberate: do not migrate to file-per-decision.
- **Agent files:** AGENTS.md canonical, CLAUDE.md holds only `@AGENTS.md`

## Layout map

| Path | Charter | Audience | Changes when |
|------|---------|----------|--------------|
| `README.md` | Orientation + routing | Consumers | Purpose changes |
| `CONTRIBUTING.md` | Setup, PR process | Contributors | Workflow changes |
| `CODING_STANDARDS.md` | How code is written | Contributors + Agents | A convention changes |
| `AGENTS.md` | Agent invariants + pointers | Agents | Commands change |
| `CLAUDE.md` | Exactly `@AGENTS.md` | Claude Code | Never |
| `ADRs.md` | Accepted decisions | Both | A decision is made |
| `GLOSSARY.md` | Ubiquitous language | Both | A term enters |
| `docs/` | Topic docs | Both | A topic changes |
