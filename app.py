import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import urllib.request
import urllib.parse
import os
import re
import tempfile
import math
import html
import hashlib
from datetime import datetime

ARCH_ITINERARIO = "itinerario_actual.json"
ARCH_CONFIG     = "config_viaje.json"

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA & ESTILO NAVIDEÑO EDITORIAL (MÓVIL + WEB COMPACTO)
# =============================================================================
st.set_page_config(
    page_title="Navidad en Nueva York 🎄❄️",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

  :root {
    color-scheme: light !important;
  }

  * {
    box-sizing: border-box;
  }

  html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, button, select, textarea,
  .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stText"], .stCaption, small {
    font-family: 'Calibri', 'Carlito', 'Segoe UI', Candara, -apple-system, BlinkMacSystemFont, Arial, sans-serif !important;
    color: #0F172A !important;
  }

  [data-testid="stIconMaterial"],
  [data-testid="stIconEmoji"],
  [data-testid*="Icon"],
  [data-testid*="icon"],
  [data-testid*="Chevron"],
  [data-testid="stExpanderToggleIcon"],
  [data-testid="stExpanderStepChevron"],
  [data-testid="stExpanderStepIcon"],
  .material-icons,
  [class*="material-symbols"],
  [data-baseweb="icon"],
  span.e1vmumty0 {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 20px !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
    color: #0F172A !important;
  }

  [data-testid="stExpander"] {
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
    overflow: hidden !important;
  }
  [data-testid="stExpander"] details summary {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 10px 14px !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 0.94rem !important;
    cursor: pointer !important;
    list-style: none !important;
  }
  [data-testid="stExpander"] details summary::-webkit-details-marker {
    display: none !important;
  }
  [data-testid="stExpander"] details summary > span,
  [data-testid="stExpander"] details summary > div {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    position: static !important;
    transform: none !important;
    margin: 0 !important;
  }
  [data-testid="stExpander"] details summary [data-testid="stIconMaterial"] {
    flex-shrink: 0 !important;
    width: 22px !important;
    height: 22px !important;
    margin-right: 4px !important;
  }

  .stApp, html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #F8F9FA !important;
    color: #0F172A !important;
  }
  .block-container {
    padding-top: 1rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1180px !important;
  }

  .hero-container {
    background: #FFFFFF !important;
    border-radius: 18px;
    padding: 16px 20px;
    color: #0F172A !important;
    margin-bottom: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    border: 1.5px solid #CBD5E1;
    border-top: 5px solid #15803D;
  }
  .hero-eyebrow {
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    color: #15803D !important;
  }
  .hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 4px 0 8px 0;
    color: #0F172A !important;
    letter-spacing: -0.5px;
    line-height: 1.15;
  }
  .hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 30px;
    padding: 4px 11px;
    font-size: 0.82rem;
    color: #0F172A !important;
    font-weight: 700;
    margin-right: 5px;
    margin-bottom: 4px;
    max-width: 100%;
    word-break: break-word;
  }
  .hero-stat-box {
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 12px;
    padding: 7px 12px;
    text-align: center;
    min-width: 72px;
    flex: 1 1 auto;
  }
  .hero-stat-val {
    font-size: 1.4rem;
    font-weight: 900;
    color: #0F172A !important;
  }
  .hero-stat-lbl {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #0F172A !important;
  }

  .ny-card {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 16px;
    padding: 15px 17px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    color: #0F172A !important;
  }
  .ny-card-header {
    font-size: 0.82rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    color: #0F172A !important;
    margin-bottom: 8px;
  }

  .place-sheet {
    background: #FFFFFF !important;
    border: 2px solid #CBD5E1 !important;
    border-radius: 16px;
    padding: 13px 15px;
    margin: 10px 0;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
    color: #0F172A !important;
  }

  .place-note {
    font-size: 0.76rem !important;
    font-weight: 400 !important;
    font-style: italic !important;
    color: #475569 !important;
    line-height: 1.3 !important;
    margin-top: 2px !important;
    padding-left: 2px !important;
    word-break: break-word !important;
    overflow-wrap: anywhere !important;
    white-space: pre-wrap !important;
  }

  .place-note a {
    color: #1D4ED8 !important;
    text-decoration: underline !important;
    font-size: inherit !important;
    font-weight: 400 !important;
  }

  .badge-cat {
    display: inline-block;
    background: #F1F5F9 !important;
    color: #0F172A !important;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 1px 7px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
  }
  .badge-hora {
    display: inline-block;
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    font-size: 0.74rem;
    font-weight: 900;
    padding: 1px 7px;
    border-radius: 6px;
    border: 1px solid #93C5FD;
  }
  .badge-indoor {
    display: inline-block;
    background: #EFF6FF !important;
    color: #1E3A8A !important;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 1px 7px;
    border-radius: 6px;
    border: 1px solid #BFDBFE;
  }
  .badge-outdoor {
    display: inline-block;
    background: #ECFDF5 !important;
    color: #064E3B !important;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 1px 7px;
    border-radius: 6px;
    border: 1px solid #A7F3D0;
  }
  .badge-dia {
    display: inline-block;
    background: #FEF3C7 !important;
    color: #78350F !important;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 1px 7px;
    border-radius: 6px;
    border: 1px solid #FDE68A;
  }

  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #E2E8F0 !important;
    padding: 4px;
    border-radius: 14px;
    border: 1px solid #CBD5E1;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-size: 0.86rem !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    padding: 6px 11px !important;
    border: none !important;
    background: transparent !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
  }
  .stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
  }

  .stButton > button, .stFormSubmitButton > button, [data-testid="stLinkButton"] > a {
    border-radius: 9px !important;
    font-weight: 800 !important;
    font-size: 0.82rem !important;
    min-height: 32px !important;
    height: 32px !important;
    padding: 0 0.55rem !important;
    border: 1.5px solid #94A3B8 !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: all 0.15s ease-in-out !important;
  }
  .stButton > button:hover, .stFormSubmitButton > button:hover, [data-testid="stLinkButton"] > a:hover {
    background: #F1F5F9 !important;
    border-color: #0F172A !important;
    color: #0F172A !important;
  }

  .edit-mini-btn {
    display: flex !important;
    justify-content: flex-end !important;
  }
  .edit-mini-btn button {
    min-height: 34px !important;
    height: 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    max-width: 34px !important;
    padding: 0 !important;
    font-size: 1.05rem !important;
    line-height: 1.1 !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
    border-radius: 7px !important;
    border: 1px solid #CBD5E1 !important;
    background: #F8FAFC !important;
    color: #334155 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
  }
  .edit-mini-btn button:hover {
    background: #E2E8F0 !important;
    border-color: #64748B !important;
  }

  .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
    border-radius: 9px !important;
    border: 1.5px solid #94A3B8 !important;
    background: #FFFFFF !important;
    font-size: 0.85rem !important;
    color: #0F172A !important;
    min-height: 34px !important;
  }
  [data-baseweb="select"] span, [data-baseweb="select"] div {
    color: #0F172A !important;
    font-weight: 700 !important;
  }
  ul[role="listbox"], ul[role="listbox"] li {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
  }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. DEFINICIÓN DEL VIAJE NAVIDEÑO (26 DIC 2026 - 4 ENE 2027)
