// Tailwind's JIT compiler needs literal class strings present in source --
// a dynamically concatenated class like `"lg:grid-cols-" + count` is
// invisible to it and never generates the CSS. Every compare component
// that lays out one column per selected startup (2-4) looks this up
// instead of building the class string itself.
const GRID_COLS_BY_COUNT: Record<number, string> = {
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
};

export function gridColsClass(count: number): string {
  return GRID_COLS_BY_COUNT[count] ?? GRID_COLS_BY_COUNT[2];
}
