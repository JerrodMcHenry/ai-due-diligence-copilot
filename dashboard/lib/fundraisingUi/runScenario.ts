// Phase 21B -- Fundraising Simulator V1, core orchestrator.
//
// The ONLY place UI input is turned into Phase 21A engine calls. This
// function computes nothing itself: every ownership, dilution, SAFE, or
// runway number comes from dashboard/lib/fundraising/*.ts (frozen,
// Phase 21A). This file's job is unit conversion in, founder-readable
// formatting out, plus the UI-specific decisions the engine deliberately
// leaves to its caller: which path to run, when a result is an estimate
// rather than a final cap table (Part 18), and when a result must be
// BLOCKED rather than shown (Part 9).

import { buildStartingCapTable, validateOwnershipPercentages } from "./startingCapTable.ts";
import { dollarsToCents } from "./formatUi.ts";
import type { OwnershipRow, ScenarioBlocked, ScenarioInput, ScenarioInvalid, ScenarioResult, ScenarioSuccess, StakeholderRole, TraceStep } from "./types.ts";

import { ownershipBreakdown, totalShares } from "../fundraising/capTable.ts";
import { estimateStandaloneSafeOwnership } from "../fundraising/safe.ts";
import { runSafeConversionAndPricedRound, runSimplePricedRound } from "../fundraising/pricedRound.ts";
import { computeRunway } from "../fundraising/runway.ts";
import { FinancingError } from "../fundraising/errors.ts";
import { type Rational, RAT_ZERO, makeRational, ratSub, ratDiv, toPercentString, toDecimalString, centsToDollarString } from "../fundraising/rational.ts";
import type { CapTableState, SafeInput, PricedRoundInput } from "../fundraising/types.ts";
import type { OwnershipRow as EngineOwnershipRow } from "../fundraising/capTable.ts";

function invalid(message: string): ScenarioInvalid {
  return { kind: "invalid", message };
}

function toEngineOwnershipRows(state: CapTableState): EngineOwnershipRow[] {
  return ownershipBreakdown(state);
}

// Price-per-share is tracked internally in CENTS (see pricedRound.ts) --
// this is the one place it's translated into a founder-readable dollar
// string, via exact Rational division (never a floating-point `number`).
function formatPricePerShareDollars(pricePerShareCents: Rational): string {
  return `$${toDecimalString(ratDiv(pricePerShareCents, makeRational(BigInt(100))), 2)}`;
}

function buildOwnershipRows(
  before: CapTableState | null,
  after: CapTableState,
  uiRoleById: Map<string, StakeholderRole>
): OwnershipRow[] {
  const beforeRows = before ? toEngineOwnershipRows(before) : [];
  const afterRows = toEngineOwnershipRows(after);
  const beforeById = new Map(beforeRows.map((r) => [r.id, r]));

  return afterRows.map((row) => {
    const beforeRow = beforeById.get(row.id);
    const role: StakeholderRole | "safe" | "investor" =
      row.kind === "safe" ? "safe" : row.kind === "investor" ? "investor" : uiRoleById.get(row.id) ?? (row.kind as StakeholderRole);

    if (!beforeRow) {
      // Two different cases collapse into "no beforeRow found," and they
      // must render differently: (1) `before` is null entirely -- this
      // call is building a STARTING snapshot (e.g. the "Before" side of
      // the visualization), where every row simply IS the state, with no
      // separate prior state to compare against, so beforePercent must
      // equal the row's own value, not "--" (a live-browser walkthrough
      // caught this: the "Before" ownership bar rendered completely
      // empty, and the "Founder ownership" headline read "-- -> 90%"
      // instead of "100% -> 90%", because both read .beforePercent from a
      // startingOwnership row built this way). (2) `before` is a real
      // prior CapTableState but THIS stakeholder didn't exist in it (a
      // new SAFE or round investor) -- there beforePercent correctly
      // stays "--", since that stakeholder genuinely owned nothing before.
      const isStartingSnapshot = before === null;
      return {
        id: row.id,
        name: row.name,
        role,
        beforePercent: isStartingSnapshot ? toPercentString(row.ownership) : "—",
        afterPercent: toPercentString(row.ownership),
        pointChange: null,
        percentDilution: null,
      };
    }

    const pointChange = ratSub(row.ownership, beforeRow.ownership);
    const percentDilution = beforeRow.ownership.num === BigInt(0) ? null : ratDiv(ratSub(beforeRow.ownership, row.ownership), beforeRow.ownership);

    return {
      id: row.id,
      name: row.name,
      role,
      beforePercent: toPercentString(beforeRow.ownership),
      afterPercent: toPercentString(row.ownership),
      pointChange: toPercentString(pointChange),
      percentDilution: percentDilution ? toPercentString(percentDilution) : null,
    };
  });
}

