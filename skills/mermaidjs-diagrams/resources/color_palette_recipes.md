# Profile category assignment patterns

All colors come from the active design profile, or the prebuilt OsakaNights fallback.
Use [profile-driven theming](color_theming.md) for resolution, boundaries, entity rows and sequence groups.
This reference assigns semantic families to slots; it defines no additional palette.

## Architecture

Assign slots in first-appearance order to actual system boundaries or responsibility families.
Keep an API and its workers in one family when they share a boundary; separate storage only when it represents another responsibility.
Use same-family shades for meaningful internal layers rather than assigning architectural meanings to fixed colors.

## Data flow

Group sources, transformations and consumers by the actual ownership or processing families in the supplied model.
Reuse the same mappings in an overview and its detailed pipelines.
Use a sequential ramp only when magnitude or order is the encoded dimension.

## Workflow

Use categorical families for owners or phases, and status tokens for actual success, warning or failure states.
Keep labels and signs alongside status colors.
A green-looking categorical slot does not become the success token.

## Dense graphs

Group by responsibility before assigning hue slots.
Use five-shade families for related subcategories and keep their assignments stable across views.
When the available categories cannot carry the model clearly, split the graph instead of cycling hues.

## Boundaries and leaves

Resolve the 16 percent category tint against the actual canvas or immediate parent surface.
Use an opaque same-family border verified against the tint.
Choose a distinct leaf shade and a foreground that reads on that leaf.
Palette preference never overrides text or border contrast.

## Worked examples

Read the active palette with `design_profile.ts palette --mode light` and again with `--mode dark`.
Resolve chosen slots to concrete supported colors before authoring Mermaid styles.
Existing example colors illustrate syntax; they are not another palette authority.
Keep verification PNGs local and publish native Mermaid source.
