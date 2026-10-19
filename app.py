"""Helios FX — minimal read-only Streamlit dashboard driven by Google Sheets Rates_Log."""
from __future__ import annotations

import csv
import hmac
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from fx_core import HEADERS, parse_rates, latest_rates, compare, fmt_toman, fmt_percent
from sheet_reader import SPREADSHEET_ID, RATES_GID, download_public_sheet
from report_image import make_png, formatted_time
from ui_styles import CSS, hero, status, kpis, table_html, section_title

st.set_page_config(page_title="Helios | FX Obligation",page_icon="💱",layout="wide",initial_sidebar_state="expanded")
st.markdown(CSS,unsafe_allow_html=True)


def simple_secret(key: str, fallback: str = "") -> str:
    try:
        return str(st.secrets.get(key,fallback))
    except (FileNotFoundError,KeyError,RuntimeError):
        return fallback


@st.cache_data(ttl=90,show_spinner=False)
def load_live_rows(sheet_id: str,gid: int,public_csv_url: str):
    return download_public_sheet(sheet_id,gid,public_csv_url)


def upload_to_rows(upload) -> list[list[object]]:
    raw=upload.getvalue().decode("utf-8-sig")
    if not raw.strip():return [HEADERS]
    try:dialect=csv.Sniffer().sniff(raw[:2048],delimiters=",;\t")
    except csv.Error:dialect=csv.excel
    return list(csv.reader(io.StringIO(raw),dialect))


with st.sidebar:
    st.markdown("<div class='hx-sidebar-brand'>HELIOS</div><div class='hx-sidebar-sub'>FX OBLIGATION  /  CONTROL PANEL</div>",unsafe_allow_html=True)
    st.markdown("### تنظیمات مقایسه")
    sheet_id=simple_secret("spreadsheet_id",SPREADSHEET_ID)
    try:gid=int(simple_secret("rates_gid",str(RATES_GID)))
    except ValueError:
        st.error("شناسه تب Rates_Log معتبر نیست.")
        st.stop()
    secret_password=simple_secret("dashboard_password")
    if secret_password:
        entered=st.text_input("رمز ورود",type="password")
        if not hmac.compare_digest(entered,secret_password):
            st.info("برای مشاهده نرخ‌ها، رمز ورود را وارد کن.")
            st.stop()

    volume=st.number_input("حجم مبنا (USD)",min_value=1,max_value=10_000_000_000,value=100_000,step=10_000,format="%d")
    with st.expander("اتصال به شیت و CSV جایگزین",expanded=False):
        st.caption("دریافت نرخ‌ها از تب Rates_Log با دسترسی مشاهده از طریق لینک یا CSV منتشرشده")
        manual_url=st.text_input("لینک CSV منتشرشده (اختیاری)",value="",placeholder="https://docs.google.com/spreadsheets/...")
        csv_file=st.file_uploader("آپلود CSV برای تست آفلاین",type=["csv"])
    published_csv_url=manual_url.strip() or simple_secret("published_csv_url")
    refresh=st.button("↻  دریافت آخرین نرخ‌ها",use_container_width=True,type="primary")
    if refresh:load_live_rows.clear()
    st.markdown(f"[باز کردن Google Sheets](https://docs.google.com/spreadsheets/d/{sheet_id}/edit)")
    st.caption("منبع اطلاعات Google Sheets است؛ داشبورد نرخ‌ها را تغییر نمی‌دهد.")

st_autorefresh(interval=120_000,key="helios_fx_refresh")
st.markdown(hero(),unsafe_allow_html=True)

if csv_file is not None:
    try:
        values=upload_to_rows(csv_file)
        source_mode="حالت آفلاین / CSV"
    except (UnicodeDecodeError,ValueError) as exc:
        st.error(f"CSV قابل خواندن نیست: {exc}")
        st.stop()
