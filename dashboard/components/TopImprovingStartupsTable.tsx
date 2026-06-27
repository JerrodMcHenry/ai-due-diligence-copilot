type ImprovingStartup = {
  company_name: string;
  first_score: number;
  latest_score: number;
  score_change: number;
};

type TopImprovingStartupsTableProps = {
  startups: ImprovingStartup[];
};

export default function TopImprovingStartupsTable({
  startups,
}: TopImprovingStartupsTableProps) {
  return (
    <section className="mt-10 rounded-xl bg-gray-900 p-6">
      <h2 className="text-2xl font-bold mb-6">Top Improving Startups</h2>

      <table className="w-full">
        <thead>
          <tr className="text-left border-b border-gray-800">
            <th className="pb-3">Company</th>
            <th className="pb-3">First Score</th>
            <th className="pb-3">Latest Score</th>
            <th className="pb-3">Score Change</th>
          </tr>
        </thead>

        <tbody>
          {startups.map((startup, index) => (
            <tr key={index} className="border-b border-gray-800">
              <td className="py-3">{startup.company_name}</td>
              <td>{startup.first_score}</td>
              <td>{startup.latest_score}</td>
              <td>{startup.score_change}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
