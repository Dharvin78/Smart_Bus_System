import sqlite3
import os
DB='db.sqlite3'
if not os.path.exists(DB):
    print('db not found')
    raise SystemExit
con=sqlite3.connect(DB)
cur=con.cursor()
try:
    cur.execute('SELECT id, full_name, photo FROM apps_drivers_driver')
    rows=cur.fetchall()
    if not rows:
        print('no drivers')
    else:
        for r in rows:
            print(r)
finally:
    con.close()
