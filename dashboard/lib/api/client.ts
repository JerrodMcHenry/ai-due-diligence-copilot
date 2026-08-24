const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ApiFetchOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  // Only pass this for calls that genuinely need a hard upper bound (the
  // real, multi-minute analysis call). Every existing GET caller omits it
  // and keeps the browser's default (no) fetch timeout, unchanged from
  // before this file was extended.
  timeoutMs?: number;
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

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: options?.method ?? "GET",
      headers:
        options?.body !== undefined
          ? { "Content-Type": "application/json" }
          : undefined,
      body: options?.body !== undefined ? JSON.stringify(options.body) : undefined,
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
