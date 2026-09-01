"use client";

import { UserButton } from "@clerk/nextjs";

// Phase 10.3 -- Shell & Navigation Reset, Part 3. Restrained, consumer-
// facing personal navigation -- NOT the old 8-item sidebar recreated
// inside a dropdown. Route/backend concepts are completely unchanged --
// this is presentation language only:
//
//   My Ideas -> /idea-lab   (was "Idea Lab")
//   My Startup -> /founder  (was "Founder Workspace")
//
// Phase 15 -- Founder Beta Surface Audit, Part 11/15/21: "Watchlist"
// (/saved) and "Investor intelligence" (/investor) removed from this
// menu -- not deleted (Part 16). Both are watchlist/discovery surfaces
// over the SAME cold-start-affected canonical startup population
// PRIMARY_NAVIGATION's own "Explore" removal addresses (see
// TopNav.tsx) -- there is currently nothing meaningful for a founder to
// watch or for an investor to browse. Both routes remain fully
// functional at their existing URLs for any user who already knows to
// go there (auth/authorization completely unchanged); this is a
// visibility decision only. Revert alongside Explore once the dataset
// is credible.
//
// Shown unconditionally to every signed-in user, same as the old
// Sidebar's own behavior -- each destination's own page already handles
// "you have nothing here yet" honestly (FounderHome's existing empty
// state), so this menu doesn't need to fetch anything to decide what to
// show.
//
// Phase 10.3 follow-up fix: this originally wrapped Clerk's own
// <UserButton /> (which renders its own <button>) inside a second,
// hand-rolled <button> used to open a custom popover -- invalid nested
// interactive markup that also silently ate every click before Clerk's
// own trigger ever saw it, so its native "Manage account" / "Sign out"
// dialog could never open. There was no way to sign out. Fixed by
// dropping the custom trigger/popover entirely and using Clerk's own
// supported extension point instead -- <UserButton.MenuItems> +
// <UserButton.Link> add these four destinations directly into Clerk's
// own account menu, alongside its built-in Manage account / Sign out
// actions, which is exactly what Part 3 asked for ("Use existing Clerk
// account functionality, not a custom auth system") and what "restrained,
// not another giant dropdown" means in practice: one native menu, not two
// stacked ones.
const ICON_CLASS = "size-4";

function IdeaIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className={ICON_CLASS}>
      <path d="M9 18h6M10 21h4M8 14a5 5 0 1 1 8 0c-.9.9-1.4 1.6-1.4 2.5h-5.2c0-.9-.5-1.6-1.4-2.5Z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function StartupIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className={ICON_CLASS}>
      <path d="M12 3l2.4 5.3 5.6.6-4.2 3.9 1.2 5.6L12 15.8l-5 2.6 1.2-5.6-4.2-3.9 5.6-.6L12 3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function LearnIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className={ICON_CLASS}>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      <path d="M4 20.5V5.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

// Phase 10.9 -- Founder Playbooks V1, Part 11: no new TopNav item --
// "Learn" is discovered here, the same restrained account-menu path
// every other personal/non-primary destination already uses, plus
// contextual links from inside the product itself (see
// dashboard/lib/playbooks/resourceMap.ts's own callers). /playbooks
// itself is public (no auth), so this link works identically for every
// signed-in user regardless of what they've built so far.
export default function PersonalMenu() {
  return (
    <UserButton appearance={{ elements: { userButtonAvatarBox: "size-9" } }}>
      <UserButton.MenuItems>
        <UserButton.Link label="My Ideas" href="/idea-lab" labelIcon={<IdeaIcon />} />
        <UserButton.Link label="My Startup" href="/founder" labelIcon={<StartupIcon />} />
        <UserButton.Link label="Learn" href="/playbooks" labelIcon={<LearnIcon />} />
      </UserButton.MenuItems>
    </UserButton>
  );
}
