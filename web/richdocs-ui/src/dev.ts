// Dev-server entry only; the production build never includes it. It stands in
// for md2html.py: the #rd-config block, the inline-mode globals, and the
// classic helpers evaluated as global scripts, then the real viewer entry.
import cytoscapeJs from "../../../skills/richdocs/assets/viewer-cytoscape.js?raw";
import deckglJs from "../../../skills/richdocs/assets/viewer-deckgl.js?raw";
import tocCss from "../../../skills/richdocs/assets/viewer-toc.css?raw";
import tocJs from "../../../skills/richdocs/assets/viewer-toc.js?raw";
import zoomCss from "../../../skills/richdocs/assets/viewer-zoom.css?raw";
import zoomJs from "../../../skills/richdocs/assets/viewer-zoom.js?raw";
import tokens from "../../../skills/richdocs/assets/design-tokens.json";

const SAMPLE = `# richdocs dev page

A paragraph with a [link](#flow), \`inline code\` and **bold** text.

## Lists

- one
- two

## Flow

\`\`\`mermaid
flowchart LR
    A["Source"] --> B["Render"] --> C["Page"]
\`\`\`

## Table

| Name | Value |
|------|-------|
| a    | 1     |
`;

for (const css of [tocCss, zoomCss]) {
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
}
for (const js of [cytoscapeJs, tocJs, zoomJs, deckglJs]) {
  const script = document.createElement("script");
  script.textContent = js;
  document.body.appendChild(script);
}

const config = document.createElement("script");
config.type = "application/json";
config.id = "rd-config";
config.textContent = JSON.stringify({
  buildId: "dev",
  source: "dev.md",
  title: "richdocs dev",
  cdn: {},
  fallbackTokens: tokens,
});
document.body.appendChild(config);
window.__DOC_MD__ = SAMPLE;
window.__DOC_TOKENS__ = tokens as unknown as NonNullable<Window["__DOC_TOKENS__"]>;

await import("./viewer/main");
