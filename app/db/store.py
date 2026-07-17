import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "agent.db")
SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with open(SCHEMA) as f:
        sql = f.read()
    conn = connect()
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print(f"Initialized {DB_PATH}")


if __name__ == "__main__":
    init()
