"""Supabase Storage and local filesystem storage abstraction for UniVault."""
import logging
import os
import secrets
import time
from io import BytesIO
from urllib.parse import urlsplit

from werkzeug.utils import secure_filename

logger = logging.getLogger("univault.storage")

# Supabase Client import
try:
    from supabase import create_client
    from storage3.types import FileOptions, URLOptions
except ImportError:
    create_client = None
    FileOptions = None
    URLOptions = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "static", "uploads")
DEFAULT_BUCKET = "univault-files"


def get_supabase_storage_config():
    """Retrieve Supabase Storage configuration from environment variables."""
    return {
        "url": os.environ.get("SUPABASE_URL", "").strip().rstrip("/"),
        "key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        "bucket": os.environ.get("SUPABASE_STORAGE_BUCKET", "").strip() or DEFAULT_BUCKET,
    }


def is_supabase_storage_configured():
    """Check if all required Supabase Storage credentials are provided."""
    cfg = get_supabase_storage_config()
    return bool(cfg["url"] and cfg["key"] and cfg["bucket"])


def get_supabase_storage_client():
    """Create and return a Supabase client configured with the service-role key."""
    if not create_client:
        raise RuntimeError("supabase Python package is required for Supabase Storage but is not installed.")
    cfg = get_supabase_storage_config()
    if not (cfg["url"] and cfg["key"]):
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
    return create_client(cfg["url"], cfg["key"])


def get_storage_bucket():
    """Get the configured Supabase Storage bucket instance."""
    client = get_supabase_storage_client()
    bucket_name = get_supabase_storage_config()["bucket"]
    return client.storage.from_(bucket_name)


def validate_pdf_content(file_bytes):
    """
    Validate that file bytes represent a genuine PDF document.
    Returns (is_valid, error_message).
    """
    if not file_bytes:
        return False, "The uploaded file is empty."
    if len(file_bytes) < 5:
        return False, "The file is too small to be a valid PDF."
    # Check PDF magic bytes '%PDF-'
    if not file_bytes.startswith(b"%PDF-"):
        return False, "Invalid PDF header. The file does not appear to be a valid PDF."
    return True, None


def upload_material_file(file_storage, custom_filename=None):
    """
    Upload a study material file (typically PDF) to Supabase Storage (if configured)
    or local storage fallback.

    Returns a dict with:
        - file_url: the storage object path (e.g. 'materials/...') or local URL
        - file_type: extension string (e.g. 'PDF')
        - file_size_kb: size in KB
        - page_count: number of pages if PDF
        - is_cloud: boolean indicating whether it was stored in Supabase Storage
    """
    original_name = custom_filename or getattr(file_storage, "filename", "document.pdf")
    safe_name = secure_filename(original_name) or "document.pdf"
    ext = safe_name.rsplit(".", 1)[-1].upper() if "." in safe_name else "PDF"

    # Read bytes into memory
    file_bytes = file_storage.read() if hasattr(file_storage, "read") else bytes(file_storage)
    file_size_kb = max(1, (len(file_bytes) + 1023) // 1024)

    # Validate PDF if applicable
    if ext == "PDF":
        is_valid, err = validate_pdf_content(file_bytes)
        if not is_valid:
            raise ValueError(err)

    # Determine page count if pypdf is available
    page_count = 0
    if ext == "PDF":
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(file_bytes))
            page_count = len(reader.pages)
        except Exception:
            page_count = 0

    unique_id = f"{int(time.time() * 1000)}_{secrets.token_hex(4)}"

    if is_supabase_storage_configured():
        cfg = get_supabase_storage_config()
        object_path = f"materials/{unique_id}/{safe_name}"
        content_type = getattr(file_storage, "content_type", None) or ("application/pdf" if ext == "PDF" else "application/octet-stream")

        try:
            bucket = get_storage_bucket()
            upload_kwargs = {"content-type": content_type}
            bucket.upload(
                path=object_path,
                file=file_bytes,
                file_options=upload_kwargs,
            )
            logger.info("Successfully uploaded %s to Supabase Storage bucket %s (%s bytes)", object_path, cfg["bucket"], len(file_bytes))
        except Exception as e:
            logger.error("Failed to upload file to Supabase Storage: %s", str(e))
            raise RuntimeError(f"Cloud storage upload failed: {str(e)}") from e

        return {
            "file_url": object_path,
            "file_type": ext,
            "file_size_kb": file_size_kb,
            "page_count": page_count,
            "is_cloud": True,
        }
    else:
        # Local fallback
        os.makedirs(LOCAL_UPLOAD_FOLDER, exist_ok=True)
        unique_local = f"{unique_id}_{safe_name}"
        local_path = os.path.join(LOCAL_UPLOAD_FOLDER, unique_local)
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        return {
            "file_url": f"/static/uploads/{unique_local}",
            "file_type": ext,
            "file_size_kb": file_size_kb,
            "page_count": page_count,
            "is_cloud": False,
        }


