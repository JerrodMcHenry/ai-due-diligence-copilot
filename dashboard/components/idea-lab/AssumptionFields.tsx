// Idea Lab V1: small, reusable, labeled inputs for the assumption editor.
// Every field is nullable-by-default and never silently defaults to a
// value that would influence scoring -- an empty field commits `null`,
// not 0 or "".

type FieldWrapperProps = {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
  // Phase 6.1: an optional provenance badge (see ProvenanceBadge.tsx),
  // rendered beside the label -- purely additive, every existing caller
  // (the venture workspace's own assumption editor) keeps working with
  // no badge shown at all.
  badge?: React.ReactNode;
};

function FieldWrapper({ label, htmlFor, children, badge }: FieldWrapperProps) {
  return (
    <div>
      <div className="mb-1.5 flex flex-wrap items-center justify-between gap-1.5">
        <label htmlFor={htmlFor} className="block text-xs font-medium text-text-muted">
          {label}
        </label>
        {badge}
      </div>
      {children}
    </div>
  );
}

const inputClasses =
  "h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20";

export function TextField({
  id,
  label,
  value,
  onChange,
  placeholder,
  multiline,
  badge,
}: {
  id: string;
  label: string;
  value: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
  multiline?: boolean;
  badge?: React.ReactNode;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge}>
      {multiline ? (
        <textarea
          id={id}
          rows={2}
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value.trim() === "" ? null : event.target.value)}
          placeholder={placeholder}
          className={`${inputClasses} resize-y py-2`}
        />
      ) : (
        <input
          id={id}
          type="text"
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value.trim() === "" ? null : event.target.value)}
          placeholder={placeholder}
          className={inputClasses}
        />
      )}
    </FieldWrapper>
  );
}

export function NumberField({
  id,
  label,
  value,
  onChange,
  min = 0,
  step = 1,
  placeholder,
  badge,
}: {
  id: string;
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  min?: number;
  step?: number;
  placeholder?: string;
  badge?: React.ReactNode;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge}>
      <input
        id={id}
        type="number"
        inputMode="decimal"
        min={min}
        step={step}
        value={value ?? ""}
        onChange={(event) => {
          const raw = event.target.value;
          onChange(raw === "" ? null : Number(raw));
        }}
        placeholder={placeholder ?? "Unknown"}
        className={inputClasses}
      />
    </FieldWrapper>
  );
}

export function SelectField({
  id,
  label,
  value,
  options,
  onChange,
  badge,
}: {
  id: string;
  label: string;
  value: string | null;
  options: string[];
  onChange: (value: string | null) => void;
  badge?: React.ReactNode;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge}>
      <select
        id={id}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value === "" ? null : event.target.value)}
        className={inputClasses}
      >
        <option value="">Unknown</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </FieldWrapper>
  );
}

export function ToggleField({
  id,
  label,
  value,
  onChange,
  badge,
}: {
  id: string;
  label: string;
  value: boolean | null;
  onChange: (value: boolean | null) => void;
  badge?: React.ReactNode;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge}>
      <select
        id={id}
        value={value === null ? "" : value ? "yes" : "no"}
        onChange={(event) =>
          onChange(event.target.value === "" ? null : event.target.value === "yes")
        }
        className={inputClasses}
      >
        <option value="">Unknown</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </FieldWrapper>
  );
}
