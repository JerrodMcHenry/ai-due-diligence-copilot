"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import PageHeader from "@/components/layout/PageHeader";
import { analyzeStartup, analyzeWebsite } from "@/lib/api";

// Website / URL Ingestion: the two ways to start an analysis. "url" is
// the primary/simple path (just paste a company website), "text" is the
// original free-form path this page has always had. Both funnel into the
// exact same canonical pipeline/response shape -- only which API client
// function gets called (and which input control is shown) differs.
type Mode = "url" | "text";

// Minimum characters before we bother sending a request -- catches the
// obviously-empty/junk case client-side without pretending to validate
// content quality (that's the real analysis's job, not this page's).
const MIN_LENGTH = 40;

const PLACEHOLDER = `Example:

Company: Acme Robotics
What it does: Acme builds autonomous inventory-scanning robots for mid-size warehouses.
Industry: Industrial robotics / supply chain
Business model: Hardware-as-a-service -- monthly subscription per robot, plus a per-warehouse onboarding fee.
Stage: Series A
Product: Scanner robots plus a fleet-management dashboard; integrates with common WMS platforms.
Customers: 12 paying warehouse operators, up from 3 a year ago.
Traction: $1.8M ARR, up from $400K last year. Net revenue retention ~115%.
Funding: Raised a $9M Series A in 2025; $11M raised to date.
Team: Founders previously built warehouse automation elsewhere; 18 employees.
Financials (if known): ~70% gross margin, 14 months of runway.

Include whatever you actually know: company name, what it does, industry,
business model, stage, product, customers, traction, funding, team, and any
financial details. More real detail produces a more complete analysis --
you don't need to fill in every line above, and you don't need to guess at
anything you don't know.`;

// What the pipeline actually does, in order -- shown as a static list of
// what SIE evaluates, never as a checklist that claims a given stage has
// finished. The backend does not currently report which stage is
// in-flight, so this is intentionally NOT rendered as live progress.
const STAGES = [
  "Researching the company",
  "Analyzing the six intelligence pillars",
  "Evaluating evidence",
  "Calculating the Startup Power Score",
  "Building the intelligence profile",
];

type Status = "idle" | "submitting" | "error";

