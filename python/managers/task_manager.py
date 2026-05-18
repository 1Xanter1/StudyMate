from datetime import datetime
from python.managers.data_manager import DataManager
from typing import List
from python.models.task import Task
from sql.database import get_connection

class TaskManager:
    def __init__(self):
        self.tasks: List[Task] = []
        self.data_manager = DataManager()

    def add_task(self, task: Task):
        self.tasks.append(task)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('''INSERT INTO tasks(title, description, deadline, priority, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            task.title,
            task.description,
            task.deadline.isoformat() if task.deadline else None,
            task.priority,
            task.completed,
            task.created_at.isoformat(),
            task.created_at.isoformat()
        ))
        connection.commit()
        connection.close()

    def delete_task(self, task_id: int):
        self.tasks = [t for t in self.tasks if t.id != task_id]

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM tasks WHERE id = ?''', (task_id,))

        connection.commit()
        connection.close()

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

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('''SELECT * from tasks''')

        rows = cursor.fetchall()
        self.tasks =[]

        for row in rows:
            task = Task(
                title = row[1],
                description = row[2],
                deadline = datetime.fromisoformat(row[3]) if row[3] else None,
                priority = row[4]
            )
            task.id = int(row[0])
            task.completed = bool(row[5])
            task.created_at = datetime.fromisoformat(row[6])

            self.tasks.append(task)

        connection.close()


    def save(self):
        self.data_manager.save_tasks(self.tasks)
