
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from config import DATABASE_PATH
from app.models import Task


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                status      TEXT    NOT NULL DEFAULT 'pending',
                priority    TEXT    NOT NULL DEFAULT 'medium',
                due_date    TEXT,
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
        """)
        conn.commit()


def create_task(
    title: str,
    description: str = "",
    status: str = "pending",
    priority: str = "medium",
    due_date: Optional[str] = None,
) -> Task:
    now = datetime.now(timezone.utc).isoformat()
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, due_date,
                               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title.strip(), description.strip(), status, priority, due_date, now, now),
        )
        conn.commit()
        return get_task_by_id(cursor.lastrowid)


def get_task_by_id(task_id: int) -> Optional[Task]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return Task.from_row(tuple(row)) if row else None


def get_all_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> list:
    query  = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY created_at DESC"

    with _get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Task.from_row(tuple(r)) for r in rows]


def update_task(task_id: int, fields: dict) -> Optional[Task]:
    allowed = {"title", "description", "status", "priority", "due_date"}
    updates = {k: v for k, v in fields.items() if k in allowed}

    if not updates:
        return get_task_by_id(task_id)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values     = list(updates.values()) + [task_id]

    with _get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()

    return get_task_by_id(task_id)


def delete_task(task_id: int) -> bool:
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return cursor.rowcount > 0
