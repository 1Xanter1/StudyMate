from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: str
    priority: str
    deadline: Optional[str]
    completed: int
    created_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class StudySession:
    id: int
    duration_seconds: int
    session_type: str
    started_at: str
    completed_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Flashcard:
    id: int
    front: str
    back: str
    box: int
    next_review: Optional[str]
    last_reviewed: Optional[str]
    correct_count: int
    wrong_count: int
    created_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ProgressStats:
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    total_sessions: int
    total_focus_minutes: float
    total_flashcards: int
    flashcards_due: int
    total_reviews: int

    def to_dict(self):
        return asdict(self)
