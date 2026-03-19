# LitigationOS — Vercel Deployment Checklist

> Generated for OPERATION OMEGA  
> Website: `00_SYSTEM/apps/website/`  
> Last verified build: ✅ Next.js 14.2.35 — all 17 pages compiled

---

## 1. Prerequisites

- [ ] Node.js ≥ 18 (project tested on v25.6.0)
- [ ] Vercel account with Pro plan (for cron jobs & serverless function config)
- [ ] Vercel CLI installed: `npm i -g vercel`
- [ ] GitHub repo connected to Vercel (recommended) OR manual CLI deploy

---

## 2. Deploy Commands

### Option A: CLI Deploy (Preview)

```bash
cd 00_SYSTEM/apps/website
npx vercel --yes
```

### Option B: CLI Deploy (Production)

```bash
cd 00_SYSTEM/apps/website
npx vercel --prod --yes
```

### Option C: Git-based Deploy

1. Push to GitHub
2. Import project in Vercel dashboard → select `00_SYSTEM/apps/website` as root directory
3. Framework preset: **Next.js** (auto-detected)
4. Build command: `next build`
5. Output directory: `.next`

---

## 3. Environment Variables (Vercel Dashboard → Settings → Environment Variables)

All secrets should be added via the Vercel dashboard or CLI (`vercel env add`).  
**Never commit real values to source control.**

| Variable | Description | Required |
|---|---|---|
| `NEXTAUTH_SECRET` | Random 32+ char secret (`openssl rand -base64 32`) | ✅ |
| `NEXTAUTH_URL` | Production URL (e.g. `https://litigationos.com`) | ✅ |
| `DATABASE_URL` | SQLite path or cloud DB connection string (see §4) | ✅ |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_...`) | ✅ |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key (`pk_live_...`) | ✅ |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) | ✅ |
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | ✅ |
| `NEO4J_URI` | Neo4j Bolt URI (`bolt://...` or `neo4j+s://...`) | ✅ |
| `NEO4J_USER` | Neo4j username | ✅ |
| `NEO4J_PASSWORD` | Neo4j password | ✅ |
| `OMEGA_RECALC_INTERVAL` | Score recalc interval in seconds (default: 21600) | Optional |
| `OMEGA_CONFIDENCE_THRESHOLD` | Min confidence for auto-scoring (default: 0.7) | Optional |
| `LOG_LEVEL` | `info` / `warn` / `error` | Optional |

---

## 4. ⚠️ Critical: better-sqlite3 & Serverless Compatibility

The website uses `better-sqlite3`, a native C++ addon. **This will NOT work in Vercel's serverless/edge environment** because:

- Vercel serverless functions run on AWS Lambda (Amazon Linux)
- Native bindings compiled on Windows/macOS won't work
- Lambda has a 50 MB deployment size limit; native addons bloat the bundle

### Recommended Solutions (pick one):

| Option | Effort | Description |
|---|---|---|
| **Turso (libSQL)** | Low | Drop-in SQLite-compatible cloud DB. Change driver to `@libsql/client`. |
| **PlanetScale / Neon** | Medium | Migrate to MySQL/Postgres cloud DB. |
| **Vercel Postgres** | Medium | Vercel's managed Postgres. Native integration. |
| **Self-host with Docker** | Low | Use the existing `Dockerfile` in `deploy/`. SQLite works fine. |

### Current Mitigation in next.config.js

```js
experimental: {
  serverComponentsExternalPackages: ['better-sqlite3'],
}
```

This tells Next.js to not bundle `better-sqlite3` into the serverless function, which is correct. If deploying to Vercel, the native binary must be compiled for Linux x64 — Vercel may handle this if the package has prebuilt binaries for `linux-x64`, but **test thoroughly**.

---

## 5. Vercel Project Configuration

The `vercel.json` at `00_SYSTEM/deploy/vercel.json` configures:

- **Region**: `iad1` (US East — Virginia)
- **Security headers**: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- **API headers**: no-store cache, nosniff, DENY framing, XSS protection
- **Rewrites**: `/dashboard` → `/app/dashboard`, `/evidence/*`, `/timeline/*`, `/omega/*`
- **Cron jobs**:
  - `/api/cron/backup` — daily at 2:00 AM
  - `/api/cron/omega-recalc` — every 6 hours

### To use this config:

Copy `vercel.json` into the website root before deploying, or configure root directory in Vercel dashboard to point to `00_SYSTEM/apps/website` and place `vercel.json` there.

```bash
cp 00_SYSTEM/deploy/vercel.json 00_SYSTEM/apps/website/vercel.json
```

---

## 6. next.config.js — Vercel Compatibility Notes

- `output: 'standalone'` is **NOT needed** for Vercel — Vercel has native Next.js support and builds optimally without it. Only use `standalone` for Docker/self-hosted.
- Current config is Vercel-ready as-is.

---

## 7. DNS Setup

1. In your domain registrar, add:
   - **A Record**: `@` → Vercel IP (provided in Vercel dashboard)
   - **CNAME**: `www` → `cname.vercel-dns.com`
2. In Vercel dashboard → Project → Settings → Domains:
   - Add `litigationos.com`
   - Add `www.litigationos.com` (redirect to apex)
3. Vercel auto-provisions SSL via Let's Encrypt
4. Update `NEXTAUTH_URL` env var to `https://litigationos.com`

---

## 8. Stripe Webhook Setup

1. In Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://litigationos.com/api/webhook`
3. Select events: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`
4. Copy signing secret → set as `STRIPE_WEBHOOK_SECRET` in Vercel env

---

## 9. Post-Deploy Verification

Run these checks after every deployment:

```bash
# Health check
curl -s https://litigationos.com/api/v1/health | jq .

# Verify security headers
curl -sI https://litigationos.com | grep -E "(Strict-Transport|X-Content-Type|X-Frame)"

# Test API endpoints
curl -s https://litigationos.com/api/v1/stats | jq .

# Test rewrites
curl -sI https://litigationos.com/dashboard  # Should return 200
curl -sI https://litigationos.com/omega       # Should return 200

# Verify Stripe webhook (send test event from Stripe dashboard)

# Check Vercel function logs for errors
vercel logs --follow
```

- [ ] Health endpoint returns `200 OK`
- [ ] Security headers present on all responses
- [ ] Dashboard rewrite works
- [ ] OMEGA rewrite works
- [ ] Stripe checkout flow completes
- [ ] Stripe webhook receives test event
- [ ] Cron jobs appear in Vercel dashboard
- [ ] No `better-sqlite3` errors in function logs
- [ ] NEXTAUTH login/logout cycle works
- [ ] SSL certificate valid

---

## 10. Rollback Procedure

```bash
# List recent deployments
vercel ls

# Promote a previous deployment to production
vercel promote <deployment-url>

# Or via dashboard: Deployments → click deployment → "..." → Promote to Production
```
