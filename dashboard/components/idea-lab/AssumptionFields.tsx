"use client";

import { useEffect, useRef } from "react";

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
  // Build V3, Part 11: the founder's own words this field's value was
  // drawn/derived from (VentureDraft's `source_quote`, e.g. "$3,000-
  // $12,000/year" behind a $7,500 midpoint price_point) -- shown as its
  // own line, never folded into the badge, so a derived/rounded value
  // never reads as if the founder typed that exact number. Only ever
  // passed by the creation-review screen, which is the only caller
  // holding real VentureDraft source_quote data; the post-create editor
  // has none (provenance is UI-only from the draft stage on, see
  // types/ideaLab.ts's own comment on draftToAssumptions).
  hint?: string | null;
};

function FieldWrapper({ label, htmlFor, children, badge, hint }: FieldWrapperProps) {
  return (
    <div>
      <div className="mb-1.5 flex flex-wrap items-center justify-between gap-1.5">
        {/* Phase 31C-B -- Global Typography & Readability Correction,
            Part 3/13: this one shared wrapper renders the field label for
            every assumption across the entire venture creation/review AND
            "Edit the full model" editor, so bumping it here (text-xs ->
            text-sm, matching Field.tsx's own form-label treatment) fixes
            the whole surface at once rather than dozens of call sites. */}
        <label htmlFor={htmlFor} className="block text-sm font-medium text-text-secondary">
          {label}
        </label>
        {badge}
      </div>
      {children}
      {hint ? (
        // Phase 29B, Part 7 bumped this from an arbitrary 11px; Phase
        // 31C-B bumps it again -- this is the founder's own verbatim
        // words, meaningful quoted content, not metadata.
        <p className="mt-1 text-sm italic leading-5 text-text-secondary">You said: &ldquo;{hint}&rdquo;</p>
      ) : null}
    </div>
  );
}

// Part 3: "FORM INPUT TEXT 16px preferred" -- text-sm -> text-base,
// applied once here for every TextField/NumberField/SelectField/
// ToggleField in the app.
const inputClasses =
  "h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20";

// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support, Part 5. The live walkthrough's own finding: a `rows={2}`
// textarea showed roughly one visible line of a real problem statement/
// solution description/differentiation, forcing internal scrolling to
// read a field the founder is supposed to be reviewing and correcting.
// `min-h-[7rem]` gives every long-form field a real minimum (~4-5 lines)
// even when short; the auto-grow effect on TextField below then expands
// it further to fit whatever the founder typed or SIE proposed, so nested
// scrolling is never needed to see the whole value. `resize-y` is kept so
// a founder can still manually expand beyond that if they want more room.
const textareaClasses =
  "w-full min-h-[7rem] rounded-lg border border-border bg-surface px-3 py-2.5 text-base leading-6 text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 resize-y overflow-hidden";

export function TextField({
  id,
  label,
  value,
  onChange,
  placeholder,
  multiline,
  badge,
  hint,
}: {
  id: string;
  label: string;
  value: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
  multiline?: boolean;
  badge?: React.ReactNode;
  hint?: string | null;
}) {
  // Applies to every multiline caller across the app -- the onboarding
  // review screen and the "Edit the full model" editor both use this
  // same TextField, so fixing it here fixes both surfaces at once
  // (Section 5's own "audit the entire model editor" instruction).
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value, multiline]);

  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge} hint={hint}>
      {multiline ? (
        <textarea
          ref={textareaRef}
          id={id}
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value.trim() === "" ? null : event.target.value)}
          placeholder={placeholder}
          className={textareaClasses}
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
  hint,
}: {
  id: string;
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  min?: number;
  step?: number;
  placeholder?: string;
  badge?: React.ReactNode;
  hint?: string | null;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge} hint={hint}>
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
  hint,
}: {
  id: string;
  label: string;
  value: string | null;
  options: string[];
  onChange: (value: string | null) => void;
  badge?: React.ReactNode;
  hint?: string | null;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge} hint={hint}>
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
  hint,
}: {
  id: string;
  label: string;
  value: boolean | null;
  onChange: (value: boolean | null) => void;
  badge?: React.ReactNode;
  hint?: string | null;
}) {
  return (
    <FieldWrapper label={label} htmlFor={id} badge={badge} hint={hint}>
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
