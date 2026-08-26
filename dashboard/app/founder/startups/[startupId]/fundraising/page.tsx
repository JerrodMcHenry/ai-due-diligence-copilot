import { auth } from "@clerk/nextjs/server";

import FundraisingReadinessView from "./FundraisingReadinessView";

type Props = {
  params: Promise<{ startupId: string }>;
};

// Phase 8 -- Fundraising Readiness V1. Same server-wrapper auth pattern
// as app/founder/startups/[startupId]/page.tsx: auth.protect() is the
// real, resource-based, server-side gate. The REAL authorization for
// this specific startup's fundraising preparation is enforced
// independently on the backend by RequireStartupMember when
// FundraisingReadinessView calls GET /founder/startups/{startupId}/
// fundraising -- this page-level check alone cannot and does not decide
// who may see which startup's private readiness assessment.
export default async function FundraisingReadinessPage({ params }: Props) {
  await auth.protect();

  const { startupId } = await params;

  return <FundraisingReadinessView startupId={Number(startupId)} />;
}
