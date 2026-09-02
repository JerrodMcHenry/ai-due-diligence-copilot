import { auth } from "@clerk/nextjs/server";

import AdminAnalyticsView from "./AdminAnalyticsView";

// Phase 28 -- Product Analytics & Growth Measurement V1, Part 13. The
// smallest safe internal reporting surface, not a new RBAC system:
// auth.protect() here only proves "signed in" (identical to every other
// protected page in this app, e.g. /idea-lab/[id]/page.tsx) -- REAL
// admin authorization happens server-side, in the FastAPI backend, via
// the existing RequireAdmin dependency (app/auth.py's ADMIN_USER_IDS
// allowlist, unchanged since Phase 7.1A). A signed-in non-admin who
// navigates here sees AdminAnalyticsView's own "Access denied" state
// (a real 403 from the backend), never real numbers -- there is no
// client-side admin check anywhere in this file standing in for that.
export default async function AdminAnalyticsPage() {
  await auth.protect();

  return <AdminAnalyticsView />;
}
