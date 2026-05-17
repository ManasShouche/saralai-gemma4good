"""Fix national schemes with empty state string -> NULL."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "schemes.db")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("UPDATE schemes SET state = NULL WHERE scope = 'national' AND state = ''")
print(f"Updated {c.rowcount} rows: national schemes with empty state -> NULL")
conn.commit()
conn.close()
