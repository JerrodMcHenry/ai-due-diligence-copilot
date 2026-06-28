type StartupHeroProps = {
  companyName: string;
  industry: string | null;
  stage: string | null;
  businessModel: string | null;
  recommendation: string | null;
};

export default function StartupHero({
  companyName,
  industry,
  stage,
  businessModel,
  recommendation,
}: StartupHeroProps) {
  return (
    <section className="rounded-xl bg-gray-900 p-8 border border-gray-800">
      <div>
        <h1 className="text-5xl font-bold">{companyName}</h1>

        <p className="mt-4 text-gray-400">
          {industry ?? "Unknown Industry"} • {stage ?? "Unknown Stage"} •{" "}
          {businessModel ?? "Unknown Model"}
        </p>
      </div>

      <div className="mt-6 rounded-lg bg-gray-950 p-4 border border-gray-800">
        <p className="text-gray-400 mb-2">Recommendation</p>
        <p className="text-gray-200 leading-7">
          {recommendation ?? "No recommendation available."}
        </p>
      </div>
    </section>
  );
}
