// Tests for mermaid_contrast.ts.
//
// Strategy:
//   - Unit-test scoreDirectives() against hand-crafted StyleDirective arrays
//     (no parsing — pure scoring logic).
//   - Integration-test auditContent() against mermaid sources that exercise
//     classDef, style, fill+color pairs, fill+stroke pairs, and the
//     "only-fill-declared" skipped case.
//   - Verify the CLI returns exit 1 on any AA failure and 0 on all pass.

import { describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  auditContent,
  auditFile,
  detectProfile,
  main,
  scoreDirectives,
  scoreDirectivesEr,
  scoreDirectivesMkdocs,
  scoreForProfile,
} from "./mermaid_contrast.ts";
import type { StyleDirective } from "./color_contrast.ts";

// ─── Scoring logic (hand-crafted directives, no parser involved) ─────────────

describe("scoreDirectives", () => {
  test("fill+color pair is scored as text (AA threshold 4.5)", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "good", properties: { fill: "#2563eb", color: "#ffffff" }, line: 1 },
    ];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(1);
    expect(pairs[0]?.kind).toBe("text");
    expect(pairs[0]?.passes).toBe(true);
    expect(pairs[0]?.assessment.ratio).toBeCloseTo(5.17, 2);
    expect(skipped).toHaveLength(0);
  });

  test("fill+stroke pair is scored as border (AA threshold 3.0)", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "x", properties: { fill: "#ffffff", stroke: "#777777" }, line: 1 },
    ];
    const { pairs } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(1);
    expect(pairs[0]?.kind).toBe("border");
    // #777 on #fff = 4.48 — passes 3.0 border threshold.
    expect(pairs[0]?.passes).toBe(true);
    expect(pairs[0]?.assessment.ratio).toBeCloseTo(4.48, 2);
  });

  test("fill+color AND fill+stroke yields TWO pairs (text + border)", () => {
    const dirs: StyleDirective[] = [
      {
        kind: "classDef",
        selector: "both",
        properties: { fill: "#2563eb", color: "#fff", stroke: "#1e40af" },
        line: 1,
      },
    ];
    const { pairs } = scoreDirectives(dirs);
    expect(pairs.map((p) => p.kind).sort()).toEqual(["border", "text"]);
  });

  test("missing fill skips the directive with a clear reason", () => {
    const dirs: StyleDirective[] = [{ kind: "classDef", selector: "orphan", properties: { color: "#fff" }, line: 1 }];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(0);
    expect(skipped).toHaveLength(1);
    expect(skipped[0]?.reason).toMatch(/no fill declared/);
  });

  test("only fill declared — BLOCKING: github requires a color: beside every fill:", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "fill-only", properties: { fill: "#2563eb" }, line: 1 },
    ];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(0);
    expect(skipped[0]?.reason).toMatch(/no color: declared/);
    // Not an informational skip: an unscoreable mandatory pair must gate, or the
    // audit exits 0 on a text pair it never checked.
    expect(skipped[0]?.blocking).toBe(true);
  });

  test("inlineClass and linkStyle are NOT scored (informational)", () => {
    const dirs: StyleDirective[] = [
      { kind: "inlineClass", selector: "A", class_name: "good", properties: {}, line: 1 },
      { kind: "linkStyle", selector: "0", properties: { stroke: "#777" }, line: 2 },
    ];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(0);
    expect(skipped).toHaveLength(0);
  });

  test("failing text pair is flagged", () => {
    const dirs: StyleDirective[] = [
      // Yellow-on-yellow-ish: fails AA hard.
      { kind: "classDef", selector: "bad", properties: { fill: "#fbbf24", color: "#f3f4f6" }, line: 1 },
    ];
    const { pairs } = scoreDirectives(dirs);
    expect(pairs[0]?.passes).toBe(false);
    expect(pairs[0]?.assessment.rating).toBe("Fail");
  });
});

// ─── Integration: mermaid source → report ────────────────────────────────────

