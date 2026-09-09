"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { extractCaptureSignals } from "@/lib/captureSignals";
import {
  buildEvidenceDraft,
  toCreateEvidencePayload,
  toRawTextEvidencePayload,
  hasExplicitRelationship,
  allCheckedItemsHaveRelationship,
  EVIDENCE_TYPE_LABELS,
  RELATIONSHIP_LABELS,
  type EvidenceTypeChoice,
  type RelationshipChoice,
} from "@/lib/build/evidenceMapping";
import {
  createVentureDecision,
  createVentureEvidence,
  createVentureMission,
  getVentureRecommendation,
  listVentureDecisions,
  listVentureEvidence,
  listVentureMissions,
  recordVentureMissionLearning,
  resolveVentureEvidence,
} from "@/lib/api";

import type {
  BlockingEvidenceItem,
  BuildRecommendation,
  CompanyIntelligenceSummary,
  CurrentQuestion,
  VentureDecision,
  VentureEvidence,
  VentureMission,
} from "@/types";

// Phase 34D -- SIE Build Intelligence Loop V1. Promoted to Overview's own
// hero by Phase 34E -- Founder Experience Simplification V1 (see that
// phase's final report for the full reasoning): this card's own internal
// logic is untouched from 34D/34D-A, only its prominence and its
// neighbors on the page changed. PrimaryCommandCard (the older, separate
// "what should I do next?" card) and the old Model/What-If tabs are gone
// specifically BECAUSE this card now does that job, evidence-aware,
// alone -- see VentureWorkspace.tsx.
//
// QUESTION -> TEST -> RESULT -> EVIDENCE -> INTERPRETATION ->
// RECOMMENDATION -> DECISION -> OUTCOME, proven end to end.
//
// Plain-language labels only (§15) -- "Hypothesis," "Evidence taxonomy,"
// "Interpretation," "Decision," "Provenance" never appear in this file's
// JSX, only in code comments.
//
// State is derived entirely from the server on every load/refresh
// (missions/evidence/decisions/recommendation) -- nothing here is
// component-local memory pretending to be venture history (§12: "based
// on persisted venture history, not component-local state").
type Props = {
  ventureId: number;
  ventureName: string;
  // Phase 34G -- SIE Intelligence Advantage V1. This component already
  // fetches GET /ventures/{id}/recommendation on every refresh; its
  // response now also carries a company-intelligence summary
  // (§10-13). Rather than a second fetch, the parent (CommandCenter.tsx)
  // receives it here and renders its own separate "current context"
  // section from it -- the same lifted-state pattern this codebase
  // already uses for primaryMissionTitle/missionedMilestones.
  onCompanyIntelligence?: (summary: CompanyIntelligenceSummary) => void;
  // Phase 38B -- Founder Command Center V1. Defaults to this card's own,
  // unchanged "What matters now" heading. CommandCenter.tsx passes
  // `null` only when a higher-priority financial constraint is already
  // occupying that exact slot on the page -- this card's own body
  // (testing/decision/outcome flows, contradiction resolution) is
  // completely unaffected either way; only whether IT renders the page's
  // primary heading changes.
  heading?: string | null;
  // Phase 38C -- Cross-System Founder Intelligence V1. Same "lift, don't
  // re-fetch" pattern as onCompanyIntelligence above: the plain-text
  // label for whatever Build currently considers its focus (the active
  // mission's question if one is being tested, else the current
  // recommendation's question) -- the one Build-side fact
  // CommandCenter.tsx's own cross-system connections need. Never a new
  // fetch; read straight off the same recommendation response this
  // component already has.
  onFocusText?: (text: string | null) => void;
};

type LoadState = "loading" | "ready" | "error";

