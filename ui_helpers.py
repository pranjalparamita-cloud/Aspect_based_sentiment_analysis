"""
ui_helpers.py — Reusable UI building blocks (HTML snippets).
------------------------------------------------------------
avatar_html()        user profile picture (or initial-letter fallback)
sent_badge()         coloured Positive/Neutral/Negative pill
product_card_html()  product tile used in the analysis grid
header()             gradient page title + subtitle + divider
"""
import streamlit as st

from config import PLATFORM_COLORS, ACCENT
from products import stars_html


def avatar_html(user, size="md"):
    cls = "avatar" if size == "md" else "avatar-sm"
    pic = (user or {}).get("profile_pic", "")
    name = (user or {}).get("username", "?")
    if pic:
        return f'<img class="{cls}" src="data:image/png;base64,{pic}"/>'
    return f'<div class="{cls} avatar-fallback">{name[:1].upper()}</div>'


def sent_badge(s):
    return f'<span class="sent-{s[:3]}">{s.capitalize()}</span>'


def product_card_html(p):
    color = PLATFORM_COLORS.get(p["platform"], ACCENT)
    off = round((1 - p["price"] / p["mrp"]) * 100)
    return f"""
    <div class="glass-soft" style="padding:14px; height:100%;">
      <img class="product-img" src="{p['img']}"
           onerror="this.onerror=null;this.src='https://placehold.co/600x400?text={p['brand']}'"/>
      <div style="margin-top:10px;">
        <span class="badge" style="background:{color};">{p['platform']}</span>
        <span class="badge" style="background:#7c3aed;">{p['category']}</span>
      </div>
      <div class="product-name">{p['name']}</div>
      <div class="stars">{stars_html(p['rating'])} <span style="color:#6d6890;">{p['rating']}</span></div>
      <div class="price-row"><span class="price-now">₹{p['price']:,}</span>
        <span class="price-was">₹{p['mrp']:,}</span>
        <span style="color:#047857;font-weight:700;font-size:0.78rem;"> {off}% off</span></div>
    </div>"""


def header(title, subtitle):
    st.markdown(f'<div class="gradient-title">{title}</div><div class="subtitle">{subtitle}</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
