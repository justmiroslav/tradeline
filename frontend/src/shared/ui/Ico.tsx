import type { SVGProps } from "react"

type IconProps = SVGProps<SVGSVGElement>

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true
}

export const Ico = {
  Sun: (p: IconProps) => (
    <svg {...base} {...p}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4" />
    </svg>
  ),
  Moon: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
    </svg>
  ),
  Arrow: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  ),
  ArrowL: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M19 12H5M11 6l-6 6 6 6" />
    </svg>
  ),
  Check: (p: IconProps) => (
    <svg {...base} strokeWidth={2} {...p}>
      <path d="M5 12l4 4L19 7" />
    </svg>
  ),
  Plus: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  X: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  Search: (p: IconProps) => (
    <svg {...base} {...p}>
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </svg>
  ),
  Home: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M4 11l8-7 8 7M6 10v9h12v-9" />
    </svg>
  ),
  List: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" />
    </svg>
  ),
  Chart: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M4 19V5M4 19h16M8 15v-4M12 15V8M16 15v-6" />
    </svg>
  ),
  Key: (p: IconProps) => (
    <svg {...base} {...p}>
      <circle cx="8" cy="14" r="4" />
      <path d="M11 11l9-9M16 6l3 3M14 8l3 3" />
    </svg>
  ),
  Crown: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M3 8l4 4 5-7 5 7 4-4-2 11H5z" />
    </svg>
  ),
  Cog: (p: IconProps) => (
    <svg {...base} {...p}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 12c0-.6-.1-1.2-.2-1.7l2-1.6-2-3.5-2.4 1a7 7 0 0 0-3-1.7L13 2h-4l-.4 2.5a7 7 0 0 0-3 1.7l-2.4-1-2 3.5 2 1.6c-.1.5-.2 1.1-.2 1.7s.1 1.2.2 1.7l-2 1.6 2 3.5 2.4-1a7 7 0 0 0 3 1.7L9 22h4l.4-2.5a7 7 0 0 0 3-1.7l2.4 1 2-3.5-2-1.6c.1-.5.2-1.1.2-1.7z" />
    </svg>
  ),
  Shield: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" />
    </svg>
  ),
  Bolt: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M13 3L4 14h7l-1 7 9-11h-7z" />
    </svg>
  ),
  Download: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M12 4v12M6 11l6 6 6-6M4 20h16" />
    </svg>
  ),
  Copy: (p: IconProps) => (
    <svg {...base} {...p}>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  ),
  More: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...p}>
      <circle cx="6" cy="12" r="1.4" />
      <circle cx="12" cy="12" r="1.4" />
      <circle cx="18" cy="12" r="1.4" />
    </svg>
  ),
  Chevron: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  ),
  Calendar: (p: IconProps) => (
    <svg {...base} {...p}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 9h18M8 3v4M16 3v4" />
    </svg>
  ),
  Lock: (p: IconProps) => (
    <svg {...base} {...p}>
      <rect x="4" y="9" width="16" height="10" rx="2" />
      <path d="M8 9V5a4 4 0 0 1 8 0v4" />
    </svg>
  ),
  Warn: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M12 3l10 18H2z" />
      <path d="M12 10v5M12 18h.01" />
    </svg>
  ),
  Trash: (p: IconProps) => (
    <svg {...base} {...p}>
      <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" />
    </svg>
  )
}
