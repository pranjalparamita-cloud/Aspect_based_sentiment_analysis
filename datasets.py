"""
datasets.py — User-uploaded review datasets (CSV / Excel, one or many).
------------------------------------------------------------------------
Replaces the old built-in store catalog. Users bring their OWN data:

  read_upload(file)      parse an uploaded CSV/XLSX file -> DataFrame
  auto_map_columns(df)   guess which column is review / item / rating / date
  reviews_from_df(...)   convert DataFrame rows -> [{author, rating, text, date}]
  search_items(...)      key-wise prefix search over item names
  save/list/load/delete  per-user dataset persistence (SQLite)
  load_sample()          built-in demo dataset (sample_data.csv)
"""
import io
import os

import pandas as pd

from database import get_conn, fetch_df

MAX_ROWS = 5000  # safety cap per file (speed + DB size)

# Column-name guesses (case-insensitive, substring match)
TEXT_CANDIDATES = ["review", "text", "comment", "feedback", "opinion", "remark", "description", "message"]
ITEM_CANDIDATES = ["product", "item", "title", "model", "name"]
RATING_CANDIDATES = ["rating", "star", "score"]
DATE_CANDIDATES = ["date", "timestamp", "created", "time", "day"]
AUTHOR_CANDIDATES = ["author", "reviewer", "username", "user", "customer"]


# ---------- parsing ----------

def read_upload(file) -> pd.DataFrame:
    """Read an uploaded CSV or Excel file into a clean DataFrame."""
    name = (file.name or "").lower()
    if name.endswith(".csv"):
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding="utf-8-sig")
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, encoding="latin-1")
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)  # needs openpyxl (in requirements.txt)
    else:
        raise ValueError(f"Unsupported file type: {file.name} (use .csv or .xlsx)")
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    truncated = len(df) > MAX_ROWS
    if truncated:
        df = df.head(MAX_ROWS)
    return df, truncated


def auto_map_columns(df) -> dict:
    """Guess mapping {text, item, rating, date, author} -> column name or None."""
    cols = list(df.columns)
    low = [c.lower() for c in cols]

    def find(cands, skip=()):
        for cand in cands:
            for c, l in zip(cols, low):
                if c in skip:
                    continue
                if cand == l or cand in l:
                    return c
        return None

    text = find(TEXT_CANDIDATES)
    if text is None and cols:  # fallback: longest-text column
        text = max(cols, key=lambda c: df[c].astype(str).str.len().mean())
    item = find(ITEM_CANDIDATES, skip=(text,))
    rating = find(RATING_CANDIDATES, skip=(text, item))
    date = find(DATE_CANDIDATES, skip=(text, item, rating))
    author = find(AUTHOR_CANDIDATES, skip=(text, item, rating, date))
    return {"text": text, "item": item, "rating": rating, "date": date, "author": author}


# ---------- analysis helpers ----------

def reviews_from_df(df: pd.DataFrame, mapping: dict, limit: int = 2000) -> list:
    """Convert DataFrame rows to the review-dict format nlp_engine expects."""
    t, r, d, a = mapping.get("text"), mapping.get("rating"), mapping.get("date"), mapping.get("author")
    out = []
    for i, (_, row) in enumerate(df.iterrows()):
        if len(out) >= limit:
            break
        text = str(row[t]).strip() if t in df.columns else ""
        if not text or text.lower() == "nan":
            continue
        rating = None
        if r in (df.columns if r else []):
            try:
                rating = float(row[r])
            except (TypeError, ValueError):
                rating = None
        date = str(row[d]).strip() if d in (df.columns if d else []) else ""
        if date.lower() == "nan":
            date = ""
        author = str(row[a]).strip() if a in (df.columns if a else []) else ""
        if not author or author.lower() == "nan":
            author = f"Review #{i + 1}"
        out.append({"author": author, "rating": rating, "text": text, "date": date})
    return out


def search_items(items: list, query: str) -> list:
    """Key-wise prefix search: items STARTING with the query rank first,
    then items merely containing it ('r' -> 're' -> 'redmi' style)."""
    q = (query or "").strip().lower()
    items = [str(x) for x in items]
    if not q:
        return sorted(set(items))
    starts = sorted({x for x in items if x.lower().startswith(q)})
    contains = sorted({x for x in items if q in x.lower() and x not in starts})
    return starts + contains


# ---------- persistence (per user, in SQLite) ----------

def _unique_name(user_id: int, name: str) -> str:
    base = name.rsplit(".", 1)[0][:60] or "dataset"
    existing = {d["name"] for d in list_datasets(user_id)}
    if base not in existing:
        return base
    i = 2
    while f"{base} ({i})" in existing:
        i += 1
    return f"{base} ({i})"


def save_dataset(user_id: int, filename: str, df: pd.DataFrame) -> str:
    """Store a dataset; returns the saved (unique) name."""
    name = _unique_name(user_id, filename)
    conn = get_conn()
    conn.execute(
        """INSERT INTO datasets (user_id, name, csv_text, columns, row_count, created_at)
           VALUES (?,?,?,?,?, datetime('now','localtime'))""",
        (user_id, name, df.to_csv(index=False), ", ".join(df.columns), len(df)),
    )
    conn.commit()
    conn.close()
    return name


def list_datasets(user_id: int) -> list:
    df = fetch_df(
        "SELECT id, name, columns, row_count, created_at FROM datasets WHERE user_id=? ORDER BY id DESC",
        (user_id,))
    return df.to_dict("records") if not df.empty else []


def load_dataset(dataset_id: int, user_id: int):
    """Return (name, DataFrame) for one of the user's datasets."""
    df = fetch_df("SELECT name, csv_text FROM datasets WHERE id=? AND user_id=?",
                  (dataset_id, user_id))
    if df.empty:
        return None, None
    return df["name"][0], pd.read_csv(io.StringIO(df["csv_text"][0]))


def delete_dataset(dataset_id: int, user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM datasets WHERE id=? AND user_id=?", (dataset_id, user_id))
    conn.commit()
    conn.close()


def load_sample():
    """Built-in demo dataset so users can try analysis instantly."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data.csv")
    return "Sample Reviews (demo)", pd.read_csv(path)
