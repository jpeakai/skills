// Runtime renderer for the paired-markdown viewer, ported from the hand-written
// assets/viewer.js it replaces.
//
// Boot order: tokens -> CSS vars -> markdown -> marked.parse -> fenced-block
// upgrades. Tokens land first so nothing paints in fallback colours.
//
// Everything md2html.py injects arrives through the #rd-config JSON block, so
// this source carries no template placeholders (richdocs ADR-008). The shared
// helpers rdInitToc, rdInitZoom, rdRenderCytoscape and rdRenderDeckGL are still
// classic scripts that the page inlines before this bundle, because the
// showcase inlines them too. They move into the registry in M2.

import { applyTokenCss, type Brandpack, type Mode } from "@/theme/tokens";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Canvas = {
  plotly: Record<Mode, { paper: string; plot: string; font: string; grid: string; series: string[] }>;
  mermaid?: Record<Mode, Record<string, string>>;
  [other: string]: unknown;
};

export type Tokens = Brandpack & { canvas: Canvas; defaultTheme?: Mode };

export interface ViewerConfig {
  buildId: string;
  source: string;
  title?: string;
  tokensSource?: string;
  cdn: Record<string, string>;
  fallbackTokens: Tokens;
}

type Block = { el: HTMLElement; payload: any; cy?: unknown; deck?: unknown };

declare global {
  interface Window {
    __DOC_MD__?: string;
    __DOC_TOKENS__?: Tokens;
    marked: { parse(md: string): string };
    mermaid: any;
    cytoscape: any;
    cytoscapeDagre: any;
    Plotly: any;
    hljs: any;
  }
  function rdInitToc(article: HTMLElement): unknown;
  function rdInitZoom(options: { pictures: string; exclude: string }): unknown;
  function rdRenderCytoscape(block: Block, tokens: Tokens, theme: Mode): void;
  function rdRenderDeckGL(block: Block, tokens: Tokens, theme: Mode): void;
}

const RICH = ["mermaid", "cytoscape", "plotly", "deckgl"];

export function readConfig(doc: Document = document): ViewerConfig {
  const el = doc.getElementById("rd-config");
  if (!el?.textContent) throw new Error("richdocs: the page has no #rd-config block");
  return JSON.parse(el.textContent) as ViewerConfig;
}

