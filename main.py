import sqlite3

conn = sqlite3.connect('WorldHeritageSites.db')

cur = conn.cursor()
cur.row_factory = sqlite3.Row

res = cur.execute('SELECT * FROM WorldHeritageSites')

res = cur.execute(
    select id_no,name_en
    from WorldHeritageSite
    where name_en like '%Ancient City%'
    order by id_no)

data = res.fetchall()
for row in data:
    print('ID Number:', row['id_no'], 'Name:', row['name_en'])

print("ola")