# =============================================================================
DIAS_VIAJE = {
    1:  {"fecha": "26 Diciembre", "dia": "Sábado"},
    2:  {"fecha": "27 Diciembre", "dia": "Domingo"},
    3:  {"fecha": "28 Diciembre", "dia": "Lunes"},
    4:  {"fecha": "29 Diciembre", "dia": "Martes"},
    5:  {"fecha": "30 Diciembre", "dia": "Miércoles"},
    6:  {"fecha": "31 Diciembre", "dia": "Jueves"},
    7:  {"fecha": "01 Enero", "dia": "Viernes"},
    8:  {"fecha": "02 Enero", "dia": "Sábado"},
    9:  {"fecha": "03 Enero", "dia": "Domingo"},
    10: {"fecha": "04 Enero", "dia": "Lunes"},
}

def etiqueta_dia(d: int) -> str:
    info = DIAS_VIAJE.get(d, {})
    return f"Día {d}: {info.get('fecha', '')} - {info.get('dia', '')}".strip()

def etiqueta_dia_corta(d: int) -> str:
    info = DIAS_VIAJE.get(d, {})
    return f"Día {d} · {info.get('fecha', '')}".strip()


def linkificar_nota(nota: str) -> str:
    texto = (nota or "").strip()
    if not texto:
        return ""

    patron_url = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
    partes = []
    cursor = 0

    for coincidencia in patron_url.finditer(texto):
        partes.append(html.escape(texto[cursor:coincidencia.start()]).replace("\n", "<br>"))

        url_original = coincidencia.group(0)
        url = url_original.rstrip(".,;:!?)]}")
        puntuacion_final = url_original[len(url):]
        if url:
            destino = url if url.lower().startswith(("http://", "https://")) else f"https://{url}"
            partes.append(
                f'<a href="{html.escape(destino, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer" style="color:#1D4ED8; text-decoration:underline; '
                f'overflow-wrap:anywhere;">{html.escape(url)}</a>'
            )
        partes.append(html.escape(puntuacion_final))
        cursor = coincidencia.end()

    partes.append(html.escape(texto[cursor:]).replace("\n", "<br>"))
    return "".join(partes)


def bloque_nota_html(nota: str) -> str:
    contenido = linkificar_nota(nota)
    return f'<div class="place-note">📝 {contenido}</div>' if contenido else ""


# =============================================================================
# 3. MOTOR INTELIGENTE DE CATEGORÍAS
# =============================================================================
CATEGORIAS_CANONICAS = [
    "🍕 Gastronomía",
    "🍪 Dulces",
    "🍸 Copas",
    "🎷 Ocio",
    "🛍️ Compras",
    "🏛️ Cultura",
    "🏙️ Miradores",
    "🌲 Parques",
    "🏨 Hotel",
    "📍 Otros"
]

MAPA_MIGRACION_CAT = {
    "🍕 Gastronomía & Restaurantes": "🍕 Gastronomía",
    "🍪 Cafeterías & Dulces": "🍪 Dulces",
    "🍸 Rooftops & Copas": "🍸 Copas",
    "🎷 Jazz, Música & Ocio": "🎷 Ocio",
    "🛍️ Compras & Outlets": "🛍️ Compras",
    "🏛️ Museos & Monumentos": "🏛️ Cultura",
    "🏙️ Miradores & Observatorios": "🏙️ Miradores",
    "🌲 Parques, Muelles & Puentes": "🌲 Parques",
    "🏨 Hotel Base": "🏨 Hotel",
    "📍 Otros Lugares": "📍 Otros"
}

def normalizar_categoria(cat: str) -> str:
    if not cat:
        return "📍 Otros"
    if cat in CATEGORIAS_CANONICAS:
        return cat
    if cat in MAPA_MIGRACION_CAT:
        return MAPA_MIGRACION_CAT[cat]
    for c in CATEGORIAS_CANONICAS:
        if c.split()[-1].lower() in cat.lower():
            return c
    return "📍 Otros"

