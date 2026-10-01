# UniVault

UniVault is a Flask portal for browsing, previewing, downloading, and sharing university study materials.

The application has been upgraded for cloud deployment on Render using a stateless architecture backed by Supabase PostgreSQL and Cloudflare R2 for file storage. Local development is still supported using SQLite and the local filesystem.

## Features

* Public material browsing, search, filters, previews, downloads, statistics, and contributor leaderboard.
* Student accounts with uploads, reviews, ratings, upvotes, persistent bookmarks, profile, and account settings.
* Administrator dashboard for users and uploaded materials.
* Protected administrator and owner actions.
* Responsive academic atlas interface with an animated isometric library illustration.
* Resource-type collections.
* Profile photo support for users and material uploaders.
* Cloud-ready storage: PostgreSQL for relational data and Cloudflare R2 for scalable PDF/image uploads.

---

## Cloud Hosting Architecture (Production)

The production environment runs on Render, using:

* **Render:** Hosts the Flask/Gunicorn web application.
* **Supabase PostgreSQL:** Stores all relational data (users, materials, reviews, etc.).
* **Cloudflare R2:** Permanently stores all uploaded user files (PDFs, profile photos).
* **GitHub:** Source code version control and continuous deployment trigger.

```text
               INTERNET
                  │
                  ▼
                Render (Flask / Gunicorn)
                  │
         ┌────────┴────────┐
         ▼                 ▼
   Cloudflare R2     Supabase PostgreSQL
  (PDFs & Images)       (App Data)
```

### Production Setup

1. **Environment Variables**: Configure the following in the Render dashboard:
   - `DATABASE_URL`: Your Supabase PostgreSQL connection string.
   - `UNIVAULT_SECRET_KEY`: A cryptographically secure random string.
   - `UNIVAULT_HTTPS`: Set to `true`.
   - `R2_ACCOUNT_ID`: Cloudflare account ID.
   - `R2_ACCESS_KEY_ID`: Cloudflare R2 access key.
   - `R2_SECRET_ACCESS_KEY`: Cloudflare R2 secret key.
   - `R2_BUCKET_NAME`: The name of your R2 bucket.
   - `R2_PUBLIC_BASE_URL`: (Optional) The public URL for the R2 bucket.
2. **Database Migration**: Run the migration script locally to transfer existing SQLite data to Supabase:
   ```bash
   python scripts/migrate_sqlite_to_postgres.py
   ```
3. **File Migration**: Run the migration script to transfer local uploads to Cloudflare R2:
   ```bash
   python scripts/migrate_uploads_to_r2.py
   ```

---

## Run the website locally (Development)

You can run UniVault locally using the default SQLite database and local filesystem for uploads.

1. Install requirements:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in any necessary overrides. By default, leaving `DATABASE_URL` and `R2_*` variables empty will fall back to local SQLite (`data/univault.db`) and local storage (`static/uploads/`).
3. Start the application:
   ```powershell
   python app.py
   ```

---

## Important distinction

* **GitHub:** Source-code storage and version control.
* **Render:** Cloud hosting platform for the Flask application.
* **Supabase PostgreSQL:** Production database storing UniVault application data.
* **Cloudflare R2:** Production object storage for uploaded files.

Do not commit `.env`, `data/univault.db`, `data/.univault_secret_key`, or `static/uploads/` to GitHub.