def upload_profile_photo_file(file_storage, user_id):
    """
    Upload a user profile photo to Supabase Storage (if configured) or local storage.
    Returns the URL or object path to store in users.profile_photo.
    """
    original_name = getattr(file_storage, "filename", "avatar.jpg")
    safe_name = secure_filename(original_name) or "avatar.jpg"
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "jpg"

    file_bytes = file_storage.read() if hasattr(file_storage, "read") else bytes(file_storage)
    unique_id = f"user_{user_id}_{int(time.time() * 1000)}_{secrets.token_hex(4)}.{ext}"

    if is_supabase_storage_configured():
        cfg = get_supabase_storage_config()
        object_path = f"profiles/{user_id}/{unique_id}"
        content_type = getattr(file_storage, "content_type", None) or f"image/{ext}"

        try:
            bucket = get_storage_bucket()
            upload_kwargs = {"content-type": content_type}
            bucket.upload(
                path=object_path,
                file=file_bytes,
                file_options=upload_kwargs,
            )
            logger.info("Successfully uploaded profile photo %s to Supabase Storage bucket %s", object_path, cfg["bucket"])
            return object_path
        except Exception as e:
            logger.error("Failed to upload profile photo to Supabase Storage: %s", str(e))
            raise RuntimeError(f"Profile photo cloud upload failed: {str(e)}") from e
    else:
        # Local fallback
        target_dir = os.path.join(LOCAL_UPLOAD_FOLDER, "profile_photos")
        os.makedirs(target_dir, exist_ok=True)
        local_path = os.path.join(target_dir, unique_id)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return f"/static/uploads/profile_photos/{unique_id}"


def get_file_download_url(file_ref, as_attachment=False, download_name=None, expires_in=3600):
    """
    Resolve a stored file reference into an accessible URL.
    - If already an HTTP/HTTPS URL, returns it directly.
    - If a local /static/uploads/... path, returns it.
    - If a Supabase Storage object path, generates a temporary signed URL.
    """
    if not file_ref:
        return None

    # Already an external or full HTTP/HTTPS URL
    if file_ref.startswith(("http://", "https://")):
        return file_ref

    # Local filesystem path
    if file_ref.startswith("/static/uploads/"):
        return file_ref

    # Supabase Storage object path (e.g. 'materials/...' or 'profiles/...')
    if is_supabase_storage_configured():
        try:
            bucket = get_storage_bucket()
            url_options = {}
            if as_attachment:
                if download_name:
                    url_options["download"] = download_name
                else:
                    url_options["download"] = True

            resp = bucket.create_signed_url(
                path=file_ref,
                expires_in=expires_in,
                options=url_options if url_options else None,
            )

            # Response is SignedUrlResponse which is dict-like with 'signedURL' or 'signedUrl'
            signed_url = None
            if isinstance(resp, dict):
                signed_url = resp.get("signedURL") or resp.get("signedUrl")
            elif hasattr(resp, "signed_url"):
                signed_url = resp.signed_url
            elif hasattr(resp, "signedURL"):
                signed_url = resp.signedURL

            return signed_url
        except Exception as e:
            logger.error("Failed to generate signed URL for Supabase object %s: %s", file_ref, str(e))
            return None

    return None


def delete_file(file_ref):
    """Safely delete a file from Supabase Storage or local storage."""
    if not file_ref:
        return

    # Check if Supabase Storage object path
    if not file_ref.startswith(("http://", "https://", "/")) and is_supabase_storage_configured():
        try:
            bucket = get_storage_bucket()
            bucket.remove([file_ref])
            logger.info("Deleted %s from Supabase Storage", file_ref)
        except Exception as e:
            logger.warning("Could not delete %s from Supabase Storage: %s", file_ref, str(e))
        return

    # Local file deletion
    if file_ref.startswith("/static/uploads/"):
        rel_path = file_ref.replace("/static/uploads/", "", 1)
        full_path = os.path.join(LOCAL_UPLOAD_FOLDER, rel_path.replace("/", os.sep))
        if os.path.isfile(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass


def file_exists(file_ref):
    """Check if a file exists in Supabase Storage or local storage."""
    if not file_ref:
        return False

    if file_ref.startswith(("http://", "https://")):
        return True

    if file_ref.startswith("/static/uploads/"):
        rel_path = file_ref.replace("/static/uploads/", "", 1)
        full_path = os.path.join(LOCAL_UPLOAD_FOLDER, rel_path.replace("/", os.sep))
        return os.path.isfile(full_path)

    if is_supabase_storage_configured():
        try:
            bucket = get_storage_bucket()
            return bucket.exists(file_ref)
        except Exception as e:
            logger.warning("Error checking if %s exists in Supabase Storage: %s", file_ref, str(e))
            return False

    return False
