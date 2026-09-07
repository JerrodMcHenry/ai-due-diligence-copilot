"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { createVentureFinancialSnapshot, createHirePlan, getVentureFinancials, previewHirePlan, updateHirePlan } from "@/lib/api";
import { dollarsToCents, centsToDollars, formatWholeDollars, formatMonthYear } from "@/lib/finance/money";

import type {
  CreateFinancialSnapshotRequest,
  CreateHirePlanRequest,
  DerivedFinancialMetrics,
  EmploymentType,
  FinancialSnapshot,
  HireImpactPreview,
  HirePlan,
  ProjectedMonth,
  ProjectedMonthWithPlan,
  VentureFinancialsResponse,
} from "@/types";

// Phase 35B -- Financial State Persistence + Runway Engine V1. The
// foundational Finance surface inside the Venture workspace -- see
// docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md for the full design.
//
// Deliberately small: no hiring, no scenarios, no fundraising-persistence
// here (§24 of the directive) -- this is ONLY actual financial state,
// deterministic burn/runway, and a bounded monthly projection. The
// existing Fundraising tab/experience (FundraisingSimulator.tsx) is
// completely untouched and lives in its own tab, not reorganized under
// this one (§18/§19: foundation first, no premature IA merge).
//
// Plain-language throughout -- "unknown" vs. "explicit zero," "modeled,
// not predicted" -- never internal vocabulary ("snapshot," "derived
// metrics," "provenance") in founder-facing copy, only in code comments.

type Props = { ventureId: number };
type LoadState = "loading" | "ready" | "error";

const STATUS_COPY: Record<DerivedFinancialMetrics["status"], { label: string; tone: "default" | "positive" | "warning" | "danger" }> = {
  insufficient_data: { label: "Add more numbers to calculate burn and runway", tone: "default" },
  cash_flow_positive: { label: "Cash-flow positive at the current snapshot", tone: "positive" },
  break_even: { label: "Break-even at the current snapshot", tone: "default" },
  burning: { label: "", tone: "warning" }, // runway_months renders the actual number instead
  out_of_cash: { label: "Out of cash at the current snapshot", tone: "danger" },
};

