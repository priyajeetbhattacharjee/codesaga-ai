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
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

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
            session["module_name"] = allowed_modules[selected_module]

            session["theme"] = selected_theme
            session["theme_name"] = allowed_themes[selected_theme]

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)