def clasificar_lugar(nombre: str, direccion: str = "", lista_origen: str = "") -> tuple[str, str]:
    nom = (nombre or "").strip().lower()
    orig = (lista_origen or "").strip().lower()

    if ('hotel' in nom or 'inn' in nom or 'alojamiento' in nom) and any(k in nom for k in ['riu', 'marriott', 'hilton', 'hyatt', 'sheraton', 'base']):
        return "🏨 Hotel", "Interior"

    if any(k in nom for k in ['summit', 'one vanderbilt', 'empire state', 'top of the rock', 'the edge', 'observatory', 'one world observatory']):
        return "🏙️ Miradores", "Interior"

    if any(k in nom for k in ['jazz', 'blue note', 'smalls', 'mezzrow', 'dizzy', "arthur's tavern", 'jazzcultural', 'village vanguard', 'broadway show', 'radio city', 'comedy cellar', 'lincoln center', 'teatro', 'theatre']):
        return "🎷 Ocio", "Interior"

    if any(k in nom for k in ['rooftop', 'westlight', 'harriet', 'magic hour', '230 fifth', 'bar 54', 'hudson vu', 'buvette', 'dante', 'speakeasy', 'cocktail', 'wine bar', 'tavern', 'brewery', 'pub']) or ('bar' in nom.split() and 'shake' not in nom and 'salad' not in nom) or 'm social' in nom:
        return "🍸 Copas", "Interior"

    if any(k in nom for k in ['bakery', 'cookie', 'cookies', 'levain', 'granny', 'caffè panna', 'caffe panna', 'krispy kreme', 'sweets', 'sweet', 'pastry', 'pâtisserie', 'donut', 'helado', 'ice cream', 'louis vuitton nyc', 'café', 'cafe', 'coffee', 'starbucks', 'magnolia', 'chocolate']):
        return "🍪 Dulces", "Interior"

    if any(k in nom for k in ['outlet', 'outlets', 'marshalls', 't.j. maxx', 'tj maxx', 'target', 'macy', 'burlington', 'century 21', 'five below', 'goodwill', 'woodbury', 'jersey gardens', 'grand slam', 'shopping', 'store', 'zara', 'uniqlo', 'tanger', 'apple store', 'sephora', 'nordstrom', 'bloomingdale']):
        return "🛍️ Compras", "Interior"

    if any(k in nom for k in ['pizza', 'pizzeria', 'burger', 'katz', 'dumpling', 'motek', 'piada', 'shake shack', 'chelsea market', 'time out market', 'deli', 'pastrami', 'tacos', 'taco', 'restaurant', 'trader joe', 'eataly', 'food hall', 'bagel', 'ramen', 'sushi', 'diner', 'smokehouse', 'noodle', 'food']):
        return "🍕 Gastronomía", "Interior"

    if any(k in nom for k in ['park', 'central park', 'bridge', 'puente', 'high line', 'little island', 'fulton ferry', 'domino', 'pier 17', 'pier 57', 'pier 35', 'pebble beach', 'tudor city', 'squibb', 'battery', 'waterfront', 'picnic', 'botanic', 'coney island', 'boardwalk']):
        return "🌲 Parques", "Exterior"

    if any(k in nom for k in ['museum', 'the met', 'moma', 'morgan library', 'tenement', '9/11 memorial', 'oculus', 'grand central', 'library', 'atlas', 'one times square', 'times square', 'memorial', 'statue of liberty', 'trinity church', 'rockefeller center', 'st. patrick']):
        tipo = "Exterior" if any(x in nom for x in ['times square', 'atlas', 'statue']) else "Interior"
        return "🏛️ Cultura", tipo

    if 'sweet' in orig:
        return "🍪 Dulces", "Interior"
    if 'food' in orig:
        return "🍕 Gastronomía", "Interior"
    if 'rooftop' in orig:
        return "🍸 Copas", "Interior"
    if 'tienda' in orig or 'outlet' in orig:
        return "🛍️ Compras", "Interior"
    if 'spot' in orig:
        return "🌲 Parques", "Exterior"

    return "📍 Otros", "Interior"

def selectbox_sin_teclado(*args, **kwargs):
    kwargs.setdefault("filter_mode", None)
    try:
        return st.selectbox(*args, **kwargs)
    except TypeError as exc:
        if "filter_mode" not in str(exc):
            raise
        kwargs.pop("filter_mode", None)
        return st.selectbox(*args, **kwargs)


def obtener_emoji_categoria(cat: str) -> str:
    for ch in cat:
        if ord(ch) > 127:
            return ch
    return "📍"

def crear_pin_google_maps(categoria: str, nombre: str = ""):
    emoji = obtener_emoji_categoria(categoria)
    html_pin = f"""
    <div style="
        width: 34px; height: 34px;
        background: #ffffff;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.25), 0 0 0 1px rgba(0,0,0,0.08);
        font-size: 18px;
        cursor: pointer;
        user-select: none;
    ">{emoji}</div>
    """
    return folium.DivIcon(html=html_pin, icon_size=(34, 34), icon_anchor=(17, 17), popup_anchor=(0, -17))

def ordenar_por_hora(lista_sitios: list) -> list:
    def clave_orden(item):
        h = (item.get("hora") or "").strip()
        if re.match(r"^\d{1,2}:\d{2}$", h):
            partes = h.split(":")
            return (0, int(partes[0]) * 60 + int(partes[1]), item.get("id", 0))
        return (1, 9999, item.get("id", 0))
    return sorted(lista_sitios, key=clave_orden)


# =============================================================================
# 4. APIs EXTERNAS CON CACHÉ DE RENDIMIENTO OPTIMIZADO
# =============================================================================
@st.cache_data(ttl=86400)
def obtener_tasa_usd_eur():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tasa = float(data.get("rates", {}).get("EUR", 0.91))
            fecha_upd = data.get("time_last_update_utc", "Hoy")[:16]
            return tasa, fecha_upd
    except Exception:
        return 0.91, "Estimada"

@st.cache_data(ttl=1800)
def consultar_clima_nyc():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=40.7128&longitude=-74.0060&"
            "current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&"
            "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&"
            "timezone=America%2FNew_York"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None

