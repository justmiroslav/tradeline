import { lazy } from "react"
import { createBrowserRouter } from "react-router-dom"

import { AuthLayout } from "@/app/layouts/AuthLayout"
import { DashboardLayout } from "@/app/layouts/DashboardLayout"
import { MarketingLayout } from "@/app/layouts/MarketingLayout"
import { RequireAuth } from "@/app/layouts/RequireAuth"
import Auth from "@/pages/Auth"
import Checkout from "@/pages/Checkout"
import Landing from "@/pages/Landing"
import NotFound from "@/pages/NotFound"
import Terms from "@/pages/Terms"
import { RouteError } from "@/shared/ui/AppError"

const Home = lazy(() => import("@/pages/dashboard/Home"))
const Journal = lazy(() => import("@/pages/dashboard/Journal"))
const Analytics = lazy(() => import("@/pages/dashboard/Analytics"))
const Keys = lazy(() => import("@/pages/dashboard/Keys"))
const Settings = lazy(() => import("@/pages/dashboard/Settings"))

export const router = createBrowserRouter([
  {
    element: <MarketingLayout />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <Landing /> },
      { path: "terms", element: <Terms /> }
    ]
  },
  {
    element: <AuthLayout />,
    errorElement: <RouteError />,
    children: [{ path: "auth", element: <Auth /> }]
  },
  {
    element: (
      <RequireAuth>
        <DashboardLayout />
      </RequireAuth>
    ),
    errorElement: <RouteError />,
    children: [
      { path: "dashboard", element: <Home /> },
      { path: "dashboard/journal", element: <Journal /> },
      { path: "dashboard/analytics", element: <Analytics /> },
      { path: "dashboard/keys", element: <Keys /> },
      { path: "dashboard/settings", element: <Settings /> }
    ]
  },
  {
    path: "checkout",
    errorElement: <RouteError />,
    element: (
      <RequireAuth>
        <Checkout />
      </RequireAuth>
    )
  },
  { path: "*", element: <NotFound /> }
])
