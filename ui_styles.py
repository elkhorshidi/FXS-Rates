"""Read-only presentation helpers: no data transformations or third-party assets."""
from __future__ import annotations
from html import escape


def safe(value) -> str:
    return escape(str(value), quote=True)


CSS = r"""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
:root {--hx-ink:#142c40;--hx-navy:#102b3f;--hx-teal:#0c928b;--hx-bg:#f4f7fa;--hx-mute:#76899a;--hx-border:#e3eaf0;--hx-white:#ffffff}
html,body,.stApp,[data-testid="stSidebar"],.stMarkdown,.stSelectbox,.stNumberInput,.stMultiSelect,
.stTextInput,.stExpander,.stButton button,.stDownloadButton button,input,button,select,textarea,
[data-testid="stDataFrame"],.stCaption,[data-testid="stWidgetLabel"] {
 font-family:'Vazirmatn','Tahoma',sans-serif!important;
}
.stApp {background:var(--hx-bg); color:var(--hx-ink)}
[data-testid="stAppViewContainer"] > .main{background:var(--hx-bg)}
.block-container {max-width:1250px; padding:1.4rem 2.3rem 3rem;}
[data-testid="stVerticalBlock"] {gap:.6rem}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:#fff; border-left:1px solid var(--hx-border); direction:rtl;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.5rem}
[data-testid="stSidebar"] .block-container {padding-top:1rem}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p {text-align:right; direction:rtl;}
[data-testid="stSidebar"] button {border-radius:12px; min-height:43px;}
.stMarkdown p, .stMarkdown li, label, [data-testid="stCaptionContainer"] {direction:rtl;text-align:right}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 {font-family:'Vazirmatn',sans-serif !important;text-align:right;direction:rtl}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {
 background:var(--hx-teal)!important;color:#fff!important;border:1px solid var(--hx-teal)!important;border-radius:12px!important;font-weight:700!important;
}
.stButton>button[kind="secondary"] {border-radius:12px!important; background:#fff!important; border-color:var(--hx-border)!important;}
[data-testid="stNumberInput"] input {font-variant-numeric:tabular-nums; direction:ltr; text-align:center;}
[data-testid="stSelectbox"] [data-baseweb="select"], [data-testid="stMultiSelect"] [data-baseweb="select"] {direction:rtl}
[data-testid="stDataFrame"]{direction:ltr}
[data-testid="stAlert"] {border-radius:12px;}
hr {border-color:var(--hx-border);margin:1rem 0!important;}
/* Custom read-only blocks: preserve Streamlit input functionality */
.hx-root {direction:rtl; text-align:right; font-family:'Vazirmatn','Tahoma',sans-serif;}
.hx-hero {background:var(--hx-navy);border-radius:19px;padding:27px 32px 24px;
 display:flex;justify-content:space-between;align-items:center;gap:24px;color:white;direction:rtl;position:relative;overflow:hidden;margin-bottom:13px;}
.hx-hero:after {content:'';width:170px;height:170px;position:absolute;left:-55px;bottom:-120px;background:#15566a;border-radius:50%;opacity:.35;}
.hx-brand {font-family:system-ui,sans-serif;font-weight:800;letter-spacing:2px;font-size:29px;direction:ltr;text-align:left;line-height:1.1;}
.hx-brand-sub {font:500 10px system-ui,sans-serif;letter-spacing:1.2px;color:#a5ccca;text-align:left;margin-top:6px;direction:ltr}
.hx-overline {font-size:11px; font-weight:600;letter-spacing:.1px;color:#7bcac4;margin-bottom:6px;}
.hx-hero h1 {color:#fff!important;margin:0!important;font-size:clamp(22px,2.3vw,31px)!important;font-weight:800!important;line-height:1.7!important;}
.hx-hero p {margin:2px 0 0!important;font-size:12px;color:#bed0da}
.hx-strip {display:flex;justify-content:space-between;align-items:center;gap:10px;direction:rtl;
 border:1px solid #cfe9e3;background:#eff9f6;color:#1d746b;padding:10px 15px;border-radius:12px;font-size:12px;margin:0 0 15px;}
.hx-dot {width:7px;height:7px;border-radius:99px;background:#13a18f;display:inline-block;margin-left:7px;box-shadow:0 0 0 3px #d1eee5}
.hx-strip small {font-size:11px;color:#427b78}
.hx-kpi-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;direction:rtl;margin:2px 0 24px;}
.hx-kpi {min-height:138px;background:white;border:1px solid var(--hx-border);border-radius:16px;padding:20px 20px 16px;box-shadow:0 3px 16px rgba(13,35,54,.035);}
.hx-kpi--accent {border-color:#a9ded8;background:linear-gradient(135deg,#f1fbf8,#fff 70%);}
.hx-kpi--primary {border-top:3px solid var(--hx-teal);padding-top:18px;}
.hx-kpi-label {color:#788a9a;font-size:12px;font-weight:600;margin-bottom:12px;white-space:nowrap}
.hx-kpi-value {font-size:clamp(18px,2.15vw,29px);color:var(--hx-ink);font-weight:800;line-height:1.6;white-space:nowrap}
.hx-kpi-unit {color:#728796;font-size:11px;margin-top:7px;}
.hx-ltr {direction:ltr;display:inline-block;unicode-bidi:isolate;font-family:'Vazirmatn',sans-serif;font-variant-numeric:tabular-nums}
.hx-section-title {display:flex;justify-content:space-between;align-items:center;gap:12px;margin:0 0 13px;direction:rtl;}
.hx-section-title h2 {font-size:19px!important;font-weight:800;margin:0!important;color:var(--hx-ink)!important}
.hx-section-title small {color:var(--hx-mute);font-size:11px;line-height:1.7;}
.hx-tag {font-size:10px;background:#e4f5f0;padding:5px 10px;border-radius:100px;color:#168078;font-weight:700;}
.hx-table-wrap {border:1px solid var(--hx-border);border-radius:16px;background:#fff;overflow-x:auto;margin-bottom:12px;box-shadow:0 3px 12px rgba(13,35,54,.02)}
.hx-table {width:100%;min-width:930px;border-collapse:collapse;direction:rtl;text-align:right;table-layout:auto;}
.hx-table th {background:#eff3f7;padding:14px 12px;color:#6c8191;font-size:11px;font-weight:700;text-align:right;white-space:nowrap;}
.hx-table td {padding:14px 12px;border-top:1px solid #edf1f4;white-space:nowrap;font-size:12px;color:#33475a;}
.hx-table tbody tr:nth-child(even) {background:#fbfcfd}
.hx-table tr.hx-row-best {background:#eef9f5!important}
.hx-table .hx-name {font-weight:800;color:#183449;}
.hx-table .hx-num {font-weight:650;font-size:12px;}
.hx-table .hx-strong {font-weight:800;color:#153147;}
.hx-table .hx-percent {color:#008d84;font-weight:800}
.hx-table .hx-percent-neg {color:#b65b46;font-weight:800}
.hx-badge {font-size:10px;font-weight:700;color:#087c74;background:#d7f1eb;border:1px solid #b7e6dc;border-radius:99px;padding:2px 7px;margin-right:5px;}
.hx-muted {font-size:11px;color:#8093a3;}
.hx-note {font-size:11px;color:var(--hx-mute);direction:rtl;text-align:right;margin:6px 0 13px}
.hx-reporthead {border-top:1px solid var(--hx-border);padding-top:18px;margin-top:10px;}
.hx-report-panel {border-radius:16px;background:white;border:1px solid var(--hx-border);padding:14px;}
.hx-sidebar-brand {font-size:24px;font-weight:900;color:#12314a;direction:ltr;text-align:left;font-family:system-ui,sans-serif;letter-spacing:2px}
.hx-sidebar-sub {font-size:10px;color:#8a9da9;margin-top:4px;direction:ltr;text-align:left;font-family:system-ui,sans-serif}
.hx-mini-title {font-weight:750;color:#274458;font-size:13px;margin:8px 0 2px;}
@media(max-width:1050px){.hx-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.block-container{padding:1.2rem 1rem 2rem}}
@media(max-width:620px){.hx-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
 .hx-kpi{min-height:118px;padding:14px 12px}.hx-kpi-label{font-size:10px}.hx-kpi-value{font-size:20px}
 .hx-hero{padding:21px 18px}.hx-brand{font-size:20px}.hx-brand-sub{font-size:7px}
 .hx-hero h1{font-size:21px!important}.hx-strip{flex-direction:column;align-items:flex-start}}
</style>
"""


