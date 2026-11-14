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
  /* ── Tipografía Calibri universal (con Carlito de Google Fonts para Linux / Streamlit Cloud) ── */
  @import url('https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&display=swap');

  html, body, [class*="css"], [class*="st-"], .stMarkdown, .stButton, button, input, select, textarea, div, p, span, h1, h2, h3, h4, h5, h6 {
    font-family: 'Calibri', 'Carlito', 'Segoe UI', Candara, -apple-system, BlinkMacSystemFont, Arial, sans-serif !important;
  }

  /* Fijar fondo y texto para evitar alteraciones de tema oscuro en móviles / Streamlit Cloud */
  .stApp {
    background-color: #F8F9FA !important;
    color: #0F172A !important;
  }
  html, body, [class*="css"] {
    background-color: #F8F9FA !important;
    color: #0F172A !important;
  }
  .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.5rem;
    max-width: 1320px;
  }

  /* ── Hero Banner Totalmente Blanco con Toques Navideños ── */
  .hero-container {
    background: #FFFFFF !important;
    border-radius: 20px;
    padding: 24px 28px;
    color: #0F172A !important;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    border: 1.5px solid #E2E8F0;
    border-top: 5px solid #15803D; /* Verde pino navideño */
  }
  .hero-eyebrow {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #15803D; /* Verde acebo / pino */
  }
  .hero-title {
    font-size: 2.3rem;
    font-weight: 700;
    margin: 4px 0 10px 0;
    color: #0F172A;
    letter-spacing: -0.5px;
  }
  .hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 30px;
    padding: 6px 14px;
    font-size: 0.85rem;
    color: #1E293B !important;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 5px;
  }
  .hero-stat-box {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px;
    padding: 10px 18px;
    text-align: center;
    min-width: 80px;
  }
  .hero-stat-val {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0F172A !important;
  }
  .hero-stat-lbl {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B !important;
  }

  /* ── Tarjetas Neutras Minimalistas ── */
  .ny-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  }
  .ny-card-header {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    color: #64748B;
    margin-bottom: 10px;
  }

  /* ── Ficha Detallada de Lugar (Place Sheet) ── */
  .place-sheet {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 18px;
    padding: 18px 22px;
    margin: 14px 0;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
    animation: fadeIn 0.2s ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ── Badges y Píldoras ── */
  .badge-cat {
    display: inline-block;
    background: #F1F5F9;
    color: #334155;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
  }
  .badge-indoor {
    display: inline-block;
    background: #EFF6FF;
    color: #1D4ED8;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 8px;
  }
  .badge-outdoor {
    display: inline-block;
    background: #ECFDF5;
    color: #047857;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 8px;
  }
  .badge-dia {
    display: inline-block;
    background: #FEF3C7;
    color: #B45309;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 8px;
  }

  /* ── Pestañas Streamlit Estilizadas ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #EDEFEA;
    padding: 5px;
    border-radius: 14px;
    border: 1px solid #E2E8F0;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
    padding: 8px 16px !important;
    border: none !important;
    background: transparent !important;
  }
  .stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
  }

  /* ── Botones Redondeados ── */
  .stButton > button {
    border-radius: 11px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    min-height: 40px;
    border: 1px solid #CBD5E1 !important;
    background: #FFFFFF !important;
    color: #1E293B !important;
    transition: all 0.15s ease-in-out !important;
  }
  .stButton > button:hover {
    background: #F8FAFC !important;
    border-color: #94A3B8 !important;
    transform: translateY(-1px);
  }

  /* ── Map iFrame ── */
  iframe {
    border-radius: 18px !important;
    border: 1px solid #CBD5E1 !important;
  }

  /* ── Inputs y Selectores ── */
  .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
    border-radius: 11px !important;
    border-color: #CBD5E1 !important;
    background: #FFFFFF !important;
    font-size: 0.9rem !important;
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
# 3. MOTOR INTELIGENTE DE CATEGORÍAS (REFINADO & EXACTO)
# =============================================================================
CATEGORIAS_CANONICAS = [
    "🍕 Gastronomía & Restaurantes",
    "🍪 Cafeterías & Dulces",
    "🍸 Rooftops & Copas",
    "🎷 Jazz, Música & Ocio",
    "🛍️ Compras & Outlets",
    "🏛️ Museos & Monumentos",
    "🏙️ Miradores & Observatorios",
    "🌲 Parques, Muelles & Puentes",
    "🏨 Hotel Base",
    "📍 Otros Lugares"
]

def clasificar_lugar(nombre: str, direccion: str = "", lista_origen: str = "") -> tuple[str, str]:
    """
    Clasifica de forma rigurosa e inteligente un sitio de Nueva York.
    Evita falsos positivos inspeccionando primero el nombre con reglas semánticas.
    """
    nom = (nombre or "").strip().lower()
    dir_l = (direccion or "").strip().lower()
    orig = (lista_origen or "").strip().lower()

    # 1. HOTEL BASE
    if ('hotel' in nom or 'inn' in nom or 'alojamiento' in nom) and any(k in nom for k in ['riu', 'marriott', 'hilton', 'hyatt', 'sheraton', 'base']):
        return "🏨 Hotel Base", "Interior"

    # 2. MIRADORES & OBSERVATORIOS
    if any(k in nom for k in ['summit', 'one vanderbilt', 'empire state', 'top of the rock', 'the edge', 'observatory', 'one world observatory']):
        return "🏙️ Miradores & Observatorios", "Interior"

    # 3. JAZZ, MÚSICA & ESPECTÁCULOS EN VIVO
    if any(k in nom for k in ['jazz', 'blue note', 'smalls', 'mezzrow', 'dizzy', "arthur's tavern", 'jazzcultural', 'village vanguard', 'broadway show', 'radio city', 'comedy cellar', 'lincoln center', 'teatro', 'theatre']):
        return "🎷 Jazz, Música & Ocio", "Interior"

    # 4. ROOFTOPS, BARES & COPAS
    if any(k in nom for k in ['rooftop', 'westlight', 'harriet', 'magic hour', '230 fifth', 'bar 54', 'hudson vu', 'buvette', 'dante', 'speakeasy', 'cocktail', 'wine bar', 'tavern', 'brewery', 'pub']) or ('bar' in nom.split() and 'shake' not in nom and 'salad' not in nom) or 'm social' in nom:
        return "🍸 Rooftops & Copas", "Interior"

    # 5. CAFETERÍAS, DULCES, HELADERÍAS & SWEETS
    if any(k in nom for k in ['bakery', 'cookie', 'cookies', 'levain', 'granny', 'caffè panna', 'caffe panna', 'krispy kreme', 'sweets', 'sweet', 'pastry', 'pâtisserie', 'donut', 'helado', 'ice cream', 'louis vuitton nyc', 'café', 'cafe', 'coffee', 'starbucks', 'magnolia', 'chocolate']):
        return "🍪 Cafeterías & Dulces", "Interior"

    # 6. COMPRAS & OUTLETS
    if any(k in nom for k in ['outlet', 'outlets', 'marshalls', 't.j. maxx', 'tj maxx', 'target', 'macy', 'burlington', 'century 21', 'five below', 'goodwill', 'woodbury', 'jersey gardens', 'grand slam', 'shopping', 'store', 'zara', 'uniqlo', 'tanger', 'apple store', 'sephora', 'nordstrom', 'bloomingdale']):
        return "🛍️ Compras & Outlets", "Interior"

    # 7. GASTRONOMÍA & RESTAURANTES
    if any(k in nom for k in ['pizza', 'pizzeria', 'burger', 'katz', 'dumpling', 'motek', 'piada', 'shake shack', 'chelsea market', 'time out market', 'deli', 'pastrami', 'tacos', 'taco', 'restaurant', 'trader joe', 'eataly', 'food hall', 'bagel', 'ramen', 'sushi', 'diner', 'smokehouse', 'noodle', 'food']):
        return "🍕 Gastronomía & Restaurantes", "Interior"

    # 8. PARQUES, MUELLES, PUENTES & EXTERIORES
    if any(k in nom for k in ['park', 'central park', 'bridge', 'puente', 'high line', 'little island', 'fulton ferry', 'domino', 'pier 17', 'pier 57', 'pier 35', 'pebble beach', 'tudor city', 'squibb', 'battery', 'waterfront', 'picnic', 'botanic', 'coney island', 'boardwalk']):
        return "🌲 Parques, Muelles & Puentes", "Exterior"

    # 9. MUSEOS & MONUMENTOS
    if any(k in nom for k in ['museum', 'the met', 'moma', 'morgan library', 'tenement', '9/11 memorial', 'oculus', 'grand central', 'library', 'atlas', 'one times square', 'times square', 'memorial', 'statue of liberty', 'trinity church', 'rockefeller center', 'st. patrick']):
        tipo = "Exterior" if any(x in nom for x in ['times square', 'atlas', 'statue']) else "Interior"
        return "🏛️ Museos & Monumentos", tipo

    # 10. INFERENCIA POR LISTA DE GOOGLE MAPS DE ORIGEN
    if 'sweet' in orig:
        return "🍪 Cafeterías & Dulces", "Interior"
    if 'food' in orig:
        return "🍕 Gastronomía & Restaurantes", "Interior"
    if 'rooftop' in orig:
        return "🍸 Rooftops & Copas", "Interior"
    if 'tienda' in orig or 'outlet' in orig:
        return "🛍️ Compras & Outlets", "Interior"
    if 'spot' in orig:
        return "🌲 Parques, Muelles & Puentes", "Exterior"

    return "📍 Otros Lugares", "Interior"

def obtener_emoji_categoria(cat: str) -> str:
    """Extrae el emoji visual de la categoría canónica."""
    for ch in cat:
        if ord(ch) > 127:
            return ch
    return "📍"

def crear_pin_google_maps(categoria: str, nombre: str = ""):
    """Crea el pin circular blanco idéntico al estilo de Google Maps de la captura."""
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


# =============================================================================
# 4. APIs EXTERNAS: CAMBIO DE MONEDA & OPEN-METEO EN TIEMPO REAL
# =============================================================================
@st.cache_data(ttl=3600)
def obtener_tasa_usd_eur():
    """Consulta la tasa en vivo USD -> EUR (API gratuita sin keys)."""
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
    """Consulta el tiempo actual y la previsión oficial en Manhattan vía Open-Meteo."""
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
    """Traduce el código WMO a texto y emoji."""
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
                return json.load(f)
        except Exception:
            pass
    return []

def guardar_itinerario_disco(lugares):
    try:
        with open(ARCH_ITINERARIO, "w", encoding="utf-8") as f:
            json.dump(lugares, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def recalcular_todas_las_categorias(lugares):
    """Reclasifica todos los lugares de la app con el motor estricto."""
    for p in lugares:
        cat, tipo = clasificar_lugar(p.get("nombre", ""), p.get("direccion", ""))
        p["categoria"] = cat
        p["tipo"] = tipo
    guardar_itinerario_disco(lugares)
    return lugares


# =============================================================================
# 6. SINCRONIZADOR DE LISTAS DE GOOGLE MAPS
# =============================================================================
def extraer_lugares_lista_gmaps(url_lista: str, nombre_lista: str = ""):
    """Extrae sitios de un enlace compartido de Google Maps y los clasifica."""
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
        
        entity_url = "https://www.google.com" + m.group(1).replace("&amp;", "&")
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
                            "tipo": tipo
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


# =============================================================================
# 6B. HERRAMIENTAS PARA AÑADIR LUGARES (GOOGLE MAPS O INTRODUCCIÓN A MANO)
# =============================================================================
def geocodificar_direccion_o_nombre(texto: str) -> tuple:
    """Geocodifica un nombre o dirección en Nueva York mediante Nominatim."""
    if not texto:
        return None, None, ""
    q = f"{texto}, New York, NY".strip()
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'ny_holiday_planner_app_v2'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            res = json.loads(r.read().decode('utf-8'))
            if res and len(res) > 0:
                lat = float(res[0]['lat'])
                lon = float(res[0]['lon'])
                nombre_comp = res[0].get('display_name', '')
                return lat, lon, nombre_comp
    except Exception:
        pass
    return None, None, ""

def agregar_sitio_a_lugares(nombre: str, direccion: str = "", lat: float = None, lon: float = None,
                            categoria: str = None, tipo: str = None, dia_dest: int = 0) -> tuple:
    """Añade un lugar manual o geocodificado al itinerario y lo persiste."""
    nom = (nombre or "").strip()
    if not nom:
        return False, "El nombre del lugar no puede estar vacío."

    # Si no se aportaron coordenadas válidas, geocodificar automáticamente en NYC
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
        "direccion": direccion,
        "categoria": categoria,
        "tipo": tipo,
        "visitado": False
    }
    st.session_state.lugares.append(nuevo)
    guardar_itinerario_disco(st.session_state.lugares)
    return True, f"¡'{nom}' añadido con éxito como {categoria}!"

def importar_sitio_desde_gmaps(url_o_texto: str, dia_dest: int = 0) -> tuple:
    """Extrae y añade sitios desde cualquier enlace de Google Maps (lugar individual o lista compartida)."""
    raw = url_o_texto.strip()
    if not raw:
        return False, "Introduce un enlace de Google Maps válido."

    # Caso 1: Enlace a lista compartida de Google Maps
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
                    s["visitado"] = False
                    st.session_state.lugares.append(s)
                    nuevos += 1
            if nuevos > 0:
                guardar_itinerario_disco(st.session_state.lugares)
                return True, f"¡Se importaron {nuevos} lugares desde la lista de Google Maps!"

    # Caso 2: Enlace a lugar individual de Google Maps
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

    return agregar_sitio_a_lugares(nombre_extraido, dir_ext, lat_ext, lon_ext, None, None, dia_dest)

def render_formulario_agregar_lugar(key_sufijo: str = "gen"):
    """Renderiza el módulo para añadir sitios desde Google Maps o a mano."""
    with st.expander("➕ Añadir Nuevo Lugar (desde Google Maps o a Mano)", expanded=False):
        tab_gm, tab_man = st.tabs(["🌐 Enlace de Google Maps", "✏️ Introducir a Mano"])

        with tab_gm:
            st.caption("Pega el enlace de Google Maps de un sitio o lista para importarlo al viaje:")
            with st.form(f"form_add_gm_{key_sufijo}"):
                url_input = st.text_input("Enlace de Google Maps (maps.app.goo.gl/... o google.com/maps/place/...):", placeholder="https://maps.app.goo.gl/...", key=f"inp_gm_{key_sufijo}")
                dias_asig_opts = ["📌 Bandeja de Guardados"] + [f"Día {d} ({DIAS_VIAJE[d]['fecha']})" for d in range(1, 11)]
                dia_dest_gm = st.selectbox("Asignar a:", dias_asig_opts, key=f"sel_dia_gm_{key_sufijo}")
                val_dia_gm = 0 if "Bandeja" in dia_dest_gm else int(re.search(r'Día (\d+)', dia_dest_gm).group(1))

                if st.form_submit_button("📥 Importar desde Google Maps", use_container_width=True):
                    if url_input:
                        with st.spinner("Analizando y geolocalizando sitio en Nueva York..."):
                            ok, msg = importar_sitio_desde_gmaps(url_input, val_dia_gm)
                            if ok:
                                st.toast(msg, icon="📍")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("Por favor introduce una URL de Google Maps.")

        with tab_man:
            st.caption("Escribe el nombre del lugar. Si dejas las coordenadas vacías, se buscarán automáticamente:")
            with st.form(f"form_add_man_{key_sufijo}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    nom_m = st.text_input("Nombre del lugar:", placeholder="Ej: Levain Bakery, Joe's Pizza, Dante...", key=f"nom_m_{key_sufijo}")
                    dir_m = st.text_input("Dirección o Barrio (opcional):", placeholder="Ej: Upper West Side, West Village...", key=f"dir_m_{key_sufijo}")
                with c_m2:
                    cat_m = st.selectbox("Categoría:", ["⚡ Detección Automática"] + CATEGORIAS_CANONICAS, key=f"cat_m_{key_sufijo}")
                    tipo_m = st.selectbox("Tipo:", ["Interior (🌧️ A cubierto)", "Exterior (☀️ Al aire libre)"], key=f"tipo_m_{key_sufijo}")

                c_m3, c_m4 = st.columns(2)
                with c_m3:
                    dia_dest_m = st.selectbox("Asignar a:", dias_asig_opts, key=f"sel_dia_m_{key_sufijo}")
                    val_dia_m = 0 if "Bandeja" in dia_dest_m else int(re.search(r'Día (\d+)', dia_dest_m).group(1))
                with c_m4:
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
                            t_val = "Interior" if "Interior" in tipo_m else "Exterior"
                            c_val = None if cat_m == "⚡ Detección Automática" else cat_m
                            ok, msg = agregar_sitio_a_lugares(nom_m, dir_m, lat_man, lon_man, c_val, t_val, val_dia_m)
                            if ok:
                                st.toast(msg, icon="✨")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("Introduce al menos el nombre del lugar.")


# =============================================================================
# 7. INICIALIZACIÓN DE ESTADO
# =============================================================================
if "config_viaje" not in st.session_state:
    st.session_state.config_viaje = cargar_config_viaje()

if "lugares" not in st.session_state or not st.session_state.lugares:
    c_lugares = cargar_itinerario_disco()
    st.session_state.lugares = c_lugares

if "lugar_activo_id" not in st.session_state:
    st.session_state.lugar_activo_id = None


# =============================================================================
# 8. CABECERA HERO EDITORIAL NAVIDEÑA (FONDO BLANCO & CALIBRI)
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
# TAB 1: MAPA GOOGLE CON PINES CIRCULARES Y APERTURA DE FICHA REAL
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[0]:
    render_formulario_agregar_lugar("mapa")
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    c_m1, c_m2, c_m3 = st.columns([3, 2, 2])
    with c_m1:
        opciones_vista = [
            "🌐 Todos los Sitios (Itinerario + Guardados + Hotel)",
            "📅 Solo Sitios en Itinerario (Días 1 a 10)",
            "🏨 Solo Hotel Base"
        ] + [f"Día {d}: {DIAS_VIAJE[d]['fecha']} - {DIAS_VIAJE[d]['titulo']}" for d in range(1, 11)]
        sel_vista = st.selectbox("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    with c_m2:
        sel_capa = st.selectbox(
            "Capa:",
            ["Google Maps Callejero", "Google Maps Satélite / Híbrido", "Google Maps Terreno", "OpenStreetMap"],
            label_visibility="collapsed"
        )
    with c_m3:
        cats_actuales = sorted(set(l.get("categoria", "📍 Otros Lugares") for l in st.session_state.lugares))
        sel_filtro_cat = st.selectbox("Categoría:", ["Todas"] + cats_actuales, label_visibility="collapsed")

    # Filtrar lugares según selección
    if "Todos" in sel_vista:
        sitios_mapa = list(st.session_state.lugares)
    elif "Solo Sitios en Itinerario" in sel_vista:
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    elif "Solo Hotel" in sel_vista:
        sitios_mapa = []
    else:
        m_dia = re.search(r'Día (\d+):', sel_vista)
        num_d = int(m_dia.group(1)) if m_dia else 1
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) == num_d]

    if sel_filtro_cat != "Todas":
        sitios_mapa = [l for l in sitios_mapa if l.get("categoria") == sel_filtro_cat]

    # Centro del mapa
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

    # 1. PIN DEL HOTEL BASE
    pop_hotel_html = f"""
    <div style="font-family: -apple-system, sans-serif; min-width: 210px; padding: 4px;">
      <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">🏨 TU HOTEL BASE</span>
      <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin: 6px 0 2px;">{h_nom}</div>
      <div style="font-size: 12px; color: #475569;">📍 {h_dir}</div>
    </div>
    """
    folium.Marker(
        location=[h_lat, h_lon],
        popup=folium.Popup(pop_hotel_html, max_width=260),
        tooltip=f"🏨 {h_nom}",
        icon=crear_pin_google_maps("🏨 Hotel Base", h_nom)
    ).add_to(mapa)

    # 2. PINES DE LUGARES
    coords_ruta = []
    for s in sitios_mapa:
        pt = (s["lat"], s["lon"])
        if s.get("dia", 0) > 0:
            coords_ruta.append(pt)

        cat_spot = s.get("categoria", "📍 Otros Lugares")
        tipo_spot = s.get("tipo", "Interior")
        dia_spot = s.get("dia", 0)
        dir_spot = s.get("direccion", "")
        nom_spot = s.get("nombre", "Lugar")

        dia_txt = f"Día {dia_spot} ({DIAS_VIAJE.get(dia_spot, {}).get('fecha', '')})" if dia_spot > 0 else "📌 En Guardados"
        tipo_badge = "🌧️ Interior" if tipo_spot == "Interior" else "☀️ Exterior"

        g_search = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(nom_spot + ' New York')}"
        g_route  = f"https://www.google.com/maps/dir/?api=1&origin={h_lat},{h_lon}&destination={s['lat']},{s['lon']}"

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 230px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 11px; font-weight: 800; color: #2563EB;">{dia_txt}</span>
            <span style="font-size: 10px; font-weight: 700; background: #F1F5F9; color: #475569; padding: 2px 6px; border-radius: 6px;">{tipo_badge}</span>
          </div>
          <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-bottom: 3px;">{obtener_emoji_categoria(cat_spot)} {nom_spot}</div>
          {f'<div style="font-size: 12px; color: #64748B; margin-bottom: 6px;">📍 {dir_spot}</div>' if dir_spot else ''}
          <div style="font-size: 11px; color: #475569; margin-bottom: 8px;"><b>Categoría:</b> {cat_spot}</div>
          <div style="display: flex; gap: 6px;">
            <a href="{g_search}" target="_blank" style="flex:1; text-align:center; background:#1A73E8; color:white; padding:7px 4px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Abrir en Maps →</a>
            <a href="{g_route}" target="_blank" style="text-align:center; background:#F8FAFC; border:1px solid #CBD5E1; color:#0F172A; padding:7px 8px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">🧭 Ruta</a>
          </div>
        </div>
        """

        folium.Marker(
            location=pt,
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f"{obtener_emoji_categoria(cat_spot)} {nom_spot}",
            icon=crear_pin_google_maps(cat_spot, nom_spot)
        ).add_to(mapa)

    if len(coords_ruta) > 1 and "Día " in sel_vista:
        folium.PolyLine(coords_ruta, color="#1A73E8", weight=3.5, opacity=0.8, dash_array="6, 8").add_to(mapa)

    # Render del mapa con captura de clic
    resultado_mapa = st_folium(
        mapa,
        use_container_width=True,
        height=520,
        returned_objects=["last_object_clicked"]
    )

    # Detección de clic para abrir ficha
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

    # Ficha del lugar abierto
    if st.session_state.lugar_activo_id is not None:
        idx_p = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == st.session_state.lugar_activo_id), None)
        if idx_p is not None:
            sp = st.session_state.lugares[idx_p]
            cat_sp = sp.get("categoria", "📍 Otros Lugares")
            tipo_sp = sp.get("tipo", "Interior")
            dir_sp = sp.get("direccion", "")
            dia_sp = sp.get("dia", 0)

            st.markdown(f"""
            <div class="place-sheet">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                  <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
                    <span class="badge-dia">{f"Día {dia_sp} ({DIAS_VIAJE.get(dia_sp, {}).get('fecha', '')})" if dia_sp > 0 else "📌 En Guardados"}</span>
                    <span class="{'badge-indoor' if tipo_sp == 'Interior' else 'badge-outdoor'}">{'🌧️ A cubierto' if tipo_sp == 'Interior' else '☀️ Al aire libre'}</span>
                    <span class="badge-cat">{cat_sp}</span>
                  </div>
                  <h2 style="margin:2px 0 4px 0; font-size:1.35rem; color:#0F172A;">{obtener_emoji_categoria(cat_sp)} {sp['nombre']}</h2>
                  {f'<div style="font-size:0.88rem; color:#64748B;">📍 {dir_sp}</div>' if dir_sp else ''}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c_act1, c_act2, c_act3, c_act4 = st.columns([2, 1.8, 1.8, 1])
            with c_act1:
                g_direct = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(sp['nombre'] + ' New York')}"
                st.link_button("🌐 Abrir en Google Maps", g_direct, use_container_width=True)
            with c_act2:
                # Selector de cambio de día
                opciones_dias = ["Bandeja de Guardados"] + [f"Día {d} ({DIAS_VIAJE[d]['fecha']})" for d in range(1, 11)]
                idx_dia_act = dia_sp if dia_sp > 0 else 0
                sel_n_dia = st.selectbox("Asignar a Día:", opciones_dias, index=idx_dia_act, key=f"sel_d_sheet_{sp['id']}")
                n_dia_val = 0 if "Bandeja" in sel_n_dia else int(re.search(r'Día (\d+)', sel_n_dia).group(1))
                if n_dia_val != dia_sp:
                    st.session_state.lugares[idx_p]["dia"] = n_dia_val
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()
            with c_act3:
                # Modificar categoría directamente si el usuario quiere ajustarla
                idx_cat = CATEGORIAS_CANONICAS.index(cat_sp) if cat_sp in CATEGORIAS_CANONICAS else 0
                sel_n_cat = st.selectbox("Categoría:", CATEGORIAS_CANONICAS, index=idx_cat, key=f"sel_cat_sheet_{sp['id']}")
                if sel_n_cat != cat_sp:
                    st.session_state.lugares[idx_p]["categoria"] = sel_n_cat
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()
            with c_act4:
                if st.button("✕ Cerrar", key="close_place_sheet", use_container_width=True):
                    st.session_state.lugar_activo_id = None
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO CRONOLÓGICO (10 DÍAS)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[1]:
    st.markdown('<div class="ny-card-header">Cronograma Diario de Actividades</div>', unsafe_allow_html=True)

    dia_sel_t2 = st.selectbox(
        "Selecciona el día a planificar:",
        [f"Día {d}: {DIAS_VIAJE[d]['fecha']} ({DIAS_VIAJE[d]['dia']}) — {DIAS_VIAJE[d]['titulo']}" for d in range(1, 11)],
        key="dia_planner_tab2"
    )
    num_dia_t2 = int(re.search(r'Día (\d+):', dia_sel_t2).group(1))
    
    paradas_dia = [l for l in st.session_state.lugares if l.get("dia", 0) == num_dia_t2]
    guardados_pool = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]

    col_it1, col_it2 = st.columns([3.5, 2])
    with col_it1:
        st.markdown(f"**{len(paradas_dia)} sitios asignados para esta jornada**")
        if not paradas_dia:
            st.info(f"Aún no hay sitios para el Día {num_dia_t2}. Añade paradas desde tu bandeja de guardados a la derecha.")
        else:
            for seq_idx, item in enumerate(paradas_dia, 1):
                idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
                is_visited = item.get("visitado", False)
                cat_i = item.get("categoria", "📍 Otros Lugares")
                emoji_i = obtener_emoji_categoria(cat_i)

                with st.container():
                    c_chk, c_info, c_move = st.columns([0.5, 4.5, 1.8])
                    with c_chk:
                        chk_val = st.checkbox("", value=is_visited, key=f"chk_v_{item['id']}")
                        if chk_val != is_visited and idx_real is not None:
                            st.session_state.lugares[idx_real]["visitado"] = chk_val
                            guardar_itinerario_disco(st.session_state.lugares)
                            st.rerun()
                    with c_info:
                        txt_color = "#94A3B8" if is_visited else "#0F172A"
                        strike_style = "text-decoration: line-through;" if is_visited else ""
                        item_dir = f" · 📍 {item['direccion']}" if item.get("direccion") else ""
                        st.markdown(f"""
                        <div style="{strike_style} font-weight:700; font-size:1rem; color:{txt_color};">
                          #{seq_idx} · {emoji_i} {item['nombre']}
                        </div>
                        <div style="font-size:0.8rem; color:#64748B;">
                          {cat_i} · {'🌧️ Interior' if item.get('tipo') == 'Interior' else '☀️ Exterior'}{item_dir}
                        </div>
                        """, unsafe_allow_html=True)
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
                    st.markdown('<hr style="margin:4px 0; border-color:#F1F5F9;">', unsafe_allow_html=True)

    with col_it2:
        st.markdown(f"**Añadir a hoy desde Guardados ({len(guardados_pool)}):**")
        if not guardados_pool:
            st.caption("No tienes sitios pendientes en la bandeja.")
        else:
            for g_item in guardados_pool[:12]:
                idx_g_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == g_item["id"]), None)
                cat_g = g_item.get("categoria", "📍 Otros Lugares")
                c_ga, c_gb = st.columns([4, 1.2])
                with c_ga:
                    st.markdown(f"""
                    <div style="font-size:0.88rem; font-weight:600; color:#1E293B;">{obtener_emoji_categoria(cat_g)} {g_item['nombre']}</div>
                    <div style="font-size:0.75rem; color:#64748B;">{cat_g}</div>
                    """, unsafe_allow_html=True)
                with c_gb:
                    if st.button("➕", key=f"btn_add_to_day_{g_item['id']}", use_container_width=True):
                        if idx_g_real is not None:
                            st.session_state.lugares[idx_g_real]["dia"] = num_dia_t2
                            guardar_itinerario_disco(st.session_state.lugares)
                            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS (WISHLIST)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[2]:
    render_formulario_agregar_lugar("guardados")
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="ny-card-header">Lugares Pendientes de Asignar a un Día</div>', unsafe_allow_html=True)

    pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    cats_en_pool = sorted(set(l.get("categoria", "📍 Otros Lugares") for l in pool_guardados))

    col_flt1, col_flt2 = st.columns([3, 1.5])
    with col_flt1:
        flt_cat_g = st.selectbox("Filtrar por categoría:", ["Todas"] + cats_en_pool, key="flt_pool_cat")
    with col_flt2:
        st.write("")
        st.write("")
        st.caption(f"Total en espera: **{len(pool_guardados)} sitios**")

    visibles_pool = [l for l in pool_guardados if flt_cat_g == "Todas" or l.get("categoria") == flt_cat_g]

    for p_spot in visibles_pool:
        idx_sp_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == p_spot["id"]), None)
        cat_p = p_spot.get("categoria", "📍 Otros Lugares")
        dir_p = p_spot.get("direccion", "")
        
        c_p1, c_p2, c_p3 = st.columns([4, 2.5, 1.2])
        with c_p1:
            st.markdown(f"""
            <div style="font-size:0.95rem; font-weight:700; color:#0F172A;">{obtener_emoji_categoria(cat_p)} {p_spot['nombre']}</div>
            <div style="font-size:0.8rem; color:#64748B;">{cat_p} · {'🌧️ Interior' if p_spot.get('tipo') == 'Interior' else '☀️ Exterior'} {f'· 📍 {dir_p}' if dir_p else ''}</div>
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
                st.session_state.lugares[idx_sp_real]["dia"] = d_num
                guardar_itinerario_disco(st.session_state.lugares)
                st.rerun()
        with c_p3:
            g_url_sp = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p_spot['nombre'] + ' New York')}"
            st.markdown(f"""
            <a href="{g_url_sp}" target="_blank" style="display:block; text-align:center; background:#F8FAFC; border:1px solid #CBD5E1; color:#0F172A; border-radius:8px; padding:6px; font-size:11px; font-weight:700; text-decoration:none; margin-top:2px;">Maps ↗</a>
            """, unsafe_allow_html=True)
        st.markdown('<hr style="margin:5px 0; border-color:#F1F5F9;">', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: MODO LLUVIA & CLIMA EN TIEMPO REAL
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[3]:
    st.markdown('<div class="ny-card-header">🌧️ Consulta Meteorológica en Tiempo Real & Sustituciones</div>', unsafe_allow_html=True)

    clima_data = consultar_clima_nyc()

    col_w_curr, col_w_day = st.columns([2.5, 3])

    with col_w_curr:
        st.markdown("#### 📍 Manhattan Ahora Mismo")
        if clima_data and "current" in clima_data:
            cur = clima_data["current"]
            temp_c = cur.get("temperature_2m", 5.0)
            sens_c = cur.get("apparent_temperature", 3.0)
            precip = cur.get("precipitation", 0.0)
            w_code = cur.get("weather_code", 0)
            desc_clima, tipo_clima = traducir_codigo_clima(w_code)
            
            st.markdown(f"""
            <div class="ny-card" style="border-left: 5px solid {'#3B82F6' if precip > 0 else '#10B981'};">
              <div style="font-size:1.8rem; font-weight:800; color:#0F172A;">{temp_c:.1f} °C</div>
              <div style="font-size:0.9rem; font-weight:600; color:#475569;">{desc_clima}</div>
              <div style="font-size:0.8rem; color:#64748B; margin-top:6px;">
                Sensación térmica: <b>{sens_c:.1f} °C</b> · Humedad: <b>{cur.get('relative_humidity_2m', 60)}%</b><br>
                Precipitación en vivo: <b>{precip:.1f} mm</b>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Conectando con la estación meteorológica de Nueva York...")

    with col_w_day:
        st.markdown("#### 🗓️ Pronóstico para tu Día de Viaje")
        dia_sel_clima = st.selectbox(
            "Selecciona el día a comprobar:",
            [f"Día {d}: {DIAS_VIAJE[d]['fecha']} ({DIAS_VIAJE[d]['dia']})" for d in range(1, 11)],
            key="sel_dia_clima"
        )
        num_dia_c = int(re.search(r'Día (\d+):', dia_sel_clima).group(1))

        # Evaluación meteorológica
        prob_lluvia = 15
        precip_mm = 0.0
        temp_max_est, temp_min_est = 6.0, -1.0
        desc_dia = "☀️ Día despejado y fresco"
        alerta_lluvia = False

        if clima_data and "daily" in clima_data:
            d_time = clima_data["daily"].get("time", [])
            idx_pronostico = (num_dia_c - 1) if (num_dia_c - 1) < len(d_time) else 0
            if idx_pronostico < len(d_time):
                p_code = clima_data["daily"]["weather_code"][idx_pronostico]
                desc_dia, _ = traducir_codigo_clima(p_code)
                prob_lluvia = clima_data["daily"]["precipitation_probability_max"][idx_pronostico] or 0
                precip_mm = clima_data["daily"]["precipitation_sum"][idx_pronostico] or 0.0
                temp_max_est = clima_data["daily"]["temperature_2m_max"][idx_pronostico] or 5.0
                temp_min_est = clima_data["daily"]["temperature_2m_min"][idx_pronostico] or -1.0
                alerta_lluvia = (prob_lluvia >= 40) or (precip_mm > 1.0) or ("Lluvia" in desc_dia) or ("Nieve" in desc_dia)

        color_card = "#FEF2F2" if alerta_lluvia else "#F0FDF4"
        border_card = "#EF4444" if alerta_lluvia else "#10B981"
        st.markdown(f"""
        <div style="background:{color_card}; border: 1.5px solid {border_card}; border-radius:14px; padding:14px 18px;">
          <div style="font-weight:800; font-size:1.1rem; color:#0F172A;">Día {num_dia_c} ({DIAS_VIAJE[num_dia_c]['fecha']}) · {desc_dia}</div>
          <div style="font-size:0.85rem; color:#334155; margin-top:4px;">
            🌡️ Temperaturas: <b>{temp_min_est:.0f} °C a {temp_max_est:.0f} °C</b><br>
            🌧️ Probabilidad de Precipitación: <b>{prob_lluvia}%</b> ({precip_mm:.1f} mm)
          </div>
          <div style="font-size:0.8rem; font-weight:700; color:{'#B91C1C' if alerta_lluvia else '#047857'}; margin-top:6px;">
            {'⚠️ ALERTA DE LLUVIA / NIEVE: Recomendable activar sustituciones a cubierto' if alerta_lluvia else '✓ Tiempo favorable para paseos al aire libre'}
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔄 Sustituciones Inteligentes por Cercanía")
    st.caption("Intercambia con 1 clic cualquier plan al aire libre por los sitios a cubierto más cercanos de tu lista:")

    planes_ext_dia = [l for l in st.session_state.lugares if l.get("dia", 0) == num_dia_c and l.get("tipo") == "Exterior"]
    lugares_indoor = [l for l in st.session_state.lugares if l.get("tipo") == "Interior"]

    if not planes_ext_dia:
        st.success(f"🎉 No hay paradas al aire libre programadas en el Día {num_dia_c}. ¡Todo el día está a cubierto!")
    else:
        for spot_ext in planes_ext_dia:
            # Calcular distancias euclidianas convertidas a km
            distancias = []
            for ind in lugares_indoor:
                if ind["id"] != spot_ext["id"]:
                    km = math.hypot(ind["lat"] - spot_ext["lat"], ind["lon"] - spot_ext["lon"]) * 111.0
                    distancias.append((km, ind))
            distancias.sort(key=lambda x: x[0])
            top_cercanos = distancias[:5]

            dir_ext_txt = f" · 📍 {spot_ext['direccion']}" if spot_ext.get("direccion") else ""
            st.markdown(f"""
            <div style="background:#FFF5F5; border-left:4px solid #EF4444; border-radius:12px; padding:12px 16px; margin: 8px 0;">
              <div style="font-weight:700; color:#991B1B;">{obtener_emoji_categoria(spot_ext.get('categoria',''))} {spot_ext['nombre']}</div>
              <div style="font-size:0.8rem; color:#7F1D1D;">Plan exterior programado para el Día {num_dia_c}{dir_ext_txt}</div>
            </div>
            """, unsafe_allow_html=True)

            c_sust1, c_sust2 = st.columns([3.5, 1.2])
            with c_sust1:
                opciones_cercanas = [f"{x['nombre']} (a {d:.1f} km) — {x.get('categoria','')}" for d, x in top_cercanos]
                sel_sust = st.selectbox("Sustituto a cubierto más cercano:", opciones_cercanas, key=f"sel_sust_{spot_ext['id']}", label_visibility="collapsed")
            with c_sust2:
                if st.button("🔄 Intercambiar", key=f"btn_swap_{spot_ext['id']}", use_container_width=True):
                    nom_sust = sel_sust.split(" (a ")[0].strip()
                    elegido = next(x for _, x in top_cercanos if x["nombre"] == nom_sust)
                    
                    idx_ext = next(i for i, x in enumerate(st.session_state.lugares) if x["id"] == spot_ext["id"])
                    idx_ind = next(i for i, x in enumerate(st.session_state.lugares) if x["id"] == elegido["id"])
                    
                    st.session_state.lugares[idx_ext]["dia"] = 0
                    st.session_state.lugares[idx_ind]["dia"] = num_dia_c
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.toast(f"¡'{elegido['nombre']}' ahora está en el Día {num_dia_c}!", icon="✨")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: DIVISAS EN TIEMPO REAL & CALCULADORA TAX Y PROPINAS NY
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[4]:
    st.markdown('<div class="ny-card-header">💵 Cambio de Moneda en Vivo & Calculadora Oficial NY</div>', unsafe_allow_html=True)

    tasa_eur, fecha_tasa = obtener_tasa_usd_eur()

    col_fx, col_tax = st.columns([2.5, 3])

    with col_fx:
        st.markdown("#### 💱 Conversor de Divisas en Tiempo Real")
        st.markdown(f"""
        <div style="background:#F1F5F9; border-radius:12px; padding:10px 14px; margin-bottom:14px; font-size:0.85rem; color:#334155;">
          Tasa de cambio actual: <b>1 USD = {tasa_eur:.4f} EUR</b><br>
          <span style="font-size:0.75rem; color:#64748B;">Actualizado: {fecha_tasa}</span>
        </div>
        """, unsafe_allow_html=True)

        modo_fx = st.radio("Convertir:", ["USD a EUR ($ ➔ €)", "EUR a USD (€ ➔ $)"], horizontal=True)
        if "USD a EUR" in modo_fx:
            val_usd = st.number_input("Cantidad en Dólares ($):", min_value=0.0, value=50.0, step=5.0)
            res_eur = val_usd * tasa_eur
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:14px; padding:16px; text-align:center; margin-top:10px;">
              <div style="font-size:0.85rem; color:#64748B;">Equivalente en Euros:</div>
              <div style="font-size:2rem; font-weight:800; color:#0F172A;">{res_eur:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            val_eur = st.number_input("Cantidad en Euros (€):", min_value=0.0, value=50.0, step=5.0)
            res_usd = val_eur / tasa_eur if tasa_eur > 0 else 0
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:14px; padding:16px; text-align:center; margin-top:10px;">
              <div style="font-size:0.85rem; color:#64748B;">Equivalente en Dólares:</div>
              <div style="font-size:2rem; font-weight:800; color:#0F172A;">${res_usd:.2f} USD</div>
            </div>
            """, unsafe_allow_html=True)

    with col_tax:
        st.markdown("#### 🧾 Calculadora de Cuenta, Impuestos & Propinas de NY")

        subtotal_bill = st.number_input("Subtotal de la cuenta ($ USD):", min_value=0.0, value=65.0, step=5.0)
        es_ropa_exenta = st.checkbox("👕 Prenda de ropa o calzado < $110 (Exenta de Sales Tax en NYC)")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            pct_propina = st.radio("Porcentaje de Propina (Tip):", [15, 18, 20, 22, 25], index=2, horizontal=True)
        with col_t2:
            base_calc = st.radio("Calcular propina sobre:", ["Subtotal sin tax", "Total con tax"])

        # Cálculos oficiales de Nueva York
        tax_rate = 0.0 if es_ropa_exenta else 0.08875
        tax_total = subtotal_bill * tax_rate
        base_tip = subtotal_bill if "Subtotal" in base_calc else (subtotal_bill + tax_total)
        tip_total = base_tip * (pct_propina / 100.0)
        gran_total = subtotal_bill + tax_total + tip_total
        gran_total_eur = gran_total * tasa_eur

        st.markdown(f"""
        <div class="ny-card" style="margin-top:12px; border: 1.5px solid #E2E8F0;">
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.9rem;">
            <span style="color:#64748B;">Subtotal carta:</span>
            <b>${subtotal_bill:.2f}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.9rem;">
            <span style="color:#64748B;">NYC Sales Tax ({'Exenta' if es_ropa_exenta else '8.875%'}):</span>
            <b>{'Exenta ($0.00)' if es_ropa_exenta else f'${tax_total:.2f}'}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.9rem;">
            <span style="color:#64748B;">Propina ({pct_propina}%):</span>
            <b>${tip_total:.2f}</b>
          </div>
          <div style="border-top:1.5px solid #E2E8F0; padding-top:10px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.1rem; font-weight:800; color:#0F172A;">Total a Pagar:</span>
            <div style="text-align:right;">
              <span style="font-size:1.45rem; font-weight:800; color:#0F172A;">${gran_total:.2f} USD</span><br>
              <span style="font-size:0.85rem; color:#64748B;">≈ {gran_total_eur:.2f} €</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        num_personas = st.slider("Dividir entre comensales:", min_value=1, max_value=8, value=2)
        if num_personas > 1:
            per_p_usd = gran_total / num_personas
            per_p_eur = gran_total_eur / num_personas
            st.info(f"👉 **Por persona ({num_personas} pers):** **${per_p_usd:.2f} USD** (~ {per_p_eur:.2f} €)")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: VUELOS, HOTEL & LISTAS DE GOOGLE MAPS
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[5]:
    c_vl1, c_vl2 = st.columns(2)

    with c_vl1:
        st.markdown('<div class="ny-card-header">✈️ Vuelos Confirmados</div>', unsafe_allow_html=True)
        with st.form("form_editar_vuelos"):
            ida_v = st.text_input("Vuelo Ida:", value=v_ida.get("vuelo", "Aer Lingus · EI583, EI107"))
            ida_f = st.text_input("Fecha Ida:", value=v_ida.get("fecha", "26 Dic"))
            ida_h = st.text_input("Hora Ida:", value=v_ida.get("hora", "15:30"))
            ida_a = st.text_input("Aeropuerto:", value=v_ida.get("aeropuerto", "JFK / Nueva York"))
            st.markdown("---")
            vta_v = st.text_input("Vuelo Regreso:", value=v_vta.get("vuelo", "Aer Lingus · EI104, EI582"))
            vta_f = st.text_input("Fecha Regreso:", value=v_vta.get("fecha", "4 Ene"))
            vta_h = st.text_input("Hora Regreso:", value=v_vta.get("hora", "20:45"))
            vta_a = st.text_input("Aeropuerto Regreso:", value=v_vta.get("aeropuerto", "JFK / Nueva York"))
            if st.form_submit_button("💾 Guardar Datos de Vuelos"):
                st.session_state.config_viaje["vuelo_ida"] = {"vuelo": ida_v, "fecha": ida_f, "hora": ida_h, "aeropuerto": ida_a}
                st.session_state.config_viaje["vuelo_vuelta"] = {"vuelo": vta_v, "fecha": vta_f, "hora": vta_h, "aeropuerto": vta_a}
                guardar_config_viaje(st.session_state.config_viaje)
                st.toast("Datos de vuelos actualizados.", icon="✈️")
                st.rerun()

    with c_vl2:
        st.markdown('<div class="ny-card-header">🏨 Hotel Base en Nueva York</div>', unsafe_allow_html=True)
        with st.form("form_editar_hotel"):
            h_n = st.text_input("Nombre Hotel:", value=hotel.get("nombre", "Courtyard by Marriott New York Manhattan Upper East Side"))
            h_d = st.text_input("Dirección:", value=hotel.get("direccion", "410 E 92nd St, New York, NY 10128"))
            h_lt = st.number_input("Latitud:", value=hotel.get("lat", 40.780242), format="%.6f")
            h_ln = st.number_input("Longitud:", value=hotel.get("lon", -73.946123), format="%.6f")
            if st.form_submit_button("💾 Guardar Hotel Base"):
                st.session_state.config_viaje["hotel"] = {"nombre": h_n, "direccion": h_d, "lat": h_lt, "lon": h_ln}
                guardar_config_viaje(st.session_state.config_viaje)
                st.toast("Hotel base actualizado.", icon="🏨")
                st.rerun()

    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    st.caption("Pulsa sincronizar para importar nuevos lugares. El motor clasificará automáticamente cada sitio en su categoría.")

    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])

    for idx_lst, lst_data in enumerate(listas_config):
        col_l1, col_l2 = st.columns([3.5, 1.2])
        with col_l1:
            st.markdown(f"**{idx_lst+1}. {lst_data['nombre']}**  \n`{lst_data['url']}`")
        with col_l2:
            if st.button("🔄 Sincronizar", key=f"btn_sync_list_{idx_lst}", use_container_width=True):
                with st.spinner(f"Descargando de {lst_data['nombre']}..."):
                    descargados = extraer_lugares_lista_gmaps(lst_data["url"], lst_data["nombre"])
                    if descargados:
                        existentes = set(x.get("nombre", "").lower() for x in st.session_state.lugares)
                        agregados = 0
                        max_id_act = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
                        for d_item in descargados:
                            if d_item["nombre"].lower() not in existentes:
                                max_id_act += 1
                                st.session_state.lugares.append({
                                    "id": max_id_act,
                                    "nombre": d_item["nombre"],
                                    "lat": d_item["lat"],
                                    "lon": d_item["lon"],
                                    "dia": 0,
                                    "direccion": d_item.get("direccion", ""),
                                    "categoria": d_item["categoria"],
                                    "tipo": d_item["tipo"],
                                    "visitado": False
                                })
                                agregados += 1
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.success(f"✓ Sincronizado: {agregados} sitios nuevos añadidos a Guardados.")
                        st.rerun()
                    else:
                        st.warning("No se pudieron extraer lugares en este momento.")

    with st.expander("➕ Añadir nueva lista de Google Maps"):
        with st.form("form_nueva_lista_gmaps"):
            n_nombre_l = st.text_input("Nombre de la lista (ej: Rooftops & Bares):")
            n_url_l = st.text_input("URL compartida de Google Maps (maps.app.goo.gl/...):")
            if st.form_submit_button("Añadir Lista"):
                if n_nombre_l and n_url_l:
                    listas_config.append({"nombre": n_nombre_l, "url": n_url_l})
                    st.session_state.config_viaje["listas_gmaps"] = listas_config
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.success("Lista guardada.")
                    st.rerun()
