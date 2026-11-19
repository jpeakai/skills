// M0 placeholder entry: proves the bundle carries React, Tailwind and shadcn,
// and re-themes from injected variables. M1 replaces it with the viewer shell.
import { createRoot } from "react-dom/client";

import "@/styles.css";
import { Button } from "@/components/ui/button";

function ScaffoldProbe() {
  return (
    <div className="flex items-center gap-2 p-4">
      <Button>primary</Button>
      <Button variant="outline">outline</Button>
      <a className="text-link underline" href="#">link</a>
    </div>
  );
}

const mount = document.getElementById("rd-root");
if (mount) createRoot(mount).render(<ScaffoldProbe />);
