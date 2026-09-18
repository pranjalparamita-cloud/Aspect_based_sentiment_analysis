"""
views/analysis.py — Dataset-driven analysis.
--------------------------------------------
1. My Datasets: upload 1+ CSV/XLSX files (or load the demo dataset)
2. Column mapping: tell the app which column holds reviews / items / ratings / dates
3. Search: key-wise item search + keyword + rating filters
4. Analyse: NLP dashboard (Sunburst / Bar / Radar / Donut / Trend line)
"""
import streamlit as st
import pandas as pd

from charts import (fig_donut, fig_bar, fig_sunburst, fig_radar,
                    fig_timeline, fig_rolling, fig_ratings)
from config import POS_COLOR, NEG_COLOR
from database import log_event, save_analysis
from datasets import (read_upload, infer_review_schema, rating_series, reviews_from_df,
                      search_items, save_dataset, list_datasets, load_dataset,
                      delete_dataset, load_sample)
from nlp_engine import analyze_reviews
from ui_helpers import header, item_card_html, sent_badge


# ---------- section 1: datasets ----------

def _dataset_section(user):
    st.markdown("### 📁 Step 1 — My Datasets")
    up_col, demo_col = st.columns([3, 1])
    with up_col:
        files = st.file_uploader(
            "Upload review datasets (CSV, Excel or JSON — one or many)",
            type=["csv", "xlsx", "xls", "json", "jsonl", "ndjson"],
            accept_multiple_files=True,
            help="Any number of columns is accepted. AspectLens keeps them all and automatically "
                 "looks for review text, product/item, rating, date and reviewer fields.",
        )
    with demo_col:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        want_demo = st.button("✨ Load demo dataset", type="secondary", use_container_width=True)

    if files:
        for f in files:
            if f.name in st.session_state.get("uploaded_names", set()):
                continue
            try:
                df, truncated = read_upload(f)
                if df.empty or len(df.columns) == 0:
                    st.error(f"❌ {f.name}: no readable data found.")
                    continue
                parse_note = df.attrs.get("parse_note")
                name = save_dataset(user["id"], f.name, df)
                st.session_state.setdefault("uploaded_names", set()).add(f.name)
                log_event(user, "upload_dataset", f"Uploaded '{name}' ({len(df)} rows)")
                st.success(f"✅ Saved **{name}** — {len(df)} rows × {len(df.columns)} columns"
                           + (" (truncated to 5000 rows)" if truncated else ""))
                if parse_note:
                    st.info(f"ℹ️ {parse_note}")
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")
        st.rerun()

    if want_demo:
        name, df = load_sample()
        saved = save_dataset(user["id"], name + ".csv", df)
        log_event(user, "upload_dataset", f"Loaded demo dataset as '{saved}'")
        st.success(f"✅ Demo dataset loaded as **{saved}**")
        st.rerun()

    datasets = list_datasets(user["id"])
    if not datasets:
        st.info("👆 Upload any CSV, Excel or JSON review dataset (or load the demo). "
                "It can contain any number of fields and use your own headers — AspectLens inspects "
                "the names and values, then suggests review text and any useful item/rating/date fields.")
        return None, None

    labels = [f"{d['name']}  ({d['row_count']} rows)" for d in datasets]
    ids = [d["id"] for d in datasets]
    prev = st.session_state.get("ds_id")
    sel_label = st.selectbox("Active dataset", labels,
                             index=ids.index(prev) if prev in ids else 0)
    ds_id = ids[labels.index(sel_label)]
    if ds_id != prev:
        for k in ("selected_item", "analysis", "visible_count", "last_search"):
            st.session_state.pop(k, None)
        st.session_state.ds_id = ds_id
        st.rerun()

    ds_name, df = load_dataset(ds_id, user["id"])
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"📄 **{ds_name}** • {len(df)} rows • columns: {', '.join(df.columns)}")
    with c2:
        if st.button("🗑️ Delete dataset", type="secondary", use_container_width=True):
            delete_dataset(ds_id, user["id"])
            log_event(user, "delete_dataset", f"Deleted '{ds_name}'")
            for k in ("ds_id", "selected_item", "analysis", "uploaded_names"):
                st.session_state.pop(k, None)
            st.rerun()
    with st.expander("👀 Preview data (first 10 rows)"):
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
    return ds_id, (ds_name, df)


# ---------- section 2: column mapping ----------

