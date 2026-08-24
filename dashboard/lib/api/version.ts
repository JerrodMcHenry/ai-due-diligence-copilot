import type { PlatformVersion } from "@/types";

import { apiFetch } from "./client";

export function getVersion(): Promise<PlatformVersion> {
  return apiFetch<PlatformVersion>("/version");
}
