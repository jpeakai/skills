// The theme injection contract: a richdocs brandpack (design-tokens.json, keys
// per richdocs ADR-033) becomes shadcn CSS variables, one rule per mode.
//
// Port of applyTokenCss() from skills/richdocs/assets/viewer.js. The --rd-*
// names it used to write are now aliases declared in styles.css.

export type Mode = "light" | "dark";

export interface ModeTokens {
  background: string;
  foreground: string;
  card: string;
  mutedForeground: string;
  primary: string;
  primaryForeground?: string;
  link?: string;
  border: string;
  radius?: string;
  muted?: string;
}

export interface Brandpack {
  fonts: { sans: string; mono: string; heading?: string };
  themes: Record<Mode, ModeTokens>;
}

const MODES: Mode[] = ["light", "dark"];

/** The shadcn variables one mode sets, in a stable order. */
export function modeVariables(tokens: Brandpack, mode: Mode): [string, string][] {
  const t = tokens.themes[mode];
  return [
    ["--background", t.background],
    ["--foreground", t.foreground],
    ["--card", t.card],
    // A brandpack has no muted surface; the card is the nearest role.
    ["--muted", t.muted ?? t.card],
    ["--muted-foreground", t.mutedForeground],
    ["--primary", t.primary],
    // Text ON the fill, then a text-safe accent for links (richdocs ADR-012).
    ["--primary-foreground", t.primaryForeground ?? t.background],
    ["--link", t.link ?? t.primary],
    ["--border", t.border],
    ["--radius", t.radius ?? "8px"],
    ["--font-sans", tokens.fonts.sans],
    ["--font-mono", tokens.fonts.mono],
    ["--font-heading", tokens.fonts.heading ?? tokens.fonts.sans],
  ];
}

/** The stylesheet text for both modes. Pure, so it is testable without a DOM. */
export function tokenCss(tokens: Brandpack, scope = ":root"): string {
  return MODES.map((mode) => {
    const body = modeVariables(tokens, mode)
      .map(([name, value]) => `${name}:${value};`)
      .join("");
    return `${scope}[data-theme=${mode}]{${body}}`;
  }).join("");
}

/** Write (or replace) the page's token stylesheet. */
export function applyTokenCss(tokens: Brandpack, doc: Document = document): void {
  let style = doc.getElementById("rd-token-css");
  if (!style) {
    style = doc.createElement("style");
    style.id = "rd-token-css";
    doc.head.appendChild(style);
  }
  style.textContent = tokenCss(tokens);
}
