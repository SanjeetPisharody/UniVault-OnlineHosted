"""Cloudflare R2 and local filesystem storage abstraction for UniVault."""
import logging
import os
import secrets
import time
from io import BytesIO
from urllib.parse import urlsplit

from werkzeug.utils import secure_filename

logger = logging.getLogger("univault.storage")

# Optional boto3 import
try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    Config = None
    ClientError = Exception

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "static", "uploads")


def get_r2_config():
    """Retrieve Cloudflare R2 credentials from environment variables."""
    return {
        "account_id": os.environ.get("R2_ACCOUNT_ID", "").strip(),
        "access_key": os.environ.get("R2_ACCESS_KEY_ID", "").strip(),
        "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket_name": os.environ.get("R2_BUCKET_NAME", "").strip(),
        "public_base_url": os.environ.get("R2_PUBLIC_BASE_URL", "").strip().rstrip("/"),
    }


def is_r2_configured():
    """Check if all required Cloudflare R2 credentials are provided."""
    cfg = get_r2_config()
    return bool(cfg["account_id"] and cfg["access_key"] and cfg["secret_key"] and cfg["bucket_name"])


def get_s3_client():
    """Create and return an S3-compatible client for Cloudflare R2."""
    if not boto3:
        raise RuntimeError("boto3 is required for Cloudflare R2 storage but is not installed.")
    cfg = get_r2_config()
    endpoint_url = f"https://{cfg['account_id']}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=cfg["access_key"],
        aws_secret_access_key=cfg["secret_key"],
        region_name="auto",
        config=Config(signature_version="s3v4") if Config else None,
    )


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
    Upload a study material file (typically PDF) to R2 (if configured) or local storage.
    
    Returns a dict with:
        - file_url: the path/key or public URL to store in the database
        - file_type: extension string (e.g. 'PDF')
        - file_size_kb: size in KB
        - page_count: number of pages if PDF
        - is_cloud: boolean indicating whether it was stored in R2
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

    if is_r2_configured():
        cfg = get_r2_config()
        object_key = f"materials/{unique_id}/{safe_name}"
        s3 = get_s3_client()
        content_type = getattr(file_storage, "content_type", None) or "application/pdf" if ext == "PDF" else "application/octet-stream"

        try:
            s3.put_object(
                Bucket=cfg["bucket_name"],
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type,
                Metadata={
                    "original_filename": safe_name,
                    "uploaded_at": str(int(time.time())),
                },
            )
            logger.info("Successfully uploaded %s to R2 (%s bytes)", object_key, len(file_bytes))
        except Exception as e:
            logger.error("Failed to upload file to Cloudflare R2: %s", str(e))
            raise RuntimeError("Cloud storage upload failed.") from e

        return {
            "file_url": object_key,
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
    Upload a user profile photo to R2 (if configured) or local storage.
    Returns the URL/path to store in users.profile_photo.
    """
    original_name = getattr(file_storage, "filename", "avatar.jpg")
    safe_name = secure_filename(original_name) or "avatar.jpg"
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "jpg"

    file_bytes = file_storage.read() if hasattr(file_storage, "read") else bytes(file_storage)
    unique_id = f"user_{user_id}_{int(time.time() * 1000)}_{secrets.token_hex(4)}.{ext}"

    if is_r2_configured():
        cfg = get_r2_config()
        object_key = f"profile_photos/{unique_id}"
        s3 = get_s3_client()
        content_type = getattr(file_storage, "content_type", None) or f"image/{ext}"

        s3.put_object(
            Bucket=cfg["bucket_name"],
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )

        if cfg["public_base_url"]:
            return f"{cfg['public_base_url']}/{object_key}"
        # If no public base URL, store object key; get_file_download_url will generate signed URL
        return object_key
    else:
        # Local fallback
        target_dir = os.path.join(LOCAL_UPLOAD_FOLDER, "profile_photos")
        os.makedirs(target_dir, exist_ok=True)
        local_path = os.path.join(target_dir, unique_id)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return f"/static/uploads/profile_photos/{unique_id}"


def get_file_download_url(file_ref, as_attachment=False, download_name=None):
    """
    Resolve a stored file reference into an accessible URL.
    - If already an HTTP/HTTPS URL, returns it directly.
    - If a local /static/uploads/... path, returns it.
    - If an R2 object key, returns a public URL or a secure presigned URL.
    """
    if not file_ref:
        return None

    # Already an external or full HTTP/HTTPS URL
    if file_ref.startswith(("http://", "https://")):
        return file_ref

    # Local filesystem path
    if file_ref.startswith("/static/uploads/"):
        return file_ref

    # R2 object key (e.g. 'materials/...' or 'profile_photos/...')
    if is_r2_configured():
        cfg = get_r2_config()
        if cfg["public_base_url"]:
            return f"{cfg['public_base_url']}/{file_ref}"

        try:
            s3 = get_s3_client()
            params = {
                "Bucket": cfg["bucket_name"],
                "Key": file_ref,
            }
            safe_download_name = download_name or os.path.basename(file_ref)
            disp_type = "attachment" if as_attachment else "inline"
            params["ResponseContentDisposition"] = f'{disp_type}; filename="{safe_download_name}"'

            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=3600,
            )
            return presigned_url
        except Exception as e:
            logger.error("Failed to generate presigned URL for %s: %s", file_ref, str(e))
            return None

    return None


def delete_file(file_ref):
    """Safely delete a file from R2 or local storage."""
    if not file_ref:
        return

    # Check if R2 object key
    if not file_ref.startswith(("http://", "https://", "/")) and is_r2_configured():
        try:
            cfg = get_r2_config()
            s3 = get_s3_client()
            s3.delete_object(Bucket=cfg["bucket_name"], Key=file_ref)
            logger.info("Deleted %s from R2", file_ref)
        except Exception as e:
            logger.warning("Could not delete %s from R2: %s", file_ref, str(e))
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
