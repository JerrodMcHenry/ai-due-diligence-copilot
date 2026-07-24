import type { HTMLAttributes, ReactNode } from "react";

type BaseCardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export default function BaseCard({
  children,
  className = "",
  ...props
}: BaseCardProps) {
  return (
    <div
      className={[
        "rounded-2xl border border-border bg-surface shadow-sm",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
