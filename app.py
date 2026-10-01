"""UniVault local Flask application."""
import hmac
from io import BytesIO
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlsplit

from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import database
import storage
from dotenv import load_dotenv

load_dotenv()

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "static", "uploads")
PROFILE_PHOTO_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "profile_photos"
)

os.makedirs(PROFILE_PHOTO_FOLDER, exist_ok=True)

def get_secret_key():
    """Prefer the owner's environment key; otherwise persist a random local key."""
    configured = os.environ.get("UNIVAULT_SECRET_KEY")
    if configured:
        return configured
    os.makedirs(database.DATA_DIR, exist_ok=True)
    key_path = os.path.join(database.DATA_DIR, ".univault_secret_key")
    try:
        with open(key_path, "x", encoding="utf-8") as key_file:
            key_file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    with open(key_path, "r", encoding="utf-8") as key_file:
        return key_file.read().strip()


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update(
    SECRET_KEY=get_secret_key(),
    MAX_CONTENT_LENGTH=32 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("UNIVAULT_HTTPS", "").lower() in ("1", "true", "yes"),
)
if not os.environ.get("UNIVAULT_SECRET_KEY"):
    app.logger.info("UNIVAULT_SECRET_KEY is unset; using a cryptographically random key stored in the ignored data/.univault_secret_key file.")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
try:
    database.init_db()
except Exception:
    app.logger.exception("Could not initialize the permanent UniVault database at %s", database.DATABASE_PATH)
    raise

FAILED_LOGINS = {}
LOGIN_LIMIT = 8
LOGIN_WINDOW = 300
LOGIN_DELAY = 0.45
MAX_PASSWORD_LENGTH = 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "zip", "png", "jpg", "jpeg"}
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(24))


