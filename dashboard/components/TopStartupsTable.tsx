type Startup = {
  company_name: string;
  industry: string;
  stage: string;
  overall_score: number;
  readiness_score: number;
};

type TopStartupsTableProps = {
  startups: Startup[];
};

export default function TopStartupsTable({ startups }: TopStartupsTableProps) {
  return (
    <section className="mt-10 rounded-xl bg-gray-900 p-6">
      <h2 className="text-2xl font-bold mb-6">Top Startups</h2>

      <table className="w-full">
        <thead>
          <tr className="text-left border-b border-gray-800 text-gray-400">
            <th className="pb-3">Company</th>
            <th className="pb-3">Industry</th>
            <th className="pb-3">Stage</th>
            <th className="pb-3">Overall Score</th>
            <th className="pb-3">Readiness</th>
          </tr>
        </thead>

        <tbody>
          {startups.map((startup, index) => (
            <tr key={index} className="border-b border-gray-800">
              <td className="py-3">{startup.company_name}</td>
              <td className="py-3">{startup.industry}</td>
              <td className="py-3">{startup.stage}</td>
              <td className="py-3">{startup.overall_score}</td>
              <td className="py-3">{startup.readiness_score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
