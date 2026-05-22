
from __future__ import annotations
import io, re, unicodedata
from pathlib import Path
from typing import Optional
import pandas as pd
import streamlit as st

def normalize_text(x):
    if x is None or pd.isna(x): return ""
    s=str(x).lower().strip().translate(str.maketrans({"ı":"i","İ":"i","ş":"s","Ş":"s","ğ":"g","Ğ":"g","ç":"c","Ç":"c","ö":"o","Ö":"o","ü":"u","Ü":"u"}))
    s=unicodedata.normalize("NFKD",s)
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ",s)).strip()

def to_float(x):
    if x is None or pd.isna(x) or x=="": return 0.0
    if isinstance(x,(int,float)): return float(x)
    s=str(x).replace("TL","").replace("TRY","").replace("₺","").replace("%","").replace('"',"").replace("\xa0","").replace(" ","").strip()
    if s.lower() in ["-","nan","none","null","n/a"]: return 0.0
    if "," in s and "." in s: s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    elif "," in s: s=s.replace(".","").replace(",",".")
    elif "." in s:
        parts=s.split(".")
        if len(parts)>1 and all(p.isdigit() for p in parts) and all(len(p)==3 for p in parts[1:]): s="".join(parts)
    try: return float(s)
    except Exception:
        try: return float(re.sub(r"[^0-9.\-]","",s))
        except Exception: return 0.0

def money(v): return f"{float(v):,.2f} TL"
def safe_divide(a,b): return float(a)/float(b) if b else 0.0
def clean_sku(x):
    if x is None or pd.isna(x): return ""
    s=str(x).strip().replace(" ","").replace("'","").replace("-","")
    if re.fullmatch(r"\d+\.0",s): s=s[:-2]
    try:
        if "e+" in s.lower(): s=str(int(float(s)))
    except Exception: pass
    return s

def find_col(df,cands):
    mp={normalize_text(c):c for c in df.columns}
    for c in cands:
        t=normalize_text(c)
        for k,v in mp.items():
            if t==k: return v
    for c in cands:
        t=normalize_text(c)
        for k,v in mp.items():
            if t and t in k: return v
    return None

def read_uploaded_file(f):
    data=f.getvalue()
    if f.name.lower().endswith((".xlsx",".xls")):
        for skip in [0,1,2,3,4,5]:
            try:
                df=pd.read_excel(io.BytesIO(data),dtype=str,skiprows=skip)
                if df.shape[1]>1: return df
            except Exception: pass
        return pd.DataFrame()
    for enc in ["utf-8-sig","utf-8","cp1254","iso-8859-9","latin1"]:
        for sep in [",",";","\t"]:
            try:
                df=pd.read_csv(io.BytesIO(data),encoding=enc,sep=sep,dtype=str,low_memory=False)
                if df.shape[1]>1: return df
            except Exception: pass
    return pd.DataFrame()

def root(): return Path(__file__).resolve().parents[1]
def manual_path(): return root()/"manual_entries.csv"
def ensure_manual():
    if not manual_path().exists():
        pd.DataFrame(columns=["date","platform","store_name","product_name","units_sold","order_count","total_revenue","ad_spend","notes"]).to_csv(manual_path(),index=False,encoding="utf-8-sig")
def load_manual(platform=None):
    ensure_manual(); df=pd.read_csv(manual_path(),dtype=str)
    for c in ["units_sold","order_count","total_revenue","ad_spend"]:
        df[c]=df[c].apply(to_float) if c in df.columns else 0.0
    if platform: df=df[df["platform"].astype(str).str.lower()==platform.lower()].copy()
    return df
