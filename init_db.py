import sqlite3

from werkzeug.security import generate_password_hash


connection = sqlite3.connect("codesaga.db")

cursor = connection.cursor()


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


print("CodeSaga database created successfully.")