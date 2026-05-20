import sqlite3
db_name = 'study_mate.db'
connection = sqlite3.connect(db_name)
cursor = connection.cursor()

def get_connection():
    return sqlite3.connect(db_name)

cursor.execute('''CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    deadline TEXT,
    priority INTEGER NOT NULL,
    completed BOOLEAN NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS focus_sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    duration INTEGER NOT NULL,
    completed BOOLEAN NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS flashcards(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT,
    interval_days INTEGER NOT NULL,
    next_review TEXT NOT NULL,
    last_reviewed TEXT NOT NULL
    )''')

connection.commit()
connection.close()