def current_user():
    if "current_user" not in g:
        uid = session.get("user_id")

        if uid:
            conn = database.get_connection()

            row = conn.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    role,
                    created_at,
                    is_active,
                    must_change_password,
                    is_owner,
                    profile_photo
                FROM users
                WHERE id=?
                """,
                (uid,)
            ).fetchone()

            conn.close()

            g.current_user = (
                dict(row)
                if row and row["is_active"]
                else None
            )
        else:
            g.current_user = None

    return g.current_user

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            if request.path.startswith("/api/"):
                return jsonify(error="Authentication required."), 401
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped


def student_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user()["role"] != "student":
            return (jsonify(error="Forbidden."), 403) if request.path.startswith("/api/") else abort(403)
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user()["role"] != "admin":
            return (jsonify(error="Forbidden."), 403) if request.path.startswith("/api/") else abort(403)
        return fn(*args, **kwargs)
    return wrapped


@app.before_request
def protect_requests():
    token = session.get("csrf_token")
    if not token:
        session["csrf_token"] = secrets.token_urlsafe(32)
        token = session["csrf_token"]
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        submitted = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not submitted or not hmac.compare_digest(token, submitted):
            return (jsonify(error="Invalid security token. Refresh the page and try again."), 400) if request.path.startswith("/api/") else ("Invalid security token. Refresh the page and try again.", 400)
    user = current_user()
    if user and user.get("must_change_password") and request.endpoint not in {"change_password", "logout", "static", "serve_static_asset"}:
        if request.path.startswith("/api/"):
            return jsonify(error="Change your initial password before continuing.", change_password_required=True), 403
        return redirect(url_for("change_password"))


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.context_processor
def template_context():
    return {"user": current_user(), "csrf_token": session.get("csrf_token")}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html", stats=database.get_stats(), filters=database.get_filter_options(),
                           leaderboard=database.get_leaderboard(limit=5),
                           initial_materials=database.get_materials(page=1, per_page=12).get("materials", []),
                           initial_total=database.get_materials(page=1, per_page=12).get("total", 0))


@app.route("/static/<path:filename>", endpoint="serve_static_asset")
def serve_static_asset(filename):
    normalized = filename.replace("\\", "/")
    if normalized.startswith("uploads/"):
        user = current_user()
        is_admin = bool(user and user.get("role") == "admin")
        if not is_admin:
            public_url = f"/static/{normalized}"
            conn = database.get_connection()
            if normalized.startswith("uploads/profile_photos/"):
                visible = conn.execute(
                    """
                    SELECT 1 FROM users WHERE profile_photo=?
                    UNION ALL
                    SELECT 1 FROM materials WHERE status='approved' AND uploader_avatar=?
                    UNION ALL
                    SELECT 1 FROM contributors WHERE avatar=?
                    LIMIT 1
                    """,
                    (public_url, public_url, public_url),
                ).fetchone()
            else:
                visible = conn.execute(
                    "SELECT 1 FROM materials WHERE status='approved' AND file_url=? LIMIT 1",
                    (public_url,),
                ).fetchone()
            conn.close()
            if not visible:
                abort(404)
    return send_from_directory(app.static_folder, filename)


# Flask registers its built-in static endpoint before custom routes. Replace
# its view so uploaded files receive the same authorization check above.
app.view_functions["static"] = serve_static_asset


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ip = request.remote_addr or "unknown"
        now = time.time()
        attempts = [t for t in FAILED_LOGINS.get(ip, []) if now - t < LOGIN_WINDOW]
        if len(attempts) >= LOGIN_LIMIT:
            error = "Too many failed attempts. Please try again in a few minutes."
        elif len(username) > 32 or len(password) > MAX_PASSWORD_LENGTH:
            check_password_hash(DUMMY_PASSWORD_HASH, "invalid-input")
            time.sleep(LOGIN_DELAY)
            attempts.append(now)
            FAILED_LOGINS[ip] = attempts
            error = "Invalid username or password."
        else:
            conn = database.get_connection()
            row = conn.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (username,)).fetchone()
            conn.close()
            password_ok = check_password_hash(row["password_hash"] if row else DUMMY_PASSWORD_HASH, password)
            valid = bool(row and row["is_active"] and password_ok)
            if valid:
                FAILED_LOGINS.pop(ip, None)
                session.clear()
                session["user_id"] = row["id"]
                session["csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("change_password") if row["must_change_password"] else url_for("index"))
            time.sleep(LOGIN_DELAY)
            attempts.append(now)
            FAILED_LOGINS[ip] = attempts
            error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or len(name) > 80:
            error = "Enter your name (80 characters or fewer)."
        elif not (3 <= len(username) <= 32) or not all(ch.isalnum() or ch in "._-" for ch in username):
            error = "Username must be 3–32 characters and use letters, numbers, dots, underscores, or hyphens."
        elif len(password) < 10 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            error = "Use at least 10 characters with at least one letter and one number."
        elif len(password) > MAX_PASSWORD_LENGTH:
            error = f"Passwords must be {MAX_PASSWORD_LENGTH} characters or fewer."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            conn = database.get_connection()
            try:
                conn.execute("INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,'student')",
                             (name, username, generate_password_hash(password)))
                conn.commit()
                return redirect(url_for("login", registered="1"))
            except database.IntegrityError:
                error = "That username is already in use."
            finally:
                conn.close()
    return render_template("register.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/profile/photo", methods=["POST"])
@login_required
def upload_profile_photo():
    user = current_user()

    if "profile_photo" not in request.files:
        return redirect(url_for("profile", photo_error="missing"))

    file = request.files["profile_photo"]

    if not file or not file.filename:
        return redirect(url_for("profile", photo_error="missing"))

    filename = secure_filename(file.filename)

    if not filename:
        return redirect(url_for("profile", photo_error="invalid"))

    extension = (
        filename.rsplit(".", 1)[1].lower()
        if "." in filename
        else ""
    )

    allowed_extensions = {"jpg", "jpeg", "png", "webp"}

    if extension not in allowed_extensions:
        return redirect(url_for("profile", photo_error="format"))

    photo_url = storage.upload_profile_photo_file(file, user["id"])

    conn = database.get_connection()

    old = conn.execute(
        "SELECT profile_photo FROM users WHERE id=?",
        (user["id"],)
    ).fetchone()

    conn.execute(
        "UPDATE users SET profile_photo=? WHERE id=?",
        (photo_url, user["id"])
    )

    conn.commit()
    conn.close()

    # Remove previous profile photo.
    if old and old["profile_photo"] and old["profile_photo"] != photo_url:
        storage.delete_file(old["profile_photo"])

    return redirect(url_for("profile", photo_updated="1"))
@app.route("/profile")
@login_required
def profile():
    user = current_user()
    photo_message = None
    photo_message_is_error = False
    if request.args.get("photo_updated") == "1":
        photo_message = "Your profile photo has been updated."
    else:
        photo_errors = {
            "missing": "Choose a photo before uploading.",
            "invalid": "The selected file name is not valid.",
            "format": "Choose a JPG, PNG or WEBP image.",
        }
        photo_message = photo_errors.get(request.args.get("photo_error"))
        photo_message_is_error = photo_message is not None

    conn = database.get_connection()

    uploads = conn.execute(
        "SELECT COUNT(*) FROM materials WHERE uploader_user_id=?",
        (user["id"],)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        uploads=uploads,
        photo_message=photo_message,
        photo_message_is_error=photo_message_is_error,
    )


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        old = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        conn = database.get_connection()
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (current_user()["id"],)).fetchone()
        if not row or not check_password_hash(row["password_hash"], old):
            error = "Current password is incorrect."
        elif len(new) < 10 or not any(c.isalpha() for c in new) or not any(c.isdigit() for c in new):
            error = "Use at least 10 characters with at least one letter and one number."
        elif len(new) > MAX_PASSWORD_LENGTH:
            error = f"Passwords must be {MAX_PASSWORD_LENGTH} characters or fewer."
        elif new != confirm:
            error = "Passwords do not match."
        else:
            conn.execute("UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?",
                         (generate_password_hash(new), current_user()["id"]))
            conn.commit(); conn.close()
            return redirect(url_for("profile"))
        conn.close()
    return render_template("change_password.html", error=error)


@app.route("/account/delete", methods=["POST"])
@student_required
def delete_account():
    password = request.form.get("password", "")
    if request.form.get("confirm_delete") != "DELETE":
        return render_template("profile.html", error="Type DELETE to confirm account removal.")
    conn = database.get_connection()
    row = conn.execute("SELECT password_hash FROM users WHERE id=?", (current_user()["id"],)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        conn.close()
        return render_template("profile.html", error="Current password is incorrect.")
    uid = current_user()["id"]
    # Retain submitted educational materials and their public contributor history.
    conn.execute("UPDATE materials SET uploader_user_id=NULL WHERE uploader_user_id=?", (uid,))
    conn.execute("UPDATE materials SET upvotes_count=CASE WHEN upvotes_count>0 THEN upvotes_count-1 ELSE 0 END WHERE id IN (SELECT material_id FROM material_upvotes WHERE user_id=?)", (uid,))
    conn.execute("UPDATE reviews SET user_id=NULL, author_name='Former student' WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit(); conn.close(); session.clear()
    return redirect(url_for("index"))


@app.route("/my-uploads")
@student_required
def my_uploads():
    conn=database.get_connection()
    uploads=[dict(r) for r in conn.execute("SELECT id,title,subject_name,status,created_at FROM materials WHERE uploader_user_id=? ORDER BY id DESC",(current_user()["id"],))]
    conn.close()
    return render_template("my_uploads.html", uploads=uploads)


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn=database.get_connection()
    users=[dict(r) for r in conn.execute("SELECT id,name,username,role,created_at,is_active,is_owner FROM users ORDER BY role DESC,username")]
    materials=[dict(r) for r in conn.execute("SELECT id,title,uploader_name,status,created_at FROM materials ORDER BY id DESC LIMIT 100")]
    reviews=[dict(r) for r in conn.execute("SELECT r.id,r.author_name,r.comment,r.rating,m.title material_title FROM reviews r JOIN materials m ON m.id=r.material_id ORDER BY r.id DESC LIMIT 100")]
    stats=database.get_stats()
    conn.close()
    return render_template("admin.html", users=users, materials=materials, reviews=reviews, stats=stats)


@app.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_create_administrator():
    data = request.get_json(silent=True) or request.form
    if not hasattr(data, "get"):
        return jsonify(error="Invalid administrator details."),400
    name = str(data.get("name", "")).strip()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    if not name or len(name) > 80:
        return jsonify(error="Enter a name of 1 to 80 characters."), 400
    if not (3 <= len(username) <= 32) or not all(ch.isalnum() or ch in "._-" for ch in username):
        return jsonify(error="Username must be 3–32 characters and use letters, numbers, dots, underscores, or hyphens."), 400
    if len(password) < 10 or not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        return jsonify(error="Use a password with at least 10 characters, including a letter and a number."), 400
    if len(password) > MAX_PASSWORD_LENGTH:
        return jsonify(error=f"Passwords must be {MAX_PASSWORD_LENGTH} characters or fewer."), 400
    if password != confirm_password:
        return jsonify(error="The passwords do not match."), 400

    conn = database.get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users(name,username,password_hash,role,must_change_password) VALUES(?,?,?,'admin',1)",
            (name, username, generate_password_hash(password)),
        )
        conn.commit()
        return jsonify(success=True, user={"id": cursor.lastrowid, "name": name, "username": username, "role": "admin"}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify(error="That username is already in use."), 409
    finally:
        conn.close()


@app.route("/api/admin/users/<int:user_id>", methods=["POST"])
@admin_required
def admin_user_action(user_id):
    data = request.get_json(silent=True) if request.is_json else request.form
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify(error="Invalid user action."),400
    action=data.get("action")

    actor = current_user()

    conn = database.get_connection()

    target = conn.execute(
        """
        SELECT
            id,
            username,
            role,
            is_active,
            is_owner
        FROM users
        WHERE id=?
        """,
        (user_id,)
    ).fetchone()

    if not target:
        conn.close()
        return jsonify(error="User not found."), 404

    # ---------------------------------------------------------
    # PERMANENT OWNER PROTECTION
    # ---------------------------------------------------------
    # The permanent owner cannot be modified by another admin.
    if target["is_owner"] and target["id"] != actor["id"]:
        conn.close()
        return jsonify(
            error=(
                "The UniVault owner account is permanently protected "
                "from other administrators."
            )
        ), 403

    # ---------------------------------------------------------
    # Prevent removing the last active administrator
    # ---------------------------------------------------------
    if target["role"] == "admin" and action in {"demote", "delete"}:
        remaining = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='admin'
              AND is_active=1
            """
        ).fetchone()[0]

        if remaining <= 1:
            conn.close()
            return jsonify(
                error="The last active administrator cannot be removed."
            ), 409

    # ---------------------------------------------------------
    # Promote
    # ---------------------------------------------------------
    if action == "promote":
        conn.execute(
            "UPDATE users SET role='admin' WHERE id=?",
            (user_id,)
        )

    # ---------------------------------------------------------
    # Demote
    # ---------------------------------------------------------
    elif action == "demote":

        if user_id == actor["id"]:
            conn.close()
            return jsonify(
                error="You cannot demote your own account."
            ), 400

        conn.execute(
            "UPDATE users SET role='student' WHERE id=?",
            (user_id,)
        )

    # ---------------------------------------------------------
    # Suspend
    # ---------------------------------------------------------
    elif action == "suspend":

        if target["role"] == "admin":
            conn.close()
            return jsonify(
                error="Administrator accounts cannot be suspended here."
            ), 403

        conn.execute(
            "UPDATE users SET is_active=0 WHERE id=?",
            (user_id,)
        )

    # ---------------------------------------------------------
    # Activate
    # ---------------------------------------------------------
    elif action == "activate":

        conn.execute(
            "UPDATE users SET is_active=1 WHERE id=?",
            (user_id,)
        )

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------
    elif action == "delete":

        if target["role"] == "admin":
            conn.close()
            return jsonify(
                error="Demote an administrator before deleting the account."
            ), 400

        conn.execute(
            """
            UPDATE materials
            SET uploader_user_id=NULL
            WHERE uploader_user_id=?
            """,
            (user_id,)
        )

        conn.execute(
            """
            UPDATE materials
            SET upvotes_count=CASE WHEN upvotes_count>0 THEN upvotes_count-1 ELSE 0 END
            WHERE id IN (
                SELECT material_id
                FROM material_upvotes
                WHERE user_id=?
            )
            """,
            (user_id,)
        )

        conn.execute(
            """
            UPDATE reviews
            SET user_id=NULL,
                author_name='Former student'
            WHERE user_id=?
            """,
            (user_id,)
        )

        conn.execute(
            "DELETE FROM users WHERE id=?",
            (user_id,)
        )

    # ---------------------------------------------------------
    # Invalid action
    # ---------------------------------------------------------
    else:
        conn.close()
        return jsonify(error="Invalid action."), 400

    conn.commit()
    conn.close()

    return jsonify(success=True)


