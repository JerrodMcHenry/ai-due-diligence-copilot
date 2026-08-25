import type { SavedStartupEntry, SavedStartupStatus } from "@/types";

import { apiFetch } from "./client";

// Saved Startups (Watchlist Phase 1): every call here requires a real
// Clerk session token (from useAuth().getToken() at the call site, same
// pattern as lib/api/analyze.ts's analyzeMultiSource()) -- these are the
// authenticated "me" endpoints, never a /users/{id}/... shape, so there
// is no user id for a caller to get wrong. A null/missing token is a
// caller bug (the UI should never render Save/Saved controls before
// Clerk has resolved sign-in state); apiFetch surfaces the resulting 401
// as a normal thrown Error, same as every other authenticated call.

export function getSavedStartups(
  token: string
): Promise<SavedStartupEntry[]> {
  return apiFetch<SavedStartupEntry[]>("/me/saved-startups", { token });
}

export function getSavedStartupStatus(
  startupId: number,
  token: string
): Promise<SavedStartupStatus> {
  return apiFetch<SavedStartupStatus>(`/me/saved-startups/${startupId}`, {
    token,
  });
}

export function saveStartup(
  startupId: number,
  token: string
): Promise<SavedStartupStatus> {
  return apiFetch<SavedStartupStatus>(`/me/saved-startups/${startupId}`, {
    method: "POST",
    token,
  });
}

export function unsaveStartup(
  startupId: number,
  token: string
): Promise<SavedStartupStatus> {
  return apiFetch<SavedStartupStatus>(`/me/saved-startups/${startupId}`, {
    method: "DELETE",
    token,
  });
}
