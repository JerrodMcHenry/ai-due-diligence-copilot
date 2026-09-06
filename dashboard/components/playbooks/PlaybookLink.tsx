import Link from "next/link";

// Phase 10.9 -- Founder Playbooks V1, Part 5. The ONE shared "Learn how"
// link every contextual integration surface uses (Founder Missions,
// NextMoves, VPSResultPanel, Pitch Deck Coach, Fundraising Readiness) --
// so the visual treatment stays restrained and consistent everywhere
// rather than four separately hand-rolled links. Pure presentation: it
// never fetches, mutates, or reads anything beyond the playbook it's
// told to link to.
type PlaybookLinkProps = {
  slug: string;
  label?: string;
  className?: string;
};

export default function PlaybookLink({ slug, label = "Learn how →", className = "" }: PlaybookLinkProps) {
  return (
    <Link
      href={`/playbooks/${slug}`}
      className={[
        // Phase 31C-C, Part 9: this is the ONE "Learn how ->" link every
        // recommendation/mission/gap card in the app renders through --
        // bumped text-xs -> text-sm since it's a real, clickable link on
        // nearly every card, not disposable metadata.
        "inline-flex items-center gap-1 text-sm font-semibold text-primary hover:text-primary-hover hover:underline",
        className,
      ].join(" ")}
    >
      {label}
    </Link>
  );
}