@app.route("/api/admin/materials/<int:material_id>", methods=["POST"])
@admin_required
def admin_material_action(material_id):
    data=request.get_json(silent=True) if request.is_json else request.form
    if data is None:
        data=request.form
    if not hasattr(data,"get"):
        return jsonify(error="Invalid material action."),400
    action=data.get("action")
    conn=database.get_connection()
    if action in {"approve","reject"}:
        conn.execute("UPDATE materials SET status=? WHERE id=?",("approved" if action=="approve" else "rejected",material_id))
    elif action=="delete":
        row=conn.execute("SELECT file_url FROM materials WHERE id=?",(material_id,)).fetchone()
        if not row: conn.close(); return jsonify(error="Material not found."),404
        conn.execute("DELETE FROM materials WHERE id=?",(material_id,))
        path=row["file_url"] or ""
        storage.delete_file(path)
    else: conn.close(); return jsonify(error="Invalid action."),400
    conn.commit(); conn.close(); return jsonify(success=True)


@app.route("/api/admin/reviews/<int:review_id>", methods=["DELETE"])
@admin_required
def admin_delete_review(review_id):
    conn=database.get_connection()
    result=conn.execute("DELETE FROM reviews WHERE id=?",(review_id,))
    conn.commit(); conn.close()
    if result.rowcount == 0: return jsonify(error="Review not found."),404
    return jsonify(success=True)


