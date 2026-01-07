from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "vistaoptica123"

# ---------------- DATABASE ----------------
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            name TEXT,
            dni TEXT,
            phone TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER,
            od TEXT,
            oi TEXT,
            diagnosis TEXT,
            notes TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER,
            frame TEXT,
            lens TEXT,
            status TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER,
            amount REAL,
            concept TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    db.commit()
    cur.close()
    db.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE username=%s AND password=%s", (user,pwd))
        u = cur.fetchone()

        cur.close()
        db.close()

        if u:
            session["user"] = u[0]
            return redirect("/dashboard
