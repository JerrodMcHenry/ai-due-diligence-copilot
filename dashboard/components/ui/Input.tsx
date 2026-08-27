import type { InputHTMLAttributes } from "react";

import Field, { FIELD_CONTROL_CLASSES, fieldBorderClasses } from "./Field";

// Design System V2 (Phase 10.4), Part 6. Comfortable mobile sizing
// (py-3 / text-sm gives a ~44px control height, matching Button's
// touch-target floor), a strong focus ring, and label/help/error text --
// built to carry the future flagship idea-entry experience (Part 6's
// explicit requirement), starting with today's AnalyzeStartupForm.
type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label?: string;
  help?: string;
  error?: string;
};

export default function Input({ id, label, help, error, required, className = "", ...props }: InputProps) {
  return (
    <Field id={id} label={label} help={help} error={error} required={required}>
      <input
        id={id}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : help ? `${id}-help` : undefined}
        className={[FIELD_CONTROL_CLASSES, fieldBorderClasses(Boolean(error)), className].join(" ")}
        {...props}
      />
    </Field>
  );
}
