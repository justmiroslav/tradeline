import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { Link } from "react-router-dom"

import { useAuth } from "@/shared/hooks/useAuth"
import { ApiError } from "@/shared/lib/api"
import { cn } from "@/shared/lib/cn"
import { Btn } from "@/shared/ui/Btn"
import { Field } from "@/shared/ui/Field"
import { Ico } from "@/shared/ui/Ico"
import { Input } from "@/shared/ui/Input"
import { Pill } from "@/shared/ui/Pill"

import { registerSchema, type RegisterValues } from "../schema"

interface RegisterFormProps {
  onRegistered: (email: string) => void
}

export function RegisterForm({ onRegistered }: RegisterFormProps) {
  const { register: registerUser } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)
  const [nameLocked, setNameLocked] = useState(true)

  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    mode: "onTouched",
    defaultValues: { name: "", email: "", password: "" }
  })

  const passwordOk = (form.watch("password") ?? "").length >= 8
  const fieldsValid = registerSchema.safeParse(form.watch()).success
  const canSubmit = fieldsValid && !form.formState.isSubmitting

  const onSubmit = async (values: RegisterValues) => {
    setServerError(null)
    try {
      await registerUser(values)
      onRegistered(values.email)
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Sign-up failed, please try again")
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5" noValidate>
      <Field label="Name" htmlFor="reg-name" error={form.formState.errors.name?.message}>
        <Input
          id="reg-name"
          type="text"
          autoComplete="off"
          readOnly={nameLocked}
          onFocus={() => setNameLocked(false)}
          invalid={!!form.formState.errors.name}
          {...form.register("name")}
        />
      </Field>

      <Field label="Email" htmlFor="reg-email" error={form.formState.errors.email?.message}>
        <Input
          id="reg-email"
          type="email"
          autoComplete="email"
          invalid={!!form.formState.errors.email}
          {...form.register("email")}
        />
      </Field>

      <Field
        label="Password"
        htmlFor="reg-password"
        error={form.formState.errors.password?.message}
        hint={
          <span className={cn("inline-flex items-center gap-1.5 transition-colors duration-200", passwordOk ? "text-profit" : "text-fg-2")}>
            <Ico.Check width={12} height={12} className={cn("transition-opacity duration-200", passwordOk ? "opacity-100" : "opacity-30")} />
            At least 8 characters
          </span>
        }
      >
        <Input
          id="reg-password"
          type="password"
          autoComplete="new-password"
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
        disabled={!canSubmit}
        trailing={!form.formState.isSubmitting ? <Ico.Arrow width={14} height={14} /> : null}
      >
        {form.formState.isSubmitting ? "Creating account…" : "Create account"}
      </Btn>

      <TermsNote />
    </form>
  )
}

function TermsNote() {
  return (
    <p className="flex items-start gap-2 m-0 text-[11.5px] text-fg-2 leading-relaxed">
      <span className="inline-flex h-[19px] items-center shrink-0" aria-hidden>
        <Ico.Shield width={13} height={13} className="text-fg-3" />
      </span>
      <span>
        By creating an account you agree to the{" "}
        <Link to="/terms" className="text-fg-1 underline underline-offset-2 hover:text-fg-0">Terms</Link>{" "}
        and to Tradeline using your trade data to generate AI insights
      </span>
    </p>
  )
}
