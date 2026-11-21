// The header's contract with the classic helpers. viewer_toc.test.ts and
// viewer_zoom.test.ts in the skill stand in a fixture for this component, so
// these attributes are what keeps that fixture honest.
import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";

import { Header } from "./Header";

const html = renderToStaticMarkup(
  <Header title="Doc &lt;1&gt;" source="doc.md" buildId="B1" initialTheme="light" onThemeChange={() => {}} />,
);

describe("Header", () => {
  test("is the header.rd-header that viewer-toc.js measures", () => {
    expect(html).toStartWith('<header class="rd-header');
  });

  test("renders the contents toggle hidden, collapsed and wired to #rd-toc", () => {
    const toggle = html.match(/<button[^>]*id="rd-toc-toggle"[^>]*>/)?.[0] ?? "";
    expect(toggle).toContain('aria-controls="rd-toc"');
    expect(toggle).toContain('aria-expanded="false"');
    expect(toggle).toMatch(/\shidden(=""|\s|>)/);
  });

  test("carries the title id the sidebar reserves, and escapes the title", () => {
    expect(html).toContain('id="rd-title"');
    expect(html).toContain("Doc &lt;1&gt;");
  });

  test("shows the source and build, and a labelled theme toggle", () => {
    expect(html).toContain("doc.md");
    expect(html).toMatch(/build (<!-- -->)?B1/);
    expect(html).toMatch(/id="rd-theme-toggle"[^>]*aria-label="Toggle theme"/);
  });
});
