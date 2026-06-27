type AnalyticsCardProps = {
  title: string;
  value: string | number;
};

export default function AnalyticsCard({ title, value }: AnalyticsCardProps) {
  return (
    <div className="rounded-xl bg-gray-900 p-6">
      <p className="text-gray-400">{title}</p>
      <h2 className="text-4xl font-bold mt-2">{value}</h2>
    </div>
  );
}
