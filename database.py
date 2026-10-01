"""Database layer supporting PostgreSQL (Supabase/production) and SQLite (local fallback) for UniVault."""
import logging
import os
import re
import sqlite3
from datetime import datetime

logger = logging.getLogger("univault.database")

try:
    import psycopg2
    from psycopg2 import IntegrityError as PGIntegrityError
except ImportError:
    psycopg2 = None
    PGIntegrityError = sqlite3.IntegrityError

# Unified IntegrityError catching both SQLite and PostgreSQL integrity violations
IntegrityError = (sqlite3.IntegrityError, PGIntegrityError)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "univault.db")


def get_database_url():
    """Retrieve database connection string from environment."""
    url = os.environ.get("DATABASE_URL", "").strip()
    return url if url else None


def is_postgres():
    """Check if the application is configured to use PostgreSQL."""
    return bool(get_database_url())


def get_db_path():
    """Return local SQLite database path."""
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATABASE_PATH


def adapt_sql(sql):
    """
    Adapt SQLite SQL syntax to PostgreSQL syntax:
    - Strips 'COLLATE NOCASE'
    - Replaces '?' placeholders with '%s' outside quotes
    - Replaces 'LIKE' with 'ILIKE' for case-insensitive search in PostgreSQL
    """
    # Remove COLLATE NOCASE
    sql = re.sub(r'\s+COLLATE\s+NOCASE\b', '', sql, flags=re.IGNORECASE)

    # Convert ? outside of single and double quotes to %s
    parts = []
    in_quote = False
    quote_char = ''
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        if not in_quote and (c == "'" or c == '"'):
            in_quote = True
            quote_char = c
            parts.append(c)
        elif in_quote and c == quote_char:
            if i + 1 < n and sql[i + 1] == quote_char:
                parts.append(c + quote_char)
                i += 1
            else:
                in_quote = False
                parts.append(c)
        elif not in_quote and c == '?':
            parts.append('%s')
        else:
            parts.append(c)
        i += 1
    adapted = ''.join(parts)

    # Use ILIKE in PostgreSQL for case-insensitive LIKE search
    adapted = re.sub(r'\bLIKE\b', 'ILIKE', adapted)
    return adapted


class PGRow(dict):
    """
    Row wrapper that matches sqlite3.Row functionality:
    - Key access: row['title']
    - Index access: row[0]
    - dict(row) converts directly to a standard Python dictionary
    - .get(), .pop(), .keys() work as expected
    """
    def __init__(self, desc, values):
        super().__init__()
        self._values = list(values)
        self._keys = [d[0] for d in desc]
        for k, v in zip(self._keys, self._values):
            self[k] = v

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        return super().__getitem__(item)

    def keys(self):
        return self._keys


class PGCursor:
    """Cursor wrapper that bridges psycopg2 to sqlite3-style interface."""
    def __init__(self, raw_cursor):
        self._cur = raw_cursor
        self.lastrowid = None
        self._inserted_row = None

    def execute(self, sql, params=None):
        adapted = adapt_sql(sql)
        is_insert = adapted.strip().upper().startswith("INSERT INTO")
        has_returning = " RETURNING " in adapted.upper()

        auto_returning = False
        if is_insert and not has_returning:
            adapted += " RETURNING id"
            auto_returning = True

        if params:
            self._cur.execute(adapted, params)
        else:
            self._cur.execute(adapted)

        if auto_returning:
            try:
                row = self._cur.fetchone()
                if row:
                    self.lastrowid = row[0]
                    self._inserted_row = row
            except Exception:
                pass

        return self

    def fetchone(self):
        if self._inserted_row is not None:
            row = self._inserted_row
            self._inserted_row = None
            if self._cur.description:
                return PGRow(self._cur.description, row)
            return row
        raw = self._cur.fetchone()
        if raw is None:
            return None
        return PGRow(self._cur.description, raw)

    def fetchall(self):
        raws = self._cur.fetchall()
        if not raws:
            return []
        desc = self._cur.description
        return [PGRow(desc, r) for r in raws]

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def close(self):
        self._cur.close()

    def __iter__(self):
        return iter(self.fetchall())


