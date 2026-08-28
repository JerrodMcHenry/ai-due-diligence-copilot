"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import Button from "@/components/ui/Button";
import { stashHomepageIdea } from "@/lib/homepageIdeaHandoff";

const IDEA_PLACEHOLDER = "Describe the startup you've always wanted to build...";

// Phase 10.5 -- Consumer Home V2, Part 2/3. The entire signed-out idea
// flow lives in this one client component: type an idea, click "Build My
// Startup", stash the text, navigate to the EXISTING /idea-lab/new flow.
// No auth check here at all -- that boundary is enforced entirely by
// /idea-lab/new's own existing proxy.ts + auth.protect() (see
// lib/homepageIdeaHandoff.ts for why that's sufficient), so this
// component behaves identically whether the visitor is signed in or not.
export default function Hero() {
  const router = useRouter();
  const [idea, setIdea] = useState("");

  function handleBuildMyStartup() {
    const trimmed = idea.trim();

    if (!trimmed) {
      return;
    }

    stashHomepageIdea(trimmed);
    router.push("/idea-lab/new");
  }

  return (
    <section className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center py-12 text-center sm:py-20">
      <p className="text-sm font-semibold uppercase tracking-wide text-primary">
        Startup Intelligence Engine
      </p>

      <h1 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight text-text-primary sm:text-6xl">
        What if your idea became a startup?
      </h1>

      <p className="mt-5 max-w-xl text-base leading-7 text-text-secondary sm:text-lg">
        Describe it in your own words. SIE helps you model it, test your
        assumptions, and improve the idea — before you build anything.
      </p>

      <div className="mt-10 w-full max-w-2xl">
        <label htmlFor="hero-idea" className="sr-only">
          Describe your startup idea
        </label>

        <textarea
          id="hero-idea"
          value={idea}
          onChange={(event) => setIdea(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              handleBuildMyStartup();
            }
          }}
          placeholder={IDEA_PLACEHOLDER}
          rows={3}
          maxLength={4000}
          className="w-full resize-none rounded-2xl border border-border bg-surface px-6 py-5 text-base leading-7 text-text-primary shadow-sm outline-none transition-colors placeholder:text-text-muted focus:border-primary focus:ring-4 focus:ring-primary/15 sm:text-lg"
        />

        <div className="mt-5 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button size="lg" onClick={handleBuildMyStartup} disabled={!idea.trim()}>
            Build My Startup
          </Button>

          <p className="text-xs text-text-muted">
            Free to start. No credit card. Your idea stays yours.
          </p>
        </div>

        {/* Phase 10.9 -- Founder Playbooks V1, Part 12: a restrained
            educational invitation that supports "Build My Startup" as the
            primary CTA rather than competing with it -- smaller type,
            secondary position, no button of its own. */}
        <p className="mt-6 text-sm text-text-muted">
          Never built a startup before?{" "}
          <Link href="/playbooks" className="font-semibold text-primary hover:underline">
            We&rsquo;ll teach you.
          </Link>
        </p>
      </div>
    </section>
  );
}
