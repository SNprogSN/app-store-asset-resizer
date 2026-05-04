#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Store Ikon Méretező
=======================
Egyetlen forrásképből automatikusan előállítja az összes szükséges
képméretet Google Play Store és Apple App Store feltöltéshez.

Generalált kimenetek:
  google_play/
    - play_store_icon_512   – Play Store ikon (512×512, max 1 MB)
    - android_launcher_*    – Launcher ikonok xxxhdpi..mdpi (192….48 px)
    - play_store_feature    – Kiemelési kép / Feature Graphic (1024×500, max 15 MB)
    - screenshots/phone/    – Telefon képernyőképek (1080×1920 és fordítva)
    - screenshots/tablet_7inch/ – 7"-os tablet (1200×1920)
    - screenshots/tablet_10inch/ – 10"-os tablet: MIN (1200×1920) + BEST (1600×2560)
  apple_store/
    - ios_AppStore_1024     – App Store feltöltő ikon (alpha nélkül, Apple előírás)
    - ios_iPhone_* / ios_iPad_* – összes támogat.  eszközméret (20…1024 px)
    - screenshots/iphone_*/  – iPhone 5.5", 6.5", 6.7"
    - screenshots/ipad_pro_*/ – iPad Pro 11" és 12.9"

Felhasználás:
    python icon_resizer.py          # grafikus mód (tkinter GUI)
    pip install Pillow               # kötelező függőség (automatikusan telepíti, ha hiányzik)

