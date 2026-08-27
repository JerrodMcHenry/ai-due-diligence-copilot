"use client";

import { UserButton } from "@clerk/nextjs";

// Phase 10.3 -- Shell & Navigation Reset, Part 3. Restrained, consumer-
// facing personal navigation -- NOT the old 8-item sidebar recreated
// inside a dropdown. Exactly four destinations, each with the friendlier
// label Part 3 specifies (route/backend concepts are completely
// unchanged -- this is presentation language only):
//
//   My Ideas             -> /idea-lab   (was "Idea Lab")
//   My Startup            -> /founder    (was "Founder Workspace")
//   Watchlist              -> /saved      (was "Saved Startups")
//   Investor intelligence  -> /investor   (was "Investor Workspace")
//
// Shown unconditionally to every signed-in user, same as the old
// Sidebar's own behavior -- each destination's own page already handles
// "you have nothing here yet" honestly (FounderHome/SavedStartupsView/
// InvestorWorkspaceView's existing empty states), so this menu doesn't
// need to fetch anything to decide what to show.
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

function WatchlistIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className={ICON_CLASS}>
      <path d="M6 4h12v17l-6-3.5L6 21V4Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
    </svg>
  );
}

function InvestorIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className={ICON_CLASS}>
      <path d="M4 20V10M11 20V4M18 20v-7" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export default function PersonalMenu() {
  return (
    <UserButton appearance={{ elements: { userButtonAvatarBox: "size-9" } }}>
      <UserButton.MenuItems>
        <UserButton.Link label="My Ideas" href="/idea-lab" labelIcon={<IdeaIcon />} />
        <UserButton.Link label="My Startup" href="/founder" labelIcon={<StartupIcon />} />
        <UserButton.Link label="Watchlist" href="/saved" labelIcon={<WatchlistIcon />} />
        <UserButton.Link label="Investor intelligence" href="/investor" labelIcon={<InvestorIcon />} />
      </UserButton.MenuItems>
    </UserButton>
  );
}