class PGConnection:
    """Connection wrapper for PostgreSQL conforming to sqlite3-style API."""
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PGCursor(self._conn.cursor())

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_connection():
    """
    Get a database connection.
    If DATABASE_URL is set, returns a PostgreSQL connection.
    Otherwise, returns an SQLite connection.
    """
    db_url = get_database_url()
    if db_url:
        if not psycopg2:
            raise RuntimeError("psycopg2-binary is required for PostgreSQL but is not installed.")
        # Handle postgres:// vs postgresql:// prefix (standard psycopg2 requirement)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        raw_conn = psycopg2.connect(db_url)
        return PGConnection(raw_conn)
    else:
        conn = sqlite3.connect(get_db_path(), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def init_db():
    """Initialize database tables, schema migrations, and default administrator."""
    if is_postgres():
        _init_postgres_db()
    else:
        _init_sqlite_db()


def _init_postgres_db():
    """PostgreSQL DDL initialization and schema migration."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      is_active INTEGER NOT NULL DEFAULT 1,
      must_change_password INTEGER NOT NULL DEFAULT 0,
      is_owner INTEGER NOT NULL DEFAULT 0,
      profile_photo TEXT DEFAULT ''
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS materials (
      id SERIAL PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT,
      subject_name TEXT NOT NULL,
      subject_code TEXT,
      branch TEXT NOT NULL,
      semester TEXT NOT NULL,
      university TEXT NOT NULL,
      material_type TEXT NOT NULL,
      academic_year TEXT DEFAULT '2024',
      file_url TEXT NOT NULL,
      file_type TEXT DEFAULT 'PDF',
      file_size_kb INTEGER DEFAULT 2048,
      page_count INTEGER DEFAULT 20,
      uploader_name TEXT NOT NULL,
      uploader_avatar TEXT,
      downloads_count INTEGER DEFAULT 0,
      views_count INTEGER DEFAULT 0,
      upvotes_count INTEGER DEFAULT 0,
      tags TEXT DEFAULT '',
      is_featured INTEGER DEFAULT 0,
      preview_content TEXT DEFAULT '',
      status TEXT DEFAULT 'approved',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      file_data BYTEA DEFAULT NULL,
      uploader_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
      id SERIAL PRIMARY KEY,
      material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
      author_name TEXT NOT NULL,
      rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
      comment TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS contributors (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      avatar TEXT,
      university TEXT,
      uploads_count INTEGER DEFAULT 0,
      upvotes_count INTEGER DEFAULT 0,
      badge TEXT DEFAULT 'Contributor',
      reputation INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS bookmarks (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, material_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS material_upvotes (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, material_id)
    )""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_upvotes_material ON material_upvotes(material_id)")

    # Idempotent column migrations for existing Postgres databases
    c.execute("ALTER TABLE materials ADD COLUMN IF NOT EXISTS file_data BYTEA DEFAULT NULL")
    c.execute("ALTER TABLE materials ADD COLUMN IF NOT EXISTS uploader_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
    c.execute("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_owner INTEGER NOT NULL DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo TEXT DEFAULT ''")

    # Set owner flag if seeded account exists and no owner is marked
    c.execute("""UPDATE users SET is_owner=1 WHERE id=(
        SELECT id FROM users WHERE LOWER(username)='sanjeet' ORDER BY id LIMIT 1
      ) AND NOT EXISTS (SELECT 1 FROM users WHERE is_owner=1)""")

    # Seed initial administrator if no administrator exists
    admin_row = c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone()
    if admin_row is None:
        c.execute("""INSERT INTO users(name,username,password_hash,role,must_change_password,is_owner)
                     VALUES(%s,%s,%s,'admin',1,1)""", (
            "Sanjeet", "Sanjeet",
            "scrypt:32768:8:1$xqcSj1Kd3xbReAfM$aa8334592483873c7ed195493e81b876138c465d005a5801ffee599d1a72e6735d9d243f77f75bd31f0a5d8eb4ea7784274d24932c76348ffe251e1889a4f16f"))

    conn.commit()
    conn.close()


def _init_sqlite_db():
    """SQLite DDL initialization and schema migration."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS materials (
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT,
      subject_name TEXT NOT NULL, subject_code TEXT, branch TEXT NOT NULL, semester TEXT NOT NULL,
      university TEXT NOT NULL, material_type TEXT NOT NULL, academic_year TEXT DEFAULT '2024',
      file_url TEXT NOT NULL, file_type TEXT DEFAULT 'PDF', file_size_kb INTEGER DEFAULT 2048,
      page_count INTEGER DEFAULT 20, uploader_name TEXT NOT NULL, uploader_avatar TEXT,
      downloads_count INTEGER DEFAULT 0, views_count INTEGER DEFAULT 0, upvotes_count INTEGER DEFAULT 0,
      tags TEXT DEFAULT '', is_featured INTEGER DEFAULT 0, preview_content TEXT DEFAULT '',
      status TEXT DEFAULT 'approved', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, file_data BLOB DEFAULT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
      id INTEGER PRIMARY KEY AUTOINCREMENT, material_id INTEGER NOT NULL, author_name TEXT NOT NULL,
      rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5), comment TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contributors (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, avatar TEXT, university TEXT,
      uploads_count INTEGER DEFAULT 0, upvotes_count INTEGER DEFAULT 0,
      badge TEXT DEFAULT 'Contributor', reputation INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
      username TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER NOT NULL DEFAULT 1,
      must_change_password INTEGER NOT NULL DEFAULT 0,
      is_owner INTEGER NOT NULL DEFAULT 0)""")

    def add_column(table, column, declaration):
        columns = {r["name"] for r in c.execute("PRAGMA table_info(" + table + ")")}
        if column not in columns:
            c.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + declaration)

    add_column("materials", "file_data", "BLOB DEFAULT NULL")
    add_column("materials", "uploader_user_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL")
    add_column("reviews", "user_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL")
    add_column("users", "is_owner", "INTEGER NOT NULL DEFAULT 0")
    add_column("users", "profile_photo", "TEXT DEFAULT ''")
    c.execute("""CREATE TABLE IF NOT EXISTS bookmarks (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, material_id INTEGER NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,material_id),
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE)""")
    c.execute("""CREATE TABLE IF NOT EXISTS material_upvotes (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, material_id INTEGER NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,material_id),
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_upvotes_material ON material_upvotes(material_id)")

    c.execute("""UPDATE users SET is_owner=1 WHERE id=(
        SELECT id FROM users WHERE LOWER(username)='sanjeet' ORDER BY id LIMIT 1
      ) AND NOT EXISTS (SELECT 1 FROM users WHERE is_owner=1)""")

    if c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone() is None:
        c.execute("""INSERT INTO users(name,username,password_hash,role,must_change_password,is_owner)
                     VALUES(?,?,?,'admin',1,1)""", (
            "Sanjeet", "Sanjeet",
            "scrypt:32768:8:1$xqcSj1Kd3xbReAfM$aa8334592483873c7ed195493e81b876138c465d005a5801ffee599d1a72e6735d9d243f77f75bd31f0a5d8eb4ea7784274d24932c76348ffe251e1889a4f16f"))
    conn.commit()
    conn.close()


