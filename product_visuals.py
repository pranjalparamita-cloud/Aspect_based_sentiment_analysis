"""
product_visuals.py — Lightweight, generated studio-style product visuals.
------------------------------------------------------------------------
Each catalog listing gets deterministic SVG images for a front, angled and
detail view without downloading, copying, or misrepresenting retailer photos.
They are generic visual previews for the generated demo catalog, not photos of
specific real-world SKUs.
"""
import base64
import hashlib
import html
import math

PALETTES = [
    ("#6657d9", "#a78bfa", "#f3e8ff"),
    ("#0f766e", "#5eead4", "#e6fffb"),
    ("#1d4ed8", "#93c5fd", "#eaf2ff"),
    ("#be185d", "#f9a8d4", "#fff0f6"),
    ("#b45309", "#fcd34d", "#fff8e7"),
    ("#475569", "#cbd5e1", "#f8fafc"),
]


def _palette(product):
    key = str(product.get("sku", product.get("id", "catalog"))).encode()
    return PALETTES[int(hashlib.sha256(key).hexdigest()[:8], 16) % len(PALETTES)]


def _silhouette(category, primary, secondary, view):
    """Return an SVG product silhouette tailored to a retail category."""
    angle = "translate(18,-4) skewX(-8)" if view == "angle" else ""
    detail = view == "detail"
    if category in {"Electronics", "Computers & Gaming"}:
        return f'''<g transform="{angle}"><rect x="125" y="72" width="270" height="188" rx="15" fill="{primary}"/>
          <rect x="142" y="89" width="236" height="152" rx="8" fill="#19233f"/><rect x="153" y="101" width="214" height="128" rx="5" fill="{secondary}" opacity=".78"/>
          <path d="M235 274h52l18 36H217z" fill="{primary}"/><rect x="175" y="308" width="172" height="13" rx="6" fill="#334155"/>
          {f'<circle cx="260" cy="165" r="52" fill="none" stroke="#fff" stroke-width="13" opacity=".88"/><circle cx="260" cy="165" r="20" fill="#fff" opacity=".8"/>' if detail else ''}</g>'''
    if category == "Mobile Accessories":
        return f'''<g transform="{angle}"><rect x="195" y="42" width="130" height="276" rx="24" fill="{primary}"/>
          <rect x="207" y="59" width="106" height="240" rx="16" fill="#15213d"/><rect x="216" y="78" width="88" height="180" rx="10" fill="{secondary}" opacity=".75"/>
          <circle cx="260" cy="278" r="8" fill="#fff" opacity=".85"/>
          {f'<rect x="232" y="109" width="56" height="56" rx="28" fill="none" stroke="#fff" stroke-width="9"/><path d="M260 120v34m-17-17h34" stroke="#fff" stroke-width="7" stroke-linecap="round"/>' if detail else ''}</g>'''
    if category == "Automotive Parts":
        return f'''<g transform="{angle}"><circle cx="260" cy="184" r="112" fill="{primary}"/><circle cx="260" cy="184" r="82" fill="{secondary}"/>
          <circle cx="260" cy="184" r="43" fill="#f8fafc"/><circle cx="260" cy="184" r="17" fill="#64748b"/>
          <g fill="#f8fafc">{''.join(f'<circle cx="{260 + int(65 * math.cos(i * 1.047))}" cy="{184 + int(65 * math.sin(i * 1.047))}" r="8"/>' for i in range(6))}</g>
          {f'<path d="M143 238l72-29 24 40-77 29z" fill="#334155"/><path d="M377 130l-72 29-24-40 77-29z" fill="#334155"/>' if detail else ''}</g>'''
    if category == "Automotive Accessories":
        return f'''<g transform="{angle}"><path d="M125 220l23-74c7-23 25-39 49-44h126c24 5 42 21 49 44l23 74v48h-270z" fill="{primary}"/>
          <path d="M169 160h182l22 58H147z" fill="{secondary}" opacity=".82"/><circle cx="180" cy="269" r="28" fill="#1e293b"/><circle cx="340" cy="269" r="28" fill="#1e293b"/>
          <circle cx="180" cy="269" r="12" fill="#cbd5e1"/><circle cx="340" cy="269" r="12" fill="#cbd5e1"/>
          {f'<rect x="230" y="180" width="60" height="28" rx="6" fill="#fff" opacity=".9"/>' if detail else ''}</g>'''
    if category in {"Home Appliances", "Home & Kitchen"}:
        return f'''<g transform="{angle}"><rect x="166" y="53" width="188" height="272" rx="22" fill="{primary}"/>
          <rect x="184" y="78" width="152" height="110" rx="11" fill="{secondary}" opacity=".8"/><circle cx="260" cy="245" r="43" fill="#ffffff" opacity=".86"/>
          <circle cx="260" cy="245" r="30" fill="#1e293b" opacity=".86"/>
          {f'<path d="M260 215v30l22 13" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>' if detail else ''}</g>'''
    if category == "Fashion & Beauty":
        return f'''<g transform="{angle}"><path d="M116 235c38-7 72-42 99-89l42 21c-11 28-2 47 36 55 48 10 83 25 101 46v34H116z" fill="{primary}"/>
          <path d="M164 235c33-19 53-43 66-73" fill="none" stroke="{secondary}" stroke-width="18" stroke-linecap="round"/>
          <rect x="118" y="301" width="278" height="16" rx="8" fill="#334155"/>
          {f'<circle cx="275" cy="194" r="31" fill="{secondary}" opacity=".8"/>' if detail else ''}</g>'''
    if category == "Sports & Outdoors":
        return f'''<g transform="{angle}"><ellipse cx="260" cy="148" rx="84" ry="104" fill="none" stroke="{primary}" stroke-width="22"/>
          <path d="M207 95l106 106m0-106L207 201m-22-53h150m-75-85v170" stroke="{secondary}" stroke-width="5" opacity=".85"/>
          <path d="M284 239l45 100" stroke="{primary}" stroke-width="22" stroke-linecap="round"/><path d="M328 331l20 40" stroke="#334155" stroke-width="29" stroke-linecap="round"/>
          {f'<circle cx="169" cy="238" r="33" fill="{secondary}" stroke="#fff" stroke-width="5"/>' if detail else ''}</g>'''
    # Books & Office
    return f'''<g transform="{angle}"><path d="M148 82h107c28 0 45 11 57 29 12-18 29-29 57-29h43v234h-143c-22 0-38 8-57 24-19-16-35-24-57-24H108V112c12-18 29-30 40-30z" fill="{primary}"/>
      <path d="M260 111v205" stroke="#fff" stroke-width="7" opacity=".85"/><path d="M141 133h82m-82 28h82m-82 28h82m76-56h76m-76 28h76m-76 28h76" stroke="{secondary}" stroke-width="8" stroke-linecap="round"/>
      {f'<rect x="204" y="210" width="112" height="30" rx="8" fill="#fff" opacity=".85"/>' if detail else ''}</g>'''


