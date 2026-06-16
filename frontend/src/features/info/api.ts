import { request } from "@/shared/lib/api"

export interface ServerInfo {
  whitelist_ips: string[]
}

export function getServerInfoRequest(): Promise<ServerInfo> {
  return request<ServerInfo>("/info")
}
