# Host support and Mermaid families

Verify the target host's Mermaid version before selecting a diagram family.
A family that renders locally may not be supported by GitHub, GitLab or another Markdown host.
Use the host's own version diagnostic or documentation rather than assuming local CLI support is equivalent.

Publish native Mermaid fences as the documentation source.
When the requested family is unavailable, choose a supported representation that preserves the model or report the limitation.
Do not discard attributes, relationships or meaningful groups merely to obtain a simpler diagram.
Do not force every family into flowchart syntax to apply colors.

Use the active design profile or prebuilt OsakaNights and the styling mechanisms supported by the selected family.
See [profile-driven theming](color_theming.md) for category, shade, compound, entity and sequence rules.

Wrap a standalone .mmd diagram in a Mermaid fence in Markdown before running Slopstopper.
Its CLI accepts Markdown files, directories, globs or standard input.
Render final diagrams in both target themes and inspect the PNGs locally.
Keep verification images under ignored scratch storage such as tmp/diagrams/.
Do not commit generated images or replace the Mermaid fence with an image, base64 payload or source-hiding disclosure.
Explicit user requests for image artifacts still take precedence.
