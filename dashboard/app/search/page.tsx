import { Suspense } from "react";
import Link from "next/link";

import PageHeader from "@/components/layout/PageHeader";

import DiscoveryView from "./DiscoveryView";

// Startup Discovery V1: /search redesigned in place from a basic
// company-name lookup into the primary startup-discovery experience --
// same route, no new /discover page (per the product decision to keep
// Search and Rankings as the only two browse routes). DiscoveryView reads
// filter state from the URL via useSearchParams(), a Client Component
// hook -- Next's own docs recommend wrapping the component that calls it
// in <Suspense>, so a route that could otherwise be static isn't forced
// fully client-rendered up to the root (same reasoning as the /analyze,
// /saved server-wrapper split, for a different underlying reason: no auth
// gate here -- discovery is public).
export default function SearchPage() {
  return (
    <>
      <PageHeader
        title="Discover Startups"
        subtitle="Browse the canonical Startup Intelligence Engine universe -- filter by industry, stage, and Startup Power Score to find companies worth a closer look."
        action={
          <Link
            href="/rankings"
            className="text-sm font-semibold text-primary hover:text-primary-hover"
          >
            View rankings →
          </Link>
        }
      />

      <Suspense
        fallback={
          <div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />
        }
      >
        <DiscoveryView />
      </Suspense>
    </>
  );
}
