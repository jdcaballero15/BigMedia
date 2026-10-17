export class ApiError extends Error {
  status: number
  fields: Record<string, string[]>

  constructor(status: number, payload: unknown) {
    const data = typeof payload === 'object' && payload !== null ? payload as Record<string, unknown> : {}
    const detail = typeof data.detail === 'string' ? data.detail : 'No se pudo completar la operación.'
    super(detail)
    this.status = status
    this.fields = Object.fromEntries(
      Object.entries(data)
        .filter(([key, value]) => key !== 'detail' && Array.isArray(value))
        .map(([key, value]) => [key, (value as unknown[]).map(String)]),
    )
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload: unknown = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(response.status, payload)
  return payload as T
}

function csrfToken(): string {
  const part = document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))
  return part ? decodeURIComponent(part.slice('csrftoken='.length)) : ''
}

export async function apiGet<T>(path: string): Promise<T> {
  return parseResponse<T>(await fetch(path, { credentials: 'same-origin' }))
}

export async function apiWrite<T>(path: string, method: 'POST' | 'PATCH', body?: unknown): Promise<T> {
  return parseResponse<T>(await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    body: JSON.stringify(body ?? {}),
  }))
}
