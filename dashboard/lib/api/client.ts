const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ApiFetchOptions = {
  method?: "GET" | "POST" | "DELETE";
  // A FormData body (Pitch Deck Upload's multipart request) is sent
  // as-is with no Content-Type header set -- the browser fills in
  // `multipart/form-data; boundary=...` itself, which it can only do
  // correctly if this code doesn't set Content-Type first. Anything
  // else is treated as a JSON body, exactly as before.
  body?: unknown;
  // Only pass this for calls that genuinely need a hard upper bound (the
  // real, multi-minute analysis call). Every existing GET caller omits it
  // and keeps the browser's default (no) fetch timeout, unchanged from
  // before this file was extended.
  timeoutMs?: number;
  // SIE Authentication Phase 2: a Clerk session token, attached as
  // `Authorization: Bearer <token>`. Deliberately a per-call option, not
  // global auth-awareness on apiFetch itself -- every existing public
  // call site (Dashboard, Rankings, Search, Startup Profile) stays
  // exactly as it was, most of them running in Server Components where
  // there's no client-side Clerk token to attach anyway. Only the
  // authenticated analyze call (see lib/api/analyze.ts) passes this.
  token?: string | null;
};

// Extended (additive, backward compatible) for POST support -- every
// existing call site was `apiFetch<T>(endpoint)` and continues to work
// unchanged (options is optional, defaults to a GET with no body).
export async function apiFetch<T>(
  endpoint: string,
  options?: ApiFetchOptions
): Promise<T> {
  const controller = options?.timeoutMs ? new AbortController() : undefined;
  const timeoutId =
    controller && options?.timeoutMs
      ? setTimeout(() => controller.abort(), options.timeoutMs)
      : undefined;

  const isFormData =
    typeof FormData !== "undefined" && options?.body instanceof FormData;

  const headers: Record<string, string> = {};

  if (options?.body !== undefined && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (options?.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: options?.method ?? "GET",
      headers: Object.keys(headers).length > 0 ? headers : undefined,
      body:
        options?.body === undefined
          ? undefined
          : isFormData
            ? (options.body as FormData)
            : JSON.stringify(options.body),
      signal: controller?.signal,
    });
  } catch {
    if (controller?.signal.aborted) {
      throw new Error(`Request timed out: ${endpoint}`);
    }

    throw new Error(`Network error reaching the API: ${endpoint}`);
  } finally {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
    }
  }

  if (!response.ok) {
    // Best-effort: surface the backend's own detail message (FastAPI's
    // default error shape is {"detail": "..."}) when the body is JSON and
    // has one. Never throws on a non-JSON/empty body -- falls back to the
    // same generic message this function always produced.
    let detail = "";

    try {
      const data = (await response.json()) as { detail?: unknown };
      detail = typeof data?.detail === "string" ? data.detail : "";
    } catch {
      // Not JSON, or no body -- fine, use the generic message below.
    }

    throw new Error(
      detail
        ? `API request failed (${response.status}): ${detail}`
        : `API request failed (${response.status}): ${endpoint}`
    );
  }

  return response.json() as Promise<T>;
}
