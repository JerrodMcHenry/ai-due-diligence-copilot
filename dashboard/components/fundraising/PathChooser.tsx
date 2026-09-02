import type { FundraisingPath } from "@/lib/fundraisingUi/types";

// Phase 21B, Part 3. Beginner-first entry point -- deterministic
// progressive disclosure (plain founder-readable choices), never an AI
// wizard. "Raise my first money" guides a founder who doesn't yet know
// which instrument applies toward the two validated starting points
// (a single SAFE, or a priced round) rather than assuming prior
// knowledge -- Part 3's explicit instruction.
type ChooserOption = {
  id: string;
  label: string;
  description: string;
  path: FundraisingPath;
  safeCount: 1 | 2;
};

const OPTIONS: ChooserOption[] = [
  {
    id: "first-raise",
    label: "Raise my first money",
    description: "Model your very first outside investment -- we'll walk you through it.",
    path: "safe",
    safeCount: 1,
  },
  {
    id: "issue-safe",
    label: "Issue a SAFE",
    description: "Model a SAFE (Simple Agreement for Future Equity) investment.",
    path: "safe",
    safeCount: 1,
  },
  {
    id: "multiple-safes",
    label: "Model multiple SAFEs",
    description: "See how two SAFEs with different terms play out together.",
    path: "safe",
    safeCount: 2,
  },
  {
    id: "priced-round",
    label: "Raise a priced round",
    description: "Model a round with an agreed valuation, like a Seed or Series A.",
    path: "priced_round",
    safeCount: 1,
  },
  {
    id: "safe-then-seed",
    label: "Model SAFE → Seed",
    description: "See what happens when an existing SAFE converts at a future priced round.",
    path: "safe_then_round",
    safeCount: 1,
  },
];

type PathChooserProps = {
  onChoose: (path: FundraisingPath, initialSafeCount: 1 | 2) => void;
  onCompare: () => void;
};

export default function PathChooser({ onChoose, onCompare }: PathChooserProps) {
  return (
    <div>
      <h3 className="text-base font-semibold text-text-primary">What are you thinking about?</h3>
      <p className="mt-1 text-sm text-text-secondary">
        Pick what&rsquo;s closest to your situation -- you don&rsquo;t need to know the details yet.
      </p>

      <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
        {OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => onChoose(option.path, option.safeCount)}
            className="rounded-2xl border border-border bg-surface p-4 text-left transition-colors hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="block text-sm font-semibold text-text-primary">{option.label}</span>
            <span className="mt-1 block text-xs leading-5 text-text-muted">{option.description}</span>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onCompare}
        className="mt-3 text-sm font-semibold text-primary hover:text-primary-hover"
      >
        Or compare two fundraising options →
      </button>
    </div>
  );
}
