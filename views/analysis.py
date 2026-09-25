"""
views/analysis.py — Built-in Product Review Intelligence workspace.
------------------------------------------------------------------
The upload-first workflow has been replaced with a professional catalog:
- 5,000 searchable product-style listings across broad shopping categories
- autocomplete-style suggestions as the user searches
- 10 mixed-sentiment, clearly labelled demo reviews per product
- aspect-based NLP dashboard and a complete review feed
"""
import html

import pandas as pd
import streamlit as st

from catalog import (catalog_categories, catalog_match_count, catalog_summary,
                     get_catalog_product, get_catalog_reviews, search_catalog)
from charts import (fig_donut, fig_bar, fig_sunburst, fig_radar,
                    fig_timeline, fig_rolling, fig_ratings)
from config import POS_COLOR, NEG_COLOR
from database import log_event, save_analysis
from nlp_engine import analyze_reviews
from product_visuals import catalog_image_html
from ui_helpers import catalog_card_html, header, sent_badge, stars_text

CATALOG_NAME = "Built-in Product Catalog · generated demo data"


def _catalog_stats():
    stats = catalog_summary()
    a, b, c = st.columns(3)
    for column, label, value, caption in (
        (a, "PRODUCT LISTINGS", f"{stats['products']:,}", "across everyday shopping categories"),
        (b, "MIXED REVIEW SAMPLES", f"{stats['reviews']:,}", "positive, neutral and negative examples"),
        (c, "SHOPPING CATEGORIES", str(stats['categories']), "electronics to automotive and lifestyle"),
    ):
        with column:
            st.markdown(f"""<div class="glass-soft" style="text-align:center; padding:15px;">
              <div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:1.8rem;">{value}</div>
              <div class="kpi-sub">{caption}</div></div>""", unsafe_allow_html=True)


def _choose_product(product, user):
    st.session_state["catalog_product_id"] = product["id"]
    st.session_state.pop("catalog_analysis", None)
    log_event(user, "catalog_product_view", f"Opened {product['sku']} · {product['title']}")
    st.rerun()


