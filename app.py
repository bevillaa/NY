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
# 1. CONFIGURACIÓN DE PÁGINA & ESTILO EDITORIAL LIMPIO (MÓVIL + WEB)
# =============================================================================
st.set_page_config(
    page_title="Nueva York · Travel Journal",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  /* -------------------------------------------------------------------------
     1. RESET Y CONFIGURACIÓN GENERAL
     ------------------------------------------------------------------------- */
  [data-testid="stToolbar"],
  [data-testid="stAppToolbar"],
  .stAppToolbar,
  .stAppDeployButton,
  [data-testid="stHeader"],
  header[data-testid="stHeader"],
  [data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  @import url('https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

  :root {
    --ivory: #F7F5F0;
    --paper: #FFFEFC;
    --ink: #373B35;
    --muted: #85877D;
    --sage-dark: #68765F;
    --sage-pale: #EEF0E9;
    --line: #E7E4DC;
  }

  * { box-sizing: border-box; }

  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
    background-color: var(--ivory) !important;
    color: var(--ink) !important;
  }

  html, body, .stApp, p, label, input, button, select, textarea,
  .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stText"], small, li {
    font-family: Calibri, Carlito, "Segoe UI", Arial, sans-serif !important;
  }

  .block-container {
    padding-top: max(0.45rem, env(safe-area-inset-top)) !important;
    padding-bottom: 2.5rem !important;
    max-width: 1220px !important;
  }

  /* -------------------------------------------------------------------------
     2. TARJETAS HERO Y COMPONENTES EDITORIALES
     ------------------------------------------------------------------------- */
  .hero-container {
    background: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-top: 3px solid var(--sage-dark) !important;
    border-radius: 14px !important;
    padding: 20px 24px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.03) !important;
  }
  .hero-eyebrow {
    color: var(--sage-dark) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
  }
  .hero-title {
    font-family: Calibri, Carlito, sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    margin: 4px 0 8px 0 !important;
  }
  .hero-stat-box {
    background: #F8F7F2 !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 8px 14px !important;
    text-align: center;
    flex: 1 1 auto;
  }
  .hero-stat-val { font-size: 1.3rem !important; font-weight: 800 !important; color: var(--sage-dark) !important; }
  .hero-stat-lbl { font-size: 0.62rem !important; font-weight: 700 !important; color: var(--muted) !important; letter-spacing: 0.1em !important; }

  .ny-card, .place-sheet {
    background: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    margin-bottom: 12px !important;
  }
  .ny-card-header {
    color: var(--sage-dark) !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase;
  }

  .place-list-title { font-size: 1.2rem !important; font-weight: 800 !important; color: var(--ink) !important; line-height: 1.2 !important; }
  .place-list-address { font-size: 0.76rem !important; color: #475569 !important; margin-top: 3px !important; }
  .place-note { font-size: 0.76rem !important; font-style: italic !important; color: #475569 !important; margin-top: 3px !important; }
  .place-full-width-info { display: block !important; width: 100% !important; box-sizing: border-box !important; }

  .badge-cat, .badge-indoor, .badge-outdoor {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
  }
  .badge-cat { background: #F1F5F9 !important; color: var(--ink) !important; }
  .badge-indoor { background: #EFF6FF !important; color: #1E3A8A !important; }
  .badge-outdoor { background: #ECFDF5 !important; color: #064E3B !important; }

  /* -------------------------------------------------------------------------
     3. NAVEGACIÓN PRINCIPAL (RADIO BUTTONS DE SECCIONES)
     ------------------------------------------------------------------------- */
  .st-key-seccion_principal_activa {
    margin: 10px 0 18px 0 !important;
    padding: 5px !important;
    background: #EEF2EF !important;
    border: 1px solid #E1E8E2 !important;
    border-radius: 14px !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] {
    display: flex !important;
    gap: 6px !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label {
    flex: 1 1 0 !important;
    min-height: 42px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    background: transparent !important;
    color: #647067 !important;
    padding: 6px 10px !important;
    cursor: pointer !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:has(input:checked) {
    background: #244C38 !important;
    color: #FFFFFF !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label p { color: inherit !important; font-weight: 700 !important; }
  .st-key-seccion_principal_activa [role="radiogroup"] label > div:first-child { display: none !important; }

  /* -------------------------------------------------------------------------
     4. FILAS DE LUGARES Y BOTONES DE ACCIÓN (LÁPIZ, MAPA, HORA, DÍA)
     ------------------------------------------------------------------------- */
  [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"],
  [class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 38px 38px 38px !important;
    align-items: center !important;
    column-gap: 6px !important;
    width: 100% !important;
  }
  [class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"] {
    grid-template-columns: minmax(0, 1fr) 38px 38px !important;
  }

  /* Botones compactos de 38x38px de Lápiz y Mapa (Fondo blanco uniforme) */
  [class*="st-key-it-edit-button-wrap-"] [data-testid="stButton"] > button,
  [class*="st-key-saved-edit-button-wrap-"] [data-testid="stButton"] > button,
  [class*="st-key-it-map-button-wrap-"] [data-testid="stLinkButton"] > a,
  [class*="st-key-saved-map-button-wrap-"] [data-testid="stLinkButton"] > a {
    box-sizing: border-box !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 38px !important;
    min-width: 38px !important;
    max-width: 38px !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 9px !important;
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    background-image: none !important;
    box-shadow: none !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    text-decoration: none !important;
    overflow: hidden !important;
  }

  /* Ocultar texto nativo de Streamlit en los botones de icono */
  [class*="st-key-it-edit-button-wrap-"] [data-testid="stButton"] > button > *,
  [class*="st-key-saved-edit-button-wrap-"] [data-testid="stButton"] > button > *,
  [class*="st-key-it-map-button-wrap-"] [data-testid="stLinkButton"] > a > * {
    display: none !important;
  }

  /* SVG del Lápiz centrado */
  [class*="st-key-it-edit-button-wrap-"] [data-testid="stButton"] > button::before,
  [class*="st-key-saved-edit-button-wrap-"] [data-testid="stButton"] > button::before {
    content: "" !important;
    display: block !important;
    width: 14px !important;
    height: 14px !important;
    background: center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
  }

  /* SVG del Mapa centrado */
  [class*="st-key-it-map-button-wrap-"] [data-testid="stLinkButton"] > a::before,
  [class*="st-key-saved-map-button-wrap-"] [data-testid="stLinkButton"] > a::before {
    content: "" !important;
    display: block !important;
    width: 14px !important;
    height: 14px !important;
    background: center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15M15 6v15'/%3E%3C/svg%3E") !important;
  }

  /* Controles secundarios (Hora y Día) */
  [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
  [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: 86px 130px !important;
    column-gap: 8px !important;
    margin-top: 4px !important;
  }

  /* -------------------------------------------------------------------------
     5. RESPONSIVE MÓVIL (PANTALLAS <= 768px)
     ------------------------------------------------------------------------- */
  @media (max-width: 768px) {
    .block-container { padding: 0.5rem 0.65rem 2rem !important; }
    .hero-container { padding: 14px 16px !important; }
    .hero-title { font-size: 1.4rem !important; }

    .st-key-seccion_principal_activa [role="radiogroup"] {
      overflow-x: auto !important;
      scrollbar-width: none;
    }
    .st-key-seccion_principal_activa [role="radiogroup"] label {
      flex: 0 0 auto !important;
      min-width: max-content !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: 80px 115px !important;
      column-gap: 6px !important;
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

def etiqueta_dia_guardados(d: int) -> str:
    info = DIAS_VIAJE.get(d, {})
    fecha = str(info.get("fecha", "")).strip()
    dia_semana = str(info.get("dia", "")).strip()
    meses = {"Diciembre": "12", "Enero": "01"}
    m = re.search(r"(\d{1,2})\s+(Diciembre|Enero)", fecha, re.IGNORECASE)
    fecha_corta = f"{int(m.group(1)):02d}/{meses[m.group(2).capitalize()]}" if m else fecha
    iniciales = {"Sábado": "S", "Domingo": "D", "Lunes": "L", "Martes": "M",
                 "Miércoles": "X", "Jueves": "J", "Viernes": "V"}
    inicial = iniciales.get(dia_semana, dia_semana[:1].upper())
    return f"Día {d} · {fecha_corta} · {inicial}"

def linkificar_nota(nota: str) -> str:
    texto = (nota or "").strip()
    if not texto: return ""
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
            partes.append(f'<a href="{html.escape(destino, quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8; text-decoration:underline;">{html.escape(url)}</a>')
        partes.append(html.escape(puntuacion_final))
        cursor = coincidencia.end()
    partes.append(html.escape(texto[cursor:]).replace("\n", "<br>"))
    return "".join(partes)

def bloque_nota_html(nota: str) -> str:
    contenido = linkificar_nota(nota)
    return f'<div class="place-note">📝 {contenido}</div>' if contenido else ""


# =============================================================================
# 3. MOTOR INTELIGENTE DE CATEGORÍAS Y UTILIDADES
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
    orig = (lista_origen or "").strip().lower()

    if orig and orig not in ("google maps", "lista", "sin lista"):
        if 'hotel' in orig: return "🏨 Hotel", "Interior"
        if any(k in orig for k in ['christmas', 'navidad', 'winter']): return "🎄 Christmas markets", "Exterior"
        if 'mirador' in orig: return "🏙️ Miradores", "Interior"
        if any(k in orig for k in ['ocio', 'jazz', 'musica']): return "🎷 Ocio", "Interior"
        if any(k in orig for k in ['copas', 'bar', 'pub']): return "🍸 Copas", "Interior"
        if any(k in orig for k in ['dulce', 'bakery', 'cafe']): return "🍪 Dulces", "Interior"
        if any(k in orig for k in ['compra', 'shop', 'outlet']): return "🛍️ Compras", "Interior"
        if any(k in orig for k in ['gastronom', 'food', 'restaurante']): return "🍽️ Gastronomía", "Interior"
        if any(k in orig for k in ['cultura', 'museo']): return "🏛️ Cultura", "Interior"
        if any(k in orig for k in ['spot', 'parque', 'puente']): return "☀️ Spots", "Exterior"

    if 'hotel' in nom: return "🏨 Hotel", "Interior"
    if any(k in texto_busqueda for k in ['christmas market', 'navidad', 'winter village']): return "🎄 Christmas markets", "Exterior"
    if any(k in texto_busqueda for k in ['summit', 'empire state', 'top of the rock', 'edge', 'observatory']): return "🏙️ Miradores", "Interior"
    if any(k in texto_busqueda for k in ['jazz', 'broadway', 'theater', 'show', 'madison square']): return "🎷 Ocio", "Interior"
    if any(k in texto_busqueda for k in ['rooftop', 'speakeasy', 'bar', 'pub', 'cocktail']): return "🍸 Copas", "Interior"
    if any(k in texto_busqueda for k in ['bakery', 'cookie', 'coffee', 'cafe', 'sweets', 'ice cream']): return "🍪 Dulces", "Interior"
    if any(k in texto_busqueda for k in ['outlet', 'target', 'macy', 'zara', 'store', 'shop']): return "🛍️ Compras", "Interior"
    if any(k in texto_busqueda for k in ['pizza', 'burger', 'deli', 'restaurant', 'food', 'bagel', 'sushi']): return "🍽️ Gastronomía", "Interior"
    if any(k in texto_busqueda for k in ['museum', 'museo', 'moma', 'memorial', 'statue', 'church', 'cathedral']): return "🏛️ Cultura", "Interior"
    if any(k in texto_busqueda for k in ['park', 'parque', 'bridge', 'puente', 'high line', 'pier', 'dumbo']): return "☀️ Spots", "Exterior"

    return "📍 Otros", "Exterior"

def selectbox_sin_teclado(*args, **kwargs):
    kwargs.setdefault("filter_mode", None)
    try:
        return st.selectbox(*args, **kwargs)
    except TypeError:
        kwargs.pop("filter_mode", None)
        return st.selectbox(*args, **kwargs)

def obtener_emoji_categoria(cat: str) -> str:
    for ch in cat:
        if ord(ch) > 127: return ch
    return "📍"

def crear_pin_google_maps(categoria: str, nombre: str = ""):
    emoji = obtener_emoji_categoria(categoria)
    html_pin = f"""
    <div style="width:34px; height:34px; background:#ffffff; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 8px rgba(0,0,0,0.25); font-size:18px;">
        {emoji}
    </div>
    """
    return folium.DivIcon(html=html_pin, icon_size=(34, 34), icon_anchor=(17, 17))

def ordenar_por_hora(lista_sitios: list) -> list:
    def clave_orden(item):
        h = (item.get("hora") or "").strip()
        if re.match(r"^\d{1,2}:\d{2}$", h):
            p = h.split(":")
            return (0, int(p[0]) * 60 + int(p[1]), item.get("id", 0))
        return (1, 9999, item.get("id", 0))
    return sorted(lista_sitios, key=clave_orden)


# =============================================================================
# 4. PERSISTENCIA DE DATOS (LOCAL & GITHUB)
# =============================================================================
def _github_configuracion():
    try:
        token = str(st.secrets.get("GITHUB_TOKEN", "")).strip()
        repo = str(st.secrets.get("GITHUB_REPO", "")).strip()
        branch = str(st.secrets.get("GITHUB_BRANCH", "main")).strip() or "main"
        return token, repo, branch
    except Exception:
        return "", "", "main"

def _guardar_json_atomico(ruta: str, datos):
    temporal = None
    try:
        carpeta = os.path.dirname(os.path.abspath(ruta))
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=carpeta, delete=False) as f:
            temporal = f.name
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
        return True
    except Exception:
        if temporal and os.path.exists(temporal): os.remove(temporal)
        return False

def _cargar_json_persistente(ruta: str):
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return None

def _guardar_json_persistente(ruta: str, datos):
    return _guardar_json_atomico(ruta, datos)

def cargar_config_viaje():
    datos = _cargar_json_persistente(ARCH_CONFIG)
    if isinstance(datos, dict): return datos
    return {
        "vuelo_ida": {"vuelo": "Aer Lingus · EI583, EI107", "fecha": "26 Dic", "hora": "15:30", "aeropuerto": "JFK / Nueva York"},
        "vuelo_vuelta": {"vuelo": "Aer Lingus · EI104, EI582", "fecha": "4 Ene", "hora": "20:45", "aeropuerto": "JFK / Nueva York"},
        "hotel": {"nombre": "Courtyard by Marriott New York Manhattan Upper East Side", "direccion": "410 E 92nd St, New York, NY 10128", "lat": 40.780242, "lon": -73.946123},
        "listas_gmaps": []
    }

def guardar_config_viaje(cfg): return _guardar_json_persistente(ARCH_CONFIG, cfg)
def cargar_itinerario_disco(): return _cargar_json_persistente(ARCH_ITINERARIO) or []
def guardar_itinerario_disco(lugares): return _guardar_json_persistente(ARCH_ITINERARIO, lugares)


# =============================================================================
# 5. INICIALIZACIÓN DE ESTADO DE SESIÓN
# =============================================================================
if "config_viaje" not in st.session_state:
    st.session_state.config_viaje = cargar_config_viaje()

if "lugares" not in st.session_state:
    st.session_state.lugares = cargar_itinerario_disco()

if "lugar_activo_id" not in st.session_state:
    st.session_state.lugar_activo_id = None

if "editando_spot_key" not in st.session_state:
    st.session_state.editando_spot_key = None


# =============================================================================
# 6. CABECERA HERO EDITORIAL
# =============================================================================
ahora_madrid = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%H:%M")
ahora_ny = datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M")

lugares_activos = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
lugares_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
lugares_visitados = [l for l in lugares_activos if l.get("visitado", False)]

st.markdown(f"""
<div class="hero-container">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
    <div>
      <div class="hero-eyebrow">✨ 26 DIC 2026 · 4 ENE 2027 ✨</div>
      <div class="hero-title">🎄 Navidad en Nueva York 🗽</div>
      <div style="display:flex; gap:12px; font-size:0.82rem; font-weight:700; color:#475569;">
        <span>Málaga: {ahora_madrid}</span>
        <span>NY: {ahora_ny}</span>
      </div>
    </div>
    <div style="display:flex; gap:8px; width:auto;">
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
# 7. NAVEGACIÓN PRINCIPAL
# =============================================================================
SECCIONES_PRINCIPALES = ["🗺️Mapa", "🗽Ruta", "📌Guardados", "✈️Info"]
seccion_principal = st.radio(
    "Sección del viaje",
    SECCIONES_PRINCIPALES,
    horizontal=True,
    label_visibility="collapsed",
    key="seccion_principal_activa"
)


# -----------------------------------------------------------------------------
# SECCIÓN 1: MAPA GOOGLE
# -----------------------------------------------------------------------------
if seccion_principal == "🗺️Mapa":
    opciones_vista = ["🗽 Todos los Sitios", "✨ Todos los Días"] + [etiqueta_dia(d) for d in range(1, 11)]
    sel_vista = selectbox_sin_teclado("Vista en el mapa:", opciones_vista, label_visibility="collapsed")

    if "Todos los Sitios" in sel_vista:
        sitios_mapa = list(st.session_state.lugares)
    elif "Todos los Días" in sel_vista:
        sitios_mapa = [l for l in st.session_state.lugares if l.get("dia", 0) > 0]
    else:
        m_dia = re.search(r"Día (\d+):", sel_vista)
        num_d = int(m_dia.group(1)) if m_dia else 1
        sitios_mapa = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == num_d])

    hotel = st.session_state.config_viaje.get("hotel", {})
    center_lat = sum(p["lat"] for p in sitios_mapa) / len(sitios_mapa) if sitios_mapa else hotel.get("lat", 40.780242)
    center_lon = sum(p["lon"] for p in sitios_mapa) / len(sitios_mapa) if sitios_mapa else hotel.get("lon", -73.946123)

    mapa = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles=None)
    folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps").add_to(mapa)

    for s in sitios_mapa:
        folium.Marker(
            location=[s["lat"], s["lon"]],
            tooltip=s["nombre"],
            icon=crear_pin_google_maps(s.get("categoria", "📍 Otros"), s["nombre"])
        ).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=700, returned_objects=[])


# -----------------------------------------------------------------------------
# SECCIÓN 2: RUTA (ITINERARIO COMPLETO)
# -----------------------------------------------------------------------------
if seccion_principal == "🗽Ruta":
    opciones_filtro_it = ["✨ Todos los Días"] + [etiqueta_dia(d) for d in range(1, 11)]
    filtro_it_sel = selectbox_sin_teclado("Ver itinerario:", opciones_filtro_it, label_visibility="collapsed")

    dias_a_mostrar = list(range(1, 11)) if "Todos los Días" in filtro_it_sel else [int(re.search(r"Día (\d+):", filtro_it_sel).group(1))]

    for d in dias_a_mostrar:
        paradas_dia = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == d])
        
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:8px 12px; margin:12px 0 8px 0; font-weight:800; font-size:1.1rem;">
          {etiqueta_dia(d)} ({len(paradas_dia)} lugares)
        </div>
        """, unsafe_allow_html=True)

        for item in paradas_dia:
            idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
            is_visited = item.get("visitado", False)
            cat_i = normalizar_categoria(item.get("categoria", "📍 Otros"))
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(item['nombre'] + ' New York')}"

            # Fila de Título y Botones de Acción (Lápiz y Mapa)
            with st.container(key=f"it-heading-row-{item['id']}"):
                c_info, c_edit, c_map, c_chk = st.columns([8.5, 0.6, 0.6, 0.5])
                with c_info:
                    st.markdown(f'<div class="place-list-title">{obtener_emoji_categoria(cat_i)} {item["nombre"]}</div>', unsafe_allow_html=True)
                with c_edit:
                    with st.container(key=f"it-edit-button-wrap-{item['id']}"):
                        if st.button(" ", key=f"btn_ed_it_{d}_{item['id']}"):
                            ek = f"it_{d}_{item['id']}"
                            st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                            st.rerun()
                with c_map:
                    with st.container(key=f"it-map-button-wrap-{item['id']}"):
                        st.link_button(" ", gmaps_url)
                with c_chk:
                    chk_val = st.checkbox("", value=is_visited, key=f"chk_it_{d}_{item['id']}")
                    if chk_val != is_visited and idx_real is not None:
                        st.session_state.lugares[idx_real]["visitado"] = chk_val
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()

            # Dirección y notas
            dir_html = f'<div class="place-list-address">📍 {html.escape(item.get("direccion", ""))}</div>' if item.get("direccion") else ''
            nota_html = bloque_nota_html(item.get("nota", ""))
            if dir_html or nota_html:
                st.markdown(f'<div class="place-full-width-info">{dir_html}{nota_html}</div>', unsafe_allow_html=True)

            # Controles de Hora y Día
            with st.container(key=f"it-controls-row-{item['id']}"):
                c_hr, c_day = st.columns([1.5, 2])
                with c_hr:
                    nueva_h = st.text_input("Hora", value=item.get("hora", ""), placeholder="HH:MM", key=f"hora_it_{d}_{item['id']}", label_visibility="collapsed")
                    if nueva_h.strip() != item.get("hora", "") and idx_real is not None:
                        st.session_state.lugares[idx_real]["hora"] = nueva_h.strip()
                        guardar_itinerario_disco(st.session_state.lugares)
                with c_day:
                    dest_d = selectbox_sin_teclado("Día", ["Guardados"] + [f"Día {x}" for x in range(1, 11)], index=d, key=f"mvd_it_{d}_{item['id']}", label_visibility="collapsed")
                    val_dest = 0 if dest_d == "Guardados" else int(re.search(r"Día (\d+)", dest_d).group(1))
                    if val_dest != d and idx_real is not None:
                        st.session_state.lugares[idx_real]["dia"] = val_dest
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()

            st.markdown('<hr style="margin:8px 0; border-color:#E2E8F0;">', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SECCIÓN 3: BANDEJA DE GUARDADOS
# -----------------------------------------------------------------------------
if seccion_principal == "📌Guardados":
    pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    
    st.markdown(f'<div class="ny-card-header">Lugares Guardados ({len(pool_guardados)})</div>', unsafe_allow_html=True)

    for p_spot in pool_guardados:
        idx_sp_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == p_spot["id"]), None)
        cat_p = normalizar_categoria(p_spot.get("categoria", "📍 Otros"))
        g_url_sp = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p_spot['nombre'] + ' New York')}"

        with st.container(key=f"saved-heading-row-{p_spot['id']}"):
            c_info, c_edit, c_map = st.columns([8.8, 0.6, 0.6])
            with c_info:
                st.markdown(f'<div class="place-list-title">{obtener_emoji_categoria(cat_p)} {p_spot["nombre"]}</div>', unsafe_allow_html=True)
            with c_edit:
                with st.container(key=f"saved-edit-button-wrap-{p_spot['id']}"):
                    if st.button(" ", key=f"btn_ed_pool_{p_spot['id']}"):
                        ek = f"pool_{p_spot['id']}"
                        st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                        st.rerun()
            with c_map:
                with st.container(key=f"saved-map-button-wrap-{p_spot['id']}"):
                    st.link_button(" ", g_url_sp)

        dir_p_html = f'<div class="place-list-address">📍 {html.escape(p_spot.get("direccion", ""))}</div>' if p_spot.get("direccion") else ''
        nota_p_html = bloque_nota_html(p_spot.get("nota", ""))
        if dir_p_html or nota_p_html:
            st.markdown(f'<div class="place-full-width-info">{dir_p_html}{nota_p_html}</div>', unsafe_allow_html=True)

        with st.container(key=f"saved-controls-row-{p_spot['id']}"):
            c_hr, c_day = st.columns([1.5, 2])
            with c_hr:
                nueva_h_pool = st.text_input("Hora", value=p_spot.get("hora", ""), placeholder="HH:MM", key=f"hora_pool_{p_spot['id']}", label_visibility="collapsed")
                if nueva_h_pool.strip() != p_spot.get("hora", "") and idx_sp_real is not None:
                    st.session_state.lugares[idx_sp_real]["hora"] = nueva_h_pool.strip()
                    guardar_itinerario_disco(st.session_state.lugares)
            with c_day:
                opts_dia_pool = ["- Día -"] + [etiqueta_dia_guardados(d) for d in range(1, 11)]
                asig_dia = selectbox_sin_teclado("Día", opts_dia_pool, index=0, key=f"asig_dia_pool_{p_spot['id']}", label_visibility="collapsed")
                if asig_dia != "- Día -" and idx_sp_real is not None:
                    d_num = int(re.search(r"Día (\d+)", asig_dia).group(1))
                    st.session_state.lugares[idx_sp_real]["dia"] = d_num
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()

        st.markdown('<hr style="margin:8px 0; border-color:#E2E8F0;">', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SECCIÓN 4: INFORMACIÓN DE HOTEL Y VUELOS
# -----------------------------------------------------------------------------
if seccion_principal == "✈️Info":
    hotel = st.session_state.config_viaje.get("hotel", {})
    v_ida = st.session_state.config_viaje.get("vuelo_ida", {})
    v_vta = st.session_state.config_viaje.get("vuelo_vuelta", {})

    st.markdown('<div class="ny-card-header">🏨 Hotel Base</div>', unsafe_allow_html=True)
    st.markdown(f"**{hotel.get('nombre')}**\n\n📍 {hotel.get('direccion')}")

    st.markdown('<div class="ny-card-header" style="margin-top:16px;">✈️ Vuelos</div>', unsafe_allow_html=True)
    st.markdown(f"**Ida:** {v_ida.get('vuelo')} ({v_ida.get('fecha')} · {v_ida.get('hora')})")
    st.markdown(f"**Vuelta:** {v_vta.get('vuelo')} ({v_vta.get('fecha')} · {v_vta.get('hora')})")
