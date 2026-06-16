export function buildListQuery(params: object): string {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue
    if (Array.isArray(v)) v.forEach(item => qs.append(k, String(item)))
    else qs.append(k, String(v))
  }
  const s = qs.toString()
  return s ? `?${s}` : ""
}
