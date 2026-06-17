// Server-side data access for the Django backend.
// SSR fetches go over the internal docker network (backend:8000); the browser
// hits /api/... same-origin through Caddy (used in later client-side features).

import { cookies } from "next/headers";

const API_BASE = process.env.INTERNAL_API_URL ?? "http://backend:8000";

// Forward the incoming request's cookies so the backend authenticates the user.
// Without this, SSR fetches are anonymous and a creator can't see their own
// pending (unverified) chapter — the backend only returns it to its owner.
async function ssrHeaders(): Promise<Record<string, string>> {
  const all = (await cookies()).getAll();
  if (!all.length) return {};
  return { cookie: all.map((c) => `${c.name}=${c.value}`).join("; ") };
}

export type Chapter = {
  id: string;
  slug: string;
  name: string;
  description: string;
  location_text: string;
  tier: "A" | "B" | "C";
  mode: string;
  verification_status: string;
  institutional_affiliation: string;
  website_url: string;
  created_at: string;
};

export async function getChapters(): Promise<Chapter[]> {
  const res = await fetch(`${API_BASE}/api/chapters/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) throw new Error(`GET /api/chapters/ -> ${res.status}`);
  return res.json();
}

export async function getChapter(slug: string): Promise<Chapter | null> {
  const res = await fetch(`${API_BASE}/api/chapters/${slug}/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GET /api/chapters/${slug}/ -> ${res.status}`);
  return res.json();
}
