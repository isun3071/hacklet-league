// Browser-side HTTP helper for same-origin calls to Django (/api, /_allauth).
// Session cookie is sent automatically (same origin); writes carry X-CSRFToken.

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return decodeURIComponent(parts.pop()!.split(";").shift() ?? "");
  return null;
}

export async function csrfToken(): Promise<string> {
  let token = getCookie("csrftoken");
  if (!token) {
    await fetch("/api/csrf/", { credentials: "include" });
    token = getCookie("csrftoken");
  }
  return token ?? "";
}

export type ApiResponse<T = unknown> = {
  ok: boolean;
  status: number;
  data: T | null;
  errors: string[];
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function extractErrors(data: any): string[] {
  if (!data || typeof data !== "object") return [];
  if (Array.isArray(data.errors)) {
    return data.errors.map((e: { message?: string }) => e?.message ?? "Error");
  }
  if (typeof data.detail === "string") return [data.detail];
  const msgs: string[] = [];
  for (const v of Object.values(data)) {
    if (Array.isArray(v)) msgs.push(...v.map((x) => String(x)));
    else if (typeof v === "string") msgs.push(v);
  }
  return msgs;
}

export async function request<T = unknown>(
  path: string,
  method: string,
  body?: unknown,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (method !== "GET") headers["X-CSRFToken"] = await csrfToken();
  const res = await fetch(path, {
    method,
    credentials: "include",
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let raw: any = null;
  try {
    raw = await res.json();
  } catch {
    /* empty body */
  }
  return { ok: res.ok, status: res.status, data: (raw as T) ?? null, errors: extractErrors(raw) };
}
