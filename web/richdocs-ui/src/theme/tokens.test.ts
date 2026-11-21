import { describe, expect, test } from "bun:test";

import { type Brandpack, modeVariables, tokenCss } from "./tokens";

const PACK: Brandpack = {
  fonts: { sans: "Inter", mono: "JetBrains Mono" },
  themes: {
    light: {
      background: "#fff", foreground: "#111", card: "#f7f7f7", mutedForeground: "#555",
      primary: "#facc15", primaryForeground: "#111", link: "#854d0e", border: "#ddd",
    },
    dark: {
      background: "#000", foreground: "#eee", card: "#111", mutedForeground: "#aaa",
      primary: "#facc15", border: "#333", radius: "4px",
    },
  },
};

describe("tokenCss", () => {
  test("writes one rule per mode under data-theme", () => {
    const css = tokenCss(PACK);
    expect(css).toStartWith(":root[data-theme=light]{");
    expect(css).toContain(":root[data-theme=dark]{");
  });

  test("keeps the fill and the text-safe link apart", () => {
    const light = Object.fromEntries(modeVariables(PACK, "light"));
    expect(light["--primary"]).toBe("#facc15");
    expect(light["--link"]).toBe("#854d0e");
  });

  test("falls back like the original viewer when roles are missing", () => {
    const dark = Object.fromEntries(modeVariables(PACK, "dark"));
    expect(dark["--primary-foreground"]).toBe("#000");
    expect(dark["--link"]).toBe("#facc15");
    expect(dark["--muted"]).toBe("#111");
    expect(dark["--radius"]).toBe("4px");
    expect(dark["--font-heading"]).toBe("Inter");
  });

  test("scopes to a showcase brand", () => {
    expect(tokenCss(PACK, ':root[data-brand="x"]')).toContain(':root[data-brand="x"][data-theme=light]{');
  });
});