describe("auditContent", () => {
  test("full flowchart source: passing + failing pairs counted correctly", () => {
    const src = `flowchart LR
    A:::good --> B:::bad
    classDef good fill:#2563eb,stroke:#1e40af,color:#ffffff
    classDef bad  fill:#fbbf24,color:#f3f4f6
`;
    const report = auditContent(src);
    expect(report.pass_count).toBe(1); // good/text passes (5.17)
    expect(report.fail_count).toBe(2); // good/border fails (1.69), bad/text fails (1.52)
  });

  test("mixed color syntaxes round-trip through the parser", () => {
    const src = `flowchart LR
    classDef mixed fill:rgb(37 99 235),color:oklch(0.98 0 0),stroke:hsl(220 80% 30%)
`;
    const report = auditContent(src);
    expect(report.pairs).toHaveLength(2);
    // text pair should pass (oklch near-white on blue ≈ 4.88)
    const textPair = report.pairs.find((p) => p.kind === "text");
    expect(textPair).toBeDefined();
    expect(textPair?.passes).toBe(true);
  });
});

// ─── Integration: markdown file with fences (absolute line numbers) ──────────

describe("auditFile — absolute line numbers", () => {
  const tmp = mkdtempSync(join(tmpdir(), "mermaid-contrast-"));

  test("line numbers are offset by fence start in .md files", async () => {
    const md = `# Doc

Prose above the diagram.

\`\`\`mermaid
flowchart LR
    A --> B
    classDef good fill:#2563eb,color:#ffffff
\`\`\`
`;
    const path = join(tmp, "sample.md");
    writeFileSync(path, md);
    const reports = await auditFile(path);
    expect(reports).toHaveLength(1);
    expect(reports[0]?.fence?.line_start).toBe(5);
    // classDef is on fence-local line 3, so absolute line = 5 + 3 = 8.
    expect(reports[0]?.pairs[0]?.line).toBe(8);
  });

  test(".mmd file gets no fence offset (file-relative line numbers)", async () => {
    const src = `flowchart LR
    A --> B
    classDef good fill:#2563eb,color:#ffffff
`;
    const path = join(tmp, "sample.mmd");
    writeFileSync(path, src);
    const reports = await auditFile(path);
    expect(reports[0]?.fence).toBeUndefined();
    expect(reports[0]?.pairs[0]?.line).toBe(3);
  });
});

// ─── scoreDirectives — unparseable color catch branches ────────────────────

describe("scoreDirectives — unparseable colors route to skipped with reasons", () => {
  test("unparseable color (text pair) is routed to skipped with 'text pair unparseable'", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "bad-text", properties: { fill: "#2563eb", color: "not-a-color" }, line: 7 },
    ];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(0);
    expect(skipped).toHaveLength(1);
    expect(skipped[0]?.reason).toMatch(/text pair unparseable/);
    expect(skipped[0]?.line).toBe(7);
  });

  test("unparseable color (border pair) is routed to skipped with 'border pair unparseable'", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "bad-border", properties: { fill: "#2563eb", stroke: "not-a-color" }, line: 9 },
    ];
    const { pairs, skipped } = scoreDirectives(dirs);
    expect(pairs).toHaveLength(0);
    // Two gaps now: the missing color: and the unparseable stroke. Both block.
    expect(skipped).toHaveLength(2);
    expect(skipped.some((s) => /border pair unparseable/.test(s.reason))).toBe(true);
    expect(skipped.every((s) => s.blocking)).toBe(true);
  });
});

// ─── mkdocs-material profile (host forces text; composite over both themes) ──

