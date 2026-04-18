"""
SQLite user storage.

Schema
------
users
  user_id        INTEGER PK
  username       TEXT
  first_name     TEXT
  lang           TEXT    DEFAULT 'ru'
  threshold      TEXT    DEFAULT '1'
  first_seen_at  TEXT    (ISO-8601 UTC)
  subscribed_at  TEXT    (ISO-8601 UTC, NULL until confirmed)
  admin_notified INTEGER DEFAULT 0
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_FILE = Path("users.db")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


# ── Init ──────────────────────────────────────────────────────────────────────


def init() -> None:
    with _con() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id        INTEGER PRIMARY KEY,
                username       TEXT,
                first_name     TEXT,
                lang           TEXT    NOT NULL DEFAULT 'ru',
                threshold      TEXT    NOT NULL DEFAULT '1000',
                first_seen_at  TEXT    NOT NULL,
                subscribed_at  TEXT,
                admin_notified INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.commit()


# ── Write ─────────────────────────────────────────────────────────────────────


def upsert(user_id: int, username: str | None, first_name: str | None) -> bool:
    """Insert or update user. Returns True if brand-new."""
    with _con() as con:
        row = con.execute(
            "SELECT user_id FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
        if row is None:
            con.execute(
                "INSERT INTO users (user_id, username, first_name, first_seen_at)"
                " VALUES (?,?,?,?)",
                (user_id, username, first_name, _now()),
            )
            con.commit()
            return True
        con.execute(
            "UPDATE users SET username=?, first_name=? WHERE user_id=?",
            (username, first_name, user_id),
        )
        con.commit()
        return False


def set_subscribed(user_id: int) -> None:
    """Record subscription timestamp (only on first confirmation)."""
    with _con() as con:
        con.execute(
            "UPDATE users SET subscribed_at=? WHERE user_id=? AND subscribed_at IS NULL",
            (_now(), user_id),
        )
        con.commit()


def mark_notified(user_id: int) -> None:
    with _con() as con:
        con.execute(
            "UPDATE users SET admin_notified=1 WHERE user_id=?", (user_id,)
        )
        con.commit()


def set_lang(user_id: int, lang: str) -> None:
    with _con() as con:
        con.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
        con.commit()


def set_threshold(user_id: int, threshold: str) -> None:
    with _con() as con:
        con.execute(
            "UPDATE users SET threshold=? WHERE user_id=?", (threshold, user_id)
        )
        con.commit()


# ── Read ──────────────────────────────────────────────────────────────────────


def get(user_id: int) -> dict | None:
    with _con() as con:
        row = con.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def active_users() -> list[dict]:
    """All users who have confirmed channel subscription."""
    with _con() as con:
        rows = con.execute(
            "SELECT * FROM users WHERE subscribed_at IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]
