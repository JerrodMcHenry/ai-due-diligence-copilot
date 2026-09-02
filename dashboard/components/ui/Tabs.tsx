"use client";

// Phase 21B -- Fundraising Simulator V1, Part 25. No shared tab primitive
// existed before this (confirmed by investigation: no role="tab" anywhere
// in the app) -- needed to split Founder Tools' existing "Simulate"
// surface into [ Venture ] [ Fundraising ] without inventing a bespoke,
// one-off switcher. Minimal, accessible (role="tablist"/"tab"/"tabpanel",
// full keyboard operability via native button focus order), matching
// Button/Badge's own restrained styling rather than a heavier pattern.
type TabsProps = {
  tabs: { id: string; label: string }[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
};

export default function Tabs({ tabs, activeId, onChange, className = "" }: TabsProps) {
  return (
    <div role="tablist" className={["inline-flex gap-1 rounded-xl border border-border bg-surface-muted p-1", className].join(" ")}>
      {tabs.map((tab) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={active}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => onChange(tab.id)}
            className={[
              "min-h-9 rounded-lg px-4 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              active ? "bg-surface text-text-primary shadow-sm" : "text-text-muted hover:text-text-secondary",
            ].join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({ id, activeId, children }: { id: string; activeId: string; children: React.ReactNode }) {
  if (id !== activeId) return null;
  return (
    <div role="tabpanel" id={`tabpanel-${id}`} aria-labelledby={`tab-${id}`}>
      {children}
    </div>
  );
}
