
from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st


# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="IQIBLA Türkiye Panel", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
MANUAL_FILE = BASE_DIR / "manual_entries.csv"
PASSWORD = "1234"

PLATFORMS = ["Trendyol", "Shopify", "Hepsiburada"]
PAGES = ["Ana Sayfa", "Trendyol", "Shopify", "Hepsiburada", "Kreatif", "Yapay Zeka"]


# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(212,175,55,0.20), transparent 25%),
        radial-gradient(circle at 86% 12%, rgba(255,255,255,0.07), transparent 23%),
        linear-gradient(135deg, #050505 0%, #101010 48%, #050505 100%);
    color: #ffffff;
}

header { visibility: hidden; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 3rem; }

[data-testid="stSidebar"] { display: none; }

.hero {
    background:
        linear-gradient(135deg, rgba(14,14,14,0.94), rgba(30,30,30,0.78)),
        radial-gradient(circle at 92% 10%, rgba(212,175,55,0.25), transparent 34%);
    border: 1px solid rgba(212,175,55,0.30);
    box-shadow: 0 28px 95px rgba(0,0,0,0.55);
    border-radius: 34px;
    padding: 34px 38px;
    margin-bottom: 20px;
}

.chip {
    display: inline-flex;
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

.title {
    color: #ffffff;
    font-size: 46px;
    font-weight: 950;
    letter-spacing: -1px;
    line-height: 1.06;
    margin-bottom: 10px;
}

.subtitle {
    color: rgba(255,255,255,0.72);
    font-size: 16px;
    line-height: 1.6;
    max-width: 960px;
}

.nav {
    background: rgba(255,255,255,0.048);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 28px;
    padding: 16px;
    margin-bottom: 22px;
    box-shadow: 0 18px 48px rgba(0,0,0,0.24);
}

.card {
    background: rgba(255,255,255,0.058);
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 26px;
    padding: 20px;
    min-height: 150px;
    box-shadow: 0 18px 48px rgba(0,0,0,0.24);
}

.card h3 { color: #fff; font-size: 20px; font-weight: 850; margin: 6px 0 8px 0; }
.card p { color: rgba(255,255,255,0.68); font-size: 13px; line-height: 1.46; margin: 0; }

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.060);
    border: 1px solid rgba(212,175,55,0.20);
    border-radius: 20px;
    padding: 16px;
    box-shadow: 0 16px 38px rgba(0,0,0,0.22);
}

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
}

