
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# AYARLAR
# =========================
st.set_page_config(page_title="IQIBLA Türkiye Panel", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
MANUAL_FILE = BASE_DIR / "manual_entries.csv"
PASSWORD = "1234"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(212,175,55,0.20), transparent 25%),
        radial-gradient(circle at 86% 12%, rgba(255,255,255,0.07), transparent 23%),
        radial-gradient(circle at 50% 90%, rgba(212,175,55,0.08), transparent 36%),
        linear-gradient(135deg, #050505 0%, #101010 48%, #050505 100%);
    color: #ffffff;
}

header { visibility: hidden; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container {
    max-width: 1500px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

/* Sidebar tamamen kapalı */
[data-testid="stSidebar"] {
    display: none;
}

/* Hero */
.modern-hero {
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(135deg, rgba(14,14,14,0.94), rgba(30,30,30,0.78)),
        radial-gradient(circle at 92% 10%, rgba(212,175,55,0.25), transparent 34%);
    border: 1px solid rgba(212,175,55,0.30);
    box-shadow: 0 28px 95px rgba(0,0,0,0.55);
    border-radius: 34px;
    padding: 34px 38px;
    margin-bottom: 20px;
    backdrop-filter: blur(18px);
}

.modern-hero:after {
    content: "";
    position: absolute;
    right: -85px;
    top: -85px;
    width: 280px;
    height: 280px;
    border-radius: 999px;
    background: rgba(212,175,55,0.12);
    filter: blur(4px);
}

.modern-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 13px;
    border: 1px solid rgba(212,175,55,0.38);
    border-radius: 999px;
    color: #d4af37;
    background: rgba(212,175,55,0.085);
    font-weight: 900;
    font-size: 12px;
    letter-spacing: .35px;
    margin-bottom: 14px;
}

.modern-title {
    color: #ffffff;
    font-size: 46px;
    font-weight: 950;
    letter-spacing: -1px;
    line-height: 1.06;
    margin-bottom: 10px;
}

.modern-subtitle {
    color: rgba(255,255,255,0.72);
    font-size: 16px;
    line-height: 1.6;
    max-width: 960px;
}

/* Top navigation */
.nav-wrap {
    background: rgba(255,255,255,0.048);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 28px;
    padding: 16px;
    margin-bottom: 22px;
    box-shadow: 0 18px 48px rgba(0,0,0,0.24);
}

/* Cards */
.modern-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 16px;
    margin-top: 16px;
    margin-bottom: 22px;
}

.modern-card {
    background: rgba(255,255,255,0.058);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 26px;
    padding: 20px;
    min-height: 148px;
    box-shadow: 0 18px 48px rgba(0,0,0,0.24);
    transition: all .18s ease;
}

.modern-card:hover {
    transform: translateY(-4px);
    border-color: rgba(212,175,55,0.42);
    background: rgba(255,255,255,0.075);
}

.modern-card h3 {
    color: #ffffff;
    font-size: 20px;
    font-weight: 850;
    margin: 6px 0 8px 0;
}

.modern-card p {
    color: rgba(255,255,255,0.68);
    font-size: 13px;
    line-height: 1.46;
    margin: 0;
}

.modern-icon {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(212,175,55,0.24), rgba(212,175,55,0.08));
    border: 1px solid rgba(212,175,55,0.24);
    font-size: 22px;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.060);
    border: 1px solid rgba(212,175,55,0.20);
    border-radius: 20px;
    padding: 16px;
    box-shadow: 0 16px 38px rgba(0,0,0,0.22);
}

[data-testid="stMetricLabel"] {
    color: rgba(255,255,255,0.70) !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 850;
}

/* Buttons */
div.stButton > button {
    border-radius: 17px;
    border: 1px solid rgba(212,175,55,0.58);
    background: linear-gradient(135deg, #d4af37, #a97815);
    color: #111111;
    font-weight: 900;
    min-height: 48px;
    box-shadow: 0 14px 36px rgba(212,175,55,0.18);
}

div.stButton > button:hover {
    border-color: #ffffff;
    color: #000000;
    box-shadow: 0 0 28px rgba(212,175,55,0.36);
    transform: translateY(-1px);
}

/* Tabs and dataframes */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.055);
    border-radius: 14px;
    border: 1px solid rgba(212,175,55,0.16);
    color: white;
    padding: 10px 16px;
}

