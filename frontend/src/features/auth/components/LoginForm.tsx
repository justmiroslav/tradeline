import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"

import { useAuth } from "@/shared/hooks/useAuth"
import { ApiError } from "@/shared/lib/api"
import { Btn } from "@/shared/ui/Btn"
import { Field } from "@/shared/ui/Field"
import { Ico } from "@/shared/ui/Ico"
import { Input } from "@/shared/ui/Input"
import { Pill } from "@/shared/ui/Pill"

import { DASHBOARD_HOME, loginSchema, type LoginValues } from "../schema"

export function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" }
  })

  const onSubmit = async (values: LoginValues) => {
    setServerError(null)
    try {
      await login(values)
      navigate(DASHBOARD_HOME, { replace: true })
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Couldn't reach the server — check it's running, then try again")
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5" noValidate>
      <Field label="Email" htmlFor="login-email" error={form.formState.errors.email?.message}>
        <Input
          id="login-email"
          type="email"
          autoComplete="email"
          invalid={!!form.formState.errors.email}
          {...form.register("email")}
        />
      </Field>

      <Field label="Password" htmlFor="login-password" error={form.formState.errors.password?.message}>
        <Input
          id="login-password"
          type="password"
          autoComplete="current-password"
          invalid={!!form.formState.errors.password}
          {...form.register("password")}
        />
      </Field>

      {serverError && <Pill tone="loss" className="self-start">{serverError}</Pill>}

      <Btn
        type="submit"
        kind="primary"
        size="md"
        full
        disabled={form.formState.isSubmitting}
        trailing={!form.formState.isSubmitting ? <Ico.Arrow width={14} height={14} /> : null}
      >
        {form.formState.isSubmitting ? "Logging in…" : "Log in"}
      </Btn>
    </form>
  )
}