export default function FinanceOverview({ ventureId }: Props) {
  const { getToken } = useAuth();
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [data, setData] = useState<VentureFinancialsResponse | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Phase 35C: closed | adding a new hire | editing an existing one.
  // Deliberately separate from `isEditing` (the snapshot form) -- only
  // one panel is ever open at a time, but they are orthogonal concerns.
  const [hirePanel, setHirePanel] = useState<{ mode: "closed" } | { mode: "add" } | { mode: "edit"; hire: HirePlan }>({ mode: "closed" });

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    try {
      const result = await getVentureFinancials(ventureId, token);
      setData(result);
      setLoadState("ready");
    } catch (err) {
      console.error("Failed to load Finance:", err);
      setLoadState("error");
    }
  }, [ventureId, getToken]);

  useEffect(() => {
    Promise.resolve().then(() => {
      refresh();
    });
  }, [refresh]);

  async function handleSave(request: CreateFinancialSnapshotRequest) {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("Your session expired. Sign in again.");
      return;
    }
    try {
      const result = await createVentureFinancialSnapshot(ventureId, request, token);
      setData(result);
      setIsEditing(false);
    } catch (err) {
      console.error(err);
      setError("Something went wrong saving these numbers. Try again.");
    }
  }

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

  async function handlePreviewHire(request: CreateHirePlanRequest, excludeId?: number): Promise<HireImpactPreview | null> {
    return withToken((token) => previewHirePlan(ventureId, request, token, excludeId));
  }

  async function handleSaveHire(request: CreateHirePlanRequest) {
    const result = await withToken(async (token) => {
      if (hirePanel.mode === "edit") {
        await updateHirePlan(ventureId, hirePanel.hire.id, request, token);
      } else {
        await createHirePlan(ventureId, request, token);
      }
      return getVentureFinancials(ventureId, token);
    });
    if (result) {
      setData(result);
      setHirePanel({ mode: "closed" });
    }
  }

  async function handleHireStatusChange(hire: HirePlan, status: "cancelled" | "actualized") {
    const result = await withToken(async (token) => {
      await updateHirePlan(ventureId, hire.id, { status }, token);
      return getVentureFinancials(ventureId, token);
    });
    if (result) setData(result);
  }

  if (loadState === "loading") {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (loadState === "error") {
    return (
      <BaseCard className="p-5">
        <p className="text-sm text-danger">Couldn&rsquo;t load Finance. Try refreshing the page.</p>
      </BaseCard>
    );
  }

  if (isEditing) {
    return (
      <BaseCard className="space-y-4 p-6 sm:p-7">
        <SnapshotForm existing={data?.latest_snapshot ?? null} onCancel={() => setIsEditing(false)} onSave={handleSave} />
        {error ? <p className="text-sm text-danger">{error}</p> : null}
      </BaseCard>
    );
  }

  if (hirePanel.mode !== "closed") {
    return (
      <BaseCard className="space-y-4 p-6 sm:p-7">
        <HireForm
          existing={hirePanel.mode === "edit" ? hirePanel.hire : null}
          hasFinancialSnapshot={Boolean(data?.latest_snapshot)}
          currentRunwayLabel={data?.derived ? runwayLabel(data.derived) : "—"}
          onPreview={handlePreviewHire}
          onSave={handleSaveHire}
          onCancel={() => setHirePanel({ mode: "closed" })}
        />
        {error ? <p className="text-sm text-danger">{error}</p> : null}
      </BaseCard>
    );
  }

  if (!data?.latest_snapshot || !data.derived) {
    return (
      <BaseCard className="space-y-3 p-6 sm:p-7 text-center">
        <h2 className="text-xl font-bold text-text-primary">Finance</h2>
        <p className="mx-auto max-w-md text-base leading-7 text-text-secondary">
          Add your current cash, revenue, and monthly spending to calculate burn and runway.
        </p>
        <Button type="button" onClick={() => setIsEditing(true)}>
          Add financial snapshot
        </Button>
      </BaseCard>
    );
  }

  return (
    <BaseCard className="space-y-6 p-6 sm:p-7">
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-xl font-bold text-text-primary">Finance</h2>
        <p className="text-xs text-text-muted">As of {formatMonthYear(data.latest_snapshot.as_of_date)}</p>
      </div>

      {error ? <p className="text-sm text-danger">{error}</p> : null}

      <HeadlineMetrics snapshot={data.latest_snapshot} derived={data.derived} />

      <CurrentSnapshotBreakdown snapshot={data.latest_snapshot} />

      <PlannedChangesSection
        hirePlans={data.hire_plans}
        onAddHire={() => setHirePanel({ mode: "add" })}
        onEditHire={(hire) => setHirePanel({ mode: "edit", hire })}
        onCancelHire={(hire) => handleHireStatusChange(hire, "cancelled")}
        onActualizeHire={(hire) => handleHireStatusChange(hire, "actualized")}
      />

      {data.projection.length > 0 ? (
        <CashOutlook projection={data.projection} projectionWithPlan={data.projection_with_plan} status={data.derived.status} />
      ) : null}

      <div>
        <Button type="button" variant="secondary" onClick={() => setIsEditing(true)}>
          Update cash &amp; monthly finances
        </Button>
        <p className="mt-1.5 text-sm leading-6 text-text-secondary">
          Keep these numbers current so SIE can calculate your burn, runway, and future financial scenarios.
        </p>
      </div>
    </BaseCard>
  );
}

// --- Headline: cash / revenue / spend / burn / runway -----------------------

function runwayLabel(derived: DerivedFinancialMetrics): string {
  if (derived.status === "burning" && derived.runway_months !== null) return `${derived.runway_months} months`;
  if (derived.status === "out_of_cash") return "0 months";
  return "—";
}

