"""
views/profile.py — My Profile & User Data screen.
-------------------------------------------------
Edit username / phone / bio, change profile photo (stored as base64
in SQLite) and change password. Shows personal stats.
"""
import base64
import io

import streamlit as st
from PIL import Image

from auth import valid_username, password_issues, verify_password, hash_password
from database import get_user_by_id, get_user_by_login, update_user, log_event, fetch_df
from ui_helpers import header, avatar_html


def page_profile():
    user = st.session_state.user
    header("My Profile & User Data", "Manage your identity — everything is saved securely in the database.")
    left, right = st.columns([1, 1.8])

    with left:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          {avatar_html(user, 'md')}
          <h3 style="margin:10px 0 0;">{user['username']}</h3>
          <div class="small-note">{user['email']}<br/>via {user['provider'].capitalize()} • since {user['created_at'][:10]}</div>
        </div>""", unsafe_allow_html=True)
        up = st.file_uploader("📷 Change profile picture", type=["png", "jpg", "jpeg", "webp"])
        if up is not None:
            try:
                img = Image.open(up).convert("RGB").resize((256, 256))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                update_user(user["id"], profile_pic=b64)
                st.session_state.user = get_user_by_id(user["id"])
                log_event(st.session_state.user, "update_profile", "Changed profile picture")
                st.success("Profile picture updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not process image: {e}")
        if user.get("profile_pic"):
            if st.button("Remove photo", type="secondary", use_container_width=True):
                update_user(user["id"], profile_pic="")
                st.session_state.user = get_user_by_id(user["id"])
                log_event(st.session_state.user, "update_profile", "Removed profile picture")
                st.rerun()

        hist = fetch_df("SELECT COUNT(*) c FROM analysis_history WHERE user_id=?", (user["id"],))
        logins = fetch_df("SELECT COUNT(*) c FROM activity_logs WHERE user_id=? AND event_type IN ('login','google_login')",
                          (user["id"],))
        st.markdown(f"""<div class="glass" style="margin-top:14px; text-align:center;">
          <div class="kpi-label">MY STATS</div>
          <div style="font-size:1.4rem;font-weight:800;color:#6d28d9;">
            {int(hist['c'][0]) if len(hist) else 0} analyses • {int(logins['c'][0]) if len(logins) else 0} logins</div>
        </div>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("##### ✏️ Edit profile")
        new_username = st.text_input("Username", value=user["username"])
        new_phone = st.text_input("Phone (optional)", value=user.get("phone") or "", placeholder="+91 …")
        new_bio = st.text_area("Bio (optional)", value=user.get("bio") or "", placeholder="Tell us about yourself…")
        if st.button("💾 Save changes", use_container_width=True):
            if not valid_username(new_username):
                st.error("Username must be 3–20 chars: letters, numbers, underscore.")
            else:
                other = get_user_by_login(new_username)
                if other and other["id"] != user["id"]:
                    st.error("That username is already taken.")
                else:
                    update_user(user["id"], username=new_username.strip(), phone=new_phone.strip(), bio=new_bio.strip())
                    st.session_state.user = get_user_by_id(user["id"])
                    log_event(st.session_state.user, "update_profile", f"Updated profile (username={new_username})")
                    st.success("Profile saved!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown("##### 🔑 Change password")
        if user["provider"] == "google":
            st.info("You signed in with Google — set an email password below to also enable email login.")
            old = None
        else:
            old = st.text_input("Current password", type="password")
        new1 = st.text_input("New password", type="password")
        new2 = st.text_input("Confirm new password", type="password")
        if st.button("🔐 Update password", use_container_width=True):
            if old is not None and not verify_password(old or "", user["password_hash"], user["salt"]):
                st.error("Current password is incorrect.")
            elif (issues := password_issues(new1 or "")):
                st.error("New password needs " + ", ".join(issues) + ".")
            elif new1 != new2:
                st.error("New passwords do not match.")
            else:
                phash, salt = hash_password(new1)
                update_user(user["id"], password_hash=phash, salt=salt)
                st.session_state.user = get_user_by_id(user["id"])
                log_event(st.session_state.user, "change_password", "Changed password")
                st.success("Password updated!")
        st.markdown("</div>", unsafe_allow_html=True)
