// Tests for assets/viewer-zoom.js, full-screen diagrams with deep zoom (ADR-024).
//
// The zoom maths is pure and tested exactly. The modal is driven through the real
// viewer.html shell in happy-dom. happy-dom has no layout, so the controller takes
// its no-layout path (zoom about the centre); that a zoom tracks the cursor, and
// that a Cytoscape.js copy opens and zooms, are checked in a real browser instead.

import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ASSETS = join(import.meta.dir, "..", "assets");
const ZOOM_SRC = readFileSync(join(ASSETS, "viewer-zoom.js"), "utf-8");
const SHELL = readFileSync(join(ASSETS, "viewer.html"), "utf-8");
const BODY = (SHELL.split("<body>")[1] ?? "").split("{{BOOTSTRAP}}")[0]?.replace(/\{\{\w+\}\}/g, "") ?? "";

type Box = { x: number; y: number; w: number; h: number };
type Api = {
  rdZoomViewBox: (vb: Box, px: number, py: number, f: number, base: Box, widest?: number) => Box;
  rdViewBoxOf: (svg: Element) => Box;
  rdInitZoom: (opts: { pictures: string; exclude?: string }) => void;
  rdCloseZoom: () => void;
};

const load = (): Api =>
  new Function(`${ZOOM_SRC}\nreturn { rdZoomViewBox, rdViewBoxOf, rdInitZoom, rdCloseZoom };`)() as Api;

const BASE: Box = { x: 0, y: 0, w: 100, h: 50 };

describe("zoom maths", () => {
  const api = load();

  test("zooming in about a point keeps that point fixed", () => {
    const vb = api.rdZoomViewBox(BASE, 25, 10, 2, BASE);
    expect(vb).toEqual({ x: 12.5, y: 5, w: 50, h: 25 });
    // The point's fraction across the view is unchanged: 25/100 == (25-12.5)/50.
    expect((25 - vb.x) / vb.w).toBe(25 / BASE.w);
  });

  test("depth is clamped at 40x the fitted view", () => {
    const vb = api.rdZoomViewBox(BASE, 50, 25, 1000, BASE);
    expect(vb.w).toBeCloseTo(100 / 40);
    expect(vb.h).toBeCloseTo(50 / 40);
  });

  test("zooming out stops at the widest allowed view", () => {
    expect(api.rdZoomViewBox(BASE, 50, 25, 0.01, BASE).w).toBeCloseTo(200); // modal: half of fit
    expect(api.rdZoomViewBox(BASE, 50, 25, 0.01, BASE, 1).w).toBeCloseTo(100); // in page: fit
  });
});

const click = (el: Element): void => {
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
};
const wheel = (el: Element, init: { deltaY: number; ctrlKey?: boolean }): WheelEvent => {
  const e = new window.WheelEvent("wheel", { bubbles: true, cancelable: true, ...init });
  // happy-dom's WheelEvent drops modifier keys from its init (its MouseEvent keeps
  // them). Browsers set ctrlKey on a wheel, and a trackpad pinch relies on it.
  Object.defineProperty(e, "ctrlKey", { value: !!init.ctrlKey });
  el.dispatchEvent(e);
  return e as unknown as WheelEvent;
};
const $ = (sel: string): HTMLElement => document.querySelector(sel) as HTMLElement;

const ARTICLE = `
  <div class="rd-canvas rd-mermaid"><svg id="m" width="400" viewBox="0 0 400 200" style="max-width: 400px"><g><rect width="10" height="10"/></g></svg></div>
  <div class="rd-canvas rd-plotly"><svg id="chart" viewBox="0 0 10 10"></svg></div>
  <p><img id="pic" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" width="20" height="10" alt="x"></p>
`;

