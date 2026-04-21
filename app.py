"""
Application de gestion des présences aux entraînements de rugby.
Lancer avec : python app.py
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Clé secrète pour les sessions (à changer en production !)
app.secret_key = os.environ.get("SECRET_KEY", "rugby-secret-key-2024")

# ── Mot de passe coach (modifiable ici ou via variable d'environnement) ────────
COACH_PASSWORD = os.environ.get("COACH_PASSWORD", "allez-les-verts")

# ── Base de données ────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "rugby.db")

def get_db():
    """Retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # accès par nom de colonne
    return conn

def init_db():
    """Crée les tables si elles n'existent pas encore."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS trainings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT NOT NULL UNIQUE,          -- format ISO : YYYY-MM-DD
                label     TEXT,                          -- description optionnelle
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                training_id INTEGER NOT NULL REFERENCES trainings(id),
                status      TEXT NOT NULL CHECK(status IN ('present','absent')),
                updated_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(player_name, training_id)        -- un seul enregistrement par joueur/séance
            );
        """)

# ── Authentification coach ────────────────────────────────────────────────────

def login_required(f):
    """Décorateur : redirige vers /login si le coach n'est pas connecté."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("coach_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """Page de connexion coach."""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == COACH_PASSWORD:
            session["coach_logged_in"] = True
            return redirect(url_for("coach_page"))
        else:
            error = "Mot de passe incorrect. Réessayez."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Déconnexion du coach."""
    session.pop("coach_logged_in", None)
    return redirect(url_for("player_page"))


# ── Routes publiques (joueurs) ─────────────────────────────────────────────────

@app.route("/")
def player_page():
    """Page principale destinée aux joueurs."""
    with get_db() as conn:
        # Séances à venir (inclus aujourd'hui)
        today = datetime.today().strftime("%Y-%m-%d")
        trainings = conn.execute(
            "SELECT * FROM trainings WHERE date >= ? ORDER BY date ASC", (today,)
        ).fetchall()
    return render_template("player.html", trainings=trainings)


@app.route("/submit", methods=["POST"])
def submit():
    """Enregistre (ou met à jour) les réponses d'un joueur."""
    data = request.get_json()
    player_name = (data.get("player_name") or "").strip()
    responses   = data.get("responses", [])   # liste de {training_id, status}

    if not player_name:
        return jsonify({"ok": False, "error": "Nom du joueur manquant."}), 400
    if not responses:
        return jsonify({"ok": False, "error": "Aucune réponse fournie."}), 400

    with get_db() as conn:
        for r in responses:
            tid    = r.get("training_id")
            status = r.get("status")
            if tid is None or status not in ("present", "absent"):
                continue
            # INSERT OR REPLACE gère la règle d'unicité + modification
            conn.execute("""
                INSERT INTO attendance (player_name, training_id, status, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(player_name, training_id)
                DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at
            """, (player_name, tid, status))

    return jsonify({"ok": True})


# ── Routes coach ───────────────────────────────────────────────────────────────

@app.route("/coach")
@login_required
def coach_page():
    """Tableau de bord de l'entraîneur."""
    with get_db() as conn:
        trainings = conn.execute(
            "SELECT * FROM trainings ORDER BY date ASC"
        ).fetchall()

        # Pour chaque séance : récupérer les réponses avec résumé
        sessions = []
        for t in trainings:
            rows = conn.execute("""
                SELECT player_name, status, updated_at
                FROM attendance
                WHERE training_id = ?
                ORDER BY player_name ASC
            """, (t["id"],)).fetchall()

            present = sum(1 for r in rows if r["status"] == "present")
            absent  = sum(1 for r in rows if r["status"] == "absent")

            sessions.append({
                "training": t,
                "rows": rows,
                "present": present,
                "absent": absent,
            })

    return render_template("coach.html", sessions=sessions)


@app.route("/add_training", methods=["POST"])
@login_required
def add_training():
    """Ajoute une nouvelle date d'entraînement."""
    date  = (request.form.get("date") or "").strip()
    label = (request.form.get("label") or "").strip()

    if not date:
        return redirect(url_for("coach_page"))

    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO trainings (date, label) VALUES (?, ?)", (date, label)
            )
        except sqlite3.IntegrityError:
            pass  # date déjà existante, on ignore

    return redirect(url_for("coach_page"))


@app.route("/delete_training/<int:training_id>", methods=["POST"])
@login_required
def delete_training(training_id):
    """Supprime une séance et ses réponses associées."""
    with get_db() as conn:
        conn.execute("DELETE FROM attendance WHERE training_id = ?", (training_id,))
        conn.execute("DELETE FROM trainings WHERE id = ?", (training_id,))
    return redirect(url_for("coach_page"))


# ── Lancement ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("✅  Base de données initialisée.")
    print("🏉  Application Rugby disponible sur http://localhost:5000")
    app.run(debug=True, port=5000)
