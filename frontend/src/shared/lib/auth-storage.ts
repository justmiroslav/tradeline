const ACCESS_KEY = "tl.access"
const REFRESH_KEY = "tl.refresh"
const LEGACY_KEY = "tl.token"
const EVENT = "tl:auth"

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function notify(): void {
  window.dispatchEvent(new CustomEvent(EVENT))
}

export const authStorage = {
  getAccess(): string | null {
    return read(ACCESS_KEY)
  },
  set(access: string): void {
    try {
      localStorage.setItem(ACCESS_KEY, access)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(LEGACY_KEY)
      notify()
    } catch {
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(ACCESS_KEY)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(LEGACY_KEY)
      notify()
    } catch {
    }
  },
  subscribe(listener: () => void): () => void {
    window.addEventListener(EVENT, listener)
    window.addEventListener("storage", listener)
    return () => {
      window.removeEventListener(EVENT, listener)
      window.removeEventListener("storage", listener)
    }
  }
}
