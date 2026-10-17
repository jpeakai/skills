#!/usr/bin/env bun
// Find a design profile, read its design-tokens.json, and hand Mermaid its colours.

// ── Imports (stdlib first) ──────────────────────────────────────────────────
import { existsSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";

// A port of the design-profiles skill's profile_resolver.py. This skill never
// imports another skill's code, so it carries its own copy (DT-TOOL-1); the
// repository tests hold the two to the same answers on the same profile.
//
// A profile name resolves through five tiers, first hit wins (DT-LOC-1):
//   1  <project>/.design-profiles/<name>/
//   2  ~/.design-profiles/<name>/
//   3  <project>/.{codex,claude}/skills/<skill>/resources/profile/<name>/
//   4  ~/.{codex,claude}/skills/<skill>/resources/profile/<name>/
//   5  this skill's own palettes (resolveProfile returns null)

// ── Configuration ───────────────────────────────────────────────────────────
export const STORE = ".design-profiles";
export const DEFAULT_FILE = ".default-profile";
export const TOKENS_FILE = "design-tokens.json";
export const EXT = "ai.jpeak.design-profiles";
export const SKILL = "mermaidjs-diagrams";
const HARNESSES = [".codex", ".claude"];

export type Flat = Record<string, unknown>;
type Node = { [key: string]: unknown };
export interface ProfileDoc {
  modifiers: { mode: { contexts: Record<string, Node[]>; default: string; $extensions?: Record<string, Node> } };
}
export interface MermaidConfig {
  theme: "base";
  themeVariables: Flat;
}
export interface Roots {
  project: string;
  home: string;
}

const isFile = (path: string): boolean => existsSync(path) && statSync(path).isFile();

// ── Resolver ────────────────────────────────────────────────────────────────
export const candidateDirs = (name: string, skill: string, roots: Roots): string[] => {
  const tier = HARNESSES.map((h) => join(h, "skills", skill, "resources", "profile", name));
  return [
    join(roots.project, STORE, name),
    join(roots.home, STORE, name),
    ...tier.map((p) => join(roots.project, p)),
    ...tier.map((p) => join(roots.home, p)),
  ];
};

export const defaultProfileName = (roots: Roots): string | null => {
  for (const store of [join(roots.project, STORE), join(roots.home, STORE)]) {
    const marker = join(store, DEFAULT_FILE);
    if (isFile(marker)) {
      const name = readFileSync(marker, "utf-8").trim();
      if (!name) throw new Error(`${marker} is empty; it must name one profile`);
      return name;
    }
  }
  return null;
};

// The design-tokens.json for `name` (or the default profile), or null for tier 5.
export const resolveProfile = (name: string | null, skill: string, roots: Roots): string | null => {
  let source = "--design-profile";
  let wanted = name;
  if (wanted === null) {
    wanted = defaultProfileName(roots);
    if (wanted === null) return null;
    source = DEFAULT_FILE;
  }
  const tried = candidateDirs(wanted, skill, roots);
  for (const dir of tried) {
    if (isFile(join(dir, TOKENS_FILE))) return join(dir, TOKENS_FILE);
  }
  const listing = tried.map((d) => `  ${join(d, TOKENS_FILE)}`).join("\n");
  throw new Error(`design profile '${wanted}' (from ${source}) resolves nowhere. Tried:\n${listing}`);
};

// ── Reader ──────────────────────────────────────────────────────────────────
const isNode = (x: unknown): x is Node => typeof x === "object" && x !== null && !Array.isArray(x);

export const modes = (doc: ProfileDoc): string[] => Object.keys(doc.modifiers.mode.contexts);
export const defaultMode = (doc: ProfileDoc): string => String(doc.modifiers.mode.default);
export const extension = (doc: ProfileDoc): Node => doc.modifiers.mode.$extensions?.[EXT] ?? {};

const merge = (into: Node, src: Node): void => {
  for (const [key, value] of Object.entries(src)) {
    const target = into[key];
    if (isNode(value) && !("$value" in value) && isNode(target)) merge(target, value);
    else into[key] = value;
  }
};

const walk = (node: Node, path: string[], kind: string, out: Map<string, [string, unknown]>): void => {
  const here = typeof node.$type === "string" ? node.$type : kind;
  for (const [key, child] of Object.entries(node)) {
    if (key.startsWith("$") || !isNode(child)) continue;
    if ("$value" in child) {
      out.set([...path, key].join("."), [typeof child.$type === "string" ? child.$type : here, child.$value]);
    } else walk(child, [...path, key], here, out);
  }
};

const plain = (kind: string, value: unknown): unknown => {
  if (kind === "color" && isNode(value)) {
    const alpha = typeof value.alpha === "number" ? value.alpha : 1;
    const hex = String(value.hex);
    return alpha < 1
      ? hex +
          Math.round(alpha * 255)
            .toString(16)
            .padStart(2, "0")
      : hex;
  }
  if (kind === "fontFamily" && Array.isArray(value)) {
    return value.map((f) => (String(f).includes(" ") && !String(f).startsWith("'") ? `'${f}'` : f)).join(", ");
  }
  return value;
};

// Every token of one mode as `{dotted.path: plain value}`, aliases resolved.
// DTCG stores `color.text` as `color.text.default`; the flat name is the bare form.
export const readTokens = (doc: ProfileDoc, mode: string = defaultMode(doc)): Flat => {
  const contexts = doc.modifiers.mode.contexts;
  if (!(mode in contexts)) {
    throw new Error(`profile has no mode '${mode}'; it carries ${JSON.stringify(Object.keys(contexts).sort())}`);
  }
  const tree: Node = {};
  for (const set of contexts[mode] ?? []) merge(tree, set);
  const raw = new Map<string, [string, unknown]>();
  walk(tree, [], "", raw);

  const resolve = (path: string, seen: string[]): [string, unknown] => {
    if (seen.includes(path)) throw new Error(`alias cycle through ${[...seen, path].join(" -> ")}`);
    const entry = raw.get(path);
    if (!entry) throw new Error(`alias to '${path}', which the profile does not define`);
    const [kind, value] = entry;
    if (typeof value === "string" && value.startsWith("{") && value.endsWith("}")) {
      const [targetKind, target] = resolve(value.slice(1, -1), [...seen, path]);
      return [kind || targetKind, target];
    }
    return [kind, value];
  };

  const flat: Flat = {};
  for (const path of raw.keys()) {
    const [kind, value] = resolve(path, []);
    flat[path.replace(/\.default$/, "")] = plain(kind, value);
  }
  return flat;
};

export const group = (flat: Flat, prefix: string): Flat =>
  Object.fromEntries(
    Object.entries(flat)
      .filter(([k]) => k.startsWith(`${prefix}.`))
      .map(([k, v]) => [k.slice(prefix.length + 1), v]),
  );

// A DTCG resolver document as design-profiles builds it; trusted like any profile file.
export const loadProfile = (path: string): ProfileDoc => JSON.parse(readFileSync(path, "utf-8")) as ProfileDoc;

// ── Mermaid ─────────────────────────────────────────────────────────────────
// An mmdc config for one mode: the `base` theme with every themeVariables key the
// profile baked (`surface.mermaid`). Mermaid derives any key it is not given by hue
// rotation, so curation sets them all; this only renames.
export const mermaidConfig = (doc: ProfileDoc, mode: string): MermaidConfig => {
  const flat = readTokens(doc, mode);
  const themeVariables: Flat = { ...group(flat, "surface.mermaid"), darkMode: mode === "dark" };
  const font = flat["font.family.body"];
  if (typeof font === "string") themeVariables.fontFamily = font;
  return { theme: "base", themeVariables };
};

// The lint's canvas flags: the page a profile's diagrams are drawn on, per mode.
// `--profile` here is the lint's HOST profile (GitHub), not a design profile.
export const lintFlags = (doc: ProfileDoc): string[] => [
  "--profile",
  "github",
  "--canvas-light",
  String(readTokens(doc, "light")["surface.mermaid.background"]),
  "--canvas-dark",
  String(readTokens(doc, "dark")["surface.mermaid.background"]),
];

// ── CLI ─────────────────────────────────────────────────────────────────────
const HELP = [
  "Usage: design_profile.ts <command> [--design-profile NAME] [--mode light|dark]",
  "",
  "Read a design profile (from the design-profiles skill) for Mermaid.",
  "With no --design-profile, .design-profiles/.default-profile names one.",
  "",
  "Commands:",
  "  status          Which profile resolves, or that this skill's own palettes apply",
  "  mermaid-config  Print an mmdc config (theme base + themeVariables) for --mode",
  "  lint-flags      Print the @jpeakai/mermaidjs-lint canvas flags for the profile",
  "",
  "Options:",
  "  --design-profile NAME  Profile name; resolves ./.design-profiles, ~/.design-profiles, then skill tiers",
  "  --mode MODE            light or dark (default: the profile's default mode)",
  "  -h, --help             Show this help and exit",
].join("\n");

export const main = (argv: string[], roots: Roots = { project: process.cwd(), home: homedir() }): string => {
  const { values, positionals } = parseArgs({
    args: argv,
    options: {
      "design-profile": { type: "string" },
      mode: { type: "string" },
      help: { type: "boolean", short: "h", default: false },
    },
    allowPositionals: true,
    strict: true,
  });
  const command = positionals[0];
  if (values.help || command === undefined) return HELP;
  if (!["status", "mermaid-config", "lint-flags"].includes(command)) throw new Error(`unknown command '${command}'`);
  const path = resolveProfile(values["design-profile"] ?? null, SKILL, roots);
  if (command === "status") {
    return path === null ? "profile: none (this skill's own palettes apply)" : `profile: ${path}`;
  }
  if (path === null) {
    throw new Error("no design profile: pass --design-profile NAME, or set .design-profiles/.default-profile");
  }
  const doc = loadProfile(path);
  if (command === "lint-flags") return lintFlags(doc).join(" ");
  return JSON.stringify(mermaidConfig(doc, values.mode ?? defaultMode(doc)), null, 2);
};

if (import.meta.main) {
  try {
    console.log(main(Bun.argv.slice(2)));
  } catch (err: unknown) {
    console.error(`error: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }
}
