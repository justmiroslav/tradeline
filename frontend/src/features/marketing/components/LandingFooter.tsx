import { Link } from "react-router-dom"

import { Logo } from "@/shared/ui/Logo"

const GITHUB_URL = "https://github.com/justmiroslav"

export function LandingFooter() {
  return (
    <footer className="px-6 sm:px-10 lg:px-14 py-9 border-t border-line flex justify-between items-center text-[12.5px] text-fg-2 flex-wrap gap-4">
      <Logo size={18} />
      <div className="flex gap-6">
        <Link to="/terms" className="text-inherit no-underline hover:text-fg-1 transition-colors">
          Terms
        </Link>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer noopener"
          className="text-inherit no-underline hover:text-fg-1 transition-colors"
        >
          Contact
        </a>
      </div>
    </footer>
  )
}
