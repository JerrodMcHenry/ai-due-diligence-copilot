type PrimaryScoreCardProps = {
  title: string;
  score: number | null;
};

export default function PrimaryScoreCard({
  title,
  score,
}: PrimaryScoreCardProps) {
  const value = score ?? 0;
  const width = `${value}%`;

  let barColor = "bg-red-500";

  if (value >= 80) {
    barColor = "bg-green-500";
  } else if (value >= 50) {
    barColor = "bg-yellow-500";
  }

  return (
    <div className="rounded-xl bg-gray-900 p-6 border border-gray-800">
      <p className="text-gray-400">{title}</p>

      <p className="mt-3 text-4xl font-bold">{score ?? "--"} / 100</p>

      <div className="mt-5 h-3 rounded-full bg-gray-800">
        <div className={`h-3 rounded-full ${barColor}`} style={{ width }} />
      </div>
    </div>
  );
}
