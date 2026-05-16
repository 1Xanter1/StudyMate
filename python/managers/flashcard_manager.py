from python.managers.task_manager import TaskManager
from python.models.flashcard import FlashcardDeck
from python.models.focus_timer import FocusTimer


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