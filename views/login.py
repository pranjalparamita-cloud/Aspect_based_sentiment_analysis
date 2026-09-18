"""
views/login.py — Login / Sign-Up / Continue-with-Google screen.
Shown when nobody is logged in (see app.py router).

Google has TWO modes:
  REAL MODE (secrets configured) -> Google's own account chooser with the
      user's logged-in Gmails; one click logs them in (see google_auth.py).
  DEMO MODE (no secrets) -> built-in demo accounts so the app works
      out-of-the-box. Follow GOOGLE_SETUP.md to enable real mode.
"""
import io
import re
import secrets

import requests
import streamlit as st
from PIL import Image

from auth import do_login, valid_username, valid_gmail, password_issues
from config import APP_NAME
from database import get_user_by_login, get_user_by_id, create_user, update_user, log_event
from google_auth import is_google_configured, build_auth_url, redirect_to_google


# ---------- real Google login ----------

def login_with_google_profile(profile):
    """Find-or-create the user for a verified Google email, then log in."""
    email = profile["email"].strip().lower()
    user = get_user_by_login(email)
    if user is None:  # first time with this Gmail -> auto-register
        base = re.sub(r"[^A-Za-z0-9_]", "_", email.split("@")[0])[:16] or "user"
        uname, i = base, 1
        while get_user_by_login(uname):
            i += 1
            uname = f"{base}{i}"
        user = create_user(uname, email, secrets.token_urlsafe(16), provider="google")
        log_event(user, "signup", f"Registered via Google ({uname})")
    # grab their Google profile photo once (best effort)
    if not user.get("profile_pic") and profile.get("picture"):
        try:
            raw = requests.get(profile["picture"], timeout=10).content
            img = Image.open(io.BytesIO(raw)).convert("RGB").resize((256, 256))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            import base64
            update_user(user["id"], profile_pic=base64.b64encode(buf.getvalue()).decode())
            user = get_user_by_id(user["id"])
        except Exception:
            pass
    do_login(user, via="google")


# ---------- account chooser screen ----------

def _demo_buttons():
    """Quick-login buttons for the built-in demo accounts."""
    for acc in ("demo@gmail.com", "admin@gmail.com"):
        if st.button(f"👤  Continue as {acc}", key=f"g_{acc}", type="secondary", use_container_width=True):
            user = get_user_by_login(acc)
            if user:
                do_login(user, via="google")


def google_account_chooser():
    """REAL MODE: redirect to Google's chooser. DEMO MODE: local fallback."""
    if is_google_configured():
        st.markdown("#### 🔐 Continue with Google")
        st.caption("Google will show its account chooser with your already-logged-in Gmail accounts — "
                   "pick one and you'll be logged in directly.")
        if st.button("🌐  Continue with Google", use_container_width=True):
            st.session_state["go_google"] = True
            st.rerun()
        with st.expander("🧪 Developer demo accounts (testing only)"):
            _demo_buttons()
        return

    # ---- demo fallback (no secrets configured) ----
    st.warning("⚙️ Real Google login isn't configured yet — **demo mode**. "
               "Follow **GOOGLE_SETUP.md** (free, ~10 min) to enable the real Gmail chooser.")
    st.markdown("#### 🔐 Choose a Google account (demo)")
    _demo_buttons()
    st.markdown("---")
    other = st.text_input("Or use another Gmail", placeholder="you@gmail.com", key="g_other")
    if st.button("Continue with this Gmail", type="secondary", use_container_width=True):
        if not valid_gmail(other or ""):
            st.error("Please enter a valid **@gmail.com** address (Gmail Authenticator).")
        else:
            user = get_user_by_login(other)
            if user is None:
                base = other.split("@")[0].replace(".", "_").replace("-", "_")[:16] or "user"
                uname = base
                suffix = 1
                while get_user_by_login(uname):
                    suffix += 1
                    uname = f"{base}{suffix}"
                user = create_user(uname, other, secrets.token_urlsafe(10), provider="google")
                log_event(user, "signup", "Auto-registered via Google (demo)")
            do_login(user, via="google")


def auth_page():
    """Full login / signup screen with glass card layout."""
    # pending redirect to Google (set by the chooser button)?
    if st.session_state.pop("go_google", False):
        redirect_to_google(build_auth_url())  # ends with st.stop()

    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        st.markdown(f"""
        <div class="glass auth-card">
          <div class="brand-mini">💜 {APP_NAME}</div>
          <div class="gradient-title" style="font-size:2.1rem;">Welcome to Aspect Sentiment Analytics</div>
          <div class="subtitle">Real-time granular sentiment analysis, categorized by feature aspects.</div>
          <div class="divider-line"></div>
        """, unsafe_allow_html=True)

        err = st.session_state.pop("oauth_error", None)
        if err:
            st.error(f"🔐 {err}")

        if st.session_state.get("show_google"):
            if st.button("← Back to email login", type="secondary"):
                st.session_state.show_google = False
                st.rerun()
            google_account_chooser()
            st.markdown("</div>", unsafe_allow_html=True)
            return

        mode = st.radio("Account", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")

        if mode == "Login":
            st.markdown("**Login to your account**")
            login = st.text_input("Username or Gmail", placeholder="demo or demo@gmail.com")
            pwd = st.text_input("Password", type="password", placeholder="••••••••")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔓  Login", use_container_width=True):
                    if not login or not pwd:
                        st.error("Enter username/gmail and password.")
                    else:
                        from auth import verify_password
                        user = get_user_by_login(login)
                        if user and verify_password(pwd, user["password_hash"], user["salt"]):
                            do_login(user, via="email")
                        else:
                            st.error("Invalid credentials. Try demo / Demo@123.")
            with col_b:
                if st.button("🌐  Continue with Google", type="secondary", use_container_width=True):
                    st.session_state.show_google = True
                    st.rerun()
        else:
            st.markdown("**Create a new account**")
            username = st.text_input("Username", placeholder="e.g. sneha_21  (3–20 chars, letters/numbers/_)")
            gmail = st.text_input("Gmail", placeholder="you@gmail.com")
            pwd = st.text_input("Password", type="password", placeholder="Min 6 chars, letter + number")
            pwd2 = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            st.caption("🔒 Gmail Authenticator: only **@gmail.com** addresses are accepted.")
            if st.button("✨  Sign Up", use_container_width=True):
                if not valid_username(username or ""):
                    st.error("Username must be 3–20 chars: letters, numbers, underscore.")
                elif not valid_gmail(gmail or ""):
                    st.error("Only valid **@gmail.com** addresses allowed.")
                elif (issues := password_issues(pwd or "")):
                    st.error("Password needs " + ", ".join(issues) + ".")
                elif pwd != pwd2:
                    st.error("Passwords do not match.")
                elif get_user_by_login(username):
                    st.error("Username already taken.")
                elif get_user_by_login(gmail):
                    st.error("This Gmail is already registered. Please login.")
                else:
                    user = create_user(username, gmail, pwd)
                    log_event(user, "signup", f"New account created ({username})")
                    st.success("Account created! Logging you in… 🎉")
                    do_login(user, via="email")
            if st.button("🌐  Sign up with Google instead", type="secondary", use_container_width=True):
                st.session_state.show_google = True
                st.rerun()

        st.markdown("""
          <div class="glass-soft" style="margin-top:18px; font-size:0.8rem;">
            <b>Demo accounts</b> &nbsp;•&nbsp; User: <code>demo@gmail.com / Demo@123</code>
            &nbsp;•&nbsp; Admin: <code>admin@gmail.com / Admin@123</code>
          </div>
        </div>""", unsafe_allow_html=True)
