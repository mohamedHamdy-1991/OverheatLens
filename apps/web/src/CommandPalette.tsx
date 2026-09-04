import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

interface Command {
  label: string;
  hint: string;
  to: string;
}

const COMMANDS: Command[] = [
  { label: "Analyze a building", hint: "model × weather × standard", to: "/analyze" },
  { label: "Weather Lab", hint: "check an EPW", to: "/weather" },
  { label: "Comfort Lab", hint: "PMV · adaptive · UTCI", to: "/comfort" },
  { label: "Compare", hint: "weather · runs · mitigation", to: "/compare" },
  { label: "Run Archive", hint: "every experiment, reproducible", to: "/runs" },
  { label: "Scenario & Batch", hint: "matrices of EnergyPlus runs", to: "/scenarios" },
  { label: "Validation", hint: "the live evidence matrix", to: "/validation" },
  { label: "Archetype Atlas", hint: "research model dossiers", to: "/atlas" },
  { label: "Mitigation Lab", hint: "Harehills parametric evidence", to: "/mitigation" },
  { label: "Methods", hint: "how the science is implemented", to: "/methods" },
  { label: "Docs", hint: "quick start & guides", to: "/docs" },
  { label: "About OverheatLens", hint: "project & licence", to: "/about" },
  { label: "Overview", hint: "laboratory desktop", to: "/" },
];

/* RULE 13: global ⌘K / Ctrl+K command search. Arrow keys + Enter, Escape closes. */
export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery("");
        setActive(0);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COMMANDS;
    return COMMANDS.filter(
      (c) => c.label.toLowerCase().includes(q) || c.hint.toLowerCase().includes(q),
    );
  }, [query]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  if (!open) return null;

  const go = (to: string) => {
    setOpen(false);
    navigate(to);
  };

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        background: "rgba(23,33,38,0.35)",
        display: "flex", justifyContent: "center", alignItems: "flex-start",
        paddingTop: "12vh",
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command search"
        style={{
          width: "min(560px, calc(100vw - 32px))",
          background: "var(--nb-surface)",
          border: "var(--nb-border-3)",
          boxShadow: "var(--nb-shadow-lg)",
          borderRadius: "var(--nb-radius-md)",
          overflow: "hidden",
        }}
      >
        <input
          ref={inputRef}
          role="combobox"
          aria-expanded="true"
          aria-controls="cmd-list"
          aria-label="Search pages and actions"
          placeholder="Search pages and actions…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setActive(0); }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, results.length - 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
            else if (e.key === "Enter" && results[active]) { go(results[active].to); }
          }}
          style={{
            width: "100%", border: "none", outline: "none",
            padding: "14px 18px", font: "inherit", fontSize: 15.5,
            borderBottom: "var(--nb-border-2)",
            background: "var(--nb-surface)", color: "var(--nb-ink)",
          }}
        />
        <ul id="cmd-list" role="listbox" style={{ listStyle: "none", margin: 0, padding: "6px", maxHeight: 320, overflowY: "auto" }}>
          {results.map((c, i) => (
            <li key={c.to + c.label} role="option" aria-selected={i === active}>
              <button
                onClick={() => go(c.to)}
                onMouseEnter={() => setActive(i)}
                style={{
                  display: "flex", width: "100%", alignItems: "baseline", gap: 12,
                  padding: "9px 12px", cursor: "pointer",
                  border: i === active ? "var(--nb-border-2)" : "2px solid transparent",
                  textAlign: "left",
                  background: i === active ? "var(--nb-yellow)" : "transparent",
                  color: "var(--nb-ink)",
                  font: "inherit", fontSize: 14,
                  fontWeight: i === active ? 800 : 400,
                }}
              >
                {c.label}
                <span style={{
                  marginLeft: "auto", fontFamily: "var(--font-mono)",
                  fontSize: 11, color: "var(--muted-ink)",
                }}>{c.hint}</span>
              </button>
            </li>
          ))}
          {results.length === 0 && (
            <li style={{ padding: "14px 16px", color: "var(--muted-ink)", fontSize: 13.5 }}>
              Nothing matches “{query}”. Try a page name such as “weather”.
            </li>
          )}
        </ul>
        <div style={{
          borderTop: "1px solid var(--line)", padding: "7px 14px",
          fontFamily: "var(--font-mono)", fontSize: 10.5, color: "var(--muted-ink)",
          display: "flex", gap: 14,
        }}>
          <span>↑↓ choose</span><span>↵ open</span><span>esc close</span>
        </div>
      </div>
    </div>
  );
}