export default function CurrentQuestionCard({
  ventureId,
  ventureName,
  onCompanyIntelligence,
  heading = "What matters now",
  onFocusText,
}: Props) {
  const { getToken } = useAuth();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [missions, setMissions] = useState<VentureMission[]>([]);
  const [evidence, setEvidence] = useState<VentureEvidence[]>([]);
  const [decisions, setDecisions] = useState<VentureDecision[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [recommendation, setRecommendation] = useState<BuildRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Phase 40A-FIX -- Private Beta P1 Hardening, P1 #2: same convention as
  // FinanceOverview.tsx's own snapshotIdempotencyKeyRef -- withToken()
  // below swallows a thrown error into `setError`/`null`, so this must
  // live here (where the action callback's own success/failure is
  // visible), not inside RecommendationState's button component.
  const customMissionIdempotencyKeyRef = useRef<string | null>(null);

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    try {
      const [missionList, evidenceList, decisionList, rec] = await Promise.all([
        listVentureMissions(ventureId, token),
        listVentureEvidence(ventureId, token),
        listVentureDecisions(ventureId, token),
        getVentureRecommendation(ventureId, token),
      ]);
      setMissions(missionList);
      setEvidence(evidenceList);
      setDecisions(decisionList);
      setCurrentQuestion(rec.current_question);
      setRecommendation(rec.recommendation);
      onCompanyIntelligence?.(rec.company_intelligence);
      onFocusText?.(rec.current_question?.question_text ?? rec.recommendation?.question_text ?? null);
      setLoadState("ready");
    } catch (err) {
      console.error("Failed to load the current question:", err);
      setLoadState("error");
    }
  }, [ventureId, getToken, onCompanyIntelligence, onFocusText]);

  useEffect(() => {
    // Promise.resolve().then() is a genuine microtask boundary, not
    // decoration -- react-hooks/set-state-in-effect flags refresh()'s
    // own synchronous setLoadState("loading")-adjacent calls as directly
    // reachable from this effect body otherwise. Same pattern
    // ShareVentureSnapshot.tsx's own load() effect already uses.
    Promise.resolve().then(() => {
      refresh();
    });
  }, [refresh]);

  if (loadState === "loading") {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (loadState === "error") {
    return (
      <BaseCard className="p-5">
        <p className="text-sm text-danger">Couldn&rsquo;t load this section. Try refreshing the page.</p>
      </BaseCard>
    );
  }

  const activeMission = currentQuestion ? missions.find((m) => m.id === currentQuestion.mission_id) ?? null : null;
  // The active mission once its interpretation exists but no decision has
  // been recorded for it yet -- this is the "awaiting decision" state,
  // distinct from "actively testing" (activeMission above, no
  // interpretation) and from "nothing active" (neither is set).
  const awaitingDecisionMission = missions.find(
    (m) => m.status === "active" && m.interpretation_summary && !decisions.some((d) => d.related_mission_id === m.id)
  );
  const mostRecentDecision = decisions.length > 0 ? decisions[decisions.length - 1] : null;

  async function withToken<T>(action: (token: string) => Promise<T>): Promise<T | null> {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("Your session expired. Sign in again.");
      return null;
    }
    try {
      return await action(token);
    } catch (err) {
      console.error(err);
      setError("Something went wrong. Try again.");
      return null;
    }
  }

  return (
    // Phase 34E -- Founder Experience Simplification V1, Sections 9/10:
    // this is now Overview's hero, deliberately the one "raised" card on
    // the page (see VentureWorkspace.tsx's own VentureIdentity, which
    // uses the calmer "default" variant precisely so this stands out by
    // contrast, not by inventing a new, heavier design primitive). The
    // "Build loop" badge is gone (Section 24 jargon audit) -- it named
    // the internal architecture, not a founder job; the heading alone
    // already says what this is.
    <BaseCard variant="raised" className="space-y-5 p-6 sm:p-7">
      {heading ? <h2 className="text-xl font-bold text-text-primary">{heading}</h2> : null}

      {error ? <p className="text-sm text-danger">{error}</p> : null}

      {activeMission ? (
        <TestingState
          mission={activeMission}
          onRecordResult={(text) =>
            withToken(async (token) => {
              await recordVentureMissionLearning(ventureId, activeMission.id, text, token);
              await refresh();
            })
          }
          onConfirmEvidence={(payloads) =>
            withToken(async (token) => {
              for (const payload of payloads) {
                await createVentureEvidence(ventureId, { ...payload, related_mission_id: activeMission.id }, token);
              }
              await refresh();
            })
          }
        />
      ) : awaitingDecisionMission ? (
        <DecisionState
          mission={awaitingDecisionMission}
          recommendation={recommendation}
          evidenceForMission={evidence.filter((e) => e.related_mission_id === awaitingDecisionMission.id && !e.superseded_by_id)}
          onDecide={(founderChoice, founderRationale, evidenceIds) =>
            withToken(async (token) => {
              await createVentureDecision(
                ventureId,
                {
                  related_mission_id: awaitingDecisionMission.id,
                  sie_recommendation: recommendation?.recommended_test_title ?? "Continue exploring this question.",
                  sie_reasoning: recommendation?.why_it_matters ?? "",
                  founder_choice: founderChoice,
                  founder_rationale: founderRationale || null,
                  evidence_ids: evidenceIds,
                },
                token
              );
              await refresh();
            })
          }
        />
      ) : (
        <RecommendationState
          ventureName={ventureName}
          recommendation={recommendation}
          onStartTest={() =>
            withToken(async (token) => {
              if (!recommendation) return;
              await createVentureMission(
                ventureId,
                {
                  title: recommendation.recommended_test_title,
                  description: recommendation.what_to_do,
                  mission_type: recommendation.recommended_test_type,
                  source: "vps_guidance",
                  question_text: recommendation.question_text,
                  why_it_matters: recommendation.why_it_matters,
                },
                token
              );
              await refresh();
            })
          }
          onStartCustomTest={(questionText, whyItMatters) =>
            withToken(async (token) => {
              if (!customMissionIdempotencyKeyRef.current) {
                customMissionIdempotencyKeyRef.current =
                  typeof crypto !== "undefined" && "randomUUID" in crypto
                    ? crypto.randomUUID()
                    : `${ventureId}-${questionText}-${Date.now()}-${Math.random()}`;
              }
              await createVentureMission(
                ventureId,
                {
                  title: questionText,
                  mission_type: "other",
                  source: "founder_created",
                  question_text: questionText,
                  why_it_matters: whyItMatters || null,
                  idempotency_key: customMissionIdempotencyKeyRef.current,
                },
                token
              );
              // Only reached on success -- a throw above (caught by
              // withToken, outside this callback) leaves the ref set so a
              // retry reuses the same key instead of creating a second
              // mission.
              customMissionIdempotencyKeyRef.current = null;
              await refresh();
            })
          }
          onResolveEvidence={(evidenceId, resolutionNote) =>
            withToken(async (token) => {
              await resolveVentureEvidence(ventureId, evidenceId, resolutionNote, token);
              await refresh();
            })
          }
        />
      )}

      {!activeMission && !awaitingDecisionMission && mostRecentDecision ? (
        <OutcomeState
          decision={mostRecentDecision}
          onRecordOutcome={(text, relationship) =>
            withToken(async (token) => {
              const payload = toRawTextEvidencePayload(text, "longitudinal_outcome", relationship);
              await createVentureEvidence(ventureId, { ...payload, related_decision_id: mostRecentDecision.id }, token);
              await refresh();
            })
          }
        />
      ) : null}
    </BaseCard>
  );
}

