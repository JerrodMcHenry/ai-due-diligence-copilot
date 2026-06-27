type StartupProfilePageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function StartupProfilePage({
  params,
}: StartupProfilePageProps) {
  const { id } = await params;

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold">Startup Profile</h1>

      <p className="mt-4 text-gray-400">Startup ID: {id}</p>
    </div>
  );
}