def get_materials(
    search="",
    branch="all",
    semester="all",
    university="all",
    material_type="all",
    sort_by="popular",
    page=1,
    per_page=12
):
    conn = get_connection()

    query = """
        SELECT
            m.*,
            COALESCE(AVG(r.rating), 5.0) AS avg_rating,
            COUNT(r.id) AS review_count,
            u.profile_photo AS current_uploader_avatar
        FROM materials m
        LEFT JOIN reviews r
            ON m.id = r.material_id
        LEFT JOIN users u
            ON m.uploader_user_id = u.id
        WHERE m.status = 'approved'
    """

    params = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        query += """
            AND (
                m.title LIKE ?
                OR m.subject_name LIKE ?
                OR m.subject_code LIKE ?
                OR m.description LIKE ?
                OR m.university LIKE ?
                OR m.uploader_name LIKE ?
                OR m.tags LIKE ?
            )
        """
        params.extend([term] * 7)

    for val, col in (
        (branch, "branch"),
        (semester, "semester"),
        (university, "university"),
        (material_type, "material_type")
    ):
        if val and val.lower() != "all":
            query += " AND LOWER(m." + col + ") = LOWER(?)"
            params.append(val)

    # In PostgreSQL, all non-aggregated columns must appear in GROUP BY
    query += " GROUP BY m.id, u.profile_photo"

    query += {
        "downloads": " ORDER BY m.downloads_count DESC, m.id DESC",
        "rating": " ORDER BY avg_rating DESC, m.upvotes_count DESC",
        "newest": " ORDER BY m.id DESC",
    }.get(
        sort_by,
        " ORDER BY m.is_featured DESC, m.upvotes_count DESC, m.downloads_count DESC"
    )

    rows = conn.execute(query, params).fetchall()
    total = len(rows)
    results = []

    start = (page - 1) * per_page
    end = start + per_page

    for row in rows[start:end]:
        d = dict(row)
        d.pop("file_data", None)

        d["uploader_avatar"] = (
            d.get("current_uploader_avatar")
            or d.get("uploader_avatar")
            or ""
        )
        d.pop("current_uploader_avatar", None)
        d.pop("uploader_user_id", None)

        d["avg_rating"] = round(float(d["avg_rating"] or 5.0), 1)

        if (
            not d.get("file_url")
            or "mathiasbynens/small/master/pdf.pdf" in d.get("file_url", "")
        ):
            d["file_url"] = f"/api/materials/{d['id']}/file"

        results.append(d)

    conn.close()

    return {
        "materials": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ((total + per_page - 1) // per_page if total else 1),
    }


def get_material_by_id(material_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            m.*,
            COALESCE(AVG(r.rating), 5.0) AS avg_rating,
            COUNT(r.id) AS review_count,
            u.profile_photo AS current_uploader_avatar
        FROM materials m
        LEFT JOIN reviews r
            ON m.id = r.material_id
        LEFT JOIN users u
            ON m.uploader_user_id = u.id
        WHERE m.id = ?
          AND m.status = 'approved'
        GROUP BY m.id, u.profile_photo
        """,
        (material_id,)
    ).fetchone()

    if not row:
        conn.close()
        return None

    item = dict(row)
    item.pop("file_data", None)

    item["uploader_avatar"] = (
        item.get("current_uploader_avatar")
        or item.get("uploader_avatar")
        or ""
    )
    item.pop("current_uploader_avatar", None)
    item.pop("uploader_user_id", None)

    item["avg_rating"] = round(float(item["avg_rating"] or 5.0), 1)

    if (
        not item.get("file_url")
        or "mathiasbynens/small/master/pdf.pdf" in item.get("file_url", "")
    ):
        item["file_url"] = f"/api/materials/{item['id']}/file"

    item["reviews"] = [
        dict(r)
        for r in conn.execute(
            """
            SELECT id, author_name, rating, comment, created_at
            FROM reviews
            WHERE material_id = ?
            ORDER BY id DESC
            """,
            (material_id,)
        ).fetchall()
    ]

    conn.close()
    return item


def increment_views(material_id):
    conn = get_connection()
    conn.execute("UPDATE materials SET views_count = views_count + 1 WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


def increment_upvote(material_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO material_upvotes(user_id, material_id) VALUES(?, ?)", (user_id, material_id))
    except IntegrityError:
        row = c.execute("SELECT upvotes_count FROM materials WHERE id = ?", (material_id,)).fetchone()
        conn.close()
        return (row["upvotes_count"] if row else 0, True)

    c.execute("UPDATE materials SET upvotes_count = upvotes_count + 1 WHERE id = ?", (material_id,))
    row = c.execute("SELECT upvotes_count FROM materials WHERE id = ?", (material_id,)).fetchone()
    conn.commit()
    conn.close()
    return (row["upvotes_count"] if row else 0, False)


def increment_download(material_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE materials SET downloads_count = downloads_count + 1 WHERE id = ?", (material_id,))
    row = c.execute("SELECT downloads_count, file_url FROM materials WHERE id = ?", (material_id,)).fetchone()
    conn.commit()
    conn.close()
    return dict(row) if row else {"downloads_count": 0, "file_url": ""}


def create_material(data, file_data=None, uploader_user_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO materials(title,description,subject_name,subject_code,branch,semester,university,material_type,academic_year,file_url,file_type,file_size_kb,page_count,uploader_name,uploader_avatar,downloads_count,views_count,upvotes_count,tags,is_featured,preview_content,status,file_data,uploader_user_id)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,0,?,0,?,'approved',?,?)""", (
        data.get("title", "").strip(), data.get("description", "").strip(), data.get("subject_name", "").strip(), data.get("subject_code", "").strip().upper(),
        data.get("branch", "Computer Science & Engineering"), data.get("semester", "Semester 1"), data.get("university", "General University"),
        data.get("material_type", "Lecture Notes"), data.get("academic_year", str(datetime.now().year)), data.get("file_url", ""), data.get("file_type", "PDF"),
        data.get("file_size_kb", 2500), data.get("page_count", 20), data.get("uploader_name", "Student Contributor"), data.get("uploader_avatar", ""),
        data.get("tags", ""), data.get("preview_content", data.get("description", "")), file_data, uploader_user_id))
    mid = c.lastrowid
    if not data.get("file_url", "").strip():
        c.execute("UPDATE materials SET file_url = ? WHERE id = ?", (f"/api/materials/{mid}/file", mid))
    name = data.get("uploader_name", "Student Contributor").strip()
    contributor = c.execute("SELECT id FROM contributors WHERE name = ?", (name,)).fetchone()
    if contributor:
        c.execute("UPDATE contributors SET uploads_count = uploads_count + 1, reputation = reputation + 150 WHERE id = ?", (contributor["id"],))
    else:
        c.execute("INSERT INTO contributors(name,avatar,university,uploads_count,upvotes_count,badge,reputation) VALUES(?,?,?,1,0,'Rising Contributor',150)",
                  (name, data.get("uploader_avatar", ""), data.get("university", "General University")))
    conn.commit()
    conn.close()
    return mid


def get_material_file_data(material_id):
    conn = get_connection()
    row = conn.execute("SELECT file_data, file_type FROM materials WHERE id = ?", (material_id,)).fetchone()
    conn.close()
    if row and row["file_data"]:
        return (bytes(row["file_data"]), row["file_type"])
    return (None, None)


def create_review(material_id, author_name, rating, comment, user_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO reviews(material_id,author_name,rating,comment,user_id) VALUES(?,?,?,?,?)",
              (material_id, author_name.strip(), rating, comment.strip(), user_id))
    rid = c.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_stats():
    conn = get_connection()
    c = conn.cursor()
    stats = dict(c.execute("""SELECT COUNT(id) total_materials, COALESCE(SUM(downloads_count),0) total_downloads,
      COALESCE(SUM(views_count),0) total_views, COALESCE(SUM(upvotes_count),0) total_upvotes,
      COUNT(DISTINCT university) total_universities, COUNT(DISTINCT branch) total_branches FROM materials WHERE status='approved'""").fetchone())
    stats["total_reviews"] = c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    return stats


def get_leaderboard(limit=6):
    conn = get_connection()
    rows = conn.execute("SELECT name,avatar,university,uploads_count,upvotes_count,badge,reputation FROM contributors ORDER BY reputation DESC,upvotes_count DESC LIMIT ?",
                        (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_filter_options():
    conn = get_connection()
    out = {key: [r[0] for r in conn.execute("SELECT DISTINCT " + col + " FROM materials WHERE status='approved' ORDER BY " + col)]
           for key, col in (("universities", "university"), ("branches", "branch"), ("semesters", "semester"), ("material_types", "material_type"))}
    conn.close()
    return out
