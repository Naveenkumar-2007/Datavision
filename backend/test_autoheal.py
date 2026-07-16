import asyncio
import os
import sys

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import verify_tables
import sqlite3

async def test():
    await verify_tables()
    conn = sqlite3.connect('datavision.db')
    tables = [r[0] for r in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print('api_call_logs in tables:', 'api_call_logs' in tables)

asyncio.run(test())
