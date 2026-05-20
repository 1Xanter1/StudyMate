from datetime import datetime
from typing import Optional

class Task:
    def __init__(self, title: str, description: str = "", deadline: Optional[datetime] = None, priority: int = 1):
        self.id = id(self)
        self.title = title
        self.description = description
        self.deadline = deadline
        self.priority = priority
        self.completed = False
        self.created_at = datetime.now()

    def mark_completed(self):
        self.completed = True

    def update(self, title=None, description=None, deadline=None, priority=None):
        if title:
            self.title = title
        if description:
            self.description = description
        if deadline:
            self.deadline = deadline
        if priority:
            self.priority = priority
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }
    @staticmethod
    def from_dict(data):
        task = Task(
            title = data["title"],
            description= data["description"],
            deadline = datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
            priority = data["priority"]
        )
        task.id = int(data["id"])
        task.completed = data["completed"]
        task.correct_deadline = datetime.fromisoformat(data["created_at"])
        return task
