"use strict";
// Full-screen diagram viewer with deep zoom (ADR-024).
//
// Inlined into its own script element BEFORE viewer.js, so these functions are
// hoisted into global scope by the time viewer.js boots. Placeholder-free by
// contract (ADR-008). The theme showcase inlines the same file, so a diagram
// behaves the same on both pages.
//
// Three kinds of diagram, one behaviour:
//   an SVG (mermaid, draw.io, any inline svg) and a raster img open in a modal
//   on click; a Cytoscape.js graph opens from its "Full screen" button, because
//   a click inside a graph is for dragging its nodes.
//
// In the modal, the wheel zooms about the cursor and a drag pans. An SVG zooms
// through its viewBox, so it stays vector-sharp at any depth; an img zooms by
// transform; a graph is a second, fully interactive Cytoscape.js instance.
// In the page, only Ctrl/Cmd + wheel (a trackpad pinch arrives as exactly this)
// zooms a diagram in place. A plain wheel always scrolls the page: a long
// document must never trap the reader inside a diagram.
//
// (Deliberately no literal script tags in this comment: a test balances the
// opening/closing tag counts in the assembled page to catch payloads that could
// break out of their script element.)

var RD_ZOOM_DEEPEST = 40;     // furthest in, as a multiple of the fitted view
var RD_ZOOM_WIDEST = 0.5;     // furthest out in the modal, as a multiple of fit
var RD_ZOOM_STEP = 1.25;      // one button press or key press
var RD_ZOOM_WHEEL = 0.0015;   // wheel sensitivity: factor = exp(-deltaY * this)

// Zoom a viewBox about a point given in viewBox units. `factor` > 1 zooms in.
// The point stays where it is on screen. Depth is clamped relative to `base`
// (the fitted viewBox): no deeper than RD_ZOOM_DEEPEST, no wider than `widest`.
function rdZoomViewBox(vb, px, py, factor, base, widest) {
  var minW = base.w / RD_ZOOM_DEEPEST;
  var maxW = base.w / (widest || RD_ZOOM_WIDEST);
  var w = Math.min(maxW, Math.max(minW, vb.w / factor));
  var f = vb.w / w;
  return { x: px - (px - vb.x) / f, y: py - (py - vb.y) / f, w: w, h: vb.h / f };
}

// The viewBox an SVG is drawn with, or one made from its size when it has none.
function rdViewBoxOf(svg) {
  var vb = svg.getAttribute("viewBox");
  if (vb) {
    var n = vb.trim().split(/[\s,]+/).map(Number);
    if (n.length === 4 && n[2] > 0 && n[3] > 0) { return { x: n[0], y: n[1], w: n[2], h: n[3] }; }
  }
  var w = parseFloat(svg.getAttribute("width")) || 0;
  var h = parseFloat(svg.getAttribute("height")) || 0;
  if ((!w || !h) && svg.getBBox) {
    try { var b = svg.getBBox(); return { x: b.x, y: b.y, w: b.width || 1, h: b.height || 1 }; } catch (e) {}
  }
  return { x: 0, y: 0, w: w || 1, h: h || 1 };
}