[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
}

.stAlert {
    border-radius: 18px;
}

input, textarea {
    border-radius: 14px !important;
}

@media (max-width: 1150px) {
    .modern-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .modern-title {
        font-size: 36px;
    }
}

@media (max-width: 700px) {
    .modern-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# GİRİŞ
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("IQIBLA Türkiye Panel")
    st.subheader("Şifreli Giriş")
    pw = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Şifre yanlış.")
    st.info("Varsayılan şifre: 1234")
    st.stop()

# =========================
# YARDIMCI FONKSİYONLAR
# =========================
def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).lower().strip()
    tr = str.maketrans({
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u"
    })
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def to_float(value) -> float:
    if value is None or pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    s = (
        s.replace("TL", "")
        .replace("TRY", "")
        .replace("₺", "")
        .replace("%", "")
        .replace('"', "")
        .replace("\xa0", "")
        .replace(" ", "")
    )
    if s.lower() in {"-", "nan", "none", "null", "n/a"}:
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
        if len(parts) > 1 and all(p.isdigit() for p in parts) and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
    try:
        return float(s)
    except Exception:
        cleaned = re.sub(r"[^0-9.\-]", "", s)
        try:
            return float(cleaned)
        except Exception:
            return 0.0

def money(v: float) -> str:
    return f"{float(v):,.2f} TL"

def safe_divide(a: float, b: float) -> float:
    return float(a) / float(b) if b else 0.0

def clean_sku(value) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).strip().replace(" ", "").replace("'", "")
    s = s.replace("-", "")
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    try:
        if "e+" in s.lower():
            s = str(int(float(s)))
    except Exception:
        pass
    return s

def find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    norm_map = {normalize_text(c): c for c in df.columns}
    for cand in candidates:
        target = normalize_text(cand)
        for norm, raw in norm_map.items():
            if target == norm:
                return raw
    for cand in candidates:
        target = normalize_text(cand)
        for norm, raw in norm_map.items():
            if target and target in norm:
                return raw
    return None

def read_csv_flexible(path: Path) -> tuple[pd.DataFrame, str, str]:
    encodings = ["utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin1"]
    seps = [",", ";", "\t"]
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep, dtype=str, low_memory=False)
                if df.shape[1] > 1:
                    return df, enc, sep
            except Exception:
                pass
    return pd.DataFrame(), "", ""

def read_table_flexible(path: Path) -> tuple[pd.DataFrame, str, str]:
    if path.suffix.lower() in [".xlsx", ".xls"]:
        for skip in [0, 1, 2, 3, 4, 5]:
            try:
                df = pd.read_excel(path, dtype=str, skiprows=skip)
                if df.shape[1] > 1:
                    return df, "excel", f"skiprows={skip}"
            except Exception:
                pass
        return pd.DataFrame(), "", ""
    return read_csv_flexible(path)

def read_shopify_orders(path: Path) -> tuple[pd.DataFrame, str, str]:
    df, enc, sep = read_csv_flexible(path)
    if not df.empty and {"Name", "Created at", "Lineitem name"}.issubset(set(df.columns)):
        return df, enc, sep
    return pd.DataFrame(), "", ""

def read_meta_billing(path: Path) -> pd.DataFrame:
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        header_idx = None
        for i, line in enumerate(lines):
            n = normalize_text(line)
            if "tarih" in n and "tutar" in n and ("para birimi" in n or "odeme" in n or "islem" in n):
                header_idx = i
                break
        if header_idx is not None:
            section = [line for line in lines[header_idx:] if line.strip()]
            rows = list(csv.reader(section))
            if len(rows) >= 2:
                return pd.DataFrame(rows[1:], columns=rows[0])
    except Exception:
        pass
    df, _, _ = read_csv_flexible(path)
    return df

