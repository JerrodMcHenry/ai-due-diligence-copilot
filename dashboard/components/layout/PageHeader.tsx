type PageHeaderProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export default function PageHeader({
  title,
  subtitle,
  action,
}: PageHeaderProps) {
  return (
    <div className="mb-8 flex items-start justify-between gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          {title}
        </h1>

        {subtitle && (
          <p className="mt-2 max-w-2xl text-sm text-slate-400">{subtitle}</p>
        )}
      </div>

      {action && <div>{action}</div>}
    </div>
  );
}