// A zoom controller for one SVG. The default preserveAspectRatio (xMidYMid meet)
// letterboxes the viewBox into the element, which is what the maths assumes.
function rdSvgZoom(svg, widest) {
  var base = rdViewBoxOf(svg);
  var vb = { x: base.x, y: base.y, w: base.w, h: base.h };
  function apply() { svg.setAttribute("viewBox", [vb.x, vb.y, vb.w, vb.h].join(" ")); }
  // Screen point -> viewBox point, and the current pixels-per-unit scale. With no
  // layout (a hidden element, or a test DOM) it falls back to the view's centre.
  function toSvg(cx, cy) {
    var r = svg.getBoundingClientRect();
    var s = Math.min(r.width / vb.w, r.height / vb.h);
    if (!(s > 0) || !isFinite(s)) { return { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2, s: 0 }; }
    var ox = r.left + (r.width - vb.w * s) / 2;
    var oy = r.top + (r.height - vb.h * s) / 2;
    return { x: vb.x + (cx - ox) / s, y: vb.y + (cy - oy) / s, s: s };
  }
  apply();
  return {
    zoomAt: function (cx, cy, f) { var p = toSvg(cx, cy); vb = rdZoomViewBox(vb, p.x, p.y, f, base, widest); apply(); },
    zoomCentre: function (f) {
      var r = svg.getBoundingClientRect();
      this.zoomAt(r.left + r.width / 2, r.top + r.height / 2, f);
    },
    panBy: function (dx, dy) {
      var s = toSvg(0, 0).s;
      if (!s) { return; }
      vb.x -= dx / s; vb.y -= dy / s; apply();
    },
    reset: function () { vb = { x: base.x, y: base.y, w: base.w, h: base.h }; apply(); },
    viewBox: function () { return { x: vb.x, y: vb.y, w: vb.w, h: vb.h }; }
  };
}

// A zoom controller for a raster image, by transform inside the modal stage.
function rdImgZoom(img, stage) {
  var s = 1, tx = 0, ty = 0, fit = 1;
  function apply() { img.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")"; }
  function reset() {
    var w = img.naturalWidth || img.width || 1, h = img.naturalHeight || img.height || 1;
    var r = stage.getBoundingClientRect();
    fit = Math.min(r.width / w, r.height / h) || 1;
    s = fit; tx = (r.width - w * s) / 2; ty = (r.height - h * s) / 2;
    apply();
  }
  if (img.complete) { reset(); } else { img.addEventListener("load", reset); }
  return {
    zoomAt: function (cx, cy, f) {
      var r = stage.getBoundingClientRect();
      var next = Math.min(fit * RD_ZOOM_DEEPEST, Math.max(fit * RD_ZOOM_WIDEST, s * f));
      var k = next / s, px = cx - r.left, py = cy - r.top;
      tx = px - (px - tx) * k; ty = py - (py - ty) * k; s = next; apply();
    },
    zoomCentre: function (f) {
      var r = stage.getBoundingClientRect();
      this.zoomAt(r.left + r.width / 2, r.top + r.height / 2, f);
    },
    panBy: function (dx, dy) { tx += dx; ty += dy; apply(); },
    reset: reset
  };
}

