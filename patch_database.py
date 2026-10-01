from pathlib import Path

p = Path("database.py")
s = p.read_text(encoding="utf-8")

old1 = '''        d = dict(row)
        d["avg_rating"] = round(d["avg_rating"], 1) if d["avg_rating"] is not None else 5.0
        results.append(d)'''

new1 = '''        d = dict(row)
        d["avg_rating"] = round(d["avg_rating"], 1) if d["avg_rating"] is not None else 5.0

        if (
            not d.get("file_url")
            or "mathiasbynens/small/master/pdf.pdf" in d.get("file_url", "")
        ):
            d["file_url"] = f"/api/materials/{d['id']}/file"

        results.append(d)'''

old2 = '''    item = dict(row)
    item["avg_rating"] = round(item["avg_rating"], 1) if item["avg_rating"] is not None else 5.0'''

new2 = '''    item = dict(row)
    item["avg_rating"] = round(item["avg_rating"], 1) if item["avg_rating"] is not None else 5.0

    if (
        not item.get("file_url")
        or "mathiasbynens/small/master/pdf.pdf" in item.get("file_url", "")
    ):
        item["file_url"] = f"/api/materials/{item['id']}/file"'''

if old1 not in s:
    raise SystemExit("ERROR: get_materials section not found")

if old2 not in s:
    raise SystemExit("ERROR: get_material_by_id section not found")

s = s.replace(old1, new1, 1)
s = s.replace(old2, new2, 1)

p.write_text(s, encoding="utf-8")
print("database.py patched successfully")