# Deploying to Render

Changes made to this copy of the project to make it deployable (see chat for the full explanation):

- `Analyze/settings.py`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` now read from
  environment variables instead of being hardcoded. `DATABASES` now uses `dj_database_url`, reading a
  `DATABASE_URL` env var (falls back to local SQLite if that var isn't set, so nothing changes for local dev).
- Added `whitenoise` for static file serving in production, and a `STATIC_ROOT` for `collectstatic`.
- `requirements.txt` re-saved as UTF-8 (it was UTF-16, which breaks `pip install` on Linux hosts) and
  `mysqlclient` swapped for `psycopg2-binary` (Postgres) + added `gunicorn`, `whitenoise`, `dj-database-url`.
- `items.sql` ported to `items_postgres.sql` (Postgres doesn't support backtick-quoted identifiers or
  `INT UNSIGNED`; functionally identical otherwise).
- `AprioriAPI/views.py` now reads `UK_Transactions.csv.gz` instead of the uncompressed CSV (137MB → 1.2MB,
  well under GitHub's 100MB file limit; pandas reads `.gz` natively, no other code changes needed).
- `Frontend/` renamed to `docs/` (GitHub Pages can only serve from the repo root or a `/docs` folder without
  extra config) and merged with the existing `docs/` folder that just held `k_selection_plot.png`. Added
  `docs/index.html` as a landing page linking to both demos, and `docs/.nojekyll` so GitHub doesn't run its
  static pages through Jekyll processing unnecessarily.
- The hardcoded `http://127.0.0.1:8000` wasn't just in `test.js` — `item.html`, `items.html`,
  `knn-parameters.html`, and `apriori-parameters.html` each had their own separate copy. All four now read
  from one new file, `docs/js/config.js` — update the URL in that one place once deployed, instead of four.
- Added DRF request throttling (`AnonRateThrottle`) so the free-tier instance can't be trivially flooded —
  see the settings.py `REST_FRAMEWORK` block.
- Added `.gitignore`, so the raw transactions CSV (raw and gzipped) never gets pushed to GitHub, matching
  the policy your own README already documents under "Known limitations". `association_rules2` — the
  mined, aggregated output — is unaffected and still ships normally; only the live re-fit endpoint
  (`POST /apriori/metrics/...`) needs the raw file, so that endpoint won't work on the public deploy unless
  you separately place the file on the server yourself (see note at the bottom).

## Steps

1. **Push to GitHub.** Create a new repo, and push this folder as-is (the `.gitignore` will keep the
   raw CSV and other junk out automatically).

2. **Create a Render account** at render.com (GitHub sign-in is fastest) if you don't have one.

3. **Create a Postgres database first:** New → PostgreSQL. Free tier is fine. Once it's up, copy its
   **Internal Database URL** — you'll need it in step 5.

4. **Create a Web Service:** New → Web Service → connect your GitHub repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: leave blank (the `Procfile` handles it), or explicitly set
     `python manage.py collectstatic --noinput && gunicorn Analyze.wsgi:application`
   - Instance type: Free

5. **Set environment variables** on the web service (Environment tab):
   - `SECRET_KEY` — generate one, e.g. run `python -c "import secrets; print(secrets.token_urlsafe(50))"` locally
   - `DEBUG` — `False`
   - `DATABASE_URL` — the Internal Database URL from step 3
   - `ALLOWED_HOSTS` — `your-app-name.onrender.com` (Render shows you the exact URL once created; you
     can add it after the first deploy and redeploy)
   - `CORS_ALLOWED_ORIGINS` — if hosting `docs/` on GitHub Pages (see below), set this to
     `https://your-github-username.github.io` exactly — no trailing slash, no path. Otherwise leave as the
     default (`null`), which only permits opening the pages locally via `file://`.
   - `KNN_TUNING_ENABLED` — `False`
   - `APRIORI_TUNING_ENABLED` — `False`

6. **Deploy.** Render will build and start the service automatically on push.

7. **Load the `items` table** (one-time, after the first successful deploy — this table is `managed=False`
   so Django migrations won't create it). From your own machine, using the **External Database URL**
   Render shows you:
   ```
   psql "<external-database-url-from-render>" -f items_postgres.sql
   ```

8. **Update `docs/js/config.js`**: change `API_BASE_URL` to `https://your-app-name.onrender.com`.

## Hosting the frontend on GitHub Pages

This lets you hand a reviewer one link instead of asking them to clone and run anything.

1. On GitHub: repo **Settings → Pages → Build and deployment → Source: "Deploy from a branch"**, branch
   `master`, folder `/docs`. Save.
2. Wait a minute or two, then GitHub shows you the live URL — `https://your-username.github.io/your-repo-name/`.
3. Go back and set `CORS_ALLOWED_ORIGINS` on Render to `https://your-username.github.io` (step 5 above) —
   note this is just the origin (username + `.github.io`), *not* the full URL with the repo name in the
   path; CORS only checks scheme + host, so the repo-name part doesn't matter here. Redeploy for it to
   take effect.
4. Update `docs/index.html`: the "GitHub" link near the top is a placeholder (`href="https://github.com/"`)
   — point it at your actual repo URL.
5. Give out the Pages URL from step 2 — `index.html` links to both demos from there. Skip linking
   `item.html` directly: it expects `items.html` to have set some page state first (which item was
   clicked), so opened cold it'll just show a blank result.

## About the disabled tuning endpoints

Both `POST /knn/parameter/<k>/` and `POST /apriori/metrics/<min_support>/<metric>/<value>/` are switched off
on the public deployment via `KNN_TUNING_ENABLED` / `APRIORI_TUNING_ENABLED`, and return a clean `503` with
an explanation instead of running. Two different reasons, same fix:

- **KNN**: both endpoints share one model file on disk with no per-user isolation — one visitor tuning k
  would silently change every other visitor's classification results. Not a resource problem, a correctness
  one; disabling it was the simpler and safer call for a shared deployment.
- **Apriori**: needs the raw transaction data, which is deliberately not published in this repo (see
  README > Known limitations).

Both work exactly as originally designed when you run the project locally — `KNN_TUNING_ENABLED` and
`APRIORI_TUNING_ENABLED` default to `True` unless explicitly set otherwise, so nothing extra to configure
for local/offline use.
