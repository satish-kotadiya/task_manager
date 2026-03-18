
from datetime import datetime, timezone

VALID_STATUSES   = ("pending", "in_progress", "completed")
VALID_PRIORITIES = ("low", "medium", "high")


class Task:


    def __init__(
        self,
        title: str,
        description: str = "",
        status: str = "pending",
        priority: str = "medium",
        due_date: str = None,
        task_id: int = None,
        created_at: str = None,
        updated_at: str = None,
    ):
        self.id          = task_id
        self.title       = title.strip()
        self.description = (description or "").strip()
        self.status      = status
        self.priority    = priority
        self.due_date    = due_date
        self.created_at  = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at  = updated_at or self.created_at

    def to_dict(self) -> dict:

        return {
            "id":          self.id,
            "title":       self.title,
            "description": self.description,
            "status":      self.status,
            "priority":    self.priority,
            "due_date":    self.due_date,
            "created_at":  self.created_at,
            "updated_at":  self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Task":

        return cls(
            task_id     = row[0],
            title       = row[1],
            description = row[2] or "",
            status      = row[3],
            priority    = row[4],
            due_date    = row[5],
            created_at  = row[6],
            updated_at  = row[7],
        )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title='{self.title}' status='{self.status}'>"
