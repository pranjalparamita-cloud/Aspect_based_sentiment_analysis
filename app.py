"""
AspectLens — Aspect-Based Sentiment Analytics  (main entry point)
=================================================================
Run / deploy THIS file:   streamlit run app.py

This file stays THIN on purpose — it only:
  1. sets page config + theme      (styles.py)
  2. initialises the database      (database.py)
  3. draws the sidebar + routing   (views/*.py)

All real logic lives in the modules below:
  config.py      constants (colours, paths, app name)
  database.py    SQLite: users, activity logs, analysis history
  auth.py        passwords, Gmail validation, login sessions
  google_auth.py real "Continue with Google" (OAuth 2.0)
  datasets.py    flexible uploads (CSV/Excel/JSON) + smart schema detection
  nlp_engine.py  aspect-sentiment NLP
  charts.py      Plotly dashboard figures
  ui_helpers.py  reusable cards / avatars / badges
  views/         one file per screen (login, analysis, profile, history, admin)
"""
import streamlit as st
from datetime import datetime

from config import APP_NAME
from styles import apply_custom_css
from database import init_db, log_event
from ui_helpers import avatar_html
from views import login, analysis, profile, history, admin

# ---------- page setup ----------
st.set_page_config(
    page_title="AspectLens • Aspect Sentiment Analytics",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


# ---------- sidebar + navigation ----------
def sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex; gap:12px; align-items:center; margin-bottom:6px;">
          {avatar_html(user, 'sm')}
          <div><div style="font-weight:800;">{user['username']}</div>
          <div class="small-note">{user['email']}</div></div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="brand-mini">💜 {APP_NAME}</div>', unsafe_allow_html=True)
        st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
        options = ["🔍 Analysis", "👤 My Profile", "🕘 My History"]
        if user.get("is_admin"):
            options.append("🛡️ Admin Panel")
        page = st.radio("Navigate", options, label_visibility="collapsed",
                        index=options.index(st.session_state.get("page", "🔍 Analysis"))
                        if st.session_state.get("page") in options else 0)
        if page != st.session_state.get("page"):
            st.session_state.page = page
            log_event(user, "navigate", f"Opened {page}")
            st.rerun()
        st.markdown("---")
        login_t = st.session_state.get("login_time")
        if login_t:
            mins = int((datetime.now() - login_t).total_seconds() // 60)
            st.caption(f"🟢 Session live • {mins} min • id {st.session_state.get('session_id', '')}")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            dur = ""
            if login_t:
                delta = datetime.now() - login_t
                dur = f"Session duration {str(delta).split('.')[0]}"
            log_event(user, "logout", f"User left the website. {dur}")
            for k in ["user", "page", "selected_pid", "analysis", "visible_count",
                      "query", "last_search", "show_google", "login_time", "session_id"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("---")
        with st.expander("ℹ️ How it works"):
            st.caption("1️⃣ Upload a review dataset — any number of columns is accepted.\n\n"
                       "2️⃣ Confirm the smart suggestions for review text, item, rating, date and author.\n\n"
                       "3️⃣ Search/select an item (if available) → **Analyse The Reviews**.\n\n"
                       "4️⃣ Pure-Python NLP tags sentences by aspect (Quality, Price, Delivery, "
                       "Packaging, Service, Features, Durability, Design) and scores sentiment.\n\n"
                       "5️⃣ Results render as Sunburst, Bar, Radar, Donut and timeline charts.")


# ---------- router ----------
def main():
    init_db()
    if "user" not in st.session_state or st.session_state.user is None:
        login.auth_page()
        st.markdown("<div class='small-note' style='text-align:center; margin-top:26px;'>"
                    "AspectLens • 100% free & open — Streamlit + SQLite + Plotly • No paid APIs</div>",
                    unsafe_allow_html=True)
        return
    sidebar()
    page = st.session_state.get("page", "🔍 Analysis")
    if page == "🔍 Analysis":
        analysis.page_analysis()
    elif page == "👤 My Profile":
        profile.page_profile()
    elif page == "🕘 My History":
        history.page_history()
    elif page == "🛡️ Admin Panel":
        admin.page_admin()


if __name__ == "__main__":
    main()
