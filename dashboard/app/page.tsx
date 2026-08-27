import { Suspense } from "react";

import AnalyzeCallout from "@/components/home/AnalyzeCallout";
import CompetitionTeaser from "@/components/home/CompetitionTeaser";
import ExplorePreview from "@/components/home/ExplorePreview";
import Hero from "@/components/home/Hero";
import IdeaJourney from "@/components/home/IdeaJourney";
import ScenarioExamples from "@/components/home/ScenarioExamples";
import ThreePaths from "@/components/home/ThreePaths";
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
// the client, and it's marked "use client" itself; everything else can
// render on the server, including ExplorePreview's own data fetch,
// matching the same convention /rankings and /search already use).
//
// force-dynamic: without this, Next.js prerenders "/" once at BUILD time
// (confirmed via a real production build -- it was marked "○ Static"),
// which would bake ExplorePreview's real startup list into the page
// permanently until the next deploy. The old Home fetched its own data
// client-side on every visit and never had this problem; this is the
// server-rendered equivalent of that same freshness guarantee, not a new
// behavior.
export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <div className="space-y-24 pb-16 sm:space-y-28">
      <div>
        <Hero />
        <VisualPayoff />
      </div>

      <ThreePaths />

      <IdeaJourney />

      <ScenarioExamples />

      <AnalyzeCallout />

      <Suspense fallback={null}>
        <ExplorePreview />
      </Suspense>

      <CompetitionTeaser />

      <TrustSection />
    </div>
  );
}