export function currentTheme(doc: Document = document): Mode {
  return doc.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function fenceLang(code: Element): string | undefined {
  return (code.className.match(/language-([\w-]+)/) ?? [])[1];
}

export function showError(el: HTMLElement, err: unknown): void {
  const div = document.createElement("div");
  div.className = "rd-error";
  div.textContent = String(err instanceof Error ? err.message : err);
  el.replaceChildren(div);
  console.error(err);
}

export class Viewer {
  readonly cfg: ViewerConfig;
  tokens: Tokens;
  private cyBlocks: Block[] = [];
  private plotlyBlocks: Block[] = [];
  private deckBlocks: Block[] = []; // holds a WebGL context; finalized on re-theme
  private mermaidSources: { el: HTMLElement; src: string }[] = [];
  private lazyLoaded: Record<string, Promise<unknown>> = {};

  constructor(cfg: ViewerConfig) {
    this.cfg = cfg;
    this.tokens = cfg.fallbackTokens;
  }

  private loadScript(name: string, url: string): Promise<unknown> {
    const cached = this.lazyLoaded[name];
    if (cached) return cached;
    const loading = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = url;
      s.onload = resolve;
      s.onerror = () => reject(new Error(`failed to load ${url}`));
      document.head.appendChild(s);
    });
    this.lazyLoaded[name] = loading;
    return loading;
  }

  // ?v=BUILD_ID + no-store: a browser refresh in the live-authoring loop must
  // show the edited markdown, never a cached copy.
  private async fetchNoStore(url: string): Promise<Response> {
    const r = await fetch(`${url}?v=${this.cfg.buildId}`, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status} fetching ${url}`);
    return r;
  }

  // ── Mermaid ──────────────────────────────────────────────────────────────
  // Rendered mermaid SVG is not re-themable in place: it is re-rendered from
  // source on every theme flip. fontFamily makes mermaid measure the face the
  // page paints; fonts.ready stops it measuring a swap fallback.
  private async renderAllMermaid(): Promise<void> {
    if (this.mermaidSources.length === 0) return;
    const theme = currentTheme();
    const fonts = this.tokens.fonts.sans;
    const profile = this.tokens.canvas.mermaid?.[theme];
    window.mermaid.initialize({
      startOnLoad: false,
      theme: profile ? "base" : theme === "dark" ? "dark" : "default",
      themeVariables: profile
        ? { ...profile, darkMode: theme === "dark", fontFamily: fonts }
        : {},
      fontFamily: fonts,
      securityLevel: "loose",
    });
    if (document.fonts?.ready) await document.fonts.ready;
    for (const [i, m] of this.mermaidSources.entries()) {
      try {
        const out = await window.mermaid.render(`rd-mmd-${this.cfg.buildId}-${i}-${theme}`, m.src);
        m.el.innerHTML = out.svg;
      } catch (err) {
        showError(m.el, err);
      }
    }
  }

  private async loadCytoscapeLibs(): Promise<void> {
    const cdn = this.cfg.cdn;
    await this.loadScript("cytoscape", cdn.cytoscape!);
    await this.loadScript("dagre", cdn.dagre!);
    await this.loadScript("cytoscapeDagre", cdn.cytoscapeDagre!);
    window.cytoscape.use(window.cytoscapeDagre);
  }

  // ── Plotly ───────────────────────────────────────────────────────────────
  // A fresh layout per chart: Plotly mutates the layout it is handed.
  private plotlyLayout(payload: any): any {
    const p = this.tokens.canvas.plotly[currentTheme()];
    const layout = { ...(payload.layout ?? {}) };
    layout.paper_bgcolor = p.paper;
    layout.plot_bgcolor = p.plot;
    layout.font = { ...(layout.font ?? {}), color: p.font, family: this.tokens.fonts.sans };
    layout.colorway = p.series;
    layout.xaxis = { ...(layout.xaxis ?? {}), gridcolor: p.grid };
    layout.yaxis = { ...(layout.yaxis ?? {}), gridcolor: p.grid };
    return layout;
  }

  // `responsive: true` sizes Plotly to its parent, and .rd-canvas has no height
  // of its own, so every renderer owes its container an explicit height.
  private renderPlotly(block: Block): Promise<unknown> {
    block.el.style.height = `${block.payload.height ?? 420}px`;
    return window.Plotly.react(block.el, block.payload.data, this.plotlyLayout(block.payload), {
      responsive: true,
    });
  }

  private renderCanvases(): void {
    const theme = currentTheme();
    for (const b of this.cyBlocks) {
      try {
        rdRenderCytoscape(b, this.tokens, theme);
      } catch (e) {
        showError(b.el, e);
      }
    }
    for (const b of this.plotlyBlocks) this.renderPlotly(b).catch((e) => showError(b.el, e));
    for (const b of this.deckBlocks) {
      try {
        rdRenderDeckGL(b, this.tokens, theme);
      } catch (e) {
        showError(b.el, e);
      }
    }
  }

  // A block's `data` may be a URL string instead of inline data: fetch and merge.
  private async resolvePayload(raw: string): Promise<any> {
    let payload = JSON.parse(raw);
    if (typeof payload.data !== "string") return payload;
    const remote = await (await this.fetchNoStore(payload.data)).json();
    if (Array.isArray(remote)) {
      payload.data = remote;
    } else {
      delete payload.data;
      payload = { ...remote, ...payload };
    }
    return payload;
  }

  // Libraries are injected only when a doc uses them, so a prose doc pays for none.
  private async upgradeFences(article: HTMLElement): Promise<void> {
    const jobs: Promise<void>[] = [];
    for (const code of article.querySelectorAll("pre > code")) {
      const lang = fenceLang(code);
      if (!lang || !RICH.includes(lang)) continue;
      const div = document.createElement("div");
      div.className = `rd-canvas rd-${lang}`;
      code.parentElement!.replaceWith(div);
      const raw = code.textContent ?? "";
      if (lang === "mermaid") {
        this.mermaidSources.push({ el: div, src: raw });
        continue;
      }
      jobs.push(
        this.resolvePayload(raw)
          .then((payload) => {
            const block = { el: div, payload };
            if (lang === "cytoscape") this.cyBlocks.push(block);
            else if (lang === "deckgl") this.deckBlocks.push(block);
            else this.plotlyBlocks.push(block);
          })
          .catch((err) => showError(div, err)),
      );
    }
    await Promise.all(jobs);
    const cdn = this.cfg.cdn;
    const loads: Promise<unknown>[] = [];
    if (this.cyBlocks.length) loads.push(this.loadCytoscapeLibs());
    if (this.plotlyBlocks.length) loads.push(this.loadScript("plotly", cdn.plotly!));
    if (this.deckBlocks.length) loads.push(this.loadScript("deckgl", cdn.deckgl!));
    await Promise.all(loads);
    this.renderCanvases();
    await this.renderAllMermaid();
  }

  // Ordinary language-tagged snippets only; unknown languages stay readable.
  private async highlightCode(article: HTMLElement): Promise<void> {
    const blocks = [...article.querySelectorAll<HTMLElement>("pre > code")].filter((code) => {
      const lang = fenceLang(code);
      return lang && !RICH.includes(lang);
    });
    if (!blocks.length) return;
    try {
      await this.loadScript("highlight", this.cfg.cdn.highlight!);
    } catch (err) {
      // A CDN failure must not hide the source or stop diagram upgrades.
      console.warn("Syntax highlighting unavailable", err);
      return;
    }
    for (const code of blocks) {
      if (window.hljs.getLanguage(fenceLang(code))) window.hljs.highlightElement(code);
    }
  }

  // CSS variables flip themselves; the canvas renderers must be re-fed by hand.
  retheme(): void {
    this.renderCanvases();
    void this.renderAllMermaid();
  }

  // --inline mode pre-seeds window.__DOC_*__; multi-file mode fetches.
  private async loadTokens(): Promise<Tokens> {
    if (window.__DOC_TOKENS__ !== undefined) return window.__DOC_TOKENS__;
    const source = this.cfg.tokensSource ?? "design-tokens.json";
    try {
      return (await (await this.fetchNoStore(source)).json()) as Tokens;
    } catch (err) {
      console.error(`${source} fetch failed; using baked fallback tokens`, err);
      return this.cfg.fallbackTokens;
    }
  }

  private async loadDoc(): Promise<string> {
    if (window.__DOC_MD__ !== undefined) return window.__DOC_MD__;
    return (await this.fetchNoStore(this.cfg.source)).text();
  }

  async boot(article: HTMLElement): Promise<void> {
    try {
      this.tokens = await this.loadTokens();
      applyTokenCss(this.tokens);
      article.innerHTML = window.marked.parse(await this.loadDoc());
      for (const table of article.querySelectorAll("table")) {
        const wrap = document.createElement("div");
        wrap.className = "rd-table-wrap";
        table.replaceWith(wrap);
        wrap.appendChild(table);
      }
      // Before the fence upgrades, so only authored headings are indexed (ADR-021).
      rdInitToc(article);
      await Promise.all([this.upgradeFences(article), this.highlightCode(article)]);
    } catch (err) {
      showError(article, err);
    }
  }
}
