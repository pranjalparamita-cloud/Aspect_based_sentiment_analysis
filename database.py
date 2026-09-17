"""
database.py — SQLite database layer (100% free, file-based).
------------------------------------------------------------
Tables:
  users            -> accounts (username, gmail, hashed password, photo, ...)
  activity_logs    -> every user action (for the Admin tracking panel)
  analysis_history -> every product analysis each user runs

All other files talk to the DB ONLY through the functions below.
"""
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

from config import DB_PATH


# ---------- low-level ----------

def get_conn():
    """Open a fresh DB connection (safe for Streamlit's threading)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables + seed demo accounts. Runs once at app startup."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            profile_pic TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            is_admin INTEGER DEFAULT 0,
            provider TEXT DEFAULT 'email',
            created_at TEXT NOT NULL,
            last_login TEXT DEFAULT ''
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            email TEXT,
            event_type TEXT,
            detail TEXT,
            timestamp TEXT,
            session_id TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id TEXT,
            product_name TEXT,
            platform TEXT,
            total_reviews INTEGER,
            positive INTEGER,
            neutral INTEGER,
            negative INTEGER,
            overall TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()

    # Seed demo accounts (only if missing). Import here to avoid a
    # circular import (auth.py itself imports this file).
    from auth import hash_password
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seeds = [
        ("admin", "admin@gmail.com", "Admin@123", 1, "email"),
        ("demo", "demo@gmail.com", "Demo@123", 0, "email"),
    ]
    for username, email, pwd, is_admin, provider in seeds:
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        if cur.fetchone() is None:
            phash, salt = hash_password(pwd)
            cur.execute(
                """INSERT INTO users (username,email,password_hash,salt,is_admin,provider,created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (username, email, phash, salt, is_admin, provider, now),
            )
    conn.commit()
    conn.close()


# ---------- users ----------

def row_to_dict(row):
    return dict(row) if row else None


def create_user(username, email, password, provider="email", is_admin=0):
    """Create an account (password is hashed) and return the user dict."""
    from auth import hash_password  # local import: avoids circular import
    conn = get_conn()
    cur = conn.cursor()
    phash, salt = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """INSERT INTO users (username,email,password_hash,salt,is_admin,provider,created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (username.strip(), email.strip().lower(), phash, salt, is_admin, provider, now),
    )
    uid = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = row_to_dict(cur.fetchone())
    conn.close()
    return user


def get_user_by_login(login: str):
    """Find a user by username OR email (case-insensitive)."""
    conn = get_conn()
    cur = conn.cursor()
    login = login.strip().lower()
    cur.execute("SELECT * FROM users WHERE LOWER(email)=? OR LOWER(username)=?", (login, login))
    user = row_to_dict(cur.fetchone())
    conn.close()
    return user


def get_user_by_id(uid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = row_to_dict(cur.fetchone())
    conn.close()
    return user


def update_user(uid: int, **fields):
    """Update allowed user fields: username, password_hash, salt,
    profile_pic, bio, phone, last_login."""
    allowed = {"username", "password_hash", "salt", "profile_pic", "bio", "phone", "last_login"}
    sets = [f"{k}=?" for k in fields if k in allowed]
    if not sets:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?",
                [fields[k] for k in fields if k in allowed] + [uid])
    conn.commit()
    conn.close()


# ---------- tracking & history ----------

def log_event(user, event_type: str, detail: str = ""):
    """Record a user action (login, search, analyse, logout, ...) for Admin."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO activity_logs (user_id,username,email,event_type,detail,timestamp,session_id)
               VALUES (?,?,?,?,?,?,?)""",
            (user["id"] if user else None,
             user["username"] if user else "guest",
             user["email"] if user else "",
             event_type, detail[:500],
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             st.session_state.get("session_id", "")),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # tracking must never crash the app


def save_analysis(user_id, product, total, pos, neu, neg, overall):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO analysis_history
           (user_id,product_id,product_name,platform,total_reviews,positive,neutral,negative,overall,timestamp)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (user_id, product["id"], product["name"], product["platform"], total,
         pos, neu, neg, overall, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def fetch_df(query, params=()):
    """Run a SELECT query and return a pandas DataFrame."""
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
