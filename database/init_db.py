import sqlite3
import os

DB_PATH = os.environ.get(
    'DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'warehouse.db'),
)
SCHEMA = os.path.join(os.path.dirname(__file__), 'schema.sql')
SEED = os.path.join(os.path.dirname(__file__), 'seed.sql')


def init():
    if os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA, encoding='utf-8') as f:
        conn.executescript(f.read())

    with open(SEED, encoding='utf-8') as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init()
