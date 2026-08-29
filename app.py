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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)