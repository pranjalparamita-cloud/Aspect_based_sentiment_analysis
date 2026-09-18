# 💜 AspectLens — Aspect-Based Sentiment Analytics

A **100% FREE** glassmorphism web app built with **Streamlit + SQLite + Plotly + pure-Python NLP**.
No paid APIs, no heavy ML downloads — deploys in one click on **Streamlit Community Cloud**.

![glassmorphism UI](https://placehold.co/800x200?text=Pastel+Glassmorphism+UI)

---

## ✨ Features

| Module | What it does |
|---|---|
| **🔐 Login / Sign-Up** | Gmail Authenticator (only `@gmail.com`), username + password + confirm password, hashed with PBKDF2 |
| **🌐 Continue with Google** | REAL Google OAuth: Google's own chooser with logged-in Gmails, one-click login (see `GOOGLE_SETUP.md`); demo fallback when not configured |
| **📁 Flexible datasets** | Upload CSV, Excel, JSON or JSONL review data with any number of columns; supports malformed marketplace exports and preserves every source field |
| **🗂️ Smart mapping** | Detects review text, item/product, rating, date and author from different header names *and actual sample values*; all suggestions are editable |
| **🔍 Analysis** | Key-wise search across detected items (`r → re → red → redmi`) with optional review-keyword and rating filters |
| **📊 Dashboard** | One click → NLP aspect-sentiment dashboard: **Sunburst, Bar, Radar, Donut + timeline/rolling Line** chart, KPI cards, aspect table, annotated reviews |
| **👤 My Profile** | Edit username, phone, bio, profile photo (stored in DB), change password, personal stats |
| **🕘 My History** | Every analysis you ran + CSV download |
| **🛡️ Admin Panel** | Full **user tracking**: login time, every action, logout/leave time, session durations, charts, CSV exports |

### NLP engine (offline, free)
- 8 aspects: **Quality, Price, Delivery, Packaging, Service, Features, Durability, Design**
- Keyword tagging + negation/intensifier-aware lexicon scoring per sentence
- Deterministic per-product review corpus (60 reviews each) so results are stable

---

## 🚀 Deploy on Streamlit Cloud (free)

1. Push this folder to a **public GitHub repo** (files: `app.py`, `requirements.txt`, `.streamlit/config.toml`).
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app** → pick repo/branch → main file `app.py` → **Deploy**.
3. Done! Your app is live with a free `https://<app>.streamlit.app` URL.

> The SQLite database (`absa.db`) is created automatically on first run.
> Demo accounts are seeded automatically (see below).

## 💻 Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🔑 Demo accounts

| Role | Email | Password |
|---|---|---|
| User | `demo@gmail.com` | `Demo@123` |
| Admin | `admin@gmail.com` | `Admin@123` |

## 📁 Project structure

```
aspect-sentiment-app/
├── app.py                  # entry point: theme, sidebar, routing (run THIS file)
├── config.py               # constants: colours, DB path, app name
├── styles.py               # glassmorphism CSS theme
├── database.py             # SQLite: users, activity logs, analysis history
├── auth.py                 # passwords, Gmail validation, login sessions
├── google_auth.py          # real "Continue with Google" (OAuth 2.0)
├── GOOGLE_SETUP.md         # guide: enable real Google login (free)
├── datasets.py             # flexible CSV/Excel/JSON uploads, smart schema inference, search
├── sample_data.csv         # demo dataset (120 reviews, 3 items)
├── nlp_engine.py           # aspect-sentiment NLP
├── charts.py               # all 5 Plotly dashboard figures
├── ui_helpers.py           # reusable cards / avatars / badges
├── views/                  # one file per screen
│   ├── login.py            # login / sign-up / Google chooser
│   ├── analysis.py         # search grid + NLP dashboard
│   ├── profile.py          # edit profile + password + photo
│   ├── history.py          # user's past analyses
│   └── admin.py            # admin user-tracking panel
├── requirements.txt        # 100% free dependencies
├── .streamlit/config.toml  # pastel theme
└── README.md
```

## 🔌 Real Google login (recommended)

The app ships with demo-mode Google login so it works immediately.
For the REAL Gmail chooser (one-click login with logged-in accounts),
follow **`GOOGLE_SETUP.md`** — free Google Cloud OAuth setup (~10 min),
then add 3 secrets in Streamlit Cloud → Manage app → Settings → Secrets.

## 🛡️ Notes

- Passwords are salted + hashed (PBKDF2-HMAC-SHA256, 100k rounds) — never stored plain.
- Profile photos are resized to 256×256 and stored as base64 in SQLite (no file server needed).
- "Leave time" is exact when users click **Logout**; otherwise the admin sees their last activity time.

Made with 💜 using only free & open-source tools.