else:
    try:
        with st.spinner("در حال دریافت نرخ‌ها از Google Sheets…"):
            values,_used_url=load_live_rows(sheet_id,gid,published_csv_url)
        source_mode="اتصال آنلاین · به‌روزرسانی ۲ دقیقه‌ای"
    except Exception as exc:
        st.warning("اتصال به نرخ‌های Google Sheets برقرار نیست.")
        st.markdown("برای استفاده بدون Google Cloud، دسترسی Viewer با لینک را برای Google Sheets فعال کن؛ یا فقط تب Rates_Log را از مسیر File → Share → Publish to web به CSV منتشر و لینکش را در تنظیمات وارد کن. توجه کن که داده‌های منتشرشده برای دارندگان لینک قابل خواندن هستند.")
        with st.expander("جزئیات خطا"):
            st.code(f"{type(exc).__name__}: {exc}")
        st.stop()

rates,warnings=parse_rates(values)
if rates.empty:
    st.info("هنوز نرخ معتبری در Rates_Log ثبت نشده است.")
    st.stop()
latest=latest_rates(rates)
free=latest[latest["kind"]=="بازار آزاد"]
if free.empty:
    st.warning("برای مقایسه، ابتدا یک نرخ بازار آزاد وارد کن.")
    st.stop()

sources=free["source"].tolist()
with st.sidebar:
    source_name=st.selectbox("منبع مبنای بازار آزاد",sources,index=len(sources)-1)

comp,market=compare(latest,source_name,float(volume))
market_row=free[free["source"]==source_name].iloc[0]
st.markdown(status(source_name,formatted_time(market_row["timestamp"],"en"),source_mode),unsafe_allow_html=True)

if warnings:
    with st.expander(f"{len(warnings)} مورد نیازمند بررسی در داده‌ها"):
        for msg in warnings[:25]:st.write("• "+msg)

if comp.empty:
    st.markdown(kpis(fmt_toman(market),"—","—","—",fmt_toman(volume)),unsafe_allow_html=True)
    st.info("هنوز ریت بانکی یا کوتاژ برای مقایسه ثبت نشده است.")
    st.stop()

best=comp.iloc[0]
st.markdown(kpis(fmt_toman(market),str(best["label"]),fmt_toman(best["effective_rate"]),fmt_percent(best["gap_pct"]),fmt_toman(volume)),unsafe_allow_html=True)
st.markdown(section_title("مقایسه آخرین نرخ‌ها",pill=f"{len(comp)} مسیر فعال"),unsafe_allow_html=True)

rows=[]
for _,r in comp.iterrows():
    gap=float(r["gap_pct"])
    rows.append({
      "name":r["label"],"raw":fmt_toman(r["raw_rate"]),
      "fee":f"{r['fee_pct']:.2f}%" if r["kind"]=="بانک" else "—",
      "effective":fmt_toman(r["effective_rate"]),"gap":fmt_toman(r["gap_toman"]),
      "pct":fmt_percent(gap),"positive":gap>=0,
      "usd":fmt_toman(r["gap_usd"]),"time":formatted_time(r["timestamp"],"en"),
    })
st.markdown(table_html(rows),unsafe_allow_html=True)
st.markdown("<div class='hx-note'>اختلاف = نرخ بازار آزاد − نرخ مؤثر. معادل دلاری برای حجم مبنای انتخاب‌شده محاسبه می‌شود. اختلاف مثبت به معنی نرخ مؤثر پایین‌تر از آزاد است.</div>",unsafe_allow_html=True)

with st.expander("مشاهده جدول قابل کپی و دانلود داده مقایسه",expanded=False):
    extended=comp[["label","timestamp","raw_rate","fee_pct","effective_rate","gap_toman","gap_pct","gap_usd"]].copy()
    extended.columns=["مسیر","زمان استعلام","نرخ خام","کارمزد (%)","نرخ مؤثر","اختلاف تومان/دلار","اختلاف (%)","معادل دلاری"]
    st.dataframe(extended,use_container_width=True,hide_index=True)
    st.download_button("دانلود CSV مقایسه",data=extended.to_csv(index=False).encode("utf-8-sig"),file_name="helios_comparison.csv",mime="text/csv")

