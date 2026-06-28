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
        {scores.map((score) => {
          const value = score.value ?? 0;
          const width = `${value * 10}%`;

          let barColor = "bg-red-500";

          if (value >= 8) {
            barColor = "bg-green-500";
          } else if (value >= 5) {
            barColor = "bg-yellow-500";
          }

          return (
            <div
              key={score.label}
              className="rounded-lg bg-gray-950 p-4 border border-gray-800"
            >
              <div className="flex justify-between items-center">
                <p className="text-gray-400">{score.label}</p>
                <p className="font-bold">{score.value ?? "--"}/10</p>
              </div>

              <div className="mt-4 h-2 rounded-full bg-gray-800">
                <div
                  className={`h-2 rounded-full ${barColor}`}
                  style={{ width }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
