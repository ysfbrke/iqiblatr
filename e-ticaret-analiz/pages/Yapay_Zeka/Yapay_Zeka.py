from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE
# =========================================================
st.set_page_config(page_title="SMARTEK360 | Yapay Zeka Analiz", layout="wide")

# Ana sayfadan giriş yapılmadan açılmasın.
if "logged_in" not in st.session_state or st.session_state.logged_in is not True:
    st.warning("Bu sayfaya erişmek için önce ana sayfadan giriş yapmalısın.")
    st.stop()


# =========================================================
# THEME / UI
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
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1450px; }
        .ai-hero {
            background: rgba(8, 8, 8, 0.78);
            border: 1px solid rgba(212, 175, 55, 0.35);
            box-shadow: 0 24px 85px rgba(0,0,0,0.50);
            border-radius: 30px;
            padding: 28px 34px;
            backdrop-filter: blur(16px);
            margin-bottom: 22px;
        }
        .ai-title { color: #ffffff; font-size: 42px; font-weight: 850; letter-spacing: 0.4px; margin-bottom: 6px; }
        .ai-subtitle { color: rgba(255,255,255,0.72); font-size: 16px; line-height: 1.5; }
        .gold-line { width: 150px; height: 3px; background: linear-gradient(90deg, transparent, #d4af37, transparent); margin-top: 18px; border-radius: 99px; }
        .assistant-box {
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(212,175,55,0.22);
            border-radius: 24px;
            padding: 20px;
            margin-top: 10px;
            margin-bottom: 18px;
        }
        div.stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(212,175,55,0.55);
            background: linear-gradient(135deg, #d4af37, #9d7417);
            color: #111111;
            font-weight: 800;
        }
        div.stButton > button:hover {
            border-color: #ffffff;
            color: #000000;
            box-shadow: 0 0 22px rgba(212,175,55,0.35);
        }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ai-hero">
        <div class="ai-title">🤖 SMARTEK360: Yapay Zeka Analiz Paneli</div>
        <div class="ai-subtitle">
            Shopify, Trendyol, Hepsiburada ve Kreatif Takibi verilerini tek bir merkezi modelde toplar.
            Satış/kâr hesapları ile kreatif yorumunu birbirinden ayırır; böylece Meta/Kreatif harcaması iki kez sayılmaz.
        </div>
        <div class="gold-line"></div>
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
    # Normal yapı: e-ticaret-analiz/pages/Yapay_Zeka/Yapay_Zeka.py
    try:
        return Path(__file__).resolve().parents[2]
    except Exception:
        return Path(__file__).resolve().parent


PROJECT_DIR = find_project_root()
PAGES_DIR = PROJECT_DIR / "pages"
SHOPIFY_DIR = PAGES_DIR / "Shopify_app"
TRENDYOL_DIR = PAGES_DIR / "smartek_app"
HEPSIBURADA_DIR = PAGES_DIR / "Hepsiburada_app"
KREATIF_DIR = PAGES_DIR / "Kreatif_Takip"
AI_DIR = Path(__file__).resolve().parent


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
        "â": "a", "î": "i", "û": "u",
    })
    text = text.translate(tr_map)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_text(value) -> str:
    return normalize_text(value).replace(" ", "")


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

    if s.lower() in {"-", "nan", "none", "null", "sürekli", "surekli", "henüzfaturakesilmemiştir.", "henüzfaturakesilmemistir."}:
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
        if len(parts) > 1 and all(part.isdigit() for part in parts):
            if all(len(part) == 3 for part in parts[1:]):
                s = "".join(parts)

    try:
        return float(s)
    except Exception:
        cleaned = re.sub(r"[^0-9.\-]", "", s)
        try:
            return float(cleaned)
        except Exception:
            return 0.0


def normalize_rate(value) -> float:
    rate = to_float(value)
    return rate / 100.0 if rate > 1 else rate


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


def find_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    if df is None or df.empty:
        return None
    normalized_cols = {normalize_text(c): c for c in df.columns}
    normalized_candidates = [normalize_text(c) for c in candidates]

    for target in normalized_candidates:
        for norm_col, raw_col in normalized_cols.items():
            if target == norm_col:
                return raw_col

    for target in normalized_candidates:
        for norm_col, raw_col in normalized_cols.items():
            if target and target in norm_col:
                return raw_col

    compact_cols = {compact_text(c): c for c in df.columns}
    compact_candidates = [c.replace(" ", "") for c in normalized_candidates]
    for target in compact_candidates:
        for norm_col, raw_col in compact_cols.items():
            if target and (target == norm_col or target in norm_col):
                return raw_col
    return None


def safe_divide(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def money(value: float) -> str:
    return f"{value:,.2f} TL"


def pct(value: float) -> str:
    return f"%{value:,.1f}"


def date_str(ts) -> str:
    parsed = pd.to_datetime(ts, errors="coerce")
    if pd.isna(parsed):
        return "-"
    return str(pd.Timestamp(parsed).date())


def list_data_files(folder: Path, include_excel: bool = True) -> list[Path]:
    if not folder.exists():
        return []
    suffixes = {".csv"}
    if include_excel:
        suffixes.update({".xlsx", ".xls"})
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in suffixes])


def read_csv_flexible(path: Path | str, *, skiprows: int = 0) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "iso-8859-9", "cp1254", "latin1"]
    seps = [",", ";", "\t"]
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep, dtype=str, low_memory=False, skiprows=skiprows)
                if df.shape[1] > 1:
                    df = df.loc[:, ~df.columns.duplicated()].copy()
                    return df
            except Exception:
                continue
    return pd.DataFrame()


def read_table_flexible(path: Path | str, *, skiprows: int = 0) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return read_csv_flexible(p, skiprows=skiprows)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        try:
            df = pd.read_excel(p, dtype=str, skiprows=skiprows)
            if df.shape[1] > 1:
                df = df.loc[:, ~df.columns.duplicated()].copy()
                return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def read_table_try_skiprows(path: Path | str, max_skip: int = 2) -> pd.DataFrame:
    best = pd.DataFrame()
    best_score = -1
    for skip in range(max_skip + 1):
        df = read_table_flexible(path, skiprows=skip)
        if df.empty:
            continue
        score = sum(1 for c in df.columns if normalize_text(c)) + df.shape[1]
        if score > best_score:
            best = df
            best_score = score
    return best


def source_files_from_df(df: pd.DataFrame) -> str:
    if df is None or df.empty or "source_file" not in df.columns:
        return ""
    return ", ".join(sorted(df["source_file"].dropna().astype(str).unique().tolist())[:12])


# =========================================================
# MANUAL PRODUCT / STOCK MAP
# =========================================================
MANUAL_INVENTORY = {
    "j01t green": 102,
    "j01t camel": 102,
    "j01 blue": 60,
    "j01 grey": 47,
    "j03 pro titanium": 541,
    "black j01t": 266,
    "j01t black": 266,
    "salat counter": 35,
    "premium black gold 22mm": 9,
    "premium rose gold 20mm": 7,
    "premium black gray 22mm": 7,
    "j01 pink": 120,
    "j01 green": 120,
    "j01 black": 160,
}

MANUAL_PRODUCT_SKU_MAP = {
    "zikr jood 3 pro gri": "6970126922132",
    "zikr jood 3 pro siyah": "6970126922125",
    "zikr ring m02 premium altin gul 20 mm": "6970126922170",
    "zikr ring m02 premium rose altin 20 mm": "6970126921630",
    "zikr ring jood gri": "970126921944",
    "zikr ring jood mavi": "970126921920",
    "zikr ring jood pembe": "970126921951",
    "zikr ring jood siyah": "970126921913",
    "zikr ring jood yesil": "970126921937",
    "zikr ring jood lite kum beji": "970126922903",
    "zikr ring jood lite siyah": "970126922880",
    "zikr ring jood lite yesil": "970126922910",
}

ZERO_COST_PRODUCT_NAMES = {"kapida odeme ucreti", "hediye kutusu"}


def infer_inventory_key(product_name: str) -> str:
    text = normalize_text(product_name)
    if "jood lite" in text or "j01t" in text:
        if "yesil" in text or "green" in text:
            return "j01t green"
        if "camel" in text or "kum" in text or "bej" in text:
            return "j01t camel"
        if "siyah" in text or "black" in text:
            return "j01t black"
    if "jood 3 pro" in text or "j03 pro" in text:
        if "titanyum" in text or "titanium" in text or "gri" in text:
            return "j03 pro titanium"
    if "rekat" in text or "salat" in text or "salavatmatik" in text:
        return "salat counter"
    if "premium" in text:
        if "rose" in text and "20" in text:
            return "premium rose gold 20mm"
        if "black" in text and "gold" in text and "22" in text:
            return "premium black gold 22mm"
        if ("gray" in text or "grey" in text or "gri" in text) and "22" in text:
            return "premium black gray 22mm"
    if "jood" in text or "j01" in text:
        if "pembe" in text or "pink" in text:
            return "j01 pink"
        if "yesil" in text or "green" in text:
            return "j01 green"
        if "siyah" in text or "black" in text:
            return "j01 black"
        if "mavi" in text or "blue" in text:
            return "j01 blue"
        if "gri" in text or "grey" in text or "gray" in text:
            return "j01 grey"
    return ""


def manual_sku_for_product(product_name: str) -> str:
    return MANUAL_PRODUCT_SKU_MAP.get(normalize_text(product_name), "")


def is_zero_cost_product(product_name: str) -> bool:
    return normalize_text(product_name) in ZERO_COST_PRODUCT_NAMES


# =========================================================
# COST TABLES
# =========================================================
@st.cache_data(show_spinner=False)
def load_cost_table(folder: Path, platform_name: str) -> pd.DataFrame:
    files = [p for p in list_data_files(folder) if "maliyet" in normalize_text(p.name) or "cost" in normalize_text(p.name)]
    if not files:
        return pd.DataFrame(columns=["sku", "unit_cost", "commission_rate", "shipping_cost", "vat_rate", "source_file"])

    path = files[0]
    df = read_table_try_skiprows(path, max_skip=1)
    if df.empty:
        return pd.DataFrame(columns=["sku", "unit_cost", "commission_rate", "shipping_cost", "vat_rate", "source_file"])

    sku_col = find_col(df, ["SKU", "Barkod", "Barcode"])
    cost_col = find_col(df, ["Maliyet", "Cost", "Alis", "Alış"])
    comm_col = find_col(df, ["Komisyon oran", "Komisyon", "Commission Rate", "Commission"])
    ship_col = find_col(df, ["Kargo", "Shipping"])
    vat_col = find_col(df, ["KDV", "VAT"])
    if not sku_col:
        return pd.DataFrame(columns=["sku", "unit_cost", "commission_rate", "shipping_cost", "vat_rate", "source_file"])

    out = pd.DataFrame({
        "sku": df[sku_col].apply(clean_sku),
        "unit_cost": df[cost_col].apply(to_float) if cost_col else 0.0,
        "commission_rate": df[comm_col].apply(normalize_rate) if comm_col else 0.0,
        "shipping_cost": df[ship_col].apply(to_float) if ship_col else 0.0,
        "vat_rate": df[vat_col].apply(normalize_rate) if vat_col else 0.0,
        "source_file": path.name,
    })
    out = out[out["sku"] != ""].drop_duplicates("sku", keep="last")
    return out


def apply_costs(lines: pd.DataFrame, costs: pd.DataFrame, platform_name: str) -> pd.DataFrame:
    if lines.empty:
        return lines
    out = lines.copy()
    if not costs.empty:
        out = out.merge(costs[["sku", "unit_cost", "commission_rate", "shipping_cost"]], on="sku", how="left")
    for col in ["unit_cost", "commission_rate", "shipping_cost"]:
        if col not in out.columns:
            out[col] = 0.0
        out[col] = out[col].fillna(0.0)

    if "product_name" in out.columns:
        zero_mask = out["product_name"].apply(is_zero_cost_product)
        out.loc[zero_mask, ["unit_cost", "commission_rate", "shipping_cost"]] = 0.0

    out["gross_profit"] = (
        out["line_revenue"].fillna(0.0)
        - (out["unit_cost"].fillna(0.0) + out["shipping_cost"].fillna(0.0)) * out["qty"].fillna(0.0)
        - out["line_revenue"].fillna(0.0) * out["commission_rate"].fillna(0.0)
    )
    out["cost_matched"] = out["unit_cost"].fillna(0).gt(0) | out["product_name"].apply(is_zero_cost_product)
    return out


