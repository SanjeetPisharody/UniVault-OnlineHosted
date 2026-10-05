# UniVault

UniVault is a Flask portal for browsing, previewing, downloading, and sharing university study materials.

🌐 **Live Website:** [Visit UniVault](https://univault-bfs0.onrender.com/)

The application is deployed on Render with a stateless architecture backed by **Supabase PostgreSQL** (database) and **Supabase Storage** (uploaded PDFs and profile photos). Local development falls back to SQLite and the local filesystem automatically when the Supabase environment variables are not set.

## Features

* Public material browsing, search, filters, previews, downloads, statistics, and contributor leaderboard.
* Student accounts with uploads, reviews, ratings, upvotes, persistent bookmarks, profile, and account settings.
* Administrator dashboard for users and uploaded materials.
* Protected administrator and owner actions.
* Responsive academic atlas interface with an animated isometric library illustration.
* Resource-type collections.
* Profile photo support for users and material uploaders.
* Cloud-ready: Supabase PostgreSQL for relational data, Supabase Storage for scalable PDF/image uploads.

---

## Cloud Hosting Architecture (Production)

```text
               INTERNET
                  │
                  ▼
           Render (Flask / Gunicorn)
                  │
         ┌────────┴────────┐
         ▼                 ▼
  Supabase Storage   Supabase PostgreSQL
  (PDFs & Images)       (App Data)
```

### Services required

| Service | Role |
|---|---|
| **Render** | Hosts the Flask/Gunicorn web application |
| **Supabase PostgreSQL** | Production relational database |
| **Supabase Storage** | PDF files and profile images |
| **GitHub** | Source control and continuous deployment |

### Supabase setup

1. Create a free project at <https://supabase.com>.
2. From **Project Settings → API**:
   - Copy the **Project URL** → `SUPABASE_URL`
   - Copy the **service_role** secret key → `SUPABASE_SERVICE_ROLE_KEY`
3. From **Storage**, create a **private** bucket named `univault-files` (or whatever you set in `SUPABASE_STORAGE_BUCKET`).
4. From **Project Settings → Database → Connection string**, copy the PostgreSQL URI → `DATABASE_URL`.

### Production deployment on Render

1. Connect Render to this GitHub repository.
2. Render reads `render.yaml` automatically.
3. Set the following **Environment Variables** in the Render dashboard (never commit them):
   - `DATABASE_URL` — Supabase PostgreSQL connection string
   - `UNIVAULT_SECRET_KEY` — a cryptographically secure random string
   - `UNIVAULT_HTTPS` — `true`
   - `SUPABASE_URL` — your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY` — your Supabase service-role key (backend only, never exposed to frontend)
   - `SUPABASE_STORAGE_BUCKET` — `univault-files` (or your chosen bucket name)

### Migrate existing SQLite data to Supabase PostgreSQL

```bash
python scripts/migrate_sqlite_to_postgres.py
```

### Migrate existing local uploads to Supabase Storage

```bash
python scripts/migrate_uploads_to_supabase.py
```

This uploads files from `static/uploads/` to Supabase Storage and updates the database references. Local files are **not** deleted automatically — remove them only after confirming the migration succeeded.

---

## Run locally (development)

SQLite and local file storage are used automatically when the Supabase environment variables are absent.

1. Install requirements:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in values as needed.
3. Start the application:
   ```powershell
   python app.py
   ```

---

## Security notes

* `SUPABASE_SERVICE_ROLE_KEY` is **only** read by Python server-side code. It is never embedded in HTML, JavaScript, templates, or API responses.
* Never commit `.env`, `data/univault.db`, `data/.univault_secret_key`, or `static/uploads/` to GitHub.
* Use a **private** Supabase Storage bucket. Temporary signed URLs (valid for 1 hour) are generated server-side for each download.

---

## Stack

| Layer | Technology |
|---|---|
| Web server | Flask + Gunicorn |
| Database | Supabase PostgreSQL (production) / SQLite (development) |
| File storage | Supabase Storage (production) / `static/uploads/` (development) |
| Hosting | Render |
| Source control | GitHub |
