import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import urllib.request
import urllib.parse
import os
import re
import math
from datetime import datetime

ARCH_ITINERARIO = "itinerario_actual.json"
ARCH_CONFIG     = "config_viaje.json"

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA & ESTILO NAVIDEÑO EDITORIAL (CALIBRI & FONDO BLANCO)
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
    gap: 12px !important;
    padding: 12px 16px !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
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

  .stApp, html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #F8F9FA !important;
    color: #0F172A !important;
  }
  .block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1320px !important;
  }

  .hero-container {
    background: #FFFFFF !important;
    border-radius: 20px;
    padding: 22px 26px;
    color: #0F172A !important;
    margin-bottom: 18px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    border: 1.5px solid #CBD5E1;
    border-top: 5px solid #15803D;
  }
  .hero-eyebrow {
    font-size: 0.85rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    color: #15803D !important;
  }
  .hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 4px 0 10px 0;
    color: #0F172A !important;
    letter-spacing: -0.5px;
    line-height: 1.15;
  }
  .hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 30px;
    padding: 6px 14px;
    font-size: 0.88rem;
    color: #0F172A !important;
    font-weight: 700;
    margin-right: 6px;
    margin-bottom: 5px;
  }
  .hero-stat-box {
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 14px;
    padding: 10px 16px;
    text-align: center;
    min-width: 78px;
    flex: 1 1 auto;
  }
  .hero-stat-val {
    font-size: 1.6rem;
    font-weight: 900;
    color: #0F172A !important;
  }
  .hero-stat-lbl {
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #0F172A !important;
  }

  .ny-card {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    color: #0F172A !important;
  }
  .ny-card-header {
    font-size: 0.84rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    color: #0F172A !important;
    margin-bottom: 10px;
  }

  .place-sheet {
    background: #FFFFFF !important;
    border: 2px solid #CBD5E1 !important;
    border-radius: 18px;
    padding: 18px 22px;
    margin: 14px 0;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
    animation: fadeIn 0.2s ease-out;
    color: #0F172A !important;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .badge-cat {
    display: inline-block;
    background: #F1F5F9 !important;
    color: #0F172A !important;
    font-size: 0.82rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #CBD5E1;
  }
  .badge-hora {
    display: inline-block;
    background: #EEF2FF !important;
    color: #1E1B4B !important;
    font-size: 0.82rem;
    font-weight: 900;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #C7D2FE;
  }
  .badge-indoor {
    display: inline-block;
    background: #EFF6FF !important;
    color: #1E3A8A !important;
    font-size: 0.8rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #BFDBFE;
  }
  .badge-outdoor {
    display: inline-block;
    background: #ECFDF5 !important;
    color: #064E3B !important;
    font-size: 0.8rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #A7F3D0;
  }
  .badge-dia {
    display: inline-block;
    background: #FEF3C7 !important;
    color: #78350F !important;
    font-size: 0.8rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #FDE68A;
  }

  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #E2E8F0 !important;
    padding: 5px;
    border-radius: 14px;
    border: 1px solid #CBD5E1;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    padding: 8px 14px !important;
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
    border-radius: 11px !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
    min-height: 40px !important;
    border: 1.5px solid #94A3B8 !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    transition: all 0.15s ease-in-out !important;
  }
  .stButton > button:hover, .stFormSubmitButton > button:hover, [data-testid="stLinkButton"] > a:hover {
    background: #F1F5F9 !important;
    border-color: #0F172A !important;
    color: #0F172A !important;
  }

  iframe {
    border-radius: 18px !important;
    border: 1.5px solid #CBD5E1 !important;
  }

  .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
    border-radius: 11px !important;
    border: 1.5px solid #94A3B8 !important;
    background: #FFFFFF !important;
    font-size: 0.92rem !important;
    color: #0F172A !important;
  }
  [data-baseweb="select"] span, [data-baseweb="select"] div {
    color: #0F172A !important;
    font-weight: 700 !important;
  }
  ul[role="listbox"], ul[role="listbox"] li {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
  }

  @media (max-width: 768px) {
    .block-container {
      padding-left: 0.75rem !important;
      padding-right: 0.75rem !important;
      padding-top: 0.75rem !important;
    }
    .hero-container {
      padding: 16px 16px !important;
      border-radius: 16px !important;
    }
    .hero-title {
      font-size: 1.65rem !important;
    }
    .hero-pill {
      font-size: 0.8rem !important;
      padding: 4px 10px !important;
    }
    .hero-stat-box {
      padding: 8px 10px !important;
      min-width: 70px !important;
    }
    .hero-stat-val {
      font-size: 1.35rem !important;
    }
    [data-testid="stHorizontalBlock"] {
      gap: 0.5rem !important;
    }
  }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. DEFINICIÓN DEL VIAJE NAVIDEÑO (26 DIC 2026 - 4 ENE 2027)
# =============================================================================
DIAS_VIAJE = {
    1:  {"fecha": "26 Dic", "dia": "Jueves",    "titulo": "Llegada a NYC & Luces Navideñas de Times Square 🎄"},
    2:  {"fecha": "27 Dic", "dia": "Viernes",   "titulo": "Midtown & Árbol de Navidad de Rockefeller Center ✨"},
    3:  {"fecha": "28 Dic", "dia": "Sábado",    "titulo": "Upper East Side, Central Park & Árbol de The Met ❄️"},
    4:  {"fecha": "29 Dic", "dia": "Domingo",   "titulo": "Chelsea, High Line & Bryant Park Winter Village ⛸️"},
    5:  {"fecha": "30 Dic", "dia": "Lunes",     "titulo": "SoHo, Greenwich Village & Compras Navideñas 🎁"},
    6:  {"fecha": "31 Dic", "dia": "Martes",    "titulo": "🎉 ¡Nochevieja en NY! Puente de Brooklyn & Fin de Año 🎆"},
    7:  {"fecha": "01 Ene", "dia": "Miércoles", "titulo": "✨ ¡Año Nuevo 2027! Patinaje sobre Hielo & Relax ⛸️"},
    8:  {"fecha": "02 Ene", "dia": "Jueves",    "titulo": "Financial District, 9/11 Memorial & Century 21 🛍️"},
    9:  {"fecha": "03 Ene", "dia": "Viernes",   "titulo": "Brooklyn, DUMBO & Outlets de Rebajas de Invierno 🛍️"},
    10: {"fecha": "04 Ene", "dia": "Sábado",    "titulo": "Último Brunch, Despedida de NYC & Vuelo de Vuelta 🛫"},
}


