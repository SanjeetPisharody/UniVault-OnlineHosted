import database

database.init_db()

conn = database.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT id, title, file_url FROM materials ORDER BY id')
rows = cursor.fetchall()
print(f'Total materials in DB: {len(rows)}')
print()
for row in rows:
    title_short = row["title"][:40]
    furl = row["file_url"]
    mid = row["id"]
    print(f'ID {mid}: {title_short!r}')
    print(f'       file_url: {furl}')

cursor.execute('SELECT count(*) as c FROM contributors')
print('Total contributors:', cursor.fetchone()['c'])
cursor.execute('SELECT count(*) as c FROM reviews')
print('Total reviews:', cursor.fetchone()['c'])
conn.close()