def product_visual_svg(product, view="front", alt=""):
    """Return an inline data-URI SVG suitable for Streamlit/HTML image tags."""
    primary, secondary, background = _palette(product)
    category = str(product.get("category", "Books & Office"))
    title = html.escape(str(product.get("product_type", product.get("title", "Product")))[:34])
    label = {"front": "FRONT VIEW", "angle": "ANGLED VIEW", "detail": "DETAIL VIEW"}.get(view, "PRODUCT VIEW")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="390" viewBox="0 0 520 390" role="img" aria-label="{html.escape(alt or title)}">
      <defs><filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#373064" flood-opacity=".22"/></filter>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff"/><stop offset="1" stop-color="{background}"/></linearGradient></defs>
      <rect width="520" height="390" rx="26" fill="url(#bg)"/><ellipse cx="260" cy="334" rx="142" ry="20" fill="#4c416b" opacity=".15"/>
      <g filter="url(#shadow)">{_silhouette(category, primary, secondary, view)}</g>
      <text x="28" y="42" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#625a7e" letter-spacing="1.4">{label}</text>
      <text x="28" y="366" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#30284d">{title}</text>
    </svg>'''
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def catalog_image_html(product, view="front", css_class="catalog-thumb"):
    src = product_visual_svg(product, view, product.get("title", "Catalog product"))
    alt = html.escape(str(product.get("title", "Catalog product")))
    return f'<img class="{css_class}" src="{src}" alt="{alt}"/>'
