from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# PAGE / VERSION
# =========================================================
st.set_page_config(page_title="SMARTEK360 | Yapay Zeka Analiz", layout="wide")
APP_VERSION = "AI_FIX_TRENDYOL_FORCE_V4_WITH_CORRECT_ADS_2026-05-23"

if "logged_in" not in st.session_state or st.session_state.logged_in is not True:
    st.warning("Bu sayfaya erişmek için önce ana sayfadan giriş yapmalısın.")
    st.stop()

# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 50% 8%, rgba(218, 165, 32, 0.16), transparent 30%),
                linear-gradient(135deg, #050505 0%, #111111 48%, #050505 100%);
        }
        header { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1500px; }
        .ai-hero {
            background: rgba(8, 8, 8, 0.78);
            border: 1px solid rgba(212, 175, 55, 0.35);
            box-shadow: 0 24px 85px rgba(0,0,0,0.50);
            border-radius: 30px;
            padding: 26px 32px;
            backdrop-filter: blur(16px);
            margin-bottom: 22px;
        }
        .ai-title { color:#fff; font-size:38px; font-weight:850; margin-bottom:6px; }
        .ai-subtitle { color:rgba(255,255,255,.72); font-size:16px; line-height:1.5; }
        .gold-line { width:150px; height:3px; background:linear-gradient(90deg,transparent,#d4af37,transparent); margin-top:18px; border-radius:99px; }
        .big-card {
            background:rgba(255,255,255,0.055);
            border:1px solid rgba(212,175,55,0.35);
            border-radius:24px;
            padding:20px 22px;
            min-height:108px;
        }
        .small-card {
            background:rgba(255,255,255,0.055);
            border:1px solid rgba(255,255,255,0.10);
            border-radius:20px;
            padding:16px 18px;
            min-height:96px;
        }
        .metric-label { color:rgba(255,255,255,.78); font-size:14px; font-weight:700; margin-bottom:8px; }
        .metric-value { color:#fff; font-size:32px; font-weight:900; white-space:normal; line-height:1.1; word-break:break-word; }
        .metric-sub { color:#d4af37; font-size:12px; font-weight:700; margin-top:8px; }
        .metric-value-small { color:#fff; font-size:24px; font-weight:850; white-space:normal; line-height:1.15; word-break:break-word; }
        div.stButton > button { border-radius:14px; border:1px solid rgba(212,175,55,0.55); background:linear-gradient(135deg,#d4af37,#9d7417); color:#111; font-weight:800; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="ai-hero">
        <div class="ai-title">🤖 SMARTEK360: Yapay Zeka Analiz Paneli</div>
        <div class="ai-subtitle">
            Bu sürümde <b>Net Ciro</b> doğrudan platform panellerindeki ana Total Revenue / Net Sales mantığıyla hesaplanır:
            Shopify + Trendyol + Hepsiburada. Ürün satırı cirosu Net Ciro hesabına karıştırılmaz.
        </div>
        <div class="gold-line"></div>
        <div style="color:rgba(255,255,255,.45);font-size:12px;margin-top:10px;">Sürüm: {APP_VERSION}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# PATHS
# =========================================================
def find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current.parent, *current.parents]:
        if (parent / "ana_sayfa.py").exists():
            return parent
    return Path(__file__).resolve().parents[2]

PROJECT_DIR = find_project_root()
PAGES_DIR = PROJECT_DIR / "pages"
SHOPIFY_DIR = PAGES_DIR / "Shopify_app"
TRENDYOL_DIR = PAGES_DIR / "smartek_app"
HEPSIBURADA_DIR = PAGES_DIR / "Hepsiburada_app"
KREATIF_DIR = PAGES_DIR / "Kreatif_Takip"

# =========================================================
# HELPERS
# =========================================================
def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).lower().strip()
    tr_map = str.maketrans({
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    })
    text = text.translate(tr_map)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9?]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def to_float(value) -> float:
    if value is None or pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    s = (s.replace("TL", "").replace("TRY", "").replace("₺", "").replace("%", "")
           .replace('"', "").replace("\xa0", "").replace(" ", ""))
    if s.lower() in {"-", "nan", "none", "null", "henüzfaturakesilmemiştir.", "surekli", "sürekli"}:
        return 0.0
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 1 and all(part.isdigit() for part in parts) and all(len(part) == 3 for part in parts[1:]):
            s = "".join(parts)
    try:
        return float(s)
    except Exception:
        cleaned = re.sub(r"[^0-9.\-]", "", s)
        try:
            return float(cleaned)
        except Exception:
            return 0.0


def money(value: float) -> str:
    return f"{float(value):,.2f} TL"


def safe_divide(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def find_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    norm_cols = {normalize_text(c): c for c in df.columns}
    norm_candidates = [normalize_text(c) for c in candidates]
    for target in norm_candidates:
        for norm_col, raw_col in norm_cols.items():
            if target == norm_col:
                return raw_col
    for target in norm_candidates:
        for norm_col, raw_col in norm_cols.items():
            if target and target in norm_col:
                return raw_col
    return None


def find_col_contains(df: pd.DataFrame, must_have: list[str]) -> Optional[str]:
    keys = [normalize_text(k) for k in must_have]
    for c in df.columns:
        n = normalize_text(c)
        if all(k in n for k in keys):
            return c
    return None


def clean_sku(value) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).strip().replace(" ", "")
    if s.startswith("6-"):
        s = s[2:]
    s = s.replace("-", "")
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    try:
        if "e+" in s.lower():
            s = str(int(float(s)))
    except Exception:
        pass
    return s


def read_csv_best(path: Path, *, expected: list[str] | None = None, skip_options=(0, 1, 2)) -> tuple[pd.DataFrame, dict]:
    encodings = ["utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin1"]
    seps = [";", ",", "\t"]
    best_df = pd.DataFrame()
    best_meta = {"encoding": "", "sep": "", "skiprows": None, "score": -1}
    expected_norm = [normalize_text(x) for x in (expected or [])]

    for enc in encodings:
        for sep in seps:
            for skip in skip_options:
                try:
                    df = pd.read_csv(path, encoding=enc, sep=sep, dtype=str, skiprows=skip, low_memory=False, keep_default_na=False)
                    if df.shape[1] <= 1:
                        continue
                    cols_norm = " | ".join(normalize_text(c) for c in df.columns)
                    score = df.shape[1]
                    for key in expected_norm:
                        if key and key in cols_norm:
                            score += 1000
                    # Trendyol bozuk karakterli dosyalarda kolonlar Sipari? gibi gelir; buna ekstra tolerans.
                    if "faturalanacak tutar" in cols_norm:
                        score += 5000
                    if "sipari" in cols_norm and ("numara" in cols_norm or "numaras" in cols_norm):
                        score += 2000
                    if "sipari" in cols_norm and "tarih" in cols_norm:
                        score += 1000
                    if score > best_meta["score"]:
                        best_df = df
                        best_meta = {"encoding": enc, "sep": sep, "skiprows": skip, "score": score}
                except Exception:
                    continue
    return best_df, best_meta


def read_table_best(path: Path, expected: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    if path.suffix.lower() == ".csv":
        return read_csv_best(path, expected=expected)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        best_df = pd.DataFrame()
        best_meta = {"encoding": "excel", "sep": "excel", "skiprows": None, "score": -1}
        expected_norm = [normalize_text(x) for x in (expected or [])]
        for skip in [0, 1, 2]:
            try:
                df = pd.read_excel(path, dtype=str, skiprows=skip).fillna("")
                if df.shape[1] <= 1:
                    continue
                cols_norm = " | ".join(normalize_text(c) for c in df.columns)
                score = df.shape[1] + sum(1000 for k in expected_norm if k and k in cols_norm)
                if score > best_meta["score"]:
                    best_df = df
                    best_meta = {"encoding": "excel", "sep": "excel", "skiprows": skip, "score": score}
            except Exception:
                continue
        return best_df, best_meta
    return pd.DataFrame(), {"encoding": "", "sep": "", "skiprows": None, "score": -1}

# =========================================================
# PLATFORM PANEL REVENUE LOADERS
# =========================================================
@st.cache_data(show_spinner=False)
def load_shopify_panel_revenue() -> tuple[float, int, float, pd.DataFrame, pd.DataFrame]:
    rows = []
    debug = []
    if not SHOPIFY_DIR.exists():
        return 0.0, 0, 0.0, pd.DataFrame(), pd.DataFrame([{"platform":"Shopify","note":"Shopify folder not found","folder":str(SHOPIFY_DIR)}])

    for path in sorted(SHOPIFY_DIR.glob("*.csv")):
        name = path.name.lower()
        if "maliyet" in name or "meta" in name or "facebook" in name or "formatted" in name:
            continue
        if "shopify002" in name or "shopify003" in name or "shopify004" in name:
            continue
        if "shopify" not in name:
            continue

        df, meta = read_table_best(path, expected=["Name", "Created at", "Total"])
        if df.empty:
            debug.append({"platform":"Shopify","file":path.name,"status":"empty/unreadable", **meta})
            continue
        name_col = find_col(df, ["Name"])
        created_col = find_col(df, ["Created at"])
        total_col = find_col(df, ["Total"])
        refund_col = find_col(df, ["Refunded Amount"])
        cancelled_col = find_col(df, ["Cancelled at"])
        financial_col = find_col(df, ["Financial Status"])
        if not name_col or not created_col or not total_col:
            debug.append({"platform":"Shopify","file":path.name,"status":"missing required columns","columns":", ".join(map(str, df.columns[:12])), **meta})
            continue

        tmp = pd.DataFrame({
            "platform": "Shopify",
            "order_id": df[name_col].astype(str),
            "order_date": pd.to_datetime(df[created_col], errors="coerce", utc=True).dt.tz_localize(None),
            "total": df[total_col].apply(to_float),
            "refund": df[refund_col].apply(to_float) if refund_col else 0.0,
            "cancelled_at": pd.to_datetime(df[cancelled_col], errors="coerce", utc=True).dt.tz_localize(None) if cancelled_col else pd.NaT,
            "financial_status": df[financial_col].astype(str).str.lower() if financial_col else "",
            "source_file": path.name,
        })
        tmp["is_cancelled"] = tmp["cancelled_at"].notna() | tmp["financial_status"].isin(["voided", "void", "cancelled", "canceled"])
        tmp["net_sales"] = tmp["total"].fillna(0) - tmp["refund"].fillna(0)
        tmp.loc[tmp["is_cancelled"], "net_sales"] = 0.0
        rows.append(tmp)
        debug.append({"platform":"Shopify","file":path.name,"status":"read","rows":len(tmp),"file_net_sales":float(tmp["net_sales"].sum()), **meta})

    if not rows:
        return 0.0, 0, 0.0, pd.DataFrame(), pd.DataFrame(debug)

    all_orders = pd.concat(rows, ignore_index=True)
    all_orders = all_orders.drop_duplicates(subset=["order_id", "order_date", "total", "refund"], keep="first")
    order_summary = all_orders.groupby("order_id", as_index=False).agg(
        platform=("platform", "first"),
        order_date=("order_date", "first"),
        net_sales=("net_sales", "first"),
        is_cancelled=("is_cancelled", "max"),
        source_file=("source_file", "first"),
    )
    total_revenue = float(order_summary["net_sales"].sum())
    known_orders = int(order_summary[order_summary["net_sales"].gt(0)]["order_id"].nunique())
    return total_revenue, known_orders, total_revenue, order_summary, pd.DataFrame(debug)


@st.cache_data(show_spinner=False)
def load_trendyol_panel_revenue() -> tuple[float, int, pd.DataFrame, pd.DataFrame]:
    rows = []
    debug = []
    if not TRENDYOL_DIR.exists():
        return 0.0, 0, pd.DataFrame(), pd.DataFrame([{"platform":"Trendyol","note":"Trendyol folder not found","folder":str(TRENDYOL_DIR)}])

    # ÖNEMLİ: Aynı export hem CSV hem XLSX varsa çift sayımı önlemek için sadece CSV Tedarikci_Siparisleri dosyaları kullanılır.
    files = sorted(TRENDYOL_DIR.glob("*.csv"))
    files = [p for p in files if ("tedarikci_siparisleri" in normalize_text(p.name) or "siparis" in normalize_text(p.name))]

    # Eğer hiç CSV yoksa Excel fallback.
    if not files:
        files = sorted(TRENDYOL_DIR.glob("*.xlsx"))
        files = [p for p in files if ("tedarikci_siparisleri" in normalize_text(p.name) or "siparis" in normalize_text(p.name))]

    for path in files:
        df, meta = read_table_best(path, expected=["Faturalanacak Tutar", "Sipariş Numarası", "Sipariş Tarihi", "Sipariş Statüsü"])
        if df.empty:
            debug.append({"platform":"Trendyol","file":path.name,"status":"empty/unreadable", **meta})
            continue

        revenue_col = find_col(df, ["Faturalanacak Tutar"])
        # Bozuk karakterli cp1254 dosyalarda Sipariş alanları Sipari? şeklinde gelebilir.
        order_col = find_col(df, ["Sipariş Numarası", "Siparis Numarasi", "Sipari? Numaras?"]) or find_col_contains(df, ["sipari", "numara"])
        date_col = find_col(df, ["Sipariş Tarihi", "Siparis Tarihi", "Sipari? Tarihi"]) or find_col_contains(df, ["sipari", "tarih"])
        status_col = find_col(df, ["Sipariş Statüsü", "Siparis Statusu", "Sipari? Statüsü", "Sipari? Stat?s?"]) or find_col_contains(df, ["statu"])
        product_col = find_col(df, ["Ürün Adı", "Urun Adi", "Ürün Ad", "Urun Ad"])
        sku_col = find_col(df, ["Barkod", "SKU"])
        qty_col = find_col(df, ["Adet"])

        if not revenue_col:
            debug.append({"platform":"Trendyol","file":path.name,"status":"Faturalanacak Tutar column not found","columns":", ".join(map(str, df.columns[:20])), **meta})
            continue

        temp = pd.DataFrame({
            "platform": "Trendyol",
            "order_id": df[order_col].astype(str) if order_col else path.stem + "_" + df.index.astype(str),
            "order_date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
            "product_name": df[product_col].astype(str) if product_col else "",
            "sku": df[sku_col].apply(clean_sku) if sku_col else "",
            "qty": df[qty_col].apply(to_float) if qty_col else 1.0,
            "revenue": df[revenue_col].apply(to_float),
            "status": df[status_col].astype(str) if status_col else "",
            "source_file": path.name,
        })
        status_n = temp["status"].apply(normalize_text)
        # İade / iptal / teslim edilemedi gibi satışa dönmeyenleri panel cirosundan çıkar.
        bad_mask = status_n.str.contains("ade|iptal|edilemedi|cancel|return", na=False)
        temp.loc[bad_mask, ["revenue", "qty"]] = 0.0
        rows.append(temp)
        debug.append({
            "platform":"Trendyol", "file":path.name, "status":"read", "rows":len(temp),
            "valid_rows":int((~bad_mask).sum()), "removed_rows":int(bad_mask.sum()),
            "file_total_revenue":float(temp["revenue"].sum()),
            "revenue_col": str(revenue_col), "order_col": str(order_col), "status_col": str(status_col), **meta
        })

    if not rows:
        return 0.0, 0, pd.DataFrame(), pd.DataFrame(debug)

    lines = pd.concat(rows, ignore_index=True)
    # Tekrarlayan aynı satırları düşür.
    lines = lines.drop_duplicates(subset=["order_id", "sku", "product_name", "qty", "revenue", "source_file"], keep="first")
    total_revenue = float(lines["revenue"].sum())
    known_orders = int(lines[lines["revenue"].gt(0)]["order_id"].nunique())
    return total_revenue, known_orders, lines, pd.DataFrame(debug)


@st.cache_data(show_spinner=False)
def load_hepsiburada_panel_revenue() -> tuple[float, int, pd.DataFrame, pd.DataFrame]:
    candidates = []
    debug = []
    if not HEPSIBURADA_DIR.exists():
        return 0.0, 0, pd.DataFrame(), pd.DataFrame([{"platform":"Hepsiburada","note":"Hepsiburada folder not found","folder":str(HEPSIBURADA_DIR)}])

    for path in sorted(HEPSIBURADA_DIR.glob("*.csv")):
        lname = normalize_text(path.name)
        if not lname.startswith("hepsiburada"):
            continue
        if "maliyet" in lname or "iade" in lname:
            continue
        df, meta = read_table_best(path, expected=["SKU", "Toplam Satis Tutari", "Toplam Satis Adedi", "Urun Adi"])
        if df.empty:
            debug.append({"platform":"Hepsiburada","file":path.name,"status":"empty/unreadable", **meta})
            continue
        sku_col = find_col(df, ["SKU"])
        revenue_col = find_col(df, ["Toplam Satis Tutari", "Toplam Satış Tutarı", "Total Sales Amount"])
        qty_col = find_col(df, ["Toplam Satis Adedi", "Toplam Satış Adedi", "Total Sales Qty", "Satis Miktari"])
        product_col = find_col(df, ["Urun Adi", "Ürün Adı", "Product Name"])
        if sku_col and revenue_col and qty_col and product_col:
            temp = pd.DataFrame({
                "platform": "Hepsiburada",
                "order_id": path.stem,
                "order_date": pd.NaT,
                "sku": df[sku_col].astype(str),
                "product_name": df[product_col].astype(str),
                "qty": df[qty_col].apply(to_float),
                "revenue": df[revenue_col].apply(to_float),
                "source_file": path.name,
            })
            candidates.append(temp)
            debug.append({"platform":"Hepsiburada","file":path.name,"status":"read snapshot","rows":len(temp),"file_total_revenue":float(temp["revenue"].sum()), **meta})
        else:
            debug.append({"platform":"Hepsiburada","file":path.name,"status":"not a sales snapshot","columns":", ".join(map(str, df.columns[:15])), **meta})

    if not candidates:
        return 0.0, 0, pd.DataFrame(), pd.DataFrame(debug)

    selected = max(candidates, key=lambda x: x["revenue"].sum()).copy()
    total_revenue = float(selected["revenue"].sum())
    # Snapshot dosyasında gerçek sipariş adedi yok; yanlış göstermemek için 0.
    return total_revenue, 0, selected, pd.DataFrame(debug)

# =========================================================
# ADS / CREATIVE SUMMARY
# =========================================================
@st.cache_data(show_spinner=False)
def load_ad_spend_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    debug = []
    # Shopify Meta/Billing files
    if SHOPIFY_DIR.exists():
        for path in sorted(SHOPIFY_DIR.glob("*.csv")):
            lname = normalize_text(path.name)
            if not ("meta" in lname or "facebook" in lname):
                continue
            df, meta = read_table_best(path, expected=["Amount spent", "Spend", "Tutar"])
            if df.empty:
                continue
            spend_col = find_col(df, ["Amount spent (TRY)", "Amount spent", "Spend", "Harcanan Tutar", "Tutar"])
            revenue_col = find_col(df, ["Purchase conversion value", "Purchases conversion value", "Revenue", "Satın alma dönüşüm değeri"])
            if spend_col:
                spend = float(df[spend_col].apply(to_float).sum())
                ad_rev = float(df[revenue_col].apply(to_float).sum()) if revenue_col else 0.0
                rows.append({"platform":"Shopify","source":"Meta/Billing","ad_spend":spend,"ad_revenue":ad_rev,"source_file":path.name})
                debug.append({"platform":"Shopify Ads","file":path.name,"spend":spend,"ad_revenue":ad_rev, **meta})

    # Trendyol manual weekly ads
    weekly = TRENDYOL_DIR / "manual_weekly_trendyol_ads.csv"
    if weekly.exists():
        df, meta = read_table_best(weekly, expected=["weekly_spend", "weekly_revenue"])
        if not df.empty:
            spend_col = find_col(df, ["weekly_spend", "weekly spend", "Haftalık Harcama", "Haftalik Harcama", "Spend"])
            revenue_col = find_col(df, ["weekly_revenue", "weekly revenue", "total ad revenue", "ad revenue", "Reklam Cirosu", "Revenue"])
            if spend_col:
                spend = float(df[spend_col].apply(to_float).sum())
                ad_rev = float(df[revenue_col].apply(to_float).sum()) if revenue_col else 0.0
                rows.append({"platform":"Trendyol","source":"Manual Weekly Trendyol Ads","ad_spend":spend,"ad_revenue":ad_rev,"source_file":weekly.name})
                debug.append({"platform":"Trendyol Ads","file":weekly.name,"spend":spend,"ad_revenue":ad_rev, **meta})

    out = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["platform","source","ad_spend","ad_revenue","source_file"])
    return out, pd.DataFrame(debug)


@st.cache_data(show_spinner=False)
def load_creative_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    debug = []
    if not KREATIF_DIR.exists():
        return pd.DataFrame(), pd.DataFrame([{"note":"Kreatif folder not found", "folder":str(KREATIF_DIR)}])
    for path in sorted(KREATIF_DIR.glob("*.csv")):
        if path.name.lower() in {"creative_history.csv", "creative_summary.csv", "creative_export.csv"}:
            continue
        df, meta = read_table_best(path, expected=["Kampanya Adı", "Harcanan Tutar", "Alışveriş", "ROAS"])
        if df.empty:
            continue
        campaign_col = find_col(df, ["Kampanya Adı", "Campaign name", "Campaign"])
        creative_col = find_col(df, ["Reklam Adı", "Reklamlar", "Ad name", "Ad"])
        spend_col = find_col(df, ["Harcanan Tutar (TRY)", "Amount spent", "Spend", "Harcama"])
        purchase_col = find_col(df, ["Alışverişler", "Purchases", "Satın almalar"])
        roas_col = find_col(df, ["Alışveriş Reklam Harcamasının Getirisi", "Purchase ROAS", "ROAS"])
        reach_col = find_col(df, ["Erişim", "Reach"])
        impr_col = find_col(df, ["Gösterim", "Impressions"])
        if not spend_col:
            continue
        temp = pd.DataFrame({
            "campaign_name": df[campaign_col].astype(str) if campaign_col else path.stem,
            "creative_name": df[creative_col].astype(str) if creative_col else "",
            "spend": df[spend_col].apply(to_float),
            "purchases": df[purchase_col].apply(to_float) if purchase_col else 0.0,
            "roas": df[roas_col].apply(to_float) if roas_col else 0.0,
            "reach": df[reach_col].apply(to_float) if reach_col else 0.0,
            "impressions": df[impr_col].apply(to_float) if impr_col else 0.0,
            "source_file": path.name,
        })
        temp = temp[~((temp["campaign_name"].astype(str).str.strip()=="") & (temp["creative_name"].astype(str).str.strip()==""))]
        temp["attributed_revenue"] = temp["spend"] * temp["roas"]
        rows.append(temp)
        debug.append({"platform":"Creative","file":path.name,"rows":len(temp),"spend":float(temp["spend"].sum()), **meta})
    if not rows:
        return pd.DataFrame(), pd.DataFrame(debug)
    out = pd.concat(rows, ignore_index=True)
    out = out.drop_duplicates(subset=["campaign_name","creative_name","spend","purchases","source_file"], keep="last")
    return out, pd.DataFrame(debug)



def build_correct_ad_spend_summary(raw_ads_df: pd.DataFrame, creative_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reklam harcaması finans hesabında yalnızca şu iki kalemi toplar:
    1) Trendyol Reklam Harcaması = manual_weekly_trendyol_ads.csv weekly_spend toplamı
    2) Meta Spend = önce Kreatif/Meta raporundaki spend toplamı; kreatif yoksa Shopify/Meta/Billing dosyaları

    Böylece Meta/Kreatif harcaması ile Shopify meta dosyası aynı anda iki kez sayılmaz.
    """
    base_cols = ["platform", "source", "ad_spend", "ad_revenue", "source_file"]
    if raw_ads_df is None or raw_ads_df.empty:
        raw_ads_df = pd.DataFrame(columns=base_cols)
    else:
        raw_ads_df = raw_ads_df.copy()
        for col in base_cols:
            if col not in raw_ads_df.columns:
                raw_ads_df[col] = 0.0 if col in {"ad_spend", "ad_revenue"} else ""

    raw_ads_df["ad_spend"] = pd.to_numeric(raw_ads_df["ad_spend"], errors="coerce").fillna(0.0)
    raw_ads_df["ad_revenue"] = pd.to_numeric(raw_ads_df["ad_revenue"], errors="coerce").fillna(0.0)

    platform_norm = raw_ads_df["platform"].astype(str).str.lower()
    source_norm = raw_ads_df["source"].astype(str).str.lower()
    file_norm = raw_ads_df["source_file"].astype(str).str.lower()

    trendyol_mask = (
        platform_norm.eq("trendyol")
        | source_norm.str.contains("trendyol", na=False)
        | file_norm.str.contains("manual_weekly_trendyol_ads", na=False)
    )
    trendyol_spend = float(raw_ads_df.loc[trendyol_mask, "ad_spend"].sum())
    trendyol_revenue = float(raw_ads_df.loc[trendyol_mask, "ad_revenue"].sum())

    # Meta Spend için önce Kreatif/Meta raporu kullanılır.
    meta_source = "Meta Spend - Kreatif Raporu"
    meta_spend = 0.0
    meta_revenue = 0.0
    if creative_df is not None and not creative_df.empty and "spend" in creative_df.columns:
        meta_spend = float(pd.to_numeric(creative_df["spend"], errors="coerce").fillna(0.0).sum())
        if "attributed_revenue" in creative_df.columns:
            meta_revenue = float(pd.to_numeric(creative_df["attributed_revenue"], errors="coerce").fillna(0.0).sum())

    # Kreatif raporu yoksa Shopify/Meta/Billing dosyaları yedek kaynak olur.
    if meta_spend <= 0:
        meta_mask = ~trendyol_mask & (
            platform_norm.eq("shopify")
            | source_norm.str.contains("meta|facebook|billing", na=False, regex=True)
            | file_norm.str.contains("meta|facebook|fb|billing|campaign", na=False, regex=True)
        )
        meta_spend = float(raw_ads_df.loc[meta_mask, "ad_spend"].sum())
        meta_revenue = float(raw_ads_df.loc[meta_mask, "ad_revenue"].sum())
        meta_source = "Meta Spend - Dosya/Billing"

    finance_ads = pd.DataFrame([
        {"platform": "Trendyol", "source": "Trendyol Reklam Harcaması", "ad_spend": trendyol_spend, "ad_revenue": trendyol_revenue, "source_file": "manual_weekly_trendyol_ads.csv"},
        {"platform": "Meta", "source": meta_source, "ad_spend": meta_spend, "ad_revenue": meta_revenue, "source_file": meta_source},
    ])
    finance_ads = finance_ads[finance_ads["ad_spend"].fillna(0).ne(0) | finance_ads["ad_revenue"].fillna(0).ne(0)].reset_index(drop=True)

    breakdown = pd.DataFrame([
        {"Kaynak": "Trendyol Reklam Harcaması", "Tutar": trendyol_spend, "Reklam Cirosu": trendyol_revenue, "Açıklama": "manual_weekly_trendyol_ads.csv weekly_spend"},
        {"Kaynak": "Meta Spend", "Tutar": meta_spend, "Reklam Cirosu": meta_revenue, "Açıklama": meta_source},
        {"Kaynak": "TOPLAM", "Tutar": trendyol_spend + meta_spend, "Reklam Cirosu": trendyol_revenue + meta_revenue, "Açıklama": "Trendyol Reklam Harcaması + Meta Spend"},
    ])
    return finance_ads, breakdown

# =========================================================
# LOAD ALL
# =========================================================
shopify_rev, shopify_orders, shopify_ref, shopify_orders_df, dbg_shopify = load_shopify_panel_revenue()
trendyol_rev, trendyol_orders, trendyol_lines_df, dbg_trendyol = load_trendyol_panel_revenue()
hb_rev, hb_orders, hb_lines_df, dbg_hb = load_hepsiburada_panel_revenue()
raw_ads_df, dbg_ads = load_ad_spend_summary()
creative_df, dbg_creative = load_creative_summary()
ads_df, ad_spend_breakdown = build_correct_ad_spend_summary(raw_ads_df, creative_df)

panel_revenue = pd.DataFrame([
    {"Platform":"Shopify", "Panel Total Revenue": shopify_rev, "Bilinen Sipariş": shopify_orders, "Revenue Source":"Shopify panelindeki Net Sales / Total mantığı", "Ana Klasör": str(SHOPIFY_DIR)},
    {"Platform":"Trendyol", "Panel Total Revenue": trendyol_rev, "Bilinen Sipariş": trendyol_orders, "Revenue Source":"Trendyol panelindeki Faturalanacak Tutar toplamı", "Ana Klasör": str(TRENDYOL_DIR)},
    {"Platform":"Hepsiburada", "Panel Total Revenue": hb_rev, "Bilinen Sipariş": hb_orders, "Revenue Source":"Hepsiburada panelindeki en yüksek Total Revenue snapshot", "Ana Klasör": str(HEPSIBURADA_DIR)},
])

total_revenue = float(panel_revenue["Panel Total Revenue"].sum())
known_orders = int(panel_revenue["Bilinen Sipariş"].sum())
total_ad_spend = float(ads_df["ad_spend"].sum()) if not ads_df.empty else 0.0
total_ad_revenue = float(ads_df["ad_revenue"].sum()) if not ads_df.empty else 0.0
roas = safe_divide(total_ad_revenue, total_ad_spend)
aov = safe_divide(total_revenue, known_orders)
net_profit_proxy = total_revenue - total_ad_spend
cac = safe_divide(total_ad_spend, known_orders)
ltv_est = aov * 1.5
forecast_30d = total_revenue / 4 if total_revenue else 0.0

with st.sidebar:
    st.header("Yapay Zeka Ayarları")
    all_time = st.toggle("Tüm Zamanlar", value=True)
    st.caption("Bu FIX4 sürümünde Net Ciro, tarih filtresinden bağımsız olarak platform panellerinin ana Total Revenue toplamını gösterir. Önce doğru toplamı sabitlemek için böyle ayarlandı.")
    st.caption("Reklam harcaması finans hesabında Trendyol Reklam Harcaması + Meta Spend olarak hesaplanır.")
    show_debug_top = st.checkbox("Üstte debug özeti göster", value=False)

st.caption("Rapor dönemi: Tüm Zamanlar")
st.info("Net Ciro artık Panel Total Revenue toplamıdır. Trendyol satırı 0 veya çok düşükse, sorun doğrudan Trendyol dosyalarının okunması/klasörüyle ilgilidir; aşağıdaki Veri Durumu sekmesi kesin sebebi gösterir.")
st.info("Reklam Harcaması = Trendyol Reklam Harcaması + Meta Spend. Meta Spend için önce Kreatif/Meta raporu kullanılır; yoksa Shopify/Meta/Billing dosyaları yedek kaynak olur.")

if show_debug_top:
    st.write("Project dir:", PROJECT_DIR)
    st.write("Trendyol dir exists:", TRENDYOL_DIR.exists(), str(TRENDYOL_DIR))

# =========================================================
# KPI CARDS
# =========================================================
col1, col2, col3 = st.columns([2.1, 1.1, 1.1])
with col1:
    st.markdown(f"""
    <div class="big-card">
        <div class="metric-label">Net Ciro</div>
        <div class="metric-value">{money(total_revenue)}</div>
        <div class="metric-sub">Panel Total Revenue toplamı</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="small-card"><div class="metric-label">Bilinen Sipariş</div><div class="metric-value-small">{known_orders:,.0f}</div></div>
    """, unsafe_allow_html=True)
with col3:
    target = 500000.0
    target_rate = safe_divide(total_revenue, target) * 100
    st.markdown(f"""
    <div class="small-card"><div class="metric-label">Hedef Gerçekleşme</div><div class="metric-value-small">%{target_rate:,.1f}</div></div>
    """, unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)
with c4:
    st.markdown(f"<div class='small-card'><div class='metric-label'>Anlık Net Kar</div><div class='metric-value-small'>{money(net_profit_proxy)}</div></div>", unsafe_allow_html=True)
with c5:
    st.markdown(f"<div class='small-card'><div class='metric-label'>AOV</div><div class='metric-value-small'>{money(aov)}</div></div>", unsafe_allow_html=True)
with c6:
    st.markdown(f"<div class='small-card'><div class='metric-label'>ROAS</div><div class='metric-value-small'>{roas:,.2f}</div></div>", unsafe_allow_html=True)

c7, c8, c9, c10 = st.columns(4)
with c7:
    st.markdown(f"<div class='small-card'><div class='metric-label'>Reklam Harcaması</div><div class='metric-value-small'>{money(total_ad_spend)}</div></div>", unsafe_allow_html=True)
with c8:
    st.markdown(f"<div class='small-card'><div class='metric-label'>CAC</div><div class='metric-value-small'>{money(cac)}</div></div>", unsafe_allow_html=True)
with c9:
    st.markdown(f"<div class='small-card'><div class='metric-label'>LTV Tahmini</div><div class='metric-value-small'>{money(ltv_est)}</div></div>", unsafe_allow_html=True)
with c10:
    st.markdown(f"<div class='small-card'><div class='metric-label'>30 Gün Tahmini Ciro</div><div class='metric-value-small'>{money(forecast_30d)}</div></div>", unsafe_allow_html=True)

# =========================================================
# AI COMMENTARY
# =========================================================
def build_commentary() -> str:
    lines = []
    lines.append("### Yapay Zeka Yorumu")
    lines.append(f"Toplam Net Ciro {money(total_revenue)} olarak hesaplandı. Bu değer Shopify, Trendyol ve Hepsiburada panellerindeki ana Total Revenue/Net Sales değerlerinin toplamıdır.")
    if trendyol_rev <= 10000:
        lines.append("⚠️ Trendyol cirosu çok düşük veya okunamamış görünüyor. Veri Durumu sekmesinde Trendyol dosyalarının okunup okunmadığını kontrol et.")
    if total_ad_spend > 0:
        lines.append(f"Toplam reklam harcaması {money(total_ad_spend)}. ROAS {roas:,.2f}. ROAS düşükse kreatif, hedefleme ve ürün sayfası birlikte kontrol edilmeli.")
    else:
        lines.append("Reklam harcaması okunmadı. Reklam dosyaları doğru klasördeyse Veri Durumu sekmesinde dosya okuma detayını kontrol et.")
    if known_orders > 0:
        lines.append(f"Bilinen sipariş sayısı {known_orders:,}. AOV {money(aov)} seviyesinde.")
    lines.append("Hepsiburada snapshot dosyasında gerçek sipariş adedi olmadığı için sipariş sayısına eklenmez; sadece ciroya eklenir.")
    return "\n\n".join(lines)

st.markdown(build_commentary())

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Panel Ciro Kontrolü", "🎨 Kreatif Yorumu", "🧪 Veri Durumu", "💬 Canlı Yapay Zeka Asistanı"])

with tab1:
    st.subheader("Panel Total Revenue Kontrolü")
    st.write("Net Ciro kartı aşağıdaki tablodaki **Panel Total Revenue** toplamıdır.")
    total_row = pd.DataFrame([{"Platform":"TOPLAM", "Panel Total Revenue":total_revenue, "Bilinen Sipariş":known_orders, "Revenue Source":"Toplam", "Ana Klasör":""}])
    display = pd.concat([panel_revenue, total_row], ignore_index=True)
    st.dataframe(
        display.style.format({"Panel Total Revenue":"{:,.2f} TL", "Bilinen Sipariş":"{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )
    fig = px.bar(panel_revenue, x="Platform", y="Panel Total Revenue", title="Platform Bazlı Panel Total Revenue")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Kreatif / Meta Yorumu")
    if creative_df.empty:
        st.info("Kreatif raporu okunmadı veya klasörde uygun CSV yok.")
    else:
        total_creative_spend = float(creative_df["spend"].sum())
        total_creative_rev = float(creative_df["attributed_revenue"].sum())
        creative_roas = safe_divide(total_creative_rev, total_creative_spend)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Kreatif Harcaması", money(total_creative_spend))
        k2.metric("Kreatif Geliri", money(total_creative_rev))
        k3.metric("Kreatif ROAS", f"{creative_roas:,.2f}")
        k4.metric("Kreatif Sayısı", f"{creative_df['creative_name'].nunique():,.0f}")
        top = creative_df.groupby(["campaign_name", "creative_name"], as_index=False).agg(
            spend=("spend", "sum"), purchases=("purchases", "sum"), attributed_revenue=("attributed_revenue", "sum"), reach=("reach", "sum"), impressions=("impressions", "sum")
        )
        top["roas"] = top.apply(lambda r: safe_divide(r["attributed_revenue"], r["spend"]), axis=1)
        st.dataframe(top.sort_values("spend", ascending=False).style.format({"spend":"{:,.2f} TL", "attributed_revenue":"{:,.2f} TL", "roas":"{:.2f}"}), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Veri Durumu / Debug")
    st.warning("Bu sekme hatanın nereden geldiğini gösterir. Trendyol satırında dosyalar görünmüyorsa veya file_total_revenue düşükse, Net Ciro da düşük çıkar.")
    st.markdown("#### Klasörler")
    folders_df = pd.DataFrame([
        {"name":"PROJECT_DIR", "path":str(PROJECT_DIR), "exists":PROJECT_DIR.exists()},
        {"name":"SHOPIFY_DIR", "path":str(SHOPIFY_DIR), "exists":SHOPIFY_DIR.exists()},
        {"name":"TRENDYOL_DIR", "path":str(TRENDYOL_DIR), "exists":TRENDYOL_DIR.exists()},
        {"name":"HEPSIBURADA_DIR", "path":str(HEPSIBURADA_DIR), "exists":HEPSIBURADA_DIR.exists()},
        {"name":"KREATIF_DIR", "path":str(KREATIF_DIR), "exists":KREATIF_DIR.exists()},
    ])
    st.dataframe(folders_df, use_container_width=True, hide_index=True)

    st.markdown("#### Reklam Harcaması Toplam Kontrolü")
    st.dataframe(ad_spend_breakdown.style.format({"Tutar":"{:,.2f} TL", "Reklam Cirosu":"{:,.2f} TL"}), use_container_width=True, hide_index=True)

    st.markdown("#### Okunan Dosya Detayları")
    all_debug = pd.concat([dbg_shopify, dbg_trendyol, dbg_hb, dbg_ads, dbg_creative], ignore_index=True) if any(not d.empty for d in [dbg_shopify, dbg_trendyol, dbg_hb, dbg_ads, dbg_creative]) else pd.DataFrame()
    if all_debug.empty:
        st.info("Debug dosya kaydı yok.")
    else:
        st.dataframe(all_debug, use_container_width=True, hide_index=True)

    st.markdown("#### Trendyol Okunan Satırlar")
    if trendyol_lines_df.empty:
        st.error("Trendyol sipariş satırı okunamadı. Dosyalar pages/smartek_app klasöründe mi ve isimlerinde Tedarikci_Siparisleri geçiyor mu kontrol et.")
    else:
        st.dataframe(trendyol_lines_df.head(200), use_container_width=True, hide_index=True)
        st.download_button("Trendyol okunan satırları indir", data=trendyol_lines_df.to_csv(index=False, encoding="utf-8-sig"), file_name="debug_trendyol_lines.csv", mime="text/csv")

with tab4:
    st.subheader("💬 Canlı Yapay Zeka Asistanı")
    st.caption("Buradaki asistan, yukarıdaki düzeltilmiş Panel Total Revenue özetini kullanır.")
    question = st.text_area("Sorunu yaz", placeholder="Örn: Bu verilere göre hangi platform daha güçlü?", height=120)
    if st.button("Yorum Oluştur"):
        context = {
            "app_version": APP_VERSION,
            "panel_revenue": panel_revenue.to_dict(orient="records"),
            "total_revenue": total_revenue,
            "known_orders": known_orders,
            "ad_spend": total_ad_spend,
            "ad_spend_breakdown": ad_spend_breakdown.to_dict(orient="records"),
            "roas": roas,
            "aov": aov,
        }
        # Gemini key varsa kullan; yoksa yerel yorum üret.
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            api_key = None
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = f"""
Sen bir e-ticaret analiz asistanısın. Türkçe cevap ver.
Aşağıdaki veri özetini kullan. Net Ciro = platform panel total revenue toplamıdır.
Veri:
{context}
Kullanıcı sorusu: {question}
"""
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.markdown(response.text)
            except Exception as exc:
                st.warning(f"Gemini çalışmadı, yerel yorum veriyorum: {exc}")
                st.markdown(build_commentary())
        else:
            st.markdown(build_commentary())