// Aggregate founder dilution (Part 11's headline number): sums ALL rows
// the founder tagged "founder" or "cofounder" in the starting cap table,
// then computes ONE combined percentage-point change and percentage
// dilution -- computed from combined share counts via exact Rational
// arithmetic (never by averaging or summing the individual per-row
// percentages, which would not be mathematically meaningful).
function aggregateFounderDilution(
  before: CapTableState,
  after: CapTableState,
  founderIds: string[]
): { pointChange: string; percentDilution: string } | null {
  if (founderIds.length === 0) return null;

  const beforeTotal = totalShares(before);
  const afterTotal = totalShares(after);
  if (beforeTotal === BigInt(0) || afterTotal === BigInt(0)) return null;

  const founderSharesBefore = before.stakeholders.filter((s) => founderIds.includes(s.id)).reduce((sum, s) => sum + s.shares, BigInt(0));
  const founderSharesAfter = after.stakeholders.filter((s) => founderIds.includes(s.id)).reduce((sum, s) => sum + s.shares, BigInt(0));

  const beforeOwnership = makeRational(founderSharesBefore, beforeTotal);
  const afterOwnership = makeRational(founderSharesAfter, afterTotal);
  const pointChange = ratSub(afterOwnership, beforeOwnership);
  const percentDilution = beforeOwnership.num === BigInt(0) ? RAT_ZERO : ratDiv(ratSub(beforeOwnership, afterOwnership), beforeOwnership);

  return { pointChange: toPercentString(pointChange), percentDilution: toPercentString(percentDilution) };
}

function buildDetailedCapTable(state: CapTableState) {
  return toEngineOwnershipRows(state).map((row) => ({
    name: row.name,
    shares: row.shares.toLocaleString("en-US"),
    ownership: toPercentString(row.ownership),
  }));
}

function buildRunway(input: ScenarioInput["runway"], capitalRaisedCents: bigint): ScenarioSuccess["runway"] {
  if (!input) return null;

  const note = "Assumes monthly burn remains constant. This is not a forecast of future spending.";

  if (input.cashOnHandDollars === null || input.monthlyBurnDollars === null) {
    return {
      currentLabel: "Runway not modeled",
      postFinancingLabel: "Runway not modeled",
      note: "Add your current cash on hand and monthly burn to see modeled runway.",
    };
  }

  const cashCents = dollarsToCents(input.cashOnHandDollars);
  const burnCents = dollarsToCents(input.monthlyBurnDollars);

  const current = computeRunway({ cashOnHandCents: cashCents, monthlyBurnCents: burnCents });
  const post = computeRunway({ cashOnHandCents: cashCents + capitalRaisedCents, monthlyBurnCents: burnCents });

  return {
    currentLabel: current.isInfinite ? "No burn modeled" : `${toDecimalString(current.runwayMonths!, 1)} months (approx.)`,
    postFinancingLabel: post.isInfinite ? "No burn modeled" : `${toDecimalString(post.runwayMonths!, 1)} months (approx.)`,
    note,
  };
}

function buildSafeInputs(uiSafes: ScenarioInput["safes"]): SafeInput[] {
  return uiSafes.map((s) => ({
    id: s.id,
    holderName: s.holderName || "SAFE Investor",
    investmentCents: dollarsToCents(s.investmentDollars),
    valuationCapCents: dollarsToCents(s.valuationCapDollars),
    discountPercent: null,
  }));
}

