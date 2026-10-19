"""One-page WhatsApp report generator, 1080x1350 PNG. No font files shipped."""
from __future__ import annotations
import io
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.request
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from fx_core import fmt_toman, fmt_percent

W, H = 1080, 1350
NAVY = "#11283A"
TEXT = "#233545"
MUTED = "#778A99"
TEAL = "#0D8F85"
BACKGROUND = "#F5F7FA"
BORDER = "#E4EAF0"


@lru_cache(maxsize=3)
def get_font_path(weight: str = "Regular") -> str | None:
    # The application fetches the open-source Vazirmatn font at runtime; no font bundled in ZIP.
    cache_dir = Path.home() / ".cache" / "helios_fx"
    dest = cache_dir / f"Vazirmatn-{weight}.ttf"
    if dest.exists() and dest.stat().st_size > 30000:
        return str(dest)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-{weight}.ttf"
        with urllib.request.urlopen(url, timeout=8) as response:
            content = response.read(1_000_000)
        if len(content) > 30000 and content[:4] in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
            dest.write_bytes(content)
            return str(dest)
    except (OSError, ValueError, TimeoutError):
        pass
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]:
        if Path(path).exists():
            return path
    return None


def prepare_fonts() -> tuple[dict[int, ImageFont.FreeTypeFont],dict[int, ImageFont.FreeTypeFont]]:
    p_regular, p_bold = get_font_path("Regular"), get_font_path("Bold")
    def load(path: str | None, pt: int):
        return ImageFont.truetype(path, pt) if path else ImageFont.load_default()
    return ({n: load(p_regular, n) for n in [19,22,24,26,30,32,36,42,52]},
            {n: load(p_bold or p_regular, n) for n in [19,22,24,26,30,32,36,42,52]})