def traducir_codigo_clima(code: int) -> tuple[str, str]:
    if code in [0]:
        return "☀️ Despejado", "soleado"
    elif code in [1, 2]:
        return "🌤️ Parcialmente nublado", "nublado"
    elif code in [3]:
        return "☁️ Nublado", "nublado"
    elif code in [45, 48]:
        return "🌫️ Niebla invernal", "frio"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️ Lluvia", "lluvia"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "🌨️ Nieve / Aguanieve", "nieve"
    elif code in [95, 96, 99]:
        return "⛈️ Tormenta", "tormenta"
    return "⛅ Tiempo variable", "variable"


# =============================================================================
# 5. CARGA Y GESTIÓN DE DATOS DEL VIAJE
# =============================================================================
@st.cache_data
def cargar_config_viaje():
    if os.path.exists(ARCH_CONFIG):
        try:
            with open(ARCH_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "vuelo_ida": {"aerolinea": "Aer Lingus", "fecha": "26 Dic", "hora": "15:30", "vuelo": "Aer Lingus · EI583, EI107", "aeropuerto": "JFK / Nueva York"},
        "vuelo_vuelta": {"aerolinea": "Aer Lingus", "fecha": "4 Ene", "hora": "20:45", "vuelo": "Aer Lingus · EI104, EI582", "aeropuerto": "JFK / Nueva York"},
        "hotel": {
            "nombre": "Courtyard by Marriott New York Manhattan Upper East Side",
            "direccion": "410 E 92nd St, New York, NY 10128",
            "lat": 40.780242, "lon": -73.946123
        },
        "listas_gmaps": []
    }

def _guardar_json_atomico(ruta: str, datos):
    temporal = None
    try:
        carpeta = os.path.dirname(os.path.abspath(ruta))
        prefijo = f".{os.path.basename(ruta)}."
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=carpeta,
            prefix=prefijo, suffix=".tmp", delete=False
        ) as f:
            temporal = f.name
            json.dump(datos, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, ruta)
        return True
    except Exception:
        try:
            if temporal and os.path.exists(temporal):
                os.remove(temporal)
        except Exception:
            pass
        return False


def guardar_config_viaje(cfg):
    cargar_config_viaje.clear()
    return _guardar_json_atomico(ARCH_CONFIG, cfg)

def cargar_itinerario_disco():
    if os.path.exists(ARCH_ITINERARIO):
        try:
            with open(ARCH_ITINERARIO, "r", encoding="utf-8") as f:
                datos = json.load(f)
                modificado = False
                for p in datos:
                    cat_norm = normalizar_categoria(p.get("categoria", ""))
                    if p.get("categoria") != cat_norm:
                        p["categoria"] = cat_norm
                        modificado = True
                    if "hora" not in p:
                        p["hora"] = ""
                        modificado = True
                    if "nota" not in p:
                        p["nota"] = ""
                        modificado = True
                if modificado:
                    guardar_itinerario_disco(datos)
                return datos
        except Exception:
            pass
    return []

def guardar_itinerario_disco(lugares):
    return _guardar_json_atomico(ARCH_ITINERARIO, lugares)


def _huella_datos(datos) -> str:
    try:
        return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        return repr(datos)


def sincronizar_config_desde_disco():
    nueva_config = cargar_config_viaje()
    config_actual = st.session_state.get("config_viaje")
    if config_actual is None or _huella_datos(config_actual) != _huella_datos(nueva_config):
        st.session_state.config_viaje = nueva_config
        st.session_state.lista_gmaps_editando = None
        return True
    return False


def sincronizar_lugares_desde_disco():
    nuevos = cargar_itinerario_disco()
    anteriores = st.session_state.get("lugares")
    if anteriores is None:
        st.session_state.lugares = nuevos
        return True

    if _huella_datos(anteriores) == _huella_datos(nuevos):
        return False

    st.session_state.lugares = nuevos
    return True


# =============================================================================
# 6. SINCRONIZADOR DE LISTAS Y GEOCODIFICACIÓN (CACHEADOS)
# =============================================================================
@st.cache_data(ttl=86400)
def geocodificar_direccion_o_nombre(texto: str) -> tuple:
    if not texto:
        return None, None, ""
    q = f"{texto}, New York, NY".strip()
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'ny_holiday_planner_app_v5'})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            res = json.loads(r.read().decode('utf-8'))
            if res and len(res) > 0:
                lat = float(res[0]['lat'])
                lon = float(res[0]['lon'])
                nombre_comp = res[0].get('display_name', '')
                return lat, lon, nombre_comp
    except Exception:
        pass
    return None, None, ""

