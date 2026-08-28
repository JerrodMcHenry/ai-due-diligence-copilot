import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import PlaybookLink from "@/components/playbooks/PlaybookLink";

// Phase 10.10 -- Founder Journey Integration, Part 6. The one restrained,
// reusable "what should I do next?" pattern -- deliberately NOT a
// recommendation engine: it has no LLM, no score, and no prediction. Every
// caller passes in a title/why/action it already deterministically
// derived from existing state (see dashboard/lib/journey/
// resolveIdeaLabNextStep.ts for the Idea Lab example); this component
// only renders whatever it's given. Pure presentation, zero I/O.
//
// An action is EITHER a plain navigation (href) OR an existing in-page
// mechanism (onClick) -- "Make this a mission" is a real API call
// Founder Missions already owns (see MissionsSection.tsx), not a route,
// so this has to support both rather than forcing everything through a
// Link.
type NextStepAction =
  | { label: string; href: string; onClick?: never; disabled?: boolean }
  | { label: string; onClick: () => void; href?: never; disabled?: boolean };

type NextStepCardProps = {
  eyebrow?: string;
  title: string;
  why?: string;
  primaryAction: NextStepAction;
  secondaryAction?: NextStepAction;
  // Optional contextual learning resource -- reuses the exact same
  // PlaybookLink every other surface uses (Founder Missions, NextMoves,
  // Pitch Deck Coach, Fundraising Readiness), never a second link style.
  learnPlaybookSlug?: string;
  className?: string;
};

function ActionButton({ action, variant }: { action: NextStepAction; variant: "primary" | "secondary" }) {
  if ("href" in action && action.href) {
    return (
      <Link href={action.href}>
        <Button type="button" variant={variant === "primary" ? "primary" : "secondary"} disabled={action.disabled}>
          {action.label}
        </Button>
      </Link>
    );
  }

  return (
    <Button
      type="button"
      variant={variant === "primary" ? "primary" : "secondary"}
      disabled={action.disabled}
      onClick={action.onClick}
    >
      {action.label}
    </Button>
  );
}

export default function NextStepCard({
  eyebrow = "What should I do next?",
  title,
  why,
  primaryAction,
  secondaryAction,
  learnPlaybookSlug,
  className = "",
}: NextStepCardProps) {
  return (
    <BaseCard variant="raised" className={["p-6", className].join(" ")}>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{eyebrow}</p>
      <p className="mt-1.5 text-lg font-bold text-text-primary">{title}</p>
      {why ? <p className="mt-1.5 text-sm leading-6 text-text-secondary">{why}</p> : null}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <ActionButton action={primaryAction} variant="primary" />
        {secondaryAction ? <ActionButton action={secondaryAction} variant="secondary" /> : null}
        {learnPlaybookSlug ? <PlaybookLink slug={learnPlaybookSlug} label="Learn how →" /> : null}
      </div>
    </BaseCard>
  );
}
