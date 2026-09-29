"use strict";
// Heading sidebar and section folds for richdocs pages (ADR-021, ADR-022).
//
// Inlined into its own script element BEFORE viewer.js, so these functions are
// hoisted into global scope by the time viewer.js boots. Placeholder-free by
// contract (ADR-008). viewer.js calls rdInitToc() once, right after the markdown
// is parsed and before any fenced block is upgraded, so only authored headings
// are indexed, never a heading inside a rendered diagram. The theme showcase
// inlines the same file and calls rdInitToc() with its own options, so the two
// pages cannot drift apart.
//
// Both are derived entirely from the rendered headings. They hold no authoring
// state, so regenerating the page always rebuilds them (ADR-001).
//
// (Deliberately no literal script tags in this comment: a test balances the
// opening/closing tag counts in the assembled page to catch payloads that could
// break out of their script element.)

// Fewer headings than this and a sidebar is noise: the page keeps its
// single-column layout and the header shows no contents button.
var RD_TOC_MIN_HEADINGS = 3;
var RD_TOC_SELECTOR = "h1, h2, h3, h4";
// Only the wide layout remembers its state. The narrow drawer always opens
// closed, because a drawer remembered open would cover the article on load.
var RD_TOC_STORAGE_KEY = "richdocs-toc";
// The sidebar (16rem) plus the unchanged 52rem article column, plus gutters.
// Below this the sidebar becomes a drawer over the article.
var RD_TOC_NARROW_QUERY = "(max-width: 72rem)";

// GitHub-style slug: lower case, punctuation dropped, spaces to hyphens.
// Letters and digits in any script survive, so a heading in Japanese still
// gets a readable anchor.
function rdSlugify(text) {
  var slug = String(text).trim().toLowerCase()
    .replace(/[^\p{L}\p{N}\s_-]/gu, "")
    .replace(/\s+/g, "-");
  return slug || "section";
}

// Give every heading a stable, unique id. An id already on a heading (raw HTML
// in the markdown) is kept. Duplicates take -1, -2, … in document order, so the
// same markdown always yields the same anchors. Ids already on the page are
// reserved first, so a heading can never steal the header's own id.
// `data-rd-toc-label` overrides the entry text, for a heading whose own text is
// filled in later by script (the showcase hero shows the brand name).
function rdAssignHeadingIds(headings, doc) {
  var used = {};
  (doc || document).querySelectorAll("[id]").forEach(function (el) { used[el.id] = true; });
  return headings.map(function (h) {
    var text = (h.getAttribute("data-rd-toc-label") || h.textContent).trim();
    if (!h.id) {
      var base = rdSlugify(text);
      var id = base;
      for (var n = 1; used[id]; n++) { id = base + "-" + n; }
      h.id = id;
      used[id] = true;
    }
    return { level: Number(h.tagName.charAt(1)), id: h.id, text: text, el: h };
  });
}

// Nest entries into lists by heading level. A skipped level (h2 then h4) nests
// one step, not two, and a shallower heading after a deep run climbs back out
// to the nearest list that holds its level. Each row is a branch button (or a
// spacer, for a leaf) followed by the link, so every level can be folded.
function rdBuildTocList(entries, doc) {
  var d = doc || document;
  var root = d.createElement("ol");
  root.id = "rd-toc-list";
  var frames = [{ level: null, list: root, last: null }];
  entries.forEach(function (e) {
    while (frames.length > 1 && e.level < frames[frames.length - 1].level) { frames.pop(); }
    var top = frames[frames.length - 1];
    if (top.level === null) { top.level = e.level; }
    if (e.level > top.level && top.last) {
      var sub = d.createElement("ol");
      top.last.appendChild(sub);
      top = { level: e.level, list: sub, last: null };
      frames.push(top);
    }
    var li = d.createElement("li");
    var row = d.createElement("div");
    row.className = "rd-toc-row";
    var spacer = d.createElement("span");
    spacer.className = "rd-toc-spacer";
    var a = d.createElement("a");
    a.href = "#" + encodeURIComponent(e.id);
    a.textContent = e.text;
    a.setAttribute("data-rd-toc-id", e.id);
    a.className = "rd-toc-level-" + e.level;
    row.appendChild(spacer);
    row.appendChild(a);
    li.appendChild(row);
    top.list.appendChild(li);
    top.last = li;
  });
  // A row learns it is a branch only once a child arrives, so swap the spacer for
  // a toggle afterwards rather than guessing ahead.
  root.querySelectorAll("li").forEach(function (li) {
    var sub = li.lastElementChild;
    if (!sub || sub.tagName !== "OL") { return; }
    var a = li.querySelector("a[data-rd-toc-id]");
    sub.id = "rd-toc-sub-" + a.getAttribute("data-rd-toc-id");
    var btn = d.createElement("button");
    btn.type = "button";
    btn.className = "rd-toc-branch";
    btn.setAttribute("aria-expanded", "true");
    btn.setAttribute("aria-controls", sub.id);
    btn.setAttribute("aria-label", "Subsections of " + a.textContent);
    li.querySelector(".rd-toc-spacer").replaceWith(btn);
  });
  return root;
}

