// Tests for design_profile.ts: the five-tier cascade, .default-profile, the DTCG
// reader, and the Mermaid config and lint flags it builds from a real profile.

import { describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  candidateDirs,
  defaultProfileName,
  extension,
  group,
  lintFlags,
  loadProfile,
  main,
  mermaidConfig,
  modes,
  type ProfileDoc,
  type Roots,
  readTokens,
  resolveProfile,
  SKILL,
} from "./design_profile.ts";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const FIXTURE = join(SCRIPT_DIR, "testdata", "osakanights", "design-tokens.json");
const SCRATCH = join(SCRIPT_DIR, "..", "..", "..", "tmp", "design_profile_test");
mkdirSync(SCRATCH, { recursive: true });

const roots = (): Roots => {
  const base = mkdtempSync(join(SCRATCH, "case-"));
  return { project: join(base, "project"), home: join(base, "home") };
};

const store = (root: string, name: string, doc: string = readFileSync(FIXTURE, "utf-8")): string => {
  const dir = join(root, ".design-profiles", name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "design-tokens.json"), doc);
  return join(dir, "design-tokens.json");
};

const setDefault = (root: string, text: string): void => {
  mkdirSync(join(root, ".design-profiles"), { recursive: true });
  writeFileSync(join(root, ".design-profiles", ".default-profile"), text);
};

const docWith = (light: object, dark: object = light): ProfileDoc => ({
  modifiers: {
    mode: {
      contexts: { light: [light as Record<string, unknown>], dark: [dark as Record<string, unknown>] },
      default: "light",
    },
  },
});

describe("resolver", () => {
  test("candidate dirs follow the five-tier order", () => {
    const r = { project: "/p", home: "/h" };
    const tail = join("skills", "x", "resources", "profile", "b");
    expect(candidateDirs("b", "x", r)).toEqual([
      "/p/.design-profiles/b",
      "/h/.design-profiles/b",
      join("/p/.codex", tail),
      join("/p/.claude", tail),
      join("/h/.codex", tail),
      join("/h/.claude", tail),
    ]);
  });

  test("the first tier holding a profile wins", () => {
    const r = roots();
    const user = store(r.home, "b");
    expect(resolveProfile("b", SKILL, r)).toBe(user);
    const local = store(r.project, "b");
    expect(resolveProfile("b", SKILL, r)).toBe(local);
  });

  test("a skill tier is found after the shared store", () => {
    const r = roots();
    const dir = join(r.project, ".claude", "skills", SKILL, "resources", "profile", "b");
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "design-tokens.json"), "{}");
    expect(resolveProfile("b", SKILL, r)).toBe(join(dir, "design-tokens.json"));
  });

  test("no name and no default is tier 5", () => {
    expect(resolveProfile(null, SKILL, roots())).toBeNull();
  });

  test(".default-profile resolves through the same cascade, project first", () => {
    const r = roots();
    const target = store(r.home, "b");
    setDefault(r.home, "ghost");
    setDefault(r.project, "b\n");
    expect(defaultProfileName(r)).toBe("b");
    expect(resolveProfile(null, SKILL, r)).toBe(target);
  });

  test("a name that resolves nowhere fails loudly, naming its source", () => {
    const r = roots();
    expect(() => resolveProfile("ghost", SKILL, r)).toThrow("'ghost' (from --design-profile) resolves nowhere");
    setDefault(r.home, "ghost");
    expect(() => resolveProfile(null, SKILL, r)).toThrow("(from .default-profile)");
  });

  test("an empty .default-profile fails loudly", () => {
    const r = roots();
    setDefault(r.project, " \n");
    expect(() => defaultProfileName(r)).toThrow("is empty");
  });
});

