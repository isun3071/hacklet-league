# Stage 0 — Landing Page

A framework-free static landing page for hackletleague.com. Three files, no build step:

- `index.html` — the page
- `styles.css` — hand-written CSS (no Tailwind yet; Stage 1 brings the real Next.js + Tailwind app)
- `favicon.svg` — inline SVG favicon

This is intentionally throwaway. Stage 1 replaces it with the integrated Next.js page on Hetzner. See [../BUILD_ROADMAP.md](../BUILD_ROADMAP.md) Stage 0.

## Local preview

```bash
cd landing
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy checklist (account-level steps — these need Ian's logins)

### 1. Buttondown (email signup)

The form is already wired to the `iansun20` Buttondown account — endpoint
`https://buttondown.com/api/emails/embed-subscribe/iansun20` (form `action` +
`onsubmit` popup). After deploy, send yourself a test subscribe to confirm it
lands in the Buttondown dashboard.

### 2. Cloudflare Pages (hosting)

No git repo yet, so use **Direct Upload**:

- Dashboard: Cloudflare → Workers & Pages → Create → Pages → **Upload assets**, then
  drag in the contents of this `landing/` folder. Framework preset: **None**.
- Or via CLI: `npx wrangler pages deploy landing`

(When the repo goes on GitHub later, switch to Git integration and set the output
directory to `landing`.)

### 3. Custom domain + DNS at Porkbun

1. In the Cloudflare Pages project → **Custom domains** → add `hackletleague.com`
   (and optionally `www`).
2. Cloudflare will prompt for DNS. Simplest path: in **Porkbun**, change the
   domain's **nameservers** to the two Cloudflare nameservers it gives you. This
   hands DNS to Cloudflare, which then wires the Pages domain and issues SSL
   automatically.
   - Alternative (keep Porkbun DNS): add the CNAME record Cloudflare specifies.
3. Wait for DNS propagation (minutes to a couple hours). SSL is automatic via
   Cloudflare Universal SSL.

### 4. Verify (Stage 0 success criteria)

- [ ] `https://hackletleague.com` loads the real page
- [ ] Valid SSL (padlock, no warnings)
- [ ] Email signup submits and the address appears in Buttondown
- [ ] Page loads fast and looks clean on mobile + desktop
