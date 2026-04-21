# 🏉 Rugby Présences – Application Web

Gestion simple des présences aux entraînements de rugby.

---

## 🚀 Lancement rapide (en local)

```bash
# 1. Créez un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 2. Installez Flask
pip install -r requirements.txt

# 3. Lancez l'application
python app.py
```

Ouvrez ensuite votre navigateur sur **http://localhost:5000**

---

## 📱 Pages disponibles

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Page joueur – indiquer ses disponibilités |
| `http://localhost:5000/coach` | Dashboard coach – gérer les séances et voir les réponses |

---

## 🏗️ Structure du projet

```
rugby-app/
├── app.py               ← Application Flask principale
├── requirements.txt     ← Dépendances Python
├── rugby.db             ← Base SQLite (créée automatiquement au premier lancement)
├── README.md
└── templates/
    ├── player.html      ← Interface joueur
    └── coach.html       ← Dashboard entraîneur
```

---

## ☁️ Déploiement en ligne

### Option A – Render.com (gratuit)
1. Créez un compte sur [render.com](https://render.com)
2. « New Web Service » → connectez votre dépôt GitHub
3. Build command : `pip install -r requirements.txt`
4. Start command : `gunicorn app:app`
5. Ajoutez `gunicorn` à `requirements.txt`

### Option B – Railway
1. Compte sur [railway.app](https://railway.app)
2. Déployez depuis GitHub, Railway détecte Flask automatiquement

### Option C – VPS (nginx + gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Puis configurez nginx pour faire du reverse proxy sur le port 8000.

---

## 🔧 Variables d'environnement (production)

```bash
FLASK_ENV=production
SECRET_KEY=votre-clé-secrète-ici
```

---

## ✨ Fonctionnalités

- ✅ Page joueur : saisie du nom + présent/absent pour chaque séance
- ✅ Envoi de plusieurs réponses en une seule fois
- ✅ Modification possible (re-soumettre écrase l'ancienne réponse)
- ✅ Dashboard coach : ajout/suppression de séances
- ✅ Résumé présents/absents par séance
- ✅ Interface mobile-friendly
- ✅ Base SQLite embarquée (zéro config)
