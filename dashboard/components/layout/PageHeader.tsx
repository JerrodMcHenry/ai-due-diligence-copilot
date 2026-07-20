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
    <header className="mb-8 flex flex-col gap-5 border-b border-slate-800 pb-7 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          {title}
        </h1>

        {subtitle ? (
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
            {subtitle}
          </p>
        ) : null}
      </div>

      {action ? (
        <div className="flex shrink-0 items-center">{action}</div>
      ) : null}
    </header>
  );
}
