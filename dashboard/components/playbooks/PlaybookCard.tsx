import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";

import type { Playbook } from "@/content/playbooks";

export default function PlaybookCard({ playbook }: { playbook: Playbook }) {
  return (
    <Link href={`/playbooks/${playbook.slug}`} className="block h-full">
      <BaseCard className="flex h-full flex-col gap-2 p-5 transition-colors hover:border-primary/40">
        <h3 className="text-sm font-semibold text-text-primary">{playbook.title}</h3>
        <p className="flex-1 text-sm leading-6 text-text-secondary">{playbook.description}</p>
        <p className="text-xs text-text-muted">{playbook.estimatedMinutes} min read</p>
      </BaseCard>
    </Link>
  );
}
