interface AppEnv {
  apiBaseUrl: string
  googleClientId: string
}

function read(): AppEnv {
  const url = import.meta.env.VITE_API_BASE_URL
  if (!url) {
    throw new Error("VITE_API_BASE_URL is not set — check frontend/.env.development")
  }
  return {
    apiBaseUrl: url.replace(/\/$/, ""),
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ""
  }
}

export const env: AppEnv = read()
