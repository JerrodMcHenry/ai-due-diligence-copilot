import Link from "next/link";

import { getSPSHistory, getStartupProfile } from "@/lib/api";

import BaseCard from "@/components/ui/BaseCard";
import StartupHeroV2 from "@/components/startup/StartupHeroV2";
import SPSHistory from "@/components/startup/SPSHistory";
import IntelligencePillars from "@/components/startup/IntelligencePillars";

import type { SPSHistoryPoint, StartupProfileResponse } from "@/types";

type Props = {
  params: Promise<{
    id: string;
  }>;
};

function isNotFoundError(error: unknown): boolean {
  return error instanceof Error && /\(404\)/.test(error.message);
}

// Rankings/Search build this route's href with
// encodeURIComponent(companyName) (required — company names can contain
// spaces/&/etc. that aren't valid unencoded in a URL). getStartupProfile /
// getSPSHistory also encode when constructing the backend request (required
// — that's the actual outgoing HTTP call). Decoding exactly once here,
// where the raw path segment enters application code, is what keeps that
// pair of encodes to a net single encoding pass end-to-end; skipping this
// step is what previously left the API call encoding an already-encoded
// value (e.g. "Ramp%20Business%20Corporation" -> "Ramp%2520..."), which the
// backend could never match against a stored company_name. Safe for names
// that were never encoded to begin with — decodeURIComponent on a string
// with no percent-sequences is a no-op — and guarded against a malformed
// sequence rather than letting the page crash on one.
function decodeCompanyNameParam(id: string): string {
  try {
    return decodeURIComponent(id);
  } catch {
    return id;
  }
}

async function loadStartupProfile(
  id: string
): Promise<StartupProfileResponse | null> {
  try {
    return await getStartupProfile(id);
  } catch (error) {
    if (isNotFoundError(error)) {
      return null;
    }

    throw error;
  }
}

// SPS History is supplementary to the profile, not core to it — any
// failure here (network hiccup, etc.) degrades to an empty history rather
// than breaking the page.
async function loadSPSHistory(id: string): Promise<SPSHistoryPoint[]> {
  try {
    return await getSPSHistory(id);
  } catch {
    return [];
  }
}

export default async function StartupProfilePage({ params }: Props) {
  const { id } = await params;
  const companyName = decodeCompanyNameParam(id);

  // MVP hardening: these two requests don't depend on each other (both
  // only need companyName), so run them in parallel rather than paying
  // two sequential network round trips for every profile load. The one
  // trade-off is that a "not found" company also fires (and discards) an
  // SPS-history request it didn't need -- a small, one-time cost on a
  // rare path, in exchange for materially faster loads on the common one.
  const [startup, history] = await Promise.all([
    loadStartupProfile(companyName),
    loadSPSHistory(companyName),
  ]);

  if (!startup) {
    return (
      <BaseCard className="p-10 text-center">
        <h1 className="text-2xl font-bold text-text-primary">
          Startup not found
        </h1>

        <p className="mt-3 text-text-secondary">
          No startup profile was found for &ldquo;{companyName}&rdquo;. It may
          need to be analyzed first, or the name may not match exactly.
        </p>

        <Link
          href="/search"
          className="mt-6 inline-flex text-sm font-semibold text-primary hover:text-primary-hover"
        >
          Back to search →
        </Link>
      </BaseCard>
    );
  }

  const methodology = startup.methodology;

  return (
    <div className="space-y-8">
      <StartupHeroV2
        methodology={methodology}
        createdAt={startup.created_at}
        startupId={startup.startup_id}
      />

      <SPSHistory history={history} />

      <IntelligencePillars methodology={methodology} />
    </div>
  );
}
