"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Badge from "@/components/ui/Badge";
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
} from "@/lib/api";

import type {
  BuildRecommendation,
  CurrentQuestion,
  VentureDecision,
  VentureEvidence,
  VentureMission,
} from "@/types";

// Phase 34D -- SIE Build Intelligence Loop V1.
//
// QUESTION -> TEST -> RESULT -> EVIDENCE -> INTERPRETATION ->
// RECOMMENDATION -> DECISION -> OUTCOME, proven end to end. This is a
// deliberately additive, self-contained surface on the existing Overview
// tab -- it does not replace PrimaryCommandCard, WhereThingsStand, or
// anything else already there (Phase 34D §2/§14's own explicit
// non-goals: no Idea Lab redesign, no navigation change, no removal of
// Model/What-If).
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
};

type LoadState = "loading" | "ready" | "error";

export default function CurrentQuestionCard({ ventureId, ventureName }: Props) {
  const { getToken } = useAuth();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [missions, setMissions] = useState<VentureMission[]>([]);
  const [evidence, setEvidence] = useState<VentureEvidence[]>([]);
  const [decisions, setDecisions] = useState<VentureDecision[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [recommendation, setRecommendation] = useState<BuildRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      setLoadState("ready");
    } catch (err) {
      console.error("Failed to load the current question:", err);
      setLoadState("error");
    }
  }, [ventureId, getToken]);

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
    <BaseCard variant="raised" className="space-y-5 p-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-text-primary">What matters now</h2>
        <Badge tone="info">Build loop</Badge>
      </div>

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
              await createVentureMission(
                ventureId,
                {
                  title: questionText,
                  mission_type: "other",
                  source: "founder_created",
                  question_text: questionText,
                  why_it_matters: whyItMatters || null,
                },
                token
              );
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

// --- Case: nothing active -- recommend the next question --------------------

function RecommendationState({
  ventureName,
  recommendation,
  onStartTest,
  onStartCustomTest,
}: {
  ventureName: string;
  recommendation: BuildRecommendation | null;
  onStartTest: () => Promise<void | null>;
  onStartCustomTest: (questionText: string, whyItMatters: string) => Promise<void | null>;
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
      <div className="space-y-2">
        <p className="text-sm text-text-secondary">Nothing specific was recognized in what you wrote -- that&rsquo;s fine.</p>
        <Button type="button" variant="secondary" size="sm" disabled={isSaving} loading={isSaving} onClick={confirmRawTextOnly}>
          Save this as-is
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
