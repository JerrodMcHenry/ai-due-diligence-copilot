"use client";

import { useCallback, useState } from "react";

// Compare Startups V1, Parts 4/14: the shared selection LOGIC (toggle,
// the 2-4 bound, clear) lives in this one hook, reused by both
// DiscoveryView and SavedStartupsView -- not shared STATE across pages
// (each page holds its own instance), per the task's explicit "do not
// introduce global state management" and "do not duplicate comparison
// state logic". Selection itself is plain, page-local, ephemeral React
// state -- it only becomes URL state (shareable, refresh-safe) once the
// user clicks through to /compare, which is where useComparisonSelection
// hands off to (see CompareSelectionBar).
export const MIN_COMPARE = 2;
export const MAX_COMPARE = 4;

export function useComparisonSelection() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const isSelected = useCallback(
    (id: number) => selectedIds.includes(id),
    [selectedIds]
  );

  const toggle = useCallback((id: number) => {
    setSelectedIds((current) => {
      if (current.includes(id)) {
        return current.filter((existingId) => existingId !== id);
      }

      if (current.length >= MAX_COMPARE) {
        // The calling control should already be disabled at max -- this
        // is a safety no-op, not the primary enforcement.
        return current;
      }

      return [...current, id];
    });
  }, []);

  const clear = useCallback(() => setSelectedIds([]), []);

  return {
    selectedIds,
    isSelected,
    toggle,
    clear,
    count: selectedIds.length,
    atMax: selectedIds.length >= MAX_COMPARE,
    canCompare: selectedIds.length >= MIN_COMPARE,
  };
}
