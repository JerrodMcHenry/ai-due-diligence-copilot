import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";
import PlaybookCard from "@/components/playbooks/PlaybookCard";
import { getAllPlaybooks, getPlaybookBySlug } from "@/content/playbooks";

const JOURNEY_STAGE_LABELS: Record<string, string> = {
  start: "Start",
  model: "Model",
  build: "Build",
  pitch: "Pitch",
  fundraise: "Fundraise",
};

type Props = {
  params: Promise<{ slug: string }>;
};

// Phase 10.9 -- Founder Playbooks V1. Public, no auth.protect() -- same
// reasoning as app/playbooks/page.tsx. A pure Server Component; an
// unknown slug calls Next's own notFound() rather than a hand-rolled
// error state, matching how every other dynamic route in this app that
// can 404 already behaves at the framework level for a truly missing
// resource.
export async function generateStaticParams() {
  return getAllPlaybooks().map((playbook) => ({ slug: playbook.slug }));
}

export default async function PlaybookDetailPage({ params }: Props) {
  const { slug } = await params;
  const playbook = getPlaybookBySlug(slug);

  if (!playbook) {
    notFound();
  }

  const relatedPlaybooks = playbook.relatedPlaybooks
    .map((relatedSlug) => getPlaybookBySlug(relatedSlug))
    .filter((related): related is NonNullable<typeof related> => Boolean(related));

  return (
    <>
      <Link href="/playbooks" className="text-xs font-semibold text-text-muted hover:text-text-primary">
        ← All playbooks
      </Link>

      <PageHeader
        title={playbook.title}
        subtitle={playbook.description}
        action={
          <span className="rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
            {JOURNEY_STAGE_LABELS[playbook.journeyStage]} · {playbook.estimatedMinutes} min
          </span>
        }
      />

      <div className="space-y-8">
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What is this?</h2>
          <div className="mt-2 space-y-3">
            {playbook.whatIsThis.map((paragraph, index) => (
              <p key={index} className="text-sm leading-6 text-text-secondary">
                {paragraph}
              </p>
            ))}
          </div>
        </section>

        <BaseCard className="p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Why it matters</h2>
          <p className="mt-2 text-sm leading-6 text-text-secondary">{playbook.whyItMatters}</p>
        </BaseCard>

        {playbook.objective ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What you&apos;re trying to learn</h2>
            <p className="mt-2 text-sm leading-6 text-text-primary">{playbook.objective}</p>
          </section>
        ) : null}

        {playbook.beforeYouStart && playbook.beforeYouStart.length > 0 ? (
          <BaseCard className="p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Before you start</h2>
            <ul className="mt-2 space-y-2">
              {playbook.beforeYouStart.map((item, index) => (
                <li key={index} className="flex gap-2.5 text-sm leading-6 text-text-secondary">
                  <span aria-hidden="true" className="text-primary">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </BaseCard>
        ) : null}

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Step by step</h2>
          <ol className="mt-2 space-y-2.5">
            {playbook.steps.map((step, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary-soft text-xs font-bold text-primary">
                  {index + 1}
                </span>
                <span className="pt-0.5 text-sm leading-6 text-text-primary">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        {playbook.questionsToAskOrDo && playbook.questionsToAskOrDo.length > 0 ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What to ask / do</h2>
            <ul className="mt-2 space-y-2">
              {playbook.questionsToAskOrDo.map((item, index) => (
                <li key={index} className="rounded-lg border border-border bg-surface-subtle px-3 py-2 text-sm leading-6 text-text-primary">
                  {item}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {playbook.exampleScript && playbook.exampleScript.length > 0 ? (
          <BaseCard className="p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Example conversation</h2>
            <div className="mt-3 space-y-2.5">
              {playbook.exampleScript.map((line, index) => (
                <div key={index} className="flex gap-3 text-sm leading-6">
                  <span className="w-14 shrink-0 text-xs font-semibold uppercase tracking-wide text-text-muted">{line.speaker}</span>
                  <span className="text-text-secondary">{line.line}</span>
                </div>
              ))}
            </div>
          </BaseCard>
        ) : null}

        {playbook.goodSignal && playbook.weakSignal ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What the signal looks like</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-success/20 bg-success-soft p-4">
                <p className="text-xs font-semibold text-success">Good signal</p>
                <ul className="mt-2 space-y-2">
                  {playbook.goodSignal.map((item, index) => (
                    <li key={index} className="flex gap-2 text-sm leading-6 text-text-primary">
                      <span aria-hidden="true" className="text-success">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl border border-danger/20 bg-danger-soft p-4">
                <p className="text-xs font-semibold text-danger">Weak or negative signal</p>
                <ul className="mt-2 space-y-2">
                  {playbook.weakSignal.map((item, index) => (
                    <li key={index} className="flex gap-2 text-sm leading-6 text-text-primary">
                      <span aria-hidden="true" className="text-danger">✕</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        ) : (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What good looks like</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">{playbook.whatGoodLooksLike}</p>
          </section>
        )}

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Common mistakes</h2>
          <ul className="mt-2 space-y-2">
            {playbook.commonMistakes.map((mistake, index) => (
              <li key={index} className="flex gap-2 text-sm leading-6 text-text-secondary">
                <span aria-hidden="true" className="text-warning">!</span>
                <span>{mistake}</span>
              </li>
            ))}
          </ul>
        </section>

        <BaseCard className="p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Checklist</h2>
          <ul className="mt-2 space-y-2">
            {playbook.checklist.map((item, index) => (
              <li key={index} className="flex gap-2.5 text-sm leading-6 text-text-primary">
                <span aria-hidden="true" className="text-success">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
          {playbook.whenYoureDone ? (
            <p className="mt-4 border-t border-border pt-4 text-sm leading-6 text-text-secondary">
              <span className="font-semibold text-text-primary">You&apos;re done when: </span>
              {playbook.whenYoureDone}
            </p>
          ) : null}
        </BaseCard>

        {playbook.whatToDoNext && playbook.whatToDoNext.length > 0 ? (
          <BaseCard className="border-primary/20 bg-primary-soft p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-primary">What to do next</h2>
            <ul className="mt-2 space-y-2">
              {playbook.whatToDoNext.map((item, index) => (
                <li key={index} className="text-sm leading-6 text-text-primary">
                  {item}
                </li>
              ))}
            </ul>
          </BaseCard>
        ) : null}

        {relatedPlaybooks.length > 0 ? (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Read next</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {relatedPlaybooks.map((related) => (
                <PlaybookCard key={related.slug} playbook={related} />
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </>
  );
}