// --- Case: actively testing -------------------------------------------------

function TestingState({
  mission,
  onRecordResult,
  onConfirmEvidence,
}: {
  mission: VentureMission;
  onRecordResult: (text: string) => Promise<void | null>;
  onConfirmEvidence: (payloads: ReturnType<typeof toCreateEvidencePayload>[]) => Promise<void | null>;
}) {
  const [text, setText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What we&rsquo;re trying to learn</p>
        <p className="mt-1 text-lg font-semibold text-text-primary">{mission.question_text ?? mission.title}</p>
        {mission.why_it_matters ? <p className="mt-1 text-base leading-7 text-text-secondary">{mission.why_it_matters}</p> : null}
      </div>

      {mission.description ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What to do</p>
          <p className="mt-1 text-base leading-6 text-text-secondary">{mission.description}</p>
        </div>
      ) : null}

      {!mission.learning_summary ? (
        <>
          <div>
            <label htmlFor="build-loop-result" className="mb-1.5 block text-sm font-medium text-text-secondary">
              What happened?
            </label>
            <textarea
              id="build-loop-result"
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={4}
              placeholder="e.g. Talked to five prospects about a paid pilot. Two agreed to pay $500/month."
              className="w-full min-h-[6rem] rounded-lg border border-border bg-surface px-3 py-2.5 text-base leading-6 text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>

          <Button
            type="button"
            disabled={isSaving || !text.trim()}
            loading={isSaving}
            onClick={async () => {
              setIsSaving(true);
              await onRecordResult(text.trim());
              setIsSaving(false);
            }}
          >
            {isSaving ? "Saving..." : "Record result"}
          </Button>
        </>
      ) : (
        <div className="border-t border-border pt-3">
          <p className="text-sm text-text-secondary">
            You recorded: &ldquo;{mission.learning_summary}&rdquo;
          </p>
          <div className="mt-3">
            <CandidateEvidenceReview resultText={mission.learning_summary} onConfirm={onConfirmEvidence} />
          </div>
        </div>
      )}
    </div>
  );
}