// Open or close one branch of the contents tree.
function rdSetBranch(li, open) {
  var btn = li.querySelector(":scope > .rd-toc-row > .rd-toc-branch");
  var sub = li.lastElementChild;
  if (!btn || !sub || sub.tagName !== "OL") { return; }
  li.classList.toggle("rd-toc-closed", !open);
  btn.setAttribute("aria-expanded", open ? "true" : "false");
  sub.hidden = !open;
}

// The heading a node starts, if any: a bare heading, or one already wrapped in
// a fold head by an earlier (deeper) pass.
function rdFoldLevel(node) {
  if (node.nodeType !== 1) { return 0; }
  var el = node.classList.contains("rd-fold-head") ? node.lastElementChild : node;
  var m = el && /^H([1-6])$/.exec(el.tagName);
  return m ? Number(m[1]) : 0;
}

// Make every section foldable in place. A section is a heading plus everything
// after it up to the next heading at the same level or shallower. Deepest first
// (reverse document order), so a parent sweeps up its already-wrapped children.
// The lone shallowest heading is the document title: folding it would fold the
// whole page, so it gets no button. Nor does a heading with nothing under it.
// The button sits BESIDE the heading, not inside it, so the heading's text (and
// so its accessible name, anchor and contents entry) is left untouched.
function rdInitFolds(entries, doc) {
  var d = doc || document;
  var folds = {};
  if (!entries.length) { return folds; }
  var top = Math.min.apply(null, entries.map(function (e) { return e.level; }));
  var loneTop = entries.filter(function (e) { return e.level === top; }).length === 1;

  entries.slice().reverse().forEach(function (e) {
    if (loneTop && e.level === top) { return; }
    var h = e.el;
    var bodyNodes = [];
    for (var n = h.nextSibling; n; n = n.nextSibling) {
      var lv = rdFoldLevel(n);
      if (lv && lv <= e.level) { break; }
      bodyNodes.push(n);
    }
    if (!bodyNodes.some(function (n) { return n.nodeType === 1 || n.textContent.trim(); })) { return; }

    var body = d.createElement("div");
    body.className = "rd-fold-body";
    var bodyId = "rd-fold-" + e.id;
    for (var k = 1; d.getElementById(bodyId); k++) { bodyId = "rd-fold-" + e.id + "-" + k; }
    body.id = bodyId;
    bodyNodes.forEach(function (n) { body.appendChild(n); });

    var head = d.createElement("div");
    head.className = "rd-fold-head rd-fold-level-" + e.level;
    var btn = d.createElement("button");
    btn.type = "button";
    btn.className = "rd-fold";
    btn.setAttribute("aria-expanded", "true");
    btn.setAttribute("aria-controls", bodyId);
    btn.setAttribute("aria-label", "Section " + e.text);
    h.before(head);
    head.appendChild(btn);
    head.appendChild(h);
    head.after(body);
    folds[e.id] = { button: btn, body: body };
  });
  return folds;
}

// Fold or unfold one section. A folded body keeps its layout width (see
// viewer-toc.css), so a chart or diagram re-rendered while folded, on a theme
// flip, still measures a real box.
function rdSetFold(fold, open) {
  fold.button.setAttribute("aria-expanded", open ? "true" : "false");
  fold.body.hidden = !open;
}

function rdTocStored() {
  try { return localStorage.getItem(RD_TOC_STORAGE_KEY); } catch (e) { return null; }
}

function rdTocStore(state) {
  try { localStorage.setItem(RD_TOC_STORAGE_KEY, state); } catch (e) {}
}

