// Founder Experience Model correction, Part 1. This used to render the
// same numbered 1-2-3-4-5 stepper (circles joined by a connecting line)
// as the per-venture VentureJourney stepper it was modeled on -- see
// that component's own updated docstring for why that shape is
// conceptually wrong: it told a visitor, before they'd even started,
// that startups move through a mandatory one-way staircase ending in
// fundraising. This is marketing/product explanation ("what does SIE
// help with"), not a claim about any real venture's state -- so unlike
// VentureJourney, there is no state to infer here at all; this is a
// static, order-agnostic description of SIE's capabilities, redesigned
// to say so honestly: no numbers, no connecting line, no forward-only
// visual, and copy that says outright that modeling/validating/building
// repeat and that fundraising is optional.
const CAPABILITIES = [
  {
    label: "Shape an idea",
    description: "Describe it in your own words. SIE structures it into a venture model you can correct.",
  },
  {
    label: "Model & validate — as many times as it takes",
    description:
      "Test assumptions, run what-if scenarios, and revisit your model as often as you learn something new. This isn't a one-time step.",
  },
  {
    label: "Build & keep learning",
    description:
      "Track real progress as you execute. Building and validating aren't sequential — most founders do both at once, continuously.",
  },
  {
    label: "Fundraise when it's relevant to you",
    description:
      "Model SAFEs, priced rounds, and dilution whenever you're actually considering raising — optional, and not every founder needs it.",
  },
];

export default function IdeaJourney() {
  return (
    <section>
      <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary md:text-3xl">
        From idea to startup
      </h2>

      <p className="mx-auto mt-3 max-w-xl text-center text-sm leading-6 text-text-secondary">
        SIE stays useful at every point along the way — not a checklist to complete in order, but a set of
        capabilities you return to as your venture evolves.
      </p>

      {/* A plain, order-agnostic grid -- deliberately no numbers and no
          connecting line between cards, so nothing here reads as "step 1
          before step 2." */}
      <div className="mx-auto mt-10 grid max-w-4xl gap-4 sm:grid-cols-2">
        {CAPABILITIES.map((capability) => (
          <div key={capability.label} className="rounded-2xl border border-border bg-surface p-5">
            <p className="text-sm font-bold text-text-primary">{capability.label}</p>
            <p className="mt-1.5 text-sm leading-6 text-text-secondary">{capability.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