describe("scoreDirectivesMkdocs", () => {
  test("translucent fill yields passing text pairs in BOTH themes; color: ignored", () => {
    const dirs: StyleDirective[] = [
      {
        kind: "classDef",
        selector: "entity",
        properties: { fill: "#1d4ed836", stroke: "#3b82f6", color: "#fff" },
        line: 1,
      },
    ];
    const { pairs, skipped } = scoreDirectivesMkdocs(dirs);
    const text = pairs.filter((p) => p.kind === "text");
    expect(text.map((p) => p.theme).sort()).toEqual(["dark", "light"]);
    expect(text.every((p) => p.passes)).toBe(true); // AAA both themes
    expect(skipped.some((s) => /color: ignored/.test(s.reason))).toBe(true);
  });

  test("border pairs are advisory (reported, not gating)", () => {
    const { pairs } = scoreDirectivesMkdocs([
      { kind: "classDef", selector: "meas", properties: { fill: "#0478572e", stroke: "#10b981" }, line: 1 },
    ]);
    const borders = pairs.filter((p) => p.kind === "border");
    expect(borders).toHaveLength(2);
    expect(borders.every((p) => p.advisory === true)).toBe(true);
  });

  test("an OPAQUE fill fails the forced light text in DARK mode (the bug, now caught)", () => {
    const { pairs } = scoreDirectivesMkdocs([
      { kind: "classDef", selector: "q", properties: { fill: "#cbd5e1", stroke: "#64748b" }, line: 1 },
    ]);
    const darkText = pairs.find((p) => p.kind === "text" && p.theme === "dark");
    expect(darkText?.passes).toBe(false);
    const lightText = pairs.find((p) => p.kind === "text" && p.theme === "light");
    expect(lightText?.passes).toBe(true); // opaque pale fill is fine in light
  });

  test("missing fill is skipped (nothing to anchor)", () => {
    const { pairs, skipped } = scoreDirectivesMkdocs([
      { kind: "classDef", selector: "x", properties: { color: "#fff" }, line: 1 },
    ]);
    expect(pairs).toHaveLength(0);
    expect(skipped[0]?.reason).toMatch(/nothing to anchor/);
  });

  test("unparseable fill is skipped with reason", () => {
    const { pairs, skipped } = scoreDirectivesMkdocs([
      { kind: "classDef", selector: "x", properties: { fill: "not-a-color" }, line: 1 },
    ]);
    expect(pairs).toHaveLength(0);
    expect(skipped.some((s) => /fill unparseable/.test(s.reason))).toBe(true);
  });

  test("unparseable stroke routes the border pair to skipped", () => {
    const { skipped } = scoreDirectivesMkdocs([
      { kind: "classDef", selector: "x", properties: { fill: "#1d4ed836", stroke: "not-a-color" }, line: 1 },
    ]);
    expect(skipped.some((s) => /border pair unparseable/.test(s.reason))).toBe(true);
  });

  test("non-classDef/style directives are ignored", () => {
    const { pairs, skipped } = scoreDirectivesMkdocs([
      { kind: "linkStyle", selector: "0", properties: { stroke: "#777" }, line: 1 },
    ]);
    expect(pairs).toHaveLength(0);
    expect(skipped).toHaveLength(0);
  });
});

describe("scoreForProfile + auditContent profile", () => {
  test("dispatches to github vs mkdocs-material", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "e", properties: { fill: "#1d4ed836", stroke: "#3b82f6" }, line: 1 },
    ];
    const gh = scoreForProfile(dirs, "github");
    const md = scoreForProfile(dirs, "mkdocs-material");
    // github: the fill is translucent, so it is composited over BOTH GitHub
    // canvases and scored per theme — a fill that reads on one and vanishes on
    // the other must not pass.
    expect(gh.pairs.some((p) => p.theme === "light")).toBe(true);
    expect(gh.pairs.some((p) => p.theme === "dark")).toBe(true);
    // mkdocs: per-theme pairs present.
    expect(md.pairs.some((p) => p.theme === "dark")).toBe(true);
  });

  test("github does NOT split an OPAQUE fill per theme (same on both canvases)", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "solid", properties: { fill: "#1e40af", color: "#ffffff" }, line: 1 },
    ];
    const gh = scoreForProfile(dirs, "github");
    expect(gh.pairs).toHaveLength(1);
    expect(gh.pairs[0]?.theme).toBeUndefined();
  });

  test("auditContent carries the profile and gates on text only under mkdocs", () => {
    const src = `flowchart LR\n  classDef entity fill:#1d4ed836,stroke:#3b82f6,stroke-width:2px\n`;
    const r = auditContent(src, "<inline>", "mkdocs-material");
    expect(r.profile).toBe("mkdocs-material");
    expect(r.fail_count).toBe(0); // text AAA both themes; border advisory excluded
  });
});

// ─── erDiagram (fill lands on even rows only; odd rows keep the theme surface) ─

