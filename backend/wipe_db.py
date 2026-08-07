import psycopg2
conn = psycopg2.connect("postgresql://datavision:datavision_dev@localhost:5433/datavision")
conn.autocommit = True
cur = conn.cursor()
print("Dropping public schema...")
cur.execute("DROP SCHEMA public CASCADE;")
print("Recreating public schema...")
cur.execute("CREATE SCHEMA public;")
print("Granting permissions...")
cur.execute("GRANT ALL ON SCHEMA public TO public;")
cur.close()
conn.close()
print("Done!")
