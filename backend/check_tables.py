import sqlite3
conn = sqlite3.connect('datavision.db')
tables = [r[0] for r in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print("TABLES:", tables)