def _mapping_section(df, ds_id):
    st.markdown("### 🗂️ Step 2 — Smart column mapping")
    auto, detection_report = infer_review_schema(df)
    key = f"mapping_{ds_id}"
    if key not in st.session_state:
        st.session_state[key] = auto
    saved = st.session_state[key]
    cols = list(df.columns)

    st.caption(f"✨ Checked **all {len(cols)} columns** using their header names and sample values. "
               "The suggestions below are editable — every original column remains in your dataset.")
    with st.expander("See automatic field detection", expanded=False):
        st.dataframe(pd.DataFrame(detection_report), use_container_width=True, hide_index=True)
        st.caption("A suggested item field enables product-wise search; rating and date fields enable "
                   "their dashboard charts. They are optional — review text is the only required field.")

    def _pick(label, role, required=False):
        options = cols if required else ["(none)"] + cols
        current = saved.get(role)
        index = options.index(current) if current in options else 0
        return st.selectbox(label, options, index=index, key=f"{key}_{role}")

    m1, m2, m3 = st.columns(3)
    with m1:
        text_col = _pick("💬 Review text *", "text", required=True)
    with m2:
        item_col = _pick("📦 Item / Product (optional)", "item")
    with m3:
        rating_col = _pick("⭐ Rating (optional)", "rating")
    m4, m5 = st.columns(2)
    with m4:
        date_col = _pick("📅 Date (optional)", "date")
    with m5:
        author_col = _pick("👤 Reviewer / Author (optional)", "author")

    mapping = {
        "text": text_col,
        "item": None if item_col == "(none)" else item_col,
        "rating": None if rating_col == "(none)" else rating_col,
        "date": None if date_col == "(none)" else date_col,
        "author": None if author_col == "(none)" else author_col,
    }
    if mapping != saved:
        st.session_state[key] = mapping
        st.session_state.pop("analysis", None)
        st.session_state.pop("selected_item", None)
    return mapping


# ---------- section 3: search ----------

def _search_section(df, mapping, user):
    st.markdown("### 🔎 Step 3 — Search your data")
    item_col, text_col, rating_col = mapping["item"], mapping["text"], mapping["rating"]

    q1, q2 = st.columns([1.3, 1])
    with q1:
        query = st.text_input("Search items" if item_col else "Search",
                              value=st.session_state.get("query", ""),
                              placeholder="Type key-wise:  a → au → aur → aura …  (press Enter)",
                              key="query") if item_col else ""
    with q2:
        keyword = st.text_input("🔤 Keyword in reviews (optional)", placeholder="e.g. battery, delivery, price…",
                                key="keyword")

    rating_vals = []
    if rating_col and rating_col in df.columns:
        # Supports 4, 4.0 and strings such as "4 out of 5 stars".
        nums = rating_series(df[rating_col]).dropna()
        if not nums.empty:
            uniq = sorted(nums.unique().tolist())
            rating_vals = st.multiselect("⭐ Filter by rating", uniq, default=uniq, key="rating_f")

    # apply keyword + rating filters
    fdf = df
    if keyword:
        fdf = fdf[fdf[text_col].astype(str).str.contains(keyword, case=False, na=False)]
    if rating_vals and rating_col:
        fdf = fdf[rating_series(fdf[rating_col]).isin(rating_vals)]

    if query != st.session_state.get("last_search", ""):
        st.session_state.last_search = query
        if query:
            log_event(user, "search", f"Searched items for '{query}'")

    if item_col and item_col in df.columns:
        items = fdf[item_col].dropna().astype(str).tolist()
        matches = search_items(items, query)
        st.markdown(f"**{len(matches)} items found**" +
                    (f" for prefix **“{query}”**" if query else f" • {len(fdf)} matching reviews"))
        if not matches:
            st.warning("No items match. Try a shorter prefix.")
            return None
        if "visible_count" not in st.session_state:
            st.session_state.visible_count = 9
        for i in range(0, min(len(matches), st.session_state.visible_count), 3):
            cols = st.columns(3)
            for j, name in enumerate(matches[i:i + 3]):
                sub = fdf[fdf[item_col].astype(str) == name]
                avg = None
                if rating_col and rating_col in df.columns:
                    nums = rating_series(sub[rating_col]).dropna()
                    avg = float(nums.mean()) if not nums.empty else None
                with cols[j]:
                    st.markdown(item_card_html(name, len(sub), avg), unsafe_allow_html=True)
                    picked = st.session_state.get("selected_item") == name
                    if st.button(f"{'✅ Selected' if picked else 'Select'}  •  {name[:22]}",
                                 key=f"sel_{i}_{j}", type="secondary", use_container_width=True):
                        st.session_state.selected_item = None if picked else name
                        st.session_state.analysis = None
                        log_event(user, "view_product", f"Selected item '{name}' ({len(sub)} reviews)")
                        st.rerun()
        if st.session_state.visible_count < len(matches):
            if st.button("⬇️ Show more items", type="secondary"):
                st.session_state.visible_count += 9
                st.rerun()
    else:
        st.info(f"📦 No item column mapped — analysis will run on **all {len(fdf)} matching reviews**.")
    return fdf


