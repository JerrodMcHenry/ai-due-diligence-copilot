import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";

import type { Playbook } from "@/content/playbooks";

export default function PlaybookCard({ playbook }: { playbook: Playbook }) {
  return (
    <Link href={`/playbooks/${playbook.slug}`} className="block h-full">
      {/* Phase 31C-C, Part 7/9: the card title was rendering SMALLER
          (14px) than its own description below it (16px) -- a genuine
          hierarchy inversion, not just a small-text issue. Bumped to
          text-lg (18px, the card-heading floor) so the title actually
          dominates. */}
      <BaseCard className="flex h-full flex-col gap-2 p-6 transition-colors hover:border-primary/40">
        <h3 className="text-lg font-semibold text-text-primary">{playbook.title}</h3>
        <p className="flex-1 text-base leading-7 text-text-secondary">{playbook.description}</p>
        <p className="text-sm text-text-muted">{playbook.estimatedMinutes} min read</p>
      </BaseCard>
    </Link>
  );
}
