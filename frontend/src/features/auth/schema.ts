import { z } from "zod"

export const DASHBOARD_HOME = "/dashboard"

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Required")
})

export const registerSchema = z.object({
  name: z.string().min(1, "Required").max(64, "Too long"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters")
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>
