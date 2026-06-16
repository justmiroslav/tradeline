interface LogoProps {
  size?: number
  withWordmark?: boolean
}

export function Logo({ size = 22, withWordmark = true }: LogoProps) {
  return (
    <span className="inline-flex items-center gap-2.25">
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden>
        <rect x="1" y="1" width="22" height="22" rx="6" fill="var(--accent)" />
        <path d="M5 16l4-5 3 3 7-8" stroke="var(--accent-fg)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="19" cy="6" r="1.6" fill="var(--accent-fg)" />
      </svg>
      {withWordmark && (
        <span
          className="font-semibold text-fg-0 tracking-tight"
          style={{ fontSize: size * 0.78 }}
        >
          Tradeline
        </span>
      )}
    </span>
  )
}
