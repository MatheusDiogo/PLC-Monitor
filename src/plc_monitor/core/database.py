import sqlite3
import threading
import time


class Database:
    def __init__(self):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._create_schema()

    def _create_schema(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript(
                """
                CREATE TABLE readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plc_id TEXT NOT NULL,
                    tag_label TEXT NOT NULL,
                    value TEXT NOT NULL,
                    student TEXT,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE status_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plc_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    student TEXT,
                    timestamp TEXT NOT NULL
                );
                CREATE INDEX idx_readings_plc ON readings(plc_id);
                CREATE INDEX idx_status_plc ON status_log(plc_id);
                """
            )
            self._conn.commit()

    def insert_reading(self, plc_id, tag_label, value, student=None):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                "INSERT INTO readings (plc_id, tag_label, value, student, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (plc_id, tag_label, str(value), student, ts),
            )
            self._conn.commit()

    def insert_status(self, plc_id, status, student=None):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                "INSERT INTO status_log (plc_id, status, student, timestamp) VALUES (?, ?, ?, ?)",
                (plc_id, status, student, ts),
            )
            self._conn.commit()

    def fetch_all_readings(self, plc_id=None):
        with self._lock:
            if plc_id:
                cur = self._conn.execute(
                    "SELECT plc_id, student, tag_label, value, timestamp FROM readings "
                    "WHERE plc_id = ? ORDER BY id ASC",
                    (plc_id,),
                )
            else:
                cur = self._conn.execute(
                    "SELECT plc_id, student, tag_label, value, timestamp FROM readings ORDER BY id ASC"
                )
            return cur.fetchall()

    def fetch_status_history(self, plc_id, limit=50):
        with self._lock:
            cur = self._conn.execute(
                "SELECT status, timestamp FROM status_log WHERE plc_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (plc_id, limit),
            )
            return cur.fetchall()

    def close(self):
        with self._lock:
            self._conn.close()
