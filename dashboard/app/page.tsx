import CompetitionTeaser from "@/components/home/CompetitionTeaser";
import EntryPaths from "@/components/home/EntryPaths";
import Hero from "@/components/home/Hero";
import IdeaJourney from "@/components/home/IdeaJourney";
import ScenarioExamples from "@/components/home/ScenarioExamples";
import TrustSection from "@/components/home/TrustSection";
import VisualPayoff from "@/components/home/VisualPayoff";

// Phase 10.5 -- Consumer Home V2. Replaces the old "platform average SPS"
// analytics dashboard (identical for every visitor, signed-in or not --
// see Phase 10.2's own audit finding) with a homepage built around the
// product's actual acquisition loop: IDEA -> MODEL -> ITERATE. Public,
// unauthenticated (Part 14) -- the ONLY auth boundary on this page is the
// existing one every other protected route already has, enforced when
// Hero's "Build My Startup" navigates to /idea-lab/new, not by anything
// here.
//
// A Server Component (the old Home was "use client" for its own
// client-side analytics fetch -- Hero is the only piece here that needs
// the client, and it's marked "use client" itself).
//
// Phase 15 -- Founder Beta Surface Audit, Part 14/19: ExplorePreview
// ("See how real startups stack up") removed from this page -- not
// deleted (components/home/ExplorePreview.tsx is untouched and still
// exports a working component). The live discovery dataset it rendered
// currently has exactly one row, whose own company_name is literally
// "Unknown" -- rendering that on the homepage is a straightforward
// "empty product surface" failure (Part 22), not a acceptable "small
// but real" example. Bring it back once the dataset backing GET
// /top-startups is credible again.
//
// force-dynamic kept (harmless with no dynamic content left on this
// page today; a deliberate precaution against silently re-baking stale
// data into a build-time-prerendered page if ExplorePreview, or
// anything else data-driven, is ever added back here without someone
// re-checking this line).
export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <div className="space-y-24 pb-16 sm:space-y-28">
      <div>
        <Hero />
        <VisualPayoff />
      </div>

      <EntryPaths />

      <IdeaJourney />

      <ScenarioExamples />

      <CompetitionTeaser />

      <TrustSection />
    </div>
  );
}
