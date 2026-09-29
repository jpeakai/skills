// Tests for the categorical palette helpers in assets/viewer-cytoscape.js (ADR-023).
//
// A brand has ONE categorical palette, `canvas.plotly.<mode>.series`. Diagram
// categories take its slots in a fixed order and never cycle. These are pure
// functions, so they run without a DOM.

import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SRC = readFileSync(join(import.meta.dir, "..", "assets", "viewer-cytoscape.js"), "utf-8");

type Tokens = { canvas: { plotly: Record<string, { series: string[] }> } };
type Api = {
  rdCategorical: (t: Tokens, theme: string) => string[];
  rdCategorySlots: (names: string[]) => Record<string, number>;
  rdCategoryColour: (t: Tokens, theme: string, slots: Record<string, number>, name: string) => string | null;
  rdCyCategories: (payload: object) => string[];
};

const api = new Function(
  `${SRC}\nreturn { rdCategorical, rdCategorySlots, rdCategoryColour, rdCyCategories };`,
)() as Api;

const TOKENS: Tokens = {
  canvas: { plotly: { light: { series: ["#111111", "#222222"] }, dark: { series: ["#aaaaaa", "#bbbbbb"] } } },
};

describe("categorical palette", () => {
  test("is the plotly series of the active mode", () => {
    expect(api.rdCategorical(TOKENS, "dark")).toEqual(["#aaaaaa", "#bbbbbb"]);
  });

  test("slots follow the declared order, ignoring repeats", () => {
    expect(api.rdCategorySlots(["Compute", "Storage", "Compute", "AI"])).toEqual({ Compute: 0, Storage: 1, AI: 2 });
  });

  test("a category wears its slot in the active mode", () => {
    const slots = api.rdCategorySlots(["Compute", "Storage"]);
    expect(api.rdCategoryColour(TOKENS, "light", slots, "Storage")).toBe("#222222");
    expect(api.rdCategoryColour(TOKENS, "dark", slots, "Storage")).toBe("#bbbbbb");
  });

  test("past the last slot, or unknown, a category gets no colour: never cycled", () => {
    const slots = api.rdCategorySlots(["A", "B", "C"]);
    expect(api.rdCategoryColour(TOKENS, "light", slots, "C")).toBeNull();
    expect(api.rdCategoryColour(TOKENS, "light", slots, "Z")).toBeNull();
  });

  test("a graph without declared categories takes them in element order", () => {
    const payload = {
      elements: [{ data: { id: "a", category: "Security" } }, { data: { id: "b" } }, { data: { id: "c", category: "Compute" } }],
    };
    expect(api.rdCyCategories(payload)).toEqual(["Security", "Compute"]);
    expect(api.rdCyCategories({ ...payload, categories: ["Compute", "Security"] })).toEqual(["Compute", "Security"]);
    expect(api.rdCyCategories({ elements: { nodes: [{ data: { category: "AI" } }], edges: [] } })).toEqual(["AI"]);
  });
});
