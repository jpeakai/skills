// The viewer bundle's entry. md2html.py inlines it after the #rd-config block
// and the classic helper scripts, at the end of <body>, so the shell is parsed.
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";

import "@/styles.css";
import "./viewer.css";
import { Header } from "./Header";
import { currentTheme, readConfig, Viewer } from "./renderer";

const cfg = readConfig();
const viewer = new Viewer(cfg);
const mount = document.getElementById("rd-header-root");
const article = document.getElementById("rd-article");
if (!mount || !article) throw new Error("richdocs: the shell lacks #rd-header-root or #rd-article");

// Synchronously, so #rd-toc-toggle exists before rdInitToc looks for it.
flushSync(() =>
  createRoot(mount).render(
    <Header
      title={cfg.title ?? document.title}
      source={cfg.source}
      buildId={cfg.buildId}
      initialTheme={currentTheme()}
      onThemeChange={() => viewer.retheme()}
    />,
  ),
);

void viewer.boot(article);

// Any picture in the article opens full screen on click (ADR-024). Plotly and
// deck.gl have their own zoom; a graph opens from its own button. Delegated
// from document, so it survives re-renders.
rdInitZoom({
  pictures: "#rd-article img, #rd-article svg",
  exclude: ".rd-plotly, .rd-deckgl, .rd-cytoscape",
});
