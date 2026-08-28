import { auth } from "@clerk/nextjs/server";

import PitchDeckCoachUpload from "./PitchDeckCoachUpload";

// Phase 10.8 -- Pitch Deck Coach V1. Same page-level auth pattern as
// app/analyze/page.tsx (Part 24: uploading/reviewing a private deck
// requires authentication). Covered by proxy.ts's existing
// "/analyze(.*)" route matcher -- no proxy.ts change needed.
export default async function PitchDeckCoachPage() {
  await auth.protect();

  return <PitchDeckCoachUpload />;
}
