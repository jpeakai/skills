// Tests for assets/viewer-toc.js, the heading sidebar (ADR-021).
//
// Strategy:
//   - Load the REAL viewer.html body (placeholders stripped) into happy-dom, so
//     the ids the sidebar depends on are asserted against the shipped shell.
//   - Evaluate viewer-toc.js the way the page does: a classic script whose
//     function declarations are globals. It is placeholder-free (ADR-008), so it
//     runs unmodified.
//   - Layout is a function of one media query. happy-dom evaluates matchMedia
//     against its real viewport and fires `change` when setViewport crosses the
//     breakpoint, so the drawer is driven exactly as a browser drives it. No
//     stubs.
//   - What needs a layout engine (which heading has scrolled under the header)
//     is not asserted here: happy-dom has no layout, and a faked geometry would
//     only test the fake. That behaviour is checked in a real browser (ADR-021).

import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ASSETS = join(import.meta.dir, "..", "assets");
const TOC_SRC = readFileSync(join(ASSETS, "viewer-toc.js"), "utf-8");
const SHELL = readFileSync(join(ASSETS, "viewer.html"), "utf-8");

// Everything between <body> and the first injected script: header + layout.
const BODY = (SHELL.split("<body>")[1] ?? "").split("{{BOOTSTRAP}}")[0]?.replace(/\{\{\w+\}\}/g, "") ?? "";

type Controller = {
  entries: { level: number; id: string; text: string; el: HTMLElement }[];
  go: (id: string) => void;
  setOpen: (open: boolean, persist: boolean) => void;
  isNarrow: () => boolean;
  applyLayout: () => void;
  refreshActive: () => void;
};

type TocApi = {
  rdSlugify: (text: string) => string;
  rdInitToc: (article: Element) => Controller | null;
};

function loadToc(): TocApi {
  // new Function runs in global scope, exactly like the page's script element.
  return new Function(`${TOC_SRC}\nreturn { rdSlugify, rdInitToc };`)() as TocApi;
}

const WIDE = 1600;
const NARROW = 600;

// GlobalRegistrator exposes happy-dom's own controls on window; the DOM lib types
// do not know about them.
type HappyWindow = { happyDOM: { setViewport: (v: { width: number; height: number }) => void } };

const setWidth = (width: number): void => {
  (window as unknown as HappyWindow).happyDOM.setViewport({ width, height: 900 });
};

function render(markdownHtml: string): { api: TocApi; article: HTMLElement; ctl: Controller | null } {
  document.body.innerHTML = BODY;
  const article = document.getElementById("rd-article") as HTMLElement;
  article.innerHTML = markdownHtml;
  const api = loadToc();
  return { api, article, ctl: api.rdInitToc(article) };
}

const $ = (sel: string): HTMLElement => document.querySelector(sel) as HTMLElement;
const tocState = (): string | null => document.documentElement.getAttribute("data-toc");

const LONG_DOC = `
  <h1>Overview</h1><p>intro</p>
  <h2>Setup</h2>
  <h3>Install</h3>
  <h4>macOS</h4>
  <h3>Configure</h3>
  <h2>Usage</h2>
  <h2>Setup</h2>
  <h4>Deep skip</h4>
`;

beforeEach(() => {
  GlobalRegistrator.register({ url: "http://localhost:8642/doc.html", width: WIDE, height: 900 });
  localStorage.clear();
});

afterEach(async () => {
  await GlobalRegistrator.unregister();
});

describe("shell", () => {
  test("viewer.html carries the sidebar, the toggle and its ARIA wiring", () => {
    document.body.innerHTML = BODY;
    const toggle = $("#rd-toc-toggle");
    expect($("nav#rd-toc").getAttribute("aria-label")).toBe("Contents");
    expect(toggle.getAttribute("aria-controls")).toBe("rd-toc");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(toggle.hidden).toBe(true);
  });
});

describe("rdSlugify", () => {
  test("lower-cases, drops punctuation and hyphenates spaces", () => {
    const { rdSlugify } = loadToc();
    expect(rdSlugify("  Hello, World!  ")).toBe("hello-world");
    expect(rdSlugify("ADR-021: the `toc` (v2)")).toBe("adr-021-the-toc-v2");
    expect(rdSlugify("東京 の 地図")).toBe("東京-の-地図");
    expect(rdSlugify("?!")).toBe("section");
  });
});