describe("modal", () => {
  let api: Api;
  beforeEach(() => {
    GlobalRegistrator.register({ url: "http://localhost:8642/doc.html", width: 1400, height: 900 });
    document.body.innerHTML = BODY;
    $("#rd-article").innerHTML = ARTICLE;
    api = load();
    api.rdInitZoom({ pictures: "#rd-article img, #rd-article svg", exclude: ".rd-plotly, .rd-deckgl, .rd-cytoscape" });
  });
  afterEach(async () => {
    await GlobalRegistrator.unregister();
  });

  test("a click on a diagram opens a copy of it full screen", () => {
    click($("#m rect"));
    const box = $(".rd-zoom");
    expect(box.getAttribute("role")).toBe("dialog");
    expect(box.getAttribute("aria-modal")).toBe("true");
    expect(document.body.classList.contains("rd-zoom-open")).toBe(true);
    const copy = box.querySelector(".rd-zoom-stage > svg") as SVGElement;
    // The outermost svg is the picture, and its fixed width is cleared to fill the stage.
    expect(copy.getAttribute("width")).toBeNull();
    expect(copy.getAttribute("viewBox")).toBe("0 0 400 200");
    expect($("#rd-article #m")).not.toBeNull(); // the page keeps its own
    expect(document.activeElement?.getAttribute("data-rd-zoom")).toBe("close");
  });

  test("a chart's svg is an interactive surface, not a picture", () => {
    click($("#chart"));
    expect(document.querySelector(".rd-zoom")).toBeNull();
  });

  test("an image opens too", () => {
    click($("#pic"));
    expect($(".rd-zoom-stage > img").tagName).toBe("IMG");
  });

  test("the wheel zooms the copy, and Fit restores it", () => {
    click($("#m"));
    const copy = $(".rd-zoom-stage > svg");
    wheel($(".rd-zoom-stage"), { deltaY: -400 });
    const zoomed = (copy.getAttribute("viewBox") ?? "").split(" ").map(Number);
    expect(zoomed[2]).toBeLessThan(400);
    click($('[data-rd-zoom="fit"]'));
    expect(copy.getAttribute("viewBox")).toBe("0 0 400 200");
    click($('[data-rd-zoom="in"]'));
    expect(Number(copy.getAttribute("viewBox")?.split(" ")[2])).toBeCloseTo(400 / 1.25);
  });

  test("Escape and the close button both close it and hand focus back", () => {
    click($("#m"));
    document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
    expect(document.querySelector(".rd-zoom")).toBeNull();
    expect(document.body.classList.contains("rd-zoom-open")).toBe(false);
    click($("#m"));
    click($('[data-rd-zoom="close"]'));
    expect(document.querySelector(".rd-zoom")).toBeNull();
  });
});

describe("in-page zoom", () => {
  let api: Api;
  beforeEach(() => {
    GlobalRegistrator.register({ url: "http://localhost:8642/doc.html", width: 1400, height: 900 });
    document.body.innerHTML = BODY;
    $("#rd-article").innerHTML = ARTICLE;
    api = load();
    api.rdInitZoom({ pictures: "#rd-article img, #rd-article svg", exclude: ".rd-plotly" });
  });
  afterEach(async () => {
    await GlobalRegistrator.unregister();
  });

  test("a plain wheel scrolls the page and never zooms", () => {
    const e = wheel($("#m"), { deltaY: -400 });
    expect(e.defaultPrevented).toBe(false);
    expect($("#m").getAttribute("viewBox")).toBe("0 0 400 200");
  });

  test("Ctrl + wheel (or a pinch) zooms the diagram in place, never wider than fit", () => {
    const e = wheel($("#m"), { deltaY: -400, ctrlKey: true });
    expect(e.defaultPrevented).toBe(true);
    expect(Number($("#m").getAttribute("viewBox")?.split(" ")[2])).toBeLessThan(400);
    wheel($("#m"), { deltaY: 4000, ctrlKey: true });
    expect(Number($("#m").getAttribute("viewBox")?.split(" ")[2])).toBeCloseTo(400);
  });

  test("the modal opens on the view the reader zoomed to", () => {
    wheel($("#m"), { deltaY: -400, ctrlKey: true });
    const inPage = $("#m").getAttribute("viewBox");
    click($("#m"));
    expect($(".rd-zoom-stage > svg").getAttribute("viewBox")).toBe(inPage);
  });
});