# =============================================================================
# 3. CATEGORÍAS DE UNA SOLA PALABRA & MOTOR DE CLASIFICACIÓN
# =============================================================================
CATEGORIAS_CANONICAS = [
    "🍕 Restaurantes",
    "🍪 Dulces",
    "🍸 Copas",
    "🎷 Ocio",
    "🛍️ Compras",
    "🏛️ Museos",
    "🏙️ Miradores",
    "🌲 Parques",
    "🏨 Hotel",
    "📍 Otros"
]

MAPEO_CATEGORIAS_ANTIGUAS = {
    "🍕 Gastronomía & Restaurantes": "🍕 Restaurantes",
    "🍪 Cafeterías & Dulces": "🍪 Dulces",
    "🍸 Rooftops & Copas": "🍸 Copas",
    "🎷 Jazz, Música & Ocio": "🎷 Ocio",
    "🛍️ Compras & Outlets": "🛍️ Compras",
    "🏛️ Museos & Monumentos": "🏛️ Museos",
    "🏙️ Miradores & Observatorios": "🏙️ Miradores",
    "🌲 Parques, Muelles & Puentes": "🌲 Parques",
    "🏨 Hotel Base": "🏨 Hotel",
    "📍 Otros Lugares": "📍 Otros",
}

def normalizar_categoria(cat: str) -> str:
    if not cat:
        return "📍 Otros"
    if cat in MAPEO_CATEGORIAS_ANTIGUAS:
        return MAPEO_CATEGORIAS_ANTIGUAS[cat]
    if cat in CATEGORIAS_CANONICAS:
        return cat
    c_low = cat.lower()
    if "restaur" in c_low or "gastro" in c_low:
        return "🍕 Restaurantes"
    if "dulce" in c_low or "cafet" in c_low:
        return "🍪 Dulces"
    if "copa" in c_low or "rooftop" in c_low:
        return "🍸 Copas"
    if "ocio" in c_low or "jazz" in c_low:
        return "🎷 Ocio"
    if "compra" in c_low or "outlet" in c_low:
        return "🛍️ Compras"
    if "museo" in c_low or "monument" in c_low:
        return "🏛️ Museos"
    if "mirador" in c_low or "observ" in c_low:
        return "🏙️ Miradores"
    if "parque" in c_low or "puente" in c_low or "muelle" in c_low:
        return "🌲 Parques"
    if "hotel" in c_low:
        return "🏨 Hotel"
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
        return "🍕 Restaurantes", "Interior"
    if any(k in nom for k in ['park', 'central park', 'bridge', 'puente', 'high line', 'little island', 'fulton ferry', 'domino', 'pier 17', 'pier 57', 'pier 35', 'pebble beach', 'tudor city', 'squibb', 'battery', 'waterfront', 'picnic', 'botanic', 'coney island', 'boardwalk']):
        return "🌲 Parques", "Exterior"
    if any(k in nom for k in ['museum', 'the met', 'moma', 'morgan library', 'tenement', '9/11 memorial', 'oculus', 'grand central', 'library', 'atlas', 'one times square', 'times square', 'memorial', 'statue of liberty', 'trinity church', 'rockefeller center', 'st. patrick']):
        tipo = "Exterior" if any(x in nom for x in ['times square', 'atlas', 'statue']) else "Interior"
        return "🏛️ Museos", tipo

    if 'sweet' in orig:
        return "🍪 Dulces", "Interior"
    if 'food' in orig:
        return "🍕 Restaurantes", "Interior"
    if 'rooftop' in orig:
        return "🍸 Copas", "Interior"
    if 'tienda' in orig or 'outlet' in orig:
        return "🛍️ Compras", "Interior"
    if 'spot' in orig:
        return "🌲 Parques", "Exterior"

    return "📍 Otros", "Interior"

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

def clave_orden_hora(item: dict):
    """Ordena primero los que tienen hora (HH:MM) cronológicamente y luego los sin hora."""
    h = (item.get("hora") or "").strip()
    m = re.match(r'^(\d{1,2}):(\d{2})$', h)
    if m:
        return (0, int(m.group(1)) * 60 + int(m.group(2)), item.get("id", 0))
    return (1, 9999, item.get("id", 0))


# =============================================================================
# 4. APIs EXTERNAS: CAMBIO DE MONEDA & OPEN-METEO EN TIEMPO REAL
# =============================================================================
@st.cache_data(ttl=3600)
def obtener_tasa_usd_eur():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
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
        with urllib.request.urlopen(req, timeout=5) as resp:
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

