import BaseCard from "@/components/ui/BaseCard";

import type { VentureSnapshotResponse } from "@/types";

// Phase 27 -- Shareable Venture Snapshot V1, Part 16. THE single shared
// renderer for the allowlisted VentureSnapshotResponse DTO -- used
// UNMODIFIED by both the founder's own preview (rendered inside
// VentureWorkspace, authenticated) and the public /v/[publicId] page
// (unauthenticated). One component, one visual truth: a founder's
// preview can never look safer/different than what a recipient actually
// receives, because both call sites pass the exact same prop shape
// through the exact same JSX.
//
// Deliberately reads ONLY the fields on VentureSnapshotResponse -- it has
// no access to (and could not render even if it wanted to) description,
// assumptions, history, captures, actions, or fundraising data, because
// none of those exist on this type at all (Part 4's "structurally
// incapable of leaking" guarantee, carried one layer up into the UI).
type VentureSnapshotCardProps = {
  snapshot: VentureSnapshotResponse;
  // Phase 31C-A -- Global Founder UX Acceptance, Part 5/6: live-discovered
  // heading-hierarchy bug -- this card's own <h1>/<h2>s are correct for
  // the real, standalone /v/[publicId] page (its true document title),
  // but the SAME component is also embedded as a live preview inside
  // ShareVentureSnapshot.tsx, on a page that already has its own <h1>
  // (the venture's own workspace title). Embedded there, this produced a
  // second <h1> and several <h2>s with no <h2> ancestor relationship to
  // the host page's outline -- a real assistive-technology navigation
  // problem, not just a lint nit. `asEmbeddedPreview` shifts every
  // heading down one level (h1->h2, h2->h3) with ZERO visual change
  // (same classes, same look -- Part 16's own "one visual truth" rule is
  // untouched) when true. Defaults to false so the public page's own
  // markup is completely unchanged.
  asEmbeddedPreview?: boolean;
};

export default function VentureSnapshotCard({ snapshot, asEmbeddedPreview = false }: VentureSnapshotCardProps) {
  const TitleTag = asEmbeddedPreview ? "h2" : "h1";
  const SectionTag = asEmbeddedPreview ? "h3" : "h2";

  return (
    <BaseCard variant="raised" className="mx-auto max-w-xl overflow-hidden p-0">
      <div className="bg-gradient-to-br from-primary-soft to-surface p-6 sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Venture</p>
        <TitleTag className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">{snapshot.name}</TitleTag>
        {snapshot.stage ? (
          <span className="mt-2 inline-block rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
            {snapshot.stage}
          </span>
        ) : null}
      </div>

      <div className="space-y-6 p-6 sm:p-8">
        {snapshot.problem_statement || snapshot.solution_description || snapshot.target_customer ? (
          <section>
            <SectionTag className="text-xs font-semibold uppercase tracking-wide text-text-muted">Building</SectionTag>
            <div className="mt-2 space-y-3">
              {snapshot.problem_statement ? (
                <div>
                  <p className="text-xs font-semibold text-text-secondary">Problem</p>
                  <p className="mt-0.5 text-sm leading-6 text-text-primary">{snapshot.problem_statement}</p>
                </div>
              ) : null}
              {snapshot.solution_description ? (
                <div>
                  <p className="text-xs font-semibold text-text-secondary">Solution</p>
                  <p className="mt-0.5 text-sm leading-6 text-text-primary">{snapshot.solution_description}</p>
                </div>
              ) : null}
              {snapshot.target_customer ? (
                <div>
                  <p className="text-xs font-semibold text-text-secondary">For</p>
                  <p className="mt-0.5 text-sm leading-6 text-text-primary">{snapshot.target_customer}</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {snapshot.evidence.length > 0 ? (
          <section>
            <SectionTag className="text-xs font-semibold uppercase tracking-wide text-text-muted">Evidence so far</SectionTag>
            <ul className="mt-2 space-y-1.5">
              {snapshot.evidence.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-text-primary">
                  <span aria-hidden="true" className="mt-0.5 text-success">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {snapshot.current_frontier ? (
          <section className="rounded-xl border border-primary/20 bg-primary/5 p-4">
            <SectionTag className="text-xs font-semibold uppercase tracking-wide text-text-muted">Proving next</SectionTag>
            <p className="mt-1.5 text-sm leading-6 text-text-primary">{snapshot.current_frontier}</p>
          </section>
        ) : null}

        {snapshot.vps !== null ? (
          <section>
            <SectionTag className="text-xs font-semibold uppercase tracking-wide text-text-muted">Venture Potential — optional</SectionTag>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-primary">{snapshot.vps.toFixed(1)}</span>
              <span className="text-sm text-text-muted">/ 10</span>
            </div>
            {snapshot.vps_categories && snapshot.vps_categories.length > 0 ? (
              <ul className="mt-3 space-y-1.5">
                {snapshot.vps_categories
                  .filter((c) => c.score !== null)
                  .map((c) => (
                    <li key={c.key} className="flex items-center justify-between text-xs text-text-secondary">
                      <span>{c.label}</span>
                      <span className="font-medium text-text-primary">{c.score!.toFixed(1)}</span>
                    </li>
                  ))}
              </ul>
            ) : null}
            {/* Global readability audit: bumped again, from text-xs to
                text-sm (Phase 29B had already bumped it once, from an
                arbitrary 11px) -- this disclaimer is trust-framing
                language a public viewer (often a third party like an
                investor) needs to actually read clearly, not tertiary
                metadata that 12px is meant for. */}
            <p className="mt-3 text-sm leading-6 text-text-muted">
              A model-based assessment from the information provided to SIE — not a company-quality, investment,
              or success prediction.
            </p>
          </section>
        ) : null}

        <div className="border-t border-border pt-4 text-center">
          <p className="text-xs text-text-muted">Built with SIE</p>
        </div>
      </div>
    </BaseCard>
  );
}