function HeadlineMetrics({ snapshot, derived }: { snapshot: FinancialSnapshot; derived: DerivedFinancialMetrics }) {
  const runwayValue = runwayLabel(derived);

  const items: { label: string; value: string }[] = [
    { label: "Cash", value: snapshot.cash_balance_cents !== null ? formatWholeDollars(snapshot.cash_balance_cents) : "Unknown" },
    { label: "Monthly revenue", value: derived.total_monthly_revenue_cents !== null ? formatWholeDollars(derived.total_monthly_revenue_cents) : "Unknown" },
    { label: "Monthly spend", value: derived.total_monthly_expenses_cents !== null ? formatWholeDollars(derived.total_monthly_expenses_cents) : "Unknown" },
    {
      label: "Net burn",
      value:
        derived.net_burn_cents === null
          ? "Unknown"
          : derived.net_burn_cents <= 0
            ? `+${formatWholeDollars(Math.abs(derived.net_burn_cents))}/mo`
            : `${formatWholeDollars(derived.net_burn_cents)}/mo`,
    },
    { label: "Runway", value: runwayValue },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-5">
        {items.map((item) => (
          <div key={item.label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{item.label}</p>
            <p className="mt-1 text-lg font-bold text-text-primary">{item.value}</p>
          </div>
        ))}
      </div>
      {STATUS_COPY[derived.status].label ? (
        <p className="mt-3 text-sm leading-6 text-text-secondary">{STATUS_COPY[derived.status].label}.</p>
      ) : null}
    </div>
  );
}

// --- Current monthly snapshot (where spending comes from) -------------------

const EXPENSE_ROWS: { key: keyof FinancialSnapshot; label: string }[] = [
  { key: "payroll_cents", label: "Payroll" },
  { key: "contractors_cents", label: "Contractors" },
  { key: "software_cents", label: "Software" },
  { key: "marketing_cents", label: "Marketing" },
  { key: "rent_cents", label: "Rent" },
  { key: "professional_services_cents", label: "Professional services" },
  { key: "other_expenses_cents", label: "Other" },
];

function CurrentSnapshotBreakdown({ snapshot }: { snapshot: FinancialSnapshot }) {
  const revenueRows = [
    { label: "Recurring revenue", cents: snapshot.monthly_recurring_revenue_cents },
    { label: "Other monthly revenue", cents: snapshot.monthly_non_recurring_revenue_cents },
  ].filter((r) => r.cents !== null);

  const expenseRows = EXPENSE_ROWS.map((r) => ({ label: r.label, cents: snapshot[r.key] as number | null })).filter((r) => r.cents !== null);

  if (revenueRows.length === 0 && expenseRows.length === 0) return null;

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Current monthly snapshot</p>
      <div className="mt-2 grid gap-x-8 gap-y-4 sm:grid-cols-2">
        {revenueRows.length > 0 ? (
          <ul className="space-y-1.5">
            {revenueRows.map((r) => (
              <li key={r.label} className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">{r.label}</span>
                <span className="font-medium text-text-primary">{formatWholeDollars(r.cents!)}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {expenseRows.length > 0 ? (
          <ul className="space-y-1.5">
            {expenseRows.map((r) => (
              <li key={r.label} className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">{r.label}</span>
                <span className="font-medium text-text-primary">{formatWholeDollars(r.cents!)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

// --- Cash outlook: bounded, readable projection summary ---------------------

function CashOutlook({
  projection,
  projectionWithPlan,
  status,
}: {
  projection: ProjectedMonth[];
  projectionWithPlan: ProjectedMonthWithPlan[];
  status: DerivedFinancialMetrics["status"];
}) {
  // Phase 35C: only show a second "with planned changes" column when a
  // planned hire is actually active somewhere in the horizon -- a
  // venture with no plans must look EXACTLY like Phase 35B's own single-
  // column table, no visual complexity added for nothing.
  const hasActivePlan = projectionWithPlan.some((m) => m.plan_expense_impact_cents > 0);

  // The two series can have DIFFERENT LENGTHS -- a plan that costs more
  // depletes cash sooner and its own array simply stops there, shorter
  // than the baseline's. Rows are merged by month_index (both series
  // share the same as_of_date/cadence), never by raw array position,
  // and a side that already depleted before this row shows $0 rather
  // than reading past the end of its own (shorter) array.
  const visible = projection.slice(0, 12);
  const visibleWithPlan = projectionWithPlan.slice(0, 12);
  const rowCount = Math.max(visible.length, hasActivePlan ? visibleWithPlan.length : 0);
  const withPlanByIndex = new Map(projectionWithPlan.map((m) => [m.month_index, m]));
  const remaining = projection.length - visible.length;
  const depletionMonth = projection.find((m) => m.depleted);
  const depletionWithPlan = projectionWithPlan.find((m) => m.depleted);

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Cash outlook</p>
      <p className="mt-1 text-sm leading-6 text-text-secondary">
        {status === "cash_flow_positive"
          ? "Based on your current monthly snapshot. If these numbers stayed unchanged, cash would keep growing."
          : "Based on your current monthly snapshot. If these numbers stayed unchanged, this is what happens next -- not a prediction."}
        {hasActivePlan ? " \"With planned changes\" includes the hires below." : ""}
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              <th className="py-1 pr-3">Month</th>
              <th className="py-1 text-right">{hasActivePlan ? "Current trajectory" : "Ending cash"}</th>
              {hasActivePlan ? <th className="py-1 pl-3 text-right">With planned changes</th> : null}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rowCount }, (_, i) => {
              const monthIndex = i + 1;
              const base = visible[i];
              const withPlan = withPlanByIndex.get(monthIndex);
              // A side with no row for this month has already depleted
              // in an earlier row -- carry $0 forward rather than
              // reading past the end of its own (shorter) array.
              const label = base ? formatMonthYear(base.date) : withPlan ? formatMonthYear(withPlan.date) : "";
              return (
                <tr key={monthIndex} className="border-t border-border">
                  <td className="py-1.5 pr-3 text-text-secondary">{label}</td>
                  <td className="py-1.5 text-right font-medium text-text-primary">
                    {formatWholeDollars(base ? base.ending_cash_cents : 0)}
                    {base?.depleted ? <span className="ml-1.5 text-xs font-semibold text-danger">$0</span> : null}
                  </td>
                  {hasActivePlan ? (
                    <td className="py-1.5 pl-3 text-right font-medium text-text-primary">
                      {formatWholeDollars(withPlan ? withPlan.ending_cash_cents : 0)}
                      {withPlan?.depleted ? <span className="ml-1.5 text-xs font-semibold text-danger">$0</span> : null}
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {remaining > 0 && !depletionMonth && !(hasActivePlan && depletionWithPlan) ? (
        <p className="mt-2 text-xs text-text-muted">Continues growing steadily beyond month {visible.length} at this rate.</p>
      ) : null}
    </div>
  );
}

// --- Phase 35C -- planned changes (hire plans) -------------------------------

function hireCostLabel(hire: HirePlan): string {
  if (hire.computed_monthly_cost_cents === null) return "—";
  return `${formatWholeDollars(hire.computed_monthly_cost_cents)}/mo`;
}

function PlannedChangesSection({
  hirePlans,
  onAddHire,
  onEditHire,
  onCancelHire,
  onActualizeHire,
}: {
  hirePlans: HirePlan[];
  onAddHire: () => void;
  onEditHire: (hire: HirePlan) => void;
  onCancelHire: (hire: HirePlan) => void;
  onActualizeHire: (hire: HirePlan) => void;
}) {
  // Only actively-planned hires are shown -- a cancelled/actualized one
  // is still safely persisted (§18: never hard-deleted) but this is
  // deliberately not a full history UI (§13 of the directive).
  const active = hirePlans.filter((h) => h.status === "planned");

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Planned changes</p>
      {active.length > 0 ? (
        <ul className="mt-2 space-y-2">
          {active.map((hire) => (
            <li key={hire.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-surface p-3">
              <div>
                <p className="text-sm font-medium text-text-primary">{hire.role}</p>
                <p className="text-xs text-text-muted">
                  {hireCostLabel(hire)} starting {formatMonthYear(hire.start_date)}
                  {hire.end_date ? ` through ${formatMonthYear(hire.end_date)}` : ""}
                </p>
              </div>
              <div className="flex flex-wrap gap-3 text-xs">
                <button type="button" onClick={() => onEditHire(hire)} className="font-semibold text-primary hover:text-primary-hover">
                  Edit
                </button>
                <button type="button" onClick={() => onCancelHire(hire)} className="font-semibold text-text-muted hover:text-danger">
                  Cancel
                </button>
                <button type="button" onClick={() => onActualizeHire(hire)} className="font-semibold text-text-muted hover:text-text-primary">
                  Mark as actualized
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm leading-6 text-text-secondary">Nothing planned yet.</p>
      )}
      <Button type="button" variant="secondary" size="sm" className="mt-2" onClick={onAddHire}>
        Model a hire
      </Button>
      <p className="mt-1.5 text-sm leading-6 text-text-secondary">
        See how adding someone to the team would affect monthly spending and your cash runway.
      </p>
    </div>
  );
}

// --- Phase 35C -- model a hire: form -> preview -> save ----------------------

type HireFormValues = {
  role: string;
  employmentType: EmploymentType;
  annualSalary: string;
  burdenPercent: string;
  monthlyCost: string;
  oneTimeCost: string;
  startDate: string;
  endDate: string;
};

function hireToFormValues(hire: HirePlan | null): HireFormValues {
  if (!hire) {
    return { role: "", employmentType: "employee", annualSalary: "", burdenPercent: "", monthlyCost: "", oneTimeCost: "", startDate: "", endDate: "" };
  }
  return {
    role: hire.role,
    employmentType: hire.employment_type,
    annualSalary: hire.annual_salary_cents !== null ? String(centsToDollars(hire.annual_salary_cents)) : "",
    burdenPercent: hire.burden_percent !== null ? String(hire.burden_percent) : "",
    monthlyCost: hire.monthly_cost_cents !== null ? String(centsToDollars(hire.monthly_cost_cents)) : "",
    oneTimeCost: hire.one_time_cost_cents !== null ? String(centsToDollars(hire.one_time_cost_cents)) : "",
    startDate: hire.start_date,
    endDate: hire.end_date ?? "",
  };
}

function formValuesToRequest(values: HireFormValues): CreateHirePlanRequest | null {
  if (!values.role.trim() || !values.startDate) return null;
  if (values.employmentType === "employee") {
    if (values.annualSalary.trim() === "" || values.burdenPercent.trim() === "") return null;
    return {
      role: values.role.trim(),
      employment_type: "employee",
      annual_salary_cents: dollarsToCents(Number(values.annualSalary)),
      burden_percent: Number(values.burdenPercent),
      monthly_cost_cents: null,
      one_time_cost_cents: values.oneTimeCost.trim() === "" ? null : dollarsToCents(Number(values.oneTimeCost)),
      start_date: values.startDate,
      end_date: values.endDate.trim() === "" ? null : values.endDate,
    };
  }
  if (values.monthlyCost.trim() === "") return null;
  return {
    role: values.role.trim(),
    employment_type: "contractor",
    annual_salary_cents: null,
    burden_percent: null,
    monthly_cost_cents: dollarsToCents(Number(values.monthlyCost)),
    one_time_cost_cents: values.oneTimeCost.trim() === "" ? null : dollarsToCents(Number(values.oneTimeCost)),
    start_date: values.startDate,
    end_date: values.endDate.trim() === "" ? null : values.endDate,
  };
}

// The single depletion-month reading a projection ever gets reduced to --
// a DATE (from the projection's own depleted flag), never a fabricated
// fractional "runway months" for a plan with dated changes (§10 of the
// directive: "avoid presenting a fractional runway number if dated
// changes make that number misleading").
function cashOutLabel(projection: ProjectedMonthWithPlan[]): string {
  const depletion = projection.find((m) => m.depleted);
  if (depletion) return `cash reaches $0 around ${formatMonthYear(depletion.date)}`;
  if (projection.length === 0) return "not enough financial data to model";
  return "stays cash-flow positive within the next 24 months";
}

function HireForm({
  existing,
  hasFinancialSnapshot,
  currentRunwayLabel,
  onPreview,
  onSave,
  onCancel,
}: {
  existing: HirePlan | null;
  hasFinancialSnapshot: boolean;
  currentRunwayLabel: string;
  onPreview: (request: CreateHirePlanRequest, excludeId?: number) => Promise<HireImpactPreview | null>;
  onSave: (request: CreateHirePlanRequest) => Promise<void>;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<HireFormValues>(() => hireToFormValues(existing));
  const [preview, setPreview] = useState<HireImpactPreview | null>(null);
  const [compareDate, setCompareDate] = useState("");
  const [comparePreview, setComparePreview] = useState<HireImpactPreview | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  function setValue<K extends keyof HireFormValues>(key: K, value: HireFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
    setPreview(null); // any edit invalidates a shown preview -- never let stale numbers linger
  }

  const request = formValuesToRequest(values);

  if (!hasFinancialSnapshot) {
    return (
      <div className="space-y-3">
        <h2 className="text-xl font-bold text-text-primary">Model a hire</h2>
        <p className="text-base leading-7 text-text-secondary">
          We need your current cash and monthly finances before we can model this hire.
        </p>
        <Button type="button" onClick={onCancel}>
          Add financial snapshot
        </Button>
      </div>
    );
  }

  if (preview) {
    const withHireLabel = cashOutLabel(preview.with_hire_projection);
    const baselineLabel = cashOutLabel(preview.baseline_projection);
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold text-text-primary">{values.role || "This hire"}</h2>
          <p className="mt-1 text-sm text-text-secondary">
            {values.employmentType === "employee" ? `${values.annualSalary ? "$" + Number(values.annualSalary).toLocaleString("en-US") : ""} salary, ${values.burdenPercent}% burden` : "Contractor"}
            {" · "}Starts {formatMonthYear(values.startDate)}
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Modeled cost</p>
          <p className="mt-1 text-lg font-bold text-text-primary">
            {preview.computed_monthly_cost_cents !== null ? `${formatWholeDollars(preview.computed_monthly_cost_cents)}/mo` : "—"}
          </p>
          {preview.computed_annual_cost_cents !== null ? (
            <p className="text-sm text-text-secondary">{formatWholeDollars(preview.computed_annual_cost_cents)}/year fully loaded</p>
          ) : null}
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Financial impact</p>
          <p className="mt-1 text-sm leading-7 text-text-secondary">
            Current runway: <span className="font-medium text-text-primary">{currentRunwayLabel}</span>
            <br />
            Without this hire, {baselineLabel}.
            <br />
            With this hire, <span className="font-medium text-text-primary">{withHireLabel}</span>.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-surface p-3">
          <p className="text-sm font-medium text-text-secondary">Compare a different start date</p>
          <div className="mt-2 flex flex-wrap items-end gap-2">
            <input
              type="date"
              value={compareDate}
              onChange={(event) => setCompareDate(event.target.value)}
              className="h-9 rounded-md border border-border bg-background px-2 text-sm text-text-primary"
            />
            <Button
              type="button"
              size="sm"
              variant="subtle"
              disabled={!compareDate || isBusy}
              onClick={async () => {
                if (!request) return;
                setIsBusy(true);
                const result = await onPreview({ ...request, start_date: compareDate }, existing?.id);
                setComparePreview(result);
                setIsBusy(false);
              }}
            >
              Compare
            </Button>
          </div>
          {comparePreview ? (
            <p className="mt-2 text-sm leading-6 text-text-secondary">
              Starting {formatMonthYear(values.startDate)} vs. {formatMonthYear(compareDate)}: {withHireLabel} vs. {cashOutLabel(comparePreview.with_hire_projection)}.
            </p>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            disabled={isBusy}
            loading={isBusy}
            onClick={async () => {
              if (!request) return;
              setIsBusy(true);
              await onSave(request);
              setIsBusy(false);
            }}
          >
            Save this plan
          </Button>
          <Button type="button" variant="subtle" disabled={isBusy} onClick={() => setPreview(null)}>
            Back to edit
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-text-primary">Model a hire</h2>
        <p className="mt-1 text-sm leading-6 text-text-secondary">
          See how adding someone to the team would affect monthly spending and your cash runway.
        </p>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-text-secondary">Role</label>
        <input
          type="text"
          value={values.role}
          onChange={(event) => setValue("role", event.target.value)}
          placeholder="e.g. Senior Engineer"
          className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
        />
      </div>

      <div>
        <p className="mb-1.5 text-sm font-medium text-text-secondary">Employee or contractor?</p>
        <div className="flex gap-2">
          {(["employee", "contractor"] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setValue("employmentType", type)}
              className={[
                "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                values.employmentType === type ? "border-primary bg-primary-soft text-primary" : "border-border text-text-secondary hover:border-primary/40",
              ].join(" ")}
            >
              {type === "employee" ? "Employee" : "Contractor"}
            </button>
          ))}
        </div>
      </div>

      {values.employmentType === "employee" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <MoneyField label="Annual salary" value={values.annualSalary} onChange={(v) => setValue("annualSalary", v)} />
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">Benefits &amp; payroll burden</label>
            <div className="relative">
              <input
                type="number"
                inputMode="decimal"
                value={values.burdenPercent}
                onChange={(event) => setValue("burdenPercent", event.target.value)}
                placeholder="e.g. 25"
                className="h-10 w-full rounded-lg border border-border bg-surface pr-8 pl-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
              />
              <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-text-muted">%</span>
            </div>
            <p className="mt-1 text-xs text-text-muted">Your own estimate -- there&rsquo;s no universal default.</p>
          </div>
        </div>
      ) : (
        <MoneyField label="Monthly cost" value={values.monthlyCost} onChange={(v) => setValue("monthlyCost", v)} />
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-text-secondary">Start date</label>
          <input
            type="date"
            value={values.startDate}
            onChange={(event) => setValue("startDate", event.target.value)}
            className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-text-secondary">End date (optional)</label>
          <input
            type="date"
            value={values.endDate}
            onChange={(event) => setValue("endDate", event.target.value)}
            className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
        </div>
      </div>

      <MoneyField label="One-time cost (optional) -- recruiting, equipment, etc." value={values.oneTimeCost} onChange={(v) => setValue("oneTimeCost", v)} />

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          disabled={!request || isBusy}
          loading={isBusy}
          onClick={async () => {
            if (!request) return;
            setIsBusy(true);
            const result = await onPreview(request, existing?.id);
            setPreview(result);
            setComparePreview(null);
            setIsBusy(false);
          }}
        >
          See financial impact
        </Button>
        <Button type="button" variant="subtle" disabled={isBusy} onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

// --- Edit / add snapshot form -------------------------------------------------

type FieldKey =
  | "cash_balance_cents"
  | "monthly_recurring_revenue_cents"
  | "monthly_non_recurring_revenue_cents"
  | "payroll_cents"
  | "contractors_cents"
  | "software_cents"
  | "marketing_cents"
  | "rent_cents"
  | "professional_services_cents"
  | "other_expenses_cents";

// Cash and recurring revenue are the two numbers every founder should
// state explicitly -- no default value, blank means genuinely unknown
// until typed (§15: "unknown is not zero"). Every other field defaults to
// "0" ONLY when there's no prior snapshot to pre-fill from -- a founder
// adding their FIRST snapshot who has no marketing spend, no rent, etc.
// shouldn't have to type "0" into five separate boxes; a founder EDITING
// an existing snapshot always sees their own last-entered values,
// including a genuinely blank field if they left one unknown before.
const NO_DEFAULT_FIELDS: FieldKey[] = ["cash_balance_cents", "monthly_recurring_revenue_cents"];

function centsToInputValue(cents: number | null): string {
  return cents === null ? "" : String(centsToDollars(cents));
}

function inputValueToCents(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? dollarsToCents(parsed) : null;
}

function SnapshotForm({
  existing,
  onCancel,
  onSave,
}: {
  existing: FinancialSnapshot | null;
  onCancel: () => void;
  onSave: (request: CreateFinancialSnapshotRequest) => Promise<void>;
}) {
  const fieldKeys: FieldKey[] = [
    "cash_balance_cents",
    "monthly_recurring_revenue_cents",
    "monthly_non_recurring_revenue_cents",
    "payroll_cents",
    "contractors_cents",
    "software_cents",
    "marketing_cents",
    "rent_cents",
    "professional_services_cents",
    "other_expenses_cents",
  ];

  const [values, setValues] = useState<Record<FieldKey, string>>(() => {
    const initial = {} as Record<FieldKey, string>;
    for (const key of fieldKeys) {
      if (existing) {
        initial[key] = centsToInputValue(existing[key] as number | null);
      } else {
        initial[key] = NO_DEFAULT_FIELDS.includes(key) ? "" : "0";
      }
    }
    return initial;
  });
  const [asOfDate, setAsOfDate] = useState(existing?.as_of_date ?? new Date().toISOString().slice(0, 10));
  const [isSaving, setIsSaving] = useState(false);

  function setValue(key: FieldKey, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit() {
    setIsSaving(true);
    const request: CreateFinancialSnapshotRequest = {
      as_of_date: asOfDate,
      cash_balance_cents: inputValueToCents(values.cash_balance_cents),
      monthly_recurring_revenue_cents: inputValueToCents(values.monthly_recurring_revenue_cents),
      monthly_non_recurring_revenue_cents: inputValueToCents(values.monthly_non_recurring_revenue_cents),
      payroll_cents: inputValueToCents(values.payroll_cents),
      contractors_cents: inputValueToCents(values.contractors_cents),
      software_cents: inputValueToCents(values.software_cents),
      marketing_cents: inputValueToCents(values.marketing_cents),
      rent_cents: inputValueToCents(values.rent_cents),
      professional_services_cents: inputValueToCents(values.professional_services_cents),
      other_expenses_cents: inputValueToCents(values.other_expenses_cents),
    };
    await onSave(request);
    setIsSaving(false);
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-text-primary">Update cash &amp; monthly finances</h2>
        <p className="mt-1 text-sm leading-6 text-text-secondary">
          Keep these numbers current so SIE can calculate your burn, runway, and future financial scenarios. This
          is a decision model, not bookkeeping -- round numbers are fine, and you can leave anything you don&rsquo;t
          know blank.
        </p>
      </div>

      <MoneyField label="Current cash" value={values.cash_balance_cents} onChange={(v) => setValue("cash_balance_cents", v)} />

      <div>
        <p className="mb-2 text-sm font-semibold text-text-primary">Monthly revenue</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <MoneyField label="Recurring revenue" value={values.monthly_recurring_revenue_cents} onChange={(v) => setValue("monthly_recurring_revenue_cents", v)} />
          <MoneyField label="Other monthly revenue" value={values.monthly_non_recurring_revenue_cents} onChange={(v) => setValue("monthly_non_recurring_revenue_cents", v)} />
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-semibold text-text-primary">Monthly spending</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <MoneyField label="Payroll" value={values.payroll_cents} onChange={(v) => setValue("payroll_cents", v)} />
          <MoneyField label="Contractors" value={values.contractors_cents} onChange={(v) => setValue("contractors_cents", v)} />
          <MoneyField label="Software" value={values.software_cents} onChange={(v) => setValue("software_cents", v)} />
          <MoneyField label="Marketing" value={values.marketing_cents} onChange={(v) => setValue("marketing_cents", v)} />
          <MoneyField label="Rent" value={values.rent_cents} onChange={(v) => setValue("rent_cents", v)} />
          <MoneyField label="Professional services" value={values.professional_services_cents} onChange={(v) => setValue("professional_services_cents", v)} />
          <MoneyField label="Other" value={values.other_expenses_cents} onChange={(v) => setValue("other_expenses_cents", v)} />
        </div>
      </div>

      <div className="max-w-[200px]">
        <label htmlFor="finance-as-of-date" className="mb-1 block text-sm font-medium text-text-secondary">
          As of
        </label>
        <input
          id="finance-as-of-date"
          type="date"
          value={asOfDate}
          onChange={(event) => setAsOfDate(event.target.value)}
          className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={isSaving} loading={isSaving} onClick={handleSubmit}>
          {isSaving ? "Saving..." : "Save"}
        </Button>
        <Button type="button" variant="subtle" disabled={isSaving} onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function MoneyField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-text-secondary">{label}</label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-text-muted">$</span>
        <input
          type="number"
          inputMode="decimal"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="0"
          className="h-10 w-full rounded-lg border border-border bg-surface pl-6 pr-3 text-base text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
        />
      </div>
    </div>
  );
}