describe("scoreDirectivesEr", () => {
  const ERD = (classDef: string): string => `erDiagram
    A ||--o{ B : "has"
    A { string one "first"
        string two "second" }
    B { string x "ex" }
    ${classDef}
    class A,B styled
`;

  test("opaque light fill + dark color: FAILS on the dark theme's odd rows (jpeakai/skills#6)", () => {
    const r = auditContent(ERD("classDef styled fill:#fef3c7,stroke:#b45309,color:#1e293b"));
    const darkOdd = r.pairs.find((p) => p.kind === "text" && p.theme === "dark" && p.row === "odd");
    expect(darkOdd?.passes).toBe(false);
    expect(darkOdd?.assessment.ratio).toBeLessThan(1.2);
    expect(r.fail_count).toBeGreaterThan(0);
  });

  test("opaque dark fill + white color: FAILS on the light theme's odd rows", () => {
    const r = auditContent(ERD("classDef styled fill:#1e40af,stroke:#1e3a8a,color:#ffffff"));
    const lightOdd = r.pairs.find((p) => p.kind === "text" && p.theme === "light" && p.row === "odd");
    expect(lightOdd?.passes).toBe(false);
    expect(lightOdd?.assessment.ratio).toBe(1);
  });

  test("translucent fill, no color:, opaque stroke: passes in both themes", () => {
    const r = auditContent(ERD("classDef styled fill:#b4530966,stroke:#d97706,stroke-width:2px"));
    expect(r.fail_count).toBe(0);
    // No blocking "no color:" gap — dropping color: is the recipe here.
    expect(r.skipped).toHaveLength(0);
    // Theme label is scored only on the author's fill (even rows), never on the
    // renderer's own odd-row pair.
    const text = r.pairs.filter((p) => p.kind === "text");
    expect(text.map((p) => `${p.theme}/${p.row}`).sort()).toEqual(["dark/even", "light/even"]);
    expect(text.find((p) => p.theme === "dark")?.foreground).toBe("#cccccc");
    // 8-digit alpha is composited over the theme's even row, not truncated.
    expect(text.find((p) => p.theme === "light")?.background).not.toBe("#b45309");
  });

  test("strokes are scored on both rows and are advisory", () => {
    const { pairs } = scoreDirectivesEr([
      { kind: "classDef", selector: "s", properties: { fill: "#b4530966", stroke: "#d97706" }, line: 1 },
    ]);
    const borders = pairs.filter((p) => p.kind === "border");
    expect(borders).toHaveLength(4);
    expect(borders.every((p) => p.advisory)).toBe(true);
    expect(borders.some((p) => !p.passes)).toBe(true);
  });

  test("color: without fill is scored against both theme rows", () => {
    const { pairs } = scoreDirectivesEr([{ kind: "style", selector: "A", properties: { color: "#1e293b" }, line: 1 }]);
    expect(pairs).toHaveLength(4);
    expect(pairs.find((p) => p.theme === "dark" && p.row === "even")?.background).toBe("#060606");
  });

  test("a directive with no colour properties, and non-style kinds, are not scored", () => {
    const { pairs, skipped } = scoreDirectivesEr([
      { kind: "classDef", selector: "w", properties: { "stroke-width": "2px" }, line: 1 },
      { kind: "linkStyle", selector: "0", properties: { stroke: "#777" }, line: 2 },
    ]);
    expect(pairs).toHaveLength(0);
    expect(skipped).toHaveLength(1);
    expect(skipped[0]?.reason).toMatch(/no color properties/);
  });

  test("an unparseable colour blocks and keeps none of the directive's pairs", () => {
    const { pairs, skipped } = scoreDirectivesEr([
      { kind: "classDef", selector: "x", properties: { fill: "#fef3c7", stroke: "not-a-color" }, line: 1 },
    ]);
    expect(pairs).toHaveLength(0);
    expect(skipped[0]?.blocking).toBe(true);
    expect(skipped[0]?.reason).toMatch(/erDiagram pair unparseable/);
  });

  test("dispatch: erDiagram only switches model under github, and frontmatter is skipped", () => {
    const dirs: StyleDirective[] = [
      { kind: "classDef", selector: "e", properties: { fill: "#fef3c7", color: "#1e293b" }, line: 1 },
    ];
    expect(scoreForProfile(dirs, "github", "erDiagram").pairs.every((p) => p.row)).toBe(true);
    expect(scoreForProfile(dirs, "github", "flowchart").pairs[0]?.row).toBeUndefined();
    expect(scoreForProfile(dirs, "mkdocs-material", "erDiagram").pairs[0]?.row).toBeUndefined();
    const withFrontmatter = `---\ntitle: x\n---\n${ERD("classDef styled fill:#fef3c7,color:#1e293b")}`;
    expect(auditContent(withFrontmatter).pairs.some((p) => p.row)).toBe(true);
  });

  test("CLI default output renders the theme/row tag and exits 1", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "mermaid-contrast-er-"));
    const path = join(tmp, "erd.md");
    writeFileSync(path, `# ERD\n\n\`\`\`mermaid\n${ERD("classDef styled fill:#fef3c7,color:#1e293b")}\`\`\`\n`);
    expect(await main([path])).toBe(1);
  });
});

