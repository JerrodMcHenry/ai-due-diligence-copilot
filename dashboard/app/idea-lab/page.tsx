import { auth } from "@clerk/nextjs/server";

import IdeaLabDashboard from "./IdeaLabDashboard";

// Idea Lab / Venture Simulator V1: same page-level protection pattern as
// app/analyze/page.tsx and app/saved/page.tsx -- auth.protect() is the
// real, resource-based check. Modeled ventures are private, persistent
// per-user workspaces (Part 16), unlike Discovery/Rankings/Compare, which
// stay fully public.
export default async function IdeaLabPage() {
  await auth.protect();

  return <IdeaLabDashboard />;
}
