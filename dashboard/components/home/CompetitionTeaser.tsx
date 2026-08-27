// Phase 10.5, Part 10. Plants the seed for future viral/group use WITHOUT
// claiming any competition/leaderboard functionality that doesn't exist
// yet -- copy stays entirely about the individual founder's own idea and
// the existing model-it/challenge-it flow, never mentions rankings
// against other users, prizes, or a leaderboard.
export default function CompetitionTeaser() {
  return (
    <section className="mx-auto max-w-2xl text-center">
      <h2 className="text-xl font-bold text-text-primary sm:text-2xl">
        Think you have the best startup idea?
      </h2>

      <p className="mt-3 text-sm leading-6 text-text-secondary">
        Build it. Model it. Challenge your assumptions. Whether you&rsquo;re a
        student, in a startup competition, going through an accelerator, or
        just testing an idea on your own — SIE gives you a real starting
        point.
      </p>
    </section>
  );
}
