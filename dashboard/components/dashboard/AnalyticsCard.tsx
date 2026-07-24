import BaseCard from "@/components/ui/BaseCard";

type AnalyticsCardProps = {
  title: string;
  value: string | number;
  description?: string;
};

export default function AnalyticsCard({
  title,
  value,
  description,
}: AnalyticsCardProps) {
  return (
    <BaseCard className="relative overflow-hidden p-6">
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent"
      />

      <p className="text-sm font-medium text-text-secondary">{title}</p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
        {value}
      </p>

      {description && (
        <p className="mt-3 text-sm leading-6 text-text-muted">{description}</p>
      )}
    </BaseCard>
  );
}
