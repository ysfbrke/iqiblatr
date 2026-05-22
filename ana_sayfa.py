from pathlib import Path
import re, unicodedata, csv
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='IQIBLA Türkiye Panel', layout='wide')
BASE = Path(__file__).resolve().parent
MANUAL = BASE / 'manual_entries.csv'
PASSWORD = '1234'

st.markdown('''<style>.stApp{background:linear-gradient(135deg,#050505,#151515);color:white}.block-container{max-width:1450px;padding-top:2rem}[data-testid="stMetric"]{background:rgba(255,255,255,.06);border:1px solid rgba(212,175,55,.25);border-radius:16px;padding:14px}div.stButton>button{border-radius:14px;font-weight:800;background:linear-gradient(135deg,#d4af37,#9d7417);color:#111;border:0}</style>''', unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title('IQIBLA Türkiye Panel')
    st.subheader('Şifreli Giriş')
    pw = st.text_input('Şifre', type='password')
    if st.button('Giriş Yap'):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error('Şifre yanlış')
    st.info('Varsayılan şifre: 1234')
    st.stop()

def norm(x):
    if x is None or pd.isna(x): return ''
    s=str(x).lower().strip()
    s=s.translate(str.maketrans({'ı':'i','İ':'i','ş':'s','Ş':'s','ğ':'g','Ğ':'g','ç':'c','Ç':'c','ö':'o','Ö':'o','ü':'u','Ü':'u'}))
    s=unicodedata.normalize('NFKD',s); s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',s)).strip()

def num(x):
    if x is None or pd.isna(x) or x=='': return 0.0
    if isinstance(x,(int,float)): return float(x)
    s=str(x).replace('TL','').replace('TRY','').replace('₺','').replace('%','').replace('\xa0','').replace(' ','').replace('"','').strip()
    if s.lower() in ['-','nan','none','null','n/a']: return 0.0
    if ',' in s and '.' in s: s=s.replace('.','').replace(',','.') if s.rfind(',')>s.rfind('.') else s.replace(',','')
    elif ',' in s: s=s.replace('.','').replace(',','.')
    elif '.' in s:
        parts=s.split('.')
        if len(parts)>1 and all(p.isdigit() for p in parts) and all(len(p)==3 for p in parts[1:]): s=''.join(parts)
    try: return float(s)
    except Exception:
        try: return float(re.sub(r'[^0-9.\-]','',s))
        except Exception: return 0.0

def money(v): return f'{float(v):,.2f} TL'
def div(a,b): return float(a)/float(b) if b else 0.0
def clean_sku(x):
    if x is None or pd.isna(x): return ''
    s=str(x).strip().replace(' ','').replace("'",'').replace('-','')
    if re.fullmatch(r'\d+\.0',s): s=s[:-2]
    try:
        if 'e+' in s.lower(): s=str(int(float(s)))
    except Exception: pass
    return s

def fcol(df, names):
    mp={norm(c):c for c in df.columns}
    for name in names:
        t=norm(name)
        for k,v in mp.items():
            if k==t: return v
    for name in names:
        t=norm(name)
        for k,v in mp.items():
            if t and t in k: return v
    return None

def read_any(p):
    if p.suffix.lower() in ['.xlsx','.xls']:
        for skip in [0,1,2,3,4,5]:
            try:
                df=pd.read_excel(p,dtype=str,skiprows=skip)
                if df.shape[1]>1: return df,'excel',str(skip)
            except Exception: pass
        return pd.DataFrame(),'',''
    for enc in ['utf-8-sig','utf-8','cp1254','iso-8859-9','latin1']:
        for sep in [',',';','\t']:
            try:
                df=pd.read_csv(p,encoding=enc,sep=sep,dtype=str,low_memory=False)
                if df.shape[1]>1: return df,enc,sep
            except Exception: pass
    return pd.DataFrame(),'',''

def read_shopify(p):
    df,enc,sep=read_any(p)
    if not df.empty and {'Name','Created at','Lineitem name'}.issubset(set(df.columns)): return df,enc,sep
    return pd.DataFrame(),'',''

def read_meta_bill(p):
    try:
        lines=p.read_text(encoding='utf-8-sig',errors='replace').splitlines(); idx=None
        for i,line in enumerate(lines):
            n=norm(line)
            if 'tarih' in n and 'tutar' in n and ('para birimi' in n or 'odeme' in n or 'islem' in n): idx=i; break
        if idx is not None:
            rows=list(csv.reader([l for l in lines[idx:] if l.strip()]))
            if len(rows)>=2: return pd.DataFrame(rows[1:],columns=rows[0])
    except Exception: pass
    df,_,_=read_any(p); return df

def ensure_manual():
    if not MANUAL.exists(): pd.DataFrame(columns=['date','platform','store_name','product_name','units_sold','order_count','total_revenue','ad_spend','notes']).to_csv(MANUAL,index=False,encoding='utf-8-sig')
def load_manual(platform=None):
    ensure_manual(); df=pd.read_csv(MANUAL,dtype=str)
    for c in ['units_sold','order_count','total_revenue','ad_spend']:
        if c not in df.columns: df[c]=0
        df[c]=df[c].apply(num)
    if platform: df=df[df['platform'].astype(str).str.lower()==platform.lower()].copy()
    return df

def manual_form(platform):
    with st.expander('✍️ Manuel Günlük Giriş', expanded=False):
        with st.form('manual_'+platform):
            a,b,c=st.columns(3)
            with a:
                d=st.date_input('Tarih'); store=st.text_input('Mağaza/Kanal',platform); product=st.text_input('Ürün adı')
            with b:
                units=st.number_input('Satılan ürün adedi',0,step=1); orders=st.number_input('Sipariş adedi',0,step=1); rev=st.number_input('Net ciro / Total Revenue',0.0,step=100.0)
            with c:
                ad=st.number_input('Reklam harcaması',0.0,step=100.0); notes=st.text_area('Not')
            if st.form_submit_button('Ekle'):
                df=load_manual(); row={'date':str(d),'platform':platform,'store_name':store,'product_name':product,'units_sold':units,'order_count':orders,'total_revenue':rev,'ad_spend':ad,'notes':notes}
                pd.concat([df,pd.DataFrame([row])],ignore_index=True).to_csv(MANUAL,index=False,encoding='utf-8-sig'); st.success('Eklendi'); st.rerun()

def all_files(): return [p for p in sorted(BASE.glob('*')) if p.suffix.lower() in ['.csv','.xlsx','.xls'] and p.name!='manual_entries.csv']
def files_for(platform):
    res=[]
    for p in all_files():
        n=norm(p.name)
        if platform=='Shopify' and any(x in n for x in ['shopify','orders export','fatura ozeti']): res.append(p)
        if platform=='Trendyol' and any(x in n for x in ['trendyol','urun reklamlari','magaza raporu','22 05']): res.append(p)
        if platform=='Hepsiburada' and 'hepsiburada' in n: res.append(p)
        if platform=='Kreatif' and any(x in n for x in ['adsiz','kreatif','creative']): res.append(p)
    return res

def cost_table(platform):
    frames=[]
    for p in files_for(platform):
        if 'maliyet' not in norm(p.name) and 'cost' not in norm(p.name): continue
        df,_,_=read_any(p)
        if df.empty: continue
        cs=fcol(df,['SKU','Barkod','Barcode','Stok Kodu']); cc=fcol(df,['Maliyet','Cost']); cm=fcol(df,['Komisyon','Commission']); ck=fcol(df,['Kargo','Shipping'])
        if not cs: continue
        x=pd.DataFrame({'sku_key':df[cs].apply(clean_sku),'unit_cost':df[cc].apply(num) if cc else 0.0,'commission_rate':df[cm].apply(num) if cm else 0.0,'unit_shipping':df[ck].apply(num) if ck else 0.0})
        x['commission_rate']=x['commission_rate'].apply(lambda v:v/100 if v>1 else v); frames.append(x)
    if not frames: return pd.DataFrame(columns=['sku_key','unit_cost','commission_rate','unit_shipping'])
    r=pd.concat(frames,ignore_index=True); return r[r['sku_key']!=''].drop_duplicates('sku_key',keep='last')

def add_cost(lines,costs):
    if lines.empty:
        lines['gross_profit']=[]; lines['matched_cost']=[]; return lines
    lines=lines.merge(costs,on='sku_key',how='left')
    for c in ['unit_cost','unit_shipping','commission_rate']: lines[c]=lines[c].fillna(0.0)
    lines['matched_cost']=lines['unit_cost'].gt(0)
    lines['gross_profit']=lines['line_revenue']-((lines['unit_cost']+lines['unit_shipping'])*lines['qty'])-(lines['line_revenue']*lines['commission_rate'])
    return lines

@st.cache_data(show_spinner=False)
def load_shopify():
    order_frames=[]; spend=[]; debug=[]
    for p in files_for('Shopify'):
        n=norm(p.name)
        if 'maliyet' in n: continue
        if 'fatura' in n or 'billing' in n:
            df=read_meta_bill(p); amount=fcol(df,['Tutar','Amount','Total','Spend','Harcama']); date=fcol(df,['Tarih','Date'])
            if amount:
                tmp=pd.DataFrame({'date':pd.to_datetime(df[date],errors='coerce',dayfirst=True) if date else pd.NaT,'ad_spend':df[amount].apply(num),'source_file':p.name})
                spend.append(tmp[tmp['ad_spend']>0]); debug.append({'file':p.name,'type':'meta_spend','status':'OK','rows':len(tmp)})
            continue
        df,enc,sep=read_shopify(p)
        if not df.empty: df['source_file']=p.name; order_frames.append(df); debug.append({'file':p.name,'type':'orders','status':'OK','rows':len(df)})
    raw=pd.concat(order_frames,ignore_index=True) if order_frames else pd.DataFrame(); costs=cost_table('Shopify'); ads=pd.concat(spend,ignore_index=True) if spend else pd.DataFrame(columns=['ad_spend','source_file'])
    if raw.empty: return pd.DataFrame(),pd.DataFrame(),costs,ads,pd.DataFrame(debug)
    for c in ['Total','Refunded Amount','Lineitem quantity','Lineitem price','Lineitem discount']:
        if c not in raw.columns: raw[c]=0
        raw[c]=raw[c].apply(num)
    for c in ['Cancelled at','Financial Status','Lineitem sku','Lineitem name','Created at']:
        if c not in raw.columns: raw[c]=''
    raw['order_name']=raw['Name'].astype(str); raw['order_date']=pd.to_datetime(raw['Created at'],errors='coerce',utc=True).dt.tz_localize(None); raw['cancelled_at']=pd.to_datetime(raw['Cancelled at'],errors='coerce',utc=True).dt.tz_localize(None); raw['financial_status']=raw['Financial Status'].astype(str).str.lower()
    raw=raw.drop_duplicates(subset=[x for x in ['Name','Created at','Lineitem sku','Lineitem name','Lineitem quantity','Lineitem price','Total'] if x in raw.columns],keep='first')
    orders=raw.groupby('order_name',as_index=False).agg(order_date=('order_date','first'),total=('Total','first'),refunded=('Refunded Amount','first'),cancelled_at=('cancelled_at','first'),financial_status=('financial_status','first'),source_file=('source_file','first'))
    orders['is_cancelled']=orders['cancelled_at'].notna()|orders['financial_status'].isin(['voided','cancelled','canceled']); orders['net_sales']=orders['total']-orders['refunded']; orders.loc[orders['is_cancelled'],'net_sales']=0.0; orders['order_count']=(~orders['is_cancelled']).astype(int)
    lines=raw.copy(); lines['sku_key']=lines['Lineitem sku'].apply(clean_sku); lines['product_name']=lines['Lineitem name'].astype(str); lines['qty']=lines['Lineitem quantity'].apply(num); lines['line_revenue']=lines['Lineitem price'].apply(num)*lines['qty']-lines['Lineitem discount'].apply(num)
    lines.loc[lines['order_name'].isin(orders.loc[orders['is_cancelled'],'order_name']),['qty','line_revenue']]=0.0
    lines=lines[['order_name','order_date','sku_key','product_name','qty','line_revenue','source_file']]
    return orders,lines,costs,ads,pd.DataFrame(debug)

def load_market(platform):
    rows=[]; ads=[]; debug=[]; costs=cost_table(platform)
    for p in files_for(platform):
        n=norm(p.name)
        if 'maliyet' in n: continue
        df,enc,sep=read_any(p)
        if df.empty: continue
        if any(x in n for x in ['reklam','ads','campaign']):
            sp=fcol(df,['Harcanan Tutar','Amount spent','Spend','Harcama','Tutar']); rv=fcol(df,['Reklam Geliri','Total Ad Revenue','Revenue','Dönüşüm değeri','Satis Tutari','Satış Tutarı']); pc=fcol(df,['Alışverişler','Purchases','Sipariş','Orders'])
            if sp:
                ads.append(pd.DataFrame({'ad_spend':df[sp].apply(num),'ad_revenue':df[rv].apply(num) if rv else 0.0,'ad_purchases':df[pc].apply(num) if pc else 0.0,'source_file':p.name})); debug.append({'file':p.name,'type':'ad','status':'OK'}); continue
        date=fcol(df,['Sipariş Tarihi','Tarih','Order Date','Date']); order=fcol(df,['Sipariş Numarası','Sipariş No','Order Number','Order','Paket No']); product=fcol(df,['Ürün Adı','Ürün Ad','Product Name','Product']); csku=fcol(df,['Barkod','SKU','Stok Kodu','Merchant SKU']); qty=fcol(df,['Adet','Miktar','Quantity','Ürün Adedi','Satış Miktarı']); rev=fcol(df,['Faturalanacak Tutar','Net Satış Tutarı','Satış Tutarı','Ürün Tutarı','Sipariş Tutarı','Toplam Satış Tutarı','Mağazanın Brüt Cirosu','Ciro','Tutar','Amount','Revenue']); status=fcol(df,['Sipariş Statüsü','Durum','Status'])
        if not rev: debug.append({'file':p.name,'type':'skipped','status':'NO_REVENUE'}); continue
        tmp=pd.DataFrame({'order_name':df[order].astype(str) if order else p.stem,'order_date':pd.to_datetime(df[date],errors='coerce',dayfirst=True) if date else pd.NaT,'product_name':df[product].astype(str) if product else platform+' Product','sku_key':df[csku].apply(clean_sku) if csku else '','qty':df[qty].apply(num) if qty else 1.0,'line_revenue':df[rev].apply(num),'status':df[status].astype(str) if status else '','source_file':p.name})
        tmp['bad']=tmp['status'].str.contains('iptal|iade|cancel|return|red',case=False,na=False); tmp.loc[tmp['bad'],['qty','line_revenue']]=0.0; rows.append(tmp[tmp['line_revenue'].fillna(0)>=0]); debug.append({'file':p.name,'type':'sales','status':'OK','used':rev})
    lines=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(columns=['order_name','order_date','product_name','sku_key','qty','line_revenue','source_file'])
    ad=pd.concat(ads,ignore_index=True) if ads else pd.DataFrame(columns=['ad_spend','ad_revenue','ad_purchases','source_file'])
    orders=lines.groupby('order_name',as_index=False).agg(order_date=('order_date','first'),net_sales=('line_revenue','sum'),qty=('qty','sum'),source_file=('source_file','first')) if not lines.empty else pd.DataFrame(columns=['order_name','order_date','net_sales','qty','source_file'])
    if not orders.empty: orders['order_count']=orders['net_sales'].gt(0).astype(int)
    return orders,lines,costs,ad,pd.DataFrame(debug)

def platform_data(platform):
    if platform=='Shopify': orders,lines,costs,ads,debug=load_shopify()
    else: orders,lines,costs,ads,debug=load_market(platform)
    lines=add_cost(lines,costs); m=load_manual(platform)
    rev=m['total_revenue'].sum() if not m.empty else 0; ords=m['order_count'].sum() if not m.empty else 0; units=m['units_sold'].sum() if not m.empty else 0; mad=m['ad_spend'].sum() if not m.empty else 0
    total=(orders['net_sales'].sum() if not orders.empty else 0)+rev; count=(orders['order_count'].sum() if not orders.empty and 'order_count' in orders else 0)+ords; sold=(lines['qty'].sum() if not lines.empty else 0)+units; gross=(lines['gross_profit'].sum() if not lines.empty else 0)+rev; spend=(ads['ad_spend'].sum() if not ads.empty and 'ad_spend' in ads else 0)+mad; adrev=0 if platform=='Shopify' else (ads['ad_revenue'].sum() if not ads.empty and 'ad_revenue' in ads else 0)
    metrics={'total_revenue':total,'order_count':count,'units_sold':sold,'aov':div(total,count),'gross_profit_before_ads':gross,'total_ad_spend':spend,'total_ad_revenue':adrev,'roas':div(adrev,spend),'net_profit_after_ads':gross-spend,'mer':div(total,spend),'cost_match_rate':float(lines['matched_cost'].mean()) if not lines.empty else 0}
    return metrics,orders,lines,ads,m,debug

def cards(metrics, show_ad=True):
    fs=[('Total Revenue','total_revenue','m'),('Order Count','order_count','i'),('Units Sold','units_sold','i'),('AOV','aov','m'),('Gross Profit Before Ads','gross_profit_before_ads','m'),('Total Ad Spend','total_ad_spend','m')]
    if show_ad: fs.append(('Total Ad Revenue','total_ad_revenue','m'))
    fs += [('ROAS','roas','r'),('Net Profit After Ads','net_profit_after_ads','m'),('MER','mer','r'),('Cost Match Rate','cost_match_rate','p')]
    for i in range(0,len(fs),4):
        cols=st.columns(4)
        for col,(label,key,t) in zip(cols,fs[i:i+4]):
            v=metrics.get(key,0); col.metric(label, money(v) if t=='m' else (f'{v:,.0f}' if t=='i' else (f'{v:.2f}' if t=='r' and v else ('N/A' if t=='r' else f'{v:.1%}'))))

def show_platform(platform):
    st.header(platform); manual_form(platform); metrics,orders,lines,ads,manual,debug=platform_data(platform); cards(metrics,show_ad=(platform!='Shopify'))
    if platform=='Shopify': st.info('Shopify Ad Revenue kullanılmaz. Sadece Shopify Ad Spend alınır.')
    t1,t2,t3,t4,t5=st.tabs(['Satış','Ürün & Kâr','Reklam','Manuel','Debug'])
    with t1:
        if not orders.empty:
            st.dataframe(orders.groupby('source_file',as_index=False).agg(order_count=('order_count','sum'),total_revenue=('net_sales','sum')),use_container_width=True,hide_index=True); st.dataframe(orders,use_container_width=True,hide_index=True)
        else: st.warning('Satış verisi okunamadı.')
    with t2:
        if not lines.empty: st.dataframe(lines.groupby(['product_name','sku_key'],as_index=False).agg(units_sold=('qty','sum'),revenue=('line_revenue','sum'),gross_profit=('gross_profit','sum'),matched_cost=('matched_cost','max')).sort_values('revenue',ascending=False),use_container_width=True,hide_index=True)
    with t3: st.dataframe(ads,use_container_width=True,hide_index=True)
    with t4: st.dataframe(manual,use_container_width=True,hide_index=True)
    with t5: st.dataframe(debug,use_container_width=True,hide_index=True); st.dataframe(pd.DataFrame([metrics]),use_container_width=True,hide_index=True)

def show_ai():
    st.header('Yapay Zeka'); s,*_=platform_data('Shopify'); t,*_=platform_data('Trendyol'); h,*_=platform_data('Hepsiburada')
    total=s['total_revenue']+t['total_revenue']+h['total_revenue']; spend=s['total_ad_spend']+t['total_ad_spend']+h['total_ad_spend']; adrev=t['total_ad_revenue']+h['total_ad_revenue']; gross=s['gross_profit_before_ads']+t['gross_profit_before_ads']+h['gross_profit_before_ads']; cnt=s['order_count']+t['order_count']+h['order_count']; units=s['units_sold']+t['units_sold']+h['units_sold']
    metrics={'total_revenue':total,'order_count':cnt,'units_sold':units,'aov':div(total,cnt),'gross_profit_before_ads':gross,'total_ad_spend':spend,'total_ad_revenue':adrev,'roas':div(adrev,spend),'net_profit_after_ads':gross-spend,'mer':div(total,spend),'cost_match_rate':0}
    cards(metrics); st.dataframe(pd.DataFrame([{'platform':'Shopify',**s,'rule':'Shopify Ad Revenue kullanılmaz'},{'platform':'Trendyol',**t},{'platform':'Hepsiburada',**h}]),use_container_width=True,hide_index=True)
    if st.button('Yorumu üret'): st.markdown(f"**Toplam ciro:** {money(total)}  \n**Reklam harcaması:** {money(spend)}  \n**Net kâr:** {money(gross-spend)}  \n**MER:** {div(total,spend):.2f}  \n**ROAS:** {div(adrev,spend):.2f}\n\nShopify {money(s['total_revenue'])}, Trendyol {money(t['total_revenue'])}, Hepsiburada {money(h['total_revenue'])}. Shopify Ad Revenue toplama katılmadı.")

st.title('IQIBLA Türkiye — E-Ticaret Paneli')
st.caption('Ana Sayfa + Şifre + Trendyol + Shopify + Hepsiburada + Kreatif + Yapay Zeka')
page=st.sidebar.radio('Sayfa',['Ana Sayfa','Trendyol','Shopify','Hepsiburada','Kreatif','Yapay Zeka'])
if page=='Ana Sayfa': st.subheader('Ana Sayfa'); st.write('Soldaki menüden panel seçebilirsin.'); st.dataframe(pd.DataFrame({'dosya':[p.name for p in all_files()]}),use_container_width=True,hide_index=True)
elif page=='Trendyol': show_platform('Trendyol')
elif page=='Shopify': show_platform('Shopify')
elif page=='Hepsiburada': show_platform('Hepsiburada')
elif page=='Kreatif': st.header('Kreatif'); st.info('Kreatif dosyaları ana dizinden okunur. Net ciroya dahil edilmez.'); st.dataframe(pd.DataFrame({'kreatif_dosyaları':[p.name for p in files_for('Kreatif')]}),use_container_width=True,hide_index=True)
elif page=='Yapay Zeka': show_ai()