# ---------- section 4: analyse + dashboard ----------

def _analyse_section(user, ds_id, ds_name, df, fdf, mapping):
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
    item = st.session_state.get("selected_item")
    scope_df = fdf[fdf[mapping["item"]].astype(str) == item] if (item and mapping["item"]) else fdf
    scope_name = item if item else "All matching reviews"

    a1, a2 = st.columns([1.4, 1])
    with a1:
        st.markdown(f"#### 🎯 Ready to analyse: **{scope_name}** ({len(scope_df)} reviews)")
    with a2:
        go = st.button("💜  Analyse The Reviews", use_container_width=True)

    if go:
        if scope_df.empty:
            st.error("No reviews in the current selection.")
            return
        with st.spinner("Running NLP aspect-sentiment analysis…"):
            reviews = reviews_from_df(scope_df, mapping)
            result = analyze_reviews(reviews)
            st.session_state.analysis = result
            save_analysis(user["id"], ds_id, scope_name, ds_name, result["total"],
                          result["overall"]["positive"], result["overall"]["neutral"],
                          result["overall"]["negative"], result["verdict"])
            log_event(user, "analyse",
                      f"Analysed '{scope_name}' in '{ds_name}' → {result['verdict']} "
                      f"(+{result['overall']['positive']}/~{result['overall']['neutral']}/-{result['overall']['negative']})")
        st.rerun()

    result = st.session_state.get("analysis")
    if not result:
        return
    _dashboard(result, ds_name, scope_name)


def _dashboard(result, ds_name, scope_name):
    st.markdown(f"### 📊 Analysis Dashboard — {scope_name} <span class='small-note'>({ds_name})</span>",
                unsafe_allow_html=True)
    ov = result["overall"]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="glass" style="text-align:center;">
          <div class="kpi-label">TOTAL REVIEWS ANALYZED</div>
          <div class="kpi-value">{result['total']}</div>
          <div class="kpi-sub">{scope_name[:28]}</div></div>""", unsafe_allow_html=True)
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

    # Line chart: monthly trend if dates exist, else rolling trend
    dates = [r.get("date", "") for r in result["rows"]]
    sents = [r["sentiment"] for r in result["rows"]]
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    tl = fig_timeline(dates, sents) if any(dates) else None
    st.plotly_chart(tl if tl else fig_rolling(sents), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    ratings = [r["rating"] for r in result["rows"] if r.get("rating") is not None]
    if ratings:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.plotly_chart(fig_ratings(ratings), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 🧩 Aspect detail")
    rows = []
    for a, d in result["aspects"].items():
        t = max(1, d["positive"] + d["neutral"] + d["negative"])
        rows.append({"Aspect": a, "👍 Positive": d["positive"], "😐 Neutral": d["neutral"],
                     "👎 Negative": d["negative"], "Positivity %": round(d["positive"] / t * 100, 1)})
    st.dataframe(pd.DataFrame(rows).sort_values("Positivity %", ascending=False),
                 use_container_width=True, hide_index=True)

    st.markdown("#### 💬 Sample analyzed reviews")
    filt = st.radio("Filter", ["All", "Positive", "Neutral", "Negative"], horizontal=True, key="rev_filter")
    shown = 0
    for r in result["rows"]:
        if filt != "All" and r["sentiment"] != filt.lower():
            continue
        tags = " ".join(f'<span class="aspect-tag">{a}</span>' for a in r["aspects"])
        meta = f"<b>{r['author']}</b> <span class='small-note'>"
        if r.get("date"):
            meta += f"• {r['date']} "
        if r.get("rating") is not None:
            try:
                star_count = max(0, min(5, int(round(float(r["rating"])))) )
                stars = "★" * star_count + "☆" * (5 - star_count)
                meta += f"• {stars}"
            except (TypeError, ValueError):
                pass
        meta += "</span>"
        st.markdown(f"""<div class="glass-soft" style="margin-bottom:10px;">
          {meta} &nbsp; {sent_badge(r['sentiment'])}<br/>
          <div style="margin:6px 0;">{r['text']}</div>{tags}</div>""", unsafe_allow_html=True)
        shown += 1
        if shown >= 8:
            break


# ---------- page entry ----------

def page_analysis():
    user = st.session_state.user
    header("Aspect Sentiment Analytics",
           "Upload your own review datasets, search the data, and analyse any item.")
    out = _dataset_section(user)
    if out[0] is None:
        return
    ds_id, (ds_name, df) = out
    mapping = _mapping_section(df, ds_id)
    fdf = _search_section(df, mapping, user)
    if fdf is None or fdf.empty:
        if fdf is not None and fdf.empty:
            st.warning("No reviews match the current filters.")
        return
    _analyse_section(user, ds_id, ds_name, df, fdf, mapping)
