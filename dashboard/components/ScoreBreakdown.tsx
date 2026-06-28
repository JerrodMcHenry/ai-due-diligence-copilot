type ScoreBreakdownProps = {
  marketScore: number | null;
  teamScore: number | null;
  productScore: number | null;
  competitionScore: number | null;
  tractionScore: number | null;
  financialScore: number | null;
};

export default function ScoreBreakdown({
  marketScore,
  teamScore,
  productScore,
  competitionScore,
  tractionScore,
  financialScore,
}: ScoreBreakdownProps) {
  const scores = [
    { label: "Market", value: marketScore },
    { label: "Team", value: teamScore },
    { label: "Product", value: productScore },
    { label: "Competition", value: competitionScore },
    { label: "Traction", value: tractionScore },
    { label: "Financial", value: financialScore },
  ];

  return (
    <section className="mt-10 rounded-xl bg-gray-900 p-6">
      <h2 className="text-2xl font-bold mb-6">Score Breakdown</h2>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {scores.map((score) => (
          <div
            key={score.label}
            className="rounded-lg bg-gray-950 p-4 border border-gray-800"
          >
            <p className="text-gray-400">{score.label}</p>
            <p className="text-3xl font-bold mt-2">{score.value ?? "--"}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
