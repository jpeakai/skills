// Tests for assets/viewer-toc.js, the heading sidebar and section folds
// (ADR-021, ADR-022).
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

type Fold = { button: HTMLButtonElement; body: HTMLElement };

type Controller = {
  entries: { level: number; id: string; text: string; el: HTMLElement }[];
  folds: Record<string, Fold>;
  go: (id: string) => void;
  setOpen: (open: boolean, persist: boolean) => void;
  isNarrow: () => boolean;
  applyLayout: () => void;
  refreshActive: () => void;
};

type TocApi = {
  rdSlugify: (text: string) => string;
  rdInitToc: (article: Element, opts?: { header?: Element; selector?: string; folds?: boolean }) => Controller | null;
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
    const underSetup = underOverview[0]?.querySelectorAll(":scope > ol > li > .rd-toc-row > a");
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
    const top = [...document.querySelectorAll("#rd-toc > ol > li > .rd-toc-row > a")].map((a) => a.textContent);
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

const click = (el: Element): void => {
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
};

describe("sidebar rail", () => {
  test("the sidebar carries its own collapse control, wired to the list", () => {
    render(LONG_DOC);
    const collapse = $("#rd-toc-collapse");
    expect(collapse.closest("#rd-toc")).not.toBeNull();
    expect(collapse.getAttribute("aria-controls")).toBe("rd-toc-list");
    expect($("#rd-toc-list").tagName).toBe("OL");
    expect(collapse.getAttribute("aria-expanded")).toBe("true");
    expect(collapse.getAttribute("aria-label")).toBe("Collapse contents");
  });

  test("on the wide layout it folds to the rail and back, remembered like the header toggle", () => {
    render(LONG_DOC);
    const collapse = $("#rd-toc-collapse");
    click(collapse);
    expect(tocState()).toBe("closed");
    expect(collapse.getAttribute("aria-label")).toBe("Expand contents");
    expect($("#rd-toc-toggle").getAttribute("aria-expanded")).toBe("false");
    expect(localStorage.getItem("richdocs-toc")).toBe("closed");
    click(collapse);
    expect(tocState()).toBe("open");
    expect(localStorage.getItem("richdocs-toc")).toBe("open");
  });

  test("in the drawer it is the close button, and hands focus back to the header toggle", () => {
    setWidth(NARROW);
    render(LONG_DOC);
    $("#rd-toc-toggle").click();
    click($("#rd-toc-collapse"));
    expect(tocState()).toBe("closed");
    expect(document.activeElement).toBe($("#rd-toc-toggle"));
  });
});

describe("contents branches", () => {
  test("only an entry with children gets a branch toggle, at every level", () => {
    render(LONG_DOC);
    const branchIds = [...document.querySelectorAll("#rd-toc .rd-toc-branch")].map(
      (b) => b.closest("li")?.querySelector("a")?.getAttribute("data-rd-toc-id"),
    );
    expect(branchIds).toEqual(["overview", "setup", "install", "setup-1"]);
    expect(document.querySelectorAll("#rd-toc .rd-toc-spacer").length).toBe(4);
  });

  test("a branch toggle folds and unfolds just its own subtree", () => {
    render(LONG_DOC);
    const btn = $('#rd-toc-sub-setup').closest("li")?.querySelector(".rd-toc-branch") as HTMLElement;
    expect(btn.getAttribute("aria-controls")).toBe("rd-toc-sub-setup");
    click(btn);
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    expect($("#rd-toc-sub-setup").hidden).toBe(true);
    expect($("#rd-toc-sub-overview").hidden).toBe(false);
    expect(location.hash).toBe("");
    click(btn);
    expect($("#rd-toc-sub-setup").hidden).toBe(false);
  });

  test("a folded branch marks its visible parent when the current entry is inside", () => {
    const { ctl } = render(LONG_DOC);
    ctl?.go("macos");
    const trail = [...document.querySelectorAll("#rd-toc .rd-toc-trail")].map((a) => a.getAttribute("data-rd-toc-id"));
    expect(trail).toEqual(["overview", "setup", "install"]);
    ctl?.go("usage");
    expect([...document.querySelectorAll("#rd-toc .rd-toc-trail")].map((a) => a.getAttribute("data-rd-toc-id"))).toEqual([
      "overview",
    ]);
  });
});

const FOLD_DOC = `
  <h1>Title</h1><p>lede</p>
  <h2>Alpha</h2><p>a1</p>
  <h3>Alpha one</h3><p>a1.1</p>
  <h2>Empty</h2>
  <h2>Beta</h2><p>b1</p><h5>fine print</h5><p>b2</p>
`;

describe("section folds", () => {
  test("every section with content folds, except the lone top heading", () => {
    const { ctl } = render(FOLD_DOC);
    expect(Object.keys(ctl?.folds ?? {}).sort()).toEqual(["alpha", "alpha-one", "beta"]);
    expect($("#title").parentElement?.id).toBe("rd-article");
  });

  test("a section runs to the next heading at its level or shallower, nesting deeper ones", () => {
    const { ctl } = render(FOLD_DOC);
    const alpha = ctl?.folds.alpha?.body as HTMLElement;
    expect(alpha.contains($("#alpha-one"))).toBe(true);
    expect(alpha.contains($("#empty"))).toBe(false);
    // An unindexed h5 is content, not a boundary.
    expect(ctl?.folds.beta?.body.querySelector("h5")?.textContent).toBe("fine print");
  });

  test("the button sits beside the heading, so its text, id and entry are untouched", () => {
    const { ctl } = render(FOLD_DOC);
    const head = $("#alpha").parentElement as HTMLElement;
    expect(head.className).toContain("rd-fold-head");
    expect(head.firstElementChild).toBe(ctl?.folds.alpha?.button as HTMLElement);
    expect($("#alpha").textContent).toBe("Alpha");
    const btn = ctl?.folds.alpha?.button as HTMLElement;
    expect(btn.getAttribute("aria-controls")).toBe(ctl?.folds.alpha?.body.id as string);
    expect(btn.getAttribute("aria-label")).toBe("Section Alpha");
  });

  test("the button folds and unfolds the body", () => {
    const { ctl } = render(FOLD_DOC);
    const fold = ctl?.folds.alpha as Fold;
    click(fold.button);
    expect(fold.button.getAttribute("aria-expanded")).toBe("false");
    expect(fold.body.hidden).toBe(true);
    click(fold.button);
    expect(fold.body.hidden).toBe(false);
  });

  test("navigating to a heading unfolds it and every section around it", () => {
    const { ctl } = render(FOLD_DOC);
    const outer = ctl?.folds.alpha as Fold;
    const inner = ctl?.folds["alpha-one"] as Fold;
    click(inner.button);
    click(outer.button);
    click($('#rd-toc a[data-rd-toc-id="alpha-one"]'));
    expect(outer.body.hidden).toBe(false);
    expect(outer.button.getAttribute("aria-expanded")).toBe("true");
    expect(inner.body.hidden).toBe(false);
  });

  test("a fragment into a folded section unfolds it on back and forward", () => {
    const { ctl } = render(FOLD_DOC);
    click((ctl?.folds.alpha as Fold).button);
    history.replaceState(null, "", "#alpha-one");
    window.dispatchEvent(new window.PopStateEvent("popstate"));
    expect(ctl?.folds.alpha?.body.hidden).toBe(false);
  });

  test("folds: false leaves the headings where they were", () => {
    document.body.innerHTML = BODY;
    const article = $("#rd-article");
    article.innerHTML = FOLD_DOC;
    const ctl = loadToc().rdInitToc(article, { folds: false });
    expect(Object.keys(ctl?.folds ?? {})).toEqual([]);
    expect(document.querySelectorAll(".rd-fold-head").length).toBe(0);
  });
});

describe("options", () => {
  test("a selector and a label override index a page that is not a rendered doc", () => {
    document.body.innerHTML = BODY;
    const article = $("#rd-article");
    article.innerHTML = `
      <section><h2 data-rd-toc-label="Overview">brand name</h2><p>x</p></section>
      <section><h2>Colour</h2><h3>Ramp</h3><p>y</p><div class="card"><h3>Card</h3></div></section>`;
    const ctl = loadToc().rdInitToc(article, { selector: "section > h2, section > h3" });
    expect(ctl?.entries.map((e) => e.text)).toEqual(["Overview", "Colour", "Ramp"]);
    expect(ctl?.entries[0]?.id).toBe("overview");
  });
});