def manual_form(platform):
    with st.expander("✍️ Manuel Günlük Giriş", expanded=False):
        with st.form(f"manual_{platform}"):
            a,b,c=st.columns(3)
            with a:
                d=st.date_input("Tarih"); store=st.text_input("Mağaza/Kanal", value=platform); product=st.text_input("Ürün adı")
            with b:
                units=st.number_input("Satılan ürün adedi",0,step=1); orders=st.number_input("Sipariş adedi",0,step=1); rev=st.number_input("Net ciro / Total Revenue",0.0,step=100.0)
            with c:
                ad=st.number_input("Reklam harcaması",0.0,step=100.0); notes=st.text_area("Not")
            if st.form_submit_button("Ekle"):
                df=load_manual()
                row={"date":str(d),"platform":platform,"store_name":store,"product_name":product,"units_sold":units,"order_count":orders,"total_revenue":rev,"ad_spend":ad,"notes":notes}
                pd.concat([df,pd.DataFrame([row])],ignore_index=True).to_csv(manual_path(),index=False,encoding="utf-8-sig")
                st.success("Manuel veri eklendi."); st.rerun()

def init_upload_state(platform):
    for k in ["sales","cost","ads"]: st.session_state.setdefault(f"{platform}_{k}_files",[])
def save_uploads(platform,kind,files):
    if files: st.session_state[f"{platform}_{kind}_files"]=[{"name":f.name,"bytes":f.getvalue()} for f in files]
def files_from_state(platform,kind):
    out=[]
    for item in st.session_state.get(f"{platform}_{kind}_files",[]):
        class O: pass
        o=O(); o.name=item["name"]; o.getvalue=lambda b=item["bytes"]: b; out.append(o)
    return out
def upload_boxes(platform):
    init_upload_state(platform)
    st.subheader("Dosya Yükleme")
    st.warning("Veri karışmasın diye satış, maliyet ve reklam dosyalarını ayrı kutulara yükle.")
    c1,c2,c3=st.columns(3)
    with c1:
        s=st.file_uploader(f"{platform} satış/sipariş dosyaları",type=["csv","xlsx","xls"],accept_multiple_files=True,key=f"{platform}_sales_up")
        if s: save_uploads(platform,"sales",s)
    with c2:
        c=st.file_uploader(f"{platform} maliyet dosyaları",type=["csv","xlsx","xls"],accept_multiple_files=True,key=f"{platform}_cost_up")
        if c: save_uploads(platform,"cost",c)
    with c3:
        a=st.file_uploader(f"{platform} reklam dosyaları",type=["csv","xlsx","xls"],accept_multiple_files=True,key=f"{platform}_ads_up")
        if a: save_uploads(platform,"ads",a)
    st.caption(f"Yüklü: Satış {len(files_from_state(platform,'sales'))} | Maliyet {len(files_from_state(platform,'cost'))} | Reklam {len(files_from_state(platform,'ads'))}")

def load_cost(platform):
    frames=[]
    for f in files_from_state(platform,"cost"):
        df=read_uploaded_file(f)
        if df.empty: continue
        sku=find_col(df,["SKU","Barkod","Barcode","Stok Kodu"])
        cost=find_col(df,["Maliyet","Maliyet Alış","Cost"])
        comm=find_col(df,["Komisyon oran","Komisyon","Commission"])
        ship=find_col(df,["Kargo","Shipping"])
        if not sku: continue
        x=pd.DataFrame({"sku_key":df[sku].apply(clean_sku),"unit_cost":df[cost].apply(to_float) if cost else 0.0,"commission_rate":df[comm].apply(to_float) if comm else 0.0,"unit_shipping":df[ship].apply(to_float) if ship else 0.0})
        x["commission_rate"]=x["commission_rate"].apply(lambda v:v/100 if v>1 else v)
        frames.append(x)
    if not frames: return pd.DataFrame(columns=["sku_key","unit_cost","commission_rate","unit_shipping"])
    r=pd.concat(frames,ignore_index=True)
    return r[r["sku_key"]!=""].drop_duplicates("sku_key",keep="last")

