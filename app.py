import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import urllib.request
import urllib.error
import urllib.parse
import os
import re
import tempfile
import math
import html
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

ARCH_ITINERARIO = "itinerario_actual.json"
ARCH_CONFIG     = "config_viaje.json"

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA & ESTILO NAVIDEÑO EDITORIAL (MÓVIL + WEB)
# =============================================================================
st.set_page_config(
    page_title="Nueva York · Travel Journal",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  /* Oculta la barra superior propia de Streamlit (GitHub, menú, editar y compartir),
     sin ocultar la cabecera personalizada de la aplicación. */
  [data-testid="stToolbar"],
  [data-testid="stAppToolbar"],
  .stAppToolbar,
  .stAppDeployButton {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
  }

  @import url('https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

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

  div[role="radiogroup"] {
    gap: 0.35rem !important;
    flex-wrap: wrap !important;
    margin: 0.15rem 0 0.8rem 0 !important;
  }
  div[role="radiogroup"] label {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 0.35rem 0.7rem !important;
    background: #FFFFFF !important;
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

  /* Nota manual fina y discreta debajo de la dirección */
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

  /* Pestañas adaptadas a táctil y móvil sin solapamientos */
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

  /* Botones generales limpios */
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

  /* Mini botones de Editar y Mapa en la cabecera */
  .header-actions {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 4px !important;
  }
  .header-actions button, .header-actions a {
    min-height: 32px !important;
    height: 32px !important;
    width: 32px !important;
    min-width: 32px !important;
    max-width: 32px !important;
    padding: 0 !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
  }

  iframe {
    border-radius: 16px !important;
    border: 1.5px solid #CBD5E1 !important;
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

  /* =========================================================================
     DISEÑO RESPONSIVE Y CONTROLES (HORA | DÍA AL PRINCIPIO)
     ========================================================================= */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: minmax(76px, 1.7fr) minmax(84px, 1.9fr) minmax(36px, 0.8fr) minmax(36px, 0.9fr) !important;
      grid-auto-flow: column !important;
      align-items: stretch !important;
      column-gap: 5px !important;
      row-gap: 0 !important;
      width: 100% !important;
    }

    /* Columna 1: Hora */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) input {
      height: 36px !important;
      text-align: center !important;
      font-size: 0.76rem !important;
      font-weight: 800 !important;
    }

    /* Columna 2: Día */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div {
      height: 36px !important;
      border-radius: 8px !important;
    }

    /* Columna 3: Mini icono Editar */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) .stButton > button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) .stButton > button {
      height: 36px !important;
      width: 100% !important;
      min-width: 36px !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background: #FFFFFF !important;
      font-size: 1.05rem !important;
    }

    /* Columna 4: Mini icono Mapa */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stLinkButton"] > a {
      height: 36px !important;
      width: 100% !important;
      min-width: 36px !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background: #FFFFFF !important;
      font-size: 1.05rem !important;
    }
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

def linkificar_nota(nota: str) -> str:
    texto = (nota or "").strip()
    if not texto: return ""
    patron_url = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
    partes, cursor = [], 0
    for coincidencia in patron_url.finditer(texto):
        partes.append(html.escape(texto[cursor:coincidencia.start()]).replace("\n", "<br>"))
        url_original = coincidencia.group(0)
        url = url_original.rstrip(".,;:!?)]}")
        puntuacion_final = url_original[len(url):]
        if url:
            destino = url if url.lower().startswith(("http://", "https://")) else f"https://{url}"
            partes.append(f'<a href="{html.escape(destino, quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8; text-decoration:underline;">{html.escape(url)}</a>')
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
    "🍽️ Gastronomía", "🍪 Dulces", "🍸 Copas", "🎷 Ocio", "🛍️ Compras",
    "🎄 Christmas markets", "🏛️ Cultura", "🏙️ Miradores", "☀️ Spots", "📍 Otros", "🏨 Hotel"
]