def all_files() -> list[Path]:
    return [
        p for p in sorted(BASE_DIR.glob("*"))
        if p.suffix.lower() in [".csv", ".xlsx", ".xls"] and p.name != "manual_entries.csv"
    ]

def files_for(platform: str) -> list[Path]:
    result = []
    for p in all_files():
        n = normalize_text(p.name)
        if platform == "Shopify":
            if any(x in n for x in ["shopify", "orders export", "fatura ozeti", "zamana gore oturumlar"]):
                result.append(p)
        elif platform == "Trendyol":
            if any(x in n for x in ["trendyol", "urun reklamlari", "magaza raporu", "22 05"]):
                result.append(p)
        elif platform == "Hepsiburada":
            if "hepsiburada" in n:
                result.append(p)
        elif platform == "Kreatif":
            if any(x in n for x in ["adsiz", "kreatif", "creative"]):
                result.append(p)
    return result

def ensure_manual_file():
    if not MANUAL_FILE.exists():
        pd.DataFrame(columns=[
            "date", "platform", "store_name", "product_name",
            "units_sold", "order_count", "total_revenue", "ad_spend", "notes"
        ]).to_csv(MANUAL_FILE, index=False, encoding="utf-8-sig")

def load_manual(platform: Optional[str] = None) -> pd.DataFrame:
    ensure_manual_file()
    df = pd.read_csv(MANUAL_FILE, dtype=str)
    for col in ["units_sold", "order_count", "total_revenue", "ad_spend"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].apply(to_float)
    if platform:
        df = df[df["platform"].astype(str).str.lower() == platform.lower()].copy()
    return df