@st.cache_data(ttl=3600)
def extraer_lugares_lista_gmaps(url_lista: str, nombre_lista: str = ""):
    import http.cookiejar

    lugares_encontrados = []
    url_limpia = (url_lista or "").strip()
    if not url_limpia:
        return lugares_encontrados

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'es-ES,es;q=0.9,en;q=0.8'),
        ('Cookie', 'CONSENT=YES+cb.20230531-07-p0.es+FX+999; SOCS=CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVzIAEaBgiA_LyaBg')
    ]

    try:
        with opener.open(url_limpia, timeout=5) as r:
            url_final = r.geturl()
            html_content = r.read().decode('utf-8', errors='ignore')

        patrones_endpoint = [
            r'href="(/maps/preview/entitylist/getlist\?[^"]+)"',
            r'((?:https://www\.google\.com)?/maps/preview/entitylist/getlist\?[^"\'\\<>]+)',
            r'(\\/maps\\/preview\\/entitylist\\/getlist\?[^"\'<>]+)'
        ]

        entity_path = None
        for pat in patrones_endpoint:
            m = re.search(pat, html_content)
            if m:
                entity_path = m.group(1)
                break

        if not entity_path:
            m_place = re.search(r'/place/([^/@?]+)', url_final)
            if m_place:
                nom_lugar = urllib.parse.unquote_plus(m_place.group(1)).replace("+", " ").strip()
                m_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url_final)
                if nom_lugar:
                    lat_p = float(m_coords.group(1)) if m_coords else None
                    lon_p = float(m_coords.group(2)) if m_coords else None
                    if lat_p is None or lon_p is None:
                        lat_p, lon_p, dir_p = geocodificar_direccion_o_nombre(f"{nom_lugar}, New York")
                    else:
                        dir_p = ""
                    cat, tipo = clasificar_lugar(nom_lugar, dir_p, nombre_lista)
                    lugares_encontrados.append({
                        "nombre": nom_lugar,
                        "lat": lat_p if lat_p is not None else 40.7580,
                        "lon": lon_p if lon_p is not None else -73.9855,
                        "direccion": dir_p,
                        "nota": "",
                        "categoria": cat,
                        "tipo": tipo,
                        "hora": ""
                    })
            return lugares_encontrados

        entity_path = (
            html.unescape(entity_path)
            .replace("\\u0026", "&")
            .replace("\\u003d", "=")
            .replace("\\/", "/")
        )

        if entity_path.startswith("http"):
            entity_url = entity_path
        else:
            entity_url = "https://www.google.com" + (entity_path if entity_path.startswith("/") else "/" + entity_path)

        with opener.open(entity_url, timeout=5) as r2:
            raw = r2.read().decode("utf-8", errors="ignore")

        raw_limpio = re.sub(r"^\)\]\}'\s*", "", raw)
        data = json.loads(raw_limpio)

        def _buscar_entidades(nodo):
            if isinstance(nodo, list):
                coords = None
                for el in nodo:
                    if (isinstance(el, list) and len(el) >= 4 and el[0] is None and el[1] is None
                            and isinstance(el[2], (int, float)) and isinstance(el[3], (int, float))):
                        coords = (float(el[2]), float(el[3]))
                        break
                if coords:
                    strs = [
                        s.strip() for s in nodo
                        if isinstance(s, str) and len(s.strip()) > 1
                        and not s.startswith(("http", "ChIJ", "/g/", "/m/", "0x"))
                    ]
                    if strs:
                        nombre_raw = strs[0]
                        partes = nombre_raw.split(",")
                        nom_spot = partes[0].strip()
                        dir_spot = ", ".join(partes[1:]).strip() if len(partes) > 1 else (strs[1] if len(strs) > 1 else "")
                        cat, tipo = clasificar_lugar(nom_spot, dir_spot, nombre_lista)
                        lugares_encontrados.append({
                            "nombre": nom_spot,
                            "lat": coords[0],
                            "lon": coords[1],
                            "direccion": dir_spot,
                            "nota": "",
                            "categoria": cat,
                            "tipo": tipo,
                            "hora": ""
                        })
                    return
                for hijo in nodo:
                    _buscar_entidades(hijo)
            elif isinstance(nodo, dict):
                for v in nodo.values():
                    _buscar_entidades(v)

        _buscar_entidades(data)

    except Exception:
        pass

    return lugares_encontrados


# =============================================================================
# 6B. HERRAMIENTAS PARA AÑADIR Y EDITAR LUGARES
# =============================================================================
def agregar_sitio_a_lugares(nombre: str, direccion: str = "", lat: float = None, lon: float = None,
                            categoria: str = None, tipo: str = None, dia_dest: int = 0, hora: str = "", nota: str = "") -> tuple:
    nom = (nombre or "").strip()
    if not nom:
        return False, "El nombre del lugar no puede estar vacío."

    if lat is None or lon is None or (lat == 0 and lon == 0):
        geo_lat, geo_lon, geo_dir = geocodificar_direccion_o_nombre(f"{nom} {direccion}")
        lat = geo_lat if geo_lat is not None else 40.7580
        lon = geo_lon if geo_lon is not None else -73.9855
        if not direccion and geo_dir:
            direccion = geo_dir

    if not categoria or categoria == "⚡ Detección Automática":
        cat_auto, tipo_auto = clasificar_lugar(nom, direccion)
        categoria = cat_auto
        if not tipo:
            tipo = tipo_auto

    if not tipo:
        tipo = "Interior"

    max_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0) + 1
    nuevo = {
        "id": max_id,
        "nombre": nom,
        "lat": float(lat),
        "lon": float(lon),
        "dia": dia_dest,
        "hora": (hora or "").strip(),
        "direccion": direccion,
        "nota": (nota or "").strip(),
        "categoria": normalizar_categoria(categoria),
        "tipo": tipo,
        "visitado": False
    }
    st.session_state.lugares.append(nuevo)
    guardar_itinerario_disco(st.session_state.lugares)
    return True, f"¡'{nom}' añadido con éxito como {nuevo['categoria']}!"

def importar_sitio_desde_gmaps(url_o_texto: str, dia_dest: int = 0, hora: str = "", nota: str = "") -> tuple:
    raw = url_o_texto.strip()
    if not raw:
        return False, "Introduce un enlace de Google Maps válido."

    if "maps" in raw and ("entitylist" in raw or "data=" in raw or "u3WSz" in raw or "gHBnh" in raw):
        lugares_lst = extraer_lugares_lista_gmaps(raw, "Google Maps")
        if lugares_lst:
            existentes = set(x.get("nombre", "").lower() for x in st.session_state.lugares)
            nuevos = 0
            max_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
            for s in lugares_lst:
                if s["nombre"].lower() not in existentes:
                    max_id += 1
                    s["id"] = max_id
                    s["dia"] = dia_dest
                    s["hora"] = (hora or "").strip()
                    s["nota"] = (nota or "").strip()
                    s["visitado"] = False
                    st.session_state.lugares.append(s)
                    nuevos += 1
            if nuevos > 0:
                guardar_itinerario_disco(st.session_state.lugares)
                return True, f"¡Se importaron {nuevos} lugares desde la lista de Google Maps!"

    nombre_extraido = ""
    lat_ext, lon_ext = None, None
    dir_ext = ""

    if raw.startswith("http://") or raw.startswith("https://"):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            req = urllib.request.Request(raw, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as r:
                url_final = r.geturl()
                html = r.read().decode('utf-8', errors='ignore')

                m_coords = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url_final)
                if m_coords:
                    lat_ext = float(m_coords.group(1))
                    lon_ext = float(m_coords.group(2))

                m_nom = re.search(r"/place/([^/@?]+)", url_final)
                if m_nom:
                    nombre_extraido = urllib.parse.unquote_plus(m_nom.group(1)).replace("+", " ")
        except Exception:
            pass

    if not nombre_extraido:
        nombre_extraido = raw.split("/")[-1].replace("+", " ")

    return agregar_sitio_a_lugares(nombre_extraido, dir_ext, lat_ext, lon_ext, None, None, dia_dest, hora, nota)

