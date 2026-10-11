# Taking this to production: 200 casinos, updated daily

## Infrastructure

I would run this on a single **€5–10/month VPS** (Hetzner CX22 or DigitalOcean droplet, 2 vCPU / 4 GB). A dedicated server is cheaper and simpler than Lambda or Cloud Run for a daily batch job that takes 10-15 minutes — there is no burst traffic to justify serverless. The scraper and the static site live on the same box.

## Database

**PostgreSQL** (on the same VPS, or Supabase's free tier to start). One `casinos` table, one `scrape_runs` table. I would keep the JSON export as a build artefact but PostgreSQL becomes essential once you need to query history, diff changes, or detect when a bonus has changed.

Backups: **pg_dump** to an S3-compatible bucket (Backblaze B2 at ~€0.005/GB) via a nightly cron job, retained for 30 days. Supabase handles this automatically if you go that route.

## Domain, DNS and HTTPS

Register the domain wherever is cheapest (Cloudflare Registrar charges at-cost). Point DNS to **Cloudflare** (free plan) — this gives us a CDN, DDoS protection and automatic HTTPS via their edge certificates. Origin HTTPS via a free Cloudflare Origin CA cert, or Let's Encrypt with certbot auto-renewal.

## Scheduling and monitoring

A **systemd timer** (or cron) triggers `scrape.py` once daily at 06:00 UTC. The script:

1. Fetches each casino page (with retries and exponential backoff).
2. Calls Gemini to structure the bonus text.
3. Writes results to Postgres and exports `casinos.json`.
4. Regenerates the static HTML (or just copies the JSON into the served directory).
5. Exits with a non-zero code if fewer than 180/200 casinos succeeded.

Failure detection: **Healthchecks.io** (free tier, up to 20 checks). The cron job pings a unique URL on success; Healthchecks sends an email/Slack alert if the ping is missed. For richer alerting, a simple Telegram bot notification on any scraper error.

The scraper logs to a file with logrotate. I would add a `/health` endpoint to the site that reports the age of the last scrape — if it is older than 36 hours, the monitoring catches it.

## Scaling from 3 to 200

- **Parallelism**: `asyncio` + `aiohttp` with a semaphore (5-10 concurrent requests) instead of sequential fetches. Polite: respect `Crawl-Delay` and add jitter.
- **LLM costs**: Gemini Flash is ~$0.10/1M tokens. 200 casinos × ~2K tokens each = ~400K tokens/day ≈ $0.04/day. Negligible.
- **Rate limits**: Batch the Gemini calls, 10 at a time, with retries.
- **Change detection**: Hash the scraped HTML; skip the LLM call if nothing changed since yesterday.

## Rough monthly cost

| Item                  | Cost         |
|-----------------------|--------------|
| VPS (Hetzner CX22)   | €5           |
| Domain (year / 12)   | €1           |
| Cloudflare            | Free         |
| Gemini API            | ~€1          |
| Backblaze B2 backups  | ~€0.50       |
| Healthchecks.io       | Free         |
| **Total**             | **~€8/month** |
