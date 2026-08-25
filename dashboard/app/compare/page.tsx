import { Suspense } from "react";

import PageHeader from "@/components/layout/PageHeader";

import CompareView from "./CompareView";

// Compare Startups V1: public, no auth gate -- comparing canonical
// intelligence is the same kind of public intelligence as Discovery/
// Rankings/Startup Profile (Part 15). CompareView reads comparison state
// from the URL via useSearchParams(), a Client Component hook -- same
// Suspense-boundary reasoning as app/search/page.tsx.
export default function ComparePage() {
  return (
    <>
      <PageHeader
        title="Compare Startups"
        subtitle="See how SIE's canonical intelligence differs across startups, pillar by pillar."
      />

      <Suspense
        fallback={
          <div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />
        }
      >
        <CompareView />
      </Suspense>
    </>
  );
}
