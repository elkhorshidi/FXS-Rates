"""HELIOS WhatsApp report — Persian shaping / RTL & 1080×1350. Fonts are fetched at runtime, never packaged."""
from __future__ import annotations
import io
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import lru_cache
import urllib.request
from PIL import Image, ImageDraw, ImageFont, features
from fx_core import fmt_toman, fmt_percent

W,H=1080,1350
NAVY="#102B3F";TEXT="#173348";MUTED="#71879A";TEAL="#008D83";BG="#F3F7F9";LINE="#E3EBF0"

@lru_cache(maxsize=4)
def get_font_path(weight="Regular"):
    """Download open-source Vazirmatn if possible; fall back to an installed Persian font."""
    folder=Path.home()/".cache"/"helios_fx";folder.mkdir(parents=True,exist_ok=True)
    p=folder/f"Vazirmatn-{weight}.ttf"
    if p.is_file() and p.stat().st_size>30000:return str(p)
    sources=[
        f"https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/fonts/ttf/Vazirmatn-{weight}.ttf",
        f"https://raw.githubusercontent.com/rastikerdar/vazirmatn/v33.003/fonts/ttf/Vazirmatn-{weight}.ttf",
    ]
    for url in sources:
        try:
            with urllib.request.urlopen(url,timeout=5) as resp:data=resp.read(1_500_000)
            if 30000<len(data)<1_500_000 and data[:4] in (b"\x00\x01\x00\x00",b"OTTO",b"true"):
                p.write_bytes(data);return str(p)
        except (OSError,ValueError,TimeoutError):pass
    for fp in (
        f"/usr/share/fonts/truetype/noto/NotoSansArabic-{'Bold' if weight=='Bold' else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if weight=='Bold' else ''}.ttf",
    ):
        if Path(fp).is_file():return fp
    return None

@lru_cache(maxsize=2)
def font_set(weight):
    path=get_font_path(weight)
    def load(size):
        if not path:return ImageFont.load_default()
        return ImageFont.truetype(path,size,layout_engine=ImageFont.Layout.RAQM if features.check_feature("raqm") else ImageFont.Layout.BASIC)
    return {sz:load(sz) for sz in range(14,55)}


@lru_cache(maxsize=2)
def latin_font_set(weight):
    """Arabic-only system fonts lack Latin digits/percent glyphs; always use Latin-capable fonts."""
    w="-Bold" if weight=="Bold" else ""
    choices=[
      f"/usr/share/fonts/truetype/dejavu/DejaVuSans{w}.ttf",
      f"/usr/share/fonts/truetype/liberation2/LiberationSans{w}.ttf",
    ]
    path=next((v for v in choices if Path(v).is_file()),get_font_path(weight))
    return {sz:ImageFont.truetype(path,sz) if path else ImageFont.load_default() for sz in range(14,55)}


