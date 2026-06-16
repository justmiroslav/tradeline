function accountHue(uid: string): number {
  let hash = 0
  for (const ch of uid) hash = (hash * 31 + ch.charCodeAt(0)) | 0
  return Math.abs(hash * 137) % 360
}

export function accountColor(uid: string, lightness = 0.72, chroma = 0.13, alpha = 1): string {
  const a = alpha === 1 ? "" : ` / ${alpha}`
  return `oklch(${lightness} ${chroma} ${accountHue(uid)}${a})`
}