describe("reader", () => {
  const colour = (hex: string, alpha?: number): object => ({ colorSpace: "srgb", components: [0, 0, 0], hex, alpha });
  const tree = {
    color: {
      $type: "color",
      text: { default: { $value: colour("#111111") }, subtle: { $value: colour("#222222") } },
      border: { default: { $value: colour("#111111", 0.14) }, focused: { $value: "{color.link}" } },
      link: { $value: "{color.text.default}" },
    },
    font: { $type: "fontFamily", family: { body: { $value: ["Fira Sans", "sans-serif"] } } },
    size: { gap: { $type: "number", $value: 4 } },
  };

  test("flattens, restores bare names and resolves alias chains", () => {
    const flat = readTokens(docWith(tree));
    expect(flat["color.text"]).toBe("#111111");
    expect(flat["color.border"]).toBe("#11111124");
    expect(flat["color.border.focused"]).toBe("#111111");
    expect(flat["font.family.body"]).toBe("'Fira Sans', sans-serif");
    expect(flat["size.gap"]).toBe(4);
    expect(group(flat, "color.text")).toEqual({ subtle: "#222222" });
  });

  test("merges a mode's sets and rejects an unknown mode", () => {
    const doc = docWith(tree);
    doc.modifiers.mode.contexts.light?.push({ color: { link: { $value: "{color.text.subtle}" } } });
    expect(readTokens(doc, "light")["color.link"]).toBe("#222222");
    expect(modes(doc)).toEqual(["light", "dark"]);
    expect(extension(doc)).toEqual({});
    expect(() => readTokens(doc, "sepia")).toThrow("no mode 'sepia'");
  });

  test.each([
    [{ a: { $value: "{b}" }, b: { $value: "{a}" } }, "alias cycle"],
    [{ a: { $value: "{nowhere}" } }, "does not define"],
  ])("rejects a broken alias", (bad, message) => {
    expect(() => readTokens(docWith(bad))).toThrow(message);
  });
});

describe("a real profile", () => {
  const doc = loadProfile(FIXTURE);

  test("the mermaid config sets every themeVariables key from the profile, per mode", () => {
    for (const mode of ["light", "dark"]) {
      const flat = readTokens(doc, mode);
      const config = mermaidConfig(doc, mode);
      expect(config.theme).toBe("base");
      expect(config.themeVariables.primaryColor).toBe(flat["color.background.brand.subtlest"]);
      expect(config.themeVariables.cScale0).toBe(flat["color.chart.categorical.1"]);
      expect(config.themeVariables.darkMode).toBe(mode === "dark");
      expect(String(config.themeVariables.fontFamily)).toContain("Fira Sans");
      // Mermaid drops 8-digit hex for some keys, so every colour is opaque.
      for (const [key, value] of Object.entries(config.themeVariables)) {
        if (typeof value === "string" && value.startsWith("#")) expect([key, value.length]).toEqual([key, 7]);
      }
    }
  });

  test("the lint flags put diagrams on the profile's background", () => {
    expect(lintFlags(doc)).toEqual([
      "--profile",
      "github",
      "--canvas-light",
      String(readTokens(doc, "light")["color.surface"]),
      "--canvas-dark",
      String(readTokens(doc, "dark")["color.surface"]),
    ]);
    expect(extension(doc).profile).toBe("osakanights");
  });
});

describe("cli", () => {
  test("help when asked or with no command", () => {
    expect(main([], roots())).toContain("Usage: design_profile.ts");
    expect(main(["--help"], roots())).toContain("mermaid-config");
  });

  test("status says which applies", () => {
    const r = roots();
    expect(main(["status"], r)).toBe("profile: none (this skill's own palettes apply)");
    const path = store(r.project, "b");
    expect(main(["status", "--design-profile", "b"], r)).toBe(`profile: ${path}`);
  });

  test("mermaid-config and lint-flags read the named or default profile", () => {
    const r = roots();
    store(r.project, "b");
    const dark = JSON.parse(main(["mermaid-config", "--design-profile", "b", "--mode", "dark"], r));
    expect(dark.themeVariables.darkMode).toBe(true);
    setDefault(r.project, "b");
    const byDefault = JSON.parse(main(["mermaid-config"], r));
    expect(byDefault.themeVariables.darkMode).toBe(true); // osakanights defaults to dark
    expect(main(["lint-flags"], r)).toStartWith("--profile github --canvas-light #");
  });

  test("a command that needs a profile fails without one", () => {
    expect(() => main(["mermaid-config"], roots())).toThrow("no design profile");
    expect(() => main(["frobnicate"], roots())).toThrow("unknown command");
  });
});