def guardar_config_viaje(cfg):
    try:
        with open(ARCH_CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def cargar_itinerario_disco():
    if os.path.exists(ARCH_ITINERARIO):
        try:
            with open(ARCH_ITINERARIO, "r", encoding="utf-8") as f:
                datos = json.load(f)
                actualizado = False
                for p in datos:
                    cat_norm = normalizar_categoria(p.get("categoria", ""))
                    if p.get("categoria") != cat_norm:
                        p["categoria"] = cat_norm
                        actualizado = True
                    if "hora" not in p:
                        p["hora"] = ""
                        actualizado = True
                if actualizado:
                    guardar_itinerario_disco(datos)
                return datos
        except Exception:
            pass
    return []

def guardar_itinerario_disco(lugares):
    try:
        with open(ARCH_ITINERARIO, "w", encoding="utf-8") as f:
            json.dump(lugares, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# =============================================================================
# 6. SINCRONIZADOR DE LISTAS DE GOOGLE MAPS Y FORMULARIO DE ALTA
# =============================================================================
def extraer_lugares_lista_gmaps(url_lista: str, nombre_lista: str = ""):
    lugares_encontrados = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
    }
    try:
        req = urllib.request.Request(url_lista, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        m = re.search(r'href="(/maps/preview/entitylist/getlist\?[^"]+)"', html)
        if not m:
            return lugares_encontrados

        entity_url = "https://www.google.com" + m.group(1).replace("&", "&")
        req2 = urllib.request.Request(entity_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=10) as r2:
            raw = r2.read().decode('utf-8', errors='ignore').lstrip(")]}'\n ")
        data = json.loads(raw)

        def _buscar_entidades(nodo):
            if isinstance(nodo, list):
                coords = None
                for el in nodo:
                    if (isinstance(el, list) and len(el) >= 4 and el[0] is None and el[1] is None
                            and isinstance(el[2], (int, float)) and isinstance(el[3], (int, float))):
                        coords = (float(el[2]), float(el[3]))
                        break
                if coords:
                    strs = [s for s in nodo if isinstance(s, str) and len(s) > 1
                            and not s.startswith("http") and not s.startswith("ChIJ")
                            and not s.startswith("/g/") and not s.startswith("/m/")]
                    if strs:
                        nombre_raw = strs[0]
                        partes = nombre_raw.split(",")
                        nom_spot = partes[0].strip()
                        dir_spot = ", ".join(partes[1:]).strip() if len(partes) > 1 else ""
                        cat, tipo = clasificar_lugar(nom_spot, dir_spot, nombre_lista)
                        lugares_encontrados.append({
                            "nombre": nom_spot,
                            "lat": coords[0],
                            "lon": coords[1],
                            "direccion": dir_spot,
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
    except Exception as e:
        st.warning(f"Aviso de sincronización ({nombre_lista}): {e}")
    return lugares_encontrados

def geocodificar_direccion_o_nombre(texto: str) -> tuple:
    if not texto:
        return None, None, ""
    q = f"{texto}, New York, NY".strip()
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'ny_holiday_planner_app_v3'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            res = json.loads(r.read().decode('utf-8'))
            if res and len(res) > 0:
                return float(res[0]['lat']), float(res[0]['lon']), res[0].get('display_name', '')
    except Exception:
        pass
    return None, None, ""

def agregar_sitio_a_lugares(nombre: str, direccion: str = "", lat: float = None, lon: float = None,
                            categoria: str = None, tipo: str = None, dia_dest: int = 0, hora: str = "") -> tuple:
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
    else:
        categoria = normalizar_categoria(categoria)

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
        "categoria": categoria,
        "tipo": tipo,
        "visitado": False
    }
    st.session_state.lugares.append(nuevo)
    guardar_itinerario_disco(st.session_state.lugares)
    return True, f"¡'{nom}' añadido con éxito como {categoria}!"

def importar_sitio_desde_gmaps(url_o_texto: str, dia_dest: int = 0) -> tuple:
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
                    s["hora"] = ""
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        try:
            req = urllib.request.Request(raw, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                url_final = r.geturl()
                html = r.read().decode('utf-8', errors='ignore')
                m_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url_final)
                if m_coords:
                    lat_ext = float(m_coords.group(1))
                    lon_ext = float(m_coords.group(2))
                m_nom = re.search(r'/place/([^/@?]+)', url_final)
                if m_nom:
                    nombre_extraido = urllib.parse.unquote_plus(m_nom.group(1)).replace("+", " ")
                elif "<title>" in html:
                    m_tit = re.search(r'<title>([^<]+)</title>', html)
                    if m_tit:
                        nombre_extraido = m_tit.group(1).replace("- Google Maps", "").replace("· Google Maps", "").strip()
        except Exception:
            pass

    if not nombre_extraido:
        nombre_extraido = raw.split("/")[-1].replace("+", " ")
        if len(nombre_extraido) < 3 or nombre_extraido.startswith("http"):
            nombre_extraido = "Lugar Google Maps"

    return agregar_sitio_a_lugares(nombre_extraido, dir_ext, lat_ext, lon_ext, None, None, dia_dest, "")

def render_formulario_agregar_lugar(key_sufijo: str = "gen"):
    with st.expander("➕ Añadir Nuevo Lugar (desde Google Maps o a Mano)", expanded=False):
        tab_gm, tab_man = st.tabs(["🌐 Enlace de Google Maps", "✏️ Introducir a Mano"])
        dias_asig_opts = ["📌 Guardados"] + [f"Día {d} ({DIAS_VIAJE[d]['fecha']})" for d in range(1, 11)]

        with tab_gm:
            st.caption("Pega el enlace de Google Maps de un sitio o lista para importarlo al viaje:")
            with st.form(f"form_add_gm_{key_sufijo}"):
                url_input = st.text_input("Enlace de Google Maps:", placeholder="https://maps.app.goo.gl/...", key=f"inp_gm_{key_sufijo}")
                dia_dest_gm = st.selectbox("Asignar a:", dias_asig_opts, key=f"sel_dia_gm_{key_sufijo}")
                val_dia_gm = 0 if "Guardados" in dia_dest_gm else int(re.search(r'Día (\d+)', dia_dest_gm).group(1))

                if st.form_submit_button("📥 Importar desde Google Maps", use_container_width=True):
                    if url_input:
                        with st.spinner("Analizando y geolocalizando sitio..."):
                            ok, msg = importar_sitio_desde_gmaps(url_input, val_dia_gm)
                            if ok:
                                st.toast(msg, icon="📍")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("Por favor introduce una URL de Google Maps.")

        with tab_man:
            st.caption("Escribe los datos del lugar (si dejas las coordenadas vacías se buscarán automáticamente):")
            with st.form(f"form_add_man_{key_sufijo}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    nom_m = st.text_input("Nombre del lugar:", placeholder="Ej: Levain Bakery, Joe's Pizza...", key=f"nom_m_{key_sufijo}")
                    dir_m = st.text_input("Dirección o Barrio:", placeholder="Ej: Upper West Side...", key=f"dir_m_{key_sufijo}")
                with c_m2:
                    cat_m = st.selectbox("Categoría:", ["⚡ Detección Automática"] + CATEGORIAS_CANONICAS, key=f"cat_m_{key_sufijo}")
                    tipo_m = st.selectbox("Tipo:", ["Interior", "Exterior"], key=f"tipo_m_{key_sufijo}")

                c_m3, c_m4 = st.columns(2)
                with c_m3:
                    dia_dest_m = st.selectbox("Asignar a:", dias_asig_opts, key=f"sel_dia_m_{key_sufijo}")
                    val_dia_m = 0 if "Guardados" in dia_dest_m else int(re.search(r'Día (\d+)', dia_dest_m).group(1))
                with c_m4:
                    hora_m = st.text_input("Hora (opcional, HH:MM):", placeholder="Ej: 10:30", key=f"hora_m_{key_sufijo}")

                coords_man_chk = st.checkbox("Introducir latitud / longitud manuales", key=f"chk_coords_{key_sufijo}")
                lat_man, lon_man = None, None
                if coords_man_chk:
                    c_lt, c_ln = st.columns(2)
                    with c_lt:
                        lat_man = st.number_input("Latitud:", value=40.7802, format="%.6f", key=f"lat_m_{key_sufijo}")
                    with c_ln:
                        lon_man = st.number_input("Longitud:", value=-73.9461, format="%.6f", key=f"lon_m_{key_sufijo}")

                if st.form_submit_button("💾 Guardar Lugar en el Viaje", use_container_width=True):
                    if nom_m:
                        with st.spinner("Guardando y geolocalizando..."):
                            c_val = None if cat_m == "⚡ Detección Automática" else cat_m
                            ok, msg = agregar_sitio_a_lugares(nom_m, dir_m, lat_man, lon_man, c_val, tipo_m, val_dia_m, hora_m)
                            if ok:
                                st.toast(msg, icon="✨")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("Introduce al menos el nombre del lugar.")

def render_editor_sitio(spot: dict, key_prefix: str):
    """Formulario desplegable para modificar cualquier dato de un sitio ya introducido."""
    idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == spot["id"]), None)
    if idx_real is None:
        return
    with st.expander(f"✏️ Editar datos de «{spot['nombre']}»", expanded=False):
        with st.form(f"form_edit_{key_prefix}_{spot['id']}"):
            c1, c2 = st.columns(2)
            with c1:
                e_nom = st.text_input("Nombre:", value=spot.get("nombre", ""))
                e_dir = st.text_input("Dirección:", value=spot.get("direccion", ""))
                e_hora = st.text_input("Hora (HH:MM):", value=spot.get("hora", ""), placeholder="Ej: 14:00")
            with c2:
                cat_act = normalizar_categoria(spot.get("categoria", "📍 Otros"))
                idx_c = CATEGORIAS_CANONICAS.index(cat_act) if cat_act in CATEGORIAS_CANONICAS else 0
                e_cat = st.selectbox("Categoría:", CATEGORIAS_CANONICAS, index=idx_c)

                tipo_act = spot.get("tipo", "Interior")
                e_tipo = st.selectbox("Tipo:", ["Interior", "Exterior"], index=0 if tipo_act == "Interior" else 1)

                opciones_dias = ["📌 Guardados"] + [f"Día {d} ({DIAS_VIAJE[d]['fecha']})" for d in range(1, 11)]
                dia_act = spot.get("dia", 0)
                e_dia_str = st.selectbox("Día:", opciones_dias, index=dia_act if 0 <= dia_act <= 10 else 0)

            c_lat, c_lon = st.columns(2)
            with c_lat:
                e_lat = st.number_input("Latitud:", value=float(spot.get("lat", 40.7580)), format="%.6f")
            with c_lon:
                e_lon = st.number_input("Longitud:", value=float(spot.get("lon", -73.9855)), format="%.6f")

            c_save, c_del = st.columns([3, 1])
            with c_save:
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                    n_dia = 0 if "Guardados" in e_dia_str else int(re.search(r'Día (\d+)', e_dia_str).group(1))
                    st.session_state.lugares[idx_real].update({
                        "nombre": e_nom.strip() or spot["nombre"],
                        "direccion": e_dir.strip(),
                        "hora": e_hora.strip(),
                        "categoria": e_cat,
                        "tipo": e_tipo,
                        "dia": n_dia,
                        "lat": float(e_lat),
                        "lon": float(e_lon),
                    })
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.toast(f"¡'{e_nom}' actualizado!", icon="✅")
                    st.rerun()
            with c_del:
                if st.form_submit_button("🗑️ Borrar", use_container_width=True):
                    st.session_state.lugares.pop(idx_real)
                    if st.session_state.get("lugar_activo_id") == spot["id"]:
                        st.session_state.lugar_activo_id = None
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.toast("Sitio eliminado.", icon="🗑️")
                    st.rerun()


# =============================================================================
# 7. INICIALIZACIÓN DE ESTADO
# =============================================================================
if "config_viaje" not in st.session_state:
    st.session_state.config_viaje = cargar_config_viaje()

if "lugares" not in st.session_state or not st.session_state.lugares:
    st.session_state.lugares = cargar_itinerario_disco()

if "lugar_activo_id" not in st.session_state:
    st.session_state.lugar_activo_id = None


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
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
    <div>
      <div class="hero-eyebrow">🎄 VIAJE DE NAVIDAD & FIN DE AÑO · 26 DIC 2026 - 4 ENE 2027 ❄️</div>
      <div class="hero-title">Navidad en Nueva York 🗽✨</div>
      <div style="margin-top: 8px;">
        <span class="hero-pill">✈️ {v_ida.get('vuelo','Aer Lingus · EI583, EI107')} · {v_ida.get('fecha','26 Dic')}</span>
        <span class="hero-pill">🛫 {v_vta.get('vuelo','Aer Lingus · EI104, EI582')} · {v_vta.get('fecha','4 Ene')}</span>
        <span class="hero-pill">🏨 {hotel.get('nombre','Courtyard by Marriott Upper East Side')}</span>
      </div>
    </div>
    <div style="display:flex; gap:10px; flex-wrap:wrap;">
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
        <div class="hero-stat-lbl">Completos</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 9. PESTAÑAS PRINCIPALES DEL SISTEMA
# =============================================================================
pestanas = st.tabs([
    "🗺️ Mapa Google",
    "📅 Itinerario (10 Días)",
    "📍 Guardados",
    "🌧️ Modo Lluvia & Clima",
    "💵 Divisas & Calculadora NY",
    "✈️ Vuelos, Hotel & Listas"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: MAPA GOOGLE (SOLO DESPLEGABLES Y MAPA)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[0]:
    c_m1, c_m2, c_m3 = st.columns([3, 2, 2])
    with c_m1:
        opciones_vista = [
            "🌐 Todos los Sitios (Itinerario + Guardados + Hotel)",
            "📅 Solo Sitios en Itinerario (Días 1 a 10)",
            "🏨 Solo Hotel"
        ] + [f"Día {d}: {DIAS_VIAJE[d]['fecha']} ({DIAS_VIAJE[d]['dia']})" for d in range(1, 11)]
        sel_vista = st.selectbox("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    with c_m2:
        sel_capa = st.selectbox(
            "Capa:",
            ["Google Maps Callejero", "Google Maps Satélite / Híbrido", "Google Maps Terreno", "OpenStreetMap"],
            label_visibility="collapsed"
        )
    with c_m3:
        cats_actuales = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in st.session_state.lugares))
        sel_filtro_cat = st.selectbox("Categoría:", ["Todas"] + cats_actuales, label_visibility="collapsed")

    if "Todos" in sel_vista:
        sitios_mapa = list(st.session_state.lugares)
    elif "Solo Sitios en Itinerario" in sel_vista:
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    elif "Solo Hotel" in sel_vista:
        sitios_mapa = []
    else:
        m_dia = re.search(r'Día (\d+):', sel_vista)
        num_d = int(m_dia.group(1)) if m_dia else 1
        sitios_mapa = sorted(
            [l for l in st.session_state.lugares if l.get("dia", 0) == num_d],
            key=clave_orden_hora
        )

    if sel_filtro_cat != "Todas":
        sitios_mapa = [l for l in sitios_mapa if normalizar_categoria(l.get("categoria")) == sel_filtro_cat]

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

    g_hotel_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(h_nom + ' ' + h_dir)}"
    pop_hotel_html = f"""
    <div style="font-family: -apple-system, sans-serif; min-width: 210px; padding: 4px;">
      <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">🏨 HOTEL</span>
      <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin: 6px 0 2px;">{h_nom}</div>
      <div style="font-size: 12px; color: #0F172A; margin-bottom: 8px;">📍 {h_dir}</div>
      <a href="{g_hotel_url}" target="_blank" style="display:block; text-align:center; background:#1A73E8; color:white; padding:7px 4px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Abrir en Google Maps →</a>
    </div>
    """
    folium.Marker(
        location=[h_lat, h_lon],
        popup=folium.Popup(pop_hotel_html, max_width=260),
        tooltip=f"🏨 {h_nom}",
        icon=crear_pin_google_maps("🏨 Hotel", h_nom)
    ).add_to(mapa)

    coords_ruta = []
    for s in sitios_mapa:
        pt = (s["lat"], s["lon"])
        if s.get("dia", 0) > 0:
            coords_ruta.append(pt)

        cat_spot = normalizar_categoria(s.get("categoria", "📍 Otros"))
        tipo_spot = s.get("tipo", "Interior")
        dia_spot = s.get("dia", 0)
        hora_spot = s.get("hora", "")
        dir_spot = s.get("direccion", "")
        nom_spot = s.get("nombre", "Lugar")

        hora_txt = f" · 🕒 {hora_spot}" if hora_spot else ""
        dia_txt = f"Día {dia_spot} ({DIAS_VIAJE.get(dia_spot, {}).get('fecha', '')}){hora_txt}" if dia_spot > 0 else "📌 Guardados"
        tipo_badge = "🌧️ Interior" if tipo_spot == "Interior" else "☀️ Exterior"

        g_search = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(nom_spot + ' New York')}"
        g_route  = f"https://www.google.com/maps/dir/?api=1&origin={h_lat},{h_lon}&destination={s['lat']},{s['lon']}"

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 230px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 11px; font-weight: 800; color: #2563EB;">{dia_txt}</span>
            <span style="font-size: 10px; font-weight: 700; background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 6px;">{tipo_badge}</span>
          </div>
          <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-bottom: 3px;">{obtener_emoji_categoria(cat_spot)} {nom_spot}</div>
          {f'<div style="font-size: 12px; color: #0F172A; margin-bottom: 6px;">📍 {dir_spot}</div>' if dir_spot else ''}
          <div style="font-size: 11px; color: #0F172A; margin-bottom: 8px;"><b>Categoría:</b> {cat_spot}</div>
          <div style="display: flex; gap: 6px;">
            <a href="{g_search}" target="_blank" style="flex:1; text-align:center; background:#1A73E8; color:white; padding:7px 4px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Abrir en Maps →</a>
            <a href="{g_route}" target="_blank" style="text-align:center; background:#F8FAFC; border:1px solid #CBD5E1; color:#0F172A; padding:7px 8px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">🧭 Ruta</a>
          </div>
        </div>
        """

        folium.Marker(
            location=pt,
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f"{obtener_emoji_categoria(cat_spot)} {nom_spot}{hora_txt}",
            icon=crear_pin_google_maps(cat_spot, nom_spot)
        ).add_to(mapa)

    if len(coords_ruta) > 1 and "Día " in sel_vista:
        folium.PolyLine(coords_ruta, color="#1A73E8", weight=3.5, opacity=0.8, dash_array="6, 8").add_to(mapa)

    resultado_mapa = st_folium(
        mapa,
        use_container_width=True,
        height=540,
        returned_objects=["last_object_clicked"]
    )

    clicked = resultado_mapa.get("last_object_clicked") if resultado_mapa else None
    if clicked and "lat" in clicked and "lng" in clicked:
        c_lat, c_lon = clicked["lat"], clicked["lng"]
        candidato, dist_min = None, float("inf")
        for s in st.session_state.lugares:
            d = math.hypot(s["lat"] - c_lat, s["lon"] - c_lon)
            if d < dist_min:
                dist_min = d
                candidato = s
        if candidato and dist_min < 0.008:
            st.session_state.lugar_activo_id = candidato["id"]

    if st.session_state.lugar_activo_id is not None:
        idx_p = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == st.session_state.lugar_activo_id), None)
        if idx_p is not None:
            sp = st.session_state.lugares[idx_p]
            cat_sp = normalizar_categoria(sp.get("categoria", "📍 Otros"))
            tipo_sp = sp.get("tipo", "Interior")
            dir_sp = sp.get("direccion", "")
            dia_sp = sp.get("dia", 0)
            hora_sp = sp.get("hora", "")

            hora_badge = f'<span class="badge-hora">🕒 {hora_sp}</span>' if hora_sp else ""
            st.markdown(f"""
            <div class="place-sheet">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                  <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
                    <span class="badge-dia">{f"Día {dia_sp} ({DIAS_VIAJE.get(dia_sp, {}).get('fecha', '')})" if dia_sp > 0 else "📌 Guardados"}</span>
                    {hora_badge}
                    <span class="{'badge-indoor' if tipo_sp == 'Interior' else 'badge-outdoor'}">{'🌧️ Interior' if tipo_sp == 'Interior' else '☀️ Exterior'}</span>
                    <span class="badge-cat">{cat_sp}</span>
                  </div>
                  <h2 style="margin:2px 0 4px 0; font-size:1.35rem; color:#0F172A;">{obtener_emoji_categoria(cat_sp)} {sp['nombre']}</h2>
                  {f'<div style="font-size:0.88rem; color:#0F172A;">📍 {dir_sp}</div>' if dir_sp else ''}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c_act1, c_act2 = st.columns([3, 1])
            with c_act1:
                g_direct = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(sp['nombre'] + ' New York')}"
                st.link_button("🌐 Abrir en Google Maps", g_direct, use_container_width=True)
            with c_act2:
                if st.button("✕ Cerrar", key="close_place_sheet", use_container_width=True):
                    st.session_state.lugar_activo_id = None
                    st.rerun()

            render_editor_sitio(sp, "mapa_sheet")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO COMPLETO (ORDENADO POR HORAS & EDICIÓN COMPLETA)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[1]:
    total_itinerario = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    total_visitados = [l for l in total_itinerario if l.get("visitado", False)]
    pct_progreso = int((len(total_visitados) / max(1, len(total_itinerario))) * 100) if total_itinerario else 0

    col_it_head1, col_it_head2 = st.columns([3, 2])
    with col_it_head1:
        st.markdown('<div class="ny-card-header">🎄 CRONOGRAMA DE VIAJE · 10 DÍAS EN NUEVA YORK</div>', unsafe_allow_html=True)
    with col_it_head2:
        st.markdown(
            f'<div style="text-align:right; font-weight:800; font-size:0.92rem; color:#0F172A;">'
            f'Progreso: <b>{len(total_visitados)}</b> de <b>{len(total_itinerario)}</b> paradas visitadas ({pct_progreso}%)'
            f'</div>',
            unsafe_allow_html=True
        )

    modo_vista_it = st.radio(
        "Modo de visualización:",
        ["📋 Ver Todos los Días Juntos (Días 1 a 10)", "🔍 Planificador Detallado (Día a Día)"],
        horizontal=True,
        key="modo_vista_itinerario"
    )

    if "Todos los Días Juntos" in modo_vista_it:
        st.markdown(
            '<div style="display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 16px 0;">' +
            "".join([
                f'<a href="#dia-{d}" style="text-decoration:none; background:#FFFFFF; border:1.5px solid #94A3B8; border-radius:10px; padding:5px 11px; font-size:0.84rem; font-weight:800; color:#0F172A;">Día {d} · {DIAS_VIAJE[d]["fecha"]}</a>'
                for d in range(1, 11)
            ]) +
            '</div>',
            unsafe_allow_html=True
        )

        for d in range(1, 11):
            dia_info = DIAS_VIAJE[d]
            paradas_dia = sorted(
                [l for l in st.session_state.lugares if l.get("dia", 0) == d],
                key=clave_orden_hora
            )
            visitados_dia = [l for l in paradas_dia if l.get("visitado", False)]

            st.markdown(f'<div id="dia-{d}"></div>', unsafe_allow_html=True)

            with st.container():
                st.markdown(f'''
                <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-left:6px solid #15803D; border-radius:14px; padding:12px 18px; margin-top:14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                  <div>
                    <span style="background:#FEF3C7; color:#78350F; font-size:0.86rem; font-weight:900; padding:3px 10px; border-radius:8px; margin-right:8px; border:1px solid #FDE68A;">
                      DÍA {d}
                    </span>
                    <span style="font-weight:800; font-size:1.05rem; color:#0F172A;">
                      {dia_info['fecha']} · {dia_info['dia']}
                    </span>
                  </div>
                  <div style="font-weight:800; font-size:0.85rem; color:#0F172A; background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:20px; padding:3px 12px;">
                    📍 {len(paradas_dia)} paradas ({len(visitados_dia)} hechas)
                  </div>
                </div>
                ''', unsafe_allow_html=True)

                if not paradas_dia:
                    st.markdown('''
                    <div style="background:#FFFFFF; border:1.5px dashed #94A3B8; border-radius:12px; padding:14px 18px; color:#0F172A; font-size:0.92rem; font-weight:600; margin-bottom:12px;">
                      ❄️ Sin actividades asignadas todavía para este día. Asígnalas desde la pestaña Guardados.
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    for seq_idx, item in enumerate(paradas_dia, 1):
                        idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
                        is_visited = item.get("visitado", False)
                        cat_i = normalizar_categoria(item.get("categoria", "📍 Otros"))
                        emoji_i = obtener_emoji_categoria(cat_i)
                        dir_i = item.get("direccion", "")
                        hora_i = item.get("hora", "")
                        maps_q = urllib.parse.quote(f"{item['nombre']}, New York")
                        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={maps_q}"

                        c_chk, c_info, c_hora, c_action = st.columns([0.4, 3.8, 1.1, 1.9])
                        with c_chk:
                            chk_val = st.checkbox("", value=is_visited, key=f"chk_all_{d}_{item['id']}")
                            if chk_val != is_visited and idx_real is not None:
                                st.session_state.lugares[idx_real]["visitado"] = chk_val
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()

                        with c_info:
                            txt_c = "#334155" if is_visited else "#0F172A"
                            strike = "text-decoration: line-through; opacity: 0.8;" if is_visited else ""
                            tipo_badge = '<span class="badge-indoor" style="font-size:0.75rem; padding:1px 6px;">🌧️ Interior</span>' if item.get("tipo") == "Interior" else '<span class="badge-outdoor" style="font-size:0.75rem; padding:1px 6px;">☀️ Exterior</span>'
                            hora_html = f'<span class="badge-hora" style="font-size:0.78rem; padding:1px 8px; margin-right:6px;">🕒 {hora_i}</span>' if hora_i else ''
                            dir_html = f'<div style="font-size:0.84rem; color:#0F172A; font-weight:600; margin-top:2px;">📍 {dir_i}</div>' if dir_i else ''

                            st.markdown(f'''
                            <div style="{strike}">
                              {hora_html}<span style="font-weight:900; font-size:1rem; color:{txt_c};">#{seq_idx} · {emoji_i} {item['nombre']}</span>
                              <span class="badge-cat" style="font-size:0.75rem; padding:1px 8px; margin-left:6px;">{cat_i}</span>
                              {tipo_badge}
                            </div>
                            {dir_html}
                            ''', unsafe_allow_html=True)

                        with c_hora:
                            nueva_h = st.text_input(
                                "Hora",
                                value=hora_i,
                                placeholder="HH:MM",
                                key=f"hora_all_{d}_{item['id']}",
                                label_visibility="collapsed"
                            )
                            if nueva_h.strip() != hora_i and idx_real is not None:
                                st.session_state.lugares[idx_real]["hora"] = nueva_h.strip()
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()

                        with c_action:
                            col_act_a, col_act_b = st.columns([1.6, 1])
                            with col_act_a:
                                dest_d = st.selectbox(
                                    "",
                                    [f"Día {x}" for x in range(1, 11)] + ["Guardados"],
                                    index=d - 1,
                                    key=f"mvd_all_{d}_{item['id']}",
                                    label_visibility="collapsed"
                                )
                                val_dest = 0 if dest_d == "Guardados" else int(dest_d.replace("Día ", ""))
                                if val_dest != d and idx_real is not None:
                                    st.session_state.lugares[idx_real]["dia"] = val_dest
                                    guardar_itinerario_disco(st.session_state.lugares)
                                    st.rerun()
                            with col_act_b:
                                st.markdown(f'<a href="{gmaps_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; border-radius:9px; border:1.5px solid #94A3B8; background:#FFFFFF; color:#0F172A; font-weight:800; font-size:0.82rem; cursor:pointer;">🗺️ Maps</button></a>', unsafe_allow_html=True)

                        render_editor_sitio(item, f"it_all_{d}")
                        st.markdown('<div style="height:1px; background:#CBD5E1; margin:6px 0;"></div>', unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    else:
        dia_sel_t2 = st.selectbox(
            "Selecciona el día a planificar:",
            [f"Día {d}: {DIAS_VIAJE[d]['fecha']} ({DIAS_VIAJE[d]['dia']})" for d in range(1, 11)],
            key="dia_planner_tab2"
        )
        num_dia_t2 = int(re.search(r'Día (\d+):', dia_sel_t2).group(1))

        paradas_dia = sorted(
            [l for l in st.session_state.lugares if l.get("dia", 0) == num_dia_t2],
            key=clave_orden_hora
        )
        guardados_pool = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]

        col_it1, col_it2 = st.columns([3.5, 2])
        with col_it1:
            st.markdown(f"**{len(paradas_dia)} sitios asignados para esta jornada (ordenados por hora)**")
            if not paradas_dia:
                st.info(f"Aún no hay sitios para el Día {num_dia_t2}. Añade paradas desde la bandeja de guardados.")
            else:
                for seq_idx, item in enumerate(paradas_dia, 1):
                    idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
                    is_visited = item.get("visitado", False)
                    cat_i = normalizar_categoria(item.get("categoria", "📍 Otros"))
                    emoji_i = obtener_emoji_categoria(cat_i)
                    hora_i = item.get("hora", "")

                    with st.container():
                        c_chk, c_info, c_hora, c_move = st.columns([0.45, 3.6, 1.1, 1.6])
                        with c_chk:
                            chk_val = st.checkbox("", value=is_visited, key=f"chk_v_{item['id']}")
                            if chk_val != is_visited and idx_real is not None:
                                st.session_state.lugares[idx_real]["visitado"] = chk_val
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()
                        with c_info:
                            txt_color = "#334155" if is_visited else "#0F172A"
                            strike_style = "text-decoration: line-through; opacity: 0.8;" if is_visited else ""
                            item_dir = f" · 📍 {item['direccion']}" if item.get("direccion") else ""
                            hora_html = f'<span class="badge-hora" style="font-size:0.78rem; padding:1px 8px; margin-right:6px;">🕒 {hora_i}</span>' if hora_i else ''
                            st.markdown(f'''
                            <div style="{strike_style} font-weight:800; font-size:1rem; color:{txt_color};">
                              {hora_html}#{seq_idx} · {emoji_i} {item['nombre']}
                            </div>
                            <div style="font-size:0.84rem; color:#0F172A; font-weight:600;">
                              {cat_i} · {'🌧️ Interior' if item.get('tipo') == 'Interior' else '☀️ Exterior'}{item_dir}
                            </div>
                            ''', unsafe_allow_html=True)
                        with c_hora:
                            nueva_h2 = st.text_input(
                                "Hora",
                                value=hora_i,
                                placeholder="HH:MM",
                                key=f"hora_det_{item['id']}",
                                label_visibility="collapsed"
                            )
                            if nueva_h2.strip() != hora_i and idx_real is not None:
                                st.session_state.lugares[idx_real]["hora"] = nueva_h2.strip()
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()
                        with c_move:
                            dest_d = st.selectbox(
                                "",
                                [f"Día {x}" for x in range(1, 11)] + ["Guardados"],
                                index=num_dia_t2 - 1,
                                key=f"mvd_{item['id']}",
                                label_visibility="collapsed"
                            )
                            val_dest = 0 if dest_d == "Guardados" else int(dest_d.replace("Día ", ""))
                            if val_dest != num_dia_t2 and idx_real is not None:
                                st.session_state.lugares[idx_real]["dia"] = val_dest
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()
                        render_editor_sitio(item, "it_det")
                        st.markdown('<hr style="margin:4px 0; border-color:#CBD5E1;">', unsafe_allow_html=True)

        with col_it2:
            st.markdown(f"**Añadir a hoy desde Guardados ({len(guardados_pool)}):**")
            if not guardados_pool:
                st.caption("No tienes sitios pendientes en la bandeja.")
            else:
                for g_item in guardados_pool[:15]:
                    idx_g_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == g_item["id"]), None)
                    cat_g = normalizar_categoria(g_item.get("categoria", "📍 Otros"))
                    c_ga, c_gb = st.columns([4, 1.2])
                    with c_ga:
                        st.markdown(f'''
                        <div style="font-size:0.9rem; font-weight:800; color:#0F172A;">{obtener_emoji_categoria(cat_g)} {g_item['nombre']}</div>
                        <div style="font-size:0.8rem; color:#0F172A; font-weight:600;">{cat_g}</div>
                        ''', unsafe_allow_html=True)
                    with c_gb:
                        if st.button("➕", key=f"btn_add_to_day_{g_item['id']}", use_container_width=True):
                            if idx_g_real is not None:
                                st.session_state.lugares[idx_g_real]["dia"] = num_dia_t2
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS (AÑADIR NUEVO LUGAR & EDITAR CUALQUIER SITIO)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[2]:
    render_formulario_agregar_lugar("guardados")
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="ny-card-header">Lugares Guardados & Gestión de Sitios</div>', unsafe_allow_html=True)

    pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    cats_en_pool = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in pool_guardados))

    col_flt1, col_flt2 = st.columns([3, 1.5])
    with col_flt1:
        flt_cat_g = st.selectbox("Filtrar por categoría:", ["Todas"] + cats_en_pool, key="flt_pool_cat")
    with col_flt2:
        st.write("")
        st.write("")
        st.caption(f"Total en espera: **{len(pool_guardados)} sitios**")

    visibles_pool = [l for l in pool_guardados if flt_cat_g == "Todas" or normalizar_categoria(l.get("categoria")) == flt_cat_g]

    for p_spot in visibles_pool:
        idx_sp_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == p_spot["id"]), None)
        cat_p = normalizar_categoria(p_spot.get("categoria", "📍 Otros"))
        dir_p = p_spot.get("direccion", "")

        c_p1, c_p2, c_p3 = st.columns([4, 2.5, 1.2])
        with c_p1:
            st.markdown(f"""
            <div style="font-size:0.95rem; font-weight:700; color:#0F172A;">{obtener_emoji_categoria(cat_p)} {p_spot['nombre']}</div>
            <div style="font-size:0.8rem; color:#0F172A;">{cat_p} · {'🌧️ Interior' if p_spot.get('tipo') == 'Interior' else '☀️ Exterior'} {f'· 📍 {dir_p}' if dir_p else ''}</div>
            """, unsafe_allow_html=True)
        with c_p2:
            asig_dia = st.selectbox(
                "Mover a:",
                ["— Asignar a Día —"] + [f"Día {d} ({DIAS_VIAJE[d]['fecha']})" for d in range(1, 11)],
                key=f"asig_dia_pool_{p_spot['id']}",
                label_visibility="collapsed"
            )
            if asig_dia != "— Asignar a Día —" and idx_sp_real is not None:
                d_num = int(re.search(r'Día (\d+)', asig_dia).group(1))
                st.session_state.lugares[idx