// A zoom controller for a Cytoscape.js instance: the graph zooms and pans itself.
function rdCyZoom(cy, minLevel) {
  function level(l) { return Math.max(minLevel || 0, Math.min(l, cy.maxZoom())); }
  return {
    zoomAt: function (cx, cy2, f) {
      var r = cy.container().getBoundingClientRect();
      cy.zoom({ level: level(cy.zoom() * f), renderedPosition: { x: cx - r.left, y: cy2 - r.top } });
    },
    zoomCentre: function (f) {
      cy.zoom({ level: level(cy.zoom() * f), renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
    },
    panBy: function () {},
    reset: function () { cy.fit(undefined, 30); }
  };
}

// Build the modal around `content` (an element to show, or a function that fills
// the stage and returns a controller). Returns the modal's close function.
function rdOpenZoom(content, opener) {
  rdCloseZoom();
  var box = document.createElement("div");
  box.className = "rd-zoom";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Diagram, full screen");

  var bar = document.createElement("div");
  bar.className = "rd-zoom-bar";
  [["out", "−", "Zoom out"], ["fit", "Fit", "Fit to screen"], ["in", "+", "Zoom in"]].forEach(function (b) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("data-rd-zoom", b[0]);
    btn.setAttribute("aria-label", b[2]);
    btn.textContent = b[1];
    bar.appendChild(btn);
  });
  var hint = document.createElement("span");
  hint.className = "rd-zoom-hint";
  hint.textContent = "Scroll to zoom · drag to pan · Esc to close";
  bar.appendChild(hint);
  var close = document.createElement("button");
  close.type = "button";
  close.setAttribute("data-rd-zoom", "close");
  close.setAttribute("aria-label", "Close full screen");
  close.textContent = "Close";
  bar.appendChild(close);

  var stage = document.createElement("div");
  stage.className = "rd-zoom-stage";
  box.appendChild(bar);
  box.appendChild(stage);
  document.body.appendChild(box);
  document.body.classList.add("rd-zoom-open");

  var ctl;
  var selfManaged = typeof content === "function";
  if (selfManaged) {
    ctl = content(stage);
  } else if (content.tagName && content.tagName.toLowerCase() === "img") {
    stage.appendChild(content);
    ctl = rdImgZoom(content, stage);
  } else {
    stage.appendChild(content);
    ctl = rdSvgZoom(content, RD_ZOOM_WIDEST);
  }
  box.__rdZoom = { ctl: ctl, opener: opener || null };

  bar.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("[data-rd-zoom]") : null;
    if (!b) { return; }
    var what = b.getAttribute("data-rd-zoom");
    if (what === "close") { rdCloseZoom(); }
    else if (what === "in") { ctl.zoomCentre(RD_ZOOM_STEP); }
    else if (what === "out") { ctl.zoomCentre(1 / RD_ZOOM_STEP); }
    else { ctl.reset(); }
  });

  // A graph handles its own wheel and drag; everything else is handled here.
  if (!selfManaged) {
    stage.addEventListener("wheel", function (e) {
      e.preventDefault();
      ctl.zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * RD_ZOOM_WHEEL));
    }, { passive: false });
    var drag = null;
    stage.addEventListener("pointerdown", function (e) {
      drag = { x: e.clientX, y: e.clientY };
      stage.classList.add("rd-dragging");
      if (stage.setPointerCapture) { try { stage.setPointerCapture(e.pointerId); } catch (err) {} }
    });
    stage.addEventListener("pointermove", function (e) {
      if (!drag) { return; }
      ctl.panBy(e.clientX - drag.x, e.clientY - drag.y);
      drag = { x: e.clientX, y: e.clientY };
    });
    ["pointerup", "pointercancel"].forEach(function (t) {
      stage.addEventListener(t, function () { drag = null; stage.classList.remove("rd-dragging"); });
    });
    stage.addEventListener("dblclick", function () { ctl.reset(); });
  }

  close.focus();
  return rdCloseZoom;
}

function rdCloseZoom() {
  var box = document.querySelector(".rd-zoom");
  if (!box) { return; }
  var state = box.__rdZoom || {};
  if (state.ctl && state.ctl.destroy) { state.ctl.destroy(); }
  box.remove();
  document.body.classList.remove("rd-zoom-open");
  if (state.opener && state.opener.focus) { try { state.opener.focus({ preventScroll: true }); } catch (e) {} }
}

// Open a copy of an SVG or img. A mermaid svg carries a fixed pixel width and a
// max-width style; both are cleared so the copy fills the stage.
function rdZoomPicture(node) {
  var clone = node.cloneNode(true);
  if (clone.tagName.toLowerCase() === "svg") {
    clone.removeAttribute("width");
    clone.removeAttribute("height");
    clone.style.maxWidth = "";
    clone.style.width = "";
    clone.style.height = "";
    // Keep the view the reader zoomed to in the page, if any.
    if (node.__rdZoom) { clone.setAttribute("viewBox", node.getAttribute("viewBox")); }
    else { var vb = rdViewBoxOf(node); clone.setAttribute("viewBox", [vb.x, vb.y, vb.w, vb.h].join(" ")); }
  } else {
    clone.removeAttribute("width");
    clone.removeAttribute("height");
  }
  return rdOpenZoom(clone, node);
}

