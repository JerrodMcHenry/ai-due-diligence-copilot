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

  const startup = await loadStartupProfile(id);

  if (!startup) {
    return (
      <BaseCard className="p-10 text-center">
        <h1 className="text-2xl font-bold text-text-primary">
          Startup not found
        </h1>

        <p className="mt-3 text-text-secondary">
          No startup profile was found for &ldquo;{id}&rdquo;. It may need to
          be analyzed first, or the name may not match exactly.
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
  const history = await loadSPSHistory(id);

  return (
    <div className="space-y-8">
      <StartupHeroV2 methodology={methodology} createdAt={startup.created_at} />

      <SPSHistory history={history} />

      <IntelligencePillars methodology={methodology} />
    </div>
  );
}