function buildRoundInput(round: NonNullable<ScenarioInput["pricedRound"]>, optionPoolIncreaseShares: bigint): PricedRoundInput {
  return {
    id: "round",
    name: round.name || "Priced Round",
    preMoneyValuationCents: dollarsToCents(round.preMoneyDollars),
    newMoneyCents: dollarsToCents(round.newMoneyDollars),
    optionPoolIncreaseShares,
    newInvestorName: round.newInvestorName || "New Investor",
  };
}

export function runScenario(input: ScenarioInput): ScenarioResult {
  const percentError = validateOwnershipPercentages(input.startingStakeholders);
  if (percentError) return invalid(percentError);

  const uiRoleById = new Map(input.startingStakeholders.map((s) => [s.id, s.role]));
  const founderIds = input.startingStakeholders.filter((s) => s.role === "founder" || s.role === "cofounder").map((s) => s.id);

  let startingState: CapTableState;
  try {
    startingState = buildStartingCapTable("Today", input.startingStakeholders);
  } catch (e) {
    return invalid(e instanceof FinancingError ? e.message : "Could not build a starting cap table from these percentages.");
  }

  try {
    if (input.path === "safe") {
      if (input.safes.length === 0) return invalid("Add at least one SAFE to simulate.");
      const safeInputs = buildSafeInputs(input.safes);
      const conversion = estimateStandaloneSafeOwnership(startingState, safeInputs);

      // Part 18: this is an ESTIMATE of what today's SAFE(s) would be
      // worth if they converted right now -- not a final cap table. Build
      // a synthetic post-state purely for display, clearly labeled.
      const estimatedState: CapTableState = {
        label: "If converted today (estimate)",
        stakeholders: [
          ...startingState.stakeholders,
          ...conversion.safeDetails.map((d) => ({ id: d.safeId, name: d.holderName, kind: "safe" as const, shares: d.conversionShares })),
        ],
      };

      const capitalRaisedCents = safeInputs.reduce((sum, s) => sum + s.investmentCents, BigInt(0));
      const trace: TraceStep[] = [
        { label: "Starting capitalization", detail: `${totalShares(startingState).toLocaleString("en-US")} shares before any SAFE.` },
        ...conversion.safeDetails.map((d) => ({
          label: `${d.holderName}'s SAFE, estimated`,
          detail: `${centsToDollarString(d.investmentCents)} invested at a ${centsToDollarString(d.valuationCapCents)} valuation cap implies roughly ${toPercentString(d.capImpliedOwnership)} ownership if it converted today.`,
        })),
        { label: "Estimated capitalization if converted today", detail: `${totalShares(estimatedState).toLocaleString("en-US")} shares.` },
      ];

      return {
        kind: "success",
        isEstimateOnly: true,
        startingOwnership: buildOwnershipRows(null, startingState, uiRoleById),
        finalOwnership: buildOwnershipRows(startingState, estimatedState, uiRoleById),
        capitalRaisedLabel: centsToDollarString(capitalRaisedCents),
        founderDilution: aggregateFounderDilution(startingState, estimatedState, founderIds),
        trace,
        detailedCapTable: buildDetailedCapTable(estimatedState),
        runway: buildRunway(input.runway, capitalRaisedCents),
        warnings: [],
      };
    }

    if (input.path === "priced_round") {
      if (!input.pricedRound) return invalid("Enter the priced round's terms to simulate.");
      const currentTotal = totalShares(startingState);
      const poolIncreaseShares = BigInt(Math.round((Number(currentTotal) * input.optionPoolIncreasePercentOfCurrent) / 100));
      const round = buildRoundInput(input.pricedRound, poolIncreaseShares);
      const result = runSimplePricedRound(startingState, round);

      const capitalRaisedCents = round.newMoneyCents;
      const trace: TraceStep[] = [
        { label: "Starting capitalization", detail: `${startingState.stakeholders.length} stakeholder(s), ${currentTotal.toLocaleString("en-US")} shares.` },
        poolIncreaseShares > BigInt(0)
          ? { label: "Option pool adjustment", detail: `${poolIncreaseShares.toLocaleString("en-US")} new option pool shares added before pricing this round.` }
          : null,
        { label: `${round.name} share issuance`, detail: `Priced at ${formatPricePerShareDollars(result.pricePerShare)} per share; ${result.newInvestorShares.toLocaleString("en-US")} new shares issued to ${round.newInvestorName}.` },
        { label: "Final capitalization", detail: `${result.newTotalShares.toLocaleString("en-US")} shares.` },
      ].filter((step): step is TraceStep => step !== null);

      return {
        kind: "success",
        isEstimateOnly: false,
        startingOwnership: buildOwnershipRows(null, startingState, uiRoleById),
        finalOwnership: buildOwnershipRows(startingState, result.postRoundState, uiRoleById),
        capitalRaisedLabel: centsToDollarString(capitalRaisedCents),
        founderDilution: aggregateFounderDilution(startingState, result.postRoundState, founderIds),
        trace,
        detailedCapTable: buildDetailedCapTable(result.postRoundState),
        runway: buildRunway(input.runway, capitalRaisedCents),
        warnings: [],
      };
    }

    // "safe_then_round"
    if (!input.pricedRound) return invalid("Enter the triggering round's terms to simulate SAFE conversion.");
    if (input.safes.length === 0) return invalid("Add at least one SAFE to simulate SAFE → priced round.");

    const safeInputs = buildSafeInputs(input.safes);
    const currentTotal = totalShares(startingState);
    const poolIncreaseShares = BigInt(Math.round((Number(currentTotal) * input.optionPoolIncreasePercentOfCurrent) / 100));
    const round = buildRoundInput(input.pricedRound, poolIncreaseShares);

    const result = runSafeConversionAndPricedRound(startingState, safeInputs, round);

    // Part 9: an untrustworthy result must never be presented as
    // authoritative -- block it outright rather than showing numbers.
    if (result.priceWarnings.length > 0) {
      const blocked: ScenarioBlocked = {
        kind: "blocked",
        reason:
          "This scenario includes a SAFE conversion case that Fundraising Simulator V1 does not yet model completely. No ownership result is shown.",
        warnings: [...result.priceWarnings],
      };
      return blocked;
    }

    const capitalRaisedCents = safeInputs.reduce((sum, s) => sum + s.investmentCents, BigInt(0)) + round.newMoneyCents;
    const trace: TraceStep[] = [
      { label: "Starting capitalization", detail: `${currentTotal.toLocaleString("en-US")} shares before any SAFE.` },
      ...result.safeConversion.safeDetails.map((d) => ({
        label: `${d.holderName}'s SAFE conversion`,
        detail: `Converts into ${d.conversionShares.toLocaleString("en-US")} shares (${toPercentString(d.capImpliedOwnership)} implied by its cap).`,
      })),
      poolIncreaseShares > BigInt(0)
        ? { label: "Option pool adjustment", detail: `${poolIncreaseShares.toLocaleString("en-US")} new option pool shares added as part of this round -- this dilutes existing shareholders, not the converting SAFE(s).` }
        : null,
      { label: `${round.name} share issuance`, detail: `${result.newInvestorShares.toLocaleString("en-US")} new shares issued to ${round.newInvestorName}.` },
      { label: "Final capitalization", detail: `${totalShares(result.postRoundState).toLocaleString("en-US")} shares.` },
    ].filter((step): step is TraceStep => step !== null);

    return {
      kind: "success",
      isEstimateOnly: false,
      startingOwnership: buildOwnershipRows(null, startingState, uiRoleById),
      finalOwnership: buildOwnershipRows(startingState, result.postRoundState, uiRoleById),
      capitalRaisedLabel: centsToDollarString(capitalRaisedCents),
      founderDilution: aggregateFounderDilution(startingState, result.postRoundState, founderIds),
      trace,
      detailedCapTable: buildDetailedCapTable(result.postRoundState),
      runway: buildRunway(input.runway, capitalRaisedCents),
      warnings: [],
    };
  } catch (e) {
    if (e instanceof FinancingError) return invalid(e.message);
    throw e;
  }
}
