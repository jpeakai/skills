# Learned: mermaid fences must pass the parse gate before the companion ships

- **Date:** 2026-07-10
- **Case:** `tmp/richdocs/pds-content-structure-au.md:70-91` — a `mindmap`
  fence authored with quoted-string labels (`"(a) significant benefits"`) and
  an HTML entity (`&amp;`) rendered as a broken diagram in the HTML companion.
- **Ruling (user):** richdocs must not hand off a companion containing an
  unparseable mermaid fence. Follow-up ruling (see `adjudications.md`): the
  gate must be richdocs' own vendored copy, not a sibling skill's.
- **Root cause:** mermaid's mindmap grammar has no quoted-string node labels
  and no HTML-entity decoding — the fence yields 0 nodes. `md2html.py`
  passes fences through verbatim, so authoring errors surface only in the
  browser, after handoff.
- **The check (deterministic, free):**

  ```bash
  bunx @jpeakai/mermaidjs-lint SOURCE.md
  ```

  `parse-diagram-unparseable … yielded 0 nodes` = the fence is invalid
  mermaid, exit 1, blocker. (Until 2026-10 this check ran the vendored
  `mermaid_complexity.ts`; ADR-025 moved it to the published lint, which reads
  the same parsers and reports this case under the new rule id.) Run it on the *source* markdown before `md2html.py`, and treat a
  non-zero exit as not-done (escalators-not-stairs).
- **Mindmap-specific traps** (all confirmed in this case): quoted labels,
  leading `(`/`)` in plain text (parses as a shape delimiter), HTML entities
  like `&amp;`. Fix by rewriting labels as plain ASCII text
  (`a. significant benefits`, `fees and charges schedule`).
