"use client";

import { useEffect, useState } from "react";
import { csrfToken } from "@/lib/http";

// allauth headless social login uses a *form POST* (not fetch) to the provider
// redirect endpoint, because the response is a chain of browser redirects:
//   our form -> allauth -> Google consent -> /accounts/google/login/callback/ -> callback_url
// Two requirements learned the hard way:
//   - csrfmiddlewaretoken (value = csrftoken cookie) satisfies Django CSRF on the POST.
//   - callback_url must be ABSOLUTE (origin + path). allauth does not honor a relative
//     callback after the OAuth round-trip, so a relative value leaves the user stranded
//     on the backend callback URL instead of returning to the SPA.
const REDIRECT = "/_allauth/browser/v1/auth/provider/redirect";

export function GoogleSignInButton({ callbackUrl = "/dashboard" }: { callbackUrl?: string }) {
  const [token, setToken] = useState<string | null>(null);
  const [absoluteCallback, setAbsoluteCallback] = useState("");

  useEffect(() => {
    setAbsoluteCallback(window.location.origin + callbackUrl);
    csrfToken().then(setToken);
  }, [callbackUrl]);

  const ready = token !== null && absoluteCallback !== "";

  return (
    <form method="post" action={REDIRECT} className="oauth-form">
      <input type="hidden" name="provider" value="google" />
      <input type="hidden" name="callback_url" value={absoluteCallback} />
      <input type="hidden" name="process" value="login" />
      <input type="hidden" name="csrfmiddlewaretoken" value={token ?? ""} />
      <button className="btn btn-oauth" type="submit" disabled={!ready}>
        {ready ? "Continue with Google" : "..."}
      </button>
    </form>
  );
}