function formatElapsed(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function validate(text: string): string | null {
  const trimmed = text.trim();

  if (trimmed.length === 0) {
    return "Enter some information about the startup before submitting.";
  }

  if (trimmed.length < MIN_LENGTH) {
    return `Add a bit more detail (at least ${MIN_LENGTH} characters) so SIE has enough to work with -- company name, what it does, industry, stage, traction, and so on.`;
  }

  return null;
}

// Client-side check only -- catches the obviously-wrong case (empty,
// missing scheme) before spending a network round trip. The backend
// (WebsiteAnalysisRequest + app/website_scrapper.py) is the actual
// source of truth for what's a safe, fetchable URL and re-validates
// independently regardless of what passes here.
function validateUrl(url: string): string | null {
  const trimmed = url.trim();

  if (trimmed.length === 0) {
    return "Enter a company website URL before submitting.";
  }

  if (!/^https?:\/\//i.test(trimmed)) {
    return "Website URL must start with http:// or https://";
  }

  return null;
}

export default function AnalyzeStartupPage() {
  const router = useRouter();

  const [mode, setMode] = useState<Mode>("url");
  const [companyText, setCompanyText] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const isSubmitting = status === "submitting";

  useEffect(() => {
    if (!isSubmitting) {
      return;
    }

    const interval = setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isSubmitting]);

  // MVP hardening: a refresh or tab close mid-analysis doesn't lose the
  // (expensive, multi-minute) analysis itself -- the backend request keeps
  // running and still persists on completion -- but it does strand the
  // user with no way to know when it finished or land on the resulting
  // profile automatically. The native browser confirmation is the
  // smallest honest guard against an accidental refresh/close; it can't
  // (and doesn't try to) prevent a deliberate one.
  useEffect(() => {
    if (!isSubmitting) {
      return;
    }

    function handleBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      // Legacy browsers key off the return value rather than
      // preventDefault() alone.
      event.returnValue = "";
    }

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isSubmitting]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    // Defense in depth: the submit button/form is unmounted while
    // isSubmitting is true (replaced by the analyzing state below), so
    // there is no visible control to double-click -- this guard only
    // matters if a submit event somehow fires again before that re-render.
    if (isSubmitting) {
      return;
    }

    const validationError =
      mode === "url" ? validateUrl(websiteUrl) : validate(companyText);

    if (validationError) {
      setStatus("error");
      setError(validationError);
      return;
    }

    setStatus("submitting");
    setError(null);
    setElapsedSeconds(0);

    try {
      const response =
        mode === "url"
          ? await analyzeWebsite(websiteUrl.trim())
          : await analyzeStartup(companyText);
      const companyName = response.context?.company_name?.trim();

      if (!companyName) {
        setStatus("error");
        setError(
          "The analysis completed, but SIE could not determine a clear company name to build a profile for. Try including the company's name explicitly and submit again."
        );
        return;
      }

      // Encode exactly once here -- the Startup Profile route decodes
      // exactly once when it reads the dynamic segment back out (see
      // app/startup/[id]/page.tsx), so this stays a single encode/decode
      // pass end-to-end, same contract as every other link into that route.
      router.push(`/startup/${encodeURIComponent(companyName)}`);
    } catch (caughtError) {
      console.error(
        mode === "url" ? "Analyze Website failed:" : "Analyze Startup failed:",
        caughtError
      );

      const message =
        caughtError instanceof Error ? caughtError.message : "";

      setStatus("error");
      setError(
        /Request timed out/.test(message)
          ? "The analysis is taking longer than expected and timed out. Your input hasn't been lost -- you can try submitting again."
          : /Network error/.test(message)
            ? "Couldn't reach the SIE backend. Confirm it's running, then try again."
            : "The analysis failed. Your input hasn't been lost -- you can try again."
      );
    }
  }

  return (
    <>
      <PageHeader
        title="Analyze Startup"
        subtitle="Give SIE what you know about a startup, and it will research, evaluate, and score it against the Methodology v2 intelligence framework, then build a full Startup Profile."
      />

      {!isSubmitting ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            role="radiogroup"
            aria-label="Analysis input method"
            className="inline-flex rounded-lg border border-slate-800 bg-slate-900 p-1"
          >
            {(["url", "text"] as const).map((candidate) => (
              <button
                key={candidate}
                type="button"
                role="radio"
                aria-checked={mode === candidate}
                onClick={() => {
                  setMode(candidate);
                  setError(null);
                }}
                className={`min-h-9 rounded-md px-4 text-sm font-semibold transition-colors ${
                  mode === candidate
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {candidate === "url" ? "Website URL" : "Company Information"}
              </button>
            ))}
          </div>

          {mode === "url" ? (
            <div>
              <label htmlFor="website-url" className="sr-only">
                Company website URL
              </label>

              <input
                id="website-url"
                type="text"
                inputMode="url"
                value={websiteUrl}
                onChange={(event) => setWebsiteUrl(event.target.value)}
                placeholder="https://example.com"
                className="w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />

              <p className="mt-2 text-xs text-slate-500">
                SIE will read the company&rsquo;s website, research it
                further, and build a full Startup Profile from what it
                finds.
              </p>
            </div>
          ) : (
            <div>
              <label htmlFor="company-text" className="sr-only">
                Startup information
              </label>

              <textarea
                id="company-text"
                value={companyText}
                onChange={(event) => setCompanyText(event.target.value)}
                placeholder={PLACEHOLDER}
                rows={16}
                className="w-full resize-y rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 font-mono text-sm leading-6 text-white outline-none transition-colors placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          )}

          {error ? (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            className="min-h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white transition-colors hover:bg-blue-500"
          >
            Analyze Startup
          </button>
        </form>
      ) : (
        <AnalyzingState elapsedSeconds={elapsedSeconds} />
      )}
    </>
  );
}

function AnalyzingState({ elapsedSeconds }: { elapsedSeconds: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-8">
      <div className="flex items-center gap-4">
        <span
          aria-hidden="true"
          className="h-8 w-8 shrink-0 animate-spin rounded-full border-2 border-slate-700 border-t-blue-500"
        />

        <div>
          <p className="text-lg font-semibold text-white">
            Analyzing startup&hellip;
          </p>

          <p className="mt-1 text-sm text-slate-400">
            SIE is researching and evaluating this startup. This typically
            takes a few minutes -- please keep this tab open.
          </p>
        </div>
      </div>

      <p className="mt-6 text-sm text-slate-500" aria-live="polite">
        Elapsed: {formatElapsed(elapsedSeconds)}
      </p>

      <div className="mt-6 border-t border-slate-800 pt-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          What SIE evaluates
        </p>

        <ul className="mt-3 space-y-2 text-sm text-slate-400">
          {STAGES.map((stage) => (
            <li key={stage} className="flex items-center gap-2.5">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 shrink-0 rounded-full bg-slate-600"
              />
              {stage}
            </li>
          ))}
        </ul>

        <p className="mt-4 text-xs text-slate-600">
          This describes what the analysis covers, not live progress -- SIE
          doesn&rsquo;t currently report which stage is in flight, so no
          single step is shown as complete until the whole analysis
          finishes.
        </p>
      </div>
    </div>
  );
}
