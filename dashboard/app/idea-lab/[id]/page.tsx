import { auth } from "@clerk/nextjs/server";

import VentureWorkspace from "./VentureWorkspace";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function VenturePage({ params }: Props) {
  await auth.protect();

  const { id } = await params;
  const ventureId = Number(id);

  return <VentureWorkspace ventureId={ventureId} />;
}