def hero() -> str:
    return """<div class='hx-root'><div class='hx-hero'>
      <div><div class='hx-overline'>HELIOS / FX INTELLIGENCE</div>
        <h1>مقایسه نرخ رفع تعهد ارزی</h1>
        <p>بانک‌ها، کوتاژ و بازار آزاد — مقایسه بر اساس آخرین نرخ ثبت‌شده</p></div>
      <div><div class='hx-brand'>HELIOS</div><div class='hx-brand-sub'>ASHA SPEED · FX DESK</div></div>
    </div></div>"""


def status(source: str, stamp: str, mode: str) -> str:
    return f"""<div class='hx-root'><div class='hx-strip'>
      <span><i class='hx-dot'></i> اتصال شیت برقرار است <span style='color:#86a49d'>|</span> نرخ مبنا: <b>{safe(source)}</b></span>
      <small>آخرین استعلام بازار آزاد: <span class='hx-ltr'>{safe(stamp)}</span> · {safe(mode)}</small>
    </div></div>"""


def kpis(market: str, best_label: str, best_rate: str, gap: str, volume: str) -> str:
    def card(label, value, foot, cls=""):
        return f"<div class='hx-kpi {cls}'><div class='hx-kpi-label'>{label}</div><div class='hx-kpi-value'>{value}</div><div class='hx-kpi-unit'>{foot}</div></div>"
    def num(t):return f"<span class='hx-ltr'>{safe(t)}</span>"
    cells = [
        card("نرخ بازار آزاد",num(market),"تومان / دلار", "hx-kpi--primary"),
        card("بالاترین نرخ مؤثر",safe(best_label),"در مسیرهای ثبت‌شده", "hx-kpi--accent"),
        card("نرخ مؤثر مسیر برتر",num(best_rate),"تومان / دلار"),
        card("فاصله تا بازار آزاد",num(gap),f"مبنای محاسبه: {safe(volume)} دلار"),
    ]
    return "<div class='hx-root'><div class='hx-kpi-grid'>" + "".join(cells) + "</div></div>"


