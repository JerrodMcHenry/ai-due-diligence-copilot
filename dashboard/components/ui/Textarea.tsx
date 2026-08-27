import type { TextareaHTMLAttributes } from "react";

import Field, { FIELD_CONTROL_CLASSES, fieldBorderClasses } from "./Field";

// Design System V2 (Phase 10.4), Part 6. Same field chrome as Input --
// large textarea usage is explicitly called out (Part 6) as needed for
// the future flagship idea-entry experience, so this defaults to a
// generous row count rather than the cramped 2-3 rows common in admin
// forms.
type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  id: string;
  label?: string;
  help?: string;
  error?: string;
};

export default function Textarea({
  id,
  label,
  help,
  error,
  required,
  rows = 6,
  className = "",
  ...props
}: TextareaProps) {
  return (
    <Field id={id} label={label} help={help} error={error} required={required}>
      <textarea
        id={id}
        required={required}
        rows={rows}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : help ? `${id}-help` : undefined}
        className={[
          FIELD_CONTROL_CLASSES,
          fieldBorderClasses(Boolean(error)),
          "resize-y leading-6",
          className,
        ].join(" ")}
        {...props}
      />
    </Field>
  );
}