def load_ads(platform):
    frames=[]; debug=[]
    for f in files_from_state(platform,"ads"):
        df=read_uploaded_file(f)
        if df.empty: debug.append({"file":f.name,"status":"ERROR"}); continue
        spend=find_col(df,["Harcanan Tutar","Amount spent","Spend","Harcama","Tutar","Amount"])
        rev=find_col(df,["Reklam Geliri","Total Ad Revenue","Revenue","Dönüşüm değeri","Satis Tutari","Satış Tutarı"])
        pur=find_col(df,["Alışverişler","Purchases","Sipariş","Orders"])
        date=find_col(df,["Tarih","Date","Day"])
        if not spend: debug.append({"file":f.name,"status":"NO_SPEND_COLUMN","columns":", ".join(map(str,df.columns[:12]))}); continue
        out=pd.DataFrame({"date":pd.to_datetime(df[date],errors="coerce",dayfirst=True) if date else pd.NaT,"ad_spend":df[spend].apply(to_float),"ad_revenue":df[rev].apply(to_float) if rev else 0.0,"ad_purchases":df[pur].apply(to_float) if pur else 0.0,"source_file":f.name})
        out=out[(out["ad_spend"]>0)|(out["ad_revenue"]>0)|(out["ad_purchases"]>0)]
        frames.append(out); debug.append({"file":f.name,"status":"OK","rows":len(out),"spend_col":spend,"revenue_col":rev or ""})
    ads=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=["date","ad_spend","ad_revenue","ad_purchases","source_file"])
    return ads,pd.DataFrame(debug)

def add_costs(lines,costs):
    if lines.empty:
        lines["matched_cost"]=[]; lines["gross_profit"]=[]; return lines
    lines=lines.merge(costs,on="sku_key",how="left")
    for c in ["unit_cost","commission_rate","unit_shipping"]: lines[c]=lines[c].fillna(0.0)
    lines["matched_cost"]=lines["unit_cost"].gt(0)
    lines["gross_profit"]=lines["line_revenue"]-((lines["unit_cost"]+lines["unit_shipping"])*lines["qty"])-(lines["line_revenue"]*lines["commission_rate"])
    return lines

def load_shopify_sales():
    raws=[]; debug=[]
    for f in files_from_state("Shopify","sales"):
        df=read_uploaded_file(f)
        if df.empty or not {"Name","Created at","Lineitem name"}.issubset(set(df.columns)):
            debug.append({"file":f.name,"status":"ERROR","reason":"Shopify sipariş formatı değil"}); continue
        df["source_file"]=f.name; raws.append(df); debug.append({"file":f.name,"status":"OK","rows":len(df)})
    raw=pd.concat(raws,ignore_index=True) if raws else pd.DataFrame()
    if raw.empty: return pd.DataFrame(),pd.DataFrame(),pd.DataFrame(debug)
    for c in ["Total","Refunded Amount","Lineitem quantity","Lineitem price","Lineitem discount"]:
        raw[c]=raw[c].apply(to_float) if c in raw.columns else 0.0
    for c in ["Cancelled at","Financial Status","Lineitem sku","Lineitem name","Created at"]:
        if c not in raw.columns: raw[c]=""
    raw["order_name"]=raw["Name"].astype(str)
    raw["order_date"]=pd.to_datetime(raw["Created at"],errors="coerce",utc=True).dt.tz_localize(None)
    raw["cancelled_at"]=pd.to_datetime(raw["Cancelled at"],errors="coerce",utc=True).dt.tz_localize(None)
    raw["financial_status"]=raw["Financial Status"].astype(str).str.lower()
    raw=raw.drop_duplicates(subset=[c for c in ["Name","Created at","Lineitem sku","Lineitem name","Lineitem quantity","Lineitem price","Total"] if c in raw.columns],keep="first")
    orders=raw.groupby("order_name",as_index=False).agg(order_date=("order_date","first"),total=("Total","first"),refunded=("Refunded Amount","first"),cancelled_at=("cancelled_at","first"),financial_status=("financial_status","first"),source_file=("source_file","first"))
    orders["is_cancelled"]=orders["cancelled_at"].notna()|orders["financial_status"].isin(["voided","cancelled","canceled"])
    orders["net_sales"]=orders["total"]-orders["refunded"]; orders.loc[orders["is_cancelled"],"net_sales"]=0.0; orders["order_count"]=(~orders["is_cancelled"]).astype(int)
    lines=raw.copy()
    lines["sku_key"]=lines["Lineitem sku"].apply(clean_sku); lines["product_name"]=lines["Lineitem name"].astype(str); lines["qty"]=lines["Lineitem quantity"].apply(to_float)
    lines["line_revenue"]=lines["Lineitem price"].apply(to_float)*lines["qty"]-lines["Lineitem discount"].apply(to_float)
    lines.loc[lines["order_name"].isin(orders.loc[orders["is_cancelled"],"order_name"]),["qty","line_revenue"]]=0.0
    return orders,lines[["order_name","order_date","sku_key","product_name","qty","line_revenue","source_file"]].copy(),pd.DataFrame(debug)

