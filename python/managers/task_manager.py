from datetime import datetime
from python.managers.data_manager import DataManager
from typing import List
from python.models.task import Task

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
