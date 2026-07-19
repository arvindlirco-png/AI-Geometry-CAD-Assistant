from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import GeometryDocument


DB_PATH = Path(__file__).resolve().parents[2] / "cad_drawings.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS drawings (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, geometry TEXT NOT NULL, chat_history TEXT NOT NULL DEFAULT '[]', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )


def save_drawing(name: str, geometry: GeometryDocument, chat_history: list[dict[str, Any]]) -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT INTO drawings (name, geometry, chat_history) VALUES (?, ?, ?)", (name, geometry.model_dump_json(), json.dumps(chat_history)))
        return int(cur.lastrowid)


def list_drawings() -> list[dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id, name, updated_at FROM drawings ORDER BY updated_at DESC").fetchall()
    return [{"id": r[0], "name": r[1], "updated_at": r[2]} for r in rows]


def get_drawing(drawing_id: int) -> dict[str, Any] | None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT id, name, geometry, chat_history, updated_at FROM drawings WHERE id=?", (drawing_id,)).fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "geometry": json.loads(row[2]), "chat_history": json.loads(row[3]), "updated_at": row[4]}


def delete_drawing(drawing_id: int) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM drawings WHERE id=?", (drawing_id,))

