import TopNav from "./TopNav";
import MobileTabBar from "./MobileTabBar";

type AppShellProps = {
  children: React.ReactNode;
};

// Phase 10.3 -- Shell & Navigation Reset. Replaces the previous fixed-
// width desktop sidebar (Sidebar.tsx, now removed) with a sticky top
// navigation bar (TopNav) and a purpose-built mobile bottom tab bar
// (MobileTabBar) -- see both components' own docstrings for the full
// design record. No route/auth logic lives here or ever did; this file
// is pure layout chrome.
//
// The old shell permanently reserved 288px (`lg:pl-72`) for the sidebar
// on every single page, including narrow, focused ones. That offset is
// gone entirely -- content now has the full viewport width to work with,
// and any page that wants a narrower reading column constrains itself
// (e.g. NewVentureForm's own `max-w-2xl`), rather than the shell forcing
// one width on everything. max-w-[1600px] is kept as the outer ceiling
// (unchanged from before) so wide data pages (Rankings, Discovery,
// Compare) render exactly as they did previously -- this phase changes
// the chrome around pages, not their own internal layouts (Part 4/9).
//
// Also fixes a pre-existing bug while touching this file anyway:
// previously hardcoded `bg-slate-950 text-white` ignored the light/dark
// theme entirely (every page's own content already read the real
// --background/--foreground tokens; only this outer shell didn't) --
// now uses the same token-driven classes as everything else, which is
// what actually makes light mode work correctly at the shell level for
// the first time.
export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />

      <main className="min-h-screen pb-24 md:pb-0">
        <div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
          {children}
        </div>
      </main>

      <MobileTabBar />
    </div>
  );
}