// Open a second, fully interactive copy of a rendered graph. The graph element
// carries its instance and the style it was built with (viewer-cytoscape.js);
// positions travel with the elements, so the copy needs no second layout.
function rdZoomGraph(el, opener) {
  var cy = el.__rdCy;
  if (!cy || !window.cytoscape) { return null; }
  return rdOpenZoom(function (stage) {
    var host = document.createElement("div");
    host.className = "rd-zoom-cy";
    stage.appendChild(host);
    var copy = window.cytoscape({
      container: host,
      elements: cy.elements().jsons(),
      style: el.__rdCyStyle,
      layout: { name: "preset" },
      boxSelectionEnabled: false,
      minZoom: 0.05,
      maxZoom: 20
    });
    copy.fit(undefined, 30);
    var ctl = rdCyZoom(copy, 0);
    ctl.destroy = function () { copy.destroy(); };
    return ctl;
  }, opener);
}

// Wire a page. `pictures` selects the SVGs and images that open on click;
// `exclude` names containers whose SVGs are interactive surfaces (a chart), not
// pictures. Graphs need no selector: any element carrying a rendered instance
// (`__rdCy`) is found from its "Full screen" button or a Ctrl/Cmd + wheel.
function rdInitZoom(opts) {
  var pictures = opts.pictures;
  var exclude = opts.exclude || "";

  function pictureAt(target) {
    var hit = target.closest ? target.closest(pictures) : null;
    if (!hit || hit.closest(".rd-zoom")) { return null; }
    if (exclude && hit.closest(exclude)) { return null; }
    // The outermost svg is the picture; a nested svg is part of it.
    while (hit.parentElement && hit.parentElement.closest("svg") && hit.parentElement.closest(pictures)) {
      hit = hit.parentElement.closest("svg");
    }
    return hit;
  }

  function graphAt(target) {
    for (var el = target; el && el !== document; el = el.parentElement) {
      if (el.__rdCy) { return el; }
    }
    return null;
  }

  document.addEventListener("click", function (e) {
    var expand = e.target.closest ? e.target.closest(".rd-zoom-expand") : null;
    if (expand) {
      var graph = graphAt(expand);
      if (graph) { e.preventDefault(); rdZoomGraph(graph, expand); }
      return;
    }
    var hit = pictureAt(e.target);
    if (!hit) { return; }
    e.preventDefault();
    rdZoomPicture(hit);
  });

  // In place: Ctrl/Cmd + wheel, or a trackpad pinch, zooms the diagram under the
  // pointer. Never deeper than the modal, and never wider than its fitted view.
  document.addEventListener("wheel", function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.target.closest(".rd-zoom")) { return; }
    var f = Math.exp(-e.deltaY * RD_ZOOM_WHEEL);
    var graph = graphAt(e.target);
    if (graph) {
      e.preventDefault();
      if (graph.__rdCyFit === undefined) { graph.__rdCyFit = graph.__rdCy.zoom(); }
      rdCyZoom(graph.__rdCy, graph.__rdCyFit).zoomAt(e.clientX, e.clientY, f);
      return;
    }
    var hit = pictureAt(e.target);
    if (!hit || hit.tagName.toLowerCase() !== "svg") { return; }
    e.preventDefault();
    if (!hit.__rdZoom) { hit.__rdZoom = rdSvgZoom(hit, 1); }
    hit.__rdZoom.zoomAt(e.clientX, e.clientY, f);
  }, { passive: false });

  document.addEventListener("keydown", function (e) {
    var box = document.querySelector(".rd-zoom");
    if (!box) { return; }
    var ctl = box.__rdZoom && box.__rdZoom.ctl;
    if (e.key === "Escape") { rdCloseZoom(); }
    else if (ctl && (e.key === "+" || e.key === "=")) { ctl.zoomCentre(RD_ZOOM_STEP); }
    else if (ctl && e.key === "-") { ctl.zoomCentre(1 / RD_ZOOM_STEP); }
    else if (ctl && e.key === "0") { ctl.reset(); }
  });
}
