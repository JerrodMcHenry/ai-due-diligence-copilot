"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { createVentureFinancialSnapshot, getVentureFinancials } from "@/lib/api";
import { dollarsToCents, centsToDollars, formatWholeDollars, formatMonthYear } from "@/lib/finance/money";

import type { CreateFinancialSnapshotRequest, DerivedFinancialMetrics, FinancialSnapshot, VentureFinancialsResponse, ProjectedMonth } from "@/types";

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

      {data.projection.length > 0 ? <CashOutlook projection={data.projection} status={data.derived.status} /> : null}

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

function HeadlineMetrics({ snapshot, derived }: { snapshot: FinancialSnapshot; derived: DerivedFinancialMetrics }) {
  const runwayValue = (() => {
    if (derived.status === "burning" && derived.runway_months !== null) return `${derived.runway_months} months`;
    if (derived.status === "out_of_cash") return "0 months";
    return "—";
  })();

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

function CashOutlook({ projection, status }: { projection: ProjectedMonth[]; status: DerivedFinancialMetrics["status"] }) {
  const visible = projection.slice(0, 12);
  const remaining = projection.length - visible.length;
  const depletionMonth = projection.find((m) => m.depleted);

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Cash outlook</p>
      <p className="mt-1 text-sm leading-6 text-text-secondary">
        {status === "cash_flow_positive"
          ? "Based on your current monthly snapshot. If these numbers stayed unchanged, cash would keep growing."
          : "Based on your current monthly snapshot. If these numbers stayed unchanged, this is what happens next -- not a prediction."}
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              <th className="py-1 pr-3">Month</th>
              <th className="py-1 text-right">Ending cash</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((m) => (
              <tr key={m.month_index} className="border-t border-border">
                <td className="py-1.5 pr-3 text-text-secondary">{formatMonthYear(m.date)}</td>
                <td className="py-1.5 text-right font-medium text-text-primary">
                  {formatWholeDollars(m.ending_cash_cents)}
                  {m.depleted ? <span className="ml-1.5 text-xs font-semibold text-danger">Cash reaches $0</span> : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {remaining > 0 && !depletionMonth ? (
        <p className="mt-2 text-xs text-text-muted">Continues growing steadily beyond month {visible.length} at this rate.</p>
      ) : null}
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