def manual_form(platform: str):
    with st.expander("✍️ Manuel Günlük Giriş", expanded=False):
        with st.form(f"manual_{platform}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                date = st.date_input("Tarih")
                store = st.text_input("Mağaza/Kanal", value=platform)
                product = st.text_input("Ürün adı")
            with c2:
                units = st.number_input("Satılan ürün adedi", min_value=0, value=0, step=1)
                orders = st.number_input("Sipariş adedi", min_value=0, value=0, step=1)
                revenue = st.number_input("Net ciro / Total Revenue", min_value=0.0, value=0.0, step=100.0)
            with c3:
                ad_spend = st.number_input("Reklam harcaması", min_value=0.0, value=0.0, step=100.0)
                notes = st.text_area("Not")
            if st.form_submit_button("Ekle"):
                df = load_manual()
                row = {
                    "date": str(date), "platform": platform, "store_name": store,
                    "product_name": product, "units_sold": units, "order_count": orders,
                    "total_revenue": revenue, "ad_spend": ad_spend, "notes": notes
                }
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv(MANUAL_FILE, index=False, encoding="utf-8-sig")
                st.success("Manuel veri eklendi.")
                st.rerun()

def load_cost_table(platform: str) -> pd.DataFrame:
    frames = []
    for p in files_for(platform):
        n = normalize_text(p.name)
        if "maliyet" not in n and "cost" not in n:
            continue
        df, _, _ = read_table_flexible(p)
        if df.empty:
            continue
        sku_col = find_col(df, ["SKU", "Barkod", "Barcode", "Stok Kodu"])
        cost_col = find_col(df, ["Maliyet", "Maliyet Alış", "Cost"])
        comm_col = find_col(df, ["Komisyon oran", "Komisyon", "Commission"])
        ship_col = find_col(df, ["Kargo", "Shipping"])
        if not sku_col:
            continue
        out = pd.DataFrame({
            "sku_key": df[sku_col].apply(clean_sku),
            "unit_cost": df[cost_col].apply(to_float) if cost_col else 0.0,
            "commission_rate": df[comm_col].apply(to_float) if comm_col else 0.0,
            "unit_shipping": df[ship_col].apply(to_float) if ship_col else 0.0,
        })
        out["commission_rate"] = out["commission_rate"].apply(lambda x: x / 100 if x > 1 else x)
        frames.append(out)
    if not frames:
        return pd.DataFrame(columns=["sku_key", "unit_cost", "commission_rate", "unit_shipping"])
    res = pd.concat(frames, ignore_index=True)
    return res[res["sku_key"] != ""].drop_duplicates("sku_key", keep="last")

def apply_costs(lines: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    if lines.empty:
        lines["matched_cost"] = []
        lines["gross_profit"] = []
        return lines
    lines = lines.merge(costs, on="sku_key", how="left")
    for col in ["unit_cost", "commission_rate", "unit_shipping"]:
        lines[col] = lines[col].fillna(0.0)
    lines["matched_cost"] = lines["unit_cost"].gt(0)
    lines["gross_profit"] = (
        lines["line_revenue"]
        - ((lines["unit_cost"] + lines["unit_shipping"]) * lines["qty"])
        - (lines["line_revenue"] * lines["commission_rate"])
    )
    return lines

@st.cache_data(show_spinner=False)
def load_shopify():
    order_frames, spend_rows, debug = [], [], []
    for p in files_for("Shopify"):
        n = normalize_text(p.name)
        if "maliyet" in n or "zamana gore" in n or "oturum" in n:
            continue
        if "fatura" in n or "billing" in n:
            df = read_meta_billing(p)
            amount_col = find_col(df, ["Tutar", "Amount", "Total", "Spend", "Harcama"])
            date_col = find_col(df, ["Tarih", "Date"])
            if amount_col:
                tmp = pd.DataFrame({
                    "date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
                    "ad_spend": df[amount_col].apply(to_float),
                    "source_file": p.name
                })
                tmp = tmp[tmp["ad_spend"] > 0]
                spend_rows.append(tmp)
                debug.append({"file": p.name, "type": "meta_spend", "status": "OK", "rows": len(tmp)})
            continue
        df, enc, sep = read_shopify_orders(p)
        if not df.empty:
            df["source_file"] = p.name
            order_frames.append(df)
            debug.append({"file": p.name, "type": "orders", "status": "OK", "rows": len(df)})
        else:
            debug.append({"file": p.name, "type": "unknown", "status": "SKIPPED", "rows": 0})
    raw = pd.concat(order_frames, ignore_index=True) if order_frames else pd.DataFrame()
    costs = load_cost_table("Shopify")
    ads = pd.concat(spend_rows, ignore_index=True) if spend_rows else pd.DataFrame(columns=["date", "ad_spend", "source_file"])
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame(), costs, ads, pd.DataFrame(debug)
    for col in ["Total", "Refunded Amount", "Lineitem quantity", "Lineitem price", "Lineitem discount"]:
        if col not in raw.columns:
            raw[col] = 0.0
        raw[col] = raw[col].apply(to_float)
    for col in ["Cancelled at", "Financial Status", "Lineitem sku", "Lineitem name", "Created at"]:
        if col not in raw.columns:
            raw[col] = ""
    raw["order_name"] = raw["Name"].astype(str)
    raw["order_date"] = pd.to_datetime(raw["Created at"], errors="coerce", utc=True).dt.tz_localize(None)
    raw["cancelled_at"] = pd.to_datetime(raw["Cancelled at"], errors="coerce", utc=True).dt.tz_localize(None)
    raw["financial_status"] = raw["Financial Status"].astype(str).str.lower()
    dedupe_cols = [c for c in ["Name", "Created at", "Lineitem sku", "Lineitem name", "Lineitem quantity", "Lineitem price", "Total"] if c in raw.columns]
    raw = raw.drop_duplicates(subset=dedupe_cols, keep="first")
    orders = raw.groupby("order_name", as_index=False).agg(
        order_date=("order_date", "first"),
        total=("Total", "first"),
        refunded=("Refunded Amount", "first"),
        cancelled_at=("cancelled_at", "first"),
        financial_status=("financial_status", "first"),
        source_file=("source_file", "first")
    )
    orders["is_cancelled"] = orders["cancelled_at"].notna() | orders["financial_status"].isin(["voided", "cancelled", "canceled"])
    orders["net_sales"] = orders["total"] - orders["refunded"]
    orders.loc[orders["is_cancelled"], "net_sales"] = 0.0
    orders["order_count"] = (~orders["is_cancelled"]).astype(int)
    lines = raw.copy()
    lines["sku_key"] = lines["Lineitem sku"].apply(clean_sku)
    lines["product_name"] = lines["Lineitem name"].astype(str)
    lines["qty"] = lines["Lineitem quantity"].apply(to_float)
    lines["line_revenue"] = lines["Lineitem price"].apply(to_float) * lines["qty"] - lines["Lineitem discount"].apply(to_float)
    lines.loc[lines["order_name"].isin(orders.loc[orders["is_cancelled"], "order_name"]), ["qty", "line_revenue"]] = 0.0
    lines = lines[["order_name", "order_date", "sku_key", "product_name", "qty", "line_revenue", "source_file"]].copy()
    return orders, lines, costs, ads, pd.DataFrame(debug)

@st.cache_data(show_spinner=False)
def load_market(platform: str):
    rows, ad_rows, debug = [], [], []
    costs = load_cost_table(platform)
    for p in files_for(platform):
        n = normalize_text(p.name)
        if "maliyet" in n:
            continue
        df, enc, sep = read_table_flexible(p)
        if df.empty:
            debug.append({"file": p.name, "type": "unknown", "status": "ERROR", "rows": 0})
            continue
        if any(x in n for x in ["reklam", "ads", "campaign"]):
            spend_col = find_col(df, ["Harcanan Tutar", "Amount spent", "Spend", "Harcama", "Tutar"])
            rev_col = find_col(df, ["Reklam Geliri", "Total Ad Revenue", "Revenue", "Dönüşüm değeri", "Donusum degeri", "Satış Tutarı", "Satis Tutari"])
            pur_col = find_col(df, ["Alışverişler", "Alisverisler", "Purchases", "Sipariş", "Orders"])
            if spend_col:
                ad_rows.append(pd.DataFrame({
                    "ad_spend": df[spend_col].apply(to_float),
                    "ad_revenue": df[rev_col].apply(to_float) if rev_col else 0.0,
                    "ad_purchases": df[pur_col].apply(to_float) if pur_col else 0.0,
                    "source_file": p.name
                }))
                debug.append({"file": p.name, "type": "ad", "status": "OK", "rows": len(df), "used_col": spend_col})
                continue
        date_col = find_col(df, ["Sipariş Tarihi", "Siparis Tarihi", "Tarih", "Order Date", "Date"])
        order_col = find_col(df, ["Sipariş Numarası", "Siparis Numarasi", "Sipariş No", "Siparis No", "Order Number", "Order", "Paket No"])
        product_col = find_col(df, ["Ürün Adı", "Urun Adi", "Ürün Ad", "Urun Ad", "Product Name", "Product"])
        sku_col = find_col(df, ["Barkod", "Barcode", "SKU", "Stok Kodu", "Merchant SKU"])
        qty_col = find_col(df, ["Adet", "Miktar", "Quantity", "Ürün Adedi", "Urun Adedi", "Satış Miktarı", "Satis Miktari"])
        revenue_col = find_col(df, [
            "Faturalanacak Tutar", "Net Satış Tutarı", "Net Satis Tutari", "Satış Tutarı", "Satis Tutari",
            "Ürün Tutarı", "Urun Tutari", "Sipariş Tutarı", "Siparis Tutari", "Toplam Satış Tutarı",
            "Toplam Satis Tutari", "Mağazanın Brüt Cirosu", "Magazanin Brut Cirosu", "Toplam Brüt Ciro",
            "Toplam Brut Ciro", "Ciro", "Tutar", "Amount", "Revenue"
        ])
        status_col = find_col(df, ["Sipariş Statüsü", "Siparis Statusu", "Durum", "Status"])
        if not revenue_col:
            debug.append({"file": p.name, "type": "skipped", "status": "NO_REVENUE_COLUMN", "rows": len(df)})
            continue
        tmp = pd.DataFrame({
            "order_name": df[order_col].astype(str) if order_col else p.stem,
            "order_date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
            "product_name": df[product_col].astype(str) if product_col else platform + " Product",
            "sku_key": df[sku_col].apply(clean_sku) if sku_col else "",
            "qty": df[qty_col].apply(to_float) if qty_col else 1.0,
            "line_revenue": df[revenue_col].apply(to_float),
            "status": df[status_col].astype(str) if status_col else "",
            "source_file": p.name
        })
        tmp["bad"] = tmp["status"].str.contains("iptal|iade|cancel|return|red", case=False, na=False)
        tmp.loc[tmp["bad"], ["qty", "line_revenue"]] = 0.0
        tmp = tmp[tmp["line_revenue"].fillna(0) >= 0].copy()
        rows.append(tmp)
        debug.append({"file": p.name, "type": "sales", "status": "OK", "rows": len(tmp), "used_col": revenue_col})
    lines = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["order_name", "order_date", "product_name", "sku_key", "qty", "line_revenue", "source_file"])
    ads = pd.concat(ad_rows, ignore_index=True) if ad_rows else pd.DataFrame(columns=["ad_spend", "ad_revenue", "ad_purchases", "source_file"])
    if not lines.empty:
        orders = lines.groupby("order_name", as_index=False).agg(
            order_date=("order_date", "first"),
            net_sales=("line_revenue", "sum"),
            qty=("qty", "sum"),
            source_file=("source_file", "first")
        )
        orders["order_count"] = orders["net_sales"].gt(0).astype(int)
    else:
        orders = pd.DataFrame(columns=["order_name", "order_date", "net_sales", "qty", "source_file", "order_count"])
    return orders, lines, costs, ads, pd.DataFrame(debug)

def platform_data(platform: str):
    if platform == "Shopify":
        orders, lines, costs, ads, debug = load_shopify()
    else:
        orders, lines, costs, ads, debug = load_market(platform)
    lines = apply_costs(lines, costs)
    manual = load_manual(platform)
    manual_rev = manual["total_revenue"].sum() if not manual.empty else 0.0
    manual_orders = manual["order_count"].sum() if not manual.empty else 0.0
    manual_units = manual["units_sold"].sum() if not manual.empty else 0.0
    manual_ad = manual["ad_spend"].sum() if not manual.empty else 0.0
    total_revenue = (orders["net_sales"].sum() if not orders.empty else 0.0) + manual_rev
    order_count = (orders["order_count"].sum() if not orders.empty and "order_count" in orders else 0.0) + manual_orders
    units_sold = (lines["qty"].sum() if not lines.empty else 0.0) + manual_units
    gross_profit = (lines["gross_profit"].sum() if not lines.empty else 0.0) + manual_rev
    ad_spend = (ads["ad_spend"].sum() if not ads.empty and "ad_spend" in ads else 0.0) + manual_ad
    ad_revenue = 0.0 if platform == "Shopify" else (ads["ad_revenue"].sum() if not ads.empty and "ad_revenue" in ads else 0.0)
    metrics = {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "units_sold": units_sold,
        "aov": safe_divide(total_revenue, order_count),
        "gross_profit_before_ads": gross_profit,
        "total_ad_spend": ad_spend,
        "total_ad_revenue": ad_revenue,
        "roas": safe_divide(ad_revenue, ad_spend),
        "net_profit_after_ads": gross_profit - ad_spend,
        "mer": safe_divide(total_revenue, ad_spend),
        "cost_match_rate": float(lines["matched_cost"].mean()) if not lines.empty else 0.0,
    }
    return metrics, orders, lines, ads, manual, debug

def kpi_cards(metrics: dict, show_ad_revenue: bool = True):
    fields = [
        ("Total Revenue", "total_revenue", "money"),
        ("Order Count", "order_count", "int"),
        ("Units Sold", "units_sold", "int"),
        ("AOV", "aov", "money"),
        ("Gross Profit Before Ads", "gross_profit_before_ads", "money"),
        ("Total Ad Spend", "total_ad_spend", "money"),
    ]
    if show_ad_revenue:
        fields.append(("Total Ad Revenue", "total_ad_revenue", "money"))
    fields += [
        ("ROAS", "roas", "ratio"),
        ("Net Profit After Ads", "net_profit_after_ads", "money"),
        ("MER", "mer", "ratio"),
        ("Cost Match Rate", "cost_match_rate", "percent"),
    ]
    for i in range(0, len(fields), 4):
        cols = st.columns(4)
        for col, (label, key, typ) in zip(cols, fields[i:i+4]):
            v = metrics.get(key, 0.0)
            if typ == "money":
                col.metric(label, money(v))
            elif typ == "int":
                col.metric(label, f"{v:,.0f}")
            elif typ == "ratio":
                col.metric(label, f"{v:.2f}" if v else "N/A")
            elif typ == "percent":
                col.metric(label, f"{v:.1%}" if v else "0.0%")

def show_platform(platform: str):
    st.header(platform)
    manual_form(platform)
    metrics, orders, lines, ads, manual, debug = platform_data(platform)
    kpi_cards(metrics, show_ad_revenue=(platform != "Shopify"))
    if platform == "Shopify":
        st.info("Shopify Ad Revenue kullanılmaz. Shopify için sadece Total Ad Spend alınır.")
    t1, t2, t3, t4, t5 = st.tabs(["Satış", "Ürün & Kâr", "Reklam", "Manuel", "Debug"])
    with t1:
        if orders.empty:
            st.warning("Satış verisi okunamadı.")
        else:
            st.dataframe(orders.groupby("source_file", as_index=False).agg(order_count=("order_count", "sum"), total_revenue=("net_sales", "sum")), use_container_width=True, hide_index=True)
            st.dataframe(orders, use_container_width=True, hide_index=True)
    with t2:
        if lines.empty:
            st.info("Ürün satırı yok.")
        else:
            product = lines.groupby(["product_name", "sku_key"], as_index=False).agg(
                units_sold=("qty", "sum"),
                revenue=("line_revenue", "sum"),
                gross_profit=("gross_profit", "sum"),
                matched_cost=("matched_cost", "max")
            )
            st.dataframe(product.sort_values("revenue", ascending=False), use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(ads, use_container_width=True, hide_index=True)
    with t4:
        st.dataframe(manual, use_container_width=True, hide_index=True)
    with t5:
        st.dataframe(debug, use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame([metrics]), use_container_width=True, hide_index=True)

def show_ai():
    st.header("Yapay Zeka")
    s, *_ = platform_data("Shopify")
    t, *_ = platform_data("Trendyol")
    h, *_ = platform_data("Hepsiburada")
    total_revenue = s["total_revenue"] + t["total_revenue"] + h["total_revenue"]
    total_ad_spend = s["total_ad_spend"] + t["total_ad_spend"] + h["total_ad_spend"]
    total_ad_revenue = t["total_ad_revenue"] + h["total_ad_revenue"]
    gross_profit = s["gross_profit_before_ads"] + t["gross_profit_before_ads"] + h["gross_profit_before_ads"]
    order_count = s["order_count"] + t["order_count"] + h["order_count"]
    units_sold = s["units_sold"] + t["units_sold"] + h["units_sold"]
    metrics = {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "units_sold": units_sold,
        "aov": safe_divide(total_revenue, order_count),
        "gross_profit_before_ads": gross_profit,
        "total_ad_spend": total_ad_spend,
        "total_ad_revenue": total_ad_revenue,
        "roas": safe_divide(total_ad_revenue, total_ad_spend),
        "net_profit_after_ads": gross_profit - total_ad_spend,
        "mer": safe_divide(total_revenue, total_ad_spend),
        "cost_match_rate": 0.0,
    }
    kpi_cards(metrics)
    summary = pd.DataFrame([
        {"platform": "Shopify", **s, "rule": "Shopify Ad Revenue kullanılmaz"},
        {"platform": "Trendyol", **t, "rule": "Trendyol dahil"},
        {"platform": "Hepsiburada", **h, "rule": "Hepsiburada dahil"},
    ])
    st.dataframe(summary, use_container_width=True, hide_index=True)
    if st.button("Yorumu üret"):
        st.markdown(f"""
**Toplam ciro:** {money(total_revenue)}  
**Toplam reklam harcaması:** {money(total_ad_spend)}  
**Net kâr:** {money(gross_profit - total_ad_spend)}  
**MER:** {safe_divide(total_revenue, total_ad_spend):.2f}  
**ROAS:** {safe_divide(total_ad_revenue, total_ad_spend):.2f}

Kanal katkısı:
- Shopify: {money(s["total_revenue"])}
- Trendyol: {money(t["total_revenue"])}
- Hepsiburada: {money(h["total_revenue"])}

Not: Shopify Ad Revenue toplama katılmadı.
""")


# =========================
# UYGULAMA — MODERN TEK SAYFA NAVİGASYON
# =========================

if "active_page" not in st.session_state:
    st.session_state.active_page = "Ana Sayfa"

def set_page(name: str):
    st.session_state.active_page = name
    st.rerun()

st.markdown("""
<div class="modern-hero">
    <div class="modern-chip">⚡ IQIBLA TÜRKİYE • SMARTEK360</div>
    <div class="modern-title">Modern E-Ticaret<br>Kontrol Merkezi</div>
    <div class="modern-subtitle">
        Trendyol, Shopify, Hepsiburada, Kreatif Takibi ve Yapay Zeka raporlarını tek ekranda yönet.
        Yan menü yok; aşağıdaki kartlara basarak sayfalar arasında geçiş yap.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
n1, n2, n3, n4, n5, n6 = st.columns(6)
with n1:
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        set_page("Ana Sayfa")
with n2:
    if st.button("🟠 Trendyol", use_container_width=True):
        set_page("Trendyol")
with n3:
    if st.button("🟣 Shopify", use_container_width=True):
        set_page("Shopify")
with n4:
    if st.button("🔵 Hepsiburada", use_container_width=True):
        set_page("Hepsiburada")
with n5:
    if st.button("🎨 Kreatif", use_container_width=True):
        set_page("Kreatif")
with n6:
    if st.button("🤖 Yapay Zeka", use_container_width=True):
        set_page("Yapay Zeka")
st.markdown('</div>', unsafe_allow_html=True)

page = st.session_state.active_page

if page == "Ana Sayfa":
    st.markdown("""
    <div class="modern-grid">
        <div class="modern-card">
            <div class="modern-icon">🟠</div>
            <h3>Trendyol</h3>
            <p>Sipariş, ciro, ürün adedi, reklam harcaması ve manuel mağaza girişi.</p>
        </div>
        <div class="modern-card">
            <div class="modern-icon">🟣</div>
            <h3>Shopify</h3>
            <p>Shopify Total Revenue, Meta harcaması, maliyet ve kâr analizi.</p>
        </div>
        <div class="modern-card">
            <div class="modern-icon">🔵</div>
            <h3>Hepsiburada</h3>
            <p>Hepsiburada satış raporu, ürün performansı ve reklam verileri.</p>
        </div>
        <div class="modern-card">
            <div class="modern-icon">🎨</div>
            <h3>Kreatif</h3>
            <p>Kreatif raporları ve Meta performansını ayrı analiz et.</p>
        </div>
        <div class="modern-card">
            <div class="modern-icon">🤖</div>
            <h3>Yapay Zeka</h3>
            <p>Toplam ciro, reklam harcaması, kârlılık ve kanal katkısını yorumla.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Aktif Modül", "5")
    k2.metric("Navigasyon", "Kartlı")
    k3.metric("Manuel Giriş", "Aktif")
    k4.metric("Veri Formatı", "CSV / XLSX")

    st.subheader("Bulunan Veri Dosyaları")
    st.dataframe(
        pd.DataFrame({"dosya": [p.name for p in all_files()]}),
        use_container_width=True,
        hide_index=True
    )

elif page == "Trendyol":
    show_platform("Trendyol")

elif page == "Shopify":
    show_platform("Shopify")

elif page == "Hepsiburada":
    show_platform("Hepsiburada")

elif page == "Kreatif":
    st.header("Kreatif")
    st.info("Kreatif dosyaları ana dizinden okunur. Net ciroya dahil edilmez.")
    st.dataframe(
        pd.DataFrame({"kreatif_dosyaları": [p.name for p in files_for("Kreatif")]}),
        use_container_width=True,
        hide_index=True
    )

elif page == "Yapay Zeka":
    show_ai()
