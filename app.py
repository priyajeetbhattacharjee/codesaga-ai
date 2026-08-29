import os
import sqlite3

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from google import genai
from werkzeug.security import check_password_hash


# Load values from the .env file.
load_dotenv()


# Create the Flask application.
app = Flask(__name__)


# Flask uses this key to protect login sessions.
app.secret_key = os.getenv(
    "SECRET_KEY",
    "temporary-development-key"
)


# Create the Gemini client.
gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    gemini_client = genai.Client(
        api_key=gemini_api_key
    )
else:
    gemini_client = None


def generate_gemini_hint(
    theme_name,
    question,
    student_answer,
    correct_concept,
    fallback_hint
):
    """
    Generate a short story-based hint without revealing
    the correct answer.
    """

    if gemini_client is None:
        return fallback_hint

    prompt = f"""
You are Cipher, a mentor inside an educational
interactive manga for beginner BCA students.

Narrative theme:
{theme_name}

Quiz question:
{question}

Student's incorrect answer:
{student_answer}

Correct concept for your private reference:
{correct_concept}

Give one short Socratic hint in Cipher's character voice.

Rules:
- Do not reveal the correct answer.
- Do not directly state the correct option.
- Connect the hint to the selected story theme.
- Be encouraging.
- Use simple language.
- Keep the hint below 60 words.
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        if response.text:
            return response.text.strip()

        return fallback_hint

    except Exception as error:
        print(f"Gemini hint error: {error}")

        return fallback_hint


def get_database_connection():
    """
    Open the SQLite database and allow columns
    to be accessed by name.
    """

    connection = sqlite3.connect("codesaga.db")
    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def save_quiz_attempt(
    student_id,
    checkpoint_number,
    question_type,
    submitted_answer,
    is_correct
):
    """
    Save every submitted quiz answer.
    """

    connection = get_database_connection()

    connection.execute(
        """
        INSERT INTO quiz_attempts (
            student_id,
            chapter_number,
            checkpoint_number,
            question_type,
            submitted_answer,
            is_correct
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            1,
            checkpoint_number,
            question_type,
            submitted_answer,
            1 if is_correct else 0
        )
    )

    connection.commit()
    connection.close()