describe("threshold", () => {
  test("fewer than three headings keeps the single-column layout", () => {
    const { ctl } = render("<h1>One</h1><h2>Two</h2><p>body</p>");
    expect(ctl).toBeNull();
    expect(document.documentElement.classList.contains("rd-has-toc")).toBe(false);
    expect($("#rd-toc-toggle").hidden).toBe(true);
    expect($("#rd-toc").children.length).toBe(0);
    expect($("#rd-article h1").id).toBe("");
  });

  test("three headings switch the sidebar on", () => {
    const { ctl } = render("<h1>A</h1><h2>B</h2><h3>C</h3>");
    expect(ctl).not.toBeNull();
    expect(document.documentElement.classList.contains("rd-has-toc")).toBe(true);
    expect($("#rd-toc-toggle").hidden).toBe(false);
  });
});

describe("hierarchy", () => {
  test("nests h1 to h4 by level, climbing back out after a deep run", () => {
    render(LONG_DOC);
    const root = $("#rd-toc > ol");
    const top = root.querySelectorAll(":scope > li");
    expect(top.length).toBe(1); // Overview
    const underOverview = root.querySelectorAll(":scope > li > ol > li");
    expect([...underOverview].map((li) => li.querySelector("a")?.textContent)).toEqual(["Setup", "Usage", "Setup"]);
    const underSetup = underOverview[0]?.querySelectorAll(":scope > ol > li > a");
    expect([...(underSetup ?? [])].map((a) => a.textContent)).toEqual(["Install", "Configure"]);
    expect(root.querySelector('a[data-rd-toc-id="macos"]')?.closest("ol")?.closest("li")?.querySelector("a")?.textContent).toBe(
      "Install",
    );
  });

  test("a skipped level nests one step, not two", () => {
    render(LONG_DOC);
    const deep = $('#rd-toc a[data-rd-toc-id="deep-skip"]');
    // h4 straight under the second "Setup" h2
    expect(deep.closest("ol")?.closest("li")?.querySelector("a")?.getAttribute("data-rd-toc-id")).toBe("setup-1");
  });

  test("a document opening deeper than h1 still roots at its first level", () => {
    render("<h2>A</h2><h3>B</h3><h2>C</h2><h1>D</h1>");
    const top = [...document.querySelectorAll("#rd-toc > ol > li > a")].map((a) => a.textContent);
    expect(top).toEqual(["A", "C", "D"]);
  });

  test("headings deeper than h4 are not indexed", () => {
    const { ctl } = render("<h1>A</h1><h2>B</h2><h5>Fine print</h5><h3>C</h3>");
    expect(ctl?.entries.map((e) => e.text)).toEqual(["A", "B", "C"]);
  });
});

describe("heading ids", () => {
  test("duplicates get unique, stable anchors in document order", () => {
    const first = render(LONG_DOC).ctl?.entries.map((e) => e.id);
    expect(first).toEqual(["overview", "setup", "install", "macos", "configure", "usage", "setup-1", "deep-skip"]);
    const again = render(LONG_DOC).ctl?.entries.map((e) => e.id);
    expect(again).toEqual(first);
  });

  test("an authored id is kept and ids already on the page are never reused", () => {
    const { ctl } = render('<h1 id="custom">Intro</h1><h2>rd title</h2><h2>rd-article</h2>');
    expect(ctl?.entries.map((e) => e.id)).toEqual(["custom", "rd-title-1", "rd-article-1"]);
    expect(document.querySelectorAll("#rd-title").length).toBe(1);
  });

  test("links carry the encoded fragment", () => {
    render("<h1>東京</h1><h2>B</h2><h3>C</h3>");
    expect($('#rd-toc a[data-rd-toc-id="東京"]').getAttribute("href")).toBe(`#${encodeURIComponent("東京")}`);
  });
});

