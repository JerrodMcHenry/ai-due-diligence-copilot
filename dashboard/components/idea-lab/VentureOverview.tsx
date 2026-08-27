import BaseCard from "@/components/ui/BaseCard";

// Phase 10.6 -- Idea Lab V2, Part 3. The plain-language summary a founder
// sees FIRST, before the seven-section assumption form -- the exact shape
// the phase spec calls out: YOUR IDEA / WHO IT'S FOR / HOW IT MIGHT MAKE
// MONEY / WHAT WE STILL NEED TO FIGURE OUT. Pure presentation over
// whatever the caller already has (a VentureDraft mid-review, or a saved
// VentureResponse) -- it computes nothing, stores nothing, and calls no
// API. "What we still need to figure out" is derived from which VPS
// categories are still null (Unavailable) when a model_result is
// available; the draft-review call site (no model_result yet) instead
// passes a static list of the categories that are always meaningful to
// think about next.
type OverviewRow = {
  label: string;
  value: string | null;
};

type VentureOverviewProps = {
  idea: string | null;
  whoItsFor: string | null;
  howItMakesMoney: string | null;
  stillFiguringOut: string[];
};

export default function VentureOverview({
  idea,
  whoItsFor,
  howItMakesMoney,
  stillFiguringOut,
}: VentureOverviewProps) {
  const rows: OverviewRow[] = [
    { label: "Your idea", value: idea },
    { label: "Who it's for", value: whoItsFor },
    { label: "How it might make money", value: howItMakesMoney },
  ];

  return (
    <BaseCard className="p-6">
      <div className="space-y-5">
        {rows.map((row) => (
          <div key={row.label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {row.label}
            </p>
            <p className="mt-1 text-base leading-6 text-text-primary">
              {row.value?.trim() || <span className="text-text-muted">Not described yet.</span>}
            </p>
          </div>
        ))}

        {stillFiguringOut.length > 0 ? (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              What we still need to figure out
            </p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {stillFiguringOut.map((item) => (
                <li
                  key={item}
                  className="rounded-full bg-warning-soft px-3 py-1 text-xs font-semibold text-warning"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </BaseCard>
  );
}
