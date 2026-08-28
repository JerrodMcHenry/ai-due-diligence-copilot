import PageHeader from "@/components/layout/PageHeader";
import PlaybookCard from "@/components/playbooks/PlaybookCard";
import { getJourneyGroups } from "@/content/playbooks";

// Phase 10.9 -- Founder Playbooks V1, Part 4. Public, no auth.protect() --
// educational content should be readable by anyone, signed in or not,
// the same posture as Rankings/Search/Compare. A pure Server Component
// reading a static content array: no client fetch, no loading state,
// nothing to hydrate. Organized around the founder journey (Part 4's own
// suggested grouping), not an alphabetical or "documentation sidebar"
// layout -- this is "Learn how to build your startup," not a knowledge
// base.
export const metadata = {
  title: "Playbooks | Startup Intelligence",
};

export default function PlaybooksIndexPage() {
  const journeyGroups = getJourneyGroups();

  return (
    <>
      <PageHeader
        title="Learn how to build your startup"
        subtitle="Short, practical guides for each stage of building a company — written for someone who's never done this before."
      />

      <div className="space-y-10">
        {journeyGroups.map((group) => (
          <section key={group.stage}>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">{group.label}</h2>

            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {group.playbooks.map((playbook) => (
                <PlaybookCard key={playbook.slug} playbook={playbook} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
