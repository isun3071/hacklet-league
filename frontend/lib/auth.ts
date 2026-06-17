import { request } from "@/lib/http";

const ALLAUTH = "/_allauth/browser/v1";

/** Returns the HTTP status from the allauth session endpoint (200 = authenticated). */
export async function getSession(): Promise<number> {
  try {
    const res = await fetch(`${ALLAUTH}/auth/session`, { credentials: "include" });
    return res.status;
  } catch {
    return 0;
  }
}

export const signup = (email: string, password: string) =>
  request(`${ALLAUTH}/auth/signup`, "POST", { email, password });

export const login = (email: string, password: string) =>
  request(`${ALLAUTH}/auth/login`, "POST", { email, password });

export const logout = () => request(`${ALLAUTH}/auth/session`, "DELETE");

export const verifyEmail = (key: string) =>
  request(`${ALLAUTH}/auth/email/verify`, "POST", { key });
