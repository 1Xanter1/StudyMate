from datetime import datetime, timedelta
from typing import List, Optional
import json

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

class FocusSession:
    def __init__(self, duration_minutes: int = 25):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration = timedelta(minutes=duration_minutes)
        self.completed = False

    def start(self):
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()
        self.completed = True

    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class FocusTimer:
    def __init__(self):
        self.current_session: Optional[FocusSession] = None
        self.history: List[FocusSession] = []

    def start_session(self, duration=25):
        self.current_session = FocusSession(duration)
        self.current_session.start()

    def end_session(self):
        if self.current_session:
            self.current_session.end()
            self.history.append(self.current_session)
            self.current_session = None

    def get_history(self):
        return self.history

class Flashcard:
    def __init__(self, question: str, answer: str):
        self.id = id(self)
        self.question = question
        self.answer = answer
        self.interval = 1
        self.next_review = datetime.now()
        self.last_reviewed: Optional[datetime] = None

    def review(self, success: bool):
        self.last_reviewed = datetime.now()
        if success:
            self.interval *= 2
        else:
            self.interval = 1
        self.next_review = datetime.now() + timedelta(days=self.interval)

class FlashcardDeck:
    def __init__(self):
        self.cards: List[Flashcard] = []

    def add_card(self, card: Flashcard):
        self.cards.append(card)

    def delete_card(self, card_id: int):
        self.cards = [c for c in self.cards if c.id != card_id]

    def get_due_cards(self):
        now = datetime.now()
        return [c for c in self.cards if c.next_review <= now]

class ProgressTracker:
    def __init__(self, task_manager: TaskManager, timer: FocusTimer, deck: FlashcardDeck):
        self.task_manager = task_manager
        self.timer = timer
        self.deck = deck

    def get_task_stats(self):
        total = len(self.task_manager.tasks)
        completed = len(self.task_manager.get_completed_tasks())
        return {"total_tasks": total, "completed_tasks": completed}

    def get_focus_stats(self):
        sessions = self.timer.get_history()
        total_time = sum((s.get_duration() for s in sessions if s.get_duration()), timedelta())

        return {
            "total_sessions": len(sessions),
            "total_time": total_time
        }

    def get_flashcard_stats(self):
        return {
            "total_cards": len(self.deck.cards),
            "due_cards": len(self.deck.get_due_cards())
        }

class DataManager:
    def save_tasks(self, tasks: List[Task], filename="tasks.json"):
        data = [vars(t) for t in tasks]
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_tasks(self, filename="tasks.json") -> List[Task]:
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                return [Task.from_dict(d) for d in data]
        except FileNotFoundError:
            return []

class TaskManager:
    def __init__(self):
        self.tasks: List[Task] = []
        self.data_manager = DataManager()

    def add_task(self, task: Task):
        self.tasks.append(task)

    def delete_task(self, task_id: int):
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_all_tasks(self):
        return self.tasks

    def get_completed_tasks(self):
        return [t for t in self.tasks if t.completed]

    def sort_by_priority(self):
        return sorted(self.tasks, key=lambda t: t.priority)

    def sort_by_deadline(self):
        return sorted(self.tasks, key=lambda t: t.deadline or datetime.max)

    def load(self):
        self.tasks = self.data_manager.load_tasks()

    def save(self):
        self.data_manager.save_tasks(self.tasks)
