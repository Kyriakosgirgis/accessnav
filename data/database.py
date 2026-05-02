import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "accessnav.db")


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self.create_tables()
        return self._conn

    def create_tables(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password    TEXT    NOT NULL,
                created_at  TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS spots (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lat         REAL    NOT NULL,
                lon         REAL    NOT NULL,
                spot_type   TEXT    NOT NULL CHECK(spot_type IN ('ramp','elevator','barrier')),
                description TEXT    DEFAULT '',
                verified    INTEGER DEFAULT 0,
                created_at  TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                lat          REAL    NOT NULL,
                lon          REAL    NOT NULL,
                barrier_type TEXT    NOT NULL,
                description  TEXT    DEFAULT '',
                created_at   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS saved_routes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                origin_lat  REAL    NOT NULL,
                origin_lon  REAL    NOT NULL,
                dest_lat    REAL    NOT NULL,
                dest_lon    REAL    NOT NULL,
                created_at  TEXT    DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

    def execute(self, sql, params=()):
        conn = self.connect()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def fetchone(self, sql, params=()):
        conn = self.connect()
        cursor = conn.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql, params=()):
        conn = self.connect()
        cursor = conn.execute(sql, params)
        return cursor.fetchall()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
            Database._instance = None