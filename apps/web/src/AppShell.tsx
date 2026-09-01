import { NavLink, Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { CommandPalette } from "./CommandPalette";
import "./shell.css";

/* One consistent drawn icon system: 1.5px strokes, 16px grid. */
const I = {
  overview: (
    <>
      <path d="M2.5 13.5v-5l5.5-4 5.5 4v5" />
      <path d="M5.5 13.5v-3.4h5v3.4" />
    </>
  ),
  analyze: <path d="M3 13.5 6.5 9l3 3L13 5.5l3 4" />,
  compare: (
    <>
      <rect x="2.5" y="4" width="4.5" height="9" rx="1" />
      <rect x="9" y="4" width="4.5" height="6" rx="1" />
      <path d="M2.5 15.5h11" />
    </>
  ),
  atlas: (
    <>
      <path d="M8.25 1.8c-3 2.6-3 11.8 0 12.4M7.75 1.8c3 2.6 3 11.8 0 12.4" />
      <circle cx="8" cy="8" r="6.2" />
    </>
  ),
  weather: (
    <>
      <circle cx="6" cy="6.5" r="2.6" />
      <path d="M6 1.2v1M6 10.8v1M.8 6.5h1M10.2 6.5h1M2.4 2.9l.7.7M9.9 10.4l-.7-.7M2.4 10.1l.7-.7M9.9 2.6l-.7.7" />
      <path d="M9.5 12.5h3.4a1.8 1.8 0 1 0-.4-3.6 2.6 2.6 0 0 0-5 .8" />
    </>
  ),
  comfort: (
    <>
      <path d="M5 9.2V2.6a1.3 1.3 0 0 1 2.6 0v6.6a2.8 2.8 0 1 1-2.6 0Z" />
      <path d="M6.3 7v3.4" />
    </>
  ),
  mitigation: <path d="M8 1.5 2.6 7.9h2.9l-1.6 6 5.4-6.4H6.4l1.6-6Z" />,
  validation: (
    <>
      <circle cx="8" cy="8" r="6.2" />
      <path d="m5.2 8.2 2 2 3.6-4" />
    </>
  ),
  methods: (
    <>
      <path d="M3 2.5h7l3 3v8H3z" />
      <path d="M5.2 7h5.6M5.2 9.5h5.6M5.2 12h3.4" />
    </>
  ),
  docs: (
    <>
      <path d="M4 1.8h6.5L13 4.3v9.9H4z" />
      <path d="M10.5 1.8v2.5H13" />
    </>
  ),
  about: (
    <>
      <circle cx="8" cy="8" r="6.2" />
      <path d="M8 7.2v3.6M8 4.9v.2" />
    </>
  ),
} as const;

function NavIcon({ d }: { d: ReactNode }) {
  return (
    <span className="nav-icon" aria-hidden="true">
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        {d}
      </svg>
    </span>
  );
}

/* Brand mark: dwelling outline + lens circle + thermal contours (plan §6.6). */
export function BrandMark({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M5 27V13l11-8.5L27 13v14" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" />
      <circle cx="16" cy="19" r="7" stroke="#182b42" strokeWidth="1.6" fill="#fdf4ea" />
      <path d="M12.2 21.5c1.3-1 2-2.2 3.8-2.2s2.5 1.2 3.8 2.2M11.5 18.6c1.5-1.2 2.5-2.6 4.5-2.6s3 1.4 4.5 2.6"
        stroke="#ed7d2a" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

const NAV: { group: string; items: { to: string; label: string; icon: ReactNode; end?: boolean }[] }[] = [
  {
    group: "Overview",
    items: [{ to: "/", label: "Overview", icon: I.overview, end: true }],
  },
  {
    group: "Assess",
    items: [
      { to: "/analyze", label: "Analyze", icon: I.analyze },
      { to: "/compare", label: "Compare", icon: I.compare },
      { to: "/atlas", label: "Archetype Atlas", icon: I.atlas },
    ],
  },
  {
    group: "Labs",
    items: [
      { to: "/weather", label: "Weather Lab", icon: I.weather },
      { to: "/comfort", label: "Comfort Lab", icon: I.comfort },
      { to: "/mitigation", label: "Mitigation Lab", icon: I.mitigation },
    ],
  },
  {
    group: "Trust",
    items: [
      { to: "/validation", label: "Validation", icon: I.validation },
      { to: "/methods", label: "Methods", icon: I.methods },
    ],
  },
];

const ROUTE_TITLES: Record<string, string> = {
  "/": "Overview",
  "/analyze": "Analyze",
  "/compare": "Compare",
  "/atlas": "Archetype Atlas",
  "/weather": "Weather Lab",
  "/comfort": "Comfort Lab",
  "/mitigation": "Mitigation Lab",
  "/validation": "Validation",
  "/methods": "Methods",
  "/docs": "Docs",
  "/about": "About & Licence",
};

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);

  const title = ROUTE_TITLES[loc.pathname] ?? "OverheatLens";

  return (
    <div className="page-shell">
      <aside className={"sidebar" + (open ? " open" : "")}>
        <Link to="/" className="brand" aria-label="OverheatLens home" onClick={() => setOpen(false)}>
          <span className="logo-mark"><BrandMark /></span>
          <span className="brand-copy">
            <strong>OVERHEATLENS</strong>
            <span>overheating evidence hub</span>
          </span>
        </Link>
        {NAV.map((g) => (
          <nav className="nav-block" key={g.group} aria-label={g.group}>
            <div className="nav-group-label">{g.group}</div>
            {g.items.map((it) => (
              <NavLink
                key={it.to}
                to={it.to}
                title={it.label}
                end={it.end}
                className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
              >
                <NavIcon d={it.icon} />
                <span className="nav-label-text">{it.label}</span>
              </NavLink>
            ))}
          </nav>
        ))}
        <div className="nav-spacer" />
        <nav className="nav-block" aria-label="Information">
          <div className="nav-group-label">Information</div>
          {[
            { to: "/docs", label: "Docs", icon: I.docs },
            { to: "/about", label: "About & Licence", icon: I.about },
          ].map((it) => (
            <NavLink key={it.to} to={it.to} title={it.label}
              className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
              <NavIcon d={it.icon} />
              <span className="nav-label-text">{it.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="guide-card">
          <strong>Get started</strong>
          Load an EPW, check its quality, then analyze a dwelling against a versioned
          overheating standard.
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="welcome">
            <small>Hello, researcher</small>
            <strong>OverheatLens workspace</strong>
          </div>
          <span className="topbar-spacer" />
          <span className="topbar-crumb">{title}</span>
          <button
            className="menu-btn"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor"
              strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
              <path d="M2 4.5h14M2 9h14M2 13.5h14" />
            </svg>
          </button>
          <button className="kbd" style={{ cursor: "pointer" }}
            onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
            aria-label="Open command search">⌘K</button>
        </header>
        {open && (
          <button
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            style={{
              position: "fixed", inset: 0, zIndex: 80, background: "rgba(21,38,58,0.3)",
              border: "none", cursor: "pointer",
            }}
          />
        )}
        <div className="content">{children}</div>
        <footer className="footer">
          <div>
            <strong>OverheatLens v0.6.0-dev — research software, not a compliance certificate.</strong>
            <br />
            Runs locally on your machine. Real weather files stay on this device and are
            never uploaded anywhere.
          </div>
          <div>
            <strong>Mohamed Hamdy Mohamed Ali</strong>
            <br />
            Leeds Sustainability Institute, Leeds Beckett University
          </div>
        </footer>
      </main>
      <CommandPalette />
    </div>
  );
}
