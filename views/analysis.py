"""
views/analysis.py — Product search grid + one-click NLP dashboard.
------------------------------------------------------------------
Sections:
1. Search & filters (key-wise prefix search from products.py)
2. Product grid with images (cards from ui_helpers.py)
3. Selected-product panel + "Analyse The Reviews" button
4. Dashboard: KPIs + Sunburst/Bar/Radar/Donut/Price charts + reviews
"""
import streamlit as st
import pandas as pd

from charts import fig_donut, fig_bar, fig_sunburst, fig_radar, fig_price
from config import POS_COLOR, NEG_COLOR, PLATFORM_COLORS, ACCENT
from database import log_event, save_analysis
from nlp_engine import analyze_reviews, price_trend
from products import CATEGORIES, PLATFORMS, get_product, search_products, stars_html
from reviews import get_product_reviews
from ui_helpers import header, product_card_html, sent_badge


def page_analysis():
    user = st.session_state.user
    header("Aspect Sentiment Analytics",
           "Real-time granular sentiment analysis categorized by feature aspects.")

    # ---------- 1. Search & filters ----------
    with st.container():
        s1, s2, s3, s4 = st.columns([2.4, 1.2, 1.2, 1.3])
        with s1:
            query = st.text_input("🔎 Search products",
                                  value=st.session_state.get("query", ""),
                                  placeholder="Type key-wise:  r → re → red → redmi …  (press Enter)",
                                  key="query")
        with s2:
            platforms = st.multiselect("Platform", PLATFORMS, default=st.session_state.get("f_platforms", []))
            st.session_state.f_platforms = platforms
        with s3:
            category = st.selectbox("Category", CATEGORIES,
                                    index=CATEGORIES.index(st.session_state.get("f_category", "All")))
            st.session_state.f_category = category
        with s4:
            sort_by = st.selectbox("Sort by", ["Relevance", "Price: Low to High", "Price: High to Low", "Rating: High to Low"])

    results = search_products(query, platforms, category, sort_by)

    # log searches only when the query actually changes (avoid spam)
    if query != st.session_state.get("last_search", ""):
        st.session_state.last_search = query
        if query:
            log_event(user, "search", f"Searched '{query}' → {len(results)} results")

    st.markdown(f"**{len(results)} products found**" +
                (f" for prefix **“{query}”**" if query else " — scroll & pick any product"))
    if not results:
        st.warning("No products match. Try a shorter prefix (e.g. just “r”).")
        return

    # ---------- 2. Product grid ----------
    if "visible_count" not in st.session_state:
        st.session_state.visible_count = 9
    visible = results[:st.session_state.visible_count]
    for i in range(0, len(visible), 3):
        cols = st.columns(3)
        for j, p in enumerate(visible[i:i + 3]):
            with cols[j]:
                st.markdown(product_card_html(p), unsafe_allow_html=True)
                if st.button(f"Select  •  {p['id']}", key=f"sel_{p['id']}", type="secondary",
                             use_container_width=True):
                    st.session_state.selected_pid = p["id"]
                    st.session_state.analysis = None
                    log_event(user, "view_product", f"Selected {p['name']} ({p['platform']})")
                    st.rerun()
    if st.session_state.visible_count < len(results):
        if st.button("⬇️  Load more products", type="secondary"):
            st.session_state.visible_count += 9
            st.rerun()

    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

    # ---------- 3. Selected product + Analyse ----------
    pid = st.session_state.get("selected_pid")
    if not pid:
        st.info("👆 Select any product above to preview it here, then hit **Analyse The Reviews**.")
        return
    product = get_product(pid)
    if not product:
        return

    d1, d2 = st.columns([1, 1.4])
    with d1:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <img src="{product['img']}" style="width:100%;height:260px;object-fit:cover;border-radius:14px;"
               onerror="this.onerror=null;this.src='https://placehold.co/600x400?text={product['brand']}'"/>
        </div>""", unsafe_allow_html=True)
    with d2:
        color = PLATFORM_COLORS.get(product["platform"], ACCENT)
        off = round((1 - product["price"] / product["mrp"]) * 100)
        st.markdown(f"""<div class="glass">
          <span class="badge" style="background:{color};">{product['platform']}</span>
          <span class="badge" style="background:#7c3aed;">{product['category']}</span>
          <h2 style="margin:10px 0 4px;">{product['name']}</h2>
          <div class="small-note">{product['brand']} • {product['desc']}</div>
          <div style="margin:10px 0;" class="stars">{stars_html(product['rating'])}
            <span style="color:#6d6890;"> {product['rating']} / 5</span></div>
          <div><span class="price-now" style="font-size:1.4rem;">₹{product['price']:,}</span>
            <span class="price-was">₹{product['mrp']:,}</span>
            <span style="color:#047857;font-weight:700;"> {off}% off</span></div>
        </div>""", unsafe_allow_html=True)
        if st.button("💜  Analyse The Reviews", use_container_width=True):
            with st.spinner("Running NLP aspect-sentiment analysis…"):
                reviews = get_product_reviews(product, n=60)
                result = analyze_reviews(reviews)
                st.session_state.analysis = result
                save_analysis(user["id"], product, result["total"],
                              result["overall"]["positive"], result["overall"]["neutral"],
                              result["overall"]["negative"], result["verdict"])
                log_event(user, "analyse",
                          f"Analysed {product['name']} → {result['verdict']} "
                          f"(+{result['overall']['positive']}/~{result['overall']['neutral']}/-{result['overall']['negative']})")
            st.rerun()

    # ---------- 4. Dashboard ----------
    result = st.session_state.get("analysis")
    if not result:
        return

    st.markdown("### 📊 Analysis Dashboard")
    ov = result["overall"]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <div class="kpi-label">TOTAL REVIEWS ANALYZED</div>
          <div class="kpi-value">{result['total']}</div>
          <div class="kpi-sub">{product['platform']} • {product['brand']}</div></div>""",
                    unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <div class="kpi-label">OVERALL VERDICT</div>
          <div style="font-size:1.7rem;font-weight:800;color:#6d28d9;">{result['verdict']}</div>
          <div class="kpi-sub">{result['pos_pct']:.1f}% positive mentions</div></div>""",
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <div class="kpi-label">POSITIVE / NEGATIVE</div>
          <div style="font-size:1.7rem;font-weight:800;">
            <span style="color:{POS_COLOR};">{ov['positive']}</span>
            <span style="color:#b9b3d9;">/</span>
            <span style="color:{NEG_COLOR};">{ov['negative']}</span></div>
          <div class="kpi-sub">{ov['neutral']} neutral reviews</div></div>""",
                    unsafe_allow_html=True)
    with k4:
        best = max(result["aspects"], key=lambda a: result["aspects"][a]["positive"] - result["aspects"][a]["negative"])
        worst = min(result["aspects"], key=lambda a: result["aspects"][a]["positive"] - result["aspects"][a]["negative"])
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <div class="kpi-label">TOP / CRITICAL ASPECT</div>
          <div style="font-size:1.25rem;font-weight:800;color:#047857;">👍 {best}</div>
          <div style="font-size:1.05rem;font-weight:700;color:#be123c;">⚠️ {worst}</div></div>""",
                    unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.plotly_chart(fig_donut(ov), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.plotly_chart(fig_bar(result["aspects"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.plotly_chart(fig_sunburst(result["aspects"], result["total"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.plotly_chart(fig_radar(result["aspects"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass">', unsafe_allow_html=True)
    labels, prices = price_trend(product)
    st.plotly_chart(fig_price(labels, prices, product), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Aspect detail table
    st.markdown("#### 🧩 Aspect detail")
    rows = []
    for a, d in result["aspects"].items():
        t = max(1, d["positive"] + d["neutral"] + d["negative"])
        rows.append({"Aspect": a, "👍 Positive": d["positive"], "😐 Neutral": d["neutral"],
                     "👎 Negative": d["negative"], "Positivity %": round(d["positive"] / t * 100, 1)})
    st.dataframe(pd.DataFrame(rows).sort_values("Positivity %", ascending=False),
                 use_container_width=True, hide_index=True)

    # Sample reviews
    st.markdown("#### 💬 Sample analyzed reviews")
    filt = st.radio("Filter", ["All", "Positive", "Neutral", "Negative"], horizontal=True, key="rev_filter")
    shown = 0
    for r in result["rows"]:
        if filt != "All" and r["sentiment"] != filt.lower():
            continue
        tags = " ".join(f'<span class="aspect-tag">{a}</span>' for a in r["aspects"])
        st.markdown(f"""<div class="glass-soft" style="margin-bottom:10px;">
          <b>{r['author']}</b> <span class="small-note">• {r['date']} • {'✅ Verified' if r['verified'] else 'Unverified'} • {'★'*r['rating']+'☆'*(5-r['rating'])}</span>
          &nbsp; {sent_badge(r['sentiment'])}<br/>
          <div style="margin:6px 0;">{r['text']}</div>{tags}</div>""", unsafe_allow_html=True)
        shown += 1
        if shown >= 8:
            break