def load_market_sales(platform):
    frames=[]; debug=[]
    for f in files_from_state(platform,"sales"):
        df=read_uploaded_file(f)
        if df.empty: debug.append({"file":f.name,"status":"ERROR"}); continue
        date=find_col(df,["Sipariş Tarihi","Tarih","Order Date","Date"])
        order=find_col(df,["Sipariş Numarası","Sipariş No","Order Number","Order","Paket No"])
        product=find_col(df,["Ürün Adı","Product Name","Product"])
        sku=find_col(df,["Barkod","SKU","Stok Kodu","Merchant SKU"])
        qty=find_col(df,["Adet","Miktar","Quantity","Ürün Adedi","Satış Miktarı"])
        rev=find_col(df,["Faturalanacak Tutar","Net Satış Tutarı","Satış Tutarı","Ürün Tutarı","Sipariş Tutarı","Toplam Satış Tutarı","Mağazanın Brüt Cirosu","Ciro","Tutar","Amount","Revenue"])
        status=find_col(df,["Sipariş Statüsü","Durum","Status"])
        if not rev: debug.append({"file":f.name,"status":"NO_REVENUE_COLUMN","columns":", ".join(map(str,df.columns[:15]))}); continue
        out=pd.DataFrame({"order_name":df[order].astype(str) if order else f.name,"order_date":pd.to_datetime(df[date],errors="coerce",dayfirst=True) if date else pd.NaT,"product_name":df[product].astype(str) if product else platform+" Product","sku_key":df[sku].apply(clean_sku) if sku else "","qty":df[qty].apply(to_float) if qty else 1.0,"line_revenue":df[rev].apply(to_float),"status":df[status].astype(str) if status else "","source_file":f.name})
        bad=out["status"].str.contains("iptal|iade|cancel|return|red",case=False,na=False)
        out.loc[bad,["qty","line_revenue"]]=0.0; out=out[out["line_revenue"].fillna(0)>=0]
        frames.append(out); debug.append({"file":f.name,"status":"OK","rows":len(out),"revenue_col":rev})
    lines=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=["order_name","order_date","product_name","sku_key","qty","line_revenue","source_file"])
    if not lines.empty:
        orders=lines.groupby("order_name",as_index=False).agg(order_date=("order_date","first"),net_sales=("line_revenue","sum"),qty=("qty","sum"),source_file=("source_file","first"))
        orders["order_count"]=orders["net_sales"].gt(0).astype(int)
    else: orders=pd.DataFrame(columns=["order_name","order_date","net_sales","qty","source_file","order_count"])
    return orders,lines,pd.DataFrame(debug)