@app.route("/api/health")
def health_check():
    return jsonify(status="healthy",service="UniVault Notes Portal API",timestamp=datetime.now(timezone.utc).isoformat())


@app.route("/api/materials", methods=["GET"])
def list_materials():
    try:
        page=max(1,int(request.args.get("page",1))); per_page=min(50,max(1,int(request.args.get("per_page",12))))
    except ValueError: page,per_page=1,12
    return jsonify(database.get_materials(search=request.args.get("search",""),branch=request.args.get("branch","all"),
      semester=request.args.get("semester","all"),university=request.args.get("university","all"),
      material_type=request.args.get("material_type","all"),sort_by=request.args.get("sort_by","popular"),page=page,per_page=per_page))


@app.route("/api/materials/<int:material_id>")
def get_material(material_id):
    item=database.get_material_by_id(material_id)
    if not item: return jsonify(error="Material not found"),404
    database.increment_views(material_id); item["views_count"]+=1; return jsonify(item)


@app.route("/api/materials", methods=["POST"])
@student_required
def upload_material():
    data=request.get_json(silent=True)
    if data is None:
        data=request.form.to_dict()
    if not isinstance(data,dict):
        return jsonify(error="Invalid material details."),400

    text_defaults={
        "title":"", "subject_name":"", "file_url":"", "description":"Student shared notes and study material.",
        "subject_code":"GEN-101", "branch":"Computer Science & Engineering", "semester":"Semester 1",
        "university":"General University", "material_type":"Lecture Notes", "academic_year":str(datetime.now().year),
        "tags":"", "preview_content":"",
    }
    text_limits={"title":200,"subject_name":160,"file_url":2048,"description":20000,"subject_code":40,
                 "branch":160,"semester":40,"university":200,"material_type":100,"academic_year":20,
                 "tags":2000,"preview_content":20000}
    text_data={}
    for key,default in text_defaults.items():
        value=data.get(key,default)
        if not isinstance(value,str):
            return jsonify(error=f"{key.replace('_',' ').capitalize()} must be text."),400
        if len(value)>text_limits[key]:
            return jsonify(error=f"{key.replace('_',' ').capitalize()} is too long."),400
        text_data[key]=value

    title=text_data["title"].strip(); subject=text_data["subject_name"].strip()
    if not title or not subject: return jsonify(error="Title and Subject Name are required fields"),400
    file_url=text_data["file_url"].strip(); file_type="PDF"; size=0; pages=0
    has_file = "file" in request.files and bool(request.files["file"].filename)
    if not has_file and file_url:
        try:
            parsed_url = urlsplit(file_url)
            parsed_url.port  # Access validates that a supplied port is numeric and in range.
            valid_direct_url = (
                parsed_url.scheme.lower() in {"http", "https"}
                and bool(parsed_url.hostname)
                and parsed_url.username is None
                and parsed_url.password is None
                and not any(ord(char) < 32 or char.isspace() for char in file_url)
            )
        except ValueError:
            valid_direct_url = False
        if not valid_direct_url:
            return jsonify(error="Provide a valid public HTTP or HTTPS file link."),400
    if has_file:
        file=request.files["file"]
        if not allowed_file(file.filename): return jsonify(error="Unsupported file type."),400
        try:
            result = storage.upload_material_file(file)
            file_url = result["file_url"]
            file_type = result["file_type"]
            size = result["file_size_kb"]
            pages = result["page_count"]
        except ValueError as e:
            return jsonify(error=str(e)), 400
        except Exception:
            return jsonify(error="Failed to process and upload file."), 500
    elif not file_url:
        file_url="/api/materials/0/file"
    try: size=size or max(1,int(data.get("file_size_kb",1)))
    except (ValueError,TypeError): size=1
    try: pages=pages or max(0,int(data.get("page_count",0)))
    except (ValueError,TypeError): pages=0
    user=current_user()
    payload={"title":title,"description":text_data["description"],
      "subject_name":subject,"subject_code":text_data["subject_code"],"branch":text_data["branch"],
      "semester":text_data["semester"],"university":text_data["university"],
      "material_type":text_data["material_type"],"academic_year":text_data["academic_year"],
      "file_url":file_url,"file_type":file_type,"file_size_kb":size,"page_count":pages,"uploader_name":user["name"],
      "uploader_avatar": user.get("profile_photo", ""),"tags":text_data["tags"],"preview_content":text_data["preview_content"] or text_data["description"] or "Preview not available."}
    mid=database.create_material(payload,uploader_user_id=user["id"])
    conn=database.get_connection(); conn.execute("UPDATE materials SET file_url=? WHERE id=? AND file_url LIKE '/api/materials/0/file'",(f"/api/materials/{mid}/file",mid)); conn.commit(); conn.close()
    return jsonify(success=True,message="Material uploaded successfully.",material_id=mid,file_size_kb=size,page_count=pages),201


