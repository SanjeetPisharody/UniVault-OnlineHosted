"""
UniVault PDF Document Generator
Generates valid, professionally formatted PDF files from academic material
content using pure Python standard library — no external C dependencies.
"""


def wrap_text(text, max_chars=80):
    """Wrap long lines of text into readable paragraph lines."""
    wrapped = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            wrapped.append("")
            continue
        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)
            if split_at == -1:
                split_at = max_chars
            wrapped.append(line[:split_at])
            line = line[split_at:].lstrip()
        wrapped.append(line)
    return wrapped


def escape_pdf(s):
    """Escape special PDF string characters."""
    return str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("\r", "").replace("\n", " ")


SECTION_PREFIXES = (
    "UNIT ", "[QUESTION", "TOPIC ", "QUICK ", "PROBLEM ", "NUMERICAL ",
    "KEY EQUATIONS", "CORE EQUATIONS", "LAPLACE", "FOURIER", "TRANSACTION",
    "TOPIC 1", "TOPIC 2", "TOPIC 3"
)


def generate_notes_pdf(material):
    """
    Generates a real, multi-page, professionally typeset study-guide PDF
    from the material's content. Returns raw bytes.
    """
    title       = str(material.get("title", "Study Material"))
    subject     = str(material.get("subject_name", "Academic Subject"))
    code        = str(material.get("subject_code", "GEN-101"))
    university  = str(material.get("university", "UniVault University"))
    branch      = str(material.get("branch", "General Engineering"))
    semester    = str(material.get("semester", "Semester 1"))
    mat_type    = str(material.get("material_type", "Lecture Notes"))
    year        = str(material.get("academic_year", "2026"))
    author      = str(material.get("uploader_name", "Student Scholar"))
    content_raw = str(material.get("preview_content") or material.get("description") or
                      "Comprehensive lecture notes and study guide for exam preparation.")

    # Build wrapped lines
    raw_lines = wrap_text(content_raw, max_chars=78)

    # Paginate
    FIRST_PAGE_LINES = 25
    NEXT_PAGE_LINES  = 40

    pages_lines = []
    pages_lines.append(raw_lines[:FIRST_PAGE_LINES])
    remaining = raw_lines[FIRST_PAGE_LINES:]
    while remaining:
        pages_lines.append(remaining[:NEXT_PAGE_LINES])
        remaining = remaining[NEXT_PAGE_LINES:]

    total_pages = len(pages_lines)

    # ---------- build page streams ----------
    page_stream_bytes = []

    for page_idx, lines in enumerate(pages_lines, 1):
        ops = []

        if page_idx == 1:
            # ── Header box
            ops += [
                "0.95 0.96 1.0 rg",
                "50 710 495 90 re f",
                "0.31 0.27 0.90 RG",
                "1.2 w",
                "50 710 495 90 re S",
            ]
            # ── Branding line
            ops += [
                "BT", "/F1 9 Tf", "0.45 0.45 0.55 rg",
                f"65 782 Td",
                "(UNIVAULT ACADEMIC PORTAL   -   VERIFIED STUDENT NOTES) Tj",
                "ET",
            ]
            # ── Title
            title_50 = escape_pdf(title[:54])
            ops += [
                "BT", "/F1 14 Tf", "0.08 0.08 0.20 rg",
                "65 760 Td",
                f"({title_50}) Tj",
                "ET",
            ]
            # ── Metadata line 1
            meta1 = f"Course: {code}  |  {subject}  |  {semester} ({year})"
            ops += [
                "BT", "/F2 9 Tf", "0.30 0.30 0.42 rg",
                "65 740 Td",
                f"({escape_pdf(meta1[:78])}) Tj",
                "ET",
            ]
            # ── Metadata line 2
            meta2 = f"{university}  |  {branch}  |  {mat_type}"
            ops += [
                "BT", "/F2 9 Tf", "0.30 0.30 0.42 rg",
                "65 726 Td",
                f"({escape_pdf(meta2[:78])}) Tj",
                "ET",
            ]
            # ── Divider
            ops += ["0.75 0.75 0.82 RG", "0.6 w", "50 700 m 545 700 l S"]

            # ── Content block starting at y=678
            curr_y = 678
            ops += [
                "BT", "/F2 10 Tf", "0.12 0.12 0.20 rg",
                f"50 {curr_y} Td", "14 TL",
            ]
            for line in lines:
                if any(line.startswith(p) for p in SECTION_PREFIXES):
                    ops += [
                        "ET",
                        "BT", "/F1 10.5 Tf", "0.20 0.20 0.75 rg",
                        f"({escape_pdf(line)}) '",
                        "ET",
                        "BT", "/F2 10 Tf", "0.12 0.12 0.20 rg",
                    ]
                elif line.startswith("- ") or line.startswith("• "):
                    ops.append(f"({escape_pdf(line)}) '")
                else:
                    ops.append(f"({escape_pdf(line)}) '")
            ops.append("ET")

        else:
            # ── Running header
            header_txt = escape_pdf(f"{title[:50]}  |  {code}")
            ops += [
                "BT", "/F1 8 Tf", "0.50 0.50 0.60 rg",
                f"50 808 Td",
                f"({header_txt}) Tj",
                "ET",
                "0.80 0.80 0.88 RG", "0.5 w", "50 798 m 545 798 l S",
            ]

            ops += [
                "BT", "/F2 10 Tf", "0.12 0.12 0.20 rg",
                "50 778 Td", "14 TL",
            ]
            for line in lines:
                if any(line.startswith(p) for p in SECTION_PREFIXES):
                    ops += [
                        "ET",
                        "BT", "/F1 10.5 Tf", "0.20 0.20 0.75 rg",
                        f"({escape_pdf(line)}) '",
                        "ET",
                        "BT", "/F2 10 Tf", "0.12 0.12 0.20 rg",
                    ]
                else:
                    ops.append(f"({escape_pdf(line)}) '")
            ops.append("ET")

        # ── Footer on every page
        ops += [
            "0.80 0.80 0.88 RG", "0.5 w", "50 52 m 545 52 l S",
            "BT", "/F2 8 Tf", "0.50 0.50 0.60 rg",
            "50 38 Td",
            "(UniVault Academic Sharing Portal  -  Free, Peer-Reviewed Educational Resource) Tj",
            "ET",
            "BT", "/F1 8 Tf", "0.50 0.50 0.60 rg",
            f"490 38 Td",
            f"(Page {page_idx} / {total_pages}) Tj",
            "ET",
        ]

        stream_body = "\n".join(ops).encode("latin-1", "replace")
        page_stream_bytes.append(stream_body)

    # ---------- assemble PDF object tree ----------
    objects = []                 # list of raw bytes for each object body
    # We'll track the object number assignment:
    # 1: Catalog
    # 2: Pages
    # 3 .. 2+total_pages: Page dicts
    # 3+total_pages .. 3+2*total_pages-1: Page streams
    # 3+2*total_pages: Font F1 (Helvetica-Bold)
    # 3+2*total_pages+1: Font F2 (Helvetica)

    n_pages = total_pages
    page_obj_ids    = list(range(3, 3 + n_pages))
    stream_obj_ids  = list(range(3 + n_pages, 3 + 2 * n_pages))
    font_f1_id      = 3 + 2 * n_pages
    font_f2_id      = font_f1_id + 1

    # Obj 1 – Catalog
    objects.append(b"<</Type/Catalog/Pages 2 0 R>>")

    # Obj 2 – Pages
    kids = " ".join(f"{oid} 0 R" for oid in page_obj_ids)
    objects.append(f"<</Type/Pages/Kids[{kids}]/Count {n_pages}>>".encode())

    # Page dicts (objs 3..2+n_pages)
    for i, stream_oid in enumerate(stream_obj_ids):
        objects.append(
            f"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]"
            f"/Contents {stream_oid} 0 R"
            f"/Resources<</Font<</F1 {font_f1_id} 0 R/F2 {font_f2_id} 0 R>>>>>>"
            .encode()
        )

    # Stream objects
    for sb in page_stream_bytes:
        header = f"<</Length {len(sb)}>>\nstream\n".encode()
        objects.append(header + sb + b"\nendstream")

    # Fonts
    objects.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold>>")
    objects.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")

    # ---------- serialize ----------
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for idx, obj_body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode())
        pdf.extend(obj_body)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    n_objs = len(objects)
    pdf.extend(f"xref\n0 {n_objs + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode())

    pdf.extend(
        f"trailer\n<</Size {n_objs + 1}/Root 1 0 R>>\n"
        f"startxref\n{xref_pos}\n%%EOF".encode()
    )
    return bytes(pdf)