describe("detectProfile", () => {
  const base = mkdtempSync(join(tmpdir(), "mermaid-detect-"));

  test("an ancestor mkdocs.yml ⇒ mkdocs-material", () => {
    const proj = join(base, "site");
    mkdirSync(join(proj, "docs"), { recursive: true });
    writeFileSync(join(proj, "mkdocs.yml"), "site_name: x\n");
    expect(detectProfile(join(proj, "docs", "page.md"))).toBe("mkdocs-material");
  });

  test("no ancestor mkdocs.yml ⇒ github", () => {
    // os tmpdir has no mkdocs.yml ancestor → github.
    expect(detectProfile(join(base, "lonely.md"))).toBe("github");
  });
});

// ─── CLI entry ───────────────────────────────────────────────────────────────

describe("main() CLI", () => {
  const tmp = mkdtempSync(join(tmpdir(), "mermaid-contrast-cli-"));

  test("--help returns 0", async () => {
    expect(await main(["--help"])).toBe(0);
  });

  test("no args returns 2", async () => {
    expect(await main([])).toBe(2);
  });

  test("passing file returns 0", async () => {
    const path = join(tmp, "pass.mmd");
    writeFileSync(path, `flowchart LR\n    A --> B\n    classDef good fill:#2563eb,color:#ffffff\n`);
    expect(await main(["--json", path])).toBe(0);
  });

  test("failing file returns 1", async () => {
    const path = join(tmp, "fail.mmd");
    writeFileSync(path, `flowchart LR\n    A --> B\n    classDef bad fill:#fbbf24,color:#f3f4f6\n`);
    expect(await main(["--json", path])).toBe(1);
  });

  test("unknown flag returns 2 (argparse error path)", async () => {
    // Exercises the parseArgs catch branch (lines 325-327).
    expect(await main(["--nonsense-flag"])).toBe(2);
  });

  test("non-existent path is a usage error (2), not a contrast failure (1)", async () => {
    // collectFiles logs a warning via its statSync catch and returns 0 files;
    // main reports "no matching files" and exits 2 so CI can tell a typo from a real failure.
    const bogus = join(tmp, `does-not-exist-${Date.now()}`);
    expect(await main([bogus])).toBe(2);
  });

  test("passes a DIRECTORY — exercises collectFiles directory branch + default output", async () => {
    // collectFiles directory branch (lines 275-279) filters by extension.
    // Default (non-json, non-summary) output path exercises formatReport + formatSummary
    // (lines 226-252, 256-260, 354-360).
    const dir = join(tmp, `dirtest-${Date.now()}`);
    mkdirSync(dir, { recursive: true });
    writeFileSync(
      join(dir, "a.mmd"),
      `flowchart LR\n    A --> B\n    classDef good fill:#2563eb,color:#ffffff,stroke:#1e40af\n`,
    );
    writeFileSync(join(dir, "b.mmd"), `flowchart LR\n    A --> B\n    classDef bad fill:#fbbf24,color:#f3f4f6\n`);
    writeFileSync(join(dir, "ignored.txt"), "not a mermaid file");
    // Run in default output mode (no --json, no --summary) to exercise formatReport.
    const code = await main([dir]);
    // Mix of pass and fail → should return 1.
    expect(code).toBe(1);
  });

  test("--summary mode exercises formatSummary-only path", async () => {
    // Lines 354-355: values.summary branch in main().
    const path = join(tmp, "summary.mmd");
    writeFileSync(path, `flowchart LR\n    classDef good fill:#2563eb,color:#ffffff\n`);
    expect(await main(["--summary", path])).toBe(0);
  });

  test("--quiet suppresses passing reports in default output", async () => {
    // Line 358: values.quiet && r.fail_count === 0 → continue.
    const path = join(tmp, "quiet.mmd");
    writeFileSync(path, `flowchart LR\n    classDef good fill:#2563eb,color:#ffffff\n`);
    expect(await main(["--quiet", path])).toBe(0);
  });

  test("default output path prints per-report + summary for failing file", async () => {
    // Lines 357-361: the for/formatReport loop + final formatSummary.
    const path = join(tmp, "default-out.mmd");
    writeFileSync(path, `flowchart LR\n    classDef bad fill:#fbbf24,color:#f3f4f6\n`);
    expect(await main([path])).toBe(1);
  });

  test("empty-directives file renders the '(no style directives found)' branch", async () => {
    // Line 231-233: r.pairs.length === 0 && r.skipped.length === 0.
    const path = join(tmp, "empty.mmd");
    writeFileSync(path, `flowchart LR\n    A --> B\n`);
    expect(await main([path])).toBe(0);
  });

  test("markdown file with fence exercises the fence header branch in formatReport", async () => {
    // Line 228: r.fence truthy branch — needs a .md file with a mermaid fence.
    const path = join(tmp, "with-fence.md");
    writeFileSync(path, `# Doc\n\n\`\`\`mermaid\nflowchart LR\n    classDef bad fill:#fbbf24,color:#f3f4f6\n\`\`\`\n`);
    expect(await main([path])).toBe(1);
  });

  test("AA Large rating exercises the yellow rating color branch in formatReport", async () => {
    // rating === "AA Large" → yellow branch (line 240).
    const path = join(tmp, "aalarge.mmd");
    // #888 on #fff ≈ 3.54 (AA Large) — text fails 4.5 but not 3.0.
    writeFileSync(path, `flowchart LR\n    classDef border-ish fill:#ffffff,color:#888888\n`);
    expect(await main([path])).toBe(1);
  });

  test("skipped directive is rendered in default output (no-fill branch)", async () => {
    // Line 247-251: the r.skipped for-loop.
    const path = join(tmp, "skipped.mmd");
    writeFileSync(path, `flowchart LR\n    classDef orphan color:#ffffff\n`);
    // No fill → skipped, no pairs → fail_count=0 → returns 0.
    expect(await main([path])).toBe(0);
  });

  test("--profile mkdocs-material on a translucent diagram passes (advisory border formatter)", async () => {
    // Default output exercises the theme tag + advisory ⚠ branches in formatReport.
    const path = join(tmp, "mkdocs-ok.md");
    writeFileSync(
      path,
      `# D\n\n\`\`\`mermaid\nflowchart LR\n    A:::entity\n    classDef entity fill:#1d4ed836,stroke:#3b82f6,stroke-width:2px\n\`\`\`\n`,
    );
    expect(await main([path, "--profile", "mkdocs-material"])).toBe(0);
  });

  test("--profile mkdocs-material on an OPAQUE diagram fails (text invisible in dark)", async () => {
    const path = join(tmp, "mkdocs-bad.mmd");
    writeFileSync(path, `flowchart LR\n    classDef q fill:#cbd5e1,stroke:#64748b\n`);
    expect(await main([path, "--profile", "mkdocs-material"])).toBe(1);
  });

  test("explicit --profile github scores fill×color as before", async () => {
    const path = join(tmp, "gh.mmd");
    writeFileSync(path, `flowchart LR\n    classDef good fill:#2563eb,color:#ffffff\n`);
    expect(await main([path, "--profile", "github"])).toBe(0);
  });

  test("invalid --profile returns 2 (usage error)", async () => {
    const path = join(tmp, "p.mmd");
    writeFileSync(path, `flowchart LR\n    classDef good fill:#2563eb,color:#fff\n`);
    expect(await main([path, "--profile", "nonsense"])).toBe(2);
  });
});

// ─── CLI bootstrap via subprocess (exercises import.meta.main block) ────────

describe("CLI subprocess", () => {
  const scriptPath = new URL("./mermaid_contrast.ts", import.meta.url).pathname;
  const tmp = mkdtempSync(join(tmpdir(), "mermaid-contrast-sub-"));

  test("bootstrap runs end-to-end on a passing file", async () => {
    // Covers lines 369-373: main().then(process.exit).
    const path = join(tmp, "ok.mmd");
    writeFileSync(path, `flowchart LR\n    classDef good fill:#2563eb,color:#ffffff\n`);
    const proc = Bun.spawn(["bun", "run", scriptPath, "--json", path], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(await proc.exited).toBe(0);
  });
});
