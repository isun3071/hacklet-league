"use client";

import { useEffect, useState } from "react";
import { csrfToken } from "@/lib/http";

// allauth headless social login uses a *form POST* (not fetch) to the provider
// redirect endpoint, because the response is a chain of browser redirects:
//   our form -> allauth -> Google consent -> /accounts/google/login/callback/ -> callbackUrl
// Django CSRF on this POST is satisfied by the csrfmiddlewaretoken hidden field
// (value = csrftoken cookie). On success allauth lands the browser on callbackUrl,
// already authenticated.
const REDIRECT = "/_allauth/browser/v1/auth/provider/redirect";

export function GoogleSignInButton({ callbackUrl = "/dashboard" }: { callbackUrl?: string }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    csrfToken().then(setToken);
  }, []);

  return (
    <form method="post" action={REDIRECT} className="oauth-form">
      <input type="hidden" name="provider" value="google" />
      <input type="hidden" name="callback_url" value={callbackUrl} />
      <input type="hidden" name="process" value="login" />
      <input type="hidden" name="csrfmiddlewaretoken" value={token ?? ""} />
      <button className="btn btn-oauth" type="submit" disabled={!token}>
        {token ? "Continue with Google" : "..."}
      </button>
    </form>
  );
}
