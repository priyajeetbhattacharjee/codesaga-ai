import sqlite3

from werkzeug.security import generate_password_hash


connection = sqlite3.connect("codesaga.db")

connection.execute("PRAGMA foreign_keys = ON")

cursor = connection.cursor()


# Student accounts
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """
)


# Every submitted quiz answer
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        chapter_number INTEGER NOT NULL,
        checkpoint_number INTEGER NOT NULL,
        question_type TEXT NOT NULL,
        submitted_answer TEXT,
        is_correct INTEGER NOT NULL,
        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (student_id)
            REFERENCES students (id)
    )
    """
)


# Final chapter scores
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS chapter_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        chapter_number INTEGER NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        total_questions INTEGER NOT NULL DEFAULT 3,
        completed INTEGER NOT NULL DEFAULT 0,
        completed_at TIMESTAMP,

        FOREIGN KEY (student_id)
            REFERENCES students (id),

        UNIQUE (student_id, chapter_number)
    )
    """
)


# Demo student
demo_password = generate_password_hash("demo123")


cursor.execute(
    """
    INSERT OR IGNORE INTO students (
        name,
        email,
        password_hash
    )
    VALUES (?, ?, ?)
    """,
    (
        "Demo Student",
        "student@example.com",
        demo_password
    )
)


connection.commit()
connection.close()


print("CodeSaga database tables created successfully.")