def normalizar_categoria(cat: str) -> str:
    if not cat: return "☀️ Spots"
    if cat in CATEGORIAS_CANONICAS: return cat
    for c in CATEGORIAS_CANONICAS:
        if c.split()[-1].lower() in cat.lower(): return c
    return "☀️ Spots"

def clasificar_lugar(nombre: str, direccion: str = "", lista_origen: str = "") -> tuple[str, str]:
    nom = (nombre or "").strip().lower()
    dir_txt = (direccion or "").strip().lower()
    texto_busqueda = f"{nom} {dir_txt}"
    
    if 'hotel' in nom or 'inn' in nom: return "🏨 Hotel", "Interior"
    if any(k in texto_busqueda for k in ['christmas market', 'holiday market', 'winter village']): return "🎄 Christmas markets", "Exterior"
    if any(k in texto_busqueda for k in ['summit', 'empire state', 'top of the rock', 'edge']): return "🏙️ Miradores", "Interior"
    if any(k in texto_busqueda for k in ['jazz', 'broadway', 'theatre', 'musical']): return "🎷 Ocio", "Interior"
    if any(k in texto_busqueda for k in ['rooftop', 'bar', 'cocktail', 'pub']): return "🍸 Copas", "Interior"
    if any(k in texto_busqueda for k in ['bakery', 'cookie', 'coffee', 'cafe', 'sweets']): return "🍪 Dulces", "Interior"
    if any(k in texto_busqueda for k in ['outlet', 'store', 'shop', 'mall']): return "🛍️ Compras", "Interior"
    if any(k in texto_busqueda for k in ['pizza', 'burger', 'deli', 'restaurant', 'food']): return "🍽️ Gastronomía", "Interior"
    if any(k in texto_busqueda for k in ['museum', 'museo', 'met', 'moma', 'statue']): return "🏛️ Cultura", "Interior"
    if any(k in texto_busqueda for k in ['park', 'bridge', 'high line', 'pier', 'square']): return "☀️ Spots", "Exterior"
    return "📍 Otros", "Exterior"

def selectbox_sin_teclado(*args, **kwargs):
    kwargs.setdefault("filter_mode", None)
    try: return st.selectbox(*args, **kwargs)
    except TypeError:
        kwargs.pop("filter_mode", None)
        return st.selectbox(*args, **kwargs)

def obtener_emoji_categoria(cat: str) -> str:
    for ch in cat:
        if ord(ch) > 127: return ch
    return "📍"

def crear_pin_google_maps(categoria: str, nombre: str = ""):
    emoji = obtener_emoji_categoria(categoria)
    html_pin = f"""<div style="width: 34px; height: 34px; background: #ffffff; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(0,0,0,0.25); font-size: 18px;">{emoji}</div>"""
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
# 4. CARGA Y GESTIÓN DE DATOS DEL VIAJE
# =============================================================================
def _cargar_json_persistente(ruta: str):
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return None

