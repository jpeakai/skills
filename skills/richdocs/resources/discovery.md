# Discovery document type (systems view)

Use this type when asked to discover the architecture of one or more systems from Git repositories and supporting documents.
`discovery` and `systems view` are aliases.
For example, `/richdocs html+inline systems view repo-a repo-b <page URL>` asks for research, authored Markdown, and an HTML companion.
It does not ask for an HTML rendering of a document that already exists.

## Inputs and outputs

Treat every repository path, URL, and Confluence page named after the type as a research source.
Locate each source through available tools.
Record the revision, page version, or retrieval date used.
If a named source cannot be read, report that limit and do not claim it was verified.
Identify the system boundary, audience, and decisions the guide should support from the request and sources.
Ask only when a missing answer materially changes the guide.

Author a persistent, editable Markdown document in the requested workspace.
Choose a clear filename and report its absolute path.
Keep Mermaid and other editable diagram sources in the Markdown or beside it.
Output modes are:

| Mode | Required result |
|------|-----------------|
| `md` | Markdown source only; do not invoke `md2html.py` |
| `html+live` | Markdown source plus the normal multi-file `md2html.py` output; serve with `serve.py` so edits to the paired Markdown appear on refresh |
| `html+inline` | Markdown source plus `md2html.py --inline`; verify the single HTML opens directly |

If the caller omits the mode, infer it from the requested deliverable; use `md` when none is specified.
HTML is always derived from the authored Markdown.
Follow the Mermaid gate in `SKILL.md` before rendering.
Do not hand-edit the generated HTML.

## Research and evidence

Start with the sources and trace the running system from entry points through interfaces, services, storage, and outputs.
Existing architecture pages are leads: verify material claims against application code, schemas, infrastructure configuration, and deployment workflows.
Cross-check names, identifiers, ownership, and contracts when combining repositories.
Distinguish implemented behaviour, configured resources, live deployment evidence, proposals, and unknowns.
Cite repository paths with line references where practical and link to the source documents beside the claims they support.

For broad, independent research, use subagents when delegation is available and authorised.
Divide by repository or lens, have each researcher hand back source paths and unresolved questions, then reconcile their findings before writing.
If delegation is unavailable, cover the same lenses serially.
Keep the final synthesis and verification with the author.

## Document shape

Build from a small system context to detailed subsystems.
Select applicable lenses rather than filling sections with unsupported guesses:

1. **System boundary:** External actors, inputs, outputs, processes, stable identifiers, shared vocabulary, and related repositories.
2. **Subsystems:** Each responsibility, interface, events, and persistent state; decompose further where it makes the system easier to understand.
3. **Deployment and infrastructure:** Build and release flow, environments, runtime services, and configured resources.
   Use provider stencils from this skill where real provider symbols clarify an infrastructure diagram; retain its editable draw.io source.
4. **State and storage:** Systems of record, data models, record owners, writers, readers, payload locations, object naming, schemas, versioning, and retention.
5. **Events and lifecycle:** Triggers, state transitions, cross-repository contracts, durable writes, failure and retry paths that change state or ownership, and the end-to-end sequence.
6. **Applications:** Frontend page and component hierarchy where present.
   Cover client fetching, caching, adapters, and domain logic.
   Explain server responsibilities and interactions.
7. **Evidence and limits:** Source references, unresolved conflicts, and a brief explanation for any requested lens that does not apply.

Pair a compact overview with a detailed reference when one diagram cannot serve both orientation and investigation.
Use Mermaid flowcharts for topology, ER diagrams for records, and sequence diagrams for lifecycle order.
For a planned change, show explicit BEFORE and AFTER views for every affected lens; mark additions green, removals red, and modifications amber.
Keep current state and proposals visibly separate.

## Validation

Check each material claim against its cited source and reconcile conflicting evidence.
Parse and render every Mermaid diagram and run this skill's complexity and colour-contrast gates.
Verify editable draw.io diagrams reopen and their provider icons match labelled services.
Run the prose gate on authored prose when available and resolve its findings without altering accurate quotations.
For HTML modes, inspect the generated output and verify the requested live or inline behaviour.
Report the source revisions, validation results, and any source or rendering limits.
