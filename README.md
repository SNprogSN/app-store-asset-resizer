# App Store Ikon Méretező

Egyetlen forrásképből automatikusan előállítja az összes szükséges képméretet **Google Play Store** és **Apple App Store** feltöltéshez.

---

## Mit generál?

### Google Play Store
| Fájl | Méret | Leírás |
|------|-------|--------|
| `play_store_icon_512` | 512×512 | Feltöltési ikon (max 1 MB) |
| `android_launcher_xxxhdpi` | 192×192 | Launcher ikon xxxhdpi |
| `android_launcher_xxhdpi` | 144×144 | Launcher ikon xxhdpi |
| `android_launcher_xhdpi` | 96×96 | Launcher ikon xhdpi |
| `android_launcher_hdpi` | 72×72 | Launcher ikon hdpi |
| `android_launcher_mdpi` | 48×48 | Launcher ikon mdpi |
| `play_store_feature_1024x500` | 1024×500 | Feature Graphic (max 15 MB) |
| Képernyőképek – telefon | 1080×1920 | Álló és fekvő |
| Képernyőképek – 7" tablet | 1200×1920 | Álló és fekvő |
| Képernyőképek – 10" tablet | 1600×2560 / 1200×1920 | BEST és MIN méret, álló és fekvő |

### Apple App Store
| Fájl | Méret | Leírás |
|------|-------|--------|
| `ios_AppStore_1024` | 1024×1024 | App Store feltöltési ikon (alpha nélkül) |
| `ios_iPhone_*` | 20–180 px | iPhone ikonok (összes skála) |
| `ios_iPad_*` | 20–167 px | iPad ikonok (összes skála) |
| Képernyőképek – iPhone 6.7" | 1290×2796 | Álló és fekvő |
| Képernyőképek – iPhone 6.5" | 1284×2778 | Álló és fekvő |
| Képernyőképek – iPhone 5.5" | 1242×2208 | Álló és fekvő |
| Képernyőképek – iPad Pro 12.9" | 2048×2732 | Álló és fekvő |
| Képernyőképek – iPad Pro 11" | 1668×2388 | Álló és fekvő |

---

## Rendszerkövetelmények

- **Windows 10 / 11** (a `start.bat` ehhez optimalizált)
- **Python 3.9 vagy újabb** – [python.org/downloads](https://www.python.org/downloads/)
  - Telepítéskor pipáld be: `[x] Add Python to PATH`
- Internet-kapcsolat az első indításhoz (csomagletöltés)

---

## Telepítés és indítás

### 1. lépés – Forrás letöltése

```
git clone https://github.com/SNprogSN/app-store-asset-resizer.git
cd app-store-asset-resizer
```

Vagy töltsd le ZIP-ként a GitHub oldalról, és csomagold ki.

### 2. lépés – Indítás

Kattints duplán a `start.bat` fájlra, vagy futtasd terminálból:

```
start.bat
```

### Mi történik az első indításkor?

1. **Python ellenőrzés** – Ha nincs telepítve, leírja hol tölthető le.
2. **`.venv` létrehozása** – Virtuális Python-környezet jön létre a projekt mappájában (~5–15 mp). Ez csak egyszer fut le.
3. **Aktiválás** – A `.venv` aktiválódik, a globális Python-telepítés érintetlen marad.
4. **Csomagok telepítése** – `Pillow`, `svglib`, `PyMuPDF` és egyéb függőségek letöltése a `requirements.txt` alapján.
5. **Alkalmazás indítása** – Megjelenik a grafikus felület.

**Második indítástól** a `.venv` és a csomagok már megvannak, az indítás szinte azonnali.

> **Miért kell a `.venv` Windows 11-en?**
> Az újabb Python verziók megtagadják a rendszer-szintű `pip install`-t engedély nélkül (PEP 668 – *externally managed environment*). A virtuális környezet ezt elkerüli, és a projekt csomagjait elkülöníti a globális Pythontól.

---

## SVG forrásképek

Az alkalmazás SVG vektoros képet is elfogad forrásként. Windows-on – ahol a `cairosvg` natív `libcairo-2.dll` függősége általában hiányzik – automatikusan `svglib` + `PyMuPDF` kombinációt használ, amely nem igényel semmilyen rendszerszintű telepítést.

---

## Saját projekt hozzáadása

Ha a forrásképeket és a generált kimeneteket **a projekt könyvtárán belül** tárolod (pl. egy almappában), vedd fel az adott mappát a `.gitignore`-ba, hogy ne kerüljenek be a verziókezelőbe:

```
# .gitignore
MoziApp/
WebshopApp/
```

Így a képek csak a gépeden lesznek, a git-be nem kerülnek be. Példa struktúra:

```
app-store-asset-resizer/
  start.bat
  icon_resizer.py
  requirements.txt
  .gitignore          <- ide vedd fel az almappádat!
  MoziApp/            <- forrásképek + generált kimenetek (NEM git-ben)
    Eredeti/
      logo.png
    app_icons_kimenet/
      google_play/
      apple_store/
```

---

## Kiemelési kép / Screenshot módok

| Mód | Leírás |
|-----|--------|
| **Vágás – középre igazítva (fill)** | Teljes területet kitölti, széleit levágja |
| **Keret – fehér háttér (fit)** | Belefér, a maradék terület fehér |
| **Keret – fekete háttér (fit)** | Belefér, a maradék terület fekete |
| **Elmosott háttér (blur + overlay)** | Elmosott kitöltő háttér, éles előtér középen |

---

## Függőségek

| Csomag | Mire való |
|--------|-----------|
| `Pillow` | Képbetöltés, átméretezés, PNG mentés |
| `svglib` | SVG → PDF konverzió (Windows fallback) |
| `PyMuPDF` | PDF → PNG raszterizálás (Windows fallback, beépített MuPDF) |
| `cairosvg` | SVG raszterizálás (Linux/macOS, vagy ha `libcairo-2.dll` elérhető) |

---

## Licenc

MIT