def save_chapter_progress(student_id, score):
    """
    Save or update the student's final chapter score.
    """

    connection = get_database_connection()

    connection.execute(
        """
        INSERT INTO chapter_progress (
            student_id,
            chapter_number,
            score,
            total_questions,
            completed,
            completed_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

        ON CONFLICT(student_id, chapter_number)
        DO UPDATE SET
            score = excluded.score,
            total_questions = excluded.total_questions,
            completed = excluded.completed,
            completed_at = CURRENT_TIMESTAMP
        """,
        (
            student_id,
            1,
            score,
            3,
            1
        )
    )

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        connection = get_database_connection()

        student = connection.execute(
            """
            SELECT *
            FROM students
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if student and check_password_hash(
            student["password_hash"],
            password
        ):
            # Remove any old mission data.
            session.clear()

            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("dashboard"))

        error = "Incorrect email or password."

    return render_template(
        "login.html",
        error=error
    )


@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        student_name=session["student_name"]
    )


@app.route("/mission/setup", methods=["GET", "POST"])
def mission_setup():
    if "student_id" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        selected_module = request.form.get("module")
        selected_theme = request.form.get("theme")

        allowed_modules = {
            "python_lists": "Python Lists"
        }

        allowed_themes = {
            "cyber_mystery": "Cyber Mystery",
            "fantasy": "Fantasy Adventure",
            "space": "Space Expedition"
        }

        if selected_module not in allowed_modules:
            error = "Please select an available module."

        elif selected_theme not in allowed_themes:
            error = "Please select a story theme."

        else:
            session["module"] = selected_module

            session["module_name"] = (
                allowed_modules[selected_module]
            )

            session["theme"] = selected_theme

            session["theme_name"] = (
                allowed_themes[selected_theme]
            )

            # Start the chapter from zero.
            session["chapter_score"] = 0

            return redirect(url_for("mission_intro"))

    return render_template(
        "mission_setup.html",
        error=error
    )


@app.route("/mission")
def mission_intro():
    if "student_id" not in session:
        return redirect(url_for("login"))

    if "module" not in session or "theme" not in session:
        return redirect(url_for("mission_setup"))

    return render_template(
        "mission_intro.html",
        student_name=session["student_name"],
        module_name=session["module_name"],
        theme=session["theme"],
        theme_name=session["theme_name"]
    )


@app.route("/chapter/1", methods=["GET", "POST"])
def chapter_one():
    if "student_id" not in session:
        return redirect(url_for("login"))

    if "theme" not in session:
        return redirect(url_for("mission_setup"))

    feedback = None
    feedback_type = None
    selected_answer = None

    if request.method == "GET":
        if session.get("chapter_score", 0) >= 1:
            feedback = (
                "Checkpoint 1 has already been completed."
            )
            feedback_type = "correct"

    if request.method == "POST":
        selected_answer = request.form.get("answer")

        if selected_answer:
            is_correct = (
                selected_answer == "square_brackets"
            )

            save_quiz_attempt(
                student_id=session["student_id"],
                checkpoint_number=1,
                question_type="MCQ",
                submitted_answer=selected_answer,
                is_correct=is_correct
            )

            if is_correct:
                feedback = (
                    "Correct! You identified the symbols "
                    "used to create a Python list."
                )

                feedback_type = "correct"

                session["chapter_score"] = max(
                    session.get("chapter_score", 0),
                    1
                )

            else:
                feedback = generate_gemini_hint(
                    theme_name=session["theme_name"],
                    question=(
                        "Which symbols are used to create "
                        "a Python list?"
                    ),
                    student_answer=selected_answer,
                    correct_concept=(
                        "Python lists are created using "
                        "square brackets."
                    ),
                    fallback_hint=(
                        "Cipher's hint: Look carefully at the "
                        "symbols surrounding the security codes "
                        "in the story panel."
                    )
                )

                feedback_type = "incorrect"

        else:
            feedback = "Please select an answer."
            feedback_type = "incorrect"

    return render_template(
        "chapter_one.html",
        student_name=session["student_name"],
        theme=session["theme"],
        theme_name=session["theme_name"],
        feedback=feedback,
        feedback_type=feedback_type,
        selected_answer=selected_answer
    )


@app.route(
    "/chapter/1/checkpoint/2",
    methods=["GET", "POST"]
)
def checkpoint_two():
    if "student_id" not in session:
        return redirect(url_for("login"))

    if "theme" not in session:
        return redirect(url_for("mission_setup"))

    if session.get("chapter_score", 0) < 1:
        return redirect(url_for("chapter_one"))

    feedback = None
    feedback_type = None
    submitted_answer = ""

    if request.method == "GET":
        if session.get("chapter_score", 0) >= 2:
            feedback = (
                "Checkpoint 2 has already been completed."
            )
            feedback_type = "correct"

    if request.method == "POST":
        submitted_answer = request.form.get(
            "answer",
            ""
        ).strip()

        if submitted_answer:
            is_correct = submitted_answer == "2"

            save_quiz_attempt(
                student_id=session["student_id"],
                checkpoint_number=2,
                question_type="Fill in the blank",
                submitted_answer=submitted_answer,
                is_correct=is_correct
            )

            if is_correct:
                feedback = (
                    "Correct! The third value is stored at "
                    "index 2 because Python starts counting "
                    "from zero."
                )

                feedback_type = "correct"

                session["chapter_score"] = max(
                    session.get("chapter_score", 0),
                    2
                )

            else:
                feedback = generate_gemini_hint(
                    theme_name=session["theme_name"],
                    question=(
                        "Which index accesses the third value "
                        "inside a Python list?"
                    ),
                    student_answer=submitted_answer,
                    correct_concept=(
                        "Python uses zero-based indexing. "
                        "The first item is index 0, the second "
                        "is index 1 and the third is index 2."
                    ),
                    fallback_hint=(
                        "Cipher's hint: Write the index "
                        "positions below the values, "
                        "beginning with 0."
                    )
                )

                feedback_type = "incorrect"

        else:
            feedback = "Please fill in the missing value."
            feedback_type = "incorrect"

    return render_template(
        "checkpoint_two.html",
        theme=session["theme"],
        theme_name=session["theme_name"],
        feedback=feedback,
        feedback_type=feedback_type,
        submitted_answer=submitted_answer
    )


@app.route(
    "/chapter/1/checkpoint/3",
    methods=["GET", "POST"]
)
def checkpoint_three():
    if "student_id" not in session:
        return redirect(url_for("login"))

    if "theme" not in session:
        return redirect(url_for("mission_setup"))

    if session.get("chapter_score", 0) < 2:
        return redirect(url_for("checkpoint_two"))

    feedback = None
    feedback_type = None
    selected_answer = None

    if request.method == "GET":
        if session.get("chapter_score", 0) >= 3:
            feedback = (
                "The final checkpoint has already been completed."
            )
            feedback_type = "correct"

    if request.method == "POST":
        selected_answer = request.form.get("answer")

        if selected_answer:
            is_correct = selected_answer == "max"

            save_quiz_attempt(
                student_id=session["student_id"],
                checkpoint_number=3,
                question_type="MCQ",
                submitted_answer=selected_answer,
                is_correct=is_correct
            )

            if is_correct:
                feedback = (
                    "Correct! The max() function returns "
                    "the largest value from a Python list."
                )

                feedback_type = "correct"
                session["chapter_score"] = 3

                save_chapter_progress(
                    student_id=session["student_id"],
                    score=3
                )

            else:
                feedback = generate_gemini_hint(
                    theme_name=session["theme_name"],
                    question=(
                        "Which Python function returns the "
                        "largest value from a list?"
                    ),
                    student_answer=selected_answer,
                    correct_concept=(
                        "The max() function returns the "
                        "largest value from a list."
                    ),
                    fallback_hint=(
                        "Cipher's hint: Look for the function "
                        "whose name means the greatest "
                        "possible value."
                    )
                )

                feedback_type = "incorrect"

        else:
            feedback = "Please select an answer."
            feedback_type = "incorrect"

    return render_template(
        "checkpoint_three.html",
        theme=session["theme"],
        theme_name=session["theme_name"],
        feedback=feedback,
        feedback_type=feedback_type,
        selected_answer=selected_answer
    )


@app.route("/chapter/1/complete")
def chapter_complete():
    if "student_id" not in session:
        return redirect(url_for("login"))

    if session.get("chapter_score", 0) < 3:
        return redirect(url_for("checkpoint_three"))

    return render_template(
        "chapter_complete.html",
        student_name=session["student_name"],
        theme=session["theme"],
        theme_name=session["theme_name"],
        score=session["chapter_score"]
    )


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)