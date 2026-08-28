import { auth } from "@clerk/nextjs/server";

import PitchDeckReviewView from "./PitchDeckReviewView";

type Props = {
  params: Promise<{ reviewId: string }>;
};

export default async function PitchDeckReviewPage({ params }: Props) {
  await auth.protect();

  const { reviewId } = await params;

  return <PitchDeckReviewView reviewId={Number(reviewId)} />;
}