def _jalali_from_gregorian(gy,gm,gd):
    starts=[0,31,59,90,120,151,181,212,243,273,304,334]
    if gy>1600:jy,gy=979,gy-1600
    else:jy,gy=0,gy-621
    gy2=gy+1 if gm>2 else gy
    days=365*gy+(gy2+3)//4-(gy2+99)//100+(gy2+399)//400-80+gd+starts[gm-1]
    jy+=33*(days//12053);days%=12053;jy+=4*(days//1461);days%=1461
    if days>365:jy+=(days-1)//365;days=(days-1)%365
    if days<186:jm,jd=1+days//31,1+days%31
    else:jm,jd=7+(days-186)//30,1+(days-186)%30
    return jy,jm,jd


def formatted_time(dt, digits="fa"):
    if dt is None:return "زمان نامشخص"
    try:
        ts=dt.to_pydatetime(warn=False) if hasattr(dt,"to_pydatetime") else dt
        if ts.year<2000:return "زمان نامشخص"
        yy,mm,dd=_jalali_from_gregorian(ts.year,ts.month,ts.day)
        s=f"{yy:04}/{mm:02}/{dd:02}  {ts.hour:02}:{ts.minute:02}"
        return s.translate(str.maketrans("0123456789","۰۱۲۳۴۵۶۷۸۹")) if digits=="fa" else s
    except (TypeError,ValueError,AttributeError):return "زمان نامشخص"




def persian_weekday(dt):
    if dt is None:
        return ""
    try:
        ts=dt.to_pydatetime(warn=False) if hasattr(dt,"to_pydatetime") else dt
        names=["دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"]
        return names[ts.weekday()]
    except (TypeError,ValueError,AttributeError):
        return ""


def report_dayline(dt):
    stamp=formatted_time(dt,"fa")
    day=persian_weekday(dt)
    if not stamp or stamp=="زمان نامشخص":
        return "زمان نامشخص"
    return f"{day} | {stamp}" if day else stamp


def make_png(result,market,market_time,market_source,volume_usd):
    """Draw a polished mobile report aligned to the approved Helios sketch."""
    im=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(im)
    normal,bold=font_set("Regular"),font_set("Bold")
    latin_normal,latin_bold=latin_font_set("Regular"),latin_font_set("Bold")

    def font(size,heavy=False,latin=False):
        return (latin_bold if heavy else latin_normal)[size] if latin else (bold if heavy else normal)[size]

    has_raqm = bool(features.check_feature("raqm"))

    def _shape_rtl(s: str) -> str:
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            return get_display(arabic_reshaper.reshape(s))
        except (ImportError, ValueError, KeyError):
            return s

    def width(s, sz, heavy=False, direction="ltr", latin=False):
        value = str(s)
        f = font(sz, heavy, latin=latin)
        if direction == "rtl" and not has_raqm:
            value = _shape_rtl(value)
        try:
            return d.textlength(value, font=f, **({"direction": direction} if has_raqm else {}))
        except (KeyError, ValueError, TypeError, OSError):
            if direction == "rtl" and has_raqm:
                value = _shape_rtl(str(s))
            return d.textlength(value, font=f)

    def fa(s,x,y,sz=24,color=TEXT,heavy=False,min_x=0):
        s=str(s)
        f=font(sz,heavy)
        while sz>14 and x-width(s,sz,heavy,"rtl")<min_x:
            sz-=1; f=font(sz,heavy)
        if has_raqm:
            try:
                d.text((x,y),s,font=f,fill=color,direction="rtl",anchor="ra")
                return
            except (KeyError, ValueError, TypeError, OSError):
                pass
        shaped=_shape_rtl(s)
        d.text((x-width(shaped,sz,heavy,"ltr"),y),shaped,font=f,fill=color)

    def en(s,x,y,sz=24,color=TEXT,heavy=False,align="left"):
        s=str(s)
        x=x-width(s,sz,heavy,latin=True) if align=="right" else x
        try:
            if has_raqm:
                d.text((x,y),s,font=font(sz,heavy,latin=True),fill=color,direction="ltr")
            else:
                d.text((x,y),s,font=font(sz,heavy,latin=True),fill=color)
        except (KeyError, ValueError, TypeError, OSError):
            d.text((x,y),s,font=font(sz,heavy,latin=True),fill=color)

    def rounded(rect,color="white",radius=19,outline=None):
        d.rounded_rectangle(rect,radius=radius,fill=color,outline=outline,width=1)

    NEG="#D94B4B"
    SOFT_GREEN="#EDF8F4"

    # Header
    d.rectangle((0,0,W,188),fill=NAVY)
    rounded((50,48,60,135),TEAL,radius=3)
    en("FXS Intelligence",76,49,39,"white",True)
    en("Helios Ecosystem",77,106,20,"#A3CECD")
    fa("گزارش مقایسه نرخ رفع تعهد ارزی",1025,42,34,"white",True,min_x=465)
    fa("مرجع: آخرین استعلام‌های ثبت‌شده",1025,110,20,"#C2D4DF",min_x=560)
    d.rectangle((50,158,1030,164),fill=TEAL)

    # top summary box
    rounded((49,212,1031,388),"white",23,LINE)
    d.line((540,238,540,366),fill=LINE,width=2)
    # right: market
    fa("نرخ مبنای بازار آزاد",996,236,22,MUTED)
    en(fmt_toman(market),1000,272,50,NAVY,True,"right")
    fa("تومان به ازای دلار",995,341,18,MUTED)
    # left: report date
    fa("تاریخ گزارش",502,236,22,MUTED)
    fa(persian_weekday(market_time) or "—",503,279,28,NAVY,True,min_x=70)
    fa(formatted_time(market_time,"fa"),503,325,18,MUTED,min_x=70)

    fa("مقایسه مسیرهای رفع تعهد",1025,420,31,NAVY,True)
    fa("نرخ مؤثر بانک پس از کسر درصد کارمزد اظهار محاسبه شده است",1023,462,19,MUTED,min_x=120)

    result=result.head(7).reset_index(drop=True)
    count=len(result)

    table_top=524
    row_h=86 if count<=3 else 76 if count<=5 else 68
    header_h=72
    bottom=table_top+header_h+count*row_h+12
    rounded((50,table_top,1030,bottom),"white",19,LINE)
    d.rounded_rectangle((51,table_top+1,1029,table_top+header_h+10),radius=18,fill=NAVY)
    d.rectangle((51,table_top+50,1029,table_top+header_h+8),fill=NAVY)

    # columns: path | announced | fee | effective | diff | %
    x_path,x_ann,x_fee,x_eff,x_gap,x_pct=(986,802,640,478,304,150)
    for text_col,right in [
        ("مسیر",x_path),
        ("نرخ اعلامی",x_ann),
        ("کارمزد اظهار",x_fee),
        ("نرخ مؤثر",x_eff),
        ("اختلاف",x_gap),
        ("٪",x_pct),
    ]:
        fa(text_col,right,table_top+18,18,"white",True)

    for i,(_,r) in enumerate(result.iterrows()):
        row_y=table_top+header_h+i*row_h
        if i==0:
            d.rectangle((56,row_y+2,1024,row_y+row_h-3),fill=SOFT_GREEN)
            d.rounded_rectangle((1012,row_y+12,1020,row_y+row_h-12),radius=4,fill=TEAL)
        elif i%2==0:
            d.rectangle((56,row_y+2,1024,row_y+row_h-2),fill="#FAFCFD")
        if i:
            d.line((64,row_y,1016,row_y),fill=LINE,width=1)

        label=str(r["label"])
        label=label if len(label)<=16 else label[:15]+"…"
        fa(label,x_path,row_y+22,22,NAVY,True,min_x=820)

        en(fmt_toman(float(r["raw_rate"])),x_ann,row_y+22,22,TEXT,True,"right")
        fee=float(r.get("fee_pct",0) or 0)
        fee_text=(f"{fee:.2f}%" if str(r.get("kind",""))=="بانک" else "0")
        en(fee_text,x_fee,row_y+22,22,TEXT,False,"right")
        en(fmt_toman(float(r["effective_rate"])),x_eff,row_y+22,22,NAVY,True,"right")

        gap_t=-abs(float(r["gap_toman"]))
        gap_p=-abs(float(r["gap_pct"]))
        en(fmt_toman(gap_t),x_gap,row_y+22,22,NEG,True,"right")
        en(fmt_percent(gap_p),x_pct,row_y+22,22,NEG,True,"right")

    # Best effective rate summary
    summary_top=bottom+28
    rounded((50,summary_top,1030,summary_top+126),"#F5FAF8",18,LINE)
    fa("بالاترین نرخ مؤثر",995,summary_top+16,22,TEAL,True)
    best_label=str(result.iloc[0]["label"]) if count else "—"
    best_rate=float(result.iloc[0]["effective_rate"]) if count else 0.0
    fa(best_label,995,summary_top+58,31,NAVY,True,min_x=640)
    en(fmt_toman(best_rate),470,summary_top+66,36,NAVY,True,"right")

    # Comparison bars
    bar_top=summary_top+198
    fa("مقایسه درصد فاصله مسیرها با بازار آزاد",1016,bar_top-30,20,NAVY,True,min_x=350)
    limit=max(1.0,max(abs(float(x)) for x in result["gap_pct"])) if count else 1.0
    for i,(_,r) in enumerate(result.iterrows()):
        yy=bar_top+i*45
        fa(str(r["label"]),1015,yy-5,17,MUTED,False,min_x=775)
        d.rounded_rectangle((350,yy+3,749,yy+15),radius=6,fill="#E8EEF2")
        bw=max(4,round(min(1,abs(float(r["gap_pct"]))/limit)*399))
        d.rounded_rectangle((749-bw,yy+3,749,yy+15),radius=6,fill=NEG)
        en(fmt_percent(-abs(float(r["gap_pct"]))),322,yy-7,17,NEG,True,align="right")

    footer_y=1204
    fa("اختلاف منفی یعنی نرخ مؤثر کمتر از بازار آزاد است.",1017,footer_y,19,TEXT,min_x=110)
    fa("نرخ‌ها استعلامی‌اند و ممکن است مربوط به ساعت‌های متفاوت باشند.",1017,footer_y+31,18,MUTED,min_x=90)
    d.line((52,1282,1028,1282),fill=LINE,width=2)
    en("HELIOS  /  ASHA SPEED KHORSHID",55,1296,17,MUTED)
    en("REPORT",1016,1296,17,MUTED,align="right")
    output=io.BytesIO(); im.save(output,format="PNG",optimize=True)
    return output.getvalue()
