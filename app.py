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
from werkzeug.security import check_password_hash


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "temporary-development-key"
)


def get_database_connection():
    connection = sqlite3.connect("codesaga.db")
    connection.row_factory = sqlite3.Row
    return connection


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

            # Reset score whenever a new mission begins.
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

        if selected_answer == "square_brackets":
            feedback = (
                "Correct! You identified the symbols used "
                "to create a Python list."
            )

            feedback_type = "correct"

            session["chapter_score"] = max(
                session.get("chapter_score", 0),
                1
            )

        elif selected_answer:
            feedback = (
                "Cipher's hint: Look carefully at the "
                "symbols surrounding the security codes "
                "in the story panel."
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

        if submitted_answer == "2":
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

        elif submitted_answer:
            feedback = (
                "Cipher's hint: Write the index positions "
                "below the values, beginning with 0."
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)