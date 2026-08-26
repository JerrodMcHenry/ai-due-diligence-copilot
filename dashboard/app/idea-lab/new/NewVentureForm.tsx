"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";

import { createVenture } from "@/lib/api";
import { emptyAssumptions, VENTURE_STAGES } from "@/types";

const IDEA_PLACEHOLDER = `e.g. "AI-powered accounts receivable automation for small construction companies."`;

// Idea Lab V1, Part 5: deliberately small -- a description, industry,
// customer, business model, and current status. NOT a 30-field business
// plan. Everything else (market/founder/GTM/economics/validation
// assumptions) is collected afterward on the venture's own workspace page
// via progressive disclosure, once there's already a venture to attach
// them to.
export default function NewVentureForm() {
  const router = useRouter();
  const { getToken } = useAuth();

  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [targetCustomer, setTargetCustomer] = useState("");
  const [businessModel, setBusinessModel] = useState("");
  const [stage, setStage] = useState<string>(VENTURE_STAGES[0]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedDescription = description.trim();

    if (!trimmedDescription) {
      setError("Describe your idea in a sentence or two to get started.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const token = await getToken();

      if (!token) {
        setError("Your session expired. Please sign in again.");
        return;
      }

      const venture = await createVenture(
        {
          name: trimmedDescription.slice(0, 120),
          description: trimmedDescription,
          industry: industry.trim() || null,
          target_customer: targetCustomer.trim() || null,
          business_model: businessModel.trim() || null,
          stage,
          assumptions: {
            ...emptyAssumptions(),
            target_customer: targetCustomer.trim() || null,
          },
        },
        token
      );

      router.push(`/idea-lab/${venture.id}`);
    } catch (submitError) {
      console.error("Failed to create venture:", submitError);
      setError("Your venture could not be created. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Model a new venture"
        subtitle="Start with what you're thinking about building — you can add more detail once your venture exists."
      />

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-5">
        <div>
          <label htmlFor="idea-description" className="mb-1.5 block text-sm font-medium text-text-primary">
            What are you thinking about building?
          </label>

          <textarea
            id="idea-description"
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder={IDEA_PLACEHOLDER}
            className="w-full resize-y rounded-lg border border-border bg-surface px-4 py-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="idea-industry" className="mb-1.5 block text-sm font-medium text-text-primary">
              Industry
            </label>
            <input
              id="idea-industry"
              type="text"
              value={industry}
              onChange={(event) => setIndustry(event.target.value)}
              placeholder="e.g. Construction Tech"
              className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>

          <div>
            <label htmlFor="idea-customer" className="mb-1.5 block text-sm font-medium text-text-primary">
              Customer
            </label>
            <input
              id="idea-customer"
              type="text"
              value={targetCustomer}
              onChange={(event) => setTargetCustomer(event.target.value)}
              placeholder="Who is this for?"
              className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>

          <div>
            <label htmlFor="idea-business-model" className="mb-1.5 block text-sm font-medium text-text-primary">
              Business model
            </label>
            <input
              id="idea-business-model"
              type="text"
              value={businessModel}
              onChange={(event) => setBusinessModel(event.target.value)}
              placeholder="e.g. Subscription"
              className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>

          <div>
            <label htmlFor="idea-stage" className="mb-1.5 block text-sm font-medium text-text-primary">
              Current status
            </label>
            <select
              id="idea-stage"
              value={stage}
              onChange={(event) => setStage(event.target.value)}
              className="h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            >
              {VENTURE_STAGES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error ? (
          <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="min-h-11 rounded-lg bg-primary px-6 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Building..." : "Build My Venture"}
        </button>
      </form>
    </>
  );
}