# =========================================================
# SHOPIFY LOADERS
# =========================================================
def read_shopify_order_csv_robust(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "iso-8859-9", "latin1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows:
                continue
            header = rows[0]
            header_len = len(header)
            fixed_rows = []
            for raw in rows[1:]:
                if not raw:
                    continue
                row = raw
                if len(row) == 1:
                    try:
                        reparsed = next(csv.reader([row[0]]))
                        if len(reparsed) > 1:
                            row = reparsed
                    except Exception:
                        pass
                if len(row) < header_len:
                    row = row + [""] * (header_len - len(row))
                elif len(row) > header_len:
                    row = row[:header_len]
                fixed_rows.append(row)
            if fixed_rows:
                df = pd.DataFrame(fixed_rows, columns=header)
                return df.loc[:, ~df.columns.duplicated()].copy()
        except Exception:
            continue
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_shopify_sales() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    costs = load_cost_table(SHOPIFY_DIR, "Shopify")
    order_frames = []
    line_frames = []
    debug_rows = []

    for path in list_data_files(SHOPIFY_DIR):
        lname = normalize_text(path.name)
        if "maliyet" in lname or "meta" in lname or "facebook" in lname:
            continue
        if "shopify002" in lname or "shopify003" in lname or "shopify004" in lname:
            continue
        if "shopify" not in lname:
            continue

        df = read_shopify_order_csv_robust(path) if path.suffix.lower() == ".csv" else read_table_flexible(path)
        if df.empty:
            debug_rows.append({"platform": "Shopify", "source_file": path.name, "status": "okunamadı", "rows": 0, "note": "Dosya boş veya format tanınmadı."})
            continue

        name_col = find_col(df, ["Name", "Order", "Sipariş"])
        created_col = find_col(df, ["Created at", "Created", "Tarih"])
        total_col = find_col(df, ["Total", "Toplam"])
        refund_col = find_col(df, ["Refunded Amount", "Refund", "İade", "Iade"])
        cancelled_col = find_col(df, ["Cancelled at", "Cancelled"])
        financial_col = find_col(df, ["Financial Status", "Payment Status"])
        product_col = find_col(df, ["Lineitem name", "Product", "Ürün", "Urun"])
        qty_col = find_col(df, ["Lineitem quantity", "Quantity", "Adet"])
        sku_col = find_col(df, ["Lineitem sku", "SKU", "Barkod"])
        price_col = find_col(df, ["Lineitem price", "Price", "Fiyat"])
        discount_col = find_col(df, ["Lineitem discount", "Discount", "İndirim", "Indirim"])

        if not name_col or not created_col or not total_col:
            debug_rows.append({"platform": "Shopify", "source_file": path.name, "status": "atlanıyor", "rows": len(df), "note": "Shopify sipariş kolonları bulunamadı."})
            continue

        order_date = pd.to_datetime(df[created_col], errors="coerce", utc=True).dt.tz_localize(None)
        cancelled_at = pd.to_datetime(df[cancelled_col], errors="coerce", utc=True).dt.tz_localize(None) if cancelled_col else pd.NaT
        financial_status = df[financial_col].fillna("").astype(str).str.lower() if financial_col else pd.Series([""] * len(df))
        is_cancelled = pd.Series(cancelled_at).notna() | financial_status.isin(["voided", "void", "cancelled", "canceled"])

        orders = pd.DataFrame({
            "platform": "Shopify",
            "order_id": df[name_col].astype(str).str.strip(),
            "order_date": order_date,
            "net_sales": df[total_col].apply(to_float),
            "refund": df[refund_col].apply(to_float) if refund_col else 0.0,
            "is_cancelled": is_cancelled,
            "source_file": path.name,
            "order_count": 1.0,
            "data_scope": "order_level",
        })
        orders.loc[orders["is_cancelled"], "net_sales"] = 0.0
        orders["net_sales"] = (orders["net_sales"] - orders["refund"].fillna(0.0)).clip(lower=0.0)
        orders = orders[orders["order_id"].astype(str).str.strip() != ""]
        order_frames.append(orders)

        if product_col:
            qty = df[qty_col].apply(to_float) if qty_col else pd.Series([1.0] * len(df))
            line_price = df[price_col].apply(to_float) if price_col else pd.Series([0.0] * len(df))
            line_discount = df[discount_col].apply(to_float) if discount_col else pd.Series([0.0] * len(df))
            product_name = df[product_col].fillna("").astype(str)
            sku_original = df[sku_col].apply(clean_sku) if sku_col else pd.Series([""] * len(df))
            sku_manual = product_name.apply(manual_sku_for_product)
            sku = sku_manual.where(sku_manual != "", sku_original)
            lines = pd.DataFrame({
                "platform": "Shopify",
                "order_id": df[name_col].astype(str).str.strip(),
                "order_date": order_date,
                "product_name": product_name,
                "sku": sku,
                "qty": qty,
                "line_revenue": line_price * qty - line_discount,
                "source_file": path.name,
                "data_scope": "order_level",
            })
            lines.loc[is_cancelled, ["qty", "line_revenue"]] = 0.0
            lines = lines[lines["order_id"].astype(str).str.strip() != ""]
            line_frames.append(lines)
        debug_rows.append({"platform": "Shopify", "source_file": path.name, "status": "okundu", "rows": len(df), "note": "Sipariş dosyası."})

    orders_all = pd.concat(order_frames, ignore_index=True) if order_frames else pd.DataFrame(columns=["platform", "order_id", "order_date", "net_sales", "source_file", "order_count", "data_scope"])
    lines_all = pd.concat(line_frames, ignore_index=True) if line_frames else pd.DataFrame(columns=["platform", "order_id", "order_date", "product_name", "sku", "qty", "line_revenue", "source_file", "data_scope"])

    if not orders_all.empty:
        orders_all = orders_all.drop_duplicates(subset=["order_id"], keep="first")
    if not lines_all.empty:
        lines_all = lines_all.drop_duplicates(subset=["order_id", "order_date", "product_name", "sku", "qty", "line_revenue"], keep="first")
        lines_all = apply_costs(lines_all, costs, "Shopify")

    return orders_all, lines_all, costs, pd.DataFrame(debug_rows)


# =========================================================
# TRENDYOL LOADERS
# =========================================================
@st.cache_data(show_spinner=False)
def load_trendyol_sales() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    costs = load_cost_table(TRENDYOL_DIR, "Trendyol")
    line_frames = []
    debug_rows = []

    for path in list_data_files(TRENDYOL_DIR):
        lname = normalize_text(path.name)
        if "maliyet" in lname or "manual weekly" in lname or "manual_weekly" in lname or "magaza raporu" in lname or "mağaza raporu" in lname:
            continue
        if "trendyol" not in lname:
            continue
        if not ("tedarikci" in lname or "siparis" in lname or "sipariş" in lname):
            continue

        df = read_table_try_skiprows(path, max_skip=2)
        if df.empty:
            debug_rows.append({"platform": "Trendyol", "source_file": path.name, "status": "okunamadı", "rows": 0, "note": "Dosya boş veya format tanınmadı."})
            continue

        date_col = find_col(df, ["Sipariş Tarihi", "Siparis Tarihi", "Order Date"])
        order_col = find_col(df, ["Sipariş Numarası", "Siparis Numarasi", "Order Number", "Order ID"])
        qty_col = find_col(df, ["Adet", "Quantity", "Qty"])
        status_col = find_col(df, ["Sipariş Statüsü", "Siparis Statusu", "Status"])
        sku_col = find_col(df, ["Barkod", "SKU", "Barcode"])
        product_col = find_col(df, ["Ürün Adı", "Ürün Ad", "Urun Adi", "Urun Ad", "Product"])
        revenue_col = find_col(df, ["Faturalanacak Tutar", "Satış Tutarı", "Satis Tutari", "Revenue", "Total"])

        if not order_col or not revenue_col:
            debug_rows.append({"platform": "Trendyol", "source_file": path.name, "status": "atlanıyor", "rows": len(df), "note": "Sipariş no veya ciro kolonu bulunamadı."})
            continue

        lines = pd.DataFrame({
            "platform": "Trendyol",
            "order_id": df[order_col].astype(str).str.strip(),
            "order_date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
            "product_name": df[product_col].astype(str) if product_col else "",
            "sku": df[sku_col].apply(clean_sku) if sku_col else "",
            "qty": df[qty_col].apply(to_float) if qty_col else 1.0,
            "line_revenue": df[revenue_col].apply(to_float),
            "status": df[status_col].astype(str) if status_col else "",
            "source_file": path.name,
            "data_scope": "order_level",
        })
        returned = lines["status"].str.contains("ade|iptal|cancel|return", case=False, na=False)
        lines.loc[returned, ["qty", "line_revenue"]] = 0.0
        lines = lines[lines["order_id"].astype(str).str.strip() != ""]
        line_frames.append(lines)
        debug_rows.append({"platform": "Trendyol", "source_file": path.name, "status": "okundu", "rows": len(lines), "note": "Sipariş dosyası."})

    lines_all = pd.concat(line_frames, ignore_index=True) if line_frames else pd.DataFrame(columns=["platform", "order_id", "order_date", "product_name", "sku", "qty", "line_revenue", "source_file", "data_scope"])
    if not lines_all.empty:
        lines_all = lines_all.drop_duplicates(subset=["order_id", "order_date", "product_name", "sku", "qty", "line_revenue"], keep="first")
        lines_all = apply_costs(lines_all, costs, "Trendyol")
        orders = lines_all.groupby("order_id", as_index=False).agg(
            platform=("platform", "first"),
            order_date=("order_date", "first"),
            net_sales=("line_revenue", "sum"),
            source_file=("source_file", "first"),
            data_scope=("data_scope", "first"),
        )
        orders["order_count"] = 1.0
    else:
        orders = pd.DataFrame(columns=["platform", "order_id", "order_date", "net_sales", "source_file", "data_scope", "order_count"])
    return orders, lines_all, costs, pd.DataFrame(debug_rows)


@st.cache_data(show_spinner=False)
def load_trendyol_manual_weekly_ads() -> pd.DataFrame:
    files = [p for p in list_data_files(TRENDYOL_DIR) if "manual_weekly_trendyol_ads" in p.name.lower()]
    if not files:
        return pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])
    path = files[0]
    df = read_table_flexible(path)
    if df.empty:
        return pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])

    week_col = find_col(df, ["week_start", "week start", "Hafta Başlangıç", "Hafta Baslangic"])
    spend_col = find_col(df, ["weekly_spend", "weekly spend", "Haftalık Harcama", "Haftalik Harcama", "Spend", "Harcama"])
    revenue_col = find_col(df, ["weekly_revenue", "weekly revenue", "total ad revenue", "ad revenue", "Haftalık Reklam Cirosu", "Revenue"])
    note_col = find_col(df, ["note", "campaign", "Açıklama", "Aciklama"])
    if not week_col or not spend_col:
        return pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])

    rows = []
    for _, r in df.iterrows():
        start = pd.to_datetime(r.get(week_col), errors="coerce")
        if pd.isna(start):
            continue
        start = pd.Timestamp(start).normalize()
        spend = to_float(r.get(spend_col))
        revenue = to_float(r.get(revenue_col)) if revenue_col else 0.0
        note = str(r.get(note_col, "Trendyol Weekly Ads")).strip() if note_col else "Trendyol Weekly Ads"
        days = pd.date_range(start, start + pd.Timedelta(days=6), freq="D")
        for day in days:
            rows.append({
                "platform": "Trendyol",
                "date": day,
                "spend": spend / 7.0,
                "attributed_revenue": revenue / 7.0,
                "campaign_name": note or "Trendyol Weekly Ads",
                "source_file": path.name,
                "spend_source": "Manual Weekly Trendyol Ads",
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])