def _catalog_search(user):
    """Autocomplete search plus paginated access to all 5,000 catalog items."""
    st.markdown("### 🔎 Browse every product")
    left, right = st.columns([2.25, 1])
    with left:
        query = st.text_input(
            "Product autocomplete",
            placeholder="Type a product, brand, category or SKU — e.g. samsung, brake pad, air fryer…",
            key="catalog_query",
            help="Suggestions search product titles, brands, categories and catalog SKUs.",
        )
    with right:
        category = st.selectbox("Category", ["All categories"] + catalog_categories(), key="catalog_category")

    # Returning to page one after a search/filter change prevents blank pages.
    signature = (query.strip().lower(), category)
    if signature != st.session_state.get("catalog_filter_signature"):
        st.session_state["catalog_filter_signature"] = signature
        st.session_state["catalog_page"] = 0
    total = catalog_match_count(query, category)
    page_size = 24
    pages = max(1, (total + page_size - 1) // page_size)
    page_index = min(st.session_state.get("catalog_page", 0), pages - 1)
    st.session_state["catalog_page"] = page_index

    header_text = "Autocomplete search results" if query.strip() else "All catalog products"
    st.markdown(f"**{header_text}** <span class='small-note'>• {total:,} matching products • "
                f"browse 24 products per page</span>", unsafe_allow_html=True)
    if not total:
        st.warning("No products matched that search. Try a shorter term, a brand, or choose All categories.")
        return

    matches = search_catalog(query, category, limit=page_size, offset=page_index * page_size)
    for start in range(0, len(matches), 4):
        columns = st.columns(4)
        for index, product in enumerate(matches[start:start + 4]):
            with columns[index]:
                st.markdown(catalog_card_html(product), unsafe_allow_html=True)
                selected = st.session_state.get("catalog_product_id") == product["id"]
                if st.button("✅ Viewing" if selected else "View product & reviews",
                             key=f"catalog_pick_{product['id']}",
                             type="secondary", use_container_width=True):
                    _choose_product(product, user)

    nav_left, nav_page, nav_right = st.columns([1, 1.35, 1])
    with nav_left:
        if st.button("← Previous", disabled=page_index == 0, use_container_width=True, key="catalog_prev"):
            st.session_state["catalog_page"] = page_index - 1
            st.rerun()
    with nav_page:
        st.markdown(f"<div class='small-note' style='text-align:center; padding-top:10px;'>"
                    f"Page <b>{page_index + 1}</b> of <b>{pages}</b> • {total:,} products</div>",
                    unsafe_allow_html=True)
    with nav_right:
        if st.button("Next →", disabled=page_index >= pages - 1, use_container_width=True, key="catalog_next"):
            st.session_state["catalog_page"] = page_index + 1
            st.rerun()


def _review_feed(reviews, analysed_rows=None):
    """Show every review below the product, as requested—not only a sample."""
    sentiment_by_index = {}
    if analysed_rows:
        sentiment_by_index = {index: row.get("sentiment", "neutral") for index, row in enumerate(analysed_rows)}

    st.markdown(f"### 💬 All catalog review samples ({len(reviews)})")
    st.caption("These are varied generated demonstration samples for this catalog item. "
               "The sentiment badge shows the NLP result after analysis; otherwise it shows the seeded review mix.")
    for index, review in enumerate(reviews):
        sentiment = sentiment_by_index.get(index, review.get("seed_sentiment", "neutral"))
        label = "NLP result" if analysed_rows else "Demo mix"
        review_text = html.escape(str(review["text"]))
        author = html.escape(str(review["author"]))
        date = html.escape(str(review["date"]))
        stars = stars_text(review.get("rating"))
        st.markdown(f"""<div class="review-feed">
          <b>{author}</b> <span class="small-note">• {date} • <span class="stars">{stars}</span></span>
          &nbsp;{sent_badge(sentiment)} <span class="small-note">{label}</span>
          <div class="review-feed-text">{review_text}</div>
        </div>""", unsafe_allow_html=True)


def _dashboard(result, product):
    title = html.escape(product["title"])
    st.markdown(f"### 📊 Review intelligence — {title}", unsafe_allow_html=True)
    overall = result["overall"]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="glass" style="text-align:center;"><div class="kpi-label">REVIEWS ANALYSED</div>
          <div class="kpi-value">{result['total']}</div><div class="kpi-sub">full product review feed</div></div>""",
                    unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="glass" style="text-align:center;"><div class="kpi-label">OVERALL VERDICT</div>
          <div style="font-size:1.4rem;font-weight:800;color:#6d28d9;">{result['verdict']}</div>
          <div class="kpi-sub">{result['pos_pct']:.1f}% positive reviews</div></div>""",
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="glass" style="text-align:center;"><div class="kpi-label">POSITIVE / NEGATIVE</div>
          <div style="font-size:1.7rem;font-weight:800;"><span style="color:{POS_COLOR};">{overall['positive']}</span>
          <span style="color:#b9b3d9;"> / </span><span style="color:{NEG_COLOR};">{overall['negative']}</span></div>
          <div class="kpi-sub">{overall['neutral']} neutral reviews</div></div>""", unsafe_allow_html=True)
    with k4:
        best = max(result["aspects"], key=lambda aspect: result["aspects"][aspect]["positive"] - result["aspects"][aspect]["negative"])
        concern = min(result["aspects"], key=lambda aspect: result["aspects"][aspect]["positive"] - result["aspects"][aspect]["negative"])
        st.markdown(f"""<div class="glass" style="text-align:center;"><div class="kpi-label">TOP / WATCH ASPECT</div>
          <div style="font-size:1.1rem;font-weight:800;color:#047857;">👍 {best}</div>
          <div style="font-size:1rem;font-weight:700;color:#be123c;">⚠️ {concern}</div></div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_donut(overall), use_container_width=True)
    with c2:
        st.plotly_chart(fig_bar(result["aspects"]), use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(fig_sunburst(result["aspects"], result["total"]), use_container_width=True)
    with c4:
        st.plotly_chart(fig_radar(result["aspects"]), use_container_width=True)

    dates = [row.get("date", "") for row in result["rows"]]
    sentiments = [row["sentiment"] for row in result["rows"]]
    trend = fig_timeline(dates, sentiments) if any(dates) else None
    st.plotly_chart(trend if trend else fig_rolling(sentiments), use_container_width=True)
    ratings = [row["rating"] for row in result["rows"] if row.get("rating") is not None]
    if ratings:
        st.plotly_chart(fig_ratings(ratings), use_container_width=True)

    detail = []
    for aspect, counts in result["aspects"].items():
        total = max(1, counts["positive"] + counts["neutral"] + counts["negative"])
        detail.append({"Aspect": aspect, "👍 Positive": counts["positive"], "😐 Neutral": counts["neutral"],
                       "👎 Negative": counts["negative"],
                       "Positivity %": round(counts["positive"] / total * 100, 1)})
    st.markdown("#### 🧩 Aspect detail")
    st.dataframe(pd.DataFrame(detail).sort_values("Positivity %", ascending=False),
                 use_container_width=True, hide_index=True)


def _product_workspace(user, product_id):
    product = get_catalog_product(product_id)
    if not product:
        st.session_state.pop("catalog_product_id", None)
        return
    reviews = get_catalog_reviews(product_id)
    average = sum(review["rating"] for review in reviews) / max(1, len(reviews))
    title = html.escape(product["title"])

    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="catalog-hero"><div class="catalog-card-top">
      <span class="catalog-category">{html.escape(product['category'])}</span>
      <span class="catalog-sku">Catalog SKU: {html.escape(product['sku'])}</span></div>
      <div class="gradient-title" style="font-size:1.65rem; margin-top:10px;">{title}</div>
      <div class="subtitle"><b>{html.escape(product['brand'])}</b> &nbsp;•&nbsp; {html.escape(product['product_type'])}
      &nbsp;•&nbsp; {len(reviews)} mixed review samples</div></div>""", unsafe_allow_html=True)
    st.markdown("<div class='demo-note'><b>Demo data notice:</b> This product-style listing and its review text are "
                "generated for application demonstration. They are not claimed to be verified customer reviews.</div>",
                unsafe_allow_html=True)

    st.markdown("#### 🖼️ Product gallery")
    st.caption("Generated studio-style visual previews: front, angled and detail views. "
               "They are visual representations for this demo catalog, not retailer photographs of a specific SKU.")
    for gallery_col, view, label in zip(st.columns(3), ("front", "angle", "detail"),
                                        ("Front view", "Angled view", "Detail view")):
        with gallery_col:
            st.markdown(catalog_image_html(product, view, "catalog-gallery-image"), unsafe_allow_html=True)
            st.markdown(f"<div class='gallery-label'>{label}</div>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Review samples", len(reviews))
    m2.metric("Average rating", f"{average:.1f} / 5")
    m3.metric("Review balance", "5 positive · 3 neutral · 2 negative")

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("#### Ready for aspect sentiment analysis")
        st.caption("The NLP engine evaluates every catalog review for quality, price, delivery, packaging, service, features, durability and design.")
    with right:
        analyse = st.button("💜 Analyse all product reviews", type="primary", use_container_width=True,
                            key=f"analyse_catalog_{product_id}")
    if analyse:
        with st.spinner("Analysing the full product review feed…"):
            result = analyze_reviews(reviews)
            st.session_state["catalog_analysis"] = {"product_id": product_id, "result": result}
            save_analysis(user["id"], f"catalog:{product_id}", product["title"], CATALOG_NAME,
                          result["total"], result["overall"]["positive"], result["overall"]["neutral"],
                          result["overall"]["negative"], result["verdict"])
            log_event(user, "catalog_analyse",
                      f"Analysed {product['sku']} · {product['title']} → {result['verdict']}")
        st.rerun()

    stored = st.session_state.get("catalog_analysis", {})
    result = stored.get("result") if stored.get("product_id") == product_id else None
    if result:
        _dashboard(result, product)
    _review_feed(reviews, result["rows"] if result else None)


def page_analysis():
    """Main route retained for app.py compatibility; it is now catalog-first."""
    user = st.session_state.user
    header("Product Review Intelligence", "Search a built-in catalog, read the full review feed, and analyse product sentiment.")
    _catalog_stats()
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='demo-note'><b>Catalog transparency:</b> 5,000 product-style listings and 50,000 "
                "mixed-sentiment review samples are bundled for a fast, professional demo experience. "
                "They are generated data, not scraped customer reviews.</div>", unsafe_allow_html=True)
    _catalog_search(user)
    selected = st.session_state.get("catalog_product_id")
    if selected:
        _product_workspace(user, selected)
