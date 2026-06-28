type AnalysisSectionProps = {
  title: string;
  content: string | Record<string, unknown> | null;
};

export default function AnalysisSection({
  title,
  content,
}: AnalysisSectionProps) {
  if (!content) return null;

  return (
    <section className="mt-10 rounded-xl bg-gray-900 p-6">
      <h2 className="text-2xl font-bold mb-4">{title}</h2>

      {typeof content === "string" ? (
        <p className="text-gray-300 whitespace-pre-line leading-8">{content}</p>
      ) : (
        <div className="space-y-4">
          {Object.entries(content).map(([key, value]) => (
            <div key={key}>
              <h3 className="font-semibold text-white">
                {key.replaceAll("_", " ")}
              </h3>

              <p className="text-gray-300 leading-8">{String(value)}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
