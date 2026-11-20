<!-- GENERATED from the bundle's *.yml by okf_render.py. Do not edit; regenerate. -->

# Decision Records

| Record | Decision | Status |
|---|---|---|
| [ADR-0001](0001-canonical-agent-instructions.md) | Keep agent instructions canonical in AGENTS.md | accepted |
| [ADR-0002](0002-human-skill-overviews.md) | Give every canonical skill a dual-density human overview | accepted |
| [ADR-0003](0003-structured-root-decisions.md) | Declare standard documentation and render root decisions from YAML | accepted |
| [ADR-0004](0004-kiro-harness-support.md) | Support Kiro through Agent Plugins manifests and kiro-conf hook wiring | proposed |
| [ADR-0005](0005-cloud-setup-script-in-skill.md) | Ship the cloud setup script inside the ccw-setup skill and release it under ccw/ tags | proposed |
| [ADR-0006](0006-auto-tag-plugin-versions.md) | Tag every plugin version automatically on main, named without the jpai- prefix | proposed |
| [ADR-0007](0007-publish-generated-plugin-mirrors.md) | Publish generated plugin mirrors on main before creating release tags | proposed |
| [ADR-0008](0008-self-contained-repository-tools.md) | Organise repository automation as self-contained CLI Tool subprojects | proposed |
| [ADR-0009](0009-resolve-skill-paths-across-harnesses.md) | Resolve skill locations through a harness-independent SKILLS_ROOT placeholder | accepted |
# By group

## repository-conventions

* [ADR-0001](0001-canonical-agent-instructions.md) - One instruction source shared by agent harnesses
* [ADR-0002](0002-human-skill-overviews.md) - Human entry points separate from runtime skill instructions
* [ADR-0003](0003-structured-root-decisions.md) - Standard documentation dialect with a generated root decision bundle
* [ADR-0004](0004-kiro-harness-support.md) - Kiro installs packs as powers and takes its hook from workspace configuration
* [ADR-0005](0005-cloud-setup-script-in-skill.md) - Machine setup is downloaded from an immutable tag, and per-session state is applied by a skill
* [ADR-0006](0006-auto-tag-plugin-versions.md) - A workflow creates each missing release tag, so no release waits on a person with tag access
* [ADR-0007](0007-publish-generated-plugin-mirrors.md) - Feature PRs carry canonical sources while publication automation commits validated plugin copies
* [ADR-0008](0008-self-contained-repository-tools.md) - Focused Tools own their environments, commands, tests and maintenance instructions
* [ADR-0009](0009-resolve-skill-paths-across-harnesses.md) - Agent skill instructions resolve their installation path without assuming a harness directory
# Relationship graph

Open [graph.html](graph.html) to explore the records visually: click a node to read it, and links between records navigate the graph.
The same edge set is rendered as prose in [graph.md](graph.md), and as data in [graph.json](graph.json).

* ADR-0005 --extended_by--> ADR-0006
* ADR-0006 --extended_by--> ADR-0007
* ADR-0006 --extends--> ADR-0005
* ADR-0007 --extends--> ADR-0006

# Scoped decision logs

- [ADR skill](../skills/adr/AGENTS.md#adr-log)
- [CLI skill](../skills/cli/AGENTS.md#adr-log)
- [Concise Decisions skill](../skills/concise-decisions/docs/adrs/README.md)
- [Gooddocs skill](../skills/gooddocs/AGENTS.md)
- [Librarian skill](../skills/librarian/AGENTS.md#adr-log)
- [Mermaid scripts](../skills/mermaidjs-diagrams/scripts/AGENTS.md)
- [Richdocs](../skills/richdocs/resources/adr-log.md)
- [Richdocs foundations](../skills/richdocs/resources/adr-log-foundations.md)
