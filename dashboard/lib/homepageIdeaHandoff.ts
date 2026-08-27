// Phase 10.5 -- Consumer Home V2, Part 3. The smallest clean handoff for
// "a signed-out visitor types an idea on Home, then arrives at the
// EXISTING Idea Lab creation flow with it intact" -- not a second
// venture-creation pipeline, just a client-side stash of the raw text the
// visitor already typed.
//
// Why sessionStorage and not a query param: /idea-lab/new is protected by
// BOTH proxy.ts's clerkMiddleware AND its own server-side auth.protect()
// (see that page's own comment) -- a signed-out visitor's navigation
// there gets redirected to the SAME-ORIGIN /sign-in?redirect_url=... page
// (Clerk's own <SignIn/>, not an external hosted domain -- see
// app/sign-in/[[...sign-in]]/page.tsx), and Clerk's own redirect_url
// mechanism already returns the visitor to /idea-lab/new after signing
// in. sessionStorage survives that whole round trip for free (same tab,
// same origin, no custom auth code needed) and keeps the idea text out of
// the URL entirely.
//
// Nothing is created here -- this only stashes raw text the visitor typed
// themselves. No venture record, no API call. NewVentureForm.tsx reads
// and immediately clears this key on mount; the existing "describe ->
// structure -> review -> explicit Create Venture click" flow downstream
// is completely unchanged.
const HOMEPAGE_IDEA_STORAGE_KEY = "sie:homepage-idea";

export function stashHomepageIdea(ideaText: string): void {
  try {
    sessionStorage.setItem(HOMEPAGE_IDEA_STORAGE_KEY, ideaText);
  } catch {
    // Private browsing / storage disabled: the visitor's idea just won't
    // be pre-filled on the next page. Not worth failing navigation over.
  }
}

// Read-and-clear in one step -- a stashed idea is meant to be consumed
// exactly once, the first time NewVentureForm mounts after it was set,
// not to silently reappear in some later, unrelated new-venture session.
export function consumeHomepageIdea(): string | null {
  try {
    const value = sessionStorage.getItem(HOMEPAGE_IDEA_STORAGE_KEY);

    if (value) {
      sessionStorage.removeItem(HOMEPAGE_IDEA_STORAGE_KEY);
    }

    return value;
  } catch {
    return null;
  }
}
