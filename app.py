import os
from flask import Flask, render_template_string, request, redirect, session
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "vistaoptica_secret_key_2026"

DATABASE_URL = os.environ.get("DATABASE_URL")

# ---------- DB ----------
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # Crear usuario admin si no existe
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", generate_password_hash("vistaoptica123"))
        )

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------- HTML ----------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vista Óptica</title>
</head>
<body>
    <h1>Vista Óptica</h1>
    <form method="POST">
        <input name="username" placeholder="Usuario" required><br><br>
        <input name="password" type="password" placeholder="Contraseña" required><br><br>
        <button type="submit">Entrar</button>
    </form>
    <p style="color:red;">{{ error }}</p>
</body>
</html>
"""

PANEL_HTML = """
<h1>Bienvenido a Vista Óptica</h1>
<p>Has iniciado sesión correctamente.</p>
<a href="/logout">Cerrar sesión</a>
"""

# ---------- RUTAS ----------
@app.route("/", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/panel")
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template_string(LOGIN_HTML, error=error)

@app.route("/panel")
def panel():
    if "user" not in session:
        return redirect("/")
    return render_template_string(PANEL_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
