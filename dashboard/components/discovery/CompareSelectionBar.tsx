"use client";

import { useRouter } from "next/navigation";

import { MAX_COMPARE, MIN_COMPARE } from "@/lib/hooks/useComparisonSelection";

type CompareSelectionBarProps = {
  selectedIds: number[];
  onClear: () => void;
};

// Compare Startups V1, Parts 4/14: shared between DiscoveryView and
// SavedStartupsView. Shows current selection state explicitly (not just
// via each card's own toggle state) and is the single place that builds
// the /compare URL -- selection only becomes shareable URL state at this
// hand-off point, never while browsing/filtering.
export default function CompareSelectionBar({
  selectedIds,
  onClear,
}: CompareSelectionBarProps) {
  const router = useRouter();

  if (selectedIds.length === 0) {
    return null;
  }

  const canCompare = selectedIds.length >= MIN_COMPARE;

  return (
    <div
      role="status"
      className="sticky bottom-4 z-10 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-primary/30 bg-surface px-5 py-3 shadow-lg shadow-black/10"
    >
      <p className="text-sm font-medium text-text-primary">
        <span className="font-semibold">{selectedIds.length}</span>{" "}
        {selectedIds.length === 1 ? "startup" : "startups"} selected
        {!canCompare ? (
          <span className="ml-2 text-text-muted">
            (select at least {MIN_COMPARE})
          </span>
        ) : null}
        {selectedIds.length >= MAX_COMPARE ? (
          <span className="ml-2 text-text-muted">(max {MAX_COMPARE})</span>
        ) : null}
      </p>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onClear}
          className="rounded-lg px-3 py-2 text-sm font-semibold text-text-muted transition-colors hover:text-danger"
        >
          Clear
        </button>

        <button
          type="button"
          disabled={!canCompare}
          onClick={() =>
            router.push(`/compare?startups=${selectedIds.join(",")}`)
          }
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          Compare Startups →
        </button>
      </div>
    </div>
  );
}
