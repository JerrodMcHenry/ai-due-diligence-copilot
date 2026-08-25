"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import PageHeader from "@/components/layout/PageHeader";
import { analyzeMultiSource } from "@/lib/api";

// Unified Multi-Source Analyze Startup: company website, pitch deck, and
// additional company information are evidence SOURCES feeding one
// canonical analysis, not separate mutually-exclusive modes -- all three
// fields are shown together, any combination (including just one) is
// valid, and a single submit sends whichever were filled in to POST
// /analyze (see lib/api/analyze.ts::analyzeMultiSource). This replaces
// the earlier three-tab mode switcher.

// Client-side only, matching app/pdf_extractor.py's real cap -- catches
// an obviously-oversized file before spending a network round trip. The
// backend re-validates independently (size, magic bytes, page count,
// encryption, ...) regardless of what passes here.
const MAX_PDF_BYTES = 15 * 1024 * 1024;

const COMPANY_TEXT_PLACEHOLDER = `Anything else worth including that the website or pitch deck might not
capture -- recent traction or metrics, funding details, specific
customers, financial details, or context on stage/business model.

This is optional and supplementary -- it doesn't need to stand on its
own the way it would if it were your only source.`;

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

// Every field below is individually optional -- validate its own shape
// only when something was actually entered, then separately require that
// at least one of the three ended up supplied. Same client-side-only
// contract as before: catches the obvious case before a network round
// trip, the backend re-validates every source independently regardless.
function validateWebsiteUrl(url: string): string | null {
  const trimmed = url.trim();

  if (trimmed.length === 0) {
    return null;
  }

  if (!/^https?:\/\//i.test(trimmed)) {
    return "Website URL must start with http:// or https://";
  }

  return null;
}

function validatePdfFile(file: File | null): string | null {
  if (!file) {
    return null;
  }

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return "Only PDF files are supported.";
  }

  if (file.size > MAX_PDF_BYTES) {
    return `That PDF is too large to analyze (max ${MAX_PDF_BYTES / (1024 * 1024)} MB).`;
  }

  return null;
}

function validateForm(
  websiteUrl: string,
  pdfFile: File | null,
  companyText: string
): string | null {
  const urlError = validateWebsiteUrl(websiteUrl);
  if (urlError) {
    return urlError;
  }

  const pdfError = validatePdfFile(pdfFile);
  if (pdfError) {
    return pdfError;
  }

  const hasWebsite = websiteUrl.trim().length > 0;
  const hasPdf = pdfFile !== null;
  const hasText = companyText.trim().length > 0;

  if (!hasWebsite && !hasPdf && !hasText) {
    return "Provide at least one of: company website, pitch deck, or company information.";
  }

  return null;
}

export default function AnalyzeStartupPage() {
  const router = useRouter();

  const [websiteUrl, setWebsiteUrl] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const [companyText, setCompanyText] = useState("");
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

    const validationError = validateForm(websiteUrl, pdfFile, companyText);

    if (validationError) {
      setStatus("error");
      setError(validationError);
      return;
    }

    setStatus("submitting");
    setError(null);
    setElapsedSeconds(0);

    try {
      const response = await analyzeMultiSource({
        websiteUrl: websiteUrl.trim() || undefined,
        pdfFile: pdfFile ?? undefined,
        companyText: companyText.trim() || undefined,
      });
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
      console.error("Analyze Startup failed:", caughtError);

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
        subtitle="Provide a company website, a pitch deck, additional information, or any combination -- SIE will combine what you give it with its own research and build one full Startup Profile against the Methodology v2 intelligence framework."
      />

      {!isSubmitting ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="website-url"
              className="text-xs font-semibold uppercase tracking-wider text-slate-500"
            >
              Company Website
            </label>

            <input
              id="website-url"
              type="text"
              inputMode="url"
              value={websiteUrl}
              onChange={(event) => setWebsiteUrl(event.target.value)}
              placeholder="https://example.com"
              className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div>
            <label
              htmlFor="pitch-deck-file"
              className="text-xs font-semibold uppercase tracking-wider text-slate-500"
            >
              Pitch Deck
            </label>

            <input
              id="pitch-deck-file"
              ref={pdfInputRef}
              type="file"
              accept="application/pdf,.pdf"
              onChange={(event) =>
                setPdfFile(event.target.files?.[0] ?? null)
              }
              className="hidden"
            />

            <div className="mt-2">
              {pdfFile ? (
                <div className="flex min-h-11 items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900 px-4 py-3">
                  <span className="truncate text-sm text-white">
                    {pdfFile.name}
                  </span>

                  <button
                    type="button"
                    onClick={() => {
                      setPdfFile(null);
                      // Reset the underlying input so choosing the same
                      // file again after removing it still fires
                      // onChange (the browser otherwise treats it as an
                      // unchanged selection and stays silent).
                      if (pdfInputRef.current) {
                        pdfInputRef.current.value = "";
                      }
                    }}
                    className="shrink-0 text-sm font-semibold text-slate-400 hover:text-white"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <label
                  htmlFor="pitch-deck-file"
                  className="flex min-h-11 w-full cursor-pointer items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900 px-4 py-3 text-sm font-semibold text-slate-300 transition-colors hover:border-blue-500 hover:text-white"
                >
                  Choose PDF file&hellip;
                </label>
              )}
            </div>
          </div>

          <div>
            <label
              htmlFor="company-text"
              className="text-xs font-semibold uppercase tracking-wider text-slate-500"
            >
              Additional Company Information
            </label>

            <textarea
              id="company-text"
              value={companyText}
              onChange={(event) => setCompanyText(event.target.value)}
              placeholder={COMPANY_TEXT_PLACEHOLDER}
              rows={8}
              className="mt-2 w-full resize-y rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 font-mono text-sm leading-6 text-white outline-none transition-colors placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <p className="text-xs text-slate-500">
            At least one source is required. Provide any combination --
            SIE combines everything you give it into one analysis.
          </p>

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
