import os
import sqlite3
import sys
import types
from datetime import datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    monkeypatch.syspath_prepend(project_root)

    if "astrbot.api" not in sys.modules:
        dummy_astrbot = types.ModuleType("astrbot")
        dummy_api = types.ModuleType("astrbot.api")

        class DummyLogger:
            def debug(self, *args, **kwargs):
                pass

            def info(self, *args, **kwargs):
                pass

            def error(self, *args, **kwargs):
                pass

            def warning(self, *args, **kwargs):
                pass

        dummy_api.logger = DummyLogger()

        monkeypatch.setitem(sys.modules, "astrbot", dummy_astrbot)
        monkeypatch.setitem(sys.modules, "astrbot.api", dummy_api)


def _init_red_packet_schema(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE red_packets (
                packet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                packet_type TEXT NOT NULL,
                total_amount INTEGER NOT NULL,
                total_count INTEGER NOT NULL,
                remaining_amount INTEGER NOT NULL,
                remaining_count INTEGER NOT NULL,
                password TEXT,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_expired INTEGER DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE red_packet_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                packet_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                claimed_at TIMESTAMP NOT NULL,
                FOREIGN KEY (packet_id) REFERENCES red_packets(packet_id)
            )
            """
        )
        conn.commit()


def test_cleanup_expired_red_packets_uses_current_schema(tmp_path):
    from core.repositories.sqlite_red_packet_repo import SqliteRedPacketRepository

    db_path = tmp_path / "red_packet.db"
    _init_red_packet_schema(str(db_path))

    expired_at = datetime.now() - timedelta(days=2)
    active_expires_at = datetime.now() + timedelta(hours=1)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO red_packets (
                sender_id, group_id, packet_type, total_amount, total_count,
                remaining_amount, remaining_count, password, created_at, expires_at, is_expired
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("sender-expired", "group-1", "normal", 100, 1, 100, 1, None, datetime.now(), expired_at, 1),
        )
        expired_packet_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO red_packet_records (packet_id, user_id, amount, claimed_at)
            VALUES (?, ?, ?, ?)
            """,
            (expired_packet_id, "claimer-expired", 100, datetime.now()),
        )

        cursor.execute(
            """
            INSERT INTO red_packets (
                sender_id, group_id, packet_type, total_amount, total_count,
                remaining_amount, remaining_count, password, created_at, expires_at, is_expired
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("sender-active", "group-1", "normal", 200, 2, 200, 2, None, datetime.now(), active_expires_at, 0),
        )
        active_packet_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO red_packet_records (packet_id, user_id, amount, claimed_at)
            VALUES (?, ?, ?, ?)
            """,
            (active_packet_id, "claimer-active", 50, datetime.now()),
        )
        conn.commit()

    repo = SqliteRedPacketRepository(str(db_path))

    cleaned_count = repo.cleanup_expired_red_packets()

    assert cleaned_count == 1

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM red_packets WHERE packet_id = ?", (expired_packet_id,))
        assert cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM red_packet_records WHERE packet_id = ?", (expired_packet_id,))
        assert cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM red_packets WHERE packet_id = ?", (active_packet_id,))
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM red_packet_records WHERE packet_id = ?", (active_packet_id,))
        assert cursor.fetchone()[0] == 1
