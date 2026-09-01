// Founder Progress / Venture History V1. Pure, deterministic formatting
// helpers over the exact events GET /ventures/{id}/history already
// returns -- no computation of new facts, no I/O. Zero "@/..." alias
// imports (same discipline as this directory's other resolvers), so
// this stays trivially testable with plain `node`.

type MinimalHistoryEvent = {
  event_type: string;
  occurred_at: string;
};

// A short, human date-group label matching Section 7's own worked
// example ("TODAY", "SEPT 12", "AUG 28") -- "Today"/"Yesterday" for the
// two most recent calendar days (in the caller's local time zone), a
// plain "MMM D" for anything older. `now` is an explicit parameter
// (never `new Date()` inside this function) so this stays a pure
// function of its inputs, deterministic and testable.
export function formatHistoryDateGroupLabel(isoDate: string, now: Date): string {
  const date = new Date(isoDate);
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

  const dayDiffMs = startOfDay(now) - startOfDay(date);
  const oneDayMs = 24 * 60 * 60 * 1000;

  if (dayDiffMs === 0) return "Today";
  if (dayDiffMs === oneDayMs) return "Yesterday";

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" }).toUpperCase();
}

// Groups an already-sorted (most-recent-first) event list into
// consecutive same-day buckets, preserving order -- never re-sorts,
// never merges non-adjacent events that happen to share a date (the
// caller's own chronological order is trusted, not recomputed here).
export function groupHistoryEventsByDate<T extends MinimalHistoryEvent>(
  events: T[],
  now: Date
): { label: string; events: T[] }[] {
  const groups: { label: string; events: T[] }[] = [];

  for (const event of events) {
    const label = formatHistoryDateGroupLabel(event.occurred_at, now);
    const lastGroup = groups[groups.length - 1];
    if (lastGroup && lastGroup.label === label) {
      lastGroup.events.push(event);
    } else {
      groups.push({ label, events: [event] });
    }
  }

  return groups;
}

// A short, plain-language verb phrase per event type -- used as a
// fallback/prefix only; callers with richer context (e.g. a category
// diff) build their own fuller copy around this.
export function historyEventVerbPhrase(eventType: string): string {
  switch (eventType) {
    case "venture_created":
      return "Venture created";
    case "action_added":
      return "Action added";
    case "learning_recorded":
      return "Learning recorded";
    case "action_completed":
      return "Action completed";
    case "model_updated":
      return "Model updated";
    default:
      return eventType;
  }
}

export function formatVpsDelta(before: number | null, after: number | null): string {
  if (before === null && after === null) return "";
  if (before === null) return `${after!.toFixed(1)}`;
  if (after === null) return `${before.toFixed(1)}`;
  if (Math.abs(after - before) < 0.05) return `${before.toFixed(1)} (unchanged)`;
  return `${before.toFixed(1)} → ${after.toFixed(1)}`;
}
