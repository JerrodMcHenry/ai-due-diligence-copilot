"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { getAdminAnalytics } from "@/lib/api";
import type { AnalyticsReport } from "@/lib/api";

// Phase 28 -- Product Analytics & Growth Measurement V1, Part 13/14.
// "The dashboard should be operational, not beautiful. We need truth,
// not another polished product surface." -- deliberately plain
// label/value rows, no charts, no color-coded gauges. Supports the two
// required windows (7/30 days, Part 14) plus one wider option for
// sanity-checking a slower-moving metric.
const WINDOW_OPTIONS = [7, 30, 90] as const;

function formatRate(value: number | null): string {
  return value === null ? "Not enough data" : `${(value * 100).toFixed(1)}%`;
}

function formatCount(value: number | null): string {
  return value === null ? "Not enough data" : value.toLocaleString();
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border py-2 text-sm last:border-b-0">
      <span className="text-text-secondary">{label}</span>
      <span className="font-mono font-medium text-text-primary">{value}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <BaseCard className="p-5">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</h2>
      <div className="mt-2">{children}</div>
    </BaseCard>
  );
}

export default function AdminAnalyticsView() {
  const { getToken } = useAuth();

  const [windowDays, setWindowDays] = useState<number>(7);
  const [report, setReport] = useState<AnalyticsReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);

  const load = useCallback(async (days: number) => {
    setIsLoading(true);
    setError(null);
    setAccessDenied(false);
    try {
      const token = await getToken();
      if (!token) {
        setError("Your session expired. Sign in again.");
        return;
      }
      const data = await getAdminAnalytics(days, token);
      setReport(data);
    } catch (err) {
      console.error("Failed to load analytics report:", err);
      // apiFetch's own error message includes the HTTP status -- a real
      // 403 from RequireAdmin is the ONLY way a non-admin ever lands
      // here; this never guesses admin status client-side.
      if (err instanceof Error && /\(403\)/.test(err.message)) {
        setAccessDenied(true);
      } else {
        setError("Couldn't load the analytics report. Try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    Promise.resolve().then(() => {
      load(windowDays);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowDays]);

  if (accessDenied) {
    return (
      <BaseCard className="mx-auto max-w-md p-10 text-center">
        <h1 className="text-xl font-bold text-text-primary">Access denied</h1>
        <p className="mt-3 text-sm text-text-secondary">
          This report is restricted to admin accounts. If you believe this is wrong, contact the person who manages
          this deployment.
        </p>
      </BaseCard>
    );
  }

  return (
    <>
      <PageHeader
        title="Product Analytics"
        subtitle="Internal reporting only -- never shown to founders. Timestamps are stored and compared in server (UTC) time; no per-founder timezone is known or applied."
      />

      <div className="mb-5 flex flex-wrap items-center gap-2">
        {WINDOW_OPTIONS.map((days) => (
          <Button
            key={days}
            type="button"
            variant={windowDays === days ? "primary" : "subtle"}
            size="sm"
            onClick={() => setWindowDays(days)}
          >
            Last {days} days
          </Button>
        ))}
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      {isLoading || !report ? (
        <div className="h-64 animate-pulse rounded-2xl border border-border bg-surface" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Section title="North Star — Weekly Active Building Ventures">
            <Row label="Active building ventures" value={formatCount(report.north_star.active_ventures)} />
          </Section>

          <Section title="Activation">
            <Row label="Ventures created" value={formatCount(report.activation.ventures_created)} />
            <Row label="Activated (>=1 building event within 24h)" value={formatCount(report.activation.activated)} />
            <Row label="Activation rate" value={formatRate(report.activation.activation_rate)} />
          </Section>

          <Section title="Retention (venture-level; lookback fixed, not window-scoped)">
            <Row label="Activated cohort size" value={formatCount(report.retention.activated_cohort_size)} />
            <Row label="W1 retention (days 7-13)" value={formatRate(report.retention.w1_retention)} />
            <Row label="D1 retention" value={formatRate(report.retention.d1_retention)} />
            <Row label="D7 retention" value={formatRate(report.retention.d7_retention)} />
            <Row label="D30 retention" value={formatRate(report.retention.d30_retention)} />
          </Section>

          <Section title="Meaningful Building Days">
            <Row label="Total meaningful building days" value={formatCount(report.meaningful_building_days.meaningful_building_days)} />
            <Row label="Active ventures" value={formatCount(report.meaningful_building_days.active_ventures)} />
            <Row label="Building days / active venture" value={formatCount(report.meaningful_building_days.building_days_per_active_venture)} />
          </Section>

          <Section title="Engagement">
            <Row label="Captures" value={formatCount(report.engagement.captures)} />
            <Row label="Actions completed" value={formatCount(report.engagement.actions_completed)} />
            <Row label="Captures / active venture" value={formatCount(report.engagement.captures_per_active_venture)} />
            <Row label="Actions completed / active venture" value={formatCount(report.engagement.actions_completed_per_active_venture)} />
          </Section>

          <Section title="Distribution (Shareable Venture Snapshot)">
            <Row label="Activated ventures (denominator)" value={formatCount(report.distribution.activated_ventures)} />
            <Row label="Snapshots enabled" value={formatCount(report.distribution.snapshots_enabled)} />
            <Row label="Share activation rate" value={formatRate(report.distribution.share_activation_rate)} />
            <Row label="Snapshot links copied" value={formatCount(report.distribution.snapshot_links_copied)} />
            <Row label="Public snapshot views" value={formatCount(report.distribution.public_snapshot_views)} />
            <Row label="Snapshot CTA clicks" value={formatCount(report.distribution.snapshot_cta_clicks)} />
            <Row label="Snapshot CTA click rate" value={formatRate(report.distribution.snapshot_cta_click_rate)} />
            <Row label="Ventures created from snapshot" value={formatCount(report.distribution.ventures_created_from_snapshot)} />
            <Row label="Snapshot -> venture creation rate" value={formatRate(report.distribution.snapshot_to_venture_creation_rate)} />
          </Section>
        </div>
      )}

      <p className="mt-6 text-xs text-text-muted">
        Test/dev data (zztest_-prefixed users) is excluded from every metric above. See
        docs/product/PRODUCT_ANALYTICS_V1.md for exact definitions and known limitations.
      </p>
    </>
  );
}
