# Deploy Runbook

How to run hackletleague.com on any Docker host. The repo is host-agnostic — a
self-hosted machine today, a Hetzner VPS later. Only `.env` changes between hosts.

Fill in your own values for the placeholders below (`<PUBLIC_IP>`, `<VM_LAN_IP>`,
`<user>`, `<YOUR_LAN_CIDR>`). Keep real IPs/hostnames out of the repo.

---

## 1. Prerequisites (on the host, one time)

Install Docker Engine + the Compose plugin:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER     # then log out/in so `docker` works without sudo
docker compose version            # confirm the plugin is present
```

## 2. Get the code onto the host

For now (no GitHub remote yet), copy the repo over from your dev machine:

```bash
rsync -av --exclude '.git' --exclude '.env' ./ <user>@<VM_LAN_IP>:~/hacklet-league/
```

Later (Stage 1, once a GitHub remote + CI exist): `git clone` on the host and let CI
build images so the host only pulls + runs — keeps a modest CPU out of the build path.

## 3. Configure

```bash
cd ~/hacklet-league
cp .env.example .env
# edit .env:
#   SITE_ADDRESS=hackletleague.com
#   ACME_EMAIL=<your real email>
```

## 4. Point DNS (at Porkbun)

- **A record**: `hackletleague.com` -> `<PUBLIC_IP>`
- (optional) `www` A record -> same IP, or a CNAME to the apex
- Set a low TTL (e.g. 600s) while you're iterating.

> ⚠️ **Residential IPs can change.** If your public IP isn't static, the A record
> will eventually break. Either confirm it's static with your ISP, or add dynamic-DNS
> (Porkbun has an API — a small cron job can keep the record updated). Ask and I'll
> add a DDNS updater script.

TLS needs DNS resolving to the box **before** Caddy can issue certs. Verify:

```bash
dig +short hackletleague.com    # should print your public IP
```

## 5. Launch

```bash
docker compose up -d      # or: make up
docker compose logs -f    # watch Caddy obtain the Let's Encrypt cert
```

Caddy auto-provisions HTTPS once DNS resolves and 80/443 are reachable. Certs persist
in the `caddy_data` volume — don't delete it (Let's Encrypt rate-limits re-issuance).

## 6. Verify (Stage 0 success criteria)

- [ ] `https://hackletleague.com` loads the landing page
- [ ] Valid padlock / no TLS warnings
- [ ] Email signup works (after the Buttondown username is set in `landing/index.html`)
- [ ] Loads fast on mobile + desktop

> NAT hairpin: some routers won't let you reach your own public IP from inside the
> LAN. If it fails from home but the cert issued fine, test from cellular/another network.

---

## Security hygiene (you just put a box on the public internet)

- **Forward only 80/443** at the router — never expose SSH to the internet.
- On the host: `sudo ufw allow 80,443/tcp` and allow SSH only from the LAN
  (`sudo ufw allow from <YOUR_LAN_CIDR> to any port 22`), then `sudo ufw enable`.
- Keep it patched (`unattended-upgrades`), run containers non-root, and take a
  **VM snapshot** (e.g. Proxmox) before risky changes so you can roll back instantly.
- Consider `fail2ban` for SSH.

---

## Moving to Hetzner later (the "seamless transfer")

Because everything is Docker + 12-factor, the move is:

1. Provision the Hetzner VPS (x86 → same arch as the home box) and install Docker (step 1).
2. Copy the repo over (`rsync` or `git clone`).
3. Copy `.env` and adjust if needed.
4. *(Once a database exists, Stage 1+)* restore the latest `pg_dump` — backup/restore
   scripts will be added with Postgres.
5. Repoint the Porkbun A record to the Hetzner IP. `docker compose up -d`. Done.

No app changes. The host is a commodity.

---

## Local preview (no domain, HTTP only)

```bash
SITE_ADDRESS=:80 ACME_EMAIL=dev@example.com docker compose up
# open http://localhost
```