# =========================================================
# HEPSIBURADA LOADERS
# =========================================================
@st.cache_data(show_spinner=False)
def load_hepsiburada_sales() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    costs = load_cost_table(HEPSIBURADA_DIR, "Hepsiburada")
    order_level_frames = []
    snapshot_candidates = []
    debug_rows = []

    for path in list_data_files(HEPSIBURADA_DIR):
        lname = normalize_text(path.name)
        if "maliyet" in lname or "iade" in lname or "return" in lname or "magaza" in lname or "mağaza" in lname:
            continue
        if "hepsiburada" not in lname:
            continue

        df = read_table_try_skiprows(path, max_skip=2)
        if df.empty:
            debug_rows.append({"platform": "Hepsiburada", "source_file": path.name, "status": "okunamadı", "rows": 0, "note": "Dosya boş veya format tanınmadı."})
            continue

        # 1) Sipariş bazlı dosya yakalamaya çalış.
        order_col = find_col(df, ["Sipariş Numarası", "Siparis Numarasi", "Order Number", "Order ID"])
        date_col = find_col(df, ["Sipariş Tarihi", "Siparis Tarihi", "Order Date", "Tarih"])
        product_col = find_col(df, ["Ürün Adı", "Urun Adi", "Product Name", "Product"])
        sku_col = find_col(df, ["SKU", "Stok Kodu", "Merchant SKU", "Barcode", "Barkod"])
        qty_col = find_col(df, ["Adet", "Miktar", "Quantity", "Qty"])
        revenue_col = find_col(df, ["Faturalanacak Tutar", "Satış Tutarı", "Satis Tutari", "Toplam Tutar", "Total", "Revenue"])
        status_col = find_col(df, ["Durum", "Sipariş Statüsü", "Status"])

        if order_col and revenue_col and (date_col or product_col):
            lines = pd.DataFrame({
                "platform": "Hepsiburada",
                "order_id": df[order_col].astype(str).str.strip(),
                "order_date": pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT,
                "product_name": df[product_col].astype(str) if product_col else "",
                "sku": df[sku_col].apply(clean_sku) if sku_col else "",
                "qty": df[qty_col].apply(to_float) if qty_col else 1.0,
                "line_revenue": df[revenue_col].apply(to_float),
                "status": df[status_col].astype(str) if status_col else "",
                "source_file": path.name,
                "data_scope": "order_level",
            })
            returned = lines["status"].str.contains("ade|iptal|cancel|return", case=False, na=False)
            lines.loc[returned, ["qty", "line_revenue"]] = 0.0
            lines = lines[lines["order_id"].astype(str).str.strip() != ""]
            order_level_frames.append(lines)
            debug_rows.append({"platform": "Hepsiburada", "source_file": path.name, "status": "okundu", "rows": len(lines), "note": "Sipariş bazlı Hepsiburada dosyası."})
            continue

        # 2) Aggregate snapshot dosyası yakala.
        sku_col = find_col(df, ["SKU"])
        product_col = find_col(df, ["Urun Adi", "Ürün Adı", "Product Name"])
        qty_col = find_col(df, ["Toplam Satis Adedi", "Toplam Satış Adedi", "Total Sales Qty", "Satis Miktari", "Satış Miktarı"])
        rev_col = find_col(df, ["Toplam Satis Tutari", "Toplam Satış Tutarı", "Total Sales Amount"])
        comm_col = find_col(df, ["Komisyon Tutar", "Commission Amount"])
        if sku_col and product_col and qty_col and rev_col:
            snapshot = pd.DataFrame({
                "platform": "Hepsiburada",
                "order_id": "hepsiburada_snapshot_" + path.stem,
                "order_date": pd.NaT,
                "product_name": df[product_col].astype(str),
                "sku": df[sku_col].apply(clean_sku),
                "qty": df[qty_col].apply(to_float),
                "line_revenue": df[rev_col].apply(to_float),
                "commission_amount_export": df[comm_col].apply(to_float) if comm_col else 0.0,
                "source_file": path.name,
                "data_scope": "aggregate_snapshot",
            })
            snapshot_candidates.append(snapshot)
            debug_rows.append({"platform": "Hepsiburada", "source_file": path.name, "status": "okundu", "rows": len(snapshot), "note": "Aggregate snapshot adayı."})
        else:
            debug_rows.append({"platform": "Hepsiburada", "source_file": path.name, "status": "atlanıyor", "rows": len(df), "note": "Sipariş veya snapshot kolonları bulunamadı."})

    if order_level_frames:
        lines_all = pd.concat(order_level_frames, ignore_index=True)
        lines_all = lines_all.drop_duplicates(subset=["order_id", "order_date", "product_name", "sku", "qty", "line_revenue"], keep="first")
        lines_all = apply_costs(lines_all, costs, "Hepsiburada")
        orders = lines_all.groupby("order_id", as_index=False).agg(
            platform=("platform", "first"),
            order_date=("order_date", "first"),
            net_sales=("line_revenue", "sum"),
            source_file=("source_file", "first"),
            data_scope=("data_scope", "first"),
        )
        orders["order_count"] = 1.0
        return orders, lines_all, costs, pd.DataFrame(debug_rows)

    if snapshot_candidates:
        # Hepsiburada özet dosyaları kümülatif olabiliyor. Çift sayımı engellemek için en yüksek ciro snapshot'ını seçiyoruz.
        selected = max(snapshot_candidates, key=lambda x: x["line_revenue"].sum()).copy()
        selected = apply_costs(selected, costs, "Hepsiburada")
        orders = pd.DataFrame([{
            "platform": "Hepsiburada",
            "order_id": "hepsiburada_aggregate_snapshot",
            "order_date": pd.NaT,
            "net_sales": float(selected["line_revenue"].sum()),
            "source_file": selected["source_file"].iloc[0] if "source_file" in selected.columns and not selected.empty else "",
            "data_scope": "aggregate_snapshot",
            "order_count": 0.0,
        }])
        return orders, selected, costs, pd.DataFrame(debug_rows)

    empty_orders = pd.DataFrame(columns=["platform", "order_id", "order_date", "net_sales", "source_file", "data_scope", "order_count"])
    empty_lines = pd.DataFrame(columns=["platform", "order_id", "order_date", "product_name", "sku", "qty", "line_revenue", "source_file", "data_scope", "gross_profit"])
    return empty_orders, empty_lines, costs, pd.DataFrame(debug_rows)


# =========================================================
# META / ADS LOADERS
# =========================================================
def find_meta_col(df: pd.DataFrame, options: list[str]) -> Optional[str]:
    return find_col(df, options)


def looks_like_meta_performance_export(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    cols = [normalize_text(c) for c in df.columns]
    has_spend = any(("harcanan tutar" in c) or ("amount spent" in c) or (c == "spend") or ("harcama" in c) for c in cols)
    has_campaign = any(("kampanya" in c) or ("campaign" in c) for c in cols)
    has_period = any(("rapor" in c) or ("reporting" in c) or (c == "date") or (c == "day") or (c == "tarih") or (c == "gun") for c in cols)
    return bool(has_spend and (has_campaign or has_period))


def parse_meta_billing_report(path: Path, platform_name: str) -> tuple[pd.DataFrame, dict | None]:
    raw_text = ""
    for enc in ["utf-8-sig", "utf-8", "iso-8859-9", "cp1254", "latin1"]:
        try:
            raw_text = path.read_text(encoding=enc, errors="replace")
            if raw_text:
                break
        except Exception:
            continue
    if not raw_text:
        return pd.DataFrame(), None

    marker_candidates = ["Meta Reklamları Ödemesi", "Meta Ads Payments", "Meta Advertising Payments"]
    start_idx = -1
    marker_used = None
    for marker in marker_candidates:
        start_idx = raw_text.find(marker)
        if start_idx != -1:
            marker_used = marker
            break
    if start_idx == -1:
        return pd.DataFrame(), None

    section_lines = raw_text[start_idx:].splitlines()
    data_lines = []
    for line in section_lines[1:]:
        if not line.strip():
            if data_lines:
                break
            continue
        if line.startswith("VAT Rate") or line.startswith('"VAT Amount'):
            break
        data_lines.append(line)

    rows = []
    reader = csv.reader(data_lines)
    for row in reader:
        if not row:
            continue
        if len(row) >= 4 and re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", str(row[0]).strip()):
            rows.append({
                "platform": platform_name,
                "date": pd.to_datetime(str(row[0]).strip(), format="%d.%m.%Y", errors="coerce"),
                "spend": to_float(row[3]),
                "attributed_revenue": 0.0,
                "campaign_name": "Meta Billing Charges",
                "source_file": path.name,
                "spend_source": "Meta Billing",
            })

    tmp = pd.DataFrame(rows).dropna(subset=["date"]) if rows else pd.DataFrame()
    if tmp.empty:
        return pd.DataFrame(), {
            "platform": platform_name, "source_file": path.name, "file_type": "Meta Billing", "status": "marker_found_no_rows",
            "rows": 0, "spend_total": 0.0, "note": f"Marker found: {marker_used}",
        }
    tmp["date"] = pd.to_datetime(tmp["date"]).dt.normalize()
    tmp = tmp.groupby(["platform", "date", "campaign_name", "source_file", "spend_source"], as_index=False).agg({"spend": "sum", "attributed_revenue": "sum"})
    return tmp, {
        "platform": platform_name, "source_file": path.name, "file_type": "Meta Billing", "status": "loaded",
        "rows": len(tmp), "spend_total": float(tmp["spend"].sum()), "note": "Spend from Meta payment ledger.",
    }


def parse_meta_performance_export(path: Path, platform_name: str) -> tuple[pd.DataFrame, dict | None]:
    df = read_table_try_skiprows(path, max_skip=1)
    if df.empty or not looks_like_meta_performance_export(df):
        return pd.DataFrame(), None

    date_col = find_meta_col(df, ["Date", "Day", "Gün", "Gun", "Tarih", "Reporting starts", "Reporting start"])
    report_start_col = find_meta_col(df, ["Rapor Başlangıcı", "Report start", "Reporting starts", "Reporting start"])
    report_end_col = find_meta_col(df, ["Rapor Sonu", "Report end", "Reporting ends", "Reporting end"])
    spend_col = find_meta_col(df, ["Amount spent", "Spend", "Harcanan Tutar", "Harcama", "Harcanan Tutar (TRY)"])
    revenue_col = find_meta_col(df, [
        "Website purchases conversion value", "Purchase conversion value", "Purchases conversion value",
        "Purchase value", "Attributed revenue", "Revenue", "Gelir", "Alışveriş dönüşüm değeri",
        "Satın alma dönüşüm değeri",
    ])
    roas_col = find_meta_col(df, ["Purchase ROAS", "Website purchase ROAS", "Alışveriş reklam harcamasının getirisi", "Satın alma ROAS", "ROAS", "Getirisi"])
    purchase_col = find_meta_col(df, ["Purchases", "Website purchases", "Alışverişler", "Satın almalar", "Satin alma", "Purchase"])
    result_col = find_meta_col(df, ["Sonuçlar", "Results"])
    campaign_col = find_meta_col(df, ["Campaign name", "Campaign", "Kampanya Adı", "Kampanya"])

    if not spend_col:
        return pd.DataFrame(), {
            "platform": platform_name, "source_file": path.name, "file_type": "Meta Performance", "status": "missing_spend",
            "rows": 0, "spend_total": 0.0, "note": "Meta formatı bulundu ama harcama kolonu eşleşmedi.",
        }

    campaign = df[campaign_col].replace("", pd.NA).ffill().fillna("Unknown Campaign") if campaign_col else pd.Series([path.stem] * len(df))
    spend = df[spend_col].apply(to_float)
    purchases = df[purchase_col].apply(to_float) if purchase_col else (df[result_col].apply(to_float) if result_col else pd.Series([0.0] * len(df)))
    if revenue_col:
        revenue = df[revenue_col].apply(to_float)
    elif roas_col:
        revenue = spend * df[roas_col].apply(to_float)
    else:
        revenue = pd.Series([0.0] * len(df))

    rows = []
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        for i in range(len(df)):
            if pd.isna(dates.iloc[i]):
                continue
            rows.append({
                "platform": platform_name,
                "date": pd.Timestamp(dates.iloc[i]).normalize(),
                "spend": float(spend.iloc[i]),
                "attributed_revenue": float(revenue.iloc[i]),
                "purchases": float(purchases.iloc[i]),
                "campaign_name": str(campaign.iloc[i]),
                "source_file": path.name,
                "spend_source": "Meta Performance",
            })
    elif report_start_col and report_end_col:
        starts = pd.to_datetime(df[report_start_col], errors="coerce")
        ends = pd.to_datetime(df[report_end_col], errors="coerce")
        for i in range(len(df)):
            start_d = starts.iloc[i]
            end_d = ends.iloc[i]
            if pd.isna(start_d) and pd.isna(end_d):
                continue
            if pd.isna(start_d):
                start_d = end_d
            if pd.isna(end_d):
                end_d = start_d
            start_d = pd.Timestamp(start_d).normalize()
            end_d = pd.Timestamp(end_d).normalize()
            if end_d < start_d:
                start_d, end_d = end_d, start_d
            days = pd.date_range(start_d, end_d, freq="D")
            n = max(len(days), 1)
            for day in days:
                rows.append({
                    "platform": platform_name,
                    "date": day,
                    "spend": float(spend.iloc[i]) / n,
                    "attributed_revenue": float(revenue.iloc[i]) / n,
                    "purchases": float(purchases.iloc[i]) / n,
                    "campaign_name": str(campaign.iloc[i]),
                    "source_file": path.name,
                    "spend_source": "Meta Performance Allocated",
                })

    tmp = pd.DataFrame(rows)
    if tmp.empty:
        return pd.DataFrame(), {
            "platform": platform_name, "source_file": path.name, "file_type": "Meta Performance", "status": "no_date",
            "rows": 0, "spend_total": float(spend.sum()), "note": "Harcama bulundu ama tarih/rapor dönemi eşleşmedi.",
        }

    tmp = tmp.groupby(["platform", "date", "campaign_name", "source_file", "spend_source"], as_index=False).agg({"spend": "sum", "attributed_revenue": "sum", "purchases": "sum"})
    return tmp, {
        "platform": platform_name, "source_file": path.name, "file_type": "Meta Performance", "status": "loaded",
        "rows": len(tmp), "spend_total": float(tmp["spend"].sum()), "note": "Meta performance export.",
    }


@st.cache_data(show_spinner=False)
def load_platform_meta_ads(folder: Path, platform_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    billing_frames = []
    performance_frames = []
    debug_rows = []

    for path in list_data_files(folder):
        lname = normalize_text(path.name)
        if "maliyet" in lname or "cost" in lname:
            continue
        # Sadece reklam/meta dosyalarını dene; ama billing dosyaları bazı durumlarda tek kolon geldiği için dosya adı önemlidir.
        if not any(k in lname for k in ["meta", "facebook", "fb", "ads", "reklam", "campaign", "kampanya", "billing"]):
            continue

        billing_df, billing_debug = parse_meta_billing_report(path, platform_name)
        if billing_debug:
            debug_rows.append(billing_debug)
        if not billing_df.empty:
            billing_frames.append(billing_df)
            continue

        perf_df, perf_debug = parse_meta_performance_export(path, platform_name)
        if perf_debug:
            debug_rows.append(perf_debug)
        if not perf_df.empty:
            performance_frames.append(perf_df)

    billing = pd.concat(billing_frames, ignore_index=True) if billing_frames else pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])
    perf = pd.concat(performance_frames, ignore_index=True) if performance_frames else pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "purchases", "campaign_name", "source_file", "spend_source"])

    if not billing.empty:
        billing = billing.drop_duplicates(subset=["date", "campaign_name", "source_file", "spend"], keep="first")
    if not perf.empty:
        perf = perf.drop_duplicates(subset=["date", "campaign_name", "source_file", "spend", "attributed_revenue"], keep="first")

    billing_daily = billing.groupby(["platform", "date"], as_index=False).agg({"spend": "sum"}).rename(columns={"spend": "billing_spend"}) if not billing.empty else pd.DataFrame(columns=["platform", "date", "billing_spend"])
    perf_daily = perf.groupby(["platform", "date"], as_index=False).agg({"spend": "sum", "attributed_revenue": "sum"}).rename(columns={"spend": "performance_spend"}) if not perf.empty else pd.DataFrame(columns=["platform", "date", "performance_spend", "attributed_revenue"])

    daily = pd.merge(billing_daily, perf_daily, on=["platform", "date"], how="outer")
    if daily.empty:
        return pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"]), pd.DataFrame(debug_rows)

    for c in ["billing_spend", "performance_spend", "attributed_revenue"]:
        if c not in daily.columns:
            daily[c] = 0.0
        daily[c] = daily[c].fillna(0.0)

    has_billing = not billing.empty
    daily["spend"] = daily["billing_spend"] if has_billing else daily["performance_spend"]
    daily["spend_source"] = "Meta Billing" if has_billing else "Meta Performance"
    daily["campaign_name"] = "Meta Ads"
    daily["source_file"] = source_files_from_df(billing if has_billing else perf)
    daily = daily[["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"]]
    return daily.sort_values("date").reset_index(drop=True), pd.DataFrame(debug_rows)


