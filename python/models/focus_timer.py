from datetime import datetime, timedelta
from typing import Optional, List

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