@app.route("/api/materials/<int:material_id>/file")
def download_material_file(material_id):
    item=database.get_material_by_id(material_id)
    if not item: return jsonify(error="Material not found"),404
    path_value=item.get("file_url","")
    url = storage.get_file_download_url(path_value, as_attachment=True)
    if url:
        if url.startswith(("http://", "https://")):
            return redirect(url)
        elif url.startswith("/static/uploads/"):
            filename=os.path.basename(url); path=os.path.join(UPLOAD_FOLDER,filename)
            if os.path.isfile(path): return send_file(path,as_attachment=True,download_name=filename)
    # Read-only compatibility for legacy files that were already stored as SQLite BLOBs.
    file_data,stored_type=database.get_material_file_data(material_id)
    if file_data:
        filename=f"UniVault_Material_{material_id}.{(stored_type or 'bin').lower()}"
        return send_file(BytesIO(file_data),mimetype="application/octet-stream",as_attachment=True,download_name=filename)
    return jsonify(error="This material has no uploaded file"),404


@app.route("/api/materials/<int:material_id>/upvote", methods=["POST"])
@student_required
def upvote_material(material_id):
    if not database.get_material_by_id(material_id): return jsonify(error="Material not found"),404
    count,duplicate=database.increment_upvote(material_id,current_user()["id"])
    return jsonify(success=True,upvotes_count=count,already_upvoted=duplicate)