def render_editor_sitio_panel(spot: dict, idx_real: int, key_ctx: str):
    edit_key = f"{key_ctx}_{spot['id']}"
    if st.session_state.get("editando_spot_key") != edit_key:
        return

    with st.container():
        st.markdown(
            f"<div style='background:#F8FAFC; border:1.5px solid #94A3B8; border-radius:12px; padding:9px 11px; margin:6px 0 8px 0;'>"
            f"<b>✏️ Editando: {spot['nombre']}</b></div>",
            unsafe_allow_html=True
        )
        with st.form(f"form_edit_spot_{edit_key}"):
            ce1, ce2 = st.columns(2)
            with ce1:
                ed_nom = st.text_input("Nombre del lugar:", value=spot.get("nombre", ""))
                ed_dir = st.text_input("Dirección / Barrio:", value=spot.get("direccion", ""))
                ed_nota = st.text_input(
                    "Nota manual:",
                    value=spot.get("nota", ""),
                    placeholder="Ej: Pedir galleta..."
                )
            with ce2:
                ed_hora = st.text_input("Hora (HH:MM):", value=spot.get("hora", ""), placeholder="HH:MM")
                cat_act = normalizar_categoria(spot.get("categoria", "📍 Otros"))
                idx_c = CATEGORIAS_CANONICAS.index(cat_act) if cat_act in CATEGORIAS_CANONICAS else 0
                ed_cat = selectbox_sin_teclado("Categoría:", CATEGORIAS_CANONICAS, index=idx_c)

                tipo_act = spot.get("tipo", "Interior")
                ed_tipo = selectbox_sin_teclado("Entorno:", ["Interior", "Exterior"], index=0 if tipo_act == "Interior" else 1)

                dias_opts = ["📌 Bandeja de Guardados"] + [etiqueta_dia(d) for d in range(1, 11)]
                dia_act = spot.get("dia", 0)
                ed_dia_str = selectbox_sin_teclado("Día asignado:", dias_opts, index=dia_act if 0 <= dia_act <= 10 else 0)

            ce3, ce4 = st.columns(2)
            with ce3:
                ed_lat = st.number_input("Latitud:", value=float(spot.get("lat", 40.7580)), format="%.6f")
            with ce4:
                ed_lon = st.number_input("Longitud:", value=float(spot.get("lon", -73.9855)), format="%.6f")

            cb1, cb2, cb3 = st.columns([2, 1.2, 1])
            with cb1:
                guardar_ed = st.form_submit_button("💾 Guardar", use_container_width=True)
            with cb2:
                eliminar_ed = st.form_submit_button("🗑️ Borrar", use_container_width=True)
            with cb3:
                cerrar_ed = st.form_submit_button("✕ Cerrar", use_container_width=True)

            if guardar_ed:
                hora_limpia = ed_hora.strip()
                if hora_limpia and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hora_limpia):
                    st.error("Formato de hora inválido. Usa HH:MM.")
                else:
                    if hora_limpia and len(hora_limpia) == 4:
                        hora_limpia = "0" + hora_limpia
                    nuevo_dia = 0 if "Bandeja" in ed_dia_str else int(re.search(r"Día (\d+)", ed_dia_str).group(1))
                    st.session_state.lugares[idx_real].update({
                        "nombre": ed_nom.strip() or spot["nombre"],
                        "direccion": ed_dir.strip(),
                        "nota": ed_nota.strip(),
                        "hora": hora_limpia,
                        "categoria": ed_cat,
                        "tipo": ed_tipo,
                        "dia": nuevo_dia,
                        "lat": float(ed_lat),
                        "lon": float(ed_lon)
                    })
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.session_state.editando_spot_key = None
                    st.rerun()

            if eliminar_ed:
                st.session_state.lugares.pop(idx_real)
                if st.session_state.lugar_activo_id == spot["id"]:
                    st.session_state.lugar_activo_id = None
                st.session_state.editando_spot_key = None
                guardar_itinerario_disco(st.session_state.lugares)
                st.rerun()

            if cerrar_ed:
                st.session_state.editando_spot_key = None
                st.rerun()