def table_html(rows: list[dict]) -> str:
    heads=["مسیر","نرخ خام","کارمزد اظهار","نرخ مؤثر","فاصله (تومان)","فاصله (%)","معادل دلاری","زمان استعلام"]
    th="".join(f"<th>{h}</th>" for h in heads)
    body=[]
    for i,r in enumerate(rows):
        path=f"<span class='hx-name'>{safe(r['name'])}</span>"+ ("<span class='hx-badge'>نرخ برتر</span>" if i==0 else "")
        values=[path,*[f"<span class='hx-ltr hx-num {'hx-strong' if k=='effective' else ('hx-percent' if k=='pct' and r['positive'] else ('hx-percent-neg' if k=='pct' else ''))}'>{safe(r[k])}</span>" for k in ("raw","fee","effective","gap","pct","usd","time")]]
        body.append(f"<tr class='{'hx-row-best' if i==0 else ''}'>"+"".join(f"<td>{v}</td>" for v in values)+"</tr>")
    return f"""<div class='hx-root'><div class='hx-table-wrap'><table class='hx-table'>
      <thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></div>"""


def section_title(title: str, note: str = "",pill: str="") -> str:
    side=f"<span class='hx-tag'>{safe(pill)}</span>" if pill else f"<small>{safe(note)}</small>"
    return f"<div class='hx-root'><div class='hx-section-title'><h2>{safe(title)}</h2>{side}</div></div>"
