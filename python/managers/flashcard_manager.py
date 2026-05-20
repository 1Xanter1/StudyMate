from sql.database import get_connection
from python.models.flashcard import Flashcard
from datetime import datetime

class FlashcardManager:
    def add_flashcard(self, card: Flashcard):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute('''INSERT INTO flashcards(question, answer, interval_days, next_review, last_reviewed)
        VALUES (?, ?, ?, ?, ?)''', (
            card.question,
            card.answer,
            card.interval,
            card.next_review.isoformat(),
            card.last_reviewed.isoformat() if card.last_reviewed else None,
        ))

        connection.commit()
        connection.close()

    def load_cards(self):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM flashcards")

        rows = cursor.fetchall()

        cards = []
        for row in rows:
            card = Flashcard(row[1],row[2])
            card.id = row[0]
            card.interval = row[3]
            card.next_review = datetime.fromisoformat(row[4])
            if row[5]:
                card.last_reviewed = datetime.fromisoformat(row[5])
            cards.append(card)
        connection.close()
        return cards
