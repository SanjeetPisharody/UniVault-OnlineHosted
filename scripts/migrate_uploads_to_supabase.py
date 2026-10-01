"""
Migrate existing local uploads to Supabase Storage and update the database.

Usage:
    Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET and
    DATABASE_URL in your .env, then run:

        python scripts/migrate_uploads_to_supabase.py

Safe to rerun: files already migrated (whose file_url no longer starts with
/static/uploads/) are skipped automatically.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import storage


class _FileStorageWrapper:
    """Minimal wrapper so storage.upload_material_file / upload_profile_photo_file
    can consume an open file handle without Flask's FileStorage."""

    def __init__(self, fh, filename):
        self._fh = fh
        self.filename = filename
        self.content_type = None

    def read(self):
        return self._fh.read()


def migrate():
    if not storage.is_supabase_storage_configured():
        print("ERROR: Supabase Storage is not configured.\n"
              "Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and "
              "SUPABASE_STORAGE_BUCKET in your .env file.")
        sys.exit(1)

    conn = database.get_connection()
    errors = 0

    # ── Materials ───────────────────────────────────────────────────────────────
    print("\n── Migrating material files ──")
    materials = conn.execute(
        "SELECT id, file_url FROM materials WHERE file_url LIKE '/static/uploads/%'"
    ).fetchall()

    if not materials:
        print("  No local material files to migrate.")
    else:
        for mat in materials:
            mat_id = mat["id"]
            file_url = mat["file_url"]
            local_path = os.path.join(
                storage.LOCAL_UPLOAD_FOLDER, os.path.basename(file_url)
            )

            if not os.path.exists(local_path):
                print(f"  WARN  material {mat_id}: local file not found at {local_path}")
                errors += 1
                continue

            try:
                with open(local_path, "rb") as fh:
                    wrapper = _FileStorageWrapper(fh, os.path.basename(file_url))
                    result = storage.upload_material_file(wrapper)

                new_path = result["file_url"]
                conn.execute(
                    "UPDATE materials SET file_url=? WHERE id=?",
                    (new_path, mat_id),
                )
                conn.commit()
                print(f"  OK    material {mat_id}: {file_url} → {new_path}")
            except Exception as exc:
                print(f"  ERROR material {mat_id}: {exc}")
                errors += 1

    # ── Profile photos ──────────────────────────────────────────────────────────
    print("\n── Migrating profile photos ──")
    users = conn.execute(
        "SELECT id, profile_photo FROM users "
        "WHERE profile_photo LIKE '/static/uploads/profile_photos/%'"
    ).fetchall()

    if not users:
        print("  No local profile photos to migrate.")
    else:
        for u in users:
            u_id = u["id"]
            photo_url = u["profile_photo"]
            local_path = os.path.join(
                storage.LOCAL_UPLOAD_FOLDER,
                "profile_photos",
                os.path.basename(photo_url),
            )

            if not os.path.exists(local_path):
                print(f"  WARN  user {u_id}: local photo not found at {local_path}")
                errors += 1
                continue

            try:
                with open(local_path, "rb") as fh:
                    wrapper = _FileStorageWrapper(fh, os.path.basename(photo_url))
                    new_path = storage.upload_profile_photo_file(wrapper, u_id)

                conn.execute(
                    "UPDATE users SET profile_photo=? WHERE id=?",
                    (new_path, u_id),
                )
                conn.commit()
                print(f"  OK    user {u_id}: {photo_url} → {new_path}")
            except Exception as exc:
                print(f"  ERROR user {u_id}: {exc}")
                errors += 1

    conn.close()

    print()
    if errors:
        print(f"Migration completed with {errors} error(s). "
              "Review the output above and rerun as needed.")
    else:
        print("Migration completed successfully.")
    print("Local files were NOT deleted. Remove them manually after confirming "
          "that Supabase Storage contains all expected files.")


if __name__ == "__main__":
    migrate()
