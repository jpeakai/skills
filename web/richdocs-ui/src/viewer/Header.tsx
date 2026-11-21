import { ListTree, Moon, Sun } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { Mode } from "@/theme/tokens";

export interface HeaderProps {
  title: string;
  source: string;
  buildId: string;
  initialTheme: Mode;
  onThemeChange: (mode: Mode) => void;
}

// The page chrome. Two ids are a contract with the classic helpers:
// viewer-toc.js finds #rd-toc-toggle, unhides it when the document has enough
// headings and owns its aria-expanded state, and measures header.rd-header for
// the sticky offset. The props below never change after mount, so React never
// overwrites what viewer-toc.js sets.
export function Header({ title, source, buildId, initialTheme, onThemeChange }: HeaderProps) {
  const [theme, setTheme] = useState<Mode>(initialTheme);

  const toggleTheme = () => {
    const next: Mode = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("richdocs-theme", next);
    } catch {
      // Storage can be blocked; the flip still applies to this page view.
    }
    setTheme(next);
    onThemeChange(next);
  };

  return (
    <header className="rd-header sticky top-0 z-10 flex items-center gap-3 border-b bg-card px-4 py-2">
      <Button
        id="rd-toc-toggle"
        type="button"
        variant="outline"
        size="sm"
        aria-controls="rd-toc"
        aria-expanded="false"
        hidden
      >
        <ListTree aria-hidden="true" />
        contents
      </Button>
      <h1 id="rd-title" className="m-0 min-w-0 truncate font-heading text-base font-semibold">
        {title}
      </h1>
      <span className="rd-meta hidden font-mono text-xs text-muted-foreground sm:inline">{source}</span>
      <span className="rd-meta hidden font-mono text-xs text-muted-foreground sm:inline">build {buildId}</span>
      <Button
        id="rd-theme-toggle"
        type="button"
        variant="outline"
        size="icon"
        className="ml-auto size-8"
        aria-label="Toggle theme"
        onClick={toggleTheme}
      >
        {theme === "dark" ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
      </Button>
    </header>
  );
}
