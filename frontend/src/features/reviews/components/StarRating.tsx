import { useState } from "react"

const STAR_PATH = "M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"

interface StarRatingProps {
  value: number
  onChange?: (value: number) => void
  size?: number
}

export function StarRating({ value, onChange, size = 20 }: StarRatingProps) {
  const interactive = !!onChange
  const [hover, setHover] = useState(0)
  const active = hover || value

  return (
    <span className="inline-flex items-center" onMouseLeave={() => interactive && setHover(0)}>
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          type="button"
          disabled={!interactive}
          onClick={() => onChange?.(star)}
          onMouseEnter={() => interactive && setHover(star)}
          aria-label={`${star} star${star > 1 ? "s" : ""}`}
          className="p-1 bg-transparent border-0 leading-none transition-transform enabled:cursor-pointer enabled:hover:scale-110"
          style={{ color: star <= active ? "var(--accent)" : "var(--fg-3)" }}
        >
          <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden style={{ display: "block" }}>
            <path d={STAR_PATH} />
          </svg>
        </button>
      ))}
    </span>
  )
}