# =========================================================
# CREATIVE LOADERS - Finans toplamına otomatik eklenmez.
# =========================================================
@st.cache_data(show_spinner=False)
def load_creative_data() -> pd.DataFrame:
    rows = []
    for path in list_data_files(KREATIF_DIR):
        if path.name.lower() in {"creative_history.csv", "creative_summary.csv", "creative_scorecard.csv", "creative_export.csv"}:
            continue
        df = read_table_try_skiprows(path, max_skip=1)
        if df.empty:
            continue

        campaign_col = find_col(df, ["Kampanya Adı", "Campaign name", "Campaign"])
        ad_col = find_col(df, ["Reklam Adı", "Reklamlar", "Ad name", "Ad"])
        reach_col = find_col(df, ["Erişim", "Reach"])
        imp_col = find_col(df, ["Gösterim", "Impressions"])
        result_col = find_col(df, ["Sonuçlar", "Results"])
        spend_col = find_col(df, ["Harcanan Tutar (TRY)", "Amount spent", "Spend", "Harcama"])
        purchase_col = find_col(df, ["Alışverişler", "Purchases", "Satın almalar"])
        roas_col = find_col(df, ["Alışveriş Reklam Harcamasının Getirisi", "Purchase ROAS", "ROAS"])
        ctr_col = find_col(df, ["CTR (Tümü)", "CTR"])
        cpc_col = find_col(df, ["CPC"])
        cpm_col = find_col(df, ["CPM"])
        freq_col = find_col(df, ["Sıklık", "Frequency"])
        start_col = find_col(df, ["Rapor Başlangıcı", "Reporting starts", "Report start"])
        end_col = find_col(df, ["Rapor Sonu", "Reporting ends", "Report end"])
        avg_purchase_value_col = find_col(df, ["Ortalama alışveriş dönüşüm değeri", "Average purchase conversion value"])
        if not spend_col:
            continue

        tmp = pd.DataFrame({
            "campaign_name": df[campaign_col].astype(str) if campaign_col else "Bilinmeyen Kampanya",
            "creative_name": df[ad_col].astype(str) if ad_col else "Bilinmeyen Kreatif",
            "reach": df[reach_col].apply(to_float) if reach_col else 0.0,
            "impressions": df[imp_col].apply(to_float) if imp_col else 0.0,
            "results": df[result_col].apply(to_float) if result_col else 0.0,
            "spend": df[spend_col].apply(to_float),
            "purchases": df[purchase_col].apply(to_float) if purchase_col else 0.0,
            "roas": df[roas_col].apply(to_float) if roas_col else 0.0,
            "ctr": df[ctr_col].apply(to_float) if ctr_col else 0.0,
            "cpc": df[cpc_col].apply(to_float) if cpc_col else 0.0,
            "cpm": df[cpm_col].apply(to_float) if cpm_col else 0.0,
            "frequency": df[freq_col].apply(to_float) if freq_col else 0.0,
            "report_start": pd.to_datetime(df[start_col], errors="coerce") if start_col else pd.NaT,
            "report_end": pd.to_datetime(df[end_col], errors="coerce") if end_col else pd.NaT,
            "avg_purchase_value": df[avg_purchase_value_col].apply(to_float) if avg_purchase_value_col else 0.0,
            "source_file": path.name,
        })
        tmp["campaign_name"] = tmp["campaign_name"].fillna("").astype(str).replace("nan", "")
        tmp["creative_name"] = tmp["creative_name"].fillna("").astype(str).replace("nan", "")
        tmp = tmp[~((tmp["campaign_name"].str.strip() == "") & (tmp["creative_name"].str.strip() == ""))].copy()
        tmp["campaign_name"] = tmp["campaign_name"].where(tmp["campaign_name"].str.strip() != "", "Bilinmeyen Kampanya")
        tmp["creative_name"] = tmp["creative_name"].where(tmp["creative_name"].str.strip() != "", "Bilinmeyen Kreatif")
        tmp["attributed_revenue"] = tmp["spend"] * tmp["roas"]
        tmp.loc[tmp["attributed_revenue"].eq(0), "attributed_revenue"] = tmp.loc[tmp["attributed_revenue"].eq(0), "purchases"] * tmp.loc[tmp["attributed_revenue"].eq(0), "avg_purchase_value"]
        tmp["cac"] = tmp.apply(lambda r: safe_divide(r["spend"], r["purchases"]), axis=1)
        tmp["calculated_roas"] = tmp.apply(lambda r: safe_divide(r["attributed_revenue"], r["spend"]), axis=1)
        tmp["report_date"] = tmp["report_end"].fillna(tmp["report_start"])
        rows.append(tmp)

    if not rows:
        return pd.DataFrame(columns=[
            "campaign_name", "creative_name", "reach", "impressions", "results",
            "spend", "purchases", "roas", "ctr", "cpc", "cpm", "frequency",
            "attributed_revenue", "cac", "calculated_roas", "report_date", "source_file"
        ])
    out = pd.concat(rows, ignore_index=True)
    out = out.drop_duplicates(subset=["campaign_name", "creative_name", "spend", "impressions", "reach", "purchases", "source_file"], keep="last")
    return out.reset_index(drop=True)


# =========================================================
# CENTRAL MODEL
# =========================================================
@st.cache_data(show_spinner=False)
def build_model() -> dict:
    shopify_orders, shopify_lines, shopify_costs, shopify_debug = load_shopify_sales()
    trendyol_orders, trendyol_lines, trendyol_costs, trendyol_debug = load_trendyol_sales()
    hb_orders, hb_lines, hb_costs, hb_debug = load_hepsiburada_sales()

    shopify_ads, shopify_ads_debug = load_platform_meta_ads(SHOPIFY_DIR, "Shopify")
    trendyol_weekly_ads = load_trendyol_manual_weekly_ads()
    trendyol_meta_ads, trendyol_ads_debug = load_platform_meta_ads(TRENDYOL_DIR, "Trendyol")
    hb_ads, hb_ads_debug = load_platform_meta_ads(HEPSIBURADA_DIR, "Hepsiburada")
    creative = load_creative_data()

    orders = pd.concat([shopify_orders, trendyol_orders, hb_orders], ignore_index=True)
    lines = pd.concat([shopify_lines, trendyol_lines, hb_lines], ignore_index=True)
    ads = pd.concat([shopify_ads, trendyol_weekly_ads, trendyol_meta_ads, hb_ads], ignore_index=True)

    if not lines.empty:
        lines["inventory_key"] = lines["product_name"].apply(infer_inventory_key)
        lines["stock_units"] = lines["inventory_key"].map(MANUAL_INVENTORY)
        lines["line_revenue"] = pd.to_numeric(lines["line_revenue"], errors="coerce").fillna(0.0)
        lines["qty"] = pd.to_numeric(lines["qty"], errors="coerce").fillna(0.0)
        lines["gross_profit"] = pd.to_numeric(lines.get("gross_profit", 0.0), errors="coerce").fillna(0.0)
        lines["cost_matched"] = lines.get("cost_matched", False)
    else:
        lines = pd.DataFrame(columns=["platform", "order_id", "order_date", "product_name", "sku", "qty", "line_revenue", "gross_profit", "source_file", "data_scope", "inventory_key", "stock_units", "cost_matched"])

    if not orders.empty:
        orders["net_sales"] = pd.to_numeric(orders["net_sales"], errors="coerce").fillna(0.0)
        orders["order_count"] = pd.to_numeric(orders.get("order_count", 1.0), errors="coerce").fillna(1.0)
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    else:
        orders = pd.DataFrame(columns=["platform", "order_id", "order_date", "net_sales", "source_file", "data_scope", "order_count"])

    if not ads.empty:
        ads["spend"] = pd.to_numeric(ads["spend"], errors="coerce").fillna(0.0)
        ads["attributed_revenue"] = pd.to_numeric(ads.get("attributed_revenue", 0.0), errors="coerce").fillna(0.0)
        ads["date"] = pd.to_datetime(ads["date"], errors="coerce")
        ads = ads.dropna(subset=["date"])
    else:
        ads = pd.DataFrame(columns=["platform", "date", "spend", "attributed_revenue", "campaign_name", "source_file", "spend_source"])

    data_debug = pd.concat([shopify_debug, trendyol_debug, hb_debug], ignore_index=True) if any(not x.empty for x in [shopify_debug, trendyol_debug, hb_debug]) else pd.DataFrame()
    ads_debug = pd.concat([shopify_ads_debug, trendyol_ads_debug, hb_ads_debug], ignore_index=True) if any(not x.empty for x in [shopify_ads_debug, trendyol_ads_debug, hb_ads_debug]) else pd.DataFrame()

    warnings = []
    if not hb_orders.empty and "data_scope" in hb_orders.columns and hb_orders["data_scope"].astype(str).eq("aggregate_snapshot").any():
        warnings.append("Hepsiburada sipariş bazlı tarihli dosya bulunmadığı için en yüksek ciroya sahip aggregate snapshot kullanıldı. Bu veri özel tarih filtresine dahil edilmez; Tüm Zamanlar görünümünde gösterilir.")
    if creative.empty:
        warnings.append("Kreatif klasöründe okunabilir kreatif raporu yok. Kreatif yorumu boş kalabilir.")
    if ads.empty:
        warnings.append("Platform bazlı reklam harcaması bulunamadı. ROAS ve net kâr sonrası reklam metrikleri eksik olabilir.")
    if not creative.empty and not ads.empty:
        warnings.append("Kreatif raporu finans toplamına otomatik eklenmiyor. Böylece Meta harcaması, Shopify/Trendyol reklam dosyalarıyla iki kez sayılmaz.")

    return {
        "orders": orders,
        "lines": lines,
        "ads": ads,
        "creative": creative,
        "data_debug": data_debug,
        "ads_debug": ads_debug,
        "warnings": warnings,
        "costs": {
            "Shopify": shopify_costs,
            "Trendyol": trendyol_costs,
            "Hepsiburada": hb_costs,
        },
    }


