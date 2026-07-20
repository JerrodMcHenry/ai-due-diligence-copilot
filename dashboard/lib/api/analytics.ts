import { apiFetch } from "./client";

export function getAnalytics() {
  return apiFetch("/analytics");
}

export function getTopStartups() {
  return apiFetch("/top-startups");
}

export function getTopImprovingStartups() {
  return apiFetch("/top-improving-startups");
}