def render_formulario_agregar_lugar(key_sufijo: str = "gen"):
    with st.expander("➕ Añadir Nuevo Lugar (Google Maps o a Mano)", expanded=False):
        tab_gm, tab_man = st.tabs(["🌐 Google Maps", "✏️ A Mano"])
        dias_asig_opts = ["📌 Bandeja de Guardados"] + [etiqueta_dia(d) for d in range(1, 11)]

        with tab_gm:
            with st.form(f"form_add_gm_{key_sufijo}"):
                url_input = st.text_input("Enlace de Google Maps:", placeholder="https://maps.app.goo.gl/...", key=f"inp_gm_{key_sufijo}")
                cg1, cg2 = st.columns(2)
                with cg1:
                    dia_dest_gm = selectbox_sin_teclado("Asignar a:", dias_asig_opts, key=f"sel_dia_gm_{key_sufijo}")
                with cg2:
                    hora_gm = st.text_input("Hora (opcional, HH:MM):", placeholder="11:00", key=f"hora_gm_{key_sufijo}")
                nota_gm = st.text_input("Nota manual (opcional):", key=f"nota_gm_{key_sufijo}")

                val_dia_gm = 0 if "Bandeja" in dia_dest_gm else int(re.search(r"Día (\d+)", dia_dest_gm).group(1))

                if st.form_submit_button("📥 Importar", use_container_width=True):
                    if url_input:
                        ok, msg = importar_sitio_desde_gmaps(url_input, val_dia_gm, hora_gm.strip(), nota_gm)
                        if ok:
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_man:
            with st.form(f"form_add_man_{key_sufijo}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    nom_m = st.text_input("Nombre:", key=f"nom_m_{key_sufijo}")
                    dir_m = st.text_input("Dirección / Barrio:", key=f"dir_m_{key_sufijo}")
                with c_m2:
                    cat_m = selectbox_sin_teclado("Categoría:", ["⚡ Detección Automática"] + CATEGORIAS_CANONICAS, key=f"cat_m_{key_sufijo}")
                    tipo_m = selectbox_sin_teclado("Tipo:", ["Interior", "Exterior"], key=f"tipo_m_{key_sufijo}")

                if st.form_submit_button("💾 Guardar Lugar", use_container_width=True):
                    if nom_m:
                        ok, msg = agregar_sitio_a_lugares(nom_m, dir_m, None, None, None if cat_m == "⚡ Detección Automática" else cat_m, tipo_m, 0, "", "")
                        if ok:
                            st.rerun()


# =============================================================================
# 7. INICIALIZACIÓN DE ESTADO
# =============================================================================
if "config_viaje" not in st.session_state:
    st.session_state.config_viaje = cargar_config_viaje()

if "lugares" not in st.session_state:
    st.session_state.lugares = cargar_itinerario_disco()
else:
    sincronizar_lugares_desde_disco()

if "lugar_activo_id" not in st.session_state:
    st.session_state.lugar_activo_id = None

if "editando_spot_key" not in st.session_state:
    st.session_state.editando_spot_key = None


# =============================================================================
# 8. CABECERA HERO EDITORIAL NAVIDEÑA
# =============================================================================
cfg_v = st.session_state.config_viaje
hotel = cfg_v.get("hotel", {})
v_ida = cfg_v.get("vuelo_ida", {})
v_vta = cfg_v.get("vuelo_vuelta", {})

lugares_activos = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
lugares_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
lugares_visitados = [l for l in lugares_activos if l.get("visitado", False)]

st.markdown(f"""
<div class="hero-container">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
    <div>
      <div class="hero-eyebrow">🎄 NAVIDAD & FIN DE AÑO · 26 DIC 2026 - 4 ENE 2027 ❄️</div>
      <div class="hero-title">Navidad en Nueva York 🗽✨</div>
      <div style="margin-top: 5px;">
        <span class="hero-pill">✈️ {v_ida.get('vuelo','Aer Lingus · EI583, EI107')} · {v_ida.get('fecha','26 Dic')}</span>
        <span class="hero-pill">🛫 {v_vta.get('vuelo','Aer Lingus · EI104, EI582')} · {v_vta.get('fecha','4 Ene')}</span>
        <span class="hero-pill">🏨 {hotel.get('nombre','Courtyard by Marriott Upper East Side')}</span>
      </div>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap; width:auto;">
      <div class="hero-stat-box">
        <div class="hero-stat-val">{len(lugares_activos)}</div>
        <div class="hero-stat-lbl">En Ruta</div>
      </div>
      <div class="hero-stat-box">
        <div class="hero-stat-val">{len(lugares_guardados)}</div>
        <div class="hero-stat-lbl">Guardados</div>
      </div>
      <div class="hero-stat-box">
        <div class="hero-stat-val">{len(lugares_visitados)}</div>
        <div class="hero-stat-lbl">Hechos</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 9. PESTAÑAS PRINCIPALES DEL SISTEMA
# =============================================================================
pestanas = st.tabs([
    "🗺️ Mapa",
    "📅 Itinerario",
    "📍 Guardados",
    "💵 Divisas & Tip",
    "✈️ Vuelos & Hotel",
    "🌧️ Clima"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: MAPA GOOGLE
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[0]:
    c_m1, c_m2, c_m3 = st.columns([3, 2, 2])
    with c_m1:
        opciones_vista = [
            "🌐 Todos los Sitios",
            "📅 Sitios en Itinerario (Días 1 a 10)",
            "🏨 Solo Hotel"
        ] + [etiqueta_dia(d) for d in range(1, 11)]
        sel_vista = selectbox_sin_teclado("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    with c_m2:
        sel_capa = selectbox_sin_teclado(
            "Capa:",
            ["Google Maps Callejero", "Google Maps Satélite / Híbrido", "Google Maps Terreno", "OpenStreetMap"],
            label_visibility="collapsed"
        )
    with c_m3:
        cats_actuales = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in st.session_state.lugares))
        sel_filtro_cat = selectbox_sin_teclado("Categoría:", ["Todas"] + cats_actuales, label_visibility="collapsed")

    if "Todos" in sel_vista:
        sitios_mapa = list(st.session_state.lugares)
    elif "Solo Sitios en Itinerario" in sel_vista:
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    elif "Solo Hotel" in sel_vista:
        sitios_mapa = []
    else:
        m_dia = re.search(r"Día (\d+):", sel_vista)
        num_d = int(m_dia.group(1)) if m_dia else 1
        sitios_mapa = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == num_d])

    if sel_filtro_cat != "Todas":
        sitios_mapa = [l for l in sitios_mapa if normalizar_categoria(l.get("categoria", "")) == sel_filtro_cat]

    h_lat = hotel.get("lat", 40.780242)
    h_lon = hotel.get("lon", -73.946123)
    h_nom = hotel.get("nombre", "Courtyard by Marriott New York Manhattan Upper East Side")
    h_dir = hotel.get("direccion", "410 E 92nd St, New York, NY 10128")

    if sitios_mapa:
        center_lat = sum(p["lat"] for p in sitios_mapa) / len(sitios_mapa)
        center_lon = sum(p["lon"] for p in sitios_mapa) / len(sitios_mapa)
    else:
        center_lat, center_lon = h_lat, h_lon

    TILES_GMAPS = {
        "Google Maps Callejero": ("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", "Google Maps"),
        "Google Maps Satélite / Híbrido": ("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", "Google Maps Satélite"),
        "Google Maps Terreno": ("https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}", "Google Maps Terreno"),
        "OpenStreetMap": ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap")
    }
    tile_url, tile_attr = TILES_GMAPS[sel_capa]

    mapa = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13 if len(sitios_mapa) < 18 else 12,
        tiles=None,
        scrollWheelZoom=False
    )
    folium.TileLayer(tiles=tile_url, attr=tile_attr, max_zoom=20).add_to(mapa)

    folium.Marker(
        location=[h_lat, h_lon],
        tooltip=f"🏨 {h_nom}",
        icon=crear_pin_google_maps("🏨 Hotel", h_nom)
    ).add_to(mapa)

    for s in sitios_mapa:
        pt = (s["lat"], s["lon"])
        cat_spot = normalizar_categoria(s.get("categoria", "📍 Otros"))
        nom_spot = s.get("nombre", "Lugar")

        folium.Marker(
            location=pt,
            tooltip=f"{obtener_emoji_categoria(cat_spot)} {nom_spot}",
            icon=crear_pin_google_maps(cat_spot, nom_spot)
        ).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=470)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[1]:
    total_itinerario = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    total_visitados = [l for l in total_itinerario if l.get("visitado", False)]
    pct_progreso = int((len(total_visitados) / max(1, len(total_itinerario))) * 100) if total_itinerario else 0

    col_it_head1, col_it_head2 = st.columns([3, 2])
    with col_it_head1:
        st.markdown('<div class="ny-card-header">🎄 CRONOGRAMA DE VIAJE · 10 DÍAS</div>', unsafe_allow_html=True)
    with col_it_head2:
        st.markdown(
            f'<div style="font-weight:800; font-size:0.84rem; color:#0F172A;">'
            f'Progreso: <b>{len(total_visitados)}</b> / <b>{len(total_itinerario)}</b> lugares ({pct_progreso}%)'
            f'</div>',
            unsafe_allow_html=True
        )

    opciones_filtro_it = ["📋 Todos los Días (Días 1 a 10)"] + [etiqueta_dia(d) for d in range(1, 11)]
    filtro_it_sel = selectbox_sin_teclado("Ver itinerario:", opciones_filtro_it, label_visibility="collapsed")

    if "Todos los Días" in filtro_it_sel:
        dias_a_mostrar = list(range(1, 11))
    else:
        m_d_it = re.search(r"Día (\d+):", filtro_it_sel)
        dias_a_mostrar = [int(m_d_it.group(1))] if m_d_it else [1]

    for d in dias_a_mostrar:
        paradas_dia = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == d])
        
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-left:6px solid #15803D; border-radius:13px; padding:8px 12px; margin-top:10px; margin-bottom:8px;">
          <div style="font-weight:900; font-size:0.98rem; color:#0F172A;">{etiqueta_dia(d)}</div>
        </div>
        """, unsafe_allow_html=True)

        for item in paradas_dia:
            idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
            is_visited = item.get("visitado", False)
            cat_i = normalizar_categoria(item.get("categoria", "📍 Otros"))
            
            c_chk, c_info = st.columns([0.45, 9.55], gap="small")
            with c_chk:
                chk_val = st.checkbox("", value=is_visited, key=f"chk_it_{d}_{item['id']}")
                if chk_val != is_visited and idx_real is not None:
                    st.session_state.lugares[idx_real]["visitado"] = chk_val
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()

            with c_info:
                st.markdown(f"**{obtener_emoji_categoria(cat_i)} {item['nombre']}** ({item.get('hora','Sin hora')})", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[2]:
    render_formulario_agregar_lugar("guardados")
    st.markdown('<div class="ny-card-header">Lugares Guardados</div>', unsafe_allow_html=True)

    pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    for p_spot in pool_guardados:
        st.markdown(f"- **{p_spot['nombre']}** ({p_spot.get('categoria','📍 Otros')})")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: MODO LLUVIA & CLIMA
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[5]:
    st.markdown('<div class="ny-card-header">🌧️ Clima en Tiempo Real</div>', unsafe_allow_html=True)
    clima_data = consultar_clima_nyc()
    if clima_data and "current" in clima_data:
        cur = clima_data["current"]
        st.success(f"Temperatura actual en Nueva York: {cur.get('temperature_2m')} °C")
    else:
        st.info("Datos meteorológicos no disponibles temporalmente.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: DIVISAS & CALCULADORA
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[3]:
    st.markdown('<div class="ny-card-header">💵 Divisas & Calculadora de Tax</div>', unsafe_allow_html=True)
    tasa_eur, _ = obtener_tasa_usd_eur()
    val_usd = st.number_input("Cantidad en Dólares ($):", value=50.0)
    st.info(f"Equivalente: **{val_usd * tasa_eur:.2f} €**")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: VUELOS, HOTEL & LISTAS
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[4]:
    st.markdown('<div class="ny-card-header">✈️ Vuelos & Hotel</div>', unsafe_allow_html=True)
    st.write(f"Hotel actual: {hotel.get('nombre')}")
