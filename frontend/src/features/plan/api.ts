import { request } from "@/shared/lib/api"
import type { PlanOut } from "@/shared/types/api"

export function listPlansRequest(): Promise<PlanOut[]> {
  return request<PlanOut[]>("/plans/")
}