model = build_model()
orders_all = model["orders"]
lines_all = model["lines"]
ads_all = model["ads"]
creative_all = model["creative"]


# =========================================================
# SIDEBAR INPUTS
# =========================================================
with st.sidebar:
    st.header("AI Varsayımları")
    monthly_revenue_target = st.number_input("Aylık Net Ciro Hedefi (TL)", min_value=0.0, value=500000.0, step=50000.0, format="%.2f")
    fixed_costs_30d = st.number_input("30 Günlük Sabit Gider (TL)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    current_cash = st.number_input("Mevcut Nakit (TL)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    planned_stock_purchase = st.number_input("Planlanan Stok Alımı (TL)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    new_customer_count = st.number_input("Yeni Müşteri Sayısı (veri yoksa manuel)", min_value=0, value=0, step=10)
    returning_customer_count = st.number_input("Geri Gelen Müşteri Sayısı (veri yoksa manuel)", min_value=0, value=0, step=10)
    avg_purchase_per_customer = st.number_input("LTV için müşteri başı ort. satın alma adedi", min_value=1.0, value=1.5, step=0.1)
    stock_lead_days = st.number_input("Stok besleme için tedarik süresi (gün)", min_value=1, value=30, step=1)
    low_stock_threshold = st.number_input("Ölü / düşük stok eşiği", min_value=0, value=10, step=1)

    st.markdown("---")
    include_creative_in_finance = st.checkbox(
        "Kreatif raporu harcamasını finans toplamına dahil et",
        value=False,
        help="Normalde kapalı kalmalı. Shopify/Trendyol reklam dosyaların varsa kreatif harcamasını tekrar eklemek çift sayım yapabilir.",
    )

    selected_report = st.selectbox(
        "AI rapor başlığı seç",
        [
            "Genel Yönetici Özeti", "Net Ciro ve Sipariş Yorumu", "Hedef Gerçekleşme Oranı", "Anlık Net Kar",
            "Top-Seller Listesi", "Ölü Stok Alarmı", "Kanal Karlılık Kıyaslaması", "Kampanya Bazlı ROAS",
            "Kreatif Karnesi", "CAC ve Müşteri Edinme Yorumu", "Yeni vs. Geri Gelen Müşteri",
            "Sepet Ortalaması (AOV)", "LTV Yorumu", "İş Birliği Performansı", "Erişim vs. Dönüşüm",
            "30 Günlük Satış Tahmini", "Stok Besleme Planı", "Nakit Akış Projeksiyonu", "Yapay Zeka Notu",
        ],
    )
    st.markdown("---")
    st.caption(f"Project root: {PROJECT_DIR}")


# =========================================================
# DATE FILTER
# =========================================================
date_candidates = []
for df, col in [(orders_all, "order_date"), (lines_all, "order_date"), (ads_all, "date"), (creative_all, "report_date")]:
    if not df.empty and col in df.columns:
        s = pd.to_datetime(df[col], errors="coerce").dropna()
        if not s.empty:
            date_candidates.append(s)

if date_candidates:
    all_dates = pd.concat(date_candidates, ignore_index=True)
    min_date = all_dates.min().normalize()
    max_date = all_dates.max().normalize()
else:
    min_date = max_date = pd.Timestamp.today().normalize()

top_spacer, start_col, end_col, all_time_col = st.columns([4.5, 1.4, 1.4, 1.0])
with start_col:
    start_date = st.date_input("Başlangıç", value=min_date.date(), min_value=min_date.date(), max_value=max_date.date())
with end_col:
    end_date = st.date_input("Bitiş", value=max_date.date(), min_value=min_date.date(), max_value=max_date.date())
with all_time_col:
    all_time = st.toggle("Tüm Zamanlar", value=True)


def filter_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns or all_time:
        return df.copy()
    s = pd.Timestamp(min(start_date, end_date))
    e = pd.Timestamp(max(start_date, end_date)) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    d = pd.to_datetime(df[col], errors="coerce")
    return df[(d >= s) & (d <= e)].copy()


orders = filter_date(orders_all, "order_date")
lines = filter_date(lines_all, "order_date")
ads = filter_date(ads_all, "date")
creative = filter_date(creative_all, "report_date")
period_label = "Tüm Zamanlar" if all_time else f"{min(start_date, end_date)} → {max(start_date, end_date)}"

if include_creative_in_finance and not creative.empty:
    creative_ads = pd.DataFrame({
        "platform": "Meta/Kreatif",
        "date": creative["report_date"],
        "spend": creative["spend"],
        "attributed_revenue": creative["attributed_revenue"],
        "campaign_name": creative["campaign_name"],
        "source_file": creative["source_file"],
        "spend_source": "Creative Report Manual Include",
    })
    ads = pd.concat([ads, creative_ads], ignore_index=True)


# =========================================================
# METRICS / SUMMARIES
# =========================================================
total_revenue = float(orders["net_sales"].sum()) if not orders.empty else float(lines["line_revenue"].sum()) if not lines.empty else 0.0
known_order_count = int(orders["order_count"].sum()) if not orders.empty and "order_count" in orders.columns else 0
aov = safe_divide(total_revenue, known_order_count)
gross_profit = float(lines["gross_profit"].sum()) if not lines.empty and "gross_profit" in lines.columns else total_revenue * 0.45
ad_spend = float(ads["spend"].sum()) if not ads.empty else 0.0
ad_revenue = float(ads["attributed_revenue"].sum()) if not ads.empty else 0.0
net_profit_now = gross_profit - ad_spend - fixed_costs_30d
overall_roas = safe_divide(ad_revenue, ad_spend)
creative_purchases = float(creative["purchases"].sum()) if not creative.empty and "purchases" in creative.columns else 0.0
cac = safe_divide(ad_spend, new_customer_count) if new_customer_count else safe_divide(ad_spend, creative_purchases)
target_rate = safe_divide(total_revenue, monthly_revenue_target) * 100 if monthly_revenue_target else 0.0
ltv = aov * avg_purchase_per_customer

# Finansın gerçekten kapsadığı gün sayısı: tarihli verilerden hesaplanır.
valid_metric_dates = []
for df, col in [(orders, "order_date"), (ads, "date")]:
    if not df.empty and col in df.columns:
        valid_metric_dates.extend(pd.to_datetime(df[col], errors="coerce").dropna().tolist())
if valid_metric_dates:
    calc_min_date = min(valid_metric_dates)
    calc_max_date = max(valid_metric_dates)
    active_days = max((pd.Timestamp(calc_max_date).normalize() - pd.Timestamp(calc_min_date).normalize()).days + 1, 1)
else:
    active_days = max((max_date - min_date).days + 1, 1)
forecast_30d_revenue = safe_divide(total_revenue, active_days) * 30 if total_revenue else 0.0

if not orders.empty:
    platform_summary = orders.groupby("platform", as_index=False).agg(
        net_revenue=("net_sales", "sum"),
        orders=("order_count", "sum"),
        sales_source=("source_file", lambda s: ", ".join(sorted(set(s.dropna().astype(str)))[:4])),
        data_scope=("data_scope", lambda s: ", ".join(sorted(set(s.dropna().astype(str)))[:4])),
    )
else:
    platform_summary = pd.DataFrame(columns=["platform", "net_revenue", "orders", "sales_source", "data_scope"])

if not lines.empty:
    profit_by_platform = lines.groupby("platform", as_index=False).agg(
        gross_profit=("gross_profit", "sum"),
        units=("qty", "sum"),
        line_revenue=("line_revenue", "sum"),
        cost_match_ratio=("cost_matched", lambda x: float(pd.Series(x).fillna(False).mean()) if len(x) else 0.0),
    )
    platform_summary = platform_summary.merge(profit_by_platform, on="platform", how="outer").fillna(0.0)
else:
    for col in ["gross_profit", "units", "line_revenue", "cost_match_ratio"]:
        platform_summary[col] = 0.0

if not ads.empty:
    ads_by_platform = ads.groupby("platform", as_index=False).agg(
        ad_spend=("spend", "sum"),
        ad_revenue=("attributed_revenue", "sum"),
        ad_source=("spend_source", lambda s: ", ".join(sorted(set(s.dropna().astype(str)))[:4])),
    )
    platform_summary = platform_summary.merge(ads_by_platform, on="platform", how="outer").fillna(0.0)
else:
    platform_summary["ad_spend"] = 0.0
    platform_summary["ad_revenue"] = 0.0
    platform_summary["ad_source"] = ""

if not platform_summary.empty:
    platform_summary["net_profit_after_ads"] = platform_summary["gross_profit"] - platform_summary["ad_spend"]
    platform_summary["aov"] = platform_summary.apply(lambda r: safe_divide(r["net_revenue"], r["orders"]), axis=1)
    platform_summary["roas"] = platform_summary.apply(lambda r: safe_divide(r["ad_revenue"], r["ad_spend"]), axis=1)
    platform_summary = platform_summary[[
        "platform", "net_revenue", "orders", "line_revenue", "gross_profit", "units",
        "ad_spend", "ad_revenue", "net_profit_after_ads", "aov", "roas", "cost_match_ratio", "data_scope", "sales_source", "ad_source"
    ]]

if not lines.empty:
    product_summary = lines.groupby(["platform", "product_name"], as_index=False).agg(
        revenue=("line_revenue", "sum"),
        qty=("qty", "sum"),
        gross_profit=("gross_profit", "sum"),
        stock_units=("stock_units", "max"),
    ).sort_values(["qty", "revenue"], ascending=False)
else:
    product_summary = pd.DataFrame(columns=["platform", "product_name", "revenue", "qty", "gross_profit", "stock_units"])

if not creative.empty:
    creative_summary = creative.groupby(["campaign_name", "creative_name"], as_index=False).agg(
        spend=("spend", "sum"),
        reach=("reach", "sum"),
        impressions=("impressions", "sum"),
        results=("results", "sum"),
        purchases=("purchases", "sum"),
        attributed_revenue=("attributed_revenue", "sum"),
        ctr=("ctr", "mean"),
        cpc=("cpc", "mean"),
        cpm=("cpm", "mean"),
        frequency=("frequency", "mean"),
    )
    creative_summary["roas"] = creative_summary.apply(lambda r: safe_divide(r["attributed_revenue"], r["spend"]), axis=1)
    creative_summary["cac"] = creative_summary.apply(lambda r: safe_divide(r["spend"], r["purchases"]), axis=1)
    creative_summary["decision"] = creative_summary.apply(
        lambda r: "Ölçekle" if r["roas"] >= 3 and r["purchases"] >= 1 else ("Durdurmayı Değerlendir" if r["spend"] >= 500 and r["roas"] < 1.5 else ("Kreatif Değiştir" if r["ctr"] < 1 and r["spend"] >= 500 else "İzle")),
        axis=1,
    )
else:
    creative_summary = pd.DataFrame(columns=["campaign_name", "creative_name", "spend", "reach", "impressions", "results", "purchases", "attributed_revenue", "ctr", "cpc", "cpm", "frequency", "roas", "cac", "decision"])


# =========================================================
# AI CHAT HELPERS
# =========================================================
def get_secret_value(key: str) -> str:
    try:
        return str(st.secrets.get(key, "")).strip()
    except Exception:
        return ""


def compact_table(df: pd.DataFrame, max_rows: int = 12) -> str:
    if df is None or df.empty:
        return "Veri yok."
    return df.head(max_rows).to_markdown(index=False)


def build_report_context(platform_summary_df: pd.DataFrame, product_summary_df: pd.DataFrame, creative_summary_df: pd.DataFrame) -> str:
    top_products = product_summary_df.sort_values(["qty", "revenue"], ascending=False).head(10) if not product_summary_df.empty else pd.DataFrame()
    top_creatives = creative_summary_df.sort_values(["roas", "purchases"], ascending=False).head(10) if not creative_summary_df.empty else pd.DataFrame()
    weak_creatives = creative_summary_df.sort_values(["spend", "roas"], ascending=[False, True]).head(10) if not creative_summary_df.empty else pd.DataFrame()
    warning_text = "\n".join([f"- {w}" for w in model.get("warnings", [])]) or "- Kritik uyarı yok."

    return f"""
RAPOR DÖNEMİ: {period_label}

GENEL KPI'LAR:
- Net Ciro: {money(total_revenue)}
- Bilinen Sipariş Adedi: {known_order_count:,}
- Hedef Gerçekleşme: {pct(target_rate)}
- Anlık Net Kar: {money(net_profit_now)}
- Brüt Kar: {money(gross_profit)}
- Reklam Harcaması: {money(ad_spend)}
- Reklam Geliri: {money(ad_revenue)}
- ROAS: {overall_roas:.2f}
- CAC: {money(cac)}
- AOV: {money(aov)}
- LTV Tahmini: {money(ltv)}
- Kreatif harcaması finans toplamına dahil mi?: {'Evet' if include_creative_in_finance else 'Hayır'}

VERİ UYARILARI:
{warning_text}

KANAL ÖZETİ:
{compact_table(platform_summary_df, 10)}

TOP-SELLER ÜRÜNLER:
{compact_table(top_products[["platform", "product_name", "revenue", "qty", "gross_profit", "stock_units"]] if not top_products.empty else top_products, 10)}

EN GÜÇLÜ KREATİFLER:
{compact_table(top_creatives[["campaign_name", "creative_name", "spend", "purchases", "attributed_revenue", "roas", "cac", "ctr", "decision"]] if not top_creatives.empty else top_creatives, 10)}

KONTROL EDİLECEK KREATİFLER:
{compact_table(weak_creatives[["campaign_name", "creative_name", "spend", "purchases", "attributed_revenue", "roas", "cac", "ctr", "decision"]] if not weak_creatives.empty else weak_creatives, 10)}

KULLANICININ MANUEL VARSAYIMLARI:
- Aylık Ciro Hedefi: {money(monthly_revenue_target)}
- 30 Günlük Sabit Gider: {money(fixed_costs_30d)}
- Mevcut Nakit: {money(current_cash)}
- Planlanan Stok Alımı: {money(planned_stock_purchase)}
- Yeni Müşteri: {new_customer_count:,}
- Geri Gelen Müşteri: {returning_customer_count:,}
- Stok Tedarik Süresi: {stock_lead_days} gün
"""


def create_general_note() -> str:
    notes = []
    if target_rate >= 100:
        notes.append("Ciro hedefi yakalanmış veya aşılmış görünüyor; artık odak kâr marjı ve stok sürekliliği olmalı.")
    elif target_rate >= 70:
        notes.append("Ciro hedefinin büyük kısmı tamamlanmış; kampanya ve top-seller ürünlerde kontrollü ölçekleme denenebilir.")
    else:
        notes.append("Ciro hedefinin altında kalınmış; reklam verimi, ürün görünürlüğü ve kampanya teklifleri güçlendirilmeli.")

    if overall_roas >= 3:
        notes.append("Finans hesabına dahil edilen reklam ROAS seviyesi güçlü; kazanan kampanya/kreatiflerde bütçe kademeli artırılabilir.")
    elif overall_roas >= 1.5:
        notes.append("ROAS orta seviyede; düşük performanslı kreatifler ayrıştırılmazsa net kâr baskılanabilir.")
    elif ad_spend > 0:
        notes.append("ROAS düşük; harcama satışa yeterince dönmüyor, kreatif ve hedefleme kontrol edilmeli.")
    else:
        notes.append("Finans modelinde reklam harcaması bulunmuyor; net kâr yorumu reklam etkisini içermeyebilir.")

    if net_profit_now < 0:
        notes.append("Anlık net kâr negatif; gider ve reklam harcaması kısa vadede kontrol edilmeli.")
    else:
        notes.append("Anlık net kâr pozitif; ölçekleme yapılırken stok ve nakit akışı birlikte izlenmeli.")

    if not product_summary.empty:
        top = product_summary.iloc[0]
        notes.append(f"Top-seller ürün: {top['product_name']} ({top['qty']:.0f} adet). Bu ürün için stok besleme önceliği verilmeli.")

    if not creative_summary.empty:
        best = creative_summary.sort_values(["roas", "purchases"], ascending=False).head(1)
        if not best.empty:
            row = best.iloc[0]
            notes.append(f"En güçlü kreatif sinyali: {row['creative_name']} | ROAS {row['roas']:.2f} | karar: {row['decision']}.")

    for warning in model.get("warnings", []):
        notes.append(f"Veri notu: {warning}")

    return "\n\n".join([f"- {n}" for n in notes])


def rule_based_chat_answer(user_question: str, context: str) -> str:
    q = normalize_text(user_question)
    if any(k in q for k in ["roas", "kampanya", "reklam"]):
        yorum = "Genel ROAS güçlü." if overall_roas >= 3 else ("Genel ROAS orta seviyede." if overall_roas >= 1.5 else "Genel ROAS düşük veya reklam geliri eksik.")
        return f"{yorum}\n\nFinans hesabındaki reklam harcaması: **{money(ad_spend)}**, reklam geliri: **{money(ad_revenue)}**, ROAS: **{overall_roas:.2f}**. Kreatif raporu finansa {'dahil' if include_creative_in_finance else 'dahil değil'}; bu sayede çift sayım kontrol altında."
    if any(k in q for k in ["stok", "besleme", "urun", "top seller", "top seller"]):
        if product_summary.empty:
            return "Ürün/stok yorumu için yeterli ürün verisi bulunamadı."
        top = product_summary.sort_values(["qty", "revenue"], ascending=False).head(5)
        return "Stok ve ürün tarafında ilk odak top-seller ürünler olmalı:\n\n" + compact_table(top[["platform", "product_name", "qty", "revenue", "stock_units"]], 5)
    if any(k in q for k in ["kar", "karlilik", "net kar", "ciro"]):
        return f"Net ciro **{money(total_revenue)}**, tahmini brüt kâr **{money(gross_profit)}**, reklam harcaması **{money(ad_spend)}**, sabit gider varsayımı **{money(fixed_costs_30d)}**. Bu varsayımla anlık net kâr **{money(net_profit_now)}**."
    if any(k in q for k in ["kreatif", "creative", "ctr", "cpc", "cpm"]):
        if creative_summary.empty:
            return "Kreatif yorumu için Kreatif_Takip klasöründe okunabilir kreatif raporu bulunamadı."
        best = creative_summary.sort_values(["roas", "purchases"], ascending=False).head(5)
        weak = creative_summary.sort_values(["spend", "roas"], ascending=[False, True]).head(5)
        return "En güçlü kreatifler:\n\n" + compact_table(best[["campaign_name", "creative_name", "spend", "purchases", "roas", "cac", "ctr", "decision"]], 5) + "\n\nKontrol edilecek kreatifler:\n\n" + compact_table(weak[["campaign_name", "creative_name", "spend", "purchases", "roas", "cac", "ctr", "decision"]], 5)
    return "Raporlara göre genel özet:\n\n" + create_general_note()


def call_gemini_assistant(user_question: str, context: str, model_name: str) -> str:
    api_key = get_secret_value("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API anahtarı bulunamadı. Streamlit Secrets içine GEMINI_API_KEY eklenirse bu mod çalışır."
    try:
        from google import genai
    except Exception as exc:
        return f"Google GenAI paketi kurulu değil. requirements.txt içine `google-genai` ekle. Teknik hata: {exc}"

    prompt = f"""
Sen IQIBLA Türkiye için çalışan veri analizi asistanısın.
Aşağıdaki rapor verilerine göre cevap ver.
Cevabın Türkçe, net, yöneticiye uygun ve aksiyon odaklı olsun.
Bilmediğin veya veri olmayan yerde tahmin uydurma; 'veri eksik' de.
Özellikle dikkat et: Kreatif raporu finans toplamına otomatik dahil edilmiyorsa, kreatif harcamasını tekrar net kârdan düşme.

{context}

KULLANICI SORUSU:
{user_question}
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as exc:
        return f"Gemini yanıtı alınamadı: {exc}"


def answer_with_selected_ai(provider: str, user_question: str, context: str, gemini_model: str) -> str:
    if provider == "Gemini":
        return call_gemini_assistant(user_question, context, gemini_model)
    return rule_based_chat_answer(user_question, context)


def priority_label(value: str) -> str:
    return f"**Öncelik Seviyesi:** {value}"


def ai_box(title: str, durum: str, guclu: str, risk: str, aksiyon: str, oncelik: str = "Orta"):
    st.markdown(f"### {title}")
    st.markdown(f"**Durum Özeti:** {durum}")
    st.markdown(f"**Güçlü Noktalar:** {guclu}")
    st.markdown(f"**Riskler:** {risk}")
    st.markdown(f"**Aksiyon Önerisi:** {aksiyon}")
    st.markdown(priority_label(oncelik))


# =========================================================
# TOP METRICS
# =========================================================
st.caption(f"Rapor dönemi: {period_label}")
for warning in model.get("warnings", []):
    st.info(warning)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Net Ciro", money(total_revenue))
k2.metric("Bilinen Sipariş", f"{known_order_count:,}")
k3.metric("Hedef Gerçekleşme", pct(target_rate))
k4.metric("Anlık Net Kar", money(net_profit_now))
k5.metric("AOV", money(aov))
k6.metric("ROAS", f"{overall_roas:.2f}")

k7, k8, k9, k10 = st.columns(4)
k7.metric("Reklam Harcaması", money(ad_spend))
k8.metric("CAC", money(cac))
k9.metric("LTV Tahmini", money(ltv))
k10.metric("30 Gün Tahmini Ciro", money(forecast_30d_revenue))


# =========================================================
# LIVE AI CHAT
# =========================================================
st.markdown(
    """
    <div class="assistant-box">
        <h3 style="color:white; margin-bottom: 6px;">💬 Canlı Yapay Zeka Asistanı</h3>
        <p style="color: rgba(255,255,255,0.70); margin-bottom: 0;">
            Asistan artık satış/kâr toplamını platform verilerinden; kreatif yorumunu ise ayrı kreatif raporundan üretir.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

chat_col1, chat_col2 = st.columns([1.4, 1.2])
with chat_col1:
    ai_provider = st.selectbox("AI Motoru", ["Yerel Kural Bazlı", "Gemini"], index=1)
with chat_col2:
    gemini_model = st.text_input("Gemini model", value="gemini-2.5-flash")

report_context = build_report_context(platform_summary, product_summary, creative_summary)
quick_questions = [
    "Genel yönetici özeti çıkar.",
    "Hangi kreatifleri ölçeklemeliyim, hangilerini durdurmalıyım?",
    "ROAS düşükse en olası sebep nedir?",
    "Stokta neyi beslemeliyim?",
    "Hangi kanal daha kârlı?",
    "30 günlük satış ve nakit riskini yorumla.",
]
selected_quick_question = st.selectbox("Hazır soru seç", [""] + quick_questions)

if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []

if selected_quick_question and st.button("Hazır soruyu sor"):
    st.session_state.ai_chat_history.append({"role": "user", "content": selected_quick_question})
    with st.spinner("Yapay zeka raporları yorumluyor..."):
        answer = answer_with_selected_ai(ai_provider, selected_quick_question, report_context, gemini_model)
    st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
    st.rerun()

for msg in st.session_state.ai_chat_history[-8:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Raporlara göre soru sor: örn. 'Hangi kreatifi kapatmalıyım?'")
if user_prompt:
    st.session_state.ai_chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.spinner("Yapay zeka raporları yorumluyor..."):
        answer = answer_with_selected_ai(ai_provider, user_prompt, report_context, gemini_model)
    st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

with st.expander("AI'ın kullandığı rapor özetini göster"):
    st.code(report_context)

st.divider()


# =========================================================
# SELECTED AI REPORT
# =========================================================
st.subheader(f"Seçili AI Yorumu: {selected_report}")

if selected_report == "Net Ciro ve Sipariş Yorumu":
    durum = f"Toplam net ciro {money(total_revenue)}, bilinen sipariş adedi {known_order_count:,}, AOV {money(aov)}. Hepsiburada snapshot varsa sipariş adedi bilinmeyebilir."
    guclu = "Ciro, sipariş ve ürün satışı aynı merkezi modelden hesaplanıyor; platformlar arası toplam artık tek tabloya bağlı."
    risk = "Tarihsiz Hepsiburada snapshot verisi özel tarih filtresine dahil edilemez. Bu durumda sadece Tüm Zamanlar görünümünde değerlendirilmelidir."
    aksiyon = "Kanal bazında ciroyu takip et; düşük AOV olan kanalda bundle, hediye kutusu veya minimum sepet kampanyası dene."
    ai_box("Net Ciro ve Sipariş Yorumu", durum, guclu, risk, aksiyon)

elif selected_report == "Hedef Gerçekleşme Oranı":
    durum = f"Aylık hedef {money(monthly_revenue_target)}, gerçekleşen net ciro {money(total_revenue)}, gerçekleşme oranı {pct(target_rate)}."
    guclu = "Hedefe yaklaşan kanallarda mevcut trafik ve ürün uyumu güçlüdür."
    risk = "Hedef düşük kalırsa ay sonuna doğru agresif reklam harcaması kârı bozabilir."
    aksiyon = "Hedefin altındaysa top-seller ürünleri öne çıkar, düşük ROAS kreatifleri durdur, yüksek dönüşümlü kanala bütçe kaydır."
    ai_box("Hedef Gerçekleşme Oranı", durum, guclu, risk, aksiyon, "Yüksek" if target_rate < 70 else "Orta")

elif selected_report == "Anlık Net Kar":
    durum = f"Tahmini brüt kâr {money(gross_profit)}, reklam harcaması {money(ad_spend)}, sabit gider {money(fixed_costs_30d)}, anlık net kâr {money(net_profit_now)}."
    guclu = "Reklam harcaması platform bazlı dosyalardan geliyor; kreatif dosyası varsayılan olarak tekrar düşülmüyor."
    risk = "Maliyet eşleşmesi düşükse brüt kâr fazla görünebilir; Veri Durumu sekmesinden maliyet eşleşmesini kontrol et."
    aksiyon = "Kârı düşüren kanalı tespit et; maliyeti yüksek SKU'ları ve düşük ROAS kampanyaları ayrı incele."
    ai_box("Anlık Net Kar", durum, guclu, risk, aksiyon, "Yüksek" if net_profit_now < 0 else "Orta")

elif selected_report == "Top-Seller Listesi":
    st.markdown("### Top-Seller Listesi")
    if product_summary.empty:
        st.info("Top-seller için ürün satış verisi bulunamadı.")
    else:
        st.dataframe(product_summary.head(20).style.format({"revenue": "{:,.2f} TL", "qty": "{:,.0f}", "gross_profit": "{:,.2f} TL", "stock_units": "{:,.0f}"}), use_container_width=True, hide_index=True)
        top = product_summary.iloc[0]
        ai_box("Top-Seller Yorumu", f"En çok satan ürün {top['product_name']} ve satış adedi {top['qty']:.0f}.", "Top-seller ürünler reklam ve stok tarafında önceliklendirilebilir.", "Top-seller ürünün stoğu zayıfsa satış kaçırma riski oluşur.", "Bu ürün için stok, reklam ve kreatif varyasyonlarını ayrı takip et.", "Yüksek")

elif selected_report == "Ölü Stok Alarmı":
    st.markdown("### Ölü / Düşük Stok Alarmı")
    if product_summary.empty:
        st.info("Stok alarmı için ürün verisi bulunamadı.")
    else:
        low_stock = product_summary[product_summary["stock_units"].fillna(999999) <= low_stock_threshold].sort_values("stock_units")
        no_sales_stock = product_summary[(product_summary["qty"].fillna(0) <= 0) & (product_summary["stock_units"].fillna(0) > low_stock_threshold)]
        c1, c2 = st.columns(2)
        with c1:
            st.write("Düşük stok ürünleri")
            st.dataframe(low_stock, use_container_width=True, hide_index=True)
        with c2:
            st.write("Satışı zayıf / ölü stok adayları")
            st.dataframe(no_sales_stock, use_container_width=True, hide_index=True)
        ai_box("Ölü Stok Alarmı", f"Düşük stok ürün sayısı {len(low_stock)}, satışı zayıf stok adayı {len(no_sales_stock)}.", "Stok görünürlüğü olan ürünlerde besleme kararı daha sağlıklı yapılabilir.", "Top-seller ürünlerde stok azalırsa reklam bütçesi boşa gidebilir; ölü stokta ise nakit bağlanır.", "Düşük stok top-seller ürünleri önceliklendir; satışı zayıf ürünler için indirim veya bundle planı yap.", "Yüksek")

elif selected_report == "Kanal Karlılık Kıyaslaması":
    st.markdown("### Kanal Karlılık Kıyaslaması")
    if platform_summary.empty:
        st.info("Kanal kıyaslaması için veri bulunamadı.")
    else:
        st.dataframe(platform_summary.sort_values("net_profit_after_ads", ascending=False).style.format({"net_revenue": "{:,.2f} TL", "orders": "{:,.0f}", "line_revenue": "{:,.2f} TL", "gross_profit": "{:,.2f} TL", "units": "{:,.0f}", "ad_spend": "{:,.2f} TL", "ad_revenue": "{:,.2f} TL", "net_profit_after_ads": "{:,.2f} TL", "aov": "{:,.2f} TL", "roas": "{:.2f}", "cost_match_ratio": "{:.1%}"}), use_container_width=True, hide_index=True)
        best = platform_summary.sort_values("net_profit_after_ads", ascending=False).iloc[0]
        ai_box("Kanal Karlılık Yorumu", f"En kârlı kanal şu an {best['platform']} görünüyor.", "Kanal bazlı ayrım bütçe ve stok kararını netleştirir.", "Sadece ciroya göre karar verilirse kârsız kanal büyütülebilir.", "Net kârı yüksek kanala ürün ve reklam önceliği ver; düşük kârlı kanalda maliyetleri kontrol et.", "Yüksek")

elif selected_report == "Kampanya Bazlı ROAS":
    st.markdown("### Kampanya Bazlı ROAS")
    if ads.empty and creative_summary.empty:
        st.info("Kampanya bazlı ROAS için reklam veya kreatif verisi bulunamadı.")
    else:
        if not ads.empty:
            campaign_ads = ads.groupby(["platform", "campaign_name"], as_index=False).agg(spend=("spend", "sum"), revenue=("attributed_revenue", "sum"))
            campaign_ads["roas"] = campaign_ads.apply(lambda r: safe_divide(r["revenue"], r["spend"]), axis=1)
            st.write("Finans hesabına dahil reklam kaynakları")
            st.dataframe(campaign_ads.sort_values("roas", ascending=False), use_container_width=True, hide_index=True)
        if not creative_summary.empty:
            st.write("Kreatif raporundaki kampanya sinyalleri")
            campaign = creative_summary.groupby("campaign_name", as_index=False).agg(spend=("spend", "sum"), revenue=("attributed_revenue", "sum"), purchases=("purchases", "sum"), reach=("reach", "sum"))
            campaign["roas"] = campaign.apply(lambda r: safe_divide(r["revenue"], r["spend"]), axis=1)
            st.dataframe(campaign.sort_values("roas", ascending=False), use_container_width=True, hide_index=True)
            fig = px.bar(campaign.sort_values("roas", ascending=False).head(15), x="campaign_name", y="roas", title="Kreatif Raporu - Kampanya Bazlı ROAS")
            st.plotly_chart(fig, use_container_width=True)
    ai_box("Kampanya Bazlı ROAS Yorumu", f"Finans ROAS {overall_roas:.2f}.", "ROAS yüksek kampanyalar ölçekleme için adaydır.", "Düşük ROAS kampanyalar kârı hızlı şekilde eritebilir.", "ROAS 3+ kampanyaları ölçekle, 1.5 altı kampanyalarda kreatif/hedefleme yenile.", "Yüksek")

elif selected_report == "Kreatif Karnesi":
    st.markdown("### Kreatif Karnesi")
    if creative_summary.empty:
        st.info("Kreatif karnesi için kreatif raporu bulunamadı.")
    else:
        st.dataframe(creative_summary.sort_values(["decision", "roas"], ascending=[True, False]).style.format({"spend": "{:,.2f} TL", "reach": "{:,.0f}", "impressions": "{:,.0f}", "results": "{:,.0f}", "purchases": "{:,.0f}", "attributed_revenue": "{:,.2f} TL", "roas": "{:.2f}", "cac": "{:,.2f} TL", "ctr": "{:.2f}", "cpc": "{:,.2f}", "cpm": "{:,.2f}", "frequency": "{:.2f}"}), use_container_width=True, hide_index=True)
        scale_count = int((creative_summary["decision"] == "Ölçekle").sum())
        stop_count = int((creative_summary["decision"] == "Durdurmayı Değerlendir").sum())
        ai_box("Kreatif Karnesi Yorumu", f"Ölçekleme adayı {scale_count}, durdurma/değiştirme adayı {stop_count} kreatif var.", "Kreatif bazlı karar ile reklam bütçesi daha kontrollü yönetilir.", "Aynı kreatif uzun süre dönerse frekans ve yorgunluk riski artar.", "Kazanan kreatiflerin varyasyonlarını üret; düşük ROAS kreatifleri yenile veya durdur.", "Yüksek")

elif selected_report == "CAC ve Müşteri Edinme Yorumu":
    durum = f"CAC yaklaşık {money(cac)}. Reklam harcaması {money(ad_spend)}, manuel yeni müşteri girişi {new_customer_count:,}."
    guclu = "CAC, LTV'nin altında kaldığında müşteri edinimi sağlıklı kabul edilir."
    risk = "Yeni müşteri verisi yoksa CAC tahmini eksik kalır. Reklam harcamasını alışveriş sayısına bölmek tam müşteri CAC'i vermez."
    aksiyon = "Shopify müşteri tipini veya müşteri ID/e-posta bazlı raporu ekleyerek gerçek CAC hesaplamasını güçlendir."
    ai_box("CAC ve Müşteri Edinme Yorumu", durum, guclu, risk, aksiyon, "Orta")

elif selected_report == "Yeni vs. Geri Gelen Müşteri":
    total_customers = new_customer_count + returning_customer_count
    new_rate = safe_divide(new_customer_count, total_customers) * 100
    returning_rate = safe_divide(returning_customer_count, total_customers) * 100
    ai_box("Yeni vs. Geri Gelen Müşteri", f"Manuel veriye göre yeni müşteri oranı {pct(new_rate)}, geri gelen müşteri oranı {pct(returning_rate)}.", "Geri gelen müşteri oranı yükselirse reklam maliyeti baskısı azalır.", "Bu veri manuel girilmediyse veya müşteri bazlı dosya yoksa analiz sınırlıdır.", "Tekrar satın alma için WhatsApp/e-posta akışı, sadakat indirimi ve aksesuar bundle kampanyası kurulabilir.")

elif selected_report == "Sepet Ortalaması (AOV)":
    ai_box("Sepet Ortalaması (AOV)", f"AOV şu an {money(aov)}.", "AOV yüksekse reklam maliyetini taşıma kapasitesi artar.", "AOV düşükse aynı reklam harcamasıyla daha düşük kâr oluşur.", "Bundle, 2. ürün indirimi, ücretsiz kargo eşiği ve hediye kutusu upsell testleri yap.")

elif selected_report == "LTV Yorumu":
    ai_box("LTV Yorumu", f"Tahmini LTV {money(ltv)}. Hesap: AOV x müşteri başı ortalama satın alma adedi.", "LTV yüksekse daha yüksek CAC tolere edilebilir.", "Gerçek müşteri tekrar satın alma verisi olmadan LTV tahmini sınırlıdır.", "Müşteri bazlı satış geçmişi eklenirse gerçek LTV ve tekrar satın alma oranı hesaplanabilir.")

elif selected_report == "İş Birliği Performansı":
    ai_box("İş Birliği Performansı", "Bu bölüm için influencer/iş birliği bazlı harcama, kupon kodu, link tıklaması ve satış dosyası gerekir.", "Kupon/link bazlı veri gelirse hangi iş birliğinin satışa döndüğü net ölçülür.", "Sadece erişim/veri ile karar verilirse satış getirmeyen iş birlikleri iyi görünebilir.", "Partner adı, harcama/ücret, erişim, tıklama, satış, ciro ve ROAS kolonlarını içeren CSV ekle.", "Orta")

elif selected_report == "Erişim vs. Dönüşüm":
    st.markdown("### Erişim vs. Dönüşüm")
    if creative_summary.empty:
        st.info("Erişim vs dönüşüm için kreatif raporu bulunamadı.")
    else:
        fig = px.scatter(creative_summary, x="reach", y="purchases", size="spend", color="roas", hover_data=["campaign_name", "creative_name", "ctr", "frequency", "decision"], title="Erişim vs Satın Alma")
        st.plotly_chart(fig, use_container_width=True)
        weak = creative_summary[(creative_summary["reach"] >= creative_summary["reach"].quantile(0.7)) & (creative_summary["purchases"] <= creative_summary["purchases"].median())]
        st.write("Yüksek erişim / düşük dönüşüm adayları")
        st.dataframe(weak, use_container_width=True, hide_index=True)
        ai_box("Erişim vs. Dönüşüm Yorumu", f"Yüksek erişim-düşük dönüşüm adayı {len(weak)} kreatif var.", "Erişim güçlüyse kreatif dikkat çekiyor olabilir.", "Dönüşüm düşükse teklif, ürün sayfası, fiyat veya güven sorunu olabilir.", "Yüksek erişim ama düşük satın alma getiren kreatiflerde ürün sayfası ve mesaj uyumunu kontrol et.", "Yüksek")

elif selected_report == "30 Günlük Satış Tahmini":
    forecast_orders = safe_divide(known_order_count, active_days) * 30
    forecast_profit = safe_divide(gross_profit, active_days) * 30 - fixed_costs_30d
    ai_box("30 Günlük Satış Tahmini", f"Son veri hızına göre 30 günlük ciro tahmini {money(forecast_30d_revenue)}, bilinen sipariş tahmini {forecast_orders:,.0f}, kâr tahmini {money(forecast_profit)}.", "Mevcut satış hızı korunursa planlama için temel tahmin oluşur.", "Kampanya, stok ve sezon etkisi tahmini değiştirebilir. Hepsiburada snapshot tarihli olmadığı için tahmini bozabilir.", "Tahmini top-seller ürünlerin stoklarıyla karşılaştır ve reklam bütçesini kâr hedefiyle sınırla.", "Yüksek")

elif selected_report == "Stok Besleme Planı":
    st.markdown("### Stok Besleme Planı")
    if product_summary.empty:
        st.info("Stok besleme planı için ürün verisi yok.")
    else:
        plan = product_summary.copy()
        plan["daily_qty"] = plan["qty"] / max(active_days, 1)
        plan["needed_for_lead_days"] = plan["daily_qty"] * stock_lead_days
        plan["recommended_restock"] = (plan["needed_for_lead_days"] - plan["stock_units"].fillna(0)).clip(lower=0)
        plan = plan.sort_values("recommended_restock", ascending=False)
        st.dataframe(plan[["platform", "product_name", "qty", "stock_units", "daily_qty", "needed_for_lead_days", "recommended_restock"]].style.format({"qty": "{:,.0f}", "stock_units": "{:,.0f}", "daily_qty": "{:,.2f}", "needed_for_lead_days": "{:,.0f}", "recommended_restock": "{:,.0f}"}), use_container_width=True, hide_index=True)
        ai_box("Stok Besleme Planı", f"Tedarik süresi {stock_lead_days} gün kabul edildi.", "Satış hızına göre stok besleme, satış kaçırma riskini azaltır.", "Stok verisi eksik ürünlerde öneri hatalı olabilir.", "Top-seller + düşük stok ürünlerini öncele; ölü stok ürünlere yeni alım yapma.", "Yüksek")

elif selected_report == "Nakit Akış Projeksiyonu":
    projected_gross_profit = safe_divide(gross_profit, active_days) * 30
    projected_ad_spend = safe_divide(ad_spend, active_days) * 30
    projected_cash = current_cash + projected_gross_profit - projected_ad_spend - fixed_costs_30d - planned_stock_purchase
    ai_box("Nakit Akış Projeksiyonu", f"30 gün sonunda tahmini nakit: {money(projected_cash)}. Mevcut nakit {money(current_cash)}, tahmini brüt kâr {money(projected_gross_profit)}, tahmini reklam harcaması {money(projected_ad_spend)}.", "Nakit projeksiyonu reklam ve stok kararlarını birlikte görmeyi sağlar.", "Tahsilat gecikmesi, iade ve ek stok alımı projeksiyonu bozabilir.", "Nakit negatife düşüyorsa reklam ölçeklemeyi sınırlı tut, stok alımını top-seller ürünlerle sınırla.", "Yüksek" if projected_cash < 0 else "Orta")

elif selected_report == "Yapay Zeka Notu" or selected_report == "Genel Yönetici Özeti":
    st.markdown("### Yapay Zeka Notu")
    st.markdown(create_general_note())

else:
    st.info("Bu başlık için yorum hazırlanıyor.")


# =========================================================
# DASHBOARD TABS
# =========================================================
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Genel Veri", "🏪 Kanal Kıyaslama", "📦 Ürün & Stok", "📣 Reklam & Kreatif", "🧪 Veri Durumu"])

with tab1:
    st.subheader("Genel Özet")
    summary_df = pd.DataFrame([
        {"Metrik": "Net Ciro", "Değer": money(total_revenue)},
        {"Metrik": "Bilinen Sipariş Adedi", "Değer": f"{known_order_count:,}"},
        {"Metrik": "Hedef Gerçekleşme", "Değer": pct(target_rate)},
        {"Metrik": "Anlık Net Kar", "Değer": money(net_profit_now)},
        {"Metrik": "Brüt Kar", "Değer": money(gross_profit)},
        {"Metrik": "Reklam Harcaması", "Değer": money(ad_spend)},
        {"Metrik": "Reklam Geliri", "Değer": money(ad_revenue)},
        {"Metrik": "ROAS", "Değer": f"{overall_roas:.2f}"},
        {"Metrik": "AOV", "Değer": money(aov)},
        {"Metrik": "CAC", "Değer": money(cac)},
        {"Metrik": "LTV Tahmini", "Değer": money(ltv)},
        {"Metrik": "Aktif Gün Sayısı", "Değer": f"{active_days}"},
    ])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Kanal Karlılık Kıyaslaması")
    if platform_summary.empty:
        st.info("Kanal verisi bulunamadı.")
    else:
        st.dataframe(platform_summary.sort_values("net_profit_after_ads", ascending=False).style.format({
            "net_revenue": "{:,.2f} TL", "orders": "{:,.0f}", "line_revenue": "{:,.2f} TL", "gross_profit": "{:,.2f} TL",
            "units": "{:,.0f}", "ad_spend": "{:,.2f} TL", "ad_revenue": "{:,.2f} TL", "net_profit_after_ads": "{:,.2f} TL",
            "aov": "{:,.2f} TL", "roas": "{:.2f}", "cost_match_ratio": "{:.1%}",
        }), use_container_width=True, hide_index=True)
        fig = px.bar(platform_summary, x="platform", y="net_profit_after_ads", title="Kanal Bazlı Net Kâr")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Ürün ve Stok")
    if product_summary.empty:
        st.info("Ürün verisi bulunamadı.")
    else:
        st.dataframe(product_summary.head(80).style.format({"revenue": "{:,.2f} TL", "qty": "{:,.0f}", "gross_profit": "{:,.2f} TL", "stock_units": "{:,.0f}"}), use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Reklam ve Kreatif")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Finans Toplamına Dahil Reklam Verisi")
        if ads.empty:
            st.info("Finans toplamına dahil reklam verisi bulunamadı.")
        else:
            ad_view = ads.groupby(["platform", "spend_source", "campaign_name"], as_index=False).agg(spend=("spend", "sum"), attributed_revenue=("attributed_revenue", "sum"))
            ad_view["roas"] = ad_view.apply(lambda r: safe_divide(r["attributed_revenue"], r["spend"]), axis=1)
            st.dataframe(ad_view.sort_values("spend", ascending=False).style.format({"spend": "{:,.2f} TL", "attributed_revenue": "{:,.2f} TL", "roas": "{:.2f}"}), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### Kreatif Karnesi")
        if creative_summary.empty:
            st.info("Kreatif verisi bulunamadı.")
        else:
            st.dataframe(creative_summary.sort_values("roas", ascending=False).head(30).style.format({"spend": "{:,.2f} TL", "reach": "{:,.0f}", "impressions": "{:,.0f}", "results": "{:,.0f}", "purchases": "{:,.0f}", "attributed_revenue": "{:,.2f} TL", "ctr": "{:.2f}", "cpc": "{:,.2f}", "cpm": "{:,.2f}", "frequency": "{:.2f}", "roas": "{:.2f}", "cac": "{:,.2f} TL"}), use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Veri Durumu ve Kontrol")
    status_rows = []
    for platform, folder in [("Shopify", SHOPIFY_DIR), ("Trendyol", TRENDYOL_DIR), ("Hepsiburada", HEPSIBURADA_DIR), ("Kreatif", KREATIF_DIR)]:
        status_rows.append({"Alan": f"{platform} klasörü", "Durum": "Var" if folder.exists() else "Yok", "Yol": str(folder)})
    status_rows += [
        {"Alan": "Sipariş verisi", "Durum": "Var" if not orders_all.empty else "Eksik", "Yol": "-"},
        {"Alan": "Ürün verisi", "Durum": "Var" if not lines_all.empty else "Eksik", "Yol": "-"},
        {"Alan": "Finans reklam verisi", "Durum": "Var" if not ads_all.empty else "Eksik", "Yol": "-"},
        {"Alan": "Kreatif verisi", "Durum": "Var" if not creative_all.empty else "Eksik", "Yol": "-"},
    ]
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

    st.markdown("#### AI toplamı hangi veriden alıyor?")
    if platform_summary.empty:
        st.info("Platform özeti üretilemedi.")
    else:
        audit = platform_summary.copy()
        st.dataframe(audit.style.format({
            "net_revenue": "{:,.2f} TL", "orders": "{:,.0f}", "line_revenue": "{:,.2f} TL", "gross_profit": "{:,.2f} TL",
            "units": "{:,.0f}", "ad_spend": "{:,.2f} TL", "ad_revenue": "{:,.2f} TL", "net_profit_after_ads": "{:,.2f} TL",
            "aov": "{:,.2f} TL", "roas": "{:.2f}", "cost_match_ratio": "{:.1%}",
        }), use_container_width=True, hide_index=True)

    if model.get("warnings"):
        st.markdown("#### Uyarılar")
        for w in model["warnings"]:
            st.warning(w)

    if not model.get("data_debug", pd.DataFrame()).empty:
        st.markdown("#### Satış Dosyası Okuma Logları")
        st.dataframe(model["data_debug"], use_container_width=True, hide_index=True)
    if not model.get("ads_debug", pd.DataFrame()).empty:
        st.markdown("#### Reklam Dosyası Okuma Logları")
        st.dataframe(model["ads_debug"], use_container_width=True, hide_index=True)

    st.markdown(
        """
        **Yeni mantık:**
        - Shopify / Trendyol / Hepsiburada satışları merkezi modelde toplanır.
        - Platform bazlı reklam dosyaları finans hesabına dahil edilir.
        - Kreatif raporu varsayılan olarak sadece yorum/kreatif kararı için kullanılır; finans toplamına eklenmez.
        - Böylece aynı Meta harcamasının iki kez düşülmesi engellenir.
        """
    )
