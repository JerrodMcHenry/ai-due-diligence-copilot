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

// Phase 31C-B, Part 3/13: form input text bumped text-sm -> text-base
// (14px -> 16px, the directive's preferred size for form input text) --
// a single shared primitive change, so every Input/Textarea in the app
// gets it at once. Existing py-3 padding already leaves enough room; no
// layout regression.
export const FIELD_CONTROL_CLASSES =
  "w-full rounded-xl border bg-surface px-4 py-3 text-base text-text-primary outline-none transition-colors placeholder:text-text-muted focus:ring-2 focus:ring-primary/20";

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
        // Part 3: form labels called out explicitly (14-16px), not
        // "genuinely nonessential compact metadata" -- bumped one step.
        <label
          htmlFor={id}
          className="text-sm font-semibold uppercase tracking-wide text-text-secondary"
        >
          {label}
          {required ? <span className="text-danger"> *</span> : null}
        </label>
      ) : null}

      <div className={label ? "mt-2" : undefined}>{children}</div>

      {help && !error ? (
        // Phase 31C-B -- Global Typography & Readability Correction,
        // Part 3/13: form help text is meaningful explanatory copy (it
        // tells a founder what to actually type), not metadata -- bumped
        // from text-xs/text-muted to text-sm/text-secondary sitewide,
        // since every Input/Textarea in the app renders through here.
        <p id={helpId} className="mt-1.5 text-sm leading-5 text-text-secondary">
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