st.markdown("<div class='hx-reporthead'></div>",unsafe_allow_html=True)
st.markdown(section_title("گزارش تک‌صفحه‌ای مشتری",note="گزارش برای واتس‌اپ · PNG عمودی ۴:۵"),unsafe_allow_html=True)

controls,preview=st.columns([.95,1.05],gap="large")
with controls:
    st.markdown("<div class='hx-mini-title'>انتخاب مسیرهای گزارش</div>",unsafe_allow_html=True)
    all_routes=comp["label"].tolist()
    selection=st.multiselect("مسیرها (حداکثر ۷ مورد)",all_routes,default=all_routes[:7],label_visibility="collapsed")
    st.caption("گزارش، آخرین نرخ ثبت‌شده هر مسیر و زمان استعلام آن را نشان می‌دهد.")

if len(selection)>7:
    with controls:st.warning("برای خوانایی گزارش، حداکثر ۷ مسیر انتخاب کن.")
elif not selection:
    with controls:st.info("حداقل یک مسیر را انتخاب کن.")
else:
    # Retain ranking order; preview and download must be based on the same bytes.
    report=comp[comp["label"].isin(selection)].copy()
    with st.spinner("آماده‌سازی گزارش تصویری…"):
        png=make_png(report,market,market_row["timestamp"],source_name,float(volume))
    with preview:
        st.image(png,caption="پیش‌نمایش نهایی گزارش مشتری · ۱۰۸۰ × ۱۳۵۰",use_container_width=True)
    with controls:
        now=datetime.now(ZoneInfo("Asia/Tehran"))
        st.download_button("دانلود گزارش PNG",data=png,file_name=now.strftime("HELIOS_FX_%Y-%m-%d_%H-%M.png"),mime="image/png",use_container_width=True,type="primary")
        with st.expander("متن قابل کپی برای واتس‌اپ"):
            lines=["گزارش مقایسه نرخ رفع تعهد ارزی",f"بازار آزاد: {fmt_toman(market)} تومان",f"حجم مبنا: {fmt_toman(volume)} دلار"]
            for _,r in report.iterrows():
                lines.append(f"{r['label']}: مؤثر {fmt_toman(r['effective_rate'])} | اختلاف {fmt_toman(r['gap_toman'])} تومان | {fmt_percent(r['gap_pct'])} | معادل {fmt_toman(r['gap_usd'])} دلار")
            st.code("\n".join(lines),language=None)

with st.expander("تاریخچه نرخ‌ها",expanded=False):
    names=sorted(rates["label"].unique())
    selected=st.multiselect("منابع",names,default=names,key="historical_sources")
    history=rates[rates["label"].isin(selected)].sort_values(["timestamp","sheet_row"])
    if history.empty:st.info("داده‌ای در فیلتر فعلی وجود ندارد.")
    else:
        plot=history[history["timestamp"].notna()].pivot_table(index="timestamp",columns="label",values="effective_rate",aggfunc="last")
        if not plot.empty:st.line_chart(plot)
        hist=history[["timestamp","label","raw_rate","fee_pct","effective_rate","reference"]].copy()
        hist.columns=["زمان","مسیر","نرخ خام","کارمزد (%)","نرخ مؤثر","مرجع"]
        st.dataframe(hist,use_container_width=True,hide_index=True)
        st.download_button("دانلود تاریخچه CSV",data=hist.to_csv(index=False).encode("utf-8-sig"),file_name="helios_rate_history.csv",mime="text/csv")

st.caption("HELIOS · ASHA SPEED KHORSHID  |  نرخ‌ها استعلامی‌اند و قطعی بودن معامله به شرایط تسویه و زمان اجرا بستگی دارد.")
