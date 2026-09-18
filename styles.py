"""
styles.py — Glassmorphism theme (pastel mesh background, glass cards,
gradient titles, pill buttons). Call apply_custom_css() once from app.py.
"""
import streamlit as st

GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

.stApp {
  font-family: 'Poppins', sans-serif;
  background:
    radial-gradient(1000px 620px at 8% 8%,   rgba(199,233,255,0.95), transparent 60%),
    radial-gradient(950px 720px at 92% 12%,  rgba(255,209,220,0.95), transparent 60%),
    radial-gradient(820px 620px at 88% 92%,  rgba(255,178,200,0.65), transparent 60%),
    radial-gradient(920px 720px at 8% 95%,   rgba(255,243,196,0.95), transparent 60%),
    radial-gradient(760px 560px at 50% 55%,  rgba(230,222,255,0.85), transparent 65%),
    linear-gradient(135deg, #eef4ff 0%, #fdf1f5 60%, #ffeef3 100%);
  background-attachment: fixed;
  color: #2b2350;
}
[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.45) !important;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-right: 1px solid rgba(255,255,255,0.65);
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
[data-testid="stHeader"] { background: rgba(255,255,255,0.0) !important; }
[data-testid="stToolbar"] { display: none; }
footer { visibility: hidden; }

.gradient-title {
  font-weight: 800; letter-spacing: -0.5px; line-height: 1.1;
  font-size: 2.7rem;
  background: linear-gradient(90deg, #5b6abf 0%, #0891b2 30%, #9333ea 65%, #ec4899 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.subtitle { color: #5b5675; font-size: 1.02rem; margin-top: 6px; }

.glass {
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.75);
  box-shadow: 0 8px 32px rgba(150,120,255,0.16);
  padding: 24px;
}
.glass-soft {
  background: rgba(255,255,255,0.42);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 6px 24px rgba(150,120,255,0.12);
  padding: 18px;
}
.auth-card { max-width: 560px; margin: 4vh auto; padding: 34px 36px; }
.brand-mini { color: #9333ea; font-weight: 700; font-size: 1.05rem; letter-spacing: 0.2px; }
.divider-line { height: 3px; border-radius: 99px; margin: 14px 0 20px;
  background: linear-gradient(90deg, rgba(34,211,238,0.7), rgba(232,121,249,0.15), rgba(139,92,246,0.7)); }

.kpi-label { font-size: 0.72rem; letter-spacing: 1.6px; color: #6d6890; font-weight: 600; }
.kpi-value { font-size: 2.6rem; font-weight: 800; color: #7c3aed; line-height: 1.1; }
.kpi-sub { font-size: 0.82rem; color: #6d6890; }

.item-name { font-weight: 700; font-size: 1rem; color: #2b2350; margin: 10px 0 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.9em; }
.badge { display: inline-block; font-size: 0.68rem; font-weight: 700; color: #fff;
  padding: 3px 10px; border-radius: 999px; margin-right: 6px; }
.price-row { margin-top: 6px; font-size: 0.9rem; }
.price-now { font-weight: 800; color: #2b2350; font-size: 1.02rem; }
.price-was { text-decoration: line-through; color: #9a94b8; font-size: 0.8rem; margin-left: 6px; }
.stars { color: #f59e0b; font-size: 0.82rem; letter-spacing: 1px; }

.sent-pos { background: rgba(16,185,129,0.16); color: #047857; border: 1px solid rgba(16,185,129,0.4);
  padding: 2px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.sent-neg { background: rgba(244,63,94,0.12); color: #be123c; border: 1px solid rgba(244,63,94,0.4);
  padding: 2px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.sent-neu { background: rgba(139,92,246,0.12); color: #6d28d9; border: 1px solid rgba(139,92,246,0.4);
  padding: 2px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.aspect-tag { background: rgba(255,255,255,0.8); border: 1px solid #e3d9ff; color: #6d28d9;
  padding: 2px 10px; border-radius: 999px; font-size: 0.7rem; font-weight: 600; margin-right: 4px; }

.avatar { width: 78px; height: 78px; border-radius: 50%; object-fit: cover;
  border: 3px solid rgba(255,255,255,0.9); box-shadow: 0 6px 18px rgba(147,51,234,0.3); }
.avatar-sm { width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
  border: 2px solid rgba(255,255,255,0.9); box-shadow: 0 4px 12px rgba(147,51,234,0.25); }
.avatar-fallback { display: flex; align-items: center; justify-content: center; color: #fff;
  font-weight: 800; background: linear-gradient(135deg, #8b5cf6, #ec4899); }

.stButton > button {
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%) !important;
  color: #fff !important; border: none !important; border-radius: 999px !important;
  padding: 0.55rem 1.9rem !important; font-weight: 600 !important; font-family: 'Poppins', sans-serif !important;
  box-shadow: 0 8px 20px rgba(168,85,247,0.35) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 12px 26px rgba(168,85,247,0.45) !important; }
.stButton > button[kind="secondary"] {
  background: rgba(255,255,255,0.85) !important; color: #4c1d95 !important;
  border: 1px solid #e3d9ff !important; box-shadow: 0 4px 14px rgba(150,120,255,0.15) !important;
}
.stTextInput input, .stTextArea textarea {
  border-radius: 14px !important; background: rgba(255,255,255,0.85) !important;
  border: 1px solid rgba(200,180,255,0.5) !important;
}
.stSelectbox div[data-baseweb="select"] > div { border-radius: 14px !important;
  background: rgba(255,255,255,0.85) !important; border: 1px solid rgba(200,180,255,0.5) !important; }
div[data-testid="stRadio"] label { background: rgba(255,255,255,0.6); border: 1px solid rgba(255,255,255,0.7);
  border-radius: 12px; padding: 6px 14px; margin-right: 6px; font-weight: 500; }
.streamlit-expanderHeader { font-weight: 600; color: #4c1d95; }
h1, h2, h3 { color: #2b2350; font-family: 'Poppins', sans-serif; }
.small-note { font-size: 0.78rem; color: #77719a; }
</style>
"""


def apply_custom_css():
    """Inject the glassmorphism theme into the Streamlit app."""
    st.markdown(GLASS_CSS, unsafe_allow_html=True)