[data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; }
.stAlert { border-radius: 18px; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
        <div class="chip">IQIBLA TÜRKİYE</div>
        <div class="title">E-Ticaret Paneli</div>
        <div class="subtitle">Giriş yaptıktan sonra Trendyol, Shopify, Hepsiburada, Kreatif ve Yapay Zeka sayfalarını aynı ekranda butonlarla değiştirebilirsin.</div>
    </div>
    """, unsafe_allow_html=True)
    pw = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Şifre yanlış.")
    st.info("Varsayılan şifre: 1234")
    st.stop()


# =========================================================
# HELPERS
# =========================================================
def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).lower().strip()
    s = s.translate(str.maketrans({
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u",
    }))
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
        s.replace("TL", "").replace("TRY", "").replace("₺", "")
        .replace("%", "").replace('"', "").replace("\xa0", "").replace(" ", "")
    )
    if s.lower() in {"-", "nan", "none", "null", "n/a"}:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 1 and all(p.isdigit() for p in parts) and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
    try:
        return float(s)
    except Exception:
        try:
            return float(re.sub(r"[^0-9.\-]", "", s))
        except Exception:
            return 0.0


def money(v: float) -> str:
    return f"{float(v):,.2f} TL"


def safe_divide(a: float, b: float) -> float:
    return float(a) / float(b) if b else 0.0


def clean_sku(value) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).strip().replace(" ", "").replace("'", "").replace("-", "")
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


def read_uploaded_file(uploaded) -> pd.DataFrame:
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith((".xlsx", ".xls")):
        for skip in [0, 1, 2, 3, 4, 5]:
            try:
                df = pd.read_excel(io.BytesIO(data), dtype=str, skiprows=skip)
                if df.shape[1] > 1:
                    return df
            except Exception:
                pass
        return pd.DataFrame()

    for enc in ["utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin1"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(io.BytesIO(data), encoding=enc, sep=sep, dtype=str, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                pass
    return pd.DataFrame()


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
    with st.expander("✍️ Manuel günlük giriş", expanded=False):
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
                    "date": str(date),
                    "platform": platform,
                    "store_name": store,
                    "product_name": product,
                    "units_sold": units,
                    "order_count": orders,
                    "total_revenue": revenue,
                    "ad_spend": ad_spend,
                    "notes": notes,
                }
                pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MANUAL_FILE, index=False, encoding="utf-8-sig")
                st.success("Manuel veri eklendi.")
                st.rerun()


def init_upload_state(platform: str):
    for kind in ["sales", "cost", "ads"]:
        st.session_state.setdefault(f"{platform}_{kind}_files", [])


def save_uploads(platform: str, kind: str, files):
    if files is not None:
        st.session_state[f"{platform}_{kind}_files"] = [
            {"name": f.name, "bytes": f.getvalue()} for f in files
        ]


def files_from_state(platform: str, kind: str):
    out = []
    for item in st.session_state.get(f"{platform}_{kind}_files", []):
        class Obj:
            pass
        o = Obj()
        o.name = item["name"]
        o.getvalue = lambda b=item["bytes"]: b
        out.append(o)
    return out


def upload_boxes(platform: str):
    init_upload_state(platform)

    st.subheader("Dosya Yükleme")
    st.warning("Verilerin yanlış yere gitmemesi için dosyaları artık ayrı kutulara yüklüyorsun. Satış dosyası satışa, maliyet dosyası maliyete, reklam dosyası reklama gider.")

    c1, c2, c3 = st.columns(3)
    with c1:
        sales = st.file_uploader(
            f"{platform} satış / sipariş dosyaları",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_{platform}_sales"
        )
        if sales:
            save_uploads(platform, "sales", sales)
    with c2:
        cost = st.file_uploader(
            f"{platform} maliyet dosyaları",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_{platform}_cost"
        )
        if cost:
            save_uploads(platform, "cost", cost)
    with c3:
        ads = st.file_uploader(
            f"{platform} reklam harcaması dosyaları",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_{platform}_ads"
        )
        if ads:
            save_uploads(platform, "ads", ads)

    loaded = {
        "Satış": len(st.session_state.get(f"{platform}_sales_files", [])),
        "Maliyet": len(st.session_state.get(f"{platform}_cost_files", [])),
        "Reklam": len(st.session_state.get(f"{platform}_ads_files", [])),
    }
    st.caption(f"Yüklü dosya sayısı: {loaded}")


# =========================================================
# DATA LOADERS
# =========================================================
def load_cost_table(platform: str) -> pd.DataFrame:
    frames = []
    for f in files_from_state(platform, "cost"):
        df = read_uploaded_file(f)
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


def load_ads(platform: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    debug = []
    for f in files_from_state(platform, "ads"):
        df = read_uploaded_file(f)
        if df.empty:
            debug.append({"file": f.name, "type": "ads", "status": "ERROR", "reason": "okunamadı"})
            continue
        spend_col = find_col(df, ["Harcanan Tutar", "Amount spent", "Spend", "Harcama", "Tutar", "Amount"])
        rev_col = find_col(df, ["Reklam Geliri", "Total Ad Revenue", "Revenue", "Dönüşüm değeri", "Donusum degeri", "Satış Tutarı", "Satis Tutari"])
        pur_col = find_col(df, ["Alışverişler", "Alisverisler", "Purchases", "Sipariş", "Orders"])
        date_col = find_col(df, ["Tarih", "Date", "Day"])
        if not spend_col:
            debug.append({"file": f.name, "type": "ads", "status": "NO_SPEND_COLUMN", "columns": ", ".join(map(str, df.columns[:12]))})
            continue
        out = pd.DataFrame({
            "date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
            "ad_spend": df[spend_col].apply(to_float),
            "ad_revenue": df[rev_col].apply(to_float) if rev_col else 0.0,
            "ad_purchases": df[pur_col].apply(to_float) if pur_col else 0.0,
            "source_file": f.name,
        })
        out = out[(out["ad_spend"] > 0) | (out["ad_revenue"] > 0) | (out["ad_purchases"] > 0)].copy()
        frames.append(out)
        debug.append({"file": f.name, "type": "ads", "status": "OK", "rows": len(out), "spend_col": spend_col, "revenue_col": rev_col or ""})
    ads = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "ad_spend", "ad_revenue", "ad_purchases", "source_file"])
    return ads, pd.DataFrame(debug)


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


def load_shopify_sales() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_frames = []
    debug = []

    for f in files_from_state("Shopify", "sales"):
        df = read_uploaded_file(f)
        if df.empty or not {"Name", "Created at", "Lineitem name"}.issubset(set(df.columns)):
            debug.append({"file": f.name, "type": "shopify_sales", "status": "ERROR", "reason": "Shopify sipariş formatı değil"})
            continue
        df["source_file"] = f.name
        raw_frames.append(df)
        debug.append({"file": f.name, "type": "shopify_sales", "status": "OK", "rows": len(df)})

    raw = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(debug)

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
        source_file=("source_file", "first"),
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

    return orders, lines, pd.DataFrame(debug)


def load_market_sales(platform: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = []
    debug = []

    for f in files_from_state(platform, "sales"):
        df = read_uploaded_file(f)
        if df.empty:
            debug.append({"file": f.name, "type": "sales", "status": "ERROR", "reason": "okunamadı"})
            continue

        date_col = find_col(df, ["Sipariş Tarihi", "Siparis Tarihi", "Tarih", "Order Date", "Date"])
        order_col = find_col(df, ["Sipariş Numarası", "Siparis Numarasi", "Sipariş No", "Siparis No", "Order Number", "Order", "Paket No"])
        product_col = find_col(df, ["Ürün Adı", "Urun Adi", "Ürün Ad", "Urun Ad", "Product Name", "Product"])
        sku_col = find_col(df, ["Barkod", "Barcode", "SKU", "Stok Kodu", "Merchant SKU"])
        qty_col = find_col(df, ["Adet", "Miktar", "Quantity", "Ürün Adedi", "Urun Adedi", "Satış Miktarı", "Satis Miktari"])
        revenue_col = find_col(df, [
            "Faturalanacak Tutar", "Net Satış Tutarı", "Net Satis Tutari",
            "Satış Tutarı", "Satis Tutari", "Ürün Tutarı", "Urun Tutari",
            "Sipariş Tutarı", "Siparis Tutari", "Toplam Satış Tutarı",
            "Toplam Satis Tutari", "Mağazanın Brüt Cirosu", "Magazanin Brut Cirosu",
            "Toplam Brüt Ciro", "Toplam Brut Ciro", "Ciro", "Tutar", "Amount", "Revenue"
        ])
        status_col = find_col(df, ["Sipariş Statüsü", "Siparis Statusu", "Durum", "Status"])

        if not revenue_col:
            debug.append({"file": f.name, "type": "sales", "status": "NO_REVENUE_COLUMN", "columns": ", ".join(map(str, df.columns[:15]))})
            continue

        out = pd.DataFrame({
            "order_name": df[order_col].astype(str) if order_col else f.name,
            "order_date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
            "product_name": df[product_col].astype(str) if product_col else platform + " Product",
            "sku_key": df[sku_col].apply(clean_sku) if sku_col else "",
            "qty": df[qty_col].apply(to_float) if qty_col else 1.0,
            "line_revenue": df[revenue_col].apply(to_float),
            "status": df[status_col].astype(str) if status_col else "",
            "source_file": f.name,
        })
        out["bad"] = out["status"].str.contains("iptal|iade|cancel|return|red", case=False, na=False)
        out.loc[out["bad"], ["qty", "line_revenue"]] = 0.0
        out = out[out["line_revenue"].fillna(0) >= 0].copy()
        frames.append(out)
        debug.append({"file": f.name, "type": "sales", "status": "OK", "rows": len(out), "revenue_col": revenue_col})

    lines = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["order_name", "order_date", "product_name", "sku_key", "qty", "line_revenue", "source_file"])
    if not lines.empty:
        orders = lines.groupby("order_name", as_index=False).agg(
            order_date=("order_date", "first"),
            net_sales=("line_revenue", "sum"),
            qty=("qty", "sum"),
            source_file=("source_file", "first"),
        )
        orders["order_count"] = orders["net_sales"].gt(0).astype(int)
    else:
        orders = pd.DataFrame(columns=["order_name", "order_date", "net_sales", "qty", "source_file", "order_count"])

    return orders, lines, pd.DataFrame(debug)


def platform_data(platform: str):
    if platform == "Shopify":
        orders, lines, debug_sales = load_shopify_sales()
    else:
        orders, lines, debug_sales = load_market_sales(platform)

    costs = load_cost_table(platform)
    ads, debug_ads = load_ads(platform)
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

    # Shopify Ad Revenue yanlış olduğu için kullanılmaz.
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

    debug = pd.concat([debug_sales, debug_ads], ignore_index=True) if not debug_sales.empty or not debug_ads.empty else pd.DataFrame()
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
    upload_boxes(platform)
    manual_form(platform)

    metrics, orders, lines, ads, manual, debug = platform_data(platform)
    kpi_cards(metrics, show_ad_revenue=(platform != "Shopify"))

    if platform == "Shopify":
        st.info("Shopify Ad Revenue kullanılmaz. Shopify için sadece Total Revenue ve Total Ad Spend alınır.")

    t1, t2, t3, t4, t5 = st.tabs(["Satış", "Ürün & Kâr", "Reklam", "Manuel", "Debug"])
    with t1:
        if orders.empty:
            st.warning("Satış verisi yok. Satış dosyasını satış kutusuna yükle.")
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
    st.header("Yapay Zeka / Toplam Rapor")

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

    if st.button("Yorumu üret", use_container_width=True):
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


# =========================================================
# APP LAYOUT
# =========================================================
if "active_page" not in st.session_state:
    st.session_state.active_page = "Ana Sayfa"

def set_page(name: str):
    st.session_state.active_page = name
    st.rerun()

st.markdown("""
<div class="hero">
    <div class="chip">IQIBLA TÜRKİYE • SMARTEK360</div>
    <div class="title">Modern E-Ticaret<br>Kontrol Merkezi</div>
    <div class="subtitle">
        Dosyaların yanlış yere gitmemesi için artık her panelde satış, maliyet ve reklam dosyalarını ayrı kutulara yüklüyorsun.
        Yan menü yok; üstteki butonlarla sayfa değiştir.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="nav">', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        set_page("Ana Sayfa")
with c2:
    if st.button("🟠 Trendyol", use_container_width=True):
        set_page("Trendyol")
with c3:
    if st.button("🟣 Shopify", use_container_width=True):
        set_page("Shopify")
with c4:
    if st.button("🔵 Hepsiburada", use_container_width=True):
        set_page("Hepsiburada")
with c5:
    if st.button("🎨 Kreatif", use_container_width=True):
        set_page("Kreatif")
with c6:
    if st.button("🤖 Yapay Zeka", use_container_width=True):
        set_page("Yapay Zeka")
st.markdown('</div>', unsafe_allow_html=True)

page = st.session_state.active_page

if page == "Ana Sayfa":
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="card"><h3>Dosyalar artık karışmaz</h3><p>Satış, maliyet ve reklam dosyaları ayrı kutulara yüklenir.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><h3>Manuel günlük giriş</h3><p>Mağaza bazında ürün adedi, sipariş, ciro ve reklam harcaması eklenir.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="card"><h3>Yapay Zeka toplamı</h3><p>Shopify + Trendyol + Hepsiburada ciro toplamı yapılır. Shopify Ad Revenue kullanılmaz.</p></div>', unsafe_allow_html=True)

    st.divider()
    st.info("Veri okumayı düzeltmek için eski dosya adı tahmin sistemi kaldırıldı. Her panelin kendi dosya yükleme kutusu var.")

elif page in PLATFORMS:
    show_platform(page)

elif page == "Kreatif":
    st.header("Kreatif")
    upload_boxes("Kreatif")
    ads, debug = load_ads("Kreatif")
    manual_form("Kreatif")
    manual = load_manual("Kreatif")
    total_spend = (ads["ad_spend"].sum() if not ads.empty else 0.0) + (manual["ad_spend"].sum() if not manual.empty else 0.0)
    total_revenue = ads["ad_revenue"].sum() if not ads.empty else 0.0
    kpi_cards({
        "total_revenue": 0.0,
        "order_count": 0.0,
        "units_sold": 0.0,
        "aov": 0.0,
        "gross_profit_before_ads": 0.0,
        "total_ad_spend": total_spend,
        "total_ad_revenue": total_revenue,
        "roas": safe_divide(total_revenue, total_spend),
        "net_profit_after_ads": -total_spend,
        "mer": 0.0,
        "cost_match_rate": 0.0,
    })
    st.warning("Kreatif net ciroya dahil edilmez.")
    st.dataframe(ads, use_container_width=True, hide_index=True)
    st.dataframe(debug, use_container_width=True, hide_index=True)

elif page == "Yapay Zeka":
    show_ai()
