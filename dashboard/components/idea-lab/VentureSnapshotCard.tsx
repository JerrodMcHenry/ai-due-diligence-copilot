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
export default function VentureSnapshotCard({ snapshot }: { snapshot: VentureSnapshotResponse }) {
  return (
    <BaseCard variant="raised" className="mx-auto max-w-xl overflow-hidden p-0">
      <div className="bg-gradient-to-br from-primary-soft to-surface p-6 sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Venture</p>
        <h1 className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">{snapshot.name}</h1>
        {snapshot.stage ? (
          <span className="mt-2 inline-block rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
            {snapshot.stage}
          </span>
        ) : null}
      </div>

      <div className="space-y-6 p-6 sm:p-8">
        {snapshot.problem_statement || snapshot.solution_description || snapshot.target_customer ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Building</h2>
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
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Evidence so far</h2>
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
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Proving next</h2>
            <p className="mt-1.5 text-sm leading-6 text-text-primary">{snapshot.current_frontier}</p>
          </section>
        ) : null}

        {snapshot.vps !== null ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Venture Potential — optional</h2>
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