def platform_data(platform):
    if platform=="Shopify": orders,lines,ds=load_shopify_sales()
    else: orders,lines,ds=load_market_sales(platform)
    costs=load_cost(platform); ads,da=load_ads(platform); lines=add_costs(lines,costs)
    m=load_manual(platform)
    mr=m["total_revenue"].sum() if not m.empty else 0.0; mo=m["order_count"].sum() if not m.empty else 0.0; mu=m["units_sold"].sum() if not m.empty else 0.0; ma=m["ad_spend"].sum() if not m.empty else 0.0
    total=(orders["net_sales"].sum() if not orders.empty else 0.0)+mr
    oc=(orders["order_count"].sum() if not orders.empty and "order_count" in orders else 0.0)+mo
    units=(lines["qty"].sum() if not lines.empty else 0.0)+mu
    gross=(lines["gross_profit"].sum() if not lines.empty else 0.0)+mr
    spend=(ads["ad_spend"].sum() if not ads.empty else 0.0)+ma
    adrev=0.0 if platform=="Shopify" else (ads["ad_revenue"].sum() if not ads.empty else 0.0)
    metrics={"total_revenue":total,"order_count":oc,"units_sold":units,"aov":safe_divide(total,oc),"gross_profit_before_ads":gross,"total_ad_spend":spend,"total_ad_revenue":adrev,"roas":safe_divide(adrev,spend),"net_profit_after_ads":gross-spend,"mer":safe_divide(total,spend),"cost_match_rate":float(lines["matched_cost"].mean()) if not lines.empty else 0.0}
    debug=pd.concat([ds,da],ignore_index=True) if (not ds.empty or not da.empty) else pd.DataFrame()
    return metrics,orders,lines,ads,m,debug

def kpi_cards(metrics, show_ad_revenue=True):
    fields=[("Total Revenue","total_revenue","m"),("Order Count","order_count","i"),("Units Sold","units_sold","i"),("AOV","aov","m"),("Gross Profit Before Ads","gross_profit_before_ads","m"),("Total Ad Spend","total_ad_spend","m")]
    if show_ad_revenue: fields.append(("Total Ad Revenue","total_ad_revenue","m"))
    fields += [("ROAS","roas","r"),("Net Profit After Ads","net_profit_after_ads","m"),("MER","mer","r"),("Cost Match Rate","cost_match_rate","p")]
    for i in range(0,len(fields),4):
        cols=st.columns(4)
        for col,(label,key,typ) in zip(cols,fields[i:i+4]):
            v=metrics.get(key,0.0)
            col.metric(label, money(v) if typ=="m" else (f"{v:,.0f}" if typ=="i" else (f"{v:.2f}" if typ=="r" and v else ("N/A" if typ=="r" else f"{v:.1%}"))))

def show_platform(platform):
    st.header(platform); upload_boxes(platform); manual_form(platform)
    metrics,orders,lines,ads,manual,debug=platform_data(platform)
    kpi_cards(metrics, show_ad_revenue=(platform!="Shopify"))
    if platform=="Shopify": st.info("Shopify Ad Revenue kullanılmaz. Shopify için sadece Total Revenue ve Total Ad Spend alınır.")
    t1,t2,t3,t4,t5=st.tabs(["Satış","Ürün & Kâr","Reklam","Manuel","Debug"])
    with t1:
        if orders.empty: st.warning("Satış verisi yok. Satış dosyasını satış kutusuna yükle.")
        else:
            st.dataframe(orders.groupby("source_file",as_index=False).agg(order_count=("order_count","sum"),total_revenue=("net_sales","sum")),use_container_width=True,hide_index=True)
            st.dataframe(orders,use_container_width=True,hide_index=True)
    with t2:
        if not lines.empty:
            product=lines.groupby(["product_name","sku_key"],as_index=False).agg(units_sold=("qty","sum"),revenue=("line_revenue","sum"),gross_profit=("gross_profit","sum"),matched_cost=("matched_cost","max"))
            st.dataframe(product.sort_values("revenue",ascending=False),use_container_width=True,hide_index=True)
    with t3: st.dataframe(ads,use_container_width=True,hide_index=True)
    with t4: st.dataframe(manual,use_container_width=True,hide_index=True)
    with t5:
        st.dataframe(debug,use_container_width=True,hide_index=True)
        st.dataframe(pd.DataFrame([metrics]),use_container_width=True,hide_index=True)
