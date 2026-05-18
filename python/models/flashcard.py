from datetime import datetime, timedelta
from typing import List, Optional
from sql.database import get_connection

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
