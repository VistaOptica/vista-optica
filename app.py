import os
import psycopg2
from flask import Flask, request, render_template_string

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Crear tabla automáticamente
with get_db() as conn:
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        """)
        conn.commit()

LOGIN_HTML = """
<h1>Vista Óptica</h1>
<form method="POST">
  <input name="username" placeholder="Usuario"><br><br>
  <input name="password" type="password" placeholder="Contraseña"><br><br>
  <button>Entrar</button>
</form>
<p style="color:red">{{error}}</p>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE username=%s", (user,))
                row = cur.fetchone()

                if row and row[0] == pw:
                    return "<h1>Bienvenido a Vista Óptica</h1>"
                else:
                    error = "Usuario o contraseña incorrectos"

    return render_template_string(LOGIN_HTML, error=error)

# Ruta para crear usuario admin
@app.route("/create_admin")
def create_admin():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, password)
                VALUES ('admin', '1234')
                ON CONFLICT DO NOTHING;
            """)
            conn.commit()
    return "Usuario admin creado correctamente"