def _guardar_json_atomico(ruta: str, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        return True
    except Exception: return False

def cargar_config_viaje():
    datos = _cargar_json_persistente(ARCH_CONFIG)
    if isinstance(datos, dict): return datos
    return {
        "vuelo_ida": {"aerolinea": "Aer Lingus", "fecha": "26 Dic", "hora": "15:30", "vuelo": "EI583, EI107"},
        "vuelo_vuelta": {"aerolinea": "Aer Lingus", "fecha": "4 Ene", "hora": "20:45", "vuelo": "EI104, EI582"},
        "hotel": {"nombre": "Courtyard Manhattan Upper East Side", "direccion": "410 E 92nd St", "lat": 40.780242, "lon": -73.946123},
        "listas_gmaps": []
    }

def cargar_itinerario_disco():
    datos = _cargar_json_persistente(ARCH_ITINERARIO)
    return datos if isinstance(datos, list) else []

def guardar_itinerario_disco(lugares):
    return _guardar_json_atomico(ARCH_ITINERARIO, lugares)

# =============================================================================
# 5. INICIALIZACIÓN DE ESTADO
# =============================================================================
if "config_viaje" not in st.session_state: st.session_state.config_viaje = cargar_config_viaje()
if "lugares" not in st.session_state: st.session_state.lugares = cargar_itinerario_disco()
if "editando_spot_key" not in st.session_state: st.session_state.editando_spot_key = None

# =============================================================================
# 6. CABECERA HERO EDITORIAL NAVIDEÑA
# =============================================================================
lugares_activos = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
lugares_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
lugares_visitados = [l for l in lugares_activos if l.get("visitado", False)]

st.markdown(f"""
<div class="hero-container">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
    <div>
      <div class="hero-eyebrow">✨ 26 DIC 2026 · 4 ENE 2027 ✨</div>
      <div class="hero-title">🎄Navidad en Nueva York🗽</div>
    </div>
    <div style="display:flex; gap:8px;">
      <div class="hero-stat-box"><div class="hero-stat-val">{len(lugares_activos)}</div><div class="hero-stat-lbl">En Ruta</div></div>
      <div class="hero-stat-box"><div class="hero-stat-val">{len(lugares_guardados)}</div><div class="hero-stat-lbl">Guardados</div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 7. PESTAÑAS PRINCIPALES DEL SISTEMA
# =============================================================================
seccion_principal = st.radio(
    "Sección del viaje",
    ["🗺️Mapa", "📍Ruta", "📎Guardados", "💸Divisas", "✈️Info"],
    horizontal=True,
    label_visibility="collapsed",
    key="seccion_principal_activa"
)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: MAPA GOOGLE
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗺️Mapa":
    c_m1, c_m3 = st.columns([3, 2])
    with c_m1:
        opciones_vista = ["🗽 Todos los Sitios", "✨ Todos los Días"] + [etiqueta_dia(d) for d in range(1, 11)]
        sel_vista = selectbox_sin_teclado("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    with c_m3:
        cats_actuales = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in st.session_state.lugares))
        sel_filtro_cat = selectbox_sin_teclado("Categoría:", ["Todas"] + cats_actuales, label_visibility="collapsed")

    # SOLUCIÓN CORREGIDA PARA "✨ Todos los Días"
    if "Todos los Sitios" in sel_vista:
        sitios_mapa = list(st.session_state.lugares)
    elif "Todos los Días" in sel_vista:
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    else:
        m_dia = re.search(r"Día (\d+):", sel_vista)
        num_d = int(m_dia.group(1)) if m_dia else 1
        sitios_mapa = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == num_d])

    if sel_filtro_cat != "Todas":
        sitios_mapa = [l for l in sitios_mapa if normalizar_categoria(l.get("categoria", "")) == sel_filtro_cat]

    hotel = st.session_state.config_viaje.get("hotel", {})
    center_lat = sum(p["lat"] for p in sitios_mapa) / len(sitios_mapa) if sitios_mapa else hotel.get("lat", 40.780242)
    center_lon = sum(p["lon"] for p in sitios_mapa) / len(sitios_mapa) if sitios_mapa else hotel.get("lon", -73.946123)

    mapa = folium.Map(location=[center_lat, center_lon], zoom_start=13, scrollWheelZoom=False)
    folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps").add_to(mapa)

    for s in sitios_mapa:
        cat_spot = normalizar_categoria(s.get("categoria", "📍 Otros"))
        folium.Marker(
            location=[s["lat"], s["lon"]],
            popup=s["nombre"],
            tooltip=s["nombre"],
            icon=crear_pin_google_maps(cat_spot, s["nombre"])
        ).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=600)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO COMPLETO (ORDEN: HORA | DÍA | EDITAR | MAPA)
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "📍Ruta":
    for d in range(1, 11):
        paradas_dia = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == d])
        st.markdown(f"### {etiqueta_dia(d)}")

        for item in paradas_dia:
            idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(item['nombre'] + ' New York')}"
            
            # Encabezado con Nombre del Lugar
            st.markdown(f"**{obtener_emoji_categoria(item.get('categoria'))} {item['nombre']}**")
            
            # Fila de Controles: Hora | Día | Editar | Mapa
            with st.container(key=f"it-controls-row-{item['id']}"):
                c_hr, c_day, c_edit, c_map = st.columns([1.7, 1.9, 0.8, 0.9], gap="small")
                with c_hr:
                    nueva_h = st.text_input("Hora", value=item.get("hora", ""), placeholder="HH:MM", key=f"hora_it_{d}_{item['id']}", label_visibility="collapsed")
                    if nueva_h != item.get("hora", "") and idx_real is not None:
                        st.session_state.lugares[idx_real]["hora"] = nueva_h
                        guardar_itinerario_disco(st.session_state.lugares)
                with c_day:
                    dest_d = selectbox_sin_teclado("Día", ["Guardados"] + [f"Día {x}" for x in range(1, 11)], index=d, key=f"mvd_it_{d}_{item['id']}", label_visibility="collapsed")
                    val_dest = 0 if dest_d == "Guardados" else int(re.search(r"Día (\d+)", dest_d).group(1))
                    if val_dest != d and idx_real is not None:
                        st.session_state.lugares[idx_real]["dia"] = val_dest
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()
                with c_edit:
                    if st.button("✏️", key=f"btn_ed_it_{d}_{item['id']}", help="Editar sitio", use_container_width=True):
                        st.toast(f"Editando {item['nombre']}")
                with c_map:
                    st.link_button("🗺️", gmaps_url, use_container_width=True, key=f"map_it_{item['id']}", help="Abrir en Maps")

            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS (ORDEN: HORA | DÍA | EDITAR | MAPA)
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "📎Guardados":
    pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    
    for p_spot in pool_guardados:
        idx_sp_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == p_spot["id"]), None)
        g_url_sp = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p_spot['nombre'] + ' New York')}"
        
        st.markdown(f"**{obtener_emoji_categoria(p_spot.get('categoria'))} {p_spot['nombre']}**")
        
        # Fila de Controles: Hora | Día | Editar | Mapa
        with st.container(key=f"saved-controls-row-{p_spot['id']}"):
            c_hr, c_day, c_edit, c_map = st.columns([1.7, 1.9, 0.8, 0.9], gap="small")
            with c_hr:
                nueva_h_pool = st.text_input("Hora", value=p_spot.get("hora", ""), placeholder="HH:MM", key=f"hora_pool_{p_spot['id']}", label_visibility="collapsed")
                if nueva_h_pool != p_spot.get("hora", "") and idx_sp_real is not None:
                    st.session_state.lugares[idx_sp_real]["hora"] = nueva_h_pool
                    guardar_itinerario_disco(st.session_state.lugares)
            with c_day:
                opts_dia_pool = ["- Día -"] + [f"Día {d}" for d in range(1, 11)]
                asig_dia = selectbox_sin_teclado("Día", opts_dia_pool, index=0, key=f"asig_dia_pool_{p_spot['id']}", label_visibility="collapsed")
                if asig_dia != "- Día -" and idx_sp_real is not None:
                    d_num = int(re.search(r"Día (\d+)", asig_dia).group(1))
                    st.session_state.lugares[idx_sp_real]["dia"] = d_num
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()
            with c_edit:
                if st.button("✏️", key=f"btn_ed_pool_{p_spot['id']}", help="Editar sitio", use_container_width=True):
                    st.toast(f"Editando {p_spot['nombre']}")
            with c_map:
                st.link_button("🗺️", g_url_sp, use_container_width=True, key=f"map_saved_{p_spot['id']}", help="Abrir en Maps")

        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