// --- Case: interpretation ready, decision pending ---------------------------

function DecisionState({
  mission,
  recommendation,
  evidenceForMission,
  onDecide,
}: {
  mission: VentureMission;
  recommendation: BuildRecommendation | null;
  evidenceForMission: VentureEvidence[];
  onDecide: (founderChoice: string, founderRationale: string, evidenceIds: number[]) => Promise<void | null>;
}) {
  const [customChoice, setCustomChoice] = useState("");
  const [rationale, setRationale] = useState("");
  const [isDeciding, setIsDeciding] = useState(false);

  async function decide(choice: string) {
    setIsDeciding(true);
    await onDecide(choice, rationale, evidenceForMission.map((e) => e.id));
    setIsDeciding(false);
  }

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What we found</p>
        <ul className="mt-1.5 space-y-1">
          {evidenceForMission.map((e) => (
            <li key={e.id} className="text-base leading-6 text-text-secondary">
              &ldquo;{e.statement}&rdquo;
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What we learned</p>
        <p className="mt-1 text-base leading-7 text-text-primary">{mission.interpretation_summary}</p>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What this doesn&rsquo;t prove</p>
        <p className="mt-1 text-sm leading-6 text-text-secondary">{mission.interpretation_limitations}</p>
      </div>

      {recommendation ? (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">SIE recommends</p>
          <p className="mt-1 text-base font-semibold text-text-primary">{recommendation.recommended_test_title}</p>
          <p className="mt-1 text-sm leading-6 text-text-secondary">{recommendation.why_it_matters}</p>
        </div>
      ) : null}

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What do you want to do?</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button type="button" disabled={isDeciding} loading={isDeciding} onClick={() => decide(recommendation?.recommended_test_title ?? "Continue as SIE recommends")}>
            Continue as recommended
          </Button>
          <Button type="button" variant="subtle" disabled={isDeciding} onClick={() => decide("Pause on this question for now")}>
            Pause for now
          </Button>
        </div>

        <div className="mt-3 flex flex-wrap items-end gap-2">
          <div className="min-w-0 flex-1">
            <label htmlFor="build-loop-custom-choice" className="mb-1 block text-sm font-medium text-text-secondary">
              Or do something else
            </label>
            <input
              id="build-loop-custom-choice"
              type="text"
              value={customChoice}
              onChange={(event) => setCustomChoice(event.target.value)}
              placeholder="What are you going to do instead?"
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>
          <Button type="button" variant="secondary" disabled={isDeciding || !customChoice.trim()} onClick={() => decide(customChoice.trim())}>
            Record this choice
          </Button>
        </div>

        <div className="mt-2">
          <label htmlFor="build-loop-rationale" className="mb-1 block text-sm font-medium text-text-secondary">
            Why (optional)
          </label>
          <input
            id="build-loop-rationale"
            type="text"
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
        </div>
      </div>
    </div>
  );
}

// --- Phase 34G-A §2/§3/§6/§10: a specific, resolvable tension -------------
//
// SIE never lets a founder outvote a contradiction by volume (§2: "8
// supports > 1 contradiction = validated" is explicitly forbidden), and
// never lets it disappear on its own -- but a founder who KNOWS the
// old result no longer reflects reality (a one-off, a different
// segment, before a real product change) has an explicit, honest way to
// say so, in their own words. Resolving does not edit or delete
// anything -- it stays visible in full venture history.
function BlockingEvidencePanel({
  items,
  onResolve,
}: {
  items: BlockingEvidenceItem[];
  onResolve: (evidenceId: number, resolutionNote: string) => Promise<void | null>;
}) {
  return (
    <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 space-y-2.5">
      <p className="text-sm font-medium text-text-primary">
        These specific results are creating this tension. If one no longer reflects where things stand, you
        can mark it resolved.
      </p>
      <ul className="space-y-2">
        {items.map((item) => (
          <BlockingEvidenceRow key={item.id} item={item} onResolve={onResolve} />
        ))}
      </ul>
    </div>
  );
}

function BlockingEvidenceRow({
  item,
  onResolve,
}: {
  item: BlockingEvidenceItem;
  onResolve: (evidenceId: number, resolutionNote: string) => Promise<void | null>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [note, setNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isResolved, setIsResolved] = useState(false);

  if (isResolved) {
    return (
      <li className="rounded-md border border-border bg-surface p-2.5 text-sm text-text-secondary">
        Marked resolved -- SIE will re-evaluate what matters most next time you check.
      </li>
    );
  }

  return (
    <li className="rounded-md border border-border bg-surface p-2.5">
      <p className="text-sm text-text-secondary">&ldquo;{item.statement}&rdquo;</p>
      {!isOpen ? (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="mt-1.5 text-xs font-semibold text-primary hover:text-primary-hover"
        >
          Was this addressed?
        </button>
      ) : (
        <div className="mt-2 space-y-2">
          <input
            type="text"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="e.g. This was a different segment -- our focus now is enterprise, where results are strong."
            className="h-9 w-full rounded-md border border-border bg-background px-2.5 text-sm text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              disabled={isSaving || !note.trim()}
              loading={isSaving}
              onClick={async () => {
                setIsSaving(true);
                await onResolve(item.id, note.trim());
                setIsSaving(false);
                setIsResolved(true);
              }}
            >
              Mark resolved
            </Button>
            <Button type="button" variant="subtle" size="sm" disabled={isSaving} onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </li>
  );
}

// --- Case: nothing active -- recommend the next question --------------------

function RecommendationState({
  ventureName,
  recommendation,
  onStartTest,
  onStartCustomTest,
  onResolveEvidence,
}: {
  ventureName: string;
  recommendation: BuildRecommendation | null;
  onStartTest: () => Promise<void | null>;
  onStartCustomTest: (questionText: string, whyItMatters: string) => Promise<void | null>;
  onResolveEvidence: (evidenceId: number, resolutionNote: string) => Promise<void | null>;
}) {
  const [isStarting, setIsStarting] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [customQuestion, setCustomQuestion] = useState("");
  const [customWhy, setCustomWhy] = useState("");
  const [isStartingCustom, setIsStartingCustom] = useState(false);

  if (!recommendation) {
    return <p className="text-sm text-text-secondary">Model a few assumptions about {ventureName} to get your first recommendation.</p>;
  }

  return (
    <div className="space-y-3">
      <div>
        <p className="mt-1 text-lg font-semibold text-text-primary">{recommendation.question_text}</p>
        <p className="mt-1 text-base leading-7 text-text-secondary">{recommendation.why_it_matters}</p>
      </div>

      {recommendation.blocking_evidence.length > 0 ? (
        <BlockingEvidencePanel items={recommendation.blocking_evidence} onResolve={onResolveEvidence} />
      ) : null}

      <div className="rounded-lg border border-border bg-surface p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Try this</p>
        <p className="mt-1 text-base font-medium text-text-primary">{recommendation.recommended_test_title}</p>
        <p className="mt-1 text-sm leading-6 text-text-secondary">{recommendation.what_to_do}</p>
      </div>

      <Button
        type="button"
        disabled={isStarting}
        loading={isStarting}
        onClick={async () => {
          setIsStarting(true);
          await onStartTest();
          setIsStarting(false);
        }}
      >
        {isStarting ? "Starting..." : "Start this test"}
      </Button>

      <div>
        <button type="button" onClick={() => setShowCustom((v) => !v)} className="text-sm font-semibold text-primary hover:text-primary-hover">
          {showCustom ? "Cancel" : "Or test something else →"}
        </button>
        {showCustom ? (
          <div className="mt-2 space-y-2">
            <input
              type="text"
              value={customQuestion}
              onChange={(event) => setCustomQuestion(event.target.value)}
              placeholder="What do you want to figure out?"
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
            <input
              type="text"
              value={customWhy}
              onChange={(event) => setCustomWhy(event.target.value)}
              placeholder="Why does it matter? (optional)"
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
            <Button
              type="button"
              variant="secondary"
              disabled={isStartingCustom || !customQuestion.trim()}
              loading={isStartingCustom}
              onClick={async () => {
                setIsStartingCustom(true);
                await onStartCustomTest(customQuestion.trim(), customWhy.trim());
                setIsStartingCustom(false);
              }}
            >
              Start this test
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// --- Shared: required, explicit relationship choice -------------------------
//
// Phase 34D-A. The live LedgerFlow walkthrough in Phase 34D accidentally
// saved an outcome ("One customer renewed. One customer churned.") with
// the silent default relationship "neutral" because nothing forced an
// explicit choice. This control is the fix: it NEVER pre-selects a value
// (not even from a signal's polarity, even though that's a strong hint),
// and it always renders a visible reason when nothing is chosen yet --
// callers additionally gate their own Save/Confirm button on
// `value !== null` so the requirement doesn't rely on this component
// alone, but the button being disabled is never the ONLY explanation a
// founder sees (§1: "do not rely solely on disabled-button state if that
// makes the reason unclear").
const RELATIONSHIP_OPTIONS: RelationshipChoice[] = ["supports", "mixed", "contradicts", "neutral"];

function RelationshipPicker({
  value,
  onChange,
  prompt = "How does this affect what we were testing?",
}: {
  value: RelationshipChoice | null;
  onChange: (choice: RelationshipChoice) => void;
  prompt?: string;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-sm font-medium text-text-secondary">{prompt}</p>
      <div className="flex flex-wrap gap-2">
        {RELATIONSHIP_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={[
              "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
              value === option ? "border-primary bg-primary-soft text-primary" : "border-border text-text-secondary hover:border-primary/40",
            ].join(" ")}
          >
            {RELATIONSHIP_LABELS[option]}
          </button>
        ))}
      </div>
      {value === null ? <p className="text-xs text-warning">Choose one before saving.</p> : null}
    </div>
  );
}

// --- Case: recording an outcome for a past decision --------------------------

function OutcomeState({
  decision,
  onRecordOutcome,
}: {
  decision: VentureDecision;
  onRecordOutcome: (text: string, relationship: RelationshipChoice) => Promise<void | null>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState("");
  // Phase 34D-A: starts unset, on purpose -- never a silent "neutral"
  // default. See RelationshipPicker above.
  const [relationship, setRelationship] = useState<RelationshipChoice | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  return (
    <div className="border-t border-border pt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What happened afterward?</p>
      <p className="mt-1 text-sm text-text-secondary">
        You decided: &ldquo;{decision.founder_choice}&rdquo;. Worth checking back in on this later.
      </p>
      {!isOpen ? (
        <Button type="button" variant="subtle" size="sm" className="mt-2" onClick={() => setIsOpen(true)}>
          Log what happened
        </Button>
      ) : (
        <div className="mt-2 space-y-3">
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={3}
            placeholder="e.g. One customer renewed. One customer churned."
            className="w-full min-h-[5rem] rounded-lg border border-border bg-surface px-3 py-2.5 text-base leading-6 text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
          <RelationshipPicker value={relationship} onChange={setRelationship} />
          <Button
            type="button"
            size="sm"
            disabled={isSaving || !text.trim() || !hasExplicitRelationship(relationship)}
            loading={isSaving}
            onClick={async () => {
              if (!hasExplicitRelationship(relationship)) return;
              setIsSaving(true);
              await onRecordOutcome(text.trim(), relationship);
              setIsSaving(false);
              setText("");
              setRelationship(null);
              setIsOpen(false);
            }}
          >
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </div>
      )}
    </div>
  );
}

// --- Case: candidate-evidence review (used once a result exists) -----------

export function CandidateEvidenceReview({
  resultText,
  onConfirm,
}: {
  resultText: string;
  onConfirm: (payloads: ReturnType<typeof toCreateEvidencePayload>[]) => Promise<void | null>;
}) {
  const signals = extractCaptureSignals(resultText);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [types, setTypes] = useState<Record<string, EvidenceTypeChoice>>({});
  const [relationships, setRelationships] = useState<Record<string, RelationshipChoice>>({});
  const [isSaving, setIsSaving] = useState(false);

  const drafts = signals.map((signal) => buildEvidenceDraft(signal));

  // Phase 34G-A §7/§8: SIE never gets to silently decide a result meant
  // nothing just because no regex matched it. When nothing structured
  // was extracted, the founder can classify the raw text themselves, in
  // plain language, using the SAME evidence-type/relationship vocabulary
  // the checkbox flow above already uses -- no new AI system, no
  // additional regex, just a fallback for exactly the gap the raw-note
  // path otherwise leaves silent.
  const [fallbackType, setFallbackType] = useState<EvidenceTypeChoice | null>(null);
  const [fallbackRelationship, setFallbackRelationship] = useState<RelationshipChoice | null>(null);

  async function confirmStructuredFallback() {
    if (!fallbackType || !hasExplicitRelationship(fallbackRelationship)) return;
    setIsSaving(true);
    await onConfirm([toRawTextEvidencePayload(resultText, fallbackType, fallbackRelationship)]);
    setIsSaving(false);
  }

  // Phase 34D-A: a checked signal is only ready to confirm once the
  // founder has explicitly picked its relationship in `relationships` --
  // never falling back to the signal's polarity-implied default. This is
  // the direct fix for the incident where a result got saved as "neutral"
  // without anyone choosing that.
  const checkedIds = [...checked];
  const unclassifiedCheckedIds = checkedIds.filter((id) => !hasExplicitRelationship(relationships[id]));
  const readyToConfirm = allCheckedItemsHaveRelationship(checkedIds, relationships);

  function toggle(id: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function confirmSelected() {
    if (!readyToConfirm) return;
    setIsSaving(true);
    const payloads = drafts
      .filter((d) => checked.has(d.signal.id))
      .map((d) => {
        const relationship = relationships[d.signal.id];
        // Guarded by readyToConfirm above; this branch is unreachable in
        // practice but keeps the map total without a non-null assertion.
        if (!hasExplicitRelationship(relationship)) return null;
        return toCreateEvidencePayload({ ...d, evidenceType: types[d.signal.id] ?? d.evidenceType, relationship });
      })
      .filter((p): p is ReturnType<typeof toCreateEvidencePayload> => p !== null);
    await onConfirm(payloads);
    setIsSaving(false);
  }

  async function confirmRawTextOnly() {
    // §2: the raw-note path is exempt from relationship classification
    // entirely -- it is not confirmed, classified evidence.
    setIsSaving(true);
    await onConfirm([toRawTextEvidencePayload(resultText, "founder_claim")]);
    setIsSaving(false);
  }

  if (signals.length === 0) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-text-secondary">
          SIE didn&rsquo;t recognize a specific result in what you wrote -- that&rsquo;s fine, but it also means
          nothing here will change what SIE recommends next unless you classify it yourself below.
        </p>
        <div className="space-y-2 rounded-lg border border-border bg-surface p-3">
          <p className="text-sm font-medium text-text-secondary">What did this result show?</p>
          <select
            value={fallbackType ?? ""}
            onChange={(event) => setFallbackType(event.target.value as EvidenceTypeChoice)}
            className="h-9 w-full rounded-md border border-border bg-background px-2.5 text-sm text-text-primary"
          >
            <option value="" disabled>
              Choose the closest match…
            </option>
            {Object.entries(EVIDENCE_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          {fallbackType ? <RelationshipPicker value={fallbackRelationship} onChange={setFallbackRelationship} /> : null}
          <Button
            type="button"
            size="sm"
            disabled={isSaving || !fallbackType || !hasExplicitRelationship(fallbackRelationship)}
            loading={isSaving}
            onClick={confirmStructuredFallback}
          >
            Classify and save
          </Button>
        </div>
        <Button type="button" variant="subtle" size="sm" disabled={isSaving} loading={isSaving} onClick={confirmRawTextOnly}>
          Just save the note as unclassified text
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What we found</p>
      <ul className="space-y-2">
        {drafts.map((draft) => (
          <li key={draft.signal.id} className="rounded-lg border border-border bg-surface p-3">
            <label className="flex items-start gap-2.5">
              <input
                type="checkbox"
                checked={checked.has(draft.signal.id)}
                onChange={() => toggle(draft.signal.id)}
                className="mt-0.5 size-4 shrink-0 accent-primary"
              />
              <span className="min-w-0">
                <span className="block text-sm font-medium text-text-primary">{draft.signal.label}</span>
                <span className="mt-0.5 block text-xs text-text-muted">from: &ldquo;{draft.signal.sourceQuote}&rdquo;</span>
              </span>
            </label>
            {checked.has(draft.signal.id) ? (
              <div className="mt-2 ml-6 space-y-2">
                <select
                  value={types[draft.signal.id] ?? draft.evidenceType}
                  onChange={(event) => setTypes((prev) => ({ ...prev, [draft.signal.id]: event.target.value as EvidenceTypeChoice }))}
                  className="h-8 rounded-md border border-border bg-background px-2 text-xs text-text-primary"
                >
                  {Object.entries(EVIDENCE_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                {/* Phase 34D-A: no pre-selection -- see RelationshipPicker's
                    own comment for why. */}
                <RelationshipPicker
                  value={relationships[draft.signal.id] ?? null}
                  onChange={(choice) => setRelationships((prev) => ({ ...prev, [draft.signal.id]: choice }))}
                  prompt="How does this affect what we were testing?"
                />
              </div>
            ) : null}
          </li>
        ))}
      </ul>
      {checked.size > 0 && unclassifiedCheckedIds.length > 0 ? (
        <p className="text-xs text-warning">
          Choose how each highlighted result affects what we were testing before confirming.
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={isSaving || !readyToConfirm} loading={isSaving} onClick={confirmSelected}>
          Confirm selected
        </Button>
        <Button type="button" variant="subtle" size="sm" disabled={isSaving} onClick={confirmRawTextOnly}>
          Just save the raw note
        </Button>
      </div>
    </div>
  );
}
