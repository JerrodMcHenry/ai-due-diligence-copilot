type PageHeaderProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

// Phase 10.3: switched from hardcoded slate-* colors (which only ever
// looked correct in dark mode -- text-white on a light background is
// invisible) to the same design tokens every other component in this
// codebase already uses. Pure color-token fix, no layout/behavior
// change -- this component is used on nearly every page (15 call sites),
// so it's directly in-path for the shell's own light/dark verification.
export default function PageHeader({
  title,
  subtitle,
  action,
}: PageHeaderProps) {
  return (
    <header className="mb-8 flex flex-col gap-5 border-b border-border pb-7 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          {title}
        </h1>

        {subtitle ? (
          <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary sm:text-base">
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
