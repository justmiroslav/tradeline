import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import { useEffect } from "react"
import { Link, NavLink } from "react-router-dom"

import { useDashboardNav } from "@/app/shell/dashboard-nav"
import { useMe } from "@/features/auth"
import { useAuth } from "@/shared/hooks/useAuth"
import { cn } from "@/shared/lib/cn"
import { PLAN_LABEL } from "@/shared/lib/plan"
import { Avatar } from "@/shared/ui/Avatar"
import { Ico } from "@/shared/ui/Ico"
import { Logo } from "@/shared/ui/Logo"

interface NavItem {
  to: string
  label: string
  icon: keyof typeof Ico
  end?: boolean
}

const PRIMARY: NavItem[] = [
  { to: "/dashboard", label: "Home", icon: "Home", end: true },
  { to: "/dashboard/journal", label: "Journal", icon: "List" },
  { to: "/dashboard/analytics", label: "Analytics", icon: "Chart" },
  { to: "/dashboard/keys", label: "API keys", icon: "Key" }
]

export function Sidebar() {
  const { logout } = useAuth()
  const { data: user } = useMe()
  const { open, setOpen } = useDashboardNav()
  const initial = user?.name?.[0]?.toUpperCase() ?? "?"
  const close = () => setOpen(false)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false) }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, setOpen])

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={close} aria-hidden />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-58 border-r border-line bg-bg-1 flex flex-col px-3.5 py-5",
          "transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
          "lg:static lg:z-auto lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Link
          to="/"
          onClick={close}
          aria-label="Tradeline home"
          className="px-2 pb-4.5 rounded-md inline-flex w-fit focus-visible:outline-none focus-visible:bg-bg-2"
        >
          <Logo size={24} />
        </Link>

        <nav className="flex flex-col gap-0.5 flex-1" aria-label="Main">
          {PRIMARY.map(item => <NavRow key={item.to} item={item} onNavigate={close} />)}
        </nav>

        <div className="h-px bg-line mb-2" />

        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              className="group w-full flex items-center gap-2.5 px-2 py-2 text-left rounded-md hover:bg-bg-2 focus-visible:bg-bg-2 focus-visible:outline-none transition-colors cursor-pointer"
              aria-label="User menu"
            >
              <Avatar initial={initial} src={user?.avatar_url} size={30} />
              <span className="flex-1 min-w-0">
                <span className="block text-[12.5px] font-medium text-fg-0 truncate">
                  {user?.name ?? "—"}
                </span>
                <span className="block text-[11px] text-fg-2 truncate">
                  {user ? PLAN_LABEL[user.plan] : ""}
                </span>
              </span>
              <Ico.Chevron width={15} height={15} className="text-fg-3 shrink-0 transition-transform group-data-[state=open]:rotate-180" />
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              side="top"
              align="start"
              sideOffset={8}
              alignOffset={10}
              className="min-w-(--radix-dropdown-menu-trigger-width) rounded-lg border border-line bg-bg-1 shadow-pop overflow-hidden z-50"
            >
              <div className="px-3.5 py-3 border-b border-line">
                <div className="text-[12px] text-fg-2 mb-1">Signed in as</div>
                <div className="text-[12.5px] text-fg-0 font-medium truncate">
                  {user?.email ?? "—"}
                </div>
              </div>

              <DropdownMenu.Item asChild>
                <NavLink
                  to="/dashboard/settings"
                  className="flex items-center gap-2.5 px-3.5 py-2.5 text-[12.5px] text-fg-0 outline-none hover:bg-bg-2 data-highlighted:bg-bg-2 cursor-pointer"
                >
                  <span className="text-fg-2 inline-flex"><Ico.Cog width={13} height={13} /></span>
                  Settings
                </NavLink>
              </DropdownMenu.Item>

              <DropdownMenu.Separator className="h-px bg-line" />
              <DropdownMenu.Item
                onSelect={(e) => { e.preventDefault(); void logout() }}
                className="flex items-center gap-2.5 px-3.5 py-2.5 text-[12.5px] text-loss outline-none hover:bg-bg-2 data-highlighted:bg-bg-2 cursor-pointer"
              >
                <Ico.ArrowL width={13} height={13} />
                Sign out
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </aside>
    </>
  )
}

function NavRow({ item, onNavigate }: { item: NavItem; onNavigate: () => void }) {
  const Icon = Ico[item.icon]
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.75 rounded-md px-2.5 py-2 text-[13.5px] transition-colors",
          isActive
            ? "bg-bg-3 text-fg-0 font-medium"
            : "text-fg-1 hover:text-fg-0 hover:bg-bg-2"
        )
      }
    >
      {({ isActive }) => (
        <>
          <span className={cn("inline-flex", isActive ? "text-accent" : "text-fg-2")}>
            <Icon width={16} height={16} />
          </span>
          {item.label}
        </>
      )}
    </NavLink>
  )
}
