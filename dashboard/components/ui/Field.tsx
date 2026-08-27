import type { ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6. Shared label/help/error chrome
// for Input and Textarea -- kept separate from the <input>/<textarea>
// element itself so both primitives render identically around whatever
// field they wrap. Not exported for use on its own; Input.tsx and
// Textarea.tsx are the public API.
export type FieldProps = {
  id: string;
  label?: string;
  help?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
};

export const FIELD_CONTROL_CLASSES =
  "w-full rounded-xl border bg-surface px-4 py-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus:ring-2 focus:ring-primary/20";

export function fieldBorderClasses(hasError: boolean): string {
  return hasError
    ? "border-danger focus:border-danger"
    : "border-border focus:border-primary";
}

export default function Field({ id, label, help, error, required, children }: FieldProps) {
  const helpId = help ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div>
      {label ? (
        <label
          htmlFor={id}
          className="text-xs font-semibold uppercase tracking-wide text-text-secondary"
        >
          {label}
          {required ? <span className="text-danger"> *</span> : null}
        </label>
      ) : null}

      <div className={label ? "mt-2" : undefined}>{children}</div>

      {help && !error ? (
        <p id={helpId} className="mt-1.5 text-xs text-text-muted">
          {help}
        </p>
      ) : null}

      {error ? (
        <p id={errorId} role="alert" className="mt-1.5 text-xs font-medium text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