def persian_num(value: str) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def _jalali_from_gregorian(gy: int, gm: int, gd: int) -> tuple[int,int,int]:
    # Integer Gregorian -> Jalali calculation; no date dependency required.
    starts = [0,31,59,90,120,151,181,212,243,273,304,334]
    if gy > 1600:
        jy, gy = 979, gy - 1600
    else:
        jy, gy = 0, gy - 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365*gy + (gy2+3)//4 - (gy2+99)//100 + (gy2+399)//400 - 80 + gd + starts[gm-1]
    jy += 33*(days//12053)
    days %= 12053
    jy += 4*(days//1461)
    days %= 1461
    if days > 365:
        jy += (days - 1)//365
        days = (days-1)%365
    if days < 186:
        jm, jd = 1 + days//31, 1+days%31
    else:
        jm, jd = 7+(days-186)//30, 1+(days-186)%30
    return jy,jm,jd


def formatted_time(dt) -> str:
    if dt is None:
        return "زمان نامشخص"
    try:
        ts = dt.to_pydatetime(warn=False) if hasattr(dt,"to_pydatetime") else dt
        if ts.year < 2000:
            return "زمان نامشخص"
        jy,jm,jd = _jalali_from_gregorian(ts.year, ts.month, ts.day)
        return persian_num(f"{jy:04}/{jm:02}/{jd:02} {ts.hour:02}:{ts.minute:02}")
    except (TypeError, ValueError, AttributeError):
        return "زمان نامشخص"

def make_png(result, market: float, market_time, market_source: str, volume_usd: float) -> bytes:
    """Result is a compare() DataFrame containing at most 7 filtered routes."""
    image = Image.new("RGB", (W,H), BACKGROUND)
    d = ImageDraw.Draw(image)
    fonts, bold = prepare_fonts()

    def rtl(text: str, x_right: int, y: int, size: int=26, ink: str=TEXT, heavy: bool=False):
        font = bold[size] if heavy else fonts[size]
        # Pillow RAQM handles Persian glyph shaping and bidi, including mixed numerals.
        try:
            d.text((x_right,y),str(text),font=font,fill=ink,direction="rtl",anchor="ra")
        except (ValueError, TypeError, KeyError):
            d.text((x_right-d.textlength(str(text),font=font),y),str(text),font=font,fill=ink)
    def ltr(text: str, x: int, y:int, size:int=26, ink: str=TEXT, heavy=False):
        d.text((x,y),text,font=(bold[size] if heavy else fonts[size]),fill=ink)
    def card(rect, fill="white", outline=None, radius=24):
        d.rounded_rectangle(rect,radius=radius,fill=fill,outline=outline,width=2)

    d.rectangle((0,0,W,214),fill=NAVY)
    d.rectangle((62,171,1018,177),fill=TEAL)
    ltr("HELIOS",60,40,52,"white",True)
    ltr("ASHA SPEED  /  FX INTELLIGENCE",64,108,19,"#AED7D3")
    rtl("مقایسه نرخ رفع تعهد ارزی",1018,49,42,"white",True)
    rtl("گزارش نرخ‌های آخرین استعلام",1018,113,24,"#D5E3EA")

    card((50,240,1030,406))
    d.line((538,266,538,380),fill=BORDER,width=2)
    rtl("نرخ مبنای بازار آزاد",993,259,26,MUTED)
    rtl(persian_num(fmt_toman(market)),995,292,52,NAVY,True)
    rtl("تومان / دلار",992,359,22,MUTED)
    rtl("بازه مقایسه (USD)",500,259,26,MUTED)
    ltr(f"{volume_usd:,.0f}",89,292,52,NAVY,True)
    rtl(formatted_time(market_time),493,360,19,MUTED)

    rtl("مقایسه مسیرهای تأمین / رفع تعهد",1015,437,36,NAVY,True)
    rtl("نرخ مؤثر بانک‌ها با کسر کارمزد اظهار محاسبه شده است",1014,488,22,MUTED)

    rows = result.head(7).reset_index(drop=True)
    table_top = 552
    card((50,table_top,1030,table_top+80+max(1,len(rows))*72+13),radius=20)
    d.rounded_rectangle((51,table_top+1,1029,table_top+80),radius=18,fill=NAVY)
    # Column header right edges: route, eff, spread per USD, pct, full USD equivalent.
    for title, right in [("مسیر",998),("نرخ مؤثر",760),("فاصله تومان",569),("اختلاف٪",354),("معادل دلار",177)]:
        rtl(title,right,table_top+24,22,"white",True)

    for i,(_,row) in enumerate(rows.iterrows()):
        top = table_top + 80 + i*72
        if i % 2:
            d.rectangle((57,top-2,1023,top+71),fill="#F8FAFC")
        if i:
            d.line((64,top-4,1017,top-4),fill=BORDER,width=1)
        label = str(row["label"])
        if len(label)>23: label=label[:22]+"…"
        rtl(label,998,top+5,24,NAVY,True)
        rtl(formatted_time(row["timestamp"]),997,top+39,19,MUTED)
        rtl(persian_num(fmt_toman(float(row["effective_rate"]))),760,top+19,24,TEXT,True)
        rtl(persian_num(fmt_toman(float(row["gap_toman"]))),569,top+19,24,TEXT,True)
        rtl(persian_num(fmt_percent(float(row["gap_pct"]))),354,top+19,24,TEAL if float(row["gap_pct"]) >= 0 else "#AF4848",True)
        rtl(persian_num(fmt_toman(float(row["gap_usd"]))),177,top+19,24,TEXT,True)

    table_bottom = table_top+80+max(1,len(rows))*72+13
    if len(rows) <= 3 and len(rows)>0:
        summary_y = table_bottom + 48
        if summary_y + 180 <= 1090:
            best = rows.iloc[0]
            card((50,summary_y,1030,summary_y+176),fill="#E8F4F1",radius=20)
            rtl("بالاترین نرخ مؤثر در مسیرهای مقایسه‌شده",994,summary_y+16,24,TEAL,True)
            rtl(str(best["label"]),995,summary_y+51,36,NAVY,True)
            rtl("معادل دلاری فاصله در حجم انتخاب‌شده",995,summary_y+112,22,MUTED)
            ltr(f"{best['gap_usd']:,.0f} USD",80,summary_y+107,36,NAVY,True)
    footer_top=max(table_bottom+32, H-225)
    if footer_top+95>H-81:
        footer_top=H-181
    rtl("اختلاف مثبت یعنی نرخ مؤثر کمتر از بازار آزاد است.",1007,footer_top,24,TEXT)
    rtl("مبالغ بر اساس آخرین نرخ ثبت‌شده هر منبع در شیت محاسبه شده‌اند.",1007,footer_top+32,22,MUTED)
    rtl("استعلامی • مشروط به زمان و شرایط معامله",1008,footer_top+62,22,MUTED)
    d.line((56,H-86,1022,H-86),fill=BORDER,width=2)
    ltr("HELIOS  |  ASHA SPEED KHORSHID",57,H-67,19,MUTED)
    now = datetime.now(ZoneInfo("Asia/Tehran")).replace(tzinfo=None)
    rtl("زمان تهیه گزارش: "+formatted_time(now),1015,H-67,19,MUTED)

    stream = io.BytesIO()
    image.save(stream,format="PNG",optimize=True)
    return stream.getvalue()