// Build the sidebar and section folds for `article` and wire the toggles.
// Returns a small controller (used by the tests), or null when the document has
// too few headings.
//
// `opts` lets a page other than the viewer reuse this (the showcase does):
//   header   — the sticky bar headings must land below (default header.rd-header)
//   selector — which headings to index (default h1 to h4)
//   folds    — false to skip section folding (default on)
function rdInitToc(article, opts) {
  var o = opts || {};
  var nav = document.getElementById("rd-toc");
  var toggle = document.getElementById("rd-toc-toggle");
  var header = o.header || document.querySelector("header.rd-header");
  var root = document.documentElement;
  var headings = Array.prototype.slice.call(article.querySelectorAll(o.selector || RD_TOC_SELECTOR));
  if (!nav || !toggle || headings.length < RD_TOC_MIN_HEADINGS) { return null; }

  var entries = rdAssignHeadingIds(headings, document);
  var links = {};

  // The sidebar's own head: a title and the collapse control. On the wide layout
  // a collapsed sidebar shrinks to a rail holding just this control, so there is
  // always a way back in exactly where the reader left it.
  var head = document.createElement("div");
  head.className = "rd-toc-head";
  var title = document.createElement("span");
  title.className = "rd-toc-title";
  title.textContent = "Contents";
  var collapse = document.createElement("button");
  collapse.type = "button";
  collapse.id = "rd-toc-collapse";
  collapse.setAttribute("aria-controls", "rd-toc-list");
  var collapseMark = document.createElement("span");
  collapseMark.setAttribute("aria-hidden", "true");
  collapseMark.textContent = "‹";
  collapse.appendChild(collapseMark);
  head.appendChild(title);
  head.appendChild(collapse);

  nav.replaceChildren(head, rdBuildTocList(entries, document));
  nav.querySelectorAll("a[data-rd-toc-id]").forEach(function (a) {
    links[a.getAttribute("data-rd-toc-id")] = a;
  });

  var folds = o.folds === false ? {} : rdInitFolds(entries, document);
  Object.keys(folds).forEach(function (id) {
    folds[id].button.addEventListener("click", function () {
      rdSetFold(folds[id], folds[id].button.getAttribute("aria-expanded") !== "true");
    });
  });

  var mql = window.matchMedia ? window.matchMedia(RD_TOC_NARROW_QUERY) : null;
  function isNarrow() { return !!(mql && mql.matches); }

  // Sticky header height, so headings scroll to just below it rather than under it.
  function measureHeader() {
    var h = header ? header.offsetHeight : 0;
    root.style.setProperty("--rd-header-h", (h || 48) + "px");
    return h || 48;
  }

  function setOpen(open, persist) {
    root.setAttribute("data-toc", open ? "open" : "closed");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    collapse.setAttribute("aria-expanded", open ? "true" : "false");
    collapse.setAttribute("aria-label", open ? "Collapse contents" : "Expand contents");
    if (persist && !isNarrow()) { rdTocStore(open ? "open" : "closed"); }
  }

  // Wide: honour the remembered state (open by default). Narrow: always closed.
  function applyLayout() {
    measureHeader();
    setOpen(isNarrow() ? false : rdTocStored() !== "closed", false);
  }

  // The current entry carries aria-current. Its ancestors carry a trail mark, so
  // when a branch is folded shut its visible parent still shows where you are.
  var active = null;
  function setActive(id) {
    if (id === active) { return; }
    if (active && links[active]) { links[active].removeAttribute("aria-current"); }
    nav.querySelectorAll(".rd-toc-trail").forEach(function (a) { a.classList.remove("rd-toc-trail"); });
    active = id;
    if (!id || !links[id]) { return; }
    links[id].setAttribute("aria-current", "location");
    var li = links[id].closest("li");
    for (li = li && li.parentElement.closest("li"); li; li = li.parentElement.closest("li")) {
      var a = li.querySelector("a[data-rd-toc-id]");
      if (a) { a.classList.add("rd-toc-trail"); }
    }
  }

  // A heading inside a folded section is not on screen, whatever its box says.
  function isFolded(el) {
    return !!(el.closest && el.closest(".rd-fold-body[hidden]"));
  }

  // The current entry is the last visible heading whose top has passed under the
  // header. Before the first heading is reached, the first entry is current. The
  // line sits below the heading's scroll-margin-top (viewer-toc.css, 0.75rem), or
  // a heading just jumped to would land a few pixels short of it and lose the
  // mark. At the very bottom the last entry wins: short closing sections can never
  // scroll up to the line, and would otherwise never be marked at all.
  function refreshActive() {
    var line = measureHeader() + 24;
    var current = entries[0].id;
    for (var i = 0; i < entries.length; i++) {
      if (isFolded(entries[i].el)) { continue; }
      if (entries[i].el.getBoundingClientRect().top <= line) { current = entries[i].id; } else { break; }
    }
    var page = document.documentElement;
    if (page.scrollHeight > window.innerHeight && window.innerHeight + window.scrollY >= page.scrollHeight - 2) {
      current = entries[entries.length - 1].id;
    }
    setActive(current);
  }

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  // Unfold whatever hides a heading: its own section, and every section around it.
  function reveal(target) {
    if (folds[target.id]) { rdSetFold(folds[target.id], true); }
    for (var body = target.closest(".rd-fold-body"); body; body = body.parentElement.closest(".rd-fold-body")) {
      var btn = document.querySelector('.rd-fold[aria-controls="' + body.id + '"]');
      if (btn) { btn.setAttribute("aria-expanded", "true"); }
      body.hidden = false;
    }
  }

  function scrollToId(id, smooth) {
    var target = document.getElementById(id);
    if (!target) { return false; }
    reveal(target);
    if (target.scrollIntoView) {
      target.scrollIntoView({ behavior: smooth && !reducedMotion() ? "smooth" : "auto", block: "start" });
    }
    setActive(id);
    return true;
  }

  // Select an entry: scroll, record the fragment, and move keyboard focus to the
  // heading so the next Tab continues from there, not from the sidebar.
  function go(id) {
    if (!scrollToId(id, true)) { return; }
    var hash = "#" + encodeURIComponent(id);
    try { history.pushState(null, "", hash); } catch (e) { location.hash = hash; }
    var target = document.getElementById(id);
    if (!target.hasAttribute("tabindex")) { target.setAttribute("tabindex", "-1"); }
    try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }
    if (isNarrow()) { setOpen(false, false); }
  }

  function idFromHash() {
    var raw = location.hash.slice(1);
    if (!raw) { return null; }
    try { return decodeURIComponent(raw); } catch (e) { return raw; }
  }

  nav.addEventListener("click", function (e) {
    var branch = e.target.closest ? e.target.closest(".rd-toc-branch") : null;
    if (branch) {
      rdSetBranch(branch.closest("li"), branch.getAttribute("aria-expanded") !== "true");
      return;
    }
    var a = e.target.closest ? e.target.closest("a[data-rd-toc-id]") : null;
    if (!a) { return; }
    e.preventDefault();
    go(a.getAttribute("data-rd-toc-id"));
  });

  // Opening the drawer moves focus into it: the nav sits after the header in
  // document order, so Tab from the button would otherwise skip past it. The
  // wide sidebar is already in the flow and leaves focus where it is.
  function flip() {
    var open = root.getAttribute("data-toc") !== "open";
    setOpen(open, true);
    if (open && isNarrow()) {
      var first = (active && links[active]) || nav.querySelector("a[data-rd-toc-id]");
      if (first) { first.focus(); }
    }
    return open;
  }
  toggle.addEventListener("click", flip);

  // The sidebar's own control. In the drawer it is the close button, and hands
  // focus back to the header button that opened the drawer.
  collapse.addEventListener("click", function () {
    var open = flip();
    if (!open && isNarrow()) { toggle.focus(); }
  });

  // Escape closes the drawer and hands focus back to the button that opened it.
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" || !isNarrow() || root.getAttribute("data-toc") !== "open") { return; }
    var inside = nav.contains(document.activeElement);
    setOpen(false, false);
    if (inside) { toggle.focus(); }
  });

  // A tap outside the open drawer dismisses it, as a drawer should.
  document.addEventListener("click", function (e) {
    if (!isNarrow() || root.getAttribute("data-toc") !== "open") { return; }
    if (nav.contains(e.target) || toggle.contains(e.target)) { return; }
    setOpen(false, false);
  });

  // The article is rendered after load, so the browser's own jump to the fragment
  // has already missed. Redo it now, and again on back/forward.
  window.addEventListener("popstate", function () {
    var id = idFromHash();
    if (id) { scrollToId(id, false); }
  });

  var pending = false;
  window.addEventListener("scroll", function () {
    if (pending) { return; }
    pending = true;
    (window.requestAnimationFrame || setTimeout)(function () { pending = false; refreshActive(); });
  }, { passive: true });

  if (mql && mql.addEventListener) { mql.addEventListener("change", applyLayout); }
  window.addEventListener("resize", measureHeader);

  root.classList.add("rd-has-toc");
  toggle.hidden = false;
  applyLayout();
  var initial = idFromHash();
  if (!(initial && scrollToId(initial, false))) { refreshActive(); }

  return {
    entries: entries,
    folds: folds,
    go: go,
    setOpen: setOpen,
    isNarrow: isNarrow,
    applyLayout: applyLayout,
    refreshActive: refreshActive
  };
}