@app.route("/api/materials/<int:material_id>/download", methods=["POST"])
def track_download(material_id):
    if not database.get_material_by_id(material_id): return jsonify(error="Material not found."),404
    result=database.increment_download(material_id)
    return jsonify(success=True,downloads_count=result["downloads_count"],file_url=url_for("download_material_file",material_id=material_id))


@app.route("/api/materials/<int:material_id>/reviews", methods=["POST"])
@student_required
def submit_review(material_id):
    data=request.get_json(silent=True)
    if data is None:
        data=request.form.to_dict()
    if not isinstance(data,dict): return jsonify(error="Invalid review details."),400
    comment=data.get("comment","")
    if not isinstance(comment,str): return jsonify(error="Review comment must be text."),400
    comment=comment.strip()
    if not comment: return jsonify(error="Review comment cannot be empty"),400
    if len(comment)>5000: return jsonify(error="Review comments must be 5,000 characters or fewer."),400
    try: rating=int(data.get("rating",5))
    except (TypeError,ValueError): return jsonify(error="Rating must be from 1 to 5."),400
    if not 1 <= rating <= 5: return jsonify(error="Rating must be from 1 to 5."),400
    if not database.get_material_by_id(material_id): return jsonify(error="Material not found."),404
    review_id=database.create_review(material_id,current_user()["name"],rating,comment,current_user()["id"])
    return jsonify(success=True,message="Review submitted successfully!",review_id=review_id),201


@app.route("/api/bookmarks", methods=["GET"])
@student_required
def get_bookmarks():
    conn=database.get_connection()
    rows=[dict(r) for r in conn.execute("""SELECT m.id,m.title,m.subject_name,m.subject_code,m.material_type,m.file_url,m.university
        FROM bookmarks b JOIN materials m ON m.id=b.material_id WHERE b.user_id=? ORDER BY b.id DESC""",(current_user()["id"],))]
    conn.close(); return jsonify(bookmarks=rows)


@app.route("/api/user-state")
@student_required
def get_user_state():
    conn=database.get_connection(); uid=current_user()["id"]
    bookmarks=[dict(r) for r in conn.execute("""SELECT m.id,m.title,m.subject_name,m.subject_code,m.material_type,m.file_url,m.university
        FROM bookmarks b JOIN materials m ON m.id=b.material_id WHERE b.user_id=?""",(uid,))]
    upvotes=[r[0] for r in conn.execute("SELECT material_id FROM material_upvotes WHERE user_id=?",(uid,))]
    conn.close(); return jsonify(bookmarks=bookmarks,upvoted_ids=upvotes)


@app.route("/api/bookmarks/<int:material_id>", methods=["POST","DELETE"])
@student_required
def change_bookmark(material_id):
    conn=database.get_connection()
    if not conn.execute("SELECT 1 FROM materials WHERE id=? AND status='approved'",(material_id,)).fetchone(): conn.close(); return jsonify(error="Material not found."),404
    if request.method=="POST":
        try: conn.execute("INSERT INTO bookmarks(user_id,material_id) VALUES(?,?)",(current_user()["id"],material_id))
        except sqlite3.IntegrityError: pass
    else: conn.execute("DELETE FROM bookmarks WHERE user_id=? AND material_id=?",(current_user()["id"],material_id))
    conn.commit(); conn.close(); return jsonify(success=True,saved=request.method=="POST")


@app.route("/api/stats")
def get_platform_stats(): return jsonify(database.get_stats())
@app.route("/api/leaderboard")
def get_leaderboard_data(): return jsonify(database.get_leaderboard(limit=10))
@app.route("/api/filter-options")
def get_filters(): return jsonify(database.get_filter_options())


@app.route("/api/materials/<int:material_id>/file-debug")
@admin_required
def debug_material_file(material_id):
    file_data,stored_type=database.get_material_file_data(material_id)
    if not file_data: return jsonify(material_id=material_id,has_file=False),404
    return jsonify(material_id=material_id,has_file=True,file_type=stored_type,file_size_bytes=len(file_data),file_size_kb=round(len(file_data)/1024,2))


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith("/api/"):
        return jsonify(error="Not found."), 404
    return "Page not found.", 404


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith("/api/"):
        return jsonify(error="Internal server error."), 500
    return "Internal server error.", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"UniVault running locally at http://127.0.0.1:{port}")
    print("Cloudflare Tunnel is not started or stopped by UniVault. Run it separately only when you need public access.")
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
