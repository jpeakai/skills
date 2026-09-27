"use strict";
// Heading sidebar for the richdocs viewer (ADR-021).
//
// Inlined into its own script element BEFORE viewer.js, so these functions are
// hoisted into global scope by the time viewer.js boots. Placeholder-free by
// contract (ADR-008). viewer.js calls rdInitToc() once, right after the markdown
// is parsed and before any fenced block is upgraded, so only authored headings
// are indexed, never a heading inside a rendered diagram.
//
// The sidebar is derived entirely from the rendered markdown. It holds no
// authoring state, so regenerating the companion always rebuilds it (ADR-001).
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
function rdAssignHeadingIds(headings, doc) {
  var used = {};
  (doc || document).querySelectorAll("[id]").forEach(function (el) { used[el.id] = true; });
  return headings.map(function (h) {
    var text = h.textContent.trim();
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
// to the nearest list that holds its level.
function rdBuildTocList(entries, doc) {
  var d = doc || document;
  var root = d.createElement("ol");
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
    var a = d.createElement("a");
    a.href = "#" + encodeURIComponent(e.id);
    a.textContent = e.text;
    a.setAttribute("data-rd-toc-id", e.id);
    a.className = "rd-toc-level-" + e.level;
    li.appendChild(a);
    top.list.appendChild(li);
    top.last = li;
  });
  return root;
}

function rdTocStored() {
  try { return localStorage.getItem(RD_TOC_STORAGE_KEY); } catch (e) { return null; }
}

function rdTocStore(state) {
  try { localStorage.setItem(RD_TOC_STORAGE_KEY, state); } catch (e) {}
}

// Build the sidebar for `article` and wire the header toggle. Returns a small
// controller (used by the tests), or null when the document has too few headings.
function rdInitToc(article) {
  var nav = document.getElementById("rd-toc");
  var toggle = document.getElementById("rd-toc-toggle");
  var header = document.querySelector("header.rd-header");
  var root = document.documentElement;
  var headings = Array.prototype.slice.call(article.querySelectorAll(RD_TOC_SELECTOR));
  if (!nav || !toggle || headings.length < RD_TOC_MIN_HEADINGS) { return null; }

  var entries = rdAssignHeadingIds(headings, document);
  var links = {};
  nav.replaceChildren(rdBuildTocList(entries, document));
  nav.querySelectorAll("a[data-rd-toc-id]").forEach(function (a) {
    links[a.getAttribute("data-rd-toc-id")] = a;
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
    if (persist && !isNarrow()) { rdTocStore(open ? "open" : "closed"); }
  }

  // Wide: honour the remembered state (open by default). Narrow: always closed.
  function applyLayout() {
    measureHeader();
    setOpen(isNarrow() ? false : rdTocStored() !== "closed", false);
  }

  var active = null;
  function setActive(id) {
    if (id === active) { return; }
    if (active && links[active]) { links[active].removeAttribute("aria-current"); }
    active = id;
    if (id && links[id]) { links[id].setAttribute("aria-current", "location"); }
  }

  // The current entry is the last heading whose top has passed under the header.
  // Before the first heading is reached, the first entry is current. The line
  // sits below the heading's scroll-margin-top (viewer.css, 0.75rem), or a
  // heading just jumped to would land a few pixels short of it and lose the mark.
  // At the very bottom the last entry wins: short closing sections can never
  // scroll up to the line, and would otherwise never be marked at all.
  function refreshActive() {
    var line = measureHeader() + 24;
    var current = entries[0].id;
    for (var i = 0; i < entries.length; i++) {
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

  function scrollToId(id, smooth) {
    var target = document.getElementById(id);
    if (!target) { return false; }
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
    var a = e.target.closest ? e.target.closest("a[data-rd-toc-id]") : null;
    if (!a) { return; }
    e.preventDefault();
    go(a.getAttribute("data-rd-toc-id"));
  });

  // Opening the drawer moves focus into it: the nav sits after the header in
  // document order, so Tab from the button would otherwise skip past it. The
  // wide sidebar is already in the flow and leaves focus where it is.
  toggle.addEventListener("click", function () {
    var open = root.getAttribute("data-toc") !== "open";
    setOpen(open, true);
    if (open && isNarrow()) {
      var first = (active && links[active]) || nav.querySelector("a[data-rd-toc-id]");
      if (first) { first.focus(); }
    }
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
    go: go,
    setOpen: setOpen,
    isNarrow: isNarrow,
    applyLayout: applyLayout,
    refreshActive: refreshActive
  };
}