describe("click navigation", () => {
  test("selecting an entry updates the fragment, marks it current and focuses the heading", () => {
    render(LONG_DOC);
    const link = $('#rd-toc a[data-rd-toc-id="configure"]');
    const evt = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    link.dispatchEvent(evt);

    expect(evt.defaultPrevented).toBe(true);
    expect(location.hash).toBe("#configure");
    expect(link.getAttribute("aria-current")).toBe("location");
    expect(document.querySelectorAll("#rd-toc [aria-current]").length).toBe(1);
    expect(document.activeElement?.id).toBe("configure");
    expect($("#configure").getAttribute("tabindex")).toBe("-1");
  });

  test("a click on the list outside any entry does nothing", () => {
    render(LONG_DOC);
    const evt = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    $("#rd-toc > ol").dispatchEvent(evt);
    expect(evt.defaultPrevented).toBe(false);
    expect(location.hash).toBe("");
  });

  test("a fragment present at load is honoured once the article renders", () => {
    history.replaceState(null, "", "#usage");
    const { ctl } = render(LONG_DOC);
    expect(ctl).not.toBeNull();
    expect($('#rd-toc a[data-rd-toc-id="usage"]').getAttribute("aria-current")).toBe("location");
  });

  test("back and forward move to the fragment's heading", () => {
    render(LONG_DOC);
    history.replaceState(null, "", "#install");
    window.dispatchEvent(new window.PopStateEvent("popstate"));
    expect($('#rd-toc a[data-rd-toc-id="install"]').getAttribute("aria-current")).toBe("location");
  });

});

describe("collapse and persistence", () => {
  test("wide layout opens by default and the toggle collapses and reopens it", () => {
    render(LONG_DOC);
    const toggle = $("#rd-toc-toggle");
    expect(tocState()).toBe("open");
    expect(toggle.getAttribute("aria-expanded")).toBe("true");

    toggle.click();
    expect(tocState()).toBe("closed");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(localStorage.getItem("richdocs-toc")).toBe("closed");

    toggle.click();
    expect(tocState()).toBe("open");
    expect(localStorage.getItem("richdocs-toc")).toBe("open");
  });

  test("a remembered collapse survives a reload", () => {
    localStorage.setItem("richdocs-toc", "closed");
    render(LONG_DOC);
    expect(tocState()).toBe("closed");
    expect($("#rd-toc-toggle").getAttribute("aria-expanded")).toBe("false");
  });
});

describe("responsive drawer", () => {
  test("narrow viewports start closed even when the wide state is open", () => {
    localStorage.setItem("richdocs-toc", "open");
    setWidth(NARROW);
    render(LONG_DOC);
    expect(tocState()).toBe("closed");
  });

  test("crossing the breakpoint collapses to a drawer and restores the wide state", () => {
    render(LONG_DOC);
    expect(tocState()).toBe("open");
    setWidth(NARROW);
    expect(tocState()).toBe("closed");
    setWidth(WIDE);
    expect(tocState()).toBe("open");
  });

  test("the drawer never writes the remembered wide state", () => {
    localStorage.setItem("richdocs-toc", "closed");
    setWidth(NARROW);
    render(LONG_DOC);
    $("#rd-toc-toggle").click();
    expect(tocState()).toBe("open");
    expect(localStorage.getItem("richdocs-toc")).toBe("closed");
  });

  test("choosing an entry in the drawer closes it", () => {
    setWidth(NARROW);
    const { ctl } = render(LONG_DOC);
    $("#rd-toc-toggle").click();
    ctl?.go("usage");
    expect(tocState()).toBe("closed");
  });

  test("opening the drawer moves focus to the current entry", () => {
    setWidth(NARROW);
    render(LONG_DOC);
    $("#rd-toc-toggle").click();
    expect(document.activeElement).toBe($("#rd-toc [aria-current]"));
  });

  test("opening the wide sidebar leaves focus where it was", () => {
    localStorage.setItem("richdocs-toc", "closed");
    render(LONG_DOC);
    const toggle = $("#rd-toc-toggle");
    toggle.focus();
    toggle.click();
    expect(document.activeElement).toBe(toggle);
  });

  test("Escape closes the drawer and returns focus to the toggle", () => {
    setWidth(NARROW);
    render(LONG_DOC);
    const toggle = $("#rd-toc-toggle");
    toggle.click();
    expect(document.activeElement?.closest("#rd-toc")).not.toBeNull();
    document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
    expect(tocState()).toBe("closed");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(toggle);
  });

  test("a tap outside the open drawer dismisses it; a tap inside does not", () => {
    setWidth(NARROW);
    render(LONG_DOC);
    $("#rd-toc-toggle").click();
    $("#rd-toc").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    expect(tocState()).toBe("open");
    $("#rd-article").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    expect(tocState()).toBe("closed");
  });

  test("Escape on the wide layout leaves the sidebar alone", () => {
    render(LONG_DOC);
    document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
    expect(tocState()).toBe("open");
  });
});
