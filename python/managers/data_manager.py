import json
from ast import List
from python.models.task import Task

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