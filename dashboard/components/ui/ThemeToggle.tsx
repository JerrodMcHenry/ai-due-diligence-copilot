"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const mounted = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );

  if (!mounted) {
    return <div className="h-10" />;
  }

  const isDark = theme === "dark";

  return (
    <div className="grid grid-cols-2 rounded-xl border border-border bg-surface p-1">
      <button
        type="button"
        onClick={() => setTheme("light")}
        aria-label="Use light theme"
        aria-pressed={!isDark}
        className={[
          "flex h-9 items-center justify-center rounded-lg transition-colors",
          !isDark
            ? "bg-primary text-white shadow-sm"
            : "text-text-muted hover:bg-surface-muted hover:text-text-primary",
        ].join(" ")}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          className="size-4"
        >
          <circle
            cx="12"
            cy="12"
            r="4"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.41M17.66 6.34l1.41-1.41"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </button>

      <button
        type="button"
        onClick={() => setTheme("dark")}
        aria-label="Use dark theme"
        aria-pressed={isDark}
        className={[
          "flex h-9 items-center justify-center rounded-lg transition-colors",
          isDark
            ? "bg-primary text-white shadow-sm"
            : "text-text-muted hover:bg-surface-muted hover:text-text-primary",
        ].join(" ")}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          className="size-4"
        >
          <path
            d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}
