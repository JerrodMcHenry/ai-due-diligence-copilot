import { notFound } from "next/navigation";

import DesignSystemShowcase from "./DesignSystemShowcase";

// Design System V2 (Phase 10.4), Part 11: a lightweight, dev-only
// verification surface -- not Storybook (the project has none, and Part
// 11 says not to introduce one solely for this phase), just a plain
// route that renders representative states of every new primitive so
// light/dark and desktop/mobile can be checked without touching any
// production page.
//
// Gated out of production builds entirely: NODE_ENV is "production" for
// `next build`/`next start` and "development" for `next dev`, so this
// route 404s in any real deployment regardless of whether a link to it
// ever existed -- it isn't an auth boundary because it doesn't need one
// (no data, no auth calls, nothing sensitive rendered; it's a static
// component gallery), but "reachable in prod at all" is exactly the
// "deployment complication" Part 11 asks to avoid, so this removes it
// outright rather than merely hiding it from navigation.
export default function DesignSystemPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return <DesignSystemShowcase />;
}
