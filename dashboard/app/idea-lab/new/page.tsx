import { auth } from "@clerk/nextjs/server";

import NewVentureForm from "./NewVentureForm";

export default async function NewVenturePage() {
  await auth.protect();

  return <NewVentureForm />;
}
