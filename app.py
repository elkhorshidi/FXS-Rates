from __future__ import annotations
import hmac
import io
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

from fx_core import HEADERS, parse_rates, latest_rates, compare, fmt_toman, fmt_percent, route_label
from report_image import make_png, formatted_time

SHEET_ID = "1xckakJWtevb91dqlpbW504SbLg2irhhxlIRHIuTF3Ow"
st.set_page_config(page_title="Helios | FX Obligation", page_icon="💱", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, .stButton button, input, select, textarea, [data-testid="stMetricValue"] {
  font-family:'Vazirmatn',Tahoma,sans-serif!important;
}
.stApp {direction:rtl; color:#203243; background:#f7f9fb}
.block-container{padding-top:2rem;max-width:1350px}
h1,h2,h3,p,.stCaption,small{direction:rtl;text-align:right}
[data-testid="stMetric"]{background:white;border:1px solid #e8eef3;padding:19px;border-radius:17px}
[data-testid="stMetricValue"]{direction:ltr;text-align:right;font-weight:700}
[data-testid="stSidebar"]{direction:rtl}
div[data-testid="stDataFrame"]{direction:ltr}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:#0f857e;border-color:#0f857e}
</style>
""",unsafe_allow_html=True)


def secrets_dict(key: str):
    try:
        item = st.secrets.get(key)
        return dict(item) if item else None
    except (FileNotFoundError, KeyError, RuntimeError):
        return None


def simple_secret(key: str, fallback: str = ""):
    try:
        return str(st.secrets.get(key, fallback))
    except (FileNotFoundError, KeyError, RuntimeError):
        return fallback


@st.cache_data(ttl=120,show_spinner=False)
def load_live_rows(spreadsheet_id: str) -> list[list[object]]:
    import gspread
    from gspread.utils import ValueRenderOption
    from google.oauth2.service_account import Credentials
    sc = secrets_dict("google_service_account")
    if not sc:
        raise RuntimeError("کلید حساب سرویس Google هنوز در Secrets ثبت نشده است.")
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(sc, scopes=scopes)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(spreadsheet_id).worksheet("Rates_Log")
    return worksheet.get("A1:H",value_render_option=ValueRenderOption.unformatted)


def upload_to_rows(uploaded_file) -> list[list[object]]:
    import csv
    raw = uploaded_file.getvalue().decode("utf-8-sig")
    if not raw.strip():
        return [HEADERS]
    dialect = csv.Sniffer().sniff(raw[:2048],delimiters=",;\t")
    return list(csv.reader(io.StringIO(raw),dialect))


st.title("Helios | مقایسه نرخ رفع تعهد ارزی")
st.caption("منبع داده: Google Sheets → Rates_Log | نرخ‌ها به تومان به ازای هر دلار")

with st.sidebar:
    st.subheader("تنظیمات داشبورد")
    st.caption("نرخ‌ها در Google Sheets ثبت می‌شوند؛ این داشبورد فقط آن‌ها را می‌خواند.")
    sheet_id = simple_secret("spreadsheet_id",SHEET_ID)
    service_account = secrets_dict("google_service_account")
    secret_password = simple_secret("dashboard_password")
    if service_account:
        if not secret_password:
            st.error("برای حفظ محرمانگی نرخ‌ها، dashboard_password را در Secrets تنظیم کن.")
            st.stop()
        entered = st.text_input("رمز ورود داشبورد",type="password",placeholder="رمز ورود")
        if not hmac.compare_digest(entered,secret_password):
            st.info("برای مشاهده نرخ‌های خصوصی، رمز ورود را وارد کن.")
            st.stop()
        use_live = True
    else:
        use_live = False
        st.info("برای اتصال خودکار، Secrets را تنظیم کن؛ تا آن موقع می‌توانی CSV شیت را بارگذاری کنی.")

    csv_file = st.file_uploader("CSV شیت (برای تست اختیاری)",type=["csv"])
    volume = st.number_input("حجم مبنای مقایسه (دلار)",min_value=1, max_value=10000000000, value=100000, step=10000, format="%d")
    if st.button("↻ به‌روزرسانی از شیت",use_container_width=True,disabled=not use_live):
        load_live_rows.clear()
        st.rerun()
    st.markdown(f"[باز کردن شیت اصلی](https://docs.google.com/spreadsheets/d/{sheet_id}/edit)")

if csv_file is not None:
    try:
        values = upload_to_rows(csv_file)
        source_mode="CSV آپلودشده؛ اتصال زنده نیست"
    except (ValueError,UnicodeDecodeError) as exc:
        st.error(f"خواندن CSV ناموفق بود: {exc}")
        st.stop()
elif use_live:
    try:
        values=load_live_rows(sheet_id)
        source_mode="Google Sheets خصوصی | آخرین همگام‌سازی حداکثر ۲ دقیقه پیش"
    except Exception as exc:
        st.error("دریافت داده از Google Sheets ناموفق بود. دسترسی Viewer حساب سرویس و Secrets را بررسی کن.")
        with st.expander("جزئیات فنی خطا"):
            st.code(type(exc).__name__+": "+str(exc))
        st.stop()
else:
    st.info("ابتدا فایل CSV شیت Rates_Log را بارگذاری کن یا دسترسی Google Sheets را از طریق Secrets فعال کن. هیچ نرخ ساختگی نمایش داده نمی‌شود.")
    st.stop()

rates, warnings=parse_rates(values)
if rates.empty:
    st.warning("هنوز نرخ معتبری ثبت نشده است. اولین داده را در Rates_Log وارد کن.")
    st.stop()

latest=latest_rates(rates)
free=latest[latest["kind"]=="بازار آزاد"]
if free.empty:
    st.warning("برای محاسبه اختلاف‌ها، حداقل یک نرخ بازار آزاد در ستون نوع مسیر لازم است.")
    st.stop()

sources=free["source"].tolist()
# If multiple free-market references exist, the most recently quoted one is the default.
source_name=st.selectbox("منبع مبنای بازار آزاد",sources,index=len(sources)-1)
comp,market=compare(latest,source_name,float(volume))
market_row=free[free["source"]==source_name].iloc[0]

st.caption(source_mode)
if warnings:
    with st.expander(f"⚠ {len(warnings)} مورد نیازمند بررسی در اطلاعات شیت"):
        for msg in warnings[:25]:st.write("• "+msg)

c1,c2,c3,c4=st.columns(4)
c1.metric("بازار آزاد",fmt_toman(market)+" تومان")
if comp.empty:
    best=None
    c2.metric("بهترین مسیر","—")
    c3.metric("ریت مؤثر", "—")
    c4.metric("اختلاف با آزاد", "—")
else:
    best=comp.iloc[0]
    c2.metric("بالاترین نرخ مؤثر",best["label"])
    c3.metric("نرخ مؤثر مسیر برتر",fmt_toman(best["effective_rate"])+" تومان")
    c4.metric("فاصله مسیر برتر با آزاد",fmt_percent(best["gap_pct"]))

st.subheader("جدول مقایسه امروز / آخرین نرخ‌ها")
if comp.empty:
    st.info("هیچ نرخ بانک یا کوتاژ ثبت نشده است.")
else:
    frame=comp.copy()
    frame["time_display"] = frame["timestamp"].map(formatted_time)
    frame["fee_display"] = frame.apply(lambda r: f"{r['fee_pct']:.2f}%" if r["kind"]=="بانک" else "—",axis=1)
    frame["effective_display"]=frame["effective_rate"].map(fmt_toman)
    frame["raw_display"]=frame["raw_rate"].map(fmt_toman)
    frame["gap_display"]=frame["gap_toman"].map(fmt_toman)
    frame["gap_pct_display"]=frame["gap_pct"].map(fmt_percent)
    frame["usd_display"]=frame["gap_usd"].map(fmt_toman)
    show = frame[["label","raw_display","fee_display","effective_display","gap_display","gap_pct_display","usd_display","time_display"]]
    show.columns=["مسیر","نرخ خام","کارمزد","نرخ مؤثر","اختلاف تومان/دلار","اختلاف ٪","معادل دلاری اختلاف","زمان استعلام"]
    st.dataframe(show,use_container_width=True,hide_index=True)
    st.caption("اختلاف = نرخ آزاد − نرخ مؤثر؛ ارقام منفی یعنی نرخ مسیر بالاتر از آزاد است. معادل دلاری بر اساس حجم مبنا محاسبه می‌شود.")

st.divider()
st.subheader("گزارش تک‌صفحه‌ای واتس‌اپ")
if not comp.empty:
    all_routes=comp["label"].tolist()
    routes_selected=st.multiselect("انتخاب مسیرهای گزارش (حداکثر ۷ مسیر)",all_routes,default=all_routes[:7])
    if len(routes_selected)>7:st.warning("برای خوانایی گزارش، حداکثر ۷ مسیر را انتخاب کن.")
    elif routes_selected:
        report=comp[comp["label"].isin(routes_selected)].copy()
        png=make_png(report,market,market_row["timestamp"],source_name,float(volume))
        st.image(png,caption="پیش‌نمایش خروجی PNG · نسبت ۴:۵",width=430)
        now=datetime.now(ZoneInfo("Asia/Tehran"))
        st.download_button("⬇ دانلود گزارش PNG",data=png,file_name=now.strftime("HELIOS_FX_%Y-%m-%d_%H-%M.png"),mime="image/png",use_container_width=True,type="primary")
        lines=["گزارش مقایسه نرخ رفع تعهد ارزی",f"بازار آزاد: {fmt_toman(market)} تومان",f"حجم مبنا: {volume:,.0f} دلار"]
        for _,r in report.iterrows():
            lines.append(f"{r['label']}: مؤثر {fmt_toman(r['effective_rate'])} | فاصله {fmt_toman(r['gap_toman'])} تومان | {fmt_percent(r['gap_pct'])} | معادل {fmt_toman(r['gap_usd'])} دلار")
        st.code("\n".join(lines),language=None)
    else:st.info("حداقل یک مسیر را انتخاب کن.")

with st.expander("تاریخچه استعلام‌ها",expanded=False):
    filter_names=sorted(rates["label"].unique())
    names=st.multiselect("فیلتر منبع / مسیر",filter_names,default=filter_names)
    historical = rates[rates["label"].isin(names)].sort_values(["timestamp","sheet_row"])
    if not historical.empty:
        plot = historical[historical["timestamp"].notna()].pivot_table(index="timestamp",columns="label",values="effective_rate",aggfunc="last")
        if not plot.empty:
            st.line_chart(plot)
        hist=historical[["timestamp","label","raw_rate","fee_pct","effective_rate","reference"]].copy()
        hist.columns=["زمان","مسیر","نرخ خام","کارمزد (%)","نرخ مؤثر","مرجع"]
        st.dataframe(hist,use_container_width=True,hide_index=True)
        st.download_button("دریافت تاریخچه فیلترشده CSV",hist.to_csv(index=False).encode("utf-8-sig"),"helios_rate_history.csv",mime="text/csv")
    else:st.info("داده‌ای برای این فیلتر وجود ندارد.")

st.caption("Helios | ASHA SPEED — محاسبات اطلاعاتی و مشروط به زمان واقعی استعلام و شرایط معامله هستند.")
