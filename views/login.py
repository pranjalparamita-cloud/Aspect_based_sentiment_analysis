"""
views/login.py — Login / Sign-Up / Continue-with-Google screen.
Shown when nobody is logged in (see app.py router).
"""
import secrets

import streamlit as st

from auth import do_login, valid_username, valid_gmail, password_issues
from config import APP_NAME
from database import get_user_by_login, create_user, log_event


def google_account_chooser():
    """Demo Google SSO: pick an account to continue instantly."""
    st.markdown("#### 🔐 Choose a Google account")
    st.caption("Demo Google SSO — pick an account to continue instantly. "
               "(For production, connect real Google OAuth in `secrets.toml`; logic is isolated in one function.)")
    demo_accounts = ["demo@gmail.com", "admin@gmail.com"]
    for acc in demo_accounts:
        if st.button(f"👤  Continue as {acc}", key=f"g_{acc}", type="secondary", use_container_width=True):
            user = get_user_by_login(acc)
            if user:
                do_login(user, via="google")
    st.markdown("---")
    other = st.text_input("Or use another Gmail", placeholder="you@gmail.com", key="g_other")
    if st.button("Continue with this Gmail", type="secondary", use_container_width=True):
        if not valid_gmail(other or ""):
            st.error("Please enter a valid **@gmail.com** address (Gmail Authenticator).")
        else:
            user = get_user_by_login(other)
            if user is None:  # auto-register Google users
                base = other.split("@")[0].replace(".", "_").replace("-", "_")[:16] or "user"
                uname = base
                suffix = 1
                while get_user_by_login(uname):
                    suffix += 1
                    uname = f"{base}{suffix}"
                user = create_user(uname, other, secrets.token_urlsafe(10), provider="google")
                log_event(user, "signup", "Auto-registered via Google")
            do_login(user, via="google")


def auth_page():
    """Full login / signup screen with glass card layout."""
    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        st.markdown(f"""
        <div class="glass auth-card">
          <div class="brand-mini">💜 {APP_NAME}</div>
          <div class="gradient-title" style="font-size:2.1rem;">Welcome to Aspect Sentiment Analytics</div>
          <div class="subtitle">Real-time granular sentiment analysis, categorized by feature aspects.</div>
          <div class="divider-line"></div>
        """, unsafe_allow_html=True)

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