Függőségek:
    Pillow >= 10.0  (https://pillow.readthedocs.io)
    Python >= 3.9
    tkinter (Python-ba beépített, csak Windows/Linux desktop szükséges)
"""

import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ── Pillow automatikus telepítés ───────────────────────────────────────────────
# Ha a Pillow könyvtár nincs telepítve, az import kivételével megpróbálja
# automatikusan pip-pel feltelepíteni. Ha ez sem sikerül, hibaüzenettel kilép.
try:
    from PIL import Image, ImageFilter
except ImportError:
    import subprocess
    ret = subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"],
                        capture_output=True, text=True)
    if ret.returncode != 0:
        messagebox.showerror(
            "Telepítési hiba",
            "A Pillow könyvtár telepítése nem sikerült.\n"
            "Futtassa manuálisan:\n\n    pip install Pillow"
        )
        sys.exit(1)
    from PIL import Image, ImageFilter


# ── cairosvg opcionális: SVG forrásképek raszterizálásához ────────────────────────
# Ha jelen van, az SVG fájlok automatikusan 2048 px szélességre raszterizálva
# lesznek betöltés előtt, így minden kimeneti formátumhoz felhasználhatók.
# Windows-on a cairosvg libcairo-2.dll natív könyvtárat igényel; ha az hiányzik,
# svglib + renderPDF + PyMuPDF kombinációt használunk fallbackként
# (teljesen Cairo-mentes, csak Python wheel-ek kellenek).
_CAIROSVG_AVAILABLE = False
_PYMUPDF_AVAILABLE  = False   # svglib + reportlab renderPDF + PyMuPDF fallback

# 1) cairosvg (Linux/macOS, vagy ha libcairo-2.dll elérhető Windowson is)
try:
    import cairosvg as _cairosvg
    _CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    try:
        import subprocess as _sp_svg
        _rv = _sp_svg.run(
            [sys.executable, "-m", "pip", "install", "cairosvg"],
            capture_output=True, text=True
        )
        if _rv.returncode == 0:
            try:
                import cairosvg as _cairosvg
                _CAIROSVG_AVAILABLE = True
            except (ImportError, OSError):
                pass
    except Exception:
        pass

# 2) svglib + renderPDF + PyMuPDF – Windows-barát fallback, nem igényel Cairo DLL-t
#    A renderPDF modul tisztán Python, a PyMuPDF wheel statikusan linkelt MuPDF-et tartalmaz.
if not _CAIROSVG_AVAILABLE:
    try:
        from svglib.svglib import svg2rlg as _svg2rlg
        from reportlab.graphics import renderPDF as _renderPDF
        import fitz as _fitz
        _PYMUPDF_AVAILABLE = True
    except ImportError:
        try:
            import subprocess as _sp_svg2
            _rv2 = _sp_svg2.run(
                [sys.executable, "-m", "pip", "install", "svglib", "PyMuPDF"],
                capture_output=True, text=True
            )
            if _rv2.returncode == 0:
                try:
                    from svglib.svglib import svg2rlg as _svg2rlg
                    from reportlab.graphics import renderPDF as _renderPDF
                    import fitz as _fitz
                    _PYMUPDF_AVAILABLE = True
                except ImportError:
                    pass
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════════
# MÉRETTÁBLÁK
# Minden lista elemének formátuma: (fájlnév_alap, szélesség_px, magasság_px, leírás)
# A 2D listák (SCREENSHOTS) és a tuple (GOOGLE_FEATURE) ugyanezt a struktúrát követik.
# ══════════════════════════════════════════════════════════════════════════════════

# Google Play Store által előírt launcher ikonméretek és a feltöltési ikon.
# Forrás: https://developer.android.com/distribute/google-play/resources/icon-design-specifications
GOOGLE_PLAY_ICONS = [
    ("play_store_icon_512",        512, 512, "Play Store feltöltési ikon (max 1 MB, PNG/JPEG)"),
    ("android_launcher_xxxhdpi",   192, 192, "Launcher ikon xxxhdpi (640 dpi)"),
    ("android_launcher_xxhdpi",    144, 144, "Launcher ikon xxhdpi  (480 dpi)"),
    ("android_launcher_xhdpi",      96,  96, "Launcher ikon xhdpi   (320 dpi)"),
    ("android_launcher_hdpi",       72,  72, "Launcher ikon hdpi    (240 dpi)"),
    ("android_launcher_mdpi",       48,  48, "Launcher ikon mdpi    (160 dpi)"),
]

# Feature Graphic: kötelező kiemelési kép a Play Store listázóban és a profiloldalon.
# Méret: pontosan 1024×500 px. Maximális fájlméret: 15 MB.
GOOGLE_FEATURE = (
    "play_store_feature_1024x500", 1024, 500,
    "Kiemelési kép / Feature Graphic (1024×500, max 15 MB)"
)

# Apple által előírt ikonméretek iOS-hez és iPadOS-hez.
# Forrás: https://developer.apple.com/design/human-interface-guidelines/app-icons
# Megnevezési konvenció: ios_{eszkoz}_{pont}pt_{skala}x_{pixel}px
APPLE_ICONS = [
    ("ios_AppStore_1024",              1024, 1024, "App Store feltöltési ikon – tilos az alpha! (Apple követelmény)"),
    ("ios_iPhone_60pt_3x_180",          180,  180, "iPhone App ikon @3x  (60pt × 3 = 180 px)"),
    ("ios_iPad_Pro_83.5pt_2x_167",      167,  167, "iPad Pro App ikon @2x (83.5pt × 2 = 167 px)"),
    ("ios_iPad_76pt_2x_152",            152,  152, "iPad App ikon @2x     (76pt × 2 = 152 px)"),
    ("ios_iPhone_60pt_2x_Spot40pt_3x",  120,  120, "iPhone App @2x (60pt×2) / Spotlight @3x (40pt×3)"),
    ("ios_iPhone_29pt_3x_87",            87,   87, "iPhone Beállítások @3x (29pt × 3 = 87 px)"),
    ("ios_iPhone_Spot40pt_2x_80",        80,   80, "iPhone/iPad Spotlight @2x (40pt × 2 = 80 px)"),
    ("ios_iPad_76pt_1x_76",              76,   76, "iPad App ikon @1x     (76pt × 1 = 76 px)"),
    ("ios_iPhone_20pt_3x_60",            60,   60, "iPhone Értesítés @3x  (20pt × 3 = 60 px)"),
    ("ios_iPhone_29pt_2x_58",            58,   58, "iPhone/iPad Beállítások @2x (29pt × 2 = 58 px)"),
    ("ios_iPhone_Spot40pt_1x_40",        40,   40, "iPhone/iPad Spotlight @1x (40pt) / Értesítés @2x (20pt×2)"),
    ("ios_iPad_29pt_1x_29",              29,   29, "iPad Beállítások @1x  (29pt × 1 = 29 px)"),
    ("ios_iPad_20pt_1x_20",              20,   20, "iPad Értesítés @1x    (20pt × 1 = 20 px)"),
]

# Az Apple előírja, hogy az App Store feltöltő ikon (1024×1024) NE tartalmazzon
# alpha (transzparencia) csatornát. Az ilyen képet a feltöltés során elutasitják.
# save_png() fehér háttérre lapítja a transparenciát ezeknél az ikonoknál.
APPLE_NO_ALPHA = {"ios_AppStore_1024"}

# Google Play Store által előírt maximális fájlméretek (byte-ban).
# Ha a generált kép meghaladja a korlátot, a naplóban figyelmeztetés jelenik meg.
LIMITS_BYTES = {
    "play_store_icon_512":          1 * 1024 * 1024,   # Play Store ikon: max 1 MB
    "play_store_feature_1024x500": 15 * 1024 * 1024,   # Feature Graphic: max 15 MB
}

# Elérhető átméretezési módok téglalap arányú kimenetekhez (Feature Graphic, screenshots).
# Formátum: (megjelenit_cimke, belso_kulcsszo)
#   fill       – Zoom + középről vag: minden pixel ki van töltve, de szorulhat vagás.
#   fit_white  – Teljes kep belefer fehér letterbox-szal a maradékban.
#   fit_black  – Teljes kep belefer fekete letterbox-szal a maradékban.
#   blur       – Elmosott (Gaussian blur) kitoltő háttér + éles előtér középen (cinematic stílus).
FEATURE_MODES = [
    ("Vágás – középre igazítva (fill)",   "fill"),
    ("Keret – fehér háttér (fit)",         "fit_white"),
    ("Keret – fekete háttér (fit)",        "fit_black"),
    ("Elmosott háttér (blur + overlay)",   "blur"),
]

# ── Google Play Store képernyőképek ────────────────────────────────────────────
# Forrás: https://support.google.com/googleplay/android-developer/answer/9866151
#
# Struktúra: [(almappa_neve, [(fájlnév, szélesség, magasság, leírás), ...]), ...]
# Minden almappába kerül portrait és landscape változat is.
#
# FONTOS különbség a tablet kategóriák között:
#   7"  – Rugalmasabb, elfogadja az 1280x800 méretet is.
#   10" – Szigorúbb: a rövidebb oldal kötelezően >= 1080 px.
#          Ha 1920x1080-t töltöl fel a 10"-os mezon, elutasitja,
#          mert az telefon/TV arány (nem tablet UI).
#          Ajánlott: 2560x1600 (16:10), minimum OK: 1920x1200.
GOOGLE_SCREENSHOTS = [
    ("phone", [
        ("screenshot_phone_portrait",   1080, 1920, "Telefon – álló  (1080×1920)"),
        ("screenshot_phone_landscape",  1920, 1080, "Telefon – fekvő (1920×1080)"),
    ]),
    ("tablet_7inch", [
        ("screenshot_7tab_portrait",    1200, 1920, '7" tablet – álló  (1200×1920)'),
        ("screenshot_7tab_landscape",   1920, 1200, '7" tablet – fekvő (1920×1200)'),
    ]),
    ("tablet_10inch", [
        # BEST: 16:10 arány, a Google Pixel Tablet natif felbontása – biztosan átmegy
        ("screenshot_10tab_portrait_best",   1600, 2560, '10" tablet – álló  BEST (1600×2560)'),
        ("screenshot_10tab_landscape_best",  2560, 1600, '10" tablet – fekvő BEST (2560×1600)'),
        # MIN: rövidebb oldal = 1200 px, megfelel a 10"-os minimum követelménynek
        ("screenshot_10tab_portrait_min",    1200, 1920, '10" tablet – álló  MIN  (1200×1920)'),
        ("screenshot_10tab_landscape_min",   1920, 1200, '10" tablet – fekvő MIN  (1920×1200)'),
    ]),
]

# ── Apple App Store képernyőképek ───────────────────────────────────────────────
# Forrás: https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications
#
# Az Apple App Store Connect kötelező méretek eszköz-csoportonként.
# A 6.7"-es és 12.9"-es iPad Pro méret feltöltése elegendő a több eszközt is lefedni.
# Portrait és landscape változatot is generálunk, külön almappákba.
APPLE_SCREENSHOTS = [
    ("iphone_6_7inch", [
        ("screenshot_iphone_6_7_portrait",   1290, 2796, 'iPhone 6.7" – álló  (1290×2796)'),
        ("screenshot_iphone_6_7_landscape",  2796, 1290, 'iPhone 6.7" – fekvő (2796×1290)'),
    ]),
    ("iphone_6_5inch", [
        ("screenshot_iphone_6_5_portrait",   1284, 2778, 'iPhone 6.5" – álló  (1284×2778)'),
        ("screenshot_iphone_6_5_landscape",  2778, 1284, 'iPhone 6.5" – fekvő (2778×1284)'),
    ]),
    ("iphone_5_5inch", [
        ("screenshot_iphone_5_5_portrait",   1242, 2208, 'iPhone 5.5" – álló  (1242×2208)'),
        ("screenshot_iphone_5_5_landscape",  2208, 1242, 'iPhone 5.5" – fekvő (2208×1242)'),
    ]),
    ("ipad_pro_12_9inch", [
        ("screenshot_ipad_pro_12_9_portrait",  2048, 2732, 'iPad Pro 12.9" – álló  (2048×2732)'),
        ("screenshot_ipad_pro_12_9_landscape", 2732, 2048, 'iPad Pro 12.9" – fekvő (2732×2048)'),
    ]),
    ("ipad_pro_11inch", [
        ("screenshot_ipad_pro_11_portrait",  1668, 2388, 'iPad Pro 11" – álló  (1668×2388)'),
        ("screenshot_ipad_pro_11_landscape", 2388, 1668, 'iPad Pro 11" – fekvő (2388×1668)'),
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════════
# KÉPFELDOLGOZÓ FÜGGVÉNYEK
# ══════════════════════════════════════════════════════════════════════════════════

def _to_rgba(img):
    """Kép biztonságos RGBA módba konvertálása. Másolatot ad vissza, az eredetit nem módosítja."""
    return img.convert("RGBA") if img.mode != "RGBA" else img.copy()


def resize_square(img, size):
    """Ikon méretezés: középre vágás négyzet arányra, majd átméretezés.

    Args:
        img:  Pillow Image objektum (bármilyen mód és méret elfogadott).
        size: Kimeneti méret pixelben (négyzet: size × size).

    Returns:
        Új RGBA Image, pontosan size × size pixeles.
    """
    img = _to_rgba(img)
    w, h = img.size
    if w != h:
        s = min(w, h)
        img = img.crop(((w - s) // 2, (h - s) // 2,
                        (w + s) // 2, (h + s) // 2))
    return img.resize((size, size), Image.LANCZOS)


def resize_feature(img, tw, th, mode):
    """Téglalap célméretre skáláz: Feature Graphic, screenshot.

    Args:
        img:  Pillow Image objektum.
        tw:   Cél szélesség pixelben.
        th:   Cél magasság pixelben.
        mode: "Átméretezési mód"; lehetséges értékek:
              'fill'      – teljes kitöltés, középről vag
              'fit_white' – belefordítás fehér letterbox-szal
              'fit_black' – belefordítás fekete letterbox-szal
              'blur'      – elmosott háttér + éles előtér

    Returns:
        Új RGBA Image, pontosan tw × th pixeles.
    """
    img = _to_rgba(img)
    sw, sh = img.size
    src_r = sw / sh
    tgt_r = tw / th

    if mode == "fill":
        # Kitölti a teljes területet, a középső rész marad
        if src_r > tgt_r:
            nh, nw = th, int(sw * th / sh)
        else:
            nw, nh = tw, int(sh * tw / sw)
        scaled = img.resize((nw, nh), Image.LANCZOS)
        l, t = (nw - tw) // 2, (nh - th) // 2
        return scaled.crop((l, t, l + tw, t + th))

    elif mode in ("fit_white", "fit_black"):
        # Belefér, a maradék terület egyszínű háttér
        bg_color = (255, 255, 255, 255) if mode == "fit_white" else (0, 0, 0, 255)
        if src_r > tgt_r:
            nw, nh = tw, int(sh * tw / sw)
        else:
            nh, nw = th, int(sw * th / sh)
        scaled = img.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (tw, th), bg_color)
        canvas.paste(scaled, ((tw - nw) // 2, (th - nh) // 2), scaled)
        return canvas

    elif mode == "blur":
        # Elmosott kitöltő háttér + éles előtér középen
        if src_r > tgt_r:
            bg_h, bg_w = th, int(sw * th / sh)
        else:
            bg_w, bg_h = tw, int(sh * tw / sw)
        bg = img.resize((bg_w, bg_h), Image.LANCZOS)
        bl, bt = (bg_w - tw) // 2, (bg_h - th) // 2
        bg = bg.crop((bl, bt, bl + tw, bt + th))
        bg = bg.convert("RGB").filter(ImageFilter.GaussianBlur(radius=18)).convert("RGBA")
        # Sötétítő overlay a jobb kontrasztért
        overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 85))
        bg = Image.alpha_composite(bg, overlay)
        # Előtér: belefér (80%-os margóval)
        m_w, m_h = int(tw * 0.80), int(th * 0.80)
        m_r = m_w / m_h
        if src_r > m_r:
            fg_w, fg_h = m_w, int(sh * m_w / sw)
        else:
            fg_h, fg_w = m_h, int(sw * m_h / sh)
        fg = img.resize((fg_w, fg_h), Image.LANCZOS)
        bg.paste(fg, ((tw - fg_w) // 2, (th - fg_h) // 2), fg)
        return bg

    # Ismeretlen mód esetén egyszerű nyújtásos átméretezés (nem ajánlott)
    return img.resize((tw, th), Image.LANCZOS)


def save_png(img, path, no_alpha=False):
    """Kép mentése PNG formátumban, opcionális alpha-lapítással.

    Args:
        img:      Pillow Image objektum.
        path:     Teljes cél elérési út (str).
        no_alpha: Ha True, az alpha csatornát fehér háttérre simítja mentés előtt.
                  Az Apple App Store feltöltő ikonhoz kötelezően True-ra kell állítani.

    Returns:
        (path, size_bytes) tuple – a mentett fájl elérési útja és mérete byte-ban.
    """
    if no_alpha:
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img.convert("RGB"))
        bg.save(path, "PNG", optimize=True)
    else:
        img.save(path, "PNG", optimize=True)
    return path, os.path.getsize(path)


def save_svg(img, path, w, h):
    """Kép mentése SVG formátumban, base64-kódolt PNG képként beágyazva.

    Az SVG fájl egy szabványos vektoros burok, amelybe a raszteres kép
    base64 kódolással van beágyazva. Így megnyitható vektoros szerkesztőkben
    (pl. Inkscape, Illustrator) és megőrzi a pontos pixelméreteket.

    Args:
        img:  Pillow Image objektum.
        path: Teljes cél elérési út (str), .svg kiterjesztéssel.
        w:    Kép szélessége pixelben (SVG viewBox és width attr.).
        h:    Kép magassága pixelben (SVG viewBox és height attr.).

    Returns:
        (path, size_bytes) tuple – a mentett fájl elérési útja és mérete byte-ban.
    """
    import base64
    buf = io.BytesIO()
    out_img = img.convert("RGBA") if img.mode not in ("RGBA", "RGB") else img
    out_img.save(buf, "PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f'  <image x="0" y="0" width="{w}" height="{h}" '
        f'xlink:href="data:image/png;base64,{b64}"/>\n'
        f'</svg>\n'
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    return path, os.path.getsize(path)


def load_source_image(path):
    """Forrás képfájl betöltése PIL Image-ként.

    PNG/JPG/BMP/WEBP stb. esetén közvetlenül Pillow-val tölti be.
    SVG esetén cairosvg-vel 2048 px szélességre raszterizálja, majd tölti be.
    Az SVG méretarányát megőrzi (csak a szélességet rögzíti 2048 px-re).

    Args:
        path: A forrásfájl elérési útja (str).

    Returns:
        (PIL Image, is_svg: bool) tuple.

    Raises:
        RuntimeError: ha SVG betöltés sikertelen (cairosvg hiányzik vagy hibás SVG).
    """
    suffix = Path(path).suffix.lower()
    if suffix == ".svg":
        if _CAIROSVG_AVAILABLE:
            png_bytes = _cairosvg.svg2png(url=path, output_width=2048)
            img = Image.open(io.BytesIO(png_bytes))
            img.load()
            return img, True
        elif _PYMUPDF_AVAILABLE:
            # SVG → PDF (reportlab renderPDF, Cairo-mentes) → PNG (PyMuPDF, statikus MuPDF)
            drawing = _svg2rlg(path)
            if drawing is None:
                raise RuntimeError(f"SVG betöltése sikertelen (üres rajz): {path}")
            pdf_bytes = _renderPDF.drawToString(drawing)
            doc = _fitz.open("pdf", pdf_bytes)
            page = doc[0]
            scale = 2048.0 / page.rect.width if page.rect.width else 1.0
            mat = _fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=True)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img.load()
            return img, True
        else:
            raise RuntimeError(
                "SVG betöltéshez a cairosvg vagy svglib+PyMuPDF könyvtár szükséges.\n"
                "Telepítse manuálisan:\n\n    pip install svglib PyMuPDF"
            )
    img = Image.open(path)
    img.load()
    return img, False


# ══════════════════════════════════════════════════════════════════════════════════
# GUI
# ══════════════════════════════════════════════════════════════════════════════════

class AppIconResizer(tk.Tk):
    """Főablak: App Store Ikon Méretező GUI.

    Tkinter alapú grafikus felület, amely a felhasználótól átveszi
    a forrásképet és a kimeneti beállításokat, majd elindítja a
    képgenerálást az összes kiválasztott store és típus esetére.
    """

    def __init__(self):
        super().__init__()
        self.title("App Store Ikon Méretező")
        self.minsize(660, 580)

        self.v_input       = tk.StringVar()
        self.v_output      = tk.StringVar()
        self.v_google      = tk.BooleanVar(value=True)
        self.v_apple       = tk.BooleanVar(value=True)
        self.v_screenshots = tk.BooleanVar(value=True)
        self.v_mode        = tk.StringVar(value=FEATURE_MODES[0][0])

        self._build_ui()
        self._center(700, 680)

    def _center(self, w, h):
        """Ablakot középre igazítja a képernyőn."""
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── UI ────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("H.TLabel",          font=("Segoe UI", 14, "bold"), foreground="#1a237e")
        style.configure("Gen.TButton",        font=("Segoe UI", 11, "bold"), padding=(0, 8))
        style.configure("TLabelframe.Label",  font=("Segoe UI", 9, "bold"))

        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        # Cím
        ttk.Label(root, text="App Store Ikon Méretező", style="H.TLabel").pack(pady=(0, 12))

        # Forrás kép
        f1 = ttk.LabelFrame(root, text="Forrás kép", padding=8)
        f1.pack(fill=tk.X, pady=(0, 6))
        ttk.Entry(f1, textvariable=self.v_input, width=62).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(f1, text="Tallózás…", command=self._browse_input).pack(side=tk.LEFT)

        # Kimeneti mappa
        f2 = ttk.LabelFrame(root, text="Kimeneti mappa", padding=8)
        f2.pack(fill=tk.X, pady=(0, 6))
        ttk.Entry(f2, textvariable=self.v_output, width=62).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(f2, text="Tallózás…", command=self._browse_output).pack(side=tk.LEFT)

        # Beállítások
        f3 = ttk.LabelFrame(root, text="Beállítások", padding=8)
        f3.pack(fill=tk.X, pady=(0, 6))

        row1 = ttk.Frame(f3)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="Store:").pack(side=tk.LEFT)
        ttk.Checkbutton(row1, text="Google Play Store", variable=self.v_google).pack(
            side=tk.LEFT, padx=(10, 0))
        ttk.Checkbutton(row1, text="Apple App Store",   variable=self.v_apple).pack(
            side=tk.LEFT, padx=(10, 0))

        row1b = ttk.Frame(f3)
        row1b.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row1b, text="Típus: ").pack(side=tk.LEFT)
        ttk.Checkbutton(row1b, text="Ikonok + Feature Graphic",
                        variable=tk.BooleanVar(value=True), state="disabled").pack(
            side=tk.LEFT, padx=(10, 0))
        ttk.Checkbutton(row1b, text="Képernyőképek (screenshots)",
                        variable=self.v_screenshots).pack(
            side=tk.LEFT, padx=(10, 0))

        row2 = ttk.Frame(f3)
        row2.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row2, text="Kiemelési kép / screenshot módja:").pack(side=tk.LEFT)
        ttk.Combobox(row2, textvariable=self.v_mode,
                     values=[m[0] for m in FEATURE_MODES],
                     state="readonly", width=36).pack(side=tk.LEFT, padx=(8, 0))

        # Generálás gomb
        ttk.Button(root, text="▶  Képek generálása", style="Gen.TButton",
                   command=self._generate).pack(fill=tk.X, pady=(6, 6))

        # Folyamatjelző
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 6))

        # Napló
        log_frm = ttk.LabelFrame(root, text="Napló", padding=6)
        log_frm.pack(fill=tk.BOTH, expand=True)
        self.log = tk.Text(log_frm, height=12, font=("Consolas", 9),
                           wrap=tk.WORD, state=tk.DISABLED, bg="#f8f8f8")
        sb = ttk.Scrollbar(log_frm, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.log.tag_config("ok",   foreground="#2e7d32")
        self.log.tag_config("warn", foreground="#e65100")
        self.log.tag_config("err",  foreground="#b71c1c")
        self.log.tag_config("info", foreground="#0d47a1")
        self.log.tag_config("head", foreground="#4a148c",
                             font=("Consolas", 9, "bold"))

    # ── Napló segédfüggvények ──────────────────────────────────────────────────────
    def _write(self, text, tag=""):
        """Szöveget ír a napló mezőbe a megadott színcimkével (ok/warn/err/info/head)."""
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text, tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.update_idletasks()

    def _clear_log(self):
        """Napló tartalmát törli."""
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    # ── Tallózás ──────────────────────────────────────────────────────────────────
    def _browse_input(self):
        p = filedialog.askopenfilename(
            title="Forrás kép kiválasztása",
            filetypes=[
                ("Képfájlok", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif *.svg"),
                ("SVG vektoros kép", "*.svg"),
                ("Minden fájl", "*.*"),
            ])
        if p:
            self.v_input.set(p)
            if not self.v_output.get():
                self.v_output.set(str(Path(p).parent / "app_icons_kimenet"))

    def _browse_output(self):
        p = filedialog.askdirectory(title="Kimeneti mappa kiválasztása")
        if p:
            self.v_output.set(p)

    # ── Feldolgozás ───────────────────────────────────────────────────────────────
    def _process_one(self, img, kind, name, w, h, folder, mode_key, also_svg=False):
        """Egyetlen kimeneti kép előállítása és mentése PNG-be, opcionálisan SVG-be is.

        Args:
            img:      Pillow Image forráskep.
            kind:     'square' == négyzet ikon | bármi más == téglalap (feature/screenshot).
            name:     Fájlnév alap (felbontás és .png ext automatikusan hozzáadva).
            w, h:     Cél szélesség és magasság pixelben.
            folder:   Kimeneti mappa elérési útja.
            mode_key: Átméretezési mód kulcsszava ld. FEATURE_MODES.
            also_svg: Ha True, PNG mellé .svg fájl is készül (base64 PNG beágyazással).

        Returns:
            True ha sikeres, False hiba esetén (a hiba a naplóba kerül).
        """
        try:
            if kind == "square":
                out_img = resize_square(img, w)
            else:
                out_img = resize_feature(img, w, h, mode_key)

            no_a = name in APPLE_NO_ALPHA
            filename = f"{name}_{w}x{h}.png"
            out_path = os.path.join(folder, filename)
            _, sz = save_png(out_img, out_path, no_alpha=no_a)

            limit = LIMITS_BYTES.get(name)
            if limit and sz > limit:
                extra = f"  ⚠ LIMIT TÚLLÉPVE! ({sz // 1024} KB > {limit // (1024 * 1024)} MB)"
                self._write(f"  [!] {filename}  {sz / 1024:.1f} KB{extra}\n", "warn")
            else:
                self._write(f"  [OK] {filename}  {sz / 1024:.1f} KB\n", "ok")

            if also_svg:
                svg_filename = f"{name}_{w}x{h}.svg"
                svg_path = os.path.join(folder, svg_filename)
                try:
                    _, svg_sz = save_svg(out_img, svg_path, w, h)
                    self._write(f"  [OK] {svg_filename}  {svg_sz / 1024:.1f} KB\n", "ok")
                except Exception as svg_e:
                    self._write(f"  [HIBA] {svg_filename}: {svg_e}\n", "err")

            return True

        except Exception as e:
            self._write(f"  [HIBA] {name}_{w}x{h}: {e}\n", "err")
            return False

    def _generate(self):
        """Fő bejaratópont: érvényesíti a beviteli mezőket, majd elindítja
        a kiválasztott stóre-ok összes képének generálását."""
        src = self.v_input.get().strip()
        out = self.v_output.get().strip()

        if not src or not os.path.isfile(src):
            messagebox.showerror("Hiba", "Érvényes forrás képfájlt adjon meg!"); return
        if not out:
            messagebox.showerror("Hiba", "Adjon meg kimeneti mappát!"); return
        if not self.v_google.get() and not self.v_apple.get():
            messagebox.showerror("Hiba", "Válasszon legalább egy store-t!"); return

        try:
            img, is_svg = load_source_image(src)
        except Exception as e:
            messagebox.showerror("Képbetöltési hiba", str(e)); return

        self._clear_log()
        svg_note = "  [SVG → raszterizálva 2048 px]" if is_svg else ""
        self._write(f"Forrás :  {src}{svg_note}\n", "info")
        self._write(f"Meret  :  {img.size[0]}x{img.size[1]} px | Mod: {img.mode}\n", "info")
        self._write(f"Kimenet:  {out}\n\n", "info")

        # Kiemelési kép mód
        mode_key = next((v for lbl, v in FEATURE_MODES if lbl == self.v_mode.get()), "fill")

        do_screenshots = self.v_screenshots.get()

        # Összesített darabszám a progress barhoz
        total = 0
        if self.v_google.get():
            total += len(GOOGLE_PLAY_ICONS) + 1  # +1 feature graphic
            if do_screenshots:
                for _, items in GOOGLE_SCREENSHOTS:
                    total += len(items)
        if self.v_apple.get():
            total += len(APPLE_ICONS)
            if do_screenshots:
                for _, items in APPLE_SCREENSHOTS:
                    total += len(items)
        self.progress["maximum"] = total
        self.progress["value"]   = 0

        ok_count = 0
        done     = 0

        # ── Google Play Store – ikonok ─────────────────────────────────────────────
        if self.v_google.get():
            gdir = os.path.join(out, "google_play")
            os.makedirs(gdir, exist_ok=True)
            self._write("── Google Play Store – Ikonok ─────────────────────────────────────\n", "head")

            for name, w, h, _ in GOOGLE_PLAY_ICONS:
                ok_count += self._process_one(img, "square", name, w, h, gdir, mode_key, also_svg=True)
                done += 1
                self.progress["value"] = done

            nm, fw, fh, _ = GOOGLE_FEATURE
            ok_count += self._process_one(img, "feature", nm, fw, fh, gdir, mode_key)
            done += 1
            self.progress["value"] = done
            self._write("\n")

            # ── Google Play Store – képernyőképek ─────────────────────────────────
            if do_screenshots:
                self._write("── Google Play Store – Képernyőképek ──────────────────────────────\n", "head")
                for subfolder, items in GOOGLE_SCREENSHOTS:
                    sdir = os.path.join(gdir, "screenshots", subfolder)
                    os.makedirs(sdir, exist_ok=True)
                    self._write(f"  [{subfolder}]\n", "info")
                    for name, w, h, _ in items:
                        ok_count += self._process_one(img, "feature", name, w, h, sdir, mode_key)
                        done += 1
                        self.progress["value"] = done
                self._write("\n")

        # ── Apple App Store – ikonok ───────────────────────────────────────────────
        if self.v_apple.get():
            adir = os.path.join(out, "apple_store")
            os.makedirs(adir, exist_ok=True)
            self._write("── Apple App Store – Ikonok ───────────────────────────────────────\n", "head")

            for name, w, h, _ in APPLE_ICONS:
                ok_count += self._process_one(img, "square", name, w, h, adir, mode_key)
                done += 1
                self.progress["value"] = done
            self._write("\n")

            # ── Apple App Store – képernyőképek ───────────────────────────────────
            if do_screenshots:
                self._write("── Apple App Store – Képernyőképek ────────────────────────────────\n", "head")
                for subfolder, items in APPLE_SCREENSHOTS:
                    sdir = os.path.join(adir, "screenshots", subfolder)
                    os.makedirs(sdir, exist_ok=True)
                    self._write(f"  [{subfolder}]\n", "info")
                    for name, w, h, _ in items:
                        ok_count += self._process_one(img, "feature", name, w, h, sdir, mode_key)
                        done += 1
                        self.progress["value"] = done
                self._write("\n")

        # ── Összesítés ─────────────────────────────────────────────────────────────
        errors = total - ok_count
        if errors == 0:
            self._write(f"Kesz! {total} fajl sikeresen letrehozva.\n", "ok")
            self._write(f"Mappa: {out}\n", "info")
        else:
            self._write(f"Befejezve: {ok_count}/{total} sikeres, {errors} hiba.\n", "warn")


# ══════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AppIconResizer()
    app.mainloop()
