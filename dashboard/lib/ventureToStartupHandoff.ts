// Phase 10.10 -- Founder Journey Integration, Part 8. The idea -> real
// startup bridge, using the EXACT SAME mechanism lib/homepageIdeaHandoff.ts
// already established for "a visitor types text in one place, it should
// be waiting for them in a different EXISTING form" -- a same-tab
// sessionStorage stash, read-and-cleared once. Nothing is created here:
// no venture-to-startup conversion, no canonical startup, no evidence.
// This only carries the founder's OWN already-written venture description
// into /analyze's existing "Additional Company Information" field as a
// convenience starting point they can edit or delete -- the same honest
// "founder's own words, offered back to them" contract
// homepageIdeaHandoff.ts already uses, applied one step later in the
// journey.
//
// Investigation note (Part 8): a modeled venture's assumptions
// (VentureAssumptions) are never transferred here, and never will be by
// this mechanism -- only the free-text `description` field, because
// that's the one piece of the venture that is unambiguously "the
// founder's own words" rather than a modeled assumption VPS scored. VPS
// categories, validation observations, and every other modeled field
// stay exactly where they are; POST /analyze's own canonical pipeline
// re-derives everything about the resulting Startup Profile from
// scratch, same as it does for any other visitor.
const VENTURE_TO_STARTUP_STORAGE_KEY = "sie:venture-description-handoff";

export function stashVentureDescriptionForAnalyze(description: string): void {
  try {
    sessionStorage.setItem(VENTURE_TO_STARTUP_STORAGE_KEY, description);
  } catch {
    // Private browsing / storage disabled: the description just won't be
    // pre-filled on /analyze. Not worth blocking navigation over.
  }
}

export function consumeVentureDescriptionForAnalyze(): string | null {
  try {
    const value = sessionStorage.getItem(VENTURE_TO_STARTUP_STORAGE_KEY);

    if (value) {
      sessionStorage.removeItem(VENTURE_TO_STARTUP_STORAGE_KEY);
    }

    return value;
  } catch {
    return null;
  }
}
