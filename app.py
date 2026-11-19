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
import copy
from datetime import datetime
from urllib.parse import urlsplit
import ipaddress
import socket
import logging
from zoneinfo import ZoneInfo

ARCH_ITINERARIO = "itinerario_actual.json"
ARCH_CONFIG     = "config_viaje.json"

logger = logging.getLogger("ny_travel_app")

_ALLOWED_MAP_HOSTS = ("google.com", "www.google.com", "maps.google.com", "maps.app.goo.gl", "goo.gl")

def _validar_url_google_maps(url: str) -> bool:
    """Solo permite URLs HTTP(S) de dominios oficiales de Google Maps."""
    try:
        parsed = urlsplit(str(url or "").strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in ("http", "https") or not host:
            return False
        if parsed.username or parsed.password:
            return False
        permitido = host in _ALLOWED_MAP_HOSTS or host.endswith(".google.com")
        if not permitido:
            return False
        # Defensa adicional ante DNS rebinding o subdominios mal configurados.
        try:
            for info in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM):
                ip = ipaddress.ip_address(info[4][0])
                if not ip.is_global:
                    return False
        except (OSError, ValueError):
            return False
        return True
    except Exception:
        return False

class _GoogleMapsRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _validar_url_google_maps(newurl):
            raise urllib.error.URLError("Redirección fuera de dominios permitidos de Google Maps")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def _abrir_url_google_maps(url: str, headers=None, timeout=8):
    if not _validar_url_google_maps(url):
        raise ValueError("Solo se permiten enlaces oficiales de Google Maps.")
    opener = urllib.request.build_opener(_GoogleMapsRedirectHandler())
    req = urllib.request.Request(url, headers=headers or {})
    return opener.open(req, timeout=timeout)



def _google_maps_api_key():
    """Lee la clave de Places desde el entorno o los secretos de Streamlit."""
    clave = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not clave:
        try:
            clave = str(st.secrets.get("GOOGLE_MAPS_API_KEY", "")).strip()
        except Exception:
            clave = ""
    return clave

def _sugerencias_google_places(texto: str, api_key: str):
    """Obtiene sugerencias de Google Places (API nueva)."""
    payload = json.dumps({"input": texto, "languageCode": "es"}).encode("utf-8")
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:autocomplete",
        data=payload,
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    opciones = []
    for item in data.get("suggestions", []):
        pred = item.get("placePrediction", {})
        pid = pred.get("placeId")
        descripcion = (pred.get("text") or {}).get("text", "")
        if pid and descripcion:
            opciones.append({"id": pid, "descripcion": descripcion})
    return opciones

def _detalles_google_place(place_id: str, api_key: str):
    """Recupera nombre, dirección y coordenadas de un lugar elegido."""
    url = "https://places.googleapis.com/v1/places/" + urllib.parse.quote(place_id, safe="")
    req = urllib.request.Request(
        url,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,location"
        }
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    loc = data.get("location") or {}
    nombre = (data.get("displayName") or {}).get("text") or ""
    return nombre, data.get("formattedAddress", ""), loc.get("latitude"), loc.get("longitude")

def _fecha_inicio_viaje(config):
    """Obtiene la fecha de salida desde ISO o desde el formato español existente."""
    valor = (config or {}).get("fecha_inicio_viaje") or (config or {}).get("fecha_inicio")
    if not valor:
        valor = ((config or {}).get("vuelo_ida") or {}).get("fecha", "")
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto).date()
    except ValueError:
        pass
    meses = {"ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3,
             "abr": 4, "abril": 4, "may": 5, "mayo": 5, "jun": 6, "junio": 6,
             "jul": 7, "julio": 7, "ago": 8, "agosto": 8, "sep": 9, "sept": 9,
             "septiembre": 9, "oct": 10, "octubre": 10, "nov": 11, "noviembre": 11,
             "dic": 12, "diciembre": 12}
    m = re.search(r"(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóú]+)(?:\s+(\d{4}))?", texto)
    if not m:
        return None
    dia, mes_txt, anio_txt = m.groups()
    mes = meses.get(mes_txt.casefold().rstrip("."))
    if not mes:
        return None
    anio = int(anio_txt) if anio_txt else datetime.now().year
    try:
        fecha = datetime(anio, mes, int(dia)).date()
        if not anio_txt and fecha < datetime.now().date():
            fecha = datetime(anio + 1, mes, int(dia)).date()
        return fecha
    except ValueError:
        return None


def _validar_lugar(registro):
    """Valida y normaliza un registro sin descartar silenciosamente datos recuperables."""
    if not isinstance(registro, dict):
        return None
    nombre = str(registro.get("nombre", "") or "").strip()
    if not nombre:
        return None
    try:
        lat, lon = float(registro.get("lat")), float(registro.get("lon"))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
    except (TypeError, ValueError):
        return None
    try:
        dia = int(registro.get("dia", 0) or 0)
    except (TypeError, ValueError):
        dia = 0
    if not 0 <= dia <= 10:
        dia = 0
    hora = str(registro.get("hora", "") or "").strip()
    if hora and not re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", hora):
        hora = ""
    if hora and len(hora) == 4:
        hora = "0" + hora
    normalizado = dict(registro)
    normalizado.update({
        "id": registro.get("id") if registro.get("id") is not None else hashlib.sha1(nombre.encode("utf-8")).hexdigest()[:12],
        "nombre": nombre, "lat": lat, "lon": lon, "dia": dia, "hora": hora,
        "direccion": str(registro.get("direccion", "") or ""),
        "nota": str(registro.get("nota", "") or ""),
        "categoria": normalizar_categoria(registro.get("categoria", "")),
        "tipo": registro.get("tipo") if registro.get("tipo") in ("Interior", "Exterior") else "Interior",
        "visitado": bool(registro.get("visitado", False)),
    })
    return normalizado

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

  @import url("https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap");

  :root {
    color-scheme: light !important;
  }

  * {
    box-sizing: border-box;
  }

  html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, button, select, textarea,
  .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stText"], .stCaption, small {
    font-family: "Calibri", "Carlito", "Segoe UI", Candara, -apple-system, BlinkMacSystemFont, Arial, sans-serif !important;
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
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
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
    -webkit-font-feature-settings: "liga" !important;
    font-feature-settings: "liga" !important;
    -webkit-font-smoothing: antialiased !important;
    color: #0F172A !important;
  }

  div[role="radiogroup"] {
    gap: 0.35rem !important;
    flex-wrap: wrap !important;
    margin: 0.15rem 0 0.8rem 0 !important;
  }
  div[role="radiogroup"] label {
    padding: 0.35rem 0.7rem !important;
  }

  [data-testid="stExpander"] { overflow: hidden !important; }
  [data-testid="stExpander"] details summary {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
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
  }

  .hero-container {
    color: #0F172A !important;
  }
  .hero-eyebrow {
    text-transform: uppercase;
  }
.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 11px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-right: 5px;
    margin-bottom: 4px;
    max-width: 100%;
    word-break: break-word;
  }
  .hero-stat-box {
    text-align: center;
    flex: 1 1 auto;
  }
  .hero-stat-val {
    font-size: 1.4rem;
  }
  .hero-stat-lbl {
    font-weight: 800;
    text-transform: uppercase;
  }

  .ny-card {
    margin-bottom: 12px;
    color: #0F172A !important;
  }
  .ny-card-header {
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .place-sheet {
    margin: 10px 0;
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

  /* Encabezado de Guardados: título flexible y sincronización a la derecha. */
  [class*="st-key-guardados-header-row"] [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) max-content !important;
    align-items: center !important;
    justify-content: stretch !important;
    column-gap: 8px !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  [class*="st-key-guardados-header-row"] [data-testid="stColumn"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  [class*="st-key-guardados-header-row"] [data-testid="stColumn"]:first-child {
    min-width: 0 !important;
  }
  [class*="st-key-guardados-header-row"] [data-testid="stColumn"]:nth-child(2) {
    justify-content: flex-end !important;
  }

  /* Botón pequeño de sincronizar listas en Guardados */
  [class*="st-key-btn_sync_guardados_wrap"] {
    display: flex !important;
    justify-content: flex-end !important;
  }
  [class*="st-key-btn_sync_guardados_wrap"] button {
    min-height: 30px !important;
    height: 30px !important;
    padding: 0 10px !important;
    font-size: 0.78rem !important;
    border-radius: 8px !important;
    width: auto !important;
    white-space: nowrap !important;
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
  ul[role="listbox"], ul[role="listbox"] li {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
  }

  /* =========================================================================
     DISEÑO RESPONSIVE PARA MÓVILES
     Las filas con Hora/Día/Maps se identifican de forma explícita; el resto
     de columnas se apila para que nunca se compriman ni se solapen.
     ========================================================================= */
  @media (max-width: 768px) {
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], section.main {
      margin: 0 !important;
      width: 100% !important;
      max-width: 100% !important;
      overflow-x: hidden !important;
    }
    .block-container {
      width: 100% !important;
      max-width: 100% !important;
      padding: 0.55rem 0.65rem 2rem !important;
      margin: 0 auto !important;
      overflow-x: clip !important;
    }
    /* Evita que nombres, notas o URL largas empujen la página fuera del móvil. */
    [data-testid="stMarkdownContainer"], [data-testid="stText"],
    .stCaption, p, a, code, pre, label {
      max-width: 100% !important;
      min-width: 0 !important;
      overflow-wrap: anywhere !important;
      word-break: break-word !important;
    }
    .hero-container {
      min-width: 0 !important;
    }
    .hero-title {  line-height: 1.18 !important; }
    .hero-pill {
      display: inline-flex !important;
      max-width: 100% !important;
      white-space: normal !important;
      overflow-wrap: anywhere !important;
      font-size: 0.71rem !important;
      line-height: 1.25 !important;
      padding: 4px 8px !important;
    }
    .hero-stat-box {  flex: 1 1 28% !important;  }
    .hero-stat-val { font-size: 1.25rem !important; }
.ny-card {   min-width: 0 !important; }
    .ny-card-header {   line-height: 1.3 !important; }
    .place-sheet {   min-width: 0 !important; }
    /* Regla segura por defecto: filas de formulario y filtros se apilan. */
    [data-testid="stHorizontalBlock"]:not([class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-guardados-header-row"] [data-testid="stHorizontalBlock"]):not([class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"]) {
      display: flex !important;
      flex-wrap: wrap !important;
      align-items: flex-start !important;
      gap: 0.5rem !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"]:not([class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"]):not([class*="st-key-guardados-header-row"] [data-testid="stHorizontalBlock"]):not([class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"]) > [data-testid="stColumn"] {
      flex: 1 1 100% !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    /* Acciones de seguimiento de vuelos y listas Google: dos botones alineados. */
    [class*="st-key-flight-links-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-gmaps-actions-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
      align-items: stretch !important;
      gap: 7px !important;
      width: 100% !important;
    }
    [class*="st-key-flight-links-"] [data-testid="stColumn"],
    [class*="st-key-gmaps-actions-"] [data-testid="stColumn"] {
      display: block !important;
      flex: none !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    [class*="st-key-flight-links-"] .stLinkButton > a,
    [class*="st-key-gmaps-actions-"] .stButton > button {
      min-height: 36px !important;
      height: auto !important;
      padding: 6px 5px !important;
      font-size: 0.72rem !important;
      white-space: normal !important;
      line-height: 1.15 !important;
      overflow-wrap: anywhere !important;
    }
    /* Pestañas en dos columnas: nada se oculta ni necesita scroll horizontal. */
    .stTabs [data-baseweb="tab-list"] {
      display: grid !important;
      grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
      gap: 4px !important;
      padding: 4px !important;
      overflow: visible !important;
      white-space: normal !important;
    }
    .stTabs [data-baseweb="tab"] {
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      width: 100% !important;
      min-width: 0 !important;
      min-height: 30px !important;
      height: auto !important;
      padding: 6px 4px !important;
      white-space: normal !important;
      text-align: center !important;
      line-height: 1.15 !important;
      font-size: 0.75rem !important;
      overflow-wrap: anywhere !important;
    }
    /* Botones y campos: contenidos en su columna y con texto envolvente. */
    .stButton:not([class*="st-key-it-edit-button-wrap-"] *):not([class*="st-key-saved-edit-button-wrap-"] *),
    .stFormSubmitButton,
    [data-testid="stLinkButton"]:not([class*="st-key-it-map-button-wrap-"] *):not([class*="st-key-saved-map-button-wrap-"] *),
    .stSelectbox:not([class*="st-key-saved-controls-row-"] *),
    .stTextInput:not([class*="st-key-saved-controls-row-"] *):not([class*="st-key-it-heading-row-"] *),
    .stNumberInput, .stDateInput, .stMultiSelect, .stSlider,
    [data-testid="stFileUploader"] {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
    }
    .stButton:not([class*="st-key-it-edit-button-wrap-"] *):not([class*="st-key-saved-edit-button-wrap-"] *) > button,
    .stFormSubmitButton > button,
    [data-testid="stLinkButton"]:not([class*="st-key-it-map-button-wrap-"] *):not([class*="st-key-saved-map-button-wrap-"] *) > a {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      min-height: 36px !important;
      height: auto !important;
      padding: 7px 8px !important;
      white-space: normal !important;
      line-height: 1.15 !important;
      overflow-wrap: anywhere !important;
      font-size: 0.76rem !important;
    }
    [data-baseweb="select"], [data-baseweb="input"], [data-baseweb="base-input"] {
      max-width: 100% !important;
      min-width: 0 !important;
    }
    .stRadio > div { flex-wrap: wrap !important; gap: 0.45rem !important; }
    iframe {
      display: block !important;
      width: 100% !important;
      max-width: 100% !important;
      height: 380px !important;
    }
    /* URL de listas: línea partida, no fuerza scroll horizontal. */
    .gmaps-list-url { overflow-wrap: anywhere !important; word-break: break-all !important; }
  }

  /* Ajustes para teléfonos estrechos. */
  @media (max-width: 380px) {
    .block-container { padding-left: 0.45rem !important; padding-right: 0.45rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.69rem !important; padding: 4px 2px !important; }
  }

  @media (max-width: 768px) {
    /* Estadística superior: reservar más ancho a la tarjeta "Guardados". */
    .hero-container > div > div:last-child {
      display: grid !important;
      gap: 6px !important;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
    }
    .hero-stat-box {
      box-sizing: border-box !important;
      width: 100% !important;
      overflow: visible !important;
    }
    .hero-stat-lbl {
      white-space: nowrap !important;
      word-break: normal !important;
      overflow-wrap: normal !important;
    }
  }

  @media (max-width: 320px) {
    .hero-stat-lbl { font-size: 0.51rem !important; letter-spacing: 0 !important; }
  }

  /* Tipografía y datos de las fichas de lugares. */
  .place-list-title {
    font-size: 1.25rem !important;
    font-weight: 900 !important;
    line-height: 1.2 !important;
    overflow-wrap: anywhere !important;
    color: #0F172A;
  }
  .place-list-address {
    margin-top: 3px !important;
    color: #475569 !important;
    font-size: 0.76rem !important;
    line-height: 1.25 !important;
    font-weight: 600 !important;
    overflow-wrap: anywhere !important;
  }

  @media (max-width: 768px) {
    /* Nombre dominante; categoría, entorno, dirección y nota siempre menores. */
    .place-list-title {
      font-size: 1.25rem !important;
      line-height: 1.22 !important;
      letter-spacing: 0 !important;
    }
    .place-list-address {
      font-size: 0.72rem !important;
      line-height: 1.28 !important;
      margin-top: 2px !important;
    }
    .place-note {
      font-size: 0.70rem !important;
      line-height: 1.28 !important;
    }
    .badge-cat, .badge-indoor, .badge-outdoor {
      font-size: 0.66rem !important;
      line-height: 1.18 !important;
      padding: 1px 5px !important;
    }
    }

  @media (max-width: 320px) {
    .place-list-address, .place-note { font-size: 0.68rem !important; }
  }

  /* La tarjeta central del resumen siempre muestra GUARDADOS completo. */
  @media (max-width: 768px) {
    .hero-container > div > div:last-child {
      grid-template-columns: minmax(0, 1fr) minmax(88px, 1.18fr) minmax(0, 1fr) !important;
    }
    .hero-container .hero-stat-box:nth-child(2) .hero-stat-lbl {
      white-space: nowrap !important;
      overflow: visible !important;
      font-size: 0.58rem !important;
      letter-spacing: 0 !important;
    }
  }
  /* Ajustes finales para que la página completa pueda desplazarse en móvil. */
  @media (max-width: 768px) {
    html, body {
      height: auto !important;
      min-height: 100% !important;
      overflow-y: auto !important;
      overscroll-behavior-y: auto !important;
    }
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main {
      height: auto !important;
      min-height: 100dvh !important;
      max-height: none !important;
      overflow-y: visible !important;
      overflow-x: hidden !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      padding-top: max(1.4rem, calc(env(safe-area-inset-top) + 0.7rem)) !important;
    }
    /* La cabecera tenía una altura fija de 30px que podía cortar su contenido. */
    .hero-container {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      overflow: visible !important;
      margin-bottom: 12px !important;
    }
    .hero-container .hero-eyebrow {
      display: block !important;
      height: auto !important;
      max-height: none !important;
      overflow: visible !important;
      line-height: 1.4 !important;
      padding-top: 2px !important;
    }
    .hero-container > div {
      min-width: 0 !important;
      width: 100% !important;
    }
    .hero-container > div > div:first-child {
      min-width: 0 !important;
      width: 100% !important;
    }
    [data-testid="stTabs"],
    [data-testid="stTabContent"],
    [data-testid="stVerticalBlock"] {
      min-height: 0 !important;
      max-height: none !important;
      overflow: visible !important;
    }
    footer, [data-testid="stFooter"] {
      display: block !important;
      visibility: visible !important;
      height: auto !important;
      min-height: 2rem !important;
      padding-bottom: env(safe-area-inset-bottom) !important;
    }
  }
  /* Corrección adicional: Streamlit puede reservar espacio aunque su toolbar esté oculta. */
  [data-testid="stHeader"],
  header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
  }
  [data-testid="stDecoration"] {
    display: none !important;
    height: 0 !important;
  }
  [data-testid="stMain"], section.main {
    padding-top: 0 !important;
    margin-top: 0 !important;
  }
  [data-testid="stMainBlockContainer"], .block-container {
    padding-top: 0.45rem !important;
    margin-top: 0 !important;
  }
  @media (max-width: 768px) {
    [data-testid="stMainBlockContainer"], .block-container {
      padding-top: max(0.25rem, env(safe-area-inset-top)) !important;
    }
    .hero-container {
      margin-top: 0 !important;
    }
  }

  /* ================================================================
     REDISEÑO EDITORIAL AESTHETIC · solo presentación, sin tocar lógica
     ================================================================ */
  :root {
    --ivory: #F7F5F0;
    --paper: #FFFEFC;
    --ink: #373B35;
    --muted: #85877D;
    --sage: #899681;
    --sage-dark: #68765F;
    --sage-pale: #EEF0E9;
    --line: #E7E4DC;
    --clay: #B78E7A;
  }
  html, body, .stApp, [data-testid="stAppViewContainer"],
  [data-testid="stMain"], section.main {
    background: var(--ivory) !important;
    color: var(--ink) !important;
  }
  html, body, .stApp, p, label, input, button, select, textarea,
  .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stText"], small {
    color: var(--ink) !important;
  }
  .block-container {
    max-width: 1220px !important;
    padding-left: clamp(1rem, 3vw, 2.6rem) !important;
    padding-right: clamp(1rem, 3vw, 2.6rem) !important;
    padding-bottom: 3rem !important;
  }
  h1, h2, h3, h4, .hero-title {
    color: var(--ink) !important;
  }
  .hero-container {
    background: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-top: 0 !important;
    border-radius: 5px 5px 18px 18px !important;
    padding: 25px 28px !important;
    margin: 8px 0 22px !important;
    box-shadow: 0 10px 35px rgba(66, 65, 54, .045) !important;
    position: relative;
  }
  .hero-container:before {
    content: "";
    position: absolute;
    top: 0; left: 28px; right: 28px;
    height: 3px;
    background: linear-gradient(90deg, var(--sage), #C8B9A8, transparent);
  }
  .hero-eyebrow {
    color: var(--sage-dark) !important;
    font-size: .68rem !important;
    font-weight: 700 !important;
    letter-spacing: .19em !important;
  }
  .hero-title {
    font-size: clamp(1.8rem, 3vw, 2.55rem) !important;
    font-weight: 600 !important;
    line-height: 1.18 !important;
    margin: 8px 0 10px !important;
  }
  .hero-pill, .hero-stat-box {
    background: var(--sage-pale) !important;
    border: 1px solid #E2E6DA !important;
    color: var(--sage-dark) !important;
    border-radius: 999px !important;
  }
  .hero-stat-box {
    border-radius: 12px !important;
    min-width: 86px !important;
    padding: 10px 15px !important;
    background: #F8F7F2 !important;
  }
  .hero-stat-val { color: var(--sage-dark) !important; font-weight: 600 !important; }
  .hero-stat-lbl { color: var(--muted) !important; font-size: .62rem !important; letter-spacing: .12em !important; }
  .ny-card, .place-sheet, [data-testid="stExpander"] {
    background: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    box-shadow: 0 5px 18px rgba(66, 65, 54, .035) !important;
  }
  .ny-card { padding: 18px 20px !important; }
  .place-sheet { border-width: 1px !important; padding: 16px 18px !important; }
  .ny-card-header {
    color: var(--sage-dark) !important;
    font-size: .7rem !important;
    letter-spacing: .15em !important;
    font-weight: 700 !important;
  }
  [data-testid="stTabs"] [role="tablist"] {
    gap: 7px !important;
    border-bottom: 1px solid var(--line) !important;
  }
  [data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px 10px 0 0 !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    padding: .65rem .9rem !important;
  }
  [data-testid="stTabs"] button[role="tab"] p { color: inherit !important; }
  [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--sage-dark) !important;
    background: #F0F1EB !important;
    border-color: var(--line) !important;
    border-bottom-color: #F0F1EB !important;
  }
  [data-testid="stButton"] > button, [data-testid="stDownloadButton"] > button {
    border: 1px solid #D9DED2 !important;
    border-radius: 10px !important;
    background: #F1F2EC !important;
    color: #596650 !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: background .18s ease, border-color .18s ease, transform .18s ease !important;
  }
  [data-testid="stButton"] > button:hover, [data-testid="stDownloadButton"] > button:hover {
    background: #E7EADF !important;
    border-color: #BFC9B5 !important;
    color: #46523F !important;
    transform: translateY(-1px);
  }
  [data-testid="stButton"] > button[kind="primary"] {
    background: var(--sage-dark) !important;
    border-color: var(--sage-dark) !important;
    color: white !important;
  }
  [data-testid="stButton"] > button[kind="primary"] * { color: white !important; }
  input:not([type="checkbox"]):not([type="radio"]), textarea,
  [data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background: #FFFEFC !important;
    border-color: #DFDED6 !important;
    border-radius: 9px !important;
  }
  input:not([type="checkbox"]):not([type="radio"]):focus, textarea:focus,
  [data-baseweb="select"] > div:focus-within, [data-baseweb="input"] > div:focus-within {
    border-color: #9AA68F !important;
    box-shadow: 0 0 0 1px #9AA68F !important;
  }
  [data-testid="stExpander"] details summary {
    background: #FBFAF6 !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
    padding: 13px 16px !important;
  }
  [data-testid="stExpander"] details summary:hover { background: #F3F3ED !important; }
  [data-testid="stAlert"] { border-radius: 11px !important; }
  [data-testid="stCaptionContainer"] p, .stCaption { color: var(--muted) !important; }
  hr { border-color: var(--line) !important; }
  div[role="radiogroup"] label {
    background: #FFFEFC !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
  }
  div[role="radiogroup"] label:has(input:checked) {
    background: var(--sage-pale) !important;
    border-color: #B8C2AE !important;
  }
  [data-testid="stCheckbox"] label p { color: var(--ink) !important; }
  @media (max-width: 768px) {
    .hero-container { padding: 22px 17px 17px !important; border-radius: 5px 5px 14px 14px !important; }
    .hero-container:before { left: 17px; right: 17px; }
    .hero-title { font-size: 1.8rem !important; }
    .ny-card, .place-sheet { padding: 13px !important; }
    [data-testid="stTabs"] [role="tablist"] { gap: 2px !important; }
    [data-testid="stTabs"] button[role="tab"] { padding: .55rem .5rem !important; }
  }

  /* TIPOGRAFÍA CALIBRI · mantiene intactos los iconos y símbolos */
  html, body, .stApp,
  .stApp p, .stApp label, .stApp input, .stApp textarea,
  .stApp select, .stApp button,
  .stApp [data-testid="stMarkdownContainer"],
  .stApp [data-testid="stText"],
  .stApp [data-testid="stCaptionContainer"],
  .stApp .stCaption,
  .stApp small, .stApp li, .stApp td, .stApp th,
  .stApp [data-baseweb="select"] *,
  .stApp [data-baseweb="input"] *,
  .stApp [data-baseweb="textarea"] * {
    font-family: Calibri, Carlito, "Segoe UI", Arial, sans-serif !important;
  }
  .stApp h1, .stApp h2, .stApp h3, .stApp h4,
  .stApp .hero-title, .stApp [data-testid="stMarkdownContainer"] h1,
  .stApp [data-testid="stMarkdownContainer"] h2,
  .stApp [data-testid="stMarkdownContainer"] h3 {
    font-family: Calibri, Carlito, "Segoe UI", Arial, sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.018em !important;
  }

  /* ===== Navegación principal: pestañas editoriales ===== */
  .st-key-seccion_principal_activa {
    margin: 14px 0 22px 0 !important;
    padding: 7px !important;
    background: #EEF2EF !important;
    border: 1px solid #E1E8E2 !important;
    border-radius: 17px !important;
    box-shadow: 0 3px 12px rgba(25, 45, 32, 0.045) !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    justify-content: space-between !important;
    gap: 6px !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: auto !important;
    scrollbar-width: none !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"]::-webkit-scrollbar {
    display: none !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label {
    position: relative !important;
    display: flex !important;
    flex: 1 1 0 !important;
    min-width: 0 !important;
    min-height: 48px !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 7px !important;
    margin: 0 !important;
    padding: 9px 11px !important;
    border: 1px solid transparent !important;
    border-radius: 12px !important;
    background: transparent !important;
    color: #647067 !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition: background .18s ease, color .18s ease, box-shadow .18s ease !important;
    white-space: nowrap !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label p,
  .st-key-seccion_principal_activa [role="radiogroup"] label span:not([data-testid]) {
    color: inherit !important;
    font-size: 0.91rem !important;
    font-weight: 650 !important;
    letter-spacing: .005em !important;
    line-height: 1.15 !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label > div:first-child {
    display: none !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:has(input:checked) {
    background: #244C38 !important;
    border-color: #244C38 !important;
    color: #FFFFFF !important;
    box-shadow: 0 3px 9px rgba(36, 76, 56, .18) !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:has(input:checked) p,
  .st-key-seccion_principal_activa [role="radiogroup"] label:has(input:checked) span {
    color: #FFFFFF !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:hover:not(:has(input:checked)) {
    background: rgba(255, 255, 255, .78) !important;
    border-color: #DCE5DD !important;
    color: #244C38 !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:focus-within {
    outline: 2px solid #91B49B !important;
    outline-offset: 2px !important;
  }
  @media (max-width: 680px) {
    .st-key-seccion_principal_activa {
      margin: 10px -2px 18px -2px !important;
      padding: 5px !important;
      border-radius: 14px !important;
    }
    .st-key-seccion_principal_activa [role="radiogroup"] {
      justify-content: flex-start !important;
      gap: 5px !important;
    }
    .st-key-seccion_principal_activa [role="radiogroup"] label {
      flex: 0 0 auto !important;
      min-width: max-content !important;
      min-height: 43px !important;
      padding: 8px 13px !important;
    }
    .st-key-seccion_principal_activa [role="radiogroup"] label p,
    .st-key-seccion_principal_activa [role="radiogroup"] label span:not([data-testid]) {
      font-size: 0.86rem !important;
    }
  }
  .place-full-width-info, .place-full-width-info .place-list-address,
  .place-full-width-info .place-note {
    display: block !important; width: 100% !important; max-width: 100% !important;
    min-width: 0 !important; box-sizing: border-box !important;
    overflow-wrap: anywhere !important; white-space: pre-wrap !important;
  }
  .place-full-width-info { flex: 1 1 100% !important; }
  @media (max-width: 768px) {
    .place-full-width-info, .place-full-width-info .place-list-address,
    .place-full-width-info .place-note { width: 100% !important; max-width: 100% !important; }
  }
  /* ================================================================
     CONTROLES DE RUTA Y GUARDADOS — REGLAS ÚNICAS DE DIMENSIONES
     Este bloque queda al final del CSS para prevalecer sobre los estilos
     generales y responsive. No modificar tamaños desde reglas genéricas.
     ================================================================ */

  /* RUTA: hora | información | editar | mapa | visitado */
  [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: 60px minmax(0, 1fr) 24px 24px 24px !important;
    grid-auto-flow: row !important;
    align-items: center !important;
    justify-content: stretch !important;
    column-gap: 1px !important;
    row-gap: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: visible !important;
  }

  [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  /* Hora: columna y widget con la misma anchura efectiva. */
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) {
    width: 60px !important;
    min-width: 60px !important;
    max-width: 60px !important;
    height: auto !important;
    align-items: flex-start !important;
    margin-right: 3px !important;
  }

  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) [data-testid="stTextInput"],
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) [data-testid="stTextInput"] > div,
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) [data-testid="stTextInput"] > div > div,
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) [data-baseweb="input"],
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) [data-baseweb="base-input"] {
    box-sizing: border-box !important;
    display: block !important;
    width: 60px !important;
    min-width: 60px !important;
    max-width: 60px !important;
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(1) input {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    margin: 0 !important;
    padding: 0 4px !important;
    font-size: 0.88rem !important;
    line-height: 36px !important;
    text-align: center !important;
    font-variant-numeric: tabular-nums !important;
  }

  /* Información: ocupa solo el espacio que queda entre hora y acciones. */
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
    padding: 0 !important;
  }

  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) [data-testid="stMarkdown"],
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) [data-testid="stMarkdown"] > div,
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"],
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) .place-list-title,
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) .place-list-address,
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(2) .place-note {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
  }

  [class*="st-key-it-heading-row-"] .place-list-title {
    font-size: calc(1.25rem - 2pt) !important;
    line-height: 1.18 !important;
  }

  [class*="st-key-it-heading-row-"] .place-list-address,
  [class*="st-key-it-heading-row-"] .place-note {
    position: static !important;
    left: auto !important;
    transform: none !important;
  }

  /* Acciones de Ruta: tres columnas idénticas al checkbox (24px), con 1px entre ellas. */
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(3),
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(4),
  [class*="st-key-it-heading-row-"] [data-testid="stColumn"]:nth-child(5) {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    align-self: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  /* GUARDADOS: información flexible + editar + mapa. */
  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 24px 24px !important;
    grid-auto-flow: row !important;
    align-items: start !important;
    justify-content: stretch !important;
    column-gap: 1px !important;
    row-gap: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stColumn"]:first-child {
    grid-column: 1 / -1 !important;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
  }

  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stColumn"]:nth-child(2) {
    grid-column: 2 !important;
  }

  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stColumn"]:nth-child(3) {
    grid-column: 3 !important;
  }

  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stColumn"]:nth-child(2),
  [class*="st-key-saved-heading-row-"]:not([class*="st-key-saved-heading-row-list-"]) [data-testid="stColumn"]:nth-child(3) {
    width: 12px !important;
    min-width: 12px !important;
    max-width: 12px !important;
    height: 12px !important;
    min-height: 12px !important;
    max-height: 12px !important;
    align-items: center !important;
    justify-content: center !important;
    justify-self: end !important;
    margin: 0 !important;
  }

  /* Acciones de Guardados: botones de 24x24px. */
  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]),
  [class*="st-key-saved-map-button-wrap-"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]) [data-testid="stElementContainer"],
  [class*="st-key-saved-map-button-wrap-"] [data-testid="stElementContainer"],
  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]) [data-testid="stButton"],
  [class*="st-key-saved-map-button-wrap-"] [data-testid="stLinkButton"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]) button,
  [class*="st-key-saved-map-button-wrap-"] a {
    box-sizing: border-box !important;
    display: inline-flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 7px !important;
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
  }

  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]) button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 16px 16px !important;
  }

  [class*="st-key-saved-map-button-wrap-"] a {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15M15 6v15'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 16px 16px !important;
  }

  [class*="st-key-saved-edit-button-wrap-"]:not([class*="st-key-saved-edit-button-wrap-list-"]) button > *,
  [class*="st-key-saved-map-button-wrap-"] a > * {
    display: none !important;
  }

  /* RUTA: editar, mapa y checkbox tienen exactamente 24x24px. */
  [class*="st-key-it-edit-button-wrap-"],
  [class*="st-key-it-map-button-wrap-"],
  [class*="st-key-it-visit-checkbox-wrap-"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    align-self: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-it-edit-button-wrap-"] [data-testid="stElementContainer"],
  [class*="st-key-it-edit-button-wrap-"] [data-testid="stButton"],
  [class*="st-key-it-map-button-wrap-"] [data-testid="stElementContainer"],
  [class*="st-key-it-map-button-wrap-"] [data-testid="stLinkButton"],
  [class*="st-key-it-visit-checkbox-wrap-"] [data-testid="stElementContainer"],
  [class*="st-key-it-visit-checkbox-wrap-"] [data-testid="stCheckbox"] {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-it-edit-button-wrap-"] button,
  [class*="st-key-it-map-button-wrap-"] a {
    box-sizing: border-box !important;
    display: inline-flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 6px !important;
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
  }

  [class*="st-key-it-edit-button-wrap-"] button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 16px 16px !important;
  }

  [class*="st-key-it-map-button-wrap-"] a {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15M15 6v15'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 16px 16px !important;
  }

  [class*="st-key-it-edit-button-wrap-"] button > *,
  [class*="st-key-it-map-button-wrap-"] a > * {
    display: none !important;
  }

  [class*="st-key-it-visit-checkbox-wrap-"] [data-testid="stCheckbox"] > label {
    box-sizing: border-box !important;    
    background-size: 16px 16px !important;
    display: inline-flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 5px !important;
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
    line-height: 0 !important;
    transform: translateY(-4px) !important;
  }

  [class*="st-key-it-visit-checkbox-wrap-"] [data-testid="stCheckbox"] label > div:first-of-type {
    box-sizing: border-box !important;
    display: flex !important;
    flex: none !important;
    width: 24px !important;
    min-width: 24px !important;
    max-width: 24px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    position: relative !important;
  }

  [class*="st-key-it-visit-checkbox-wrap-"] [data-testid="stCheckbox"] label p {
    display: none !important;
  }

  /* GUARDADOS: dos columnas iguales. Solo se dimensionan los controles reales,
     no todos sus contenedores internos (evita capas duplicadas/superpuestas). */
  [class*="st-key-saved-controls-row-"] {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    margin-top: 6px !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    grid-auto-flow: row !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    column-gap: 8px !important;
    row-gap: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-testid="stTextInput"],
  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-testid="stSelectbox"] {
    box-sizing: border-box !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
  }

  /* Altura real de los controles Hora/Día: reducir el control completo,
     no solo el texto. Se dimensiona una única capa visual por widget. */
  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-baseweb="input"],
  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-baseweb="select"] {
    box-sizing: border-box !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: 17px !important;
    min-height: 17px !important;
    max-height: 17px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }

  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-baseweb="input"] input,
  [class*="st-key-saved-controls-row-"] [data-testid="stColumn"] [data-baseweb="select"] [role="combobox"] {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: 10px !important;
    min-height: 10px !important;
    max-height: 10px !important;
    padding: 0 4px !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    line-height: 15px !important;
    text-align: center !important;
    border: 0 !important;
    box-shadow: none !important;
  }

  /* El borde pertenece a la superficie externa de cada widget; no se crea
     un segundo borde en una capa interior, evitando botones duplicados. */
  [class*="st-key-saved-controls-row-"] [data-baseweb="input"],
  [class*="st-key-saved-controls-row-"] [data-baseweb="select"] {
    border: 1px solid #94A3B8 !important;
    border-radius: 7px !important;
    box-shadow: none !important;
    outline: none !important;
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


def etiqueta_dia_guardados(d: int) -> str:
    """Etiqueta compacta del selector de Guardados: Día 1 · 26/12 · S."""
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
    """Escapa el texto de la nota y convierte las URL http(s) y www en enlaces."""
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
    """Devuelve la nota con el mismo estilo pequeño usado debajo de la dirección."""
    contenido = linkificar_nota(nota)
    return f'<div class="place-note">📝 {contenido}</div>' if contenido else ""


# =============================================================================
# 3. MOTOR INTELIGENTE DE CATEGORÍAS
# =============================================================================
CATEGORIAS_CANONICAS = [
    "🍽️ Gastronomía",
    "🍪 Dulces",
    "🍸 Rooftop",
    "🎷 Ocio",
    "🛍️ Compras",
    "🎄 Christmas markets",
    "🏛️ Cultura",
    "☀️ Spots",
    "📍 Otros",
    "🏨 Hotel"
]

MAPA_MIGRACION_CAT = {
    "🍕 Gastronomía": "🍽️ Gastronomía",
    "🍕 Gastronomía & Restaurantes": "🍽️ Gastronomía",
    "🍪 Cafeterías & Dulces": "🍪 Dulces",
    "🍸 Rooftop": "🍸 Rooftop",
    "🎷 Jazz, Música & Ocio": "🎷 Ocio",
    "🛍️ Compras & Outlets": "🛍️ Compras",
    "🏛️ Museos & Monumentos": "🏛️ Cultura",
    "🌲 Parques, Muelles, Rooftops & Puentes": "☀️ Spots",
    "🏨 Hotel Base": "🏨 Hotel",
    "📍 Otros Lugares": "📍 Otros",
    "Otros": "📍 Otros"
}

def normalizar_categoria(cat: str) -> str:
    if not cat:
        return "☀️ Spots"
    if cat in CATEGORIAS_CANONICAS:
        return cat
    if cat in MAPA_MIGRACION_CAT:
        return MAPA_MIGRACION_CAT[cat]
    for c in CATEGORIAS_CANONICAS:
        if c.split()[-1].lower() in cat.lower():
            return c
    return "☀️ Spots"

def clasificar_lugar(nombre: str, direccion: str = "", lista_origen: str = "") -> tuple[str, str]:
    nom = (nombre or "").strip().lower()
    dir_txt = (direccion or "").strip().lower()
    texto_busqueda = f"{nom} {dir_txt}"
    orig = (lista_origen or "").strip().lower()

    # 0. PRIORIDAD MÁXIMA: Clasificación directa por el nombre de la lista de Google Maps
    if orig and orig not in ("google maps", "lista", "sin lista"):
        if 'hotel' in orig or 'alojamiento' in orig:
            return "🏨 Hotel", "Interior"
        if any(k in orig for k in ['christmas', 'holiday', 'navidad', 'mercadillo', 'winter village']):
            tipo_nav = "Interior" if 'santaland' in texto_busqueda else "Exterior"
            return "🎄 Christmas markets", tipo_nav
        if any(k in orig for k in ['ocio', 'jazz', 'música', 'musica', 'teatro', 'show', 'deporte']):
            return "🎷 Ocio", "Interior"
        if any(k in orig for k in ['copas', 'rooftop', 'bar', 'cocktail', 'pub']):
            return "🍸 Rooftop", "Interior"
        if any(k in orig for k in ['dulce', 'sweet', 'cafeter', 'coffee', 'bakery', 'postre', 'helad', 'cookie']):
            return "🍪 Dulces", "Interior"
        if any(k in orig for k in ['compra', 'tienda', 'outlet', 'shop', 'shopping']):
            return "🛍️ Compras", "Interior"
        if any(k in orig for k in ['gastronom', 'food', 'restaurante', 'comer', 'cenar', 'comida']):
            return "🍽️ Gastronomía", "Interior"
        if any(k in orig for k in ['cultura', 'museo', 'monumento', 'historia']):
            return "🏛️ Cultura", "Interior"
        if any(k in orig for k in ['spot', 'parque', 'puente', 'paseo', 'barrio']):
            return "☀️ Spots", "Exterior"

    # 1. Hotel
    if ('hotel' in nom or 'inn' in nom or 'alojamiento' in nom or 'hostel' in nom) and any(k in texto_busqueda for k in ['riu', 'marriott', 'hilton', 'hyatt', 'sheraton', 'base', 'courtyard', 'westin', 'intercontinental']):
        return "🏨 Hotel", "Interior"

    # 2. Christmas markets
    if any(k in texto_busqueda for k in ['christmas market', 'holiday market', 'winter village', 'holiday shops', 'mercadillo navideño', 'mercado navideño', 'navidad', 'santa land', 'santaland', 'dyker heights', 'tree lighting', 'rockefeller tree']):
        tipo_nav = "Interior" if 'santaland' in texto_busqueda else "Exterior"
        return "🎄 Christmas markets", tipo_nav

    # 4. Ocio
    if any(k in texto_busqueda for k in ['jazz', 'blue note', 'smalls', 'mezzrow', 'dizzy', "arthur's tavern", 'jazzcultural', 'village vanguard', 'broadway', 'radio city', 'comedy cellar', 'lincoln center', 'teatro', 'theatre', 'madison square garden', 'barclays center', 'cinema', 'cine', 'nba', 'knicks', 'nets', 'rangers', 'hockey', 'musical', 'concierto', 'concert', 'show', 'club', 'arcade']):
        return "🎷 Ocio", "Interior"

    # 5. Copas
    if any(k in texto_busqueda for k in ['rooftop', 'westlight', 'harriet', 'magic hour', '230 fifth', 'bar 54', 'hudson vu', 'buvette', 'dante', 'speakeasy', 'cocktail', 'wine bar', 'tavern', 'brewery', 'pub', 'lounge', 'biergarten', 'taproom', 'saloon', 'copas']) or ('bar' in nom.split() and 'shake' not in nom and 'salad' not in nom and 'sushi' not in nom) or 'm social' in nom:
        return "🍸 Rooftop", "Interior"

    # 6. Dulces
    if any(k in texto_busqueda for k in ['bakery', 'cookie', 'cookies', 'levain', 'granny', 'caffè panna', 'caffe panna', 'krispy kreme', 'sweets', 'sweet', 'pastry', 'pâtisserie', 'donut', 'doughnut', 'helado', 'ice cream', 'gelato', 'louis vuitton nyc', 'café', 'cafe', 'coffee', 'starbucks', 'magnolia', 'chocolate', 'chocolat', 'cupcake', 'cheesecake', 'crepe', 'waffle', 'boba', 'matcha', 'tea room', 'dulce']):
        return "🍪 Dulces", "Interior"

    # 7. Compras
    if any(k in texto_busqueda for k in ['outlet', 'outlets', 'marshalls', 't.j. maxx', 'tj maxx', 'target', 'macy', 'burlington', 'century 21', 'five below', 'goodwill', 'woodbury', 'jersey gardens', 'grand slam', 'shopping', 'store', 'zara', 'uniqlo', 'tanger', 'apple store', 'sephora', 'nordstrom', 'bloomingdale', 'saks', 'nike', 'adidas', 'lego', 'nintendo', 'fao schwarz', 'thrift', 'vintage', 'mall', 'tienda', 'boutique', 'market', 'bazar', 'souvenir']):
        if 'chelsea market' not in texto_busqueda and 'time out market' not in texto_busqueda and 'christmas market' not in texto_busqueda and 'holiday market' not in texto_busqueda:
            return "🛍️ Compras", "Interior"

    # 8. Gastronomía
    if any(k in texto_busqueda for k in ['pizza', 'pizzeria', 'burger', 'katz', 'dumpling', 'motek', 'piada', 'shake shack', 'chelsea market', 'time out market', 'deli', 'pastrami', 'tacos', 'taco', 'restaurant', 'restaurante', 'trader joe', 'eataly', 'food hall', 'bagel', 'ramen', 'sushi', 'diner', 'smokehouse', 'noodle', 'food', 'steakhouse', 'bistro', 'trattoria', 'osteria', 'grill', 'kitchen', 'bbq', 'barbecue', 'brunch', 'cantina', 'taqueria', 'hot dog', 'lobster', 'seafood']):
        return "🍽️ Gastronomía", "Interior"

    # 9. Cultura
    if any(k in texto_busqueda for k in ['museum', 'museo', 'the met', 'moma', 'guggenheim', 'whitney', 'natural history', 'morgan library', 'tenement', '9/11 memorial', 'oculus', 'grand central', 'library', 'biblioteca', 'atlas', 'one times square', 'times square', 'memorial', 'statue of liberty', 'estatua de la libertad', 'ellis island', 'trinity church', 'rockefeller center', 'st. patrick', 'cathedral', 'catedral', 'church', 'iglesia', 'united nations', 'onu', 'wall street', 'charging bull', 'federal hall', 'chrysler building', 'flatiron', 'empire state', 'gallery', 'galería']):
        tipo = "Exterior" if any(x in texto_busqueda for x in ['times square', 'atlas', 'statue', 'charging bull', 'wall street', 'memorial']) else "Interior"
        return "🏛️ Cultura", tipo

    # 10. Spots
    if any(k in texto_busqueda for k in ['park', 'parque', 'central park', 'bryant park', 'washington square', 'bridge', 'puente', 'brooklyn bridge', 'manhattan bridge', 'high line', 'little island', 'fulton ferry', 'domino', 'pier 17', 'pier 57', 'pier 35', 'pier', 'muelle', 'pebble beach', 'tudor city', 'squibb', 'battery', 'waterfront', 'picnic', 'botanic', 'coney island', 'boardwalk', 'dumbo', 'soho', 'west village', 'greenwich', 'chinatown', 'little italy', 'hudson yards', 'vessel', 'roosevelt island', 'tram', 'ferry', 'spot', 'mirador callejero']):
        return "☀️ Spots", "Exterior"

    # 11. Otros (fallback cuando no encaja en ninguna categoría anterior ni en el nombre de lista)
    return "📍 Otros", "Exterior"

def selectbox_sin_teclado(*args, **kwargs):
    """Selectbox sin búsqueda de texto: el móvil solo muestra las opciones.

    Para garantizarlo en el despliegue, usar Streamlit >= 1.67.0
    (filter_mode=None). La sincronización automática usa st.fragment.
    """
    kwargs.setdefault("filter_mode", None)
    try:
        return st.selectbox(*args, **kwargs)
    except TypeError as exc:
        # Compatibilidad con versiones de Streamlit anteriores a filter_mode.
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
        if re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", h):
            partes = h.split(":")
            return (0, int(partes[0]) * 60 + int(partes[1]), str(item.get("id", 0)))
        return (1, 9999, str(item.get("id", 0)))
    return sorted(lista_sitios, key=clave_orden)


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
def _github_configuracion():
    """Lee la configuración opcional de persistencia desde Streamlit Secrets."""
    try:
        token = str(st.secrets.get("GITHUB_TOKEN", "")).strip()
        repo = str(st.secrets.get("GITHUB_REPO", "")).strip()
        branch = str(st.secrets.get("GITHUB_BRANCH", "main")).strip() or "main"
        return token, repo, branch
    except Exception:
        return "", "", "main"


def _github_request(ruta_repo: str, metodo: str = "GET", datos=None):
    """Accede a un archivo del repositorio mediante GitHub Contents API."""
    import base64

    token, repo, branch = _github_configuracion()
    if not token or not repo or "/" not in repo:
        return None

    ruta = urllib.parse.quote(ruta_repo, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    if metodo == "GET":
        url += "?ref=" + urllib.parse.quote(branch)
    payload = None
    if datos is not None:
        payload = json.dumps(datos, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method=metodo,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "streamlit-itinerario-viaje",
            **({"Content-Type": "application/json"} if payload is not None else {})
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            resultado = json.loads(response.read().decode("utf-8"))
        if metodo == "GET":
            contenido = base64.b64decode(resultado["content"]).decode("utf-8")
            return json.loads(contenido), resultado.get("sha")
        return True
    except urllib.error.HTTPError as exc:
        if metodo == "GET" and exc.code == 404:
            return None, None
        detalle = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub respondió {exc.code}: {detalle}") from exc


def _cargar_json_persistente(ruta: str):
    """
    GitHub es la fuente de verdad cuando está configurado.
    Nunca sustituye un error remoto por una copia local potencialmente vacía/antigua.
    """
    token, repo, _ = _github_configuracion()
    if token and repo:
        try:
            remoto = _github_request(ruta, "GET")
            if remoto is None:
                raise RuntimeError(
                    "No se pudo consultar GitHub: revisa GITHUB_TOKEN y GITHUB_REPO."
                )
            datos_remotos, _sha = remoto
            try:
                st.session_state[f"_github_sha_{ruta}"] = _sha
            except Exception:
                pass
            if datos_remotos is not None:
                # Validar la forma esperada antes de aceptar el contenido remoto.
                if ruta == ARCH_ITINERARIO and not isinstance(datos_remotos, list):
                    raise RuntimeError(f"{ruta} no contiene una lista JSON válida.")
                if ruta == ARCH_CONFIG and not isinstance(datos_remotos, dict):
                    raise RuntimeError(f"{ruta} no contiene un objeto JSON válido.")
                _guardar_json_atomico(ruta, datos_remotos)
                return datos_remotos

            # El archivo aún no existe en GitHub: migración inicial controlada
            # desde el disco local, si existe y contiene JSON válido.
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    datos_locales = json.load(f)
                if ruta == ARCH_ITINERARIO and not isinstance(datos_locales, list):
                    raise RuntimeError(f"La copia local de {ruta} no es una lista JSON.")
                if ruta == ARCH_CONFIG and not isinstance(datos_locales, dict):
                    raise RuntimeError(f"La copia local de {ruta} no es un objeto JSON.")
                if not _guardar_json_persistente(ruta, datos_locales):
                    raise RuntimeError(
                        f"No se pudo migrar {ruta} a GitHub. No se usará una copia local como si estuviera sincronizada."
                    )
                return datos_locales
            return None
        except Exception as exc:
            # Fallar de forma segura: no cargar una copia local vieja que luego
            # pueda sobrescribir el itinerario compartido.
            raise RuntimeError(
                f"No se pudieron leer los datos persistentes ({os.path.basename(ruta)}) desde GitHub: {exc}"
            ) from exc

    # Modo local solo cuando no hay configuración remota.
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            st.warning(f"No se pudo leer {ruta}: {exc}")
    return None


def _guardar_json_persistente(ruta: str, datos):
    """
    Si GitHub está configurado, primero confirma allí el cambio.
    El disco local es solo una caché; nunca se considera un guardado persistente
    hasta recibir confirmación de GitHub.
    """
    token, repo, branch = _github_configuracion()
    if not (token and repo):
        return _guardar_json_atomico(ruta, datos)

    import base64
    try:
        remoto = _github_request(ruta, "GET")
        if remoto is None:
            raise RuntimeError(
                "No se pudo leer el archivo remoto para obtener su SHA. No se ha sobrescrito nada."
            )
        datos_remotos, sha = remoto

        # Control optimista: impide que una sesión antigua sobrescriba cambios
        # remotos realizados desde su última lectura.
        try:
            clave_sha = f"_github_sha_{ruta}"
            sha_conocido = st.session_state.get(clave_sha, None)
            if clave_sha in st.session_state and sha_conocido != sha:
                raise RuntimeError("Conflicto de sincronización: el archivo cambió en otro dispositivo. Recarga antes de guardar.")
        except RuntimeError:
            raise
        except Exception:
            pass

        # Evita que una sesión vacía por error borre accidentalmente un itinerario
        # que ya existe en GitHub. El borrado total debe hacerse de forma deliberada
        # desde GitHub, no como efecto secundario de una sesión recién iniciada.
        if (
            ruta == ARCH_ITINERARIO
            and isinstance(datos_remotos, list)
            and len(datos_remotos) > 0
            and isinstance(datos, list)
            and len(datos) == 0
        ):
            raise RuntimeError(
                "Protección activada: GitHub contiene lugares y esta sesión intenta guardar una lista vacía. "
                "No se ha sobrescrito el itinerario."
            )

        contenido = base64.b64encode(
            json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii")
        url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(ruta, safe='/')}"
        cuerpo = {
            "message": f"Actualizar datos del viaje: {os.path.basename(ruta)}",
            "content": contenido,
            "branch": branch
        }
        if sha:
            cuerpo["sha"] = sha
        req = urllib.request.Request(
            url, data=json.dumps(cuerpo).encode("utf-8"), method="PUT",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "streamlit-itinerario-viaje",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            respuesta = json.loads(response.read().decode("utf-8"))
        nuevo_sha = respuesta.get("content", {}).get("sha")
        if not nuevo_sha:
            raise RuntimeError("GitHub no confirmó el guardado del archivo.")
        try:
            st.session_state[f"_github_sha_{ruta}"] = nuevo_sha
        except Exception:
            pass

        # Actualizar caché local solo después de confirmar la escritura remota.
        _guardar_json_atomico(ruta, datos)
        return True
    except Exception as exc:
        st.error(
            f"NO se ha confirmado el guardado en GitHub ({os.path.basename(ruta)}). "
            f"Los datos de esta sesión no están protegidos frente a un redeploy. "
            f"No cierres la sesión hasta resolverlo. Detalle: {exc}"
        )
        return False


def cargar_config_viaje():
    datos = _cargar_json_persistente(ARCH_CONFIG)
    if isinstance(datos, dict):
        return datos
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
    """Escribe JSON atómicamente en el disco local como caché/respaldo."""
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
    except Exception as exc:
        try:
            if temporal and os.path.exists(temporal):
                os.remove(temporal)
        except Exception:
            pass
        try:
            st.error(f"No se pudieron guardar los datos locales ({os.path.basename(ruta)}): {exc}")
        except Exception:
            pass
        return False


def guardar_config_viaje(cfg):
    return _guardar_json_persistente(ARCH_CONFIG, cfg)


def cargar_itinerario_disco():
    datos = _cargar_json_persistente(ARCH_ITINERARIO)
    if isinstance(datos, list):
        normalizados = []
        ids_vistos = set()
        modificado = False
        for registro in datos:
            lugar = _validar_lugar(registro)
            if lugar is None:
                modificado = True
                logger.warning("Se omitió un registro de itinerario inválido.")
                continue
            base_id = str(lugar.get("id"))
            if base_id in ids_vistos:
                lugar["id"] = f"{base_id}-{hashlib.sha1((lugar['nombre'] + str(lugar['lat']) + str(lugar['lon'])).encode()).hexdigest()[:6]}"
                modificado = True
            ids_vistos.add(str(lugar["id"]))
            normalizados.append(lugar)
            if lugar != registro:
                modificado = True
        if modificado:
            # La normalización local no debe sobrescribir automáticamente el remoto.
            _guardar_json_atomico(ARCH_ITINERARIO, normalizados)
        return normalizados
    return []


def guardar_itinerario_disco(lugares):
    """Guarda el itinerario en disco y en GitHub si se configuró persistencia."""
    return _guardar_json_persistente(ARCH_ITINERARIO, lugares)


def actualizar_hora_itinerario(dia: int, lugar_id):
    """Guarda el cambio de hora desde el evento del widget, antes del rerun."""
    clave_widget = f"hora_it_{dia}_{lugar_id}"
    hora_nueva = str(st.session_state.get(clave_widget, "") or "").strip()

    # Mantiene la validación HH:MM y normaliza, por ejemplo, 9:30 a 09:30.
    if hora_nueva and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hora_nueva):
        return
    if hora_nueva and len(hora_nueva) == 4:
        hora_nueva = "0" + hora_nueva

    lugar = next(
        (x for x in st.session_state.get("lugares", []) if str(x.get("id")) == str(lugar_id)),
        None
    )
    if lugar is None:
        return

    hora_anterior = str(lugar.get("hora", "") or "").strip()
    if hora_nueva == hora_anterior:
        return

    lugar["hora"] = hora_nueva
    if guardar_itinerario_disco(st.session_state.lugares):
        st.session_state[clave_widget] = hora_nueva
    else:
        # Si el guardado persistente falla, no dejamos una hora falsa en la sesión.
        lugar["hora"] = hora_anterior
        st.session_state[clave_widget] = hora_anterior


def _huella_datos(datos) -> str:
    """Firma estable para detectar cambios escritos desde otro navegador."""
    try:
        return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        return repr(datos)


def sincronizar_config_desde_disco():
    """Recarga vuelos, hotel y listas de Google Maps si otra sesión los ha editado."""
    nueva_config = cargar_config_viaje()
    config_actual = st.session_state.get("config_viaje")
    if config_actual is None or _huella_datos(config_actual) != _huella_datos(nueva_config):
        st.session_state.config_viaje = nueva_config
        # Cierra el editor de lista que pudiera estar abierto. Las claves de
        # formulario incluyen la huella del nombre/URL para reconstruirse con
        # los valores nuevos sin tocar widgets que ya se hayan renderizado.
        st.session_state.lista_gmaps_editando = None
        return True
    return False


def sincronizar_lugares_desde_disco():
    """Actualiza la sesión si otro dispositivo ha cambiado el itinerario compartido."""
    nuevos = cargar_itinerario_disco()
    anteriores = st.session_state.get("lugares")
    if anteriores is None:
        st.session_state.lugares = nuevos
        return True

    if _huella_datos(anteriores) == _huella_datos(nuevos):
        return False

    antes_por_id = {str(x.get("id")): x for x in anteriores if isinstance(x, dict) and x.get("id") is not None}
    nuevos_por_id = {str(x.get("id")): x for x in nuevos if isinstance(x, dict) and x.get("id") is not None}
    ids_cambiados = set(antes_por_id) | set(nuevos_por_id)
    ids_cambiados = {
        pid for pid in ids_cambiados
        if _huella_datos(antes_por_id.get(pid)) != _huella_datos(nuevos_por_id.get(pid))
    }

    # Los widgets mantienen su valor dentro de cada sesión. Al cambiar un lugar
    # desde otro dispositivo, eliminamos solo sus claves para que se reconstruyan
    # con la hora/día/estado más recientes del archivo compartido.
    prefijos_widget_lugar = (
        "mvd_it_", "asig_dia_pool_", "hora_it_", "hora_pool_",
        "sel_d_sheet_", "hora_sheet_", "chk_it_"
    )
    for clave in list(st.session_state.keys()):
        nombre_clave = str(clave)
        if nombre_clave.startswith(prefijos_widget_lugar) and any(
            nombre_clave.endswith(f"_{pid}") for pid in ids_cambiados
        ):
            try:
                del st.session_state[clave]
            except Exception:
                pass

    st.session_state.lugares = nuevos
    ids_actuales = {x.get("id") for x in nuevos if isinstance(x, dict)}
    if st.session_state.get("lugar_activo_id") not in ids_actuales:
        st.session_state.lugar_activo_id = None
    return True


# =============================================================================
# 6. SINCRONIZADOR DE LISTAS DE GOOGLE MAPS 
# =============================================================================
def extraer_lugares_lista_gmaps(url_lista: str, nombre_lista: str = ""):
    import http.cookiejar

    url_limpia = (url_lista or "").strip()
    if not url_limpia or not _validar_url_google_maps(url_limpia):
        return []

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "es-ES,es;q=0.9,en;q=0.8"),
        ("Cookie", "CONSENT=YES+cb.20230531-07-p0.es+FX+999; SOCS=CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVzIAEaBgiA_LyaBg"),
    ]

    encontrados = []
    vistos = set()
    titulo_detectado = (nombre_lista or "").strip()

    def _limpiar_titulo_gmaps(raw_title: str) -> str:
        t = html.unescape(str(raw_title or "")).strip()
        t = re.sub(r"\s*-\s*Google\s*Maps\s*$", "", t, flags=re.IGNORECASE).strip()
        if t.lower() in ("google maps", "maps", ""):
            return ""
        return t

    def _agregar(nombre, lat, lon, direccion=""):
        nombre = re.sub(r"\s+", " ", str(nombre or "")).strip(" ,\t\r\n")
        if not nombre or len(nombre) < 2:
            return
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return
        clave = re.sub(r"[^a-z0-9]+", "", nombre.casefold())
        if not clave or clave in vistos:
            return
        vistos.add(clave)
        origen_efectivo = f"{nombre_lista} {titulo_detectado}".strip()
        cat, tipo = clasificar_lugar(nombre, direccion, origen_efectivo)
        encontrados.append({
            "nombre": nombre,
            "lat": lat,
            "lon": lon,
            "direccion": str(direccion or "").strip(),
            "nota": "",
            "categoria": cat,
            "tipo": tipo,
            "hora": "",
            "lista_origen": titulo_detectado or nombre_lista or "",
        })

    try:
        with opener.open(url_limpia, timeout=12) as respuesta:
            url_final = respuesta.geturl()
            pagina = respuesta.read().decode("utf-8", errors="ignore")

        # 1. Extraer título de la lista desde og:title o title
        for pat_tit in (
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r'<title>([^<]+)</title>',
        ):
            m_tit = re.search(pat_tit, pagina, flags=re.IGNORECASE)
            if m_tit:
                cand = _limpiar_titulo_gmaps(m_tit.group(1))
                if cand:
                    if not titulo_detectado or titulo_detectado.lower() in ("google maps", "lista", "sin lista"):
                        titulo_detectado = cand
                    break

        # 2. Extraer rutas getlist limpiando correctamente los escapes unescaped de JSON/JavaScript
        patrones = (
            r'href=["\'](/maps/preview/entitylist/getlist\?[^"\']+)["\']',
            r'((?:https://www\.google\.com)?/maps/preview/entitylist/getlist\?[^"\'\\<>]+)',
            r'(\\?/maps\\?/preview\\?/entitylist\\?/getlist\\?[^"\'<>]+)',
        )
        rutas = []
        for patron in patrones:
            rutas.extend(re.findall(patron, pagina))
        
        rutas = list(dict.fromkeys(rutas))

        if not rutas:
            m_lugar = re.search(r"/place/([^/@?]+)", url_final)
            if m_lugar:
                nombre = urllib.parse.unquote_plus(m_lugar.group(1)).replace("+", " ").strip()
                m_coords = re.search(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", url_final)
                if m_coords:
                    _agregar(nombre, m_coords.group(1), m_coords.group(2))
                else:
                    lat, lon, direccion = geocodificar_direccion_o_nombre(f"{nombre}, New York")
                    if lat is not None and lon is not None:
                        _agregar(nombre, lat, lon, direccion)
            return encontrados

        for ruta in rutas:
            # CORRECCIÓN DE UNESCAPE DE RUTAS GOOGLE:
            ruta_clean = (
                html.unescape(ruta)
                .replace("\\u0026", "&")
                .replace("\\u003d", "=")
                .replace("\\/", "/")
                .replace("\\?", "?")
                .replace("\\", "")  # Eliminar barras invertidas sobrantes
            )
            if ruta_clean.startswith("http"):
                endpoint = ruta_clean
            else:
                endpoint = "https://www.google.com" + (ruta_clean if ruta_clean.startswith("/") else "/" + ruta_clean)

            try:
                with _abrir_url_google_maps(endpoint, headers=dict(opener.addheaders), timeout=12) as respuesta_lista:
                    raw = respuesta_lista.read().decode("utf-8", errors="ignore")
                raw = re.sub(r"^\)\]\}'\s*", "", raw)
                data = json.loads(raw)
                
                if isinstance(data, list) and data and isinstance(data[0], list):
                    for idx_cand in (4, 1, 2):
                        if len(data[0]) > idx_cand and isinstance(data[0][idx_cand], str):
                            cand_json = _limpiar_titulo_gmaps(data[0][idx_cand])
                            if cand_json and len(cand_json) >= 3 and not cand_json.startswith(("http", "ChIJ", "/")):
                                if not titulo_detectado or titulo_detectado.lower() in ("google maps", "lista", "sin lista"):
                                    titulo_detectado = cand_json
                                break
            except Exception:
                continue

            def _recorrer(nodo):
                try:
                    if isinstance(nodo, dict):
                        for valor in nodo.values():
                            _recorrer(valor)
                        return

                    if not isinstance(nodo, list):
                        return

                    coords = None
                    for elemento in nodo:
                        if (
                            isinstance(elemento, list) and len(elemento) >= 4
                            and elemento[0] is None and elemento[1] is None
                            and isinstance(elemento[2], (int, float))
                            and isinstance(elemento[3], (int, float))
                        ):
                            coords = (elemento[2], elemento[3])
                            break

                    if coords:
                        textos = [
                            str(x).strip() for x in nodo
                            if isinstance(x, str) and len(str(x).strip()) > 1
                            and not str(x).strip().startswith(("http", "ChIJ", "/g/", "/m/", "0x"))
                        ]
                        if textos:
                            nombre_raw = textos[0]
                            partes = nombre_raw.split(",", 1)
                            nombre = partes[0].strip()
                            direccion = partes[1].strip() if len(partes) > 1 else (
                                textos[1] if len(textos) > 1 else ""
                            )
                            _agregar(nombre, coords[0], coords[1], direccion)

                    for hijo in nodo:
                        if isinstance(hijo, (list, dict)):
                            _recorrer(hijo)
                except Exception:
                    pass

            _recorrer(data)

    except Exception as exc:
        try:
            st.warning(f"Aviso de sincronización ({nombre_lista}): {exc}")
        except Exception:
            pass

    return encontrados


def ejecutar_sincronizacion_listas_gmaps():
    lugares_antes_sync = copy.deepcopy(st.session_state.get("lugares", []))
    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")
        return
    total_nuevos = 0
    total_actualizados = 0
    total_descargados = 0
    errores_sync = []
    nuevos_ids = []

    def _clave_lugar_sync(nombre, lat, lon):
        nombre_n = re.sub(r"\s+", " ", str(nombre or "").strip().casefold())
        try:
            return (nombre_n, round(float(lat), 5), round(float(lon), 5))
        except (TypeError, ValueError):
            return (nombre_n, None, None)

    mapa_existentes_sync = {
        _clave_lugar_sync(x.get("nombre"), x.get("lat"), x.get("lon")): x
        for x in st.session_state.lugares if isinstance(x, dict)
    }
    ids_sync = []
    for x in st.session_state.lugares:
        try:
            ids_sync.append(int(x.get("id", 0)))
        except (TypeError, ValueError, AttributeError):
            pass
    max_id_sync = max(ids_sync, default=0)

    with st.spinner("Sincronizando todas las listas de Google Maps y clasificando lugares..."):
        for i_lista, datos_lista in enumerate(listas_config):
            nom_lista = str(datos_lista.get("nombre", f"Lista {i_lista + 1}"))
            url_lista_sync = str(datos_lista.get("url", "")).strip()
            if not url_lista_sync:
                errores_sync.append(f"{nom_lista}: falta la URL")
                continue
            try:
                descargados_lista = extraer_lugares_lista_gmaps(url_lista_sync, nom_lista)
                total_descargados += len(descargados_lista or [])
                for item_sync in descargados_lista or []:
                    nombre_sync = str(item_sync.get("nombre", "")).strip()
                    if not nombre_sync:
                        continue
                    dir_sync = str(item_sync.get("direccion", "")).strip()
                    origen_sync = str(item_sync.get("lista_origen") or nom_lista).strip()
                    cat_clasif, tipo_clasif = clasificar_lugar(nombre_sync, dir_sync, origen_sync)
                    cat_final = normalizar_categoria(cat_clasif)
                    clave_sync = _clave_lugar_sync(nombre_sync, item_sync.get("lat"), item_sync.get("lon"))
                    existente = mapa_existentes_sync.get(clave_sync)
                    if existente is None:
                        nombre_norm_sync = re.sub(r"\s+", " ", nombre_sync.casefold())
                        for (k_nom, _, _), cand_ex in mapa_existentes_sync.items():
                            if k_nom == nombre_norm_sync:
                                existente = cand_ex
                                break
                    if existente is not None:
                        cambio_item = False
                        if dir_sync and not existente.get("direccion"):
                            existente["direccion"] = dir_sync
                            cambio_item = True
                        if origen_sync and existente.get("lista_origen") != origen_sync:
                            existente["lista_origen"] = origen_sync
                            cambio_item = True
                        # No sobrescribir la categoría de un sitio que ya estaba guardado.
                        if existente.get("tipo") != tipo_clasif:
                            existente["tipo"] = tipo_clasif
                            cambio_item = True
                        if cambio_item:
                            total_actualizados += 1
                        continue
                    max_id_sync += 1
                    nuevo_lugar_sync = {
                        "id": max_id_sync,
                        "nombre": nombre_sync,
                        "lat": float(item_sync.get("lat", 40.7580)),
                        "lon": float(item_sync.get("lon", -73.9855)),
                        "dia": 0,
                        "hora": "",
                        "direccion": dir_sync,
                        "nota": "",
                        "categoria": cat_final,
                        "tipo": tipo_clasif,
                        "lista_origen": origen_sync,
                        "visitado": False
                    }
                    st.session_state.lugares.append(nuevo_lugar_sync)
                    mapa_existentes_sync[clave_sync] = nuevo_lugar_sync
                    nuevos_ids.append(max_id_sync)
                    total_nuevos += 1
            except Exception as exc:
                errores_sync.append(f"{nom_lista}: {exc}")

        # Las categorías de los sitios ya existentes son datos elegidos/guardados:
        # la sincronización de Google Maps solo añade sitios nuevos y completa
        # campos vacíos (p. ej. dirección), pero nunca reclasifica los existentes.
        # Los sitios nuevos ya llegan clasificados al crearse en el bloque anterior.

    # GUARDADO PERSISTENTE EN DISCO / GITHUB AL TERMINAR
    if total_nuevos > 0 or total_actualizados > 0:
        if not guardar_itinerario_disco(st.session_state.lugares):
            st.session_state.lugares = lugares_antes_sync
            st.session_state["_msg_sync_guardados"] = ("error", "No se pudo guardar la sincronización. Se han restaurado los datos anteriores.")
            st.rerun()
            return

    if nuevos_ids:
        prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
        st.session_state.nuevos_lugares_ids = list(dict.fromkeys(nuevos_ids + prev_nuevos))

    if errores_sync:
        st.session_state["_errores_sync_guardados"] = errores_sync
    
    st.session_state["_msg_sync_guardados"] = ("success", f"¡Sincronización completada! {total_nuevos} lugares nuevos añadidos y {total_actualizados} actualizados.")
    st.rerun()

# =============================================================================
# 6B. HERRAMIENTAS PARA AÑADIR Y EDITAR LUGARES
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def geocodificar_direccion_o_nombre(texto: str) -> tuple:
    if not texto:
        return None, None, ""
    q = f"{texto}, New York, NY".strip()
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'ny_holiday_planner_app_v5'})
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
                            categoria: str = None, tipo: str = None, dia_dest: int = 0, hora: str = "", nota: str = "") -> tuple:
    nom = (nombre or "").strip()
    if not nom:
        return False, "El nombre del lugar no puede estar vacío."

    if lat is None or lon is None or (lat == 0 and lon == 0):
        geo_lat, geo_lon, geo_dir = geocodificar_direccion_o_nombre(f"{nom} {direccion}")
        if geo_lat is None or geo_lon is None:
            # Permite guardar nombres sin una ubicación concreta.
            # Se usa el centro de referencia de Nueva York para que el registro
            # siga siendo compatible con el mapa; no se inventa una dirección.
            lat, lon = 40.7580, -73.9855
        else:
            lat, lon = geo_lat, geo_lon
            if not direccion and geo_dir:
                direccion = geo_dir

    if not categoria or categoria == "⚡ Detección Automática":
        cat_auto, tipo_auto = clasificar_lugar(nom, direccion)
        categoria = cat_auto
        if not tipo:
            tipo = tipo_auto

    if not tipo:
        tipo = "Interior"
    try:
        lat, lon = float(lat), float(lon)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False, "Las coordenadas están fuera de los rangos geográficos válidos."
    except (TypeError, ValueError):
        return False, "Las coordenadas no son válidas."
    if hora and not re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", str(hora).strip()):
        return False, "Formato de hora inválido. Usa HH:MM."

    ids_numericos = []
    for existente in st.session_state.lugares:
        try:
            ids_numericos.append(int(existente.get("id", 0)))
        except (TypeError, ValueError, AttributeError):
            continue
    max_id = max(ids_numericos, default=0) + 1
    ids_existentes = {str(x.get("id")) for x in st.session_state.lugares if isinstance(x, dict)}
    while str(max_id) in ids_existentes:
        max_id += 1
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
    if not guardar_itinerario_disco(st.session_state.lugares):
        st.session_state.lugares.pop()
        return False, "No se pudo guardar el lugar en el archivo compartido. No se ha añadido; revisa los permisos de escritura."
    prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
    st.session_state.nuevos_lugares_ids = list(dict.fromkeys([max_id] + prev_nuevos))
    return True, f"¡'{nom}' añadido con éxito como {nuevo['categoria']}!"

def importar_sitio_desde_gmaps(url_o_texto: str, dia_dest: int = 0, hora: str = "", nota: str = "") -> tuple:
    raw = url_o_texto.strip()
    if not raw:
        return False, "Introduce un enlace de Google Maps válido."

    if _validar_url_google_maps(raw):
        lugares_lst = extraer_lugares_lista_gmaps(raw, "")
        if lugares_lst:
            existentes = {str(x.get("nombre", "")).strip().casefold() for x in st.session_state.lugares}
            nuevos = 0
            ids_numericos = []
            for existente in st.session_state.lugares:
                try:
                    ids_numericos.append(int(existente.get("id", 0)))
                except (TypeError, ValueError, AttributeError):
                    continue
            max_id = max(ids_numericos, default=0)
            for s in lugares_lst:
                clave_nombre = str(s.get("nombre", "")).strip().casefold()
                if clave_nombre and clave_nombre not in existentes:
                    max_id += 1
                    s["id"] = max_id
                    s["dia"] = dia_dest
                    s["hora"] = (hora or "").strip()
                    s["nota"] = (nota or "").strip()
                    s["visitado"] = False
                    st.session_state.lugares.append(s)
                    existentes.add(s["nombre"].strip().casefold())
                    nuevos += 1
            if nuevos > 0:
                ids_imp = [x["id"] for x in st.session_state.lugares[-nuevos:]]
                if not guardar_itinerario_disco(st.session_state.lugares):
                    # Si el guardado remoto falla, no damos la importación por hecha.
                    st.session_state.lugares = cargar_itinerario_disco()
                    return False, "No se pudieron guardar en GitHub los lugares importados. No se ha confirmado la importación."
                prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
                st.session_state.nuevos_lugares_ids = list(dict.fromkeys(ids_imp + prev_nuevos))
                return True, f"¡Se importaron {nuevos} lugares desde la lista de Google Maps!"

    nombre_extraido = ""
    lat_ext, lon_ext = None, None
    dir_ext = ""

    if raw.startswith("http://") or raw.startswith("https://"):
        if not _validar_url_google_maps(raw):
            return False, "El enlace debe pertenecer a un dominio oficial de Google Maps."
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        try:
            with _abrir_url_google_maps(raw, headers=headers, timeout=6) as r:
                url_final = r.geturl()
                html = r.read().decode('utf-8', errors='ignore')

                m_coords = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url_final)
                if m_coords:
                    lat_ext = float(m_coords.group(1))
                    lon_ext = float(m_coords.group(2))

                m_nom = re.search(r"/place/([^/@?]+)", url_final)
                if m_nom:
                    nombre_extraido = urllib.parse.unquote_plus(m_nom.group(1)).replace("+", " ")
                elif "<title>" in html:
                    m_tit = re.search(r"<title>([^<]+)</title>", html)
                    if m_tit:
                        nombre_extraido = m_tit.group(1).replace("- Google Maps", "").replace("· Google Maps", "").strip()
        except Exception:
            pass

    if not nombre_extraido:
        nombre_extraido = raw.split("/")[-1].replace("+", " ")
        if len(nombre_extraido) < 3 or nombre_extraido.startswith("http"):
            nombre_extraido = "Lugar Google Maps"

    return agregar_sitio_a_lugares(nombre_extraido, dir_ext, lat_ext, lon_ext, None, None, dia_dest, hora, nota)

def render_editor_sitio_panel(spot: dict, idx_real: int, key_ctx: str):
    """Panel desplegable para editar nombre, dirección, nota manual, hora, categoría, día y coords."""
    edit_key = f"{key_ctx}_{spot['id']}"
    if st.session_state.get("editando_spot_key") != edit_key:
        return

    with st.container():
        st.markdown(
            f"<div style='background:#F8FAFC; border:1.5px solid #94A3B8; border-radius:12px; padding:9px 11px; margin:6px 0 8px 0;'>"
            f"<b>✏️ Editando: {html.escape(str(spot.get('nombre', '')))}</b></div>",
            unsafe_allow_html=True
        )
        with st.form(f"form_edit_spot_{edit_key}"):
            ce1, ce2 = st.columns(2)
            with ce1:
                ed_nom = st.text_input("Nombre del lugar:", value=spot.get("nombre", ""))
                ed_dir = st.text_input("Dirección / Barrio:", value=spot.get("direccion", ""))
                ed_nota = st.text_input(
                    "Nota manual (aparece debajo de la dirección):",
                    value=spot.get("nota", ""),
                    placeholder="Ej: Pedir galleta de chocolate, ir antes de las 18h..."
                )
            with ce2:
                ed_hora = st.text_input("Hora (HH:MM, ej. 10:30):", value=spot.get("hora", ""), placeholder="HH:MM")
                cat_act = normalizar_categoria(spot.get("categoria", "📍 Otros"))
                idx_c = CATEGORIAS_CANONICAS.index(cat_act) if cat_act in CATEGORIAS_CANONICAS else 0
                ed_cat = selectbox_sin_teclado("Categoría:", CATEGORIAS_CANONICAS, index=idx_c)

                tipo_act = spot.get("tipo", "Interior")
                ed_tipo = selectbox_sin_teclado("Entorno:", ["Interior", "Exterior"], index=0 if tipo_act == "Interior" else 1)

                dias_opts = ["📌Guardados"] + [etiqueta_dia(d) for d in range(1, 11)]
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
                # Recalcular el índice por ID al enviar: evita editar/eliminar otro
                # elemento si la lista se ha actualizado durante un rerun.
                idx_guardar = next(
                    (i for i, x in enumerate(st.session_state.lugares)
                     if str(x.get("id")) == str(spot.get("id"))),
                    None
                )
                if idx_guardar is None:
                    st.error("Este lugar ya no está en el itinerario. Actualiza la página y vuelve a intentarlo.")
                    st.stop()
                hora_limpia = ed_hora.strip()
                if hora_limpia and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hora_limpia):
                    st.error("Formato de hora inválido. Usa HH:MM (ej. 09:30) o déjalo vacío.")
                else:
                    if hora_limpia and len(hora_limpia) == 4:
                        hora_limpia = "0" + hora_limpia
                    nuevo_dia = 0 if "Guardados" in ed_dia_str else int(re.search(r"Día (\d+)", ed_dia_str).group(1))
                    if not (-90 <= float(ed_lat) <= 90 and -180 <= float(ed_lon) <= 180):
                        st.error("Las coordenadas deben estar entre -90/90 de latitud y -180/180 de longitud.")
                    else:
                        anterior = dict(st.session_state.lugares[idx_guardar])
                        st.session_state.lugares[idx_guardar].update({
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
                        if guardar_itinerario_disco(st.session_state.lugares):
                            st.session_state.editando_spot_key = None
                            st.toast(f"¡'{ed_nom}' actualizado!", icon="✅")
                            st.rerun()
                        else:
                            st.session_state.lugares[idx_guardar] = anterior
                            st.error("No se pudo guardar el cambio. Se han restaurado los datos anteriores.")

            if eliminar_ed:
                idx_borrar = next(
                    (i for i, x in enumerate(st.session_state.lugares)
                     if str(x.get("id")) == str(spot.get("id"))),
                    None
                )
                if idx_borrar is None:
                    st.error("Este lugar ya no está en el itinerario. Actualiza la página y vuelve a intentarlo.")
                    st.stop()
                nom_borrado = spot["nombre"]
                eliminado = st.session_state.lugares.pop(idx_borrar)
                if guardar_itinerario_disco(st.session_state.lugares):
                    if st.session_state.lugar_activo_id == spot["id"]:
                        st.session_state.lugar_activo_id = None
                    st.session_state.editando_spot_key = None
                    st.toast(f"Sitio '{nom_borrado}' eliminado.", icon="🗑️")
                    st.rerun()
                else:
                    st.session_state.lugares.insert(idx_borrar, eliminado)
                    st.error("No se pudo eliminar el sitio. Se han restaurado los datos anteriores.")

            if cerrar_ed:
                st.session_state.editando_spot_key = None
                st.rerun()

def render_formulario_agregar_lugar(key_sufijo: str = "gen"):
    """Módulo desplegable para añadir sitios desde Google Maps o a mano."""
    with st.expander("➕ Añadir", expanded=False):
        tab_gm, tab_man = st.tabs(["🌐 Google Maps", "✏️ A Mano"])
        dias_asig_opts = ["📌Guardados"] + [etiqueta_dia(d) for d in range(1, 11)]

        with tab_gm:
            st.caption("Busca un establecimiento en Google Maps o pega un enlace de un sitio o lista:")
            api_key_places = _google_maps_api_key()
            busqueda_places = st.text_input(
                "Buscar sitio en Google Maps:",
                placeholder="Empieza a escribir el nombre de un restaurante, museo...",
                key=f"buscar_places_{key_sufijo}"
            )
            if busqueda_places.strip() and len(busqueda_places.strip()) >= 3 and not _validar_url_google_maps(busqueda_places.strip()):
                if not api_key_places:
                    st.info("Configura GOOGLE_MAPS_API_KEY para activar las sugerencias de Google Maps. También puedes pegar un enlace debajo.")
                else:
                    try:
                        opciones_places = _sugerencias_google_places(busqueda_places.strip(), api_key_places)
                        if opciones_places:
                            # Las sugerencias aparecen como filas seleccionables justo debajo
                            # del campo de búsqueda; al pulsar una se añade directamente.
                            with st.container(border=True):
                                for i, opcion in enumerate(opciones_places):
                                    if st.button(
                                        f"📍  {opcion['descripcion']}",
                                        key=f"sel_places_{key_sufijo}_{i}_{hashlib.md5(opcion['id'].encode()).hexdigest()[:7]}",
                                        use_container_width=True,
                                        type="secondary"
                                    ):
                                        try:
                                            with st.spinner("Añadiendo lugar..."):
                                                nom_p, dir_p, lat_p, lon_p = _detalles_google_place(opcion["id"], api_key_places)
                                            if not nom_p:
                                                st.error("Google Maps no ha devuelto el nombre del lugar.")
                                            else:
                                                ok, msg = agregar_sitio_a_lugares(nom_p, dir_p, lat_p, lon_p)
                                                if ok:
                                                    st.toast(msg, icon="📍")
                                                    st.rerun()
                                                else:
                                                    st.error(msg)
                                        except Exception as exc:
                                            logger.warning("Error obteniendo detalles de Google Place: %s", exc)
                                            st.error("No se pudo añadir el lugar. Comprueba la configuración de Places API.")
                        else:
                            st.caption("No se han encontrado coincidencias. Prueba con otro nombre.")
                    except Exception as exc:
                        logger.warning("Error en autocompletado de Google Places: %s", exc)
                        st.warning("No se pudieron cargar las sugerencias. Comprueba la API key y que Places API (New) esté habilitada.")
            st.caption("O, si lo prefieres, pega el enlace de Google Maps de un sitio o lista:")
            with st.form(f"form_add_gm_{key_sufijo}"):
                url_input = st.text_input("Enlace de Google Maps:", placeholder="https://maps.app.goo.gl/...", key=f"inp_gm_{key_sufijo}")
                cg1, cg2 = st.columns(2)
                with cg1:
                    dia_dest_gm = selectbox_sin_teclado("Asignar a:", dias_asig_opts, key=f"sel_dia_gm_{key_sufijo}")
                with cg2:
                    hora_gm = st.text_input("Hora (opcional, HH:MM):", placeholder="11:00", key=f"hora_gm_{key_sufijo}")
                nota_gm = st.text_input("Nota manual (opcional):", placeholder="Ej: Reserva a las 20:00, probar pastrami...", key=f"nota_gm_{key_sufijo}")

                val_dia_gm = 0 if "Guardados" in dia_dest_gm else int(re.search(r"Día (\d+)", dia_dest_gm).group(1))

                if st.form_submit_button("📥 Importar", use_container_width=True):
                    if url_input:
                        h_limpia = hora_gm.strip()
                        if h_limpia and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", h_limpia):
                            st.error("Usa formato HH:MM (ej. 14:30).")
                        else:
                            if h_limpia and len(h_limpia) == 4:
                                h_limpia = "0" + h_limpia
                            with st.spinner("Importando lugar..."):
                                ok, msg = importar_sitio_desde_gmaps(url_input, val_dia_gm, h_limpia, nota_gm)
                                if ok:
                                    st.toast(msg, icon="📍")
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        st.warning("Introduce una URL de Google Maps.")

        with tab_man:
            st.caption("Escribe el nombre del lugar (las coordenadas se buscan solas):")
            with st.form(f"form_add_man_{key_sufijo}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    nom_m = st.text_input("Nombre:", placeholder="Ej: Levain Bakery, Joe's Pizza...", key=f"nom_m_{key_sufijo}")
                    dir_m = st.text_input("Dirección / Barrio:", placeholder="Ej: West Village...", key=f"dir_m_{key_sufijo}")
                with c_m2:
                    cat_m = selectbox_sin_teclado("Categoría:", ["⚡ Detección Automática"] + CATEGORIAS_CANONICAS, key=f"cat_m_{key_sufijo}")
                    tipo_m = selectbox_sin_teclado("Tipo:", ["Interior (🌧️ A cubierto)", "Exterior (☀️ Al aire libre)"], key=f"tipo_m_{key_sufijo}")

                c_m3, c_m4 = st.columns(2)
                with c_m3:
                    dia_dest_m = selectbox_sin_teclado("Asignar a:", dias_asig_opts, key=f"sel_dia_m_{key_sufijo}")
                    val_dia_m = 0 if "Guardados" in dia_dest_m else int(re.search(r"Día (\d+)", dia_dest_m).group(1))
                with c_m4:
                    hora_m = st.text_input("Hora (opcional, HH:MM):", placeholder="16:00", key=f"hora_m_{key_sufijo}")

                nota_m = st.text_input("Nota manual (opcional):", placeholder="Ej: Llevar efectivo, entrada gratuita los viernes...", key=f"nota_m_{key_sufijo}")

                coords_man_chk = st.checkbox("Introducir coordenadas manuales", key=f"chk_coords_{key_sufijo}")
                lat_man, lon_man = None, None
                if coords_man_chk:
                    c_lt, c_ln = st.columns(2)
                    with c_lt:
                        lat_man = st.number_input("Latitud:", value=40.7802, format="%.6f", key=f"lat_m_{key_sufijo}")
                    with c_ln:
                        lon_man = st.number_input("Longitud:", value=-73.9461, format="%.6f", key=f"lon_m_{key_sufijo}")

                if st.form_submit_button("💾 Guardar Lugar", use_container_width=True):
                    if nom_m:
                        h_limpia = hora_m.strip()
                        if h_limpia and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", h_limpia):
                            st.error("Usa formato HH:MM (ej. 16:00).")
                        else:
                            if h_limpia and len(h_limpia) == 4:
                                h_limpia = "0" + h_limpia
                            with st.spinner("Guardando..."):
                                t_val = "Interior" if "Interior" in tipo_m else "Exterior"
                                c_val = None if cat_m == "⚡ Detección Automática" else cat_m
                                ok, msg = agregar_sitio_a_lugares(nom_m, dir_m, lat_man, lon_man, c_val, t_val, val_dia_m, h_limpia, nota_m)
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

if "lugares" not in st.session_state:
    st.session_state.lugares = cargar_itinerario_disco()
else:
    sincronizar_lugares_desde_disco()

if "lugar_activo_id" not in st.session_state:
    st.session_state.lugar_activo_id = None

if "editando_spot_key" not in st.session_state:
    st.session_state.editando_spot_key = None


# En Streamlit Cloud el disco local no es persistente entre ciertos redeploys.
# Avisamos una sola vez por sesión si todavía no se configuró almacenamiento remoto.
if not all(_github_configuracion()[:2]) and not st.session_state.get("_aviso_persistencia_mostrado"):
    st.warning(
        "⚠️ Persistencia remota no configurada: los cambios se guardan en el disco de esta instancia, "
        "pero podrían perderse al reiniciar o desplegar la app. Configura GITHUB_TOKEN y GITHUB_REPO "
        "en Streamlit → Settings → Secrets para conservar notas, lugares y días entre despliegues."
    )
    st.session_state["_aviso_persistencia_mostrado"] = True


def _vigilar_cambios_de_otros_dispositivos():
    """Comprueba periódicamente cambios de itinerario, hotel, vuelos y listas."""
    datos_compartidos = cargar_itinerario_disco()
    cambio_lugares = _huella_datos(datos_compartidos) != _huella_datos(st.session_state.get("lugares", []))
    cambio_config = _huella_datos(cargar_config_viaje()) != _huella_datos(st.session_state.get("config_viaje", {}))

    if cambio_lugares:
        sincronizar_lugares_desde_disco()
    if cambio_config:
        sincronizar_config_desde_disco()

    if cambio_lugares or cambio_config:
        # El rerun completo actualiza mapa, contadores, itinerario, guardados y listas.
        st.rerun()


if hasattr(st, "fragment"):
    @st.fragment(run_every="60s")
    def _sincronizador_automatico_dispositivos():
        _vigilar_cambios_de_otros_dispositivos()

    _sincronizador_automatico_dispositivos()


# =============================================================================
# 8. CABECERA HERO EDITORIAL NAVIDEÑA
# =============================================================================
cfg_v = st.session_state.config_viaje
ahora_madrid = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%H:%M")
ahora_nueva_york = datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M")
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
      <div class="hero-eyebrow">✨ 26 DIC 2026 · 4 ENE 2027 ✨</div>
      <div class="hero-title">🎄Navidad en Nueva York🗽</div>
      <div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:7px; font-size:0.82rem; font-weight:700; color:#475569;">
        <span>Málaga&nbsp; · &nbsp;{ahora_madrid}</span>
        <span>NY&nbsp; · &nbsp;{ahora_nueva_york}</span>
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
# Navegación bajo demanda: solo se construye la sección elegida.
# Así evitamos renderizar el mapa y el resto de pestañas en cada cambio.
SECCIONES_PRINCIPALES = [
    "🗺️Mapa",
    "🗽Ruta",
    "📌Guardados",
    "💸Divisas",
    "✈️Info",
    "🗒️Listas",
    "☑️Checklist",
]
seccion_principal = st.radio(
    "Sección del viaje",
    SECCIONES_PRINCIPALES,
    horizontal=True,
    label_visibility="collapsed",
    key="seccion_principal_activa",
)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: MAPA GOOGLE
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗺️Mapa":
    c_m1, c_m3 = st.columns([3, 2])
    with c_m1:
        opciones_vista = [
            "🗽 Todos los Sitios",
            "✨ Todos los Días"
        ] + [etiqueta_dia(d) for d in range(1, 11)]
        sel_vista = selectbox_sin_teclado("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    # Se fija una única capa de Google Maps para evitar el desplegable de estilos.
    sel_capa = "Google Maps Callejero"
    with c_m3:
        cats_actuales = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in st.session_state.lugares))
        sel_filtro_cat = selectbox_sin_teclado("Categoría:", ["Todas"] + cats_actuales, label_visibility="collapsed")

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
    <div style="font-family: -apple-system, sans-serif; min-width: 200px; padding: 4px;">
      <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">🏨HOTEL</span>
      <div style="font-size: 14px; font-weight: 700; color: #0F172A; margin: 6px 0 2px;">{h_nom}</div>
      <div style="font-size: 12px; color: #0F172A; margin-bottom: 8px;">📍 {h_dir}</div>
      <a href="{g_hotel_url}" target="_blank" style="display:block; text-align:center; background:#1A73E8; color:white; padding:6px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Abrir Hotel en Maps →</a>
    </div>
    """
    folium.Marker(
        location=[h_lat, h_lon],
        popup=folium.Popup(pop_hotel_html, max_width=250),
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
        nota_spot = s.get("nota", "")
        nom_spot = s.get("nombre", "Lugar")

        dia_txt = etiqueta_dia(dia_spot) if dia_spot > 0 else "📌 En Guardados"
        if hora_spot:
            dia_txt += f" · 🕒 {hora_spot}"
        tipo_badge = "🌧️ Interior" if tipo_spot == "Interior" else "☀️ Exterior"

        g_search = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(nom_spot + ' New York')}"
        g_route  = f"https://www.google.com/maps/dir/?api=1&origin={h_lat},{h_lon}&destination={s['lat']},{s['lon']}"

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-width: 220px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 4px;">
            <span style="font-size: 11px; font-weight: 800; color: #2563EB;">{dia_txt}</span>
            <span style="font-size: 10px; font-weight: 700; background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 6px;">{tipo_badge}</span>
          </div>
          <div style="font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 3px;">{obtener_emoji_categoria(cat_spot)} {nom_spot}</div>
          {f'<div style="font-size: 11px; color: #0F172A; margin-bottom: 3px;">📍 {dir_spot}</div>' if dir_spot else ''}
          {f'<div style="font-size:10.5px; color:#475569; font-style:italic; line-height:1.3; margin-bottom:6px; overflow-wrap:anywhere;">📝 {linkificar_nota(nota_spot)}</div>' if nota_spot else ''}
          <div style="font-size: 11px; color: #0F172A; margin-bottom: 8px;"><b>Categoría:</b> {cat_spot}</div>
          <div style="display: flex; gap: 6px;">
            <a href="{g_search}" target="_blank" style="flex:1; text-align:center; background:#1A73E8; color:white; padding:6px 4px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Maps →</a>
            <a href="{g_route}" target="_blank" style="text-align:center; background:#F8FAFC; border:1px solid #CBD5E1; color:#0F172A; padding:6px 8px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">🧭 Ruta</a>
          </div>
        </div>
        """

        folium.Marker(
            location=pt,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{obtener_emoji_categoria(cat_spot)} {nom_spot}" + (f" ({hora_spot})" if hora_spot else ""),
            icon=crear_pin_google_maps(cat_spot, nom_spot)
        ).add_to(mapa)

    if len(coords_ruta) > 1 and "Día " in sel_vista:
        folium.PolyLine(coords_ruta, color="#1A73E8", weight=3.5, opacity=0.8, dash_array="6, 8").add_to(mapa)

    resultado_mapa = st_folium(
        mapa,
        use_container_width=True,
        height=920,
        returned_objects=[]
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗽Ruta":
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

    opciones_filtro_it = ["✨ Todos los Días"] + [etiqueta_dia(d) for d in range(1, 11)]
    filtro_it_sel = selectbox_sin_teclado(
        "Ver itinerario:",
        opciones_filtro_it,
        key="filtro_itinerario_dia",
        label_visibility="collapsed"
    )

    if "Todos los Días" in filtro_it_sel:
        # El desplegable es el único selector de día; se eliminan los botones rápidos.
        dias_a_mostrar = list(range(1, 11))
    else:
        m_d_it = re.search(r"Día (\d+):", filtro_it_sel)
        dias_a_mostrar = [int(m_d_it.group(1))] if m_d_it else [1]

    for d in dias_a_mostrar:
        paradas_dia = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == d])
        visitados_dia = [l for l in paradas_dia if l.get("visitado", False)]

        st.markdown(f'<div id="dia-{d}"></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #E5E7EB; border-left:1.5px solid #E5E7EB; border-radius:13px; padding:8px 12px; margin-top:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <div style="font-weight:900; font-size:1.23rem; color:#0F172A;">
            {etiqueta_dia(d)}
          </div>
          <div style="font-weight:800; font-size:0.78rem; color:#0F172A; background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:20px; padding:2px 9px;">
            {len(visitados_dia)}/{len(paradas_dia)} ✔
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not paradas_dia:
            st.markdown("""
            <div style="background:#FFFFFF; border:1.5px dashed #94A3B8; border-radius:11px; padding:10px 12px; color:#0F172A; font-size:0.84rem; font-weight:600; margin-bottom:10px;">
              ❄️ Sin lugares asignados para este día. Asígnalos desde <b>📍 Guardados</b>.
            </div>
            """, unsafe_allow_html=True)
        else:
            for seq_idx, item in enumerate(paradas_dia, 1):
                idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == item["id"]), None)
                is_visited = item.get("visitado", False)
                cat_i = normalizar_categoria(item.get("categoria", "📍 Otros"))
                emoji_i = obtener_emoji_categoria(cat_i)
                dir_i = item.get("direccion", "")
                nota_i = item.get("nota", "")
                hora_i = item.get("hora", "")
                maps_q = urllib.parse.quote(f"{item['nombre']}, New York")
                gmaps_url = f"https://www.google.com/maps/search/?api=1&query={maps_q}"

                # Fila de Ruta: hora | nombre | editar | mapa | visitado.
                with st.container(key=f"it-heading-row-{item['id']}"):
                    # Streamlit crea cinco columnas; la distribución se controla
                    # mediante la cuadrícula CSS de esta fila.
                    c_hr_head, c_info, c_edit_head, c_map_head, c_chk = st.columns(
                        [0.8, 6.0, 0.55, 0.55, 0.55],
                        gap=None,
                        vertical_alignment="center"
                    )

                    with c_hr_head:
                        st.text_input(
                            "Hora",
                            value=hora_i,
                            placeholder="HH:MM",
                            key=f"hora_it_{d}_{item['id']}",
                            on_change=actualizar_hora_itinerario,
                            args=(d, item["id"]),
                            label_visibility="collapsed"
                        )

                    with c_info:
                        txt_c = "#334155" if is_visited else "#0F172A"
                        strike = "text-decoration: line-through; opacity: 0.78;" if is_visited else ""
                        dir_html = f'<div class="place-list-address">📍 {html.escape(str(dir_i))}</div>' if dir_i else ''
                        nota_html = bloque_nota_html(nota_i)
                        st.markdown(
                            f'<div style="{strike}; min-width:0; width:100%; overflow-wrap:anywhere;">'
                            f'<div class="place-list-title" style="color:{txt_c};">{emoji_i} {item["nombre"]}</div>'
                            f'{dir_html}{nota_html}</div>',
                            unsafe_allow_html=True
                        )

                    with c_edit_head:
                        with st.container(key=f"it-edit-button-wrap-{item['id']}"):
                            if st.button(" ", key=f"btn_ed_it_{d}_{item['id']}", help="Editar sitio"):
                                ek = f"it_{d}_{item['id']}"
                                st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                                st.rerun()

                    with c_map_head:
                        with st.container(key=f"it-map-button-wrap-{item['id']}"):
                            st.link_button(" ", gmaps_url, help="Abrir en Google Maps")

                    with c_chk:
                        with st.container(key=f"it-visit-checkbox-wrap-{item['id']}"):
                            chk_val = st.checkbox("", value=is_visited, key=f"chk_it_{d}_{item['id']}")
                        if chk_val != is_visited and idx_real is not None:
                            anterior_visitado = st.session_state.lugares[idx_real].get("visitado", False)
                            st.session_state.lugares[idx_real]["visitado"] = chk_val
                            if guardar_itinerario_disco(st.session_state.lugares):
                                st.rerun()
                            else:
                                st.session_state.lugares[idx_real]["visitado"] = anterior_visitado
                                st.error("No se pudo guardar el estado de visita.")
                if idx_real is not None:
                    render_editor_sitio_panel(item, idx_real, f"it_{d}")

                st.markdown('<div style="height:1px; background:#CBD5E1; margin:6px 0;"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "📌Guardados":
    render_formulario_agregar_lugar("guardados")
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    pulsado_sync = False
    with st.container(key="guardados-header-row"):
        col_gh1, col_gh2 = st.columns([3.4, 1.2], vertical_alignment="center")
        with col_gh1:
            st.markdown('<div class="ny-card-header" style="margin-bottom:0;">Lugares Guardados</div>', unsafe_allow_html=True)
        with col_gh2:
            with st.container(key="btn_sync_guardados_wrap"):
                if st.button("🔄 Sincronizar", key="btn_sync_guardados_mini", help="Sincronizar listas de Google Maps"):
                    pulsado_sync = True

    if pulsado_sync:
        ejecutar_sincronizacion_listas_gmaps()

    if "_msg_sync_guardados" in st.session_state:
        tipo_msg, txt_msg = st.session_state.pop("_msg_sync_guardados")
        if tipo_msg == "success":
            st.success(txt_msg)
        elif tipo_msg == "error":
            st.error(txt_msg)
        else:
            st.info(txt_msg)
    if "_errores_sync_guardados" in st.session_state:
        for err_s in st.session_state.pop("_errores_sync_guardados"):
            st.warning(err_s)

    ver_todos_edicion = st.checkbox("Mostrar también los lugares ya asignados", value=False, key="chk_ver_todos_guardados")

    if ver_todos_edicion:
        pool_guardados = list(st.session_state.lugares)
    else:
        pool_guardados = [l for l in st.session_state.lugares if l.get("dia", 0) == 0]

    cats_en_pool = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in pool_guardados))

    col_flt1, col_flt2 = st.columns(2)
    with col_flt1:
        flt_cat_g = selectbox_sin_teclado("Categoría:", ["Todas"] + cats_en_pool, key="flt_pool_cat")
    with col_flt2:
        busq_g = st.text_input("Buscar:", placeholder="Nombre del sitio...", key="busq_pool_nom")

    nuevos_ids_set = set(st.session_state.get("nuevos_lugares_ids", []))
    nuevos_orden = {nid: idx for idx, nid in enumerate(st.session_state.get("nuevos_lugares_ids", []))}

    visibles_pool = [
        l for l in pool_guardados
        if (flt_cat_g == "Todas" or normalizar_categoria(l.get("categoria", "")) == flt_cat_g)
        and (not busq_g.strip() or busq_g.strip().lower() in str(l.get("nombre", "")).lower())
    ]
    visibles_pool.sort(key=lambda l: int(l.get("id", 0)), reverse=True)

    st.caption(f"Mostrando **{len(visibles_pool)}** sitios")

    for p_spot in visibles_pool:
        idx_sp_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == p_spot["id"]), None)
        cat_p = normalizar_categoria(p_spot.get("categoria", "📍 Otros"))
        dir_p = p_spot.get("direccion", "")
        nota_p = p_spot.get("nota", "")
        dia_p = p_spot.get("dia", 0)
        hora_p = p_spot.get("hora", "")

        nota_p_html = bloque_nota_html(nota_p)
        dir_p_html = f'<div class="place-list-address">📍 {html.escape(str(dir_p))}</div>' if dir_p else ''
        tipo_p_html = '<span class="badge-indoor">🌧️ Interior</span>' if p_spot.get("tipo") == "Interior" else '<span class="badge-outdoor">☀️ Exterior</span>'

        # Toda la información se presenta antes de los controles.
        with st.container(key=f"saved-heading-row-{p_spot['id']}"):
            c_saved_info, c_saved_edit, c_saved_map = st.columns([8.8, 0.6, 0.6], gap=None)
            with c_saved_info:
                st.markdown(f"""
                <div style="width:100%; min-width:0; overflow-wrap:anywhere;">
                  <div class="place-list-title">{obtener_emoji_categoria(cat_p)} {html.escape(str(p_spot.get('nombre', '')))}</div>
                  <div style="margin-top:4px; display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="badge-cat">{cat_p}</span>{tipo_p_html}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with c_saved_edit:
                with st.container(key=f"saved-edit-button-wrap-{p_spot['id']}"):
                    if st.button(" ", key=f"btn_ed_pool_{p_spot['id']}", help="Editar sitio"):
                        ek = f"pool_{p_spot['id']}"
                        st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                        st.rerun()
            with c_saved_map:
                g_url_sp = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p_spot['nombre'] + ' New York')}"
                with st.container(key=f"saved-map-button-wrap-{p_spot['id']}"):
                    st.link_button(" ", g_url_sp, help="Abrir en Google Maps")
            # Dirección y nota en una fila independiente de ancho completo.
            if dir_p_html or nota_p_html:
                st.markdown(f'<div class="place-full-width-info">{dir_p_html}{nota_p_html}</div>', unsafe_allow_html=True)

        # Cuatro controles uniformes debajo del nombre y de toda su subinformación.
        with st.container(key=f"saved-controls-row-{p_spot['id']}"):
            c_hr, c_day = st.columns([1, 1], gap="small")
            with c_hr:
                nueva_h_pool = st.text_input(
                    "Hora",
                    value=hora_p,
                    placeholder="HH:MM",
                    key=f"hora_pool_{p_spot['id']}",
                    label_visibility="collapsed"
                )
                if nueva_h_pool.strip() != hora_p and idx_sp_real is not None:
                    hl = nueva_h_pool.strip()
                    if not hl or re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hl):
                        if hl and len(hl) == 4:
                            hl = "0" + hl
                        hora_anterior_pool = st.session_state.lugares[idx_sp_real].get("hora", "")
                        st.session_state.lugares[idx_sp_real]["hora"] = hl
                        if guardar_itinerario_disco(st.session_state.lugares):
                            st.rerun()
                        else:
                            st.session_state.lugares[idx_sp_real]["hora"] = hora_anterior_pool
                            st.error("No se pudo guardar la hora.")
            with c_day:
                opts_dia_pool = ["- Día -"] + [etiqueta_dia_guardados(d) for d in range(1, 11)]
                idx_sel_pool = dia_p if 1 <= dia_p <= 10 else 0
                asig_dia = selectbox_sin_teclado(
                    "Día",
                    opts_dia_pool,
                    index=idx_sel_pool,
                    key=f"asig_dia_pool_{p_spot['id']}",
                    label_visibility="collapsed"
                )
                if asig_dia != "- Día -" and idx_sp_real is not None:
                    d_num = int(re.search(r"Día (\d+)", asig_dia).group(1))
                    if d_num != dia_p:
                        dia_anterior_pool = st.session_state.lugares[idx_sp_real].get("dia", 0)
                        st.session_state.lugares[idx_sp_real]["dia"] = d_num
                        if guardar_itinerario_disco(st.session_state.lugares):
                            st.rerun()
                        else:
                            st.session_state.lugares[idx_sp_real]["dia"] = dia_anterior_pool
                            st.error("No se pudo guardar la asignación del día.")

        if idx_sp_real is not None:
            render_editor_sitio_panel(p_spot, idx_sp_real, "pool")

        st.markdown('<hr style="margin:6px 0; border-color:#E2E8F0;">', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: MODO LLUVIA & CLIMA EN TIEMPO REAL
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🌧️ Clima":
    st.markdown('<div class="ny-card-header">🌧️ Clima en Tiempo Real & Plan B a Cubierto</div>', unsafe_allow_html=True)

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
              <div style="font-size:1.7rem; font-weight:800; color:#0F172A;">{temp_c:.1f} °C</div>
              <div style="font-size:0.9rem; font-weight:600; color:#0F172A;">{desc_clima}</div>
              <div style="font-size:0.8rem; color:#0F172A; margin-top:6px;">
                Sensación térmica: <b>{sens_c:.1f} °C</b> · Humedad: <b>{cur.get('relative_humidity_2m', 60)}%</b><br>
                Precipitación en vivo: <b>{precip:.1f} mm</b>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Conectando con la estación meteorológica de Nueva York...")

    with col_w_day:
        st.markdown("#### 🗓️ Pronóstico por Día")
        dia_sel_clima = selectbox_sin_teclado(
            "Selecciona el día:",
            [etiqueta_dia(d) for d in range(1, 11)],
            key="sel_dia_clima"
        )
        num_dia_c = int(re.search(r"Día (\d+):", dia_sel_clima).group(1))

        prob_lluvia = precip_mm = temp_max_est = temp_min_est = None
        desc_dia = "Pronóstico no disponible"
        alerta_lluvia = False
        pronostico_disponible = False

        if clima_data and "daily" in clima_data:
            d_time = clima_data["daily"].get("time", [])
            # No asociar Día N al índice N-1: la API entrega fechas de calendario.
            # Si la fecha real del viaje no está disponible, no mostrar un pronóstico falso.
            fecha_viaje = None
            cfg_clima = st.session_state.get("config_viaje", {})
            fecha_base = _fecha_inicio_viaje(cfg_clima)
            if fecha_base:
                from datetime import timedelta
                fecha_viaje = (fecha_base + timedelta(days=num_dia_c - 1)).isoformat()
            if fecha_viaje and fecha_viaje in d_time:
                idx_pronostico = d_time.index(fecha_viaje)
                daily = clima_data["daily"]
                campos = ("weather_code", "precipitation_probability_max", "precipitation_sum", "temperature_2m_max", "temperature_2m_min")
                if all(idx_pronostico < len(daily.get(campo, [])) for campo in campos):
                    p_code = daily["weather_code"][idx_pronostico]
                    desc_dia, _ = traducir_codigo_clima(p_code)
                    prob_lluvia = daily["precipitation_probability_max"][idx_pronostico] or 0
                    precip_mm = daily["precipitation_sum"][idx_pronostico] or 0.0
                    temp_max_est = daily["temperature_2m_max"][idx_pronostico] if daily["temperature_2m_max"][idx_pronostico] is not None else 5.0
                    temp_min_est = daily["temperature_2m_min"][idx_pronostico] if daily["temperature_2m_min"][idx_pronostico] is not None else -1.0
                    alerta_lluvia = (prob_lluvia >= 40) or (precip_mm > 1.0) or ("Lluvia" in desc_dia) or ("Nieve" in desc_dia)
                    pronostico_disponible = True
                else:
                    desc_dia = "Pronóstico no disponible"
            else:
                desc_dia = "Pronóstico no disponible"

        color_card = "#FEF2F2" if alerta_lluvia else "#F0FDF4"
        border_card = "#EF4444" if alerta_lluvia else "#10B981"
        st.markdown(f"""
        <div style="background:{color_card}; border: 1.5px solid {border_card}; border-radius:14px; padding:14px 16px;">
          <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">{etiqueta_dia(num_dia_c)} · {desc_dia}</div>
          <div style="font-size:0.84rem; color:#0F172A; margin-top:4px;">
            🌡️ Temperaturas: <b>{f'{temp_min_est:.0f} °C a {temp_max_est:.0f} °C' if pronostico_disponible else 'No disponible'}</b><br>
            🌧️ Probabilidad de Precipitación: <b>{f'{prob_lluvia}%' if pronostico_disponible else 'No disponible'}</b> ({f'{precip_mm:.1f} mm' if pronostico_disponible else '—'})
          </div>
          <div style="font-size:0.8rem; font-weight:700; color:{'#B91C1C' if alerta_lluvia else '#047857'}; margin-top:6px;">
            {'⚠️ ALERTA DE LLUVIA / NIEVE: Recomendable activar sustituciones a cubierto' if alerta_lluvia else ('✓ Tiempo favorable para paseos al aire libre' if pronostico_disponible else 'Pronóstico aún no disponible para esta fecha')}
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔄 Sustituciones Inteligentes por Cercanía")
    st.caption("Intercambia cualquier plan al aire libre por los sitios a cubierto más cercanos:")

    planes_ext_dia = [l for l in st.session_state.lugares if l.get("dia", 0) == num_dia_c and l.get("tipo") == "Exterior"]
    lugares_indoor = [l for l in st.session_state.lugares if l.get("tipo") == "Interior"]

    if not planes_ext_dia:
        st.success(f"🎉 No hay paradas al aire libre programadas en el Día {num_dia_c}.")
    else:
        for spot_ext in planes_ext_dia:
            distancias = []
            for ind in lugares_indoor:
                if ind["id"] != spot_ext["id"]:
                    km = math.hypot(ind["lat"] - spot_ext["lat"], ind["lon"] - spot_ext["lon"]) * 111.0
                    distancias.append((km, ind))
            distancias.sort(key=lambda x: x[0])
            top_cercanos = distancias[:5]

            dir_ext_txt = f" · 📍 {html.escape(str(spot_ext.get('direccion', '')))}" if spot_ext.get("direccion") else ""
            nota_ext_html = bloque_nota_html(spot_ext.get("nota", ""))
            st.markdown(f"""
            <div style="background:#FFF5F5; border-left:4px solid #EF4444; border-radius:12px; padding:10px 14px; margin: 8px 0;">
              <div style="font-weight:700; color:#991B1B;">{obtener_emoji_categoria(normalizar_categoria(spot_ext.get('categoria','')))} {html.escape(str(spot_ext.get('nombre', '')))}</div>
              <div style="font-size:0.8rem; color:#7F1D1D;">Plan exterior · Día {num_dia_c}{dir_ext_txt}</div>
              {nota_ext_html}
            </div>
            """, unsafe_allow_html=True)

            c_sust1, c_sust2 = st.columns([3.5, 1.5])
            with c_sust1:
                opciones_cercanas = [f"{x['nombre']} (a {d:.1f} km) - {normalizar_categoria(x.get('categoria',''))}" for d, x in top_cercanos]
                if opciones_cercanas:
                    ids_opciones = [str(x.get("id")) for _, x in top_cercanos]
                    sel_sust_id = st.selectbox("Sustituto a cubierto:", ids_opciones, format_func=lambda ident: next((f"{x['nombre']} (a {d:.1f} km) - {normalizar_categoria(x.get('categoria',''))}" for d, x in top_cercanos if str(x.get("id")) == ident), ident), key=f"sel_sust_{spot_ext['id']}", label_visibility="collapsed")
                else:
                    sel_sust_id = None
                    st.info("No hay alternativas a cubierto disponibles.")
            with c_sust2:
                if st.button("🔄 Cambiar", key=f"btn_swap_{spot_ext['id']}", use_container_width=True, disabled=not bool(top_cercanos)):
                    elegido = next((x for _, x in top_cercanos if str(x.get("id")) == str(sel_sust_id)), None)
                    idx_ext = next((i for i, x in enumerate(st.session_state.lugares) if str(x.get("id")) == str(spot_ext["id"])), None)
                    idx_ind = next((i for i, x in enumerate(st.session_state.lugares) if elegido and str(x.get("id")) == str(elegido["id"])), None)
                    if elegido is None or idx_ext is None or idx_ind is None:
                        st.error("No se pudo localizar una de las paradas. Actualiza la página.")
                    else:
                        anterior_ext = dict(st.session_state.lugares[idx_ext])
                        anterior_ind = dict(st.session_state.lugares[idx_ind])
                        hora_heredada = st.session_state.lugares[idx_ext].get("hora", "")
                        st.session_state.lugares[idx_ext]["dia"] = 0
                        st.session_state.lugares[idx_ind]["dia"] = num_dia_c
                        if hora_heredada and not st.session_state.lugares[idx_ind].get("hora"):
                            st.session_state.lugares[idx_ind]["hora"] = hora_heredada
                        if guardar_itinerario_disco(st.session_state.lugares):
                            st.toast(f"¡'{elegido['nombre']}' ahora está en el Día {num_dia_c}!", icon="✨")
                            st.rerun()
                        else:
                            st.session_state.lugares[idx_ext] = anterior_ext
                            st.session_state.lugares[idx_ind] = anterior_ind
                            st.error("No se pudo guardar el cambio. Se han restaurado los datos anteriores.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: DIVISAS EN TIEMPO REAL & CALCULADORA TAX Y PROPINAS NY
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "💸Divisas":
    st.markdown('<div class="ny-card-header">💵 Calculadora</div>', unsafe_allow_html=True)

    tasa_eur, fecha_tasa = obtener_tasa_usd_eur()

    col_fx, col_tax = st.columns([2.5, 3])

    with col_fx:
        st.markdown("#### 💱 Conversor de Divisas")
        st.markdown(f"""
        <div style="background:#F1F5F9; border-radius:12px; padding:10px 14px; margin-bottom:12px; font-size:0.84rem; color:#0F172A;">
          Tasa actual: <b>1 USD = {tasa_eur:.4f} EUR</b><br>
          <span style="font-size:0.74rem; color:#334155;">Actualizado: {fecha_tasa}</span>
        </div>
        """, unsafe_allow_html=True)

        modo_fx = st.radio("Convertir:", ["USD a EUR ($ ➔ €)", "EUR a USD (€ ➔ $)"], horizontal=True)
        if "USD a EUR" in modo_fx:
            val_usd = st.number_input("Cantidad en Dólares ($):", min_value=0.0, value=50.0, step=5.0)
            res_eur = val_usd * tasa_eur
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:14px; padding:14px; text-align:center; margin-top:8px;">
              <div style="font-size:0.84rem; color:#0F172A;">Equivalente en Euros:</div>
              <div style="font-size:1.85rem; font-weight:800; color:#0F172A;">{res_eur:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            val_eur = st.number_input("Cantidad en Euros (€):", min_value=0.0, value=50.0, step=5.0)
            res_usd = val_eur / tasa_eur if tasa_eur > 0 else 0
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:14px; padding:14px; text-align:center; margin-top:8px;">
              <div style="font-size:0.84rem; color:#0F172A;">Equivalente en Dólares:</div>
              <div style="font-size:1.85rem; font-weight:800; color:#0F172A;">${res_usd:.2f} USD</div>
            </div>
            """, unsafe_allow_html=True)

    with col_tax:
        st.markdown("#### 🧾 Calculadora de Cuenta, Tax & Tips")

        subtotal_bill = st.number_input("Subtotal de la cuenta ($ USD):", min_value=0.0, value=65.0, step=5.0)
        aplicar_tax = st.toggle(
            "Aplicar NYC Tax (8,875%)",
            value=True,
            key="calc_aplicar_tax",
            help="Desactívalo para calcular la cuenta sin impuesto."
        )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            pct_propina = st.number_input(
                "Porcentaje de Propina (%):",
                min_value=0.0,
                max_value=100.0,
                value=18.0,
                step=1.0,
                format="%.1f"
            )
        with col_t2:
            base_calc = st.radio("Calcular propina sobre:", ["Subtotal sin tax", "Total con tax"])

        tax_rate = 0.08875 if aplicar_tax else 0.0
        tax_total = subtotal_bill * tax_rate
        base_tip = subtotal_bill if "Subtotal" in base_calc else (subtotal_bill + tax_total)
        tip_total = base_tip * (pct_propina / 100.0)
        gran_total = subtotal_bill + tax_total + tip_total
        gran_total_eur = gran_total * tasa_eur

        st.markdown(f"""
        <div class="ny-card" style="margin-top:10px; border: 1.5px solid #E2E8F0;">
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.88rem;">
            <span style="color:#0F172A;">Subtotal carta:</span>
            <b>${subtotal_bill:.2f}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.88rem;">
            <span style="color:#0F172A;">NYC Tax ({'8.875%' if aplicar_tax else 'Desactivado'}):</span>
            <b>{f'${tax_total:.2f}' if aplicar_tax else 'Sin tax ($0.00)'}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.88rem;">
            <span style="color:#0F172A;">Propina ({pct_propina:.1f}%):</span>
            <b>${tip_total:.2f}</b>
          </div>
          <div style="border-top:1.5px solid #E2E8F0; padding-top:10px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.05rem; font-weight:800; color:#0F172A;">Total a Pagar:</span>
            <div style="text-align:right;">
              <span style="font-size:1.35rem; font-weight:800; color:#0F172A;">${gran_total:.2f} USD</span><br>
              <span style="font-size:0.84rem; color:#0F172A;">≈ {gran_total_eur:.2f} €</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        num_personas = 3
        st.markdown("**Dividir entre 3 personas**")
        per_p_usd = gran_total / num_personas
        per_p_eur = gran_total_eur / num_personas
        st.info(f"👉 **Por persona (3 personas):** **${per_p_usd:.2f} USD** (~ {per_p_eur:.2f} €)")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: VUELOS, HOTEL & LISTAS
# ─────────────────────────────────────────────────────────────────────────────
def extraer_codigos_vuelo(texto_vuelo: str) -> list:
    return re.findall(r"\b([A-Z]{2}\d{2,4})\b", (texto_vuelo or "").upper())

if seccion_principal == "✈️Info":
    c_vl1, c_vl2 = st.columns(2)

    with c_vl1:
        st.markdown('<div class="ny-card-header">✈️ Vuelos & Estado en Tiempo Real</div>', unsafe_allow_html=True)

        cods_ida = extraer_codigos_vuelo(v_ida.get("vuelo", ""))
        cods_vta = extraer_codigos_vuelo(v_vta.get("vuelo", ""))

        st.caption("Consulta los detalles de cada vuelo en FlightAware o Flightradar24.")

        if cods_ida:
            st.markdown(f"**🛫 Ida ({v_ida.get('fecha', '26 Dic')} · {v_ida.get('hora', '15:30')}):**")
            for idx_c, cod in enumerate(cods_ida):
                fa_url = f"https://es.flightaware.com/live/flight/{cod}"
                fr_url = f"https://www.flightradar24.com/data/flights/{cod.lower()}"
                with st.container(key=f"flight-links-ida-{idx_c}-{cod.lower()}"):
                    st.markdown(f"<div style='font-weight:800; font-size:0.84rem; margin:4px 0;'>✈️ {html.escape(cod)}</div>", unsafe_allow_html=True)
                    fa_col, fr_col = st.columns(2, gap="small")
                    with fa_col:
                        st.link_button("FlightAware ↗", fa_url, use_container_width=True)
                    with fr_col:
                        st.link_button("Flightradar24 ↗", fr_url, use_container_width=True)

        if cods_vta:
            st.markdown(f"**🛬 Regreso ({v_vta.get('fecha', '4 Ene')} · {v_vta.get('hora', '20:45')}):**")
            for idx_c, cod in enumerate(cods_vta):
                fa_url = f"https://es.flightaware.com/live/flight/{cod}"
                fr_url = f"https://www.flightradar24.com/data/flights/{cod.lower()}"
                with st.container(key=f"flight-links-regreso-{idx_c}-{cod.lower()}"):
                    st.markdown(f"<div style='font-weight:800; font-size:0.84rem; margin:4px 0;'>✈️ {html.escape(cod)}</div>", unsafe_allow_html=True)
                    fa_col, fr_col = st.columns(2, gap="small")
                    with fa_col:
                        st.link_button("FlightAware ↗", fa_url, use_container_width=True)
                    with fr_col:
                        st.link_button("Flightradar24 ↗", fr_url, use_container_width=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.expander("✏️ Editar datos de vuelos", expanded=False):
            with st.form("form_editar_vuelos"):
                ida_v = st.text_input("Vuelo Ida (ej. Aer Lingus · EI583, EI107):", value=v_ida.get("vuelo", "Aer Lingus · EI583, EI107"))
                ida_f = st.text_input("Fecha Ida:", value=v_ida.get("fecha", "26 Dic"))
                ida_h = st.text_input("Hora Ida:", value=v_ida.get("hora", "15:30"))
                ida_a = st.text_input("Aeropuerto:", value=v_ida.get("aeropuerto", "JFK / Nueva York"))
                st.markdown("---")
                vta_v = st.text_input("Vuelo Regreso (ej. Aer Lingus · EI104, EI582):", value=v_vta.get("vuelo", "Aer Lingus · EI104, EI582"))
                vta_f = st.text_input("Fecha Regreso:", value=v_vta.get("fecha", "4 Ene"))
                vta_h = st.text_input("Hora Regreso:", value=v_vta.get("hora", "20:45"))
                vta_a = st.text_input("Aeropuerto Regreso:", value=v_vta.get("aeropuerto", "JFK / Nueva York"))
                if st.form_submit_button("💾 Guardar Vuelos"):
                    config_anterior = copy.deepcopy(st.session_state.config_viaje)
                    st.session_state.config_viaje["vuelo_ida"] = {"vuelo": ida_v, "fecha": ida_f, "hora": ida_h, "aeropuerto": ida_a}
                    st.session_state.config_viaje["vuelo_vuelta"] = {"vuelo": vta_v, "fecha": vta_f, "hora": vta_h, "aeropuerto": vta_a}
                    if guardar_config_viaje(st.session_state.config_viaje):
                        st.toast("Datos de vuelos actualizados.", icon="✈️")
                        st.rerun()
                    else:
                        st.session_state.config_viaje = config_anterior
                        st.error("No se pudieron guardar los vuelos. Se han restaurado los datos anteriores.")

    with c_vl2:
        st.markdown('<div class="ny-card-header">🏨 Hotel</div>', unsafe_allow_html=True)

        hotel_nom_act = hotel.get("nombre", "Courtyard by Marriott New York Manhattan Upper East Side")
        hotel_dir_act = hotel.get("direccion", "410 E 92nd St, New York, NY 10128")
        hotel_lat_act = hotel.get("lat", 40.780242)
        hotel_lon_act = hotel.get("lon", -73.946123)

        gmaps_hotel_search = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hotel_nom_act + ' ' + hotel_dir_act)}"
        gmaps_hotel_dir = f"https://www.google.com/maps/dir/?api=1&destination={hotel_lat_act},{hotel_lon_act}"

        st.markdown(f"""
        <div class="ny-card" style="border-left: 5px solid #15803D; margin-bottom:10px;">
          <div style="font-weight:900; font-size:1.05rem; color:#0F172A; margin-bottom:4px;">🏨 {html.escape(str(hotel_nom_act))}</div>
          <div style="font-size:0.88rem; color:#0F172A; margin-bottom:4px;">📍 {html.escape(str(hotel_dir_act))}</div>
          <div style="font-size:0.78rem; color:#334155;">Coordenadas: {hotel_lat_act:.6f}, {hotel_lon_act:.6f}</div>
        </div>
        """, unsafe_allow_html=True)

        ch_btn1, ch_btn2 = st.columns(2)
        with ch_btn1:
            st.link_button("🗺️ Ver en Maps", gmaps_hotel_search, use_container_width=True)
        with ch_btn2:
            st.link_button("🧭 Cómo llegar", gmaps_hotel_dir, use_container_width=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.expander("✏️ Editar datos del hotel", expanded=False):
            with st.form("form_editar_hotel"):
                h_n = st.text_input("Nombre Hotel:", value=hotel_nom_act)
                h_d = st.text_input("Dirección:", value=hotel_dir_act)
                h_lt = st.number_input("Latitud:", value=float(hotel_lat_act), format="%.6f")
                h_ln = st.number_input("Longitud:", value=float(hotel_lon_act), format="%.6f")
                if st.form_submit_button("💾 Guardar Hotel"):
                    if not (-90 <= float(h_lt) <= 90 and -180 <= float(h_ln) <= 180):
                        st.error("Las coordenadas del hotel no son válidas.")
                    else:
                        config_anterior = copy.deepcopy(st.session_state.config_viaje)
                        st.session_state.config_viaje["hotel"] = {"nombre": h_n.strip(), "direccion": h_d.strip(), "lat": h_lt, "lon": h_ln}
                        if guardar_config_viaje(st.session_state.config_viaje):
                            st.toast("Hotel base actualizado.", icon="🏨")
                            st.rerun()
                        else:
                            st.session_state.config_viaje = config_anterior
                            st.error("No se pudo guardar el hotel. Se han restaurado los datos anteriores.")


# ─────────────────────────────────────────────────────────────────────────────
# NUEVA PESTAÑA: LISTAS DE GOOGLE MAPS
# Se conserva íntegro el código de gestión y sincronización existente.
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗒️Listas":
    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    st.caption("Se puede cambiar el nombre o la URL de cualquier lista, después pulsar sincronizar para importar los lugares nuevos.")

    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")
    else:
        if st.button("🔄 Sincronizar todas las listas", key="btn_sync_all_gmaps", use_container_width=True, type="primary"):
            ejecutar_sincronizacion_listas_gmaps()

    for idx_lst, lst_data in enumerate(listas_config):
        nombre_lista = str(lst_data.get("nombre", f"Lista {idx_lst + 1}"))
        url_lista = str(lst_data.get("url", ""))
        sufijo_edicion = hashlib.sha1(f"{nombre_lista}\0{url_lista}".encode("utf-8")).hexdigest()[:10]
        key_ed_nombre = f"gmaps_edit_nombre_{idx_lst}_{sufijo_edicion}"
        key_ed_url = f"gmaps_edit_url_{idx_lst}_{sufijo_edicion}"

        with st.container(key=f"saved-heading-row-list-{idx_lst}"):
            col_nombre, col_edit = st.columns([9.45, 0.55], gap="small", vertical_alignment="center")
            with col_nombre:
                st.markdown(
                    f"<div style='font-weight:800; color:#0F172A; overflow-wrap:anywhere;'>{idx_lst + 1}. {html.escape(nombre_lista)}</div>"
                    f"<div class='gmaps-list-url' style='font-size:0.76rem; color:#475569; margin-top:2px; margin-bottom:6px;'>{html.escape(url_lista)}</div>",
                    unsafe_allow_html=True
                )
            with col_edit:
                with st.container(key=f"saved-edit-button-wrap-list-{idx_lst}"):
                    if st.button(" ", key=f"btn_ed_pool_list_{idx_lst}", help="Editar lista"):
                        actual = st.session_state.get("lista_gmaps_editando")
                        st.session_state.lista_gmaps_editando = None if actual == idx_lst else idx_lst
                        for clave in (key_ed_nombre, key_ed_url):
                            st.session_state.pop(clave, None)
                        st.rerun()

        if st.session_state.get("lista_gmaps_editando") == idx_lst:
            st.markdown(f"**Editar lista: {html.escape(nombre_lista)}**")
            with st.form(f"form_editar_lista_gmaps_{idx_lst}"):
                nuevo_nombre_lista = st.text_input("Nombre de la lista:", value=nombre_lista, key=key_ed_nombre)
                nueva_url_lista = st.text_input("URL compartida de Google Maps:", value=url_lista,
                    placeholder="https://maps.app.goo.gl/...", key=key_ed_url)
                guardar_lista = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
                cancelar_lista = st.form_submit_button("Cancelar", use_container_width=True)
                if guardar_lista:
                    nombre_limpio = nuevo_nombre_lista.strip()
                    url_limpia = nueva_url_lista.strip()
                    partes_url = urllib.parse.urlparse(url_limpia)
                    if not nombre_limpio:
                        st.error("El nombre de la lista no puede estar vacío.")
                    elif not _validar_url_google_maps(url_limpia):
                        st.error("Introduce un enlace válido de un dominio oficial de Google Maps.")
                    else:
                        listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                        if idx_lst < len(listas_actualizadas):
                            listas_actualizadas[idx_lst] = {"nombre": nombre_limpio, "url": url_limpia}
                            st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                            if guardar_config_viaje(st.session_state.config_viaje):
                                st.session_state.lista_gmaps_editando = None
                                st.toast("Lista de Google Maps actualizada.", icon="✅")
                                st.rerun()
                elif cancelar_lista:
                    st.session_state.lista_gmaps_editando = None
                    st.rerun()

    with st.expander("➕ Añadir nueva lista de Google Maps"):
        with st.form("form_nueva_lista_gmaps"):
            n_nombre_l = st.text_input("Nombre de la lista (ej: Rooftops & Bares):")
            n_url_l = st.text_input("URL compartida de Google Maps (maps.app.goo.gl/...):")
            if st.form_submit_button("Añadir Lista"):
                url_nueva = (n_url_l or "").strip()
                partes_url = urllib.parse.urlparse(url_nueva)
                if not n_nombre_l.strip():
                    st.error("Introduce un nombre para la lista.")
                elif not _validar_url_google_maps(url_nueva):
                    st.error("Introduce un enlace válido de un dominio oficial de Google Maps.")
                else:
                    listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                    listas_actualizadas.append({"nombre": n_nombre_l.strip(), "url": url_nueva})
                    st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                    if guardar_config_viaje(st.session_state.config_viaje):
                        st.success("Lista guardada.")
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB EXTRA: CHECKLIST GENERAL DE PENDIENTES
# Los elementos se guardan en config_viaje.json para mantenerlos entre sesiones.
# ─────────────────────────────────────────────────────────────────────────────
def _anadir_pendiente_checklist():
    """Callback: guarda la tarea antes del rerun y limpia los campos sin tocar
    el estado de widgets después de que Streamlit los haya renderizado.
    """
    texto = str(st.session_state.get("checklist_nuevo_texto", "") or "").strip()
    nota = str(st.session_state.get("checklist_nueva_nota", "") or "").strip()
    tipo = st.session_state.get("checklist_nuevo_tipo", "Otro")

    if not texto:
        st.session_state["_checklist_mensaje"] = ("warning", "Escribe qué tienes pendiente.")
        return

    config = st.session_state.config_viaje
    pendientes_actuales = config.setdefault("checklist_pendientes", [])
    if not isinstance(pendientes_actuales, list):
        pendientes_actuales = []
        config["checklist_pendientes"] = pendientes_actuales

    nuevo = {
        "id": hashlib.sha1(
            f"{texto}|{datetime.now().isoformat()}|{len(pendientes_actuales)}".encode("utf-8")
        ).hexdigest()[:12],
        "texto": texto,
        "tipo": tipo,
        "nota": nota,
        "hecho": False
    }
    pendientes_actuales.append(nuevo)

    try:
        guardado = guardar_config_viaje(config)
    except Exception as exc:
        logger.exception("Error al guardar una tarea de la checklist")
        guardado = False
        detalle_error = str(exc)
    else:
        detalle_error = ""

    if guardado:
        st.session_state["checklist_nuevo_texto"] = ""
        st.session_state["checklist_nueva_nota"] = ""
        st.session_state["checklist_formulario_abierto"] = False
        st.session_state["_checklist_mensaje"] = ("success", f"«{texto}» se ha añadido a la checklist.")
    else:
        # No dejar una tarea que no llegó a persistirse como si estuviera guardada.
        pendientes_actuales.pop()
        st.session_state["_checklist_mensaje"] = (
            "error",
            "No se ha podido guardar el pendiente. "
            + (f"Detalle: {detalle_error}" if detalle_error else "Revisa la configuración de persistencia.")
        )


if seccion_principal == "☑️Checklist":
    st.markdown("---")
    st.markdown("""
    <style>
      /* CABECERA: anula explícitamente el apilado móvil de Streamlit. */
      @media (max-width: 900px) {
        [class*="st-key-checklist_header_row"] [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          align-items: center !important;
          width: 100% !important;
          gap: 8px !important;
        }
        [class*="st-key-checklist_header_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
          flex: 1 1 auto !important;
          width: auto !important;
          min-width: 0 !important;
        }
        [class*="st-key-checklist_header_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
          flex: 0 0 48px !important;
          width: 48px !important;
          min-width: 48px !important;
          max-width: 48px !important;
        }
      }
      [class*="st-key-checklist_header_row"] [data-testid="stButton"] button {
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        font-size: 24px !important;
      }

      /* FORMULARIO: se selecciona el bloque real del formulario, no una
         supuesta clase st-key del formulario que Streamlit no aplica aquí. */
      @media (max-width: 900px) {
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          align-items: stretch !important;
          gap: 8px !important;
          width: 100% !important;
        }
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
          display: block !important;
          flex: 1 1 0% !important;
          width: 50% !important;
          min-width: 0 !important;
          max-width: 50% !important;
          padding: 0 !important;
        }
        [data-testid="stForm"] [data-testid="stFormSubmitButton"],
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
          box-sizing: border-box !important;
          display: flex !important;
          width: 100% !important;
          min-width: 0 !important;
          max-width: 100% !important;
        }
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
          min-height: 42px !important;
          min-width: 32px !important;
          height: auto !important;
          justify-content: center !important;
          align-items: center !important;
          white-space: normal !important;
          overflow-wrap: anywhere !important;
          padding: 8px 5px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)

    # Fila de cabecera: se fuerza a permanecer horizontal también en móvil.
    with st.container(key="checklist_header_row"):
        col_checklist_titulo, col_checklist_anadir = st.columns(
            [1, 0.16], vertical_alignment="center", gap="small"
        )
        with col_checklist_titulo:
            st.markdown(
                '<div class="ny-card-header">☑️ Checklist de pendientes</div>',
                unsafe_allow_html=True
            )
        with col_checklist_anadir:
            st.button(
                "＋",
                key="btn_abrir_formulario_checklist",
                help="Añadir un pendiente",
                on_click=lambda: st.session_state.__setitem__(
                    "checklist_formulario_abierto", True
                )
            )
    st.caption("Un sitio para apuntar todo lo que falta.")

    pendientes = st.session_state.config_viaje.setdefault("checklist_pendientes", [])
    if not isinstance(pendientes, list):
        pendientes = []
        st.session_state.config_viaje["checklist_pendientes"] = pendientes

    # El formulario permanece oculto hasta que se pulse el botón +.
    if "checklist_formulario_abierto" not in st.session_state:
        st.session_state["checklist_formulario_abierto"] = False



    with st.container():
        if st.session_state["checklist_formulario_abierto"]:
            with st.expander("Añadir detalle", expanded=True):
                nuevo_pendiente = st.text_input(
                    "¿Qué te falta?",
                    placeholder="Ej: Comprar entradas, sacar visa...",
                    key="checklist_nuevo_texto"
                )
                col_tipo, col_detalle = st.columns([1, 2])
                with col_tipo:
                    tipo_pendiente = st.selectbox(
                        "Tipo",
                        ["Hacer", "Comprar", "Reservar", "Otro"],
                        key="checklist_nuevo_tipo"
                    )
                with col_detalle:
                    detalle_pendiente = st.text_input(
                        "Nota (opcional)",
                        placeholder="Fecha, enlace, detalles...",
                        key="checklist_nueva_nota"
                    )

                st.button(
                    "＋ Añadir a la checklist",
                    use_container_width=True,
                    key="btn_anadir_checklist",
                    on_click=_anadir_pendiente_checklist
                )
                st.button(
                    "Cerrar",
                    key="btn_cerrar_formulario_checklist",
                    on_click=lambda: st.session_state.__setitem__("checklist_formulario_abierto", False)
                )

        mensaje_checklist = st.session_state.pop("_checklist_mensaje", None)
        if mensaje_checklist:
            nivel, mensaje = mensaje_checklist
            getattr(st, nivel)(mensaje)

    total_pendientes = len(pendientes)
    total_hechos = sum(1 for pnd in pendientes if pnd.get("hecho", False))
    total_abiertos = total_pendientes - total_hechos
    progreso = int(total_hechos / total_pendientes * 100) if total_pendientes else 0

    # Resumen compacto: las tres estadísticas permanecen en una única fila.
    st.markdown(
        f"""
        <div style="
            display:grid;
            grid-template-columns:repeat(3, minmax(0, 1fr));
            gap:12px;
            width:100%;
            margin:10px 0 14px 0;
        ">
          <div style="border:1px solid rgba(128,128,128,.28); border-radius:10px; padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:8px; min-width:0;
          transform: translateY(-4px);">
            <span style="font-size:0.95rem; white-space:nowrap;">Total</span>
            <strong style="font-size:1.35rem; white-space:nowrap;">{total_pendientes}</strong>
          </div>
          <div style="border:1px solid rgba(128,128,128,.28); border-radius:10px; padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:8px; min-width:0;">
            <span style="font-size:0.95rem; white-space:nowrap;">Pendientes</span>
            <strong style="font-size:1.35rem; white-space:nowrap;">{total_abiertos}</strong>
          </div>
          <div style="border:1px solid rgba(128,128,128,.28); border-radius:10px; padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:8px; min-width:0;">
            <span style="font-size:0.95rem; white-space:nowrap;">Completados</span>
            <strong style="font-size:1.35rem; white-space:nowrap;">{total_hechos}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(progreso / 100 if total_pendientes else 0, text=f"{progreso}% completado")

    filtro_checklist = st.radio(
        "Mostrar",
        ["Todos", "Pendientes", "Completados"],
        horizontal=True,
        key="filtro_checklist_pendientes"
    )

    visibles = [
        (i, pnd) for i, pnd in enumerate(pendientes)
        if filtro_checklist == "Todos"
        or (filtro_checklist == "Pendientes" and not pnd.get("hecho", False))
        or (filtro_checklist == "Completados" and pnd.get("hecho", False))
    ]

    if not visibles:
        if not pendientes:
            st.info("Todavía no has añadido nada. Escribe arriba todo lo que quieras recordar.")
        elif filtro_checklist == "Pendientes":
            st.success("¡Todo hecho! No tienes tareas pendientes.")
        else:
            st.info("No hay elementos en esta categoría.")
    
    else:
        # En móvil, replicar la distribución de Guardados: una sola fila
        # con texto flexible y las dos acciones fijas a la derecha.
        st.markdown(
            """
            <style>
            /* Acciones de checklist con el mismo lenguaje visual que Guardados. */
            [class*="st-key-checklist-edit-button-wrap-"],
            [class*="st-key-checklist-delete-button-wrap-"] {
                box-sizing: border-box !important;
                display: flex !important;
                flex: none !important;
                width: 24px !important;
                min-width: 24px !important;
                max-width: 24px !important;
                height: 24px !important;
                min-height: 24px !important;
                max-height: 24px !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: visible !important;
            }
            [class*="st-key-checklist-edit-button-wrap-"] [data-testid="stButton"],
            [class*="st-key-checklist-delete-button-wrap-"] [data-testid="stButton"],
            [class*="st-key-checklist-edit-button-wrap-"] button,
            [class*="st-key-checklist-delete-button-wrap-"] button {
                box-sizing: border-box !important;
                display: inline-flex !important;
                flex: none !important;
                width: 24px !important;
                min-width: 24px !important;
                max-width: 24px !important;
                height: 24px !important;
                min-height: 24px !important;
                max-height: 24px !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 !important;
                padding: 0 !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 7px !important;
                background-color: #FFFFFF !important;
                background-repeat: no-repeat !important;
                background-position: center !important;
                background-size: 16px 16px !important;
                font-size: 0 !important;
                line-height: 0 !important;
                overflow: hidden !important;
            }
            [class*="st-key-checklist-edit-button-wrap-"] button {
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
            }
            [class*="st-key-checklist-delete-button-wrap-"] button {
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 6h18'/%3E%3Cpath d='M8 6V4h8v2'/%3E%3Cpath d='m19 6-1 14H6L5 6'/%3E%3Cpath d='M10 11v5M14 11v5'/%3E%3C/svg%3E") !important;
            }
            [class*="st-key-checklist-edit-button-wrap-"] button > *,
            [class*="st-key-checklist-delete-button-wrap-"] button > * {
                display: none !important;
            }

            @media (max-width: 640px) {
                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] {
                    display: grid !important;
                    grid-template-columns: 22px minmax(0, 1fr) 24px 24px !important;
                    grid-auto-flow: row !important;
                    align-items: center !important;
                    justify-content: stretch !important;
                    column-gap: 4px !important;
                    row-gap: 0 !important;
                    width: 100% !important;
                    min-width: 0 !important;
                    max-width: 100% !important;
                    overflow: visible !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                    box-sizing: border-box !important;
                    display: flex !important;
                    flex: none !important;
                    width: auto !important;
                    min-width: 0 !important;
                    max-width: none !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    overflow: visible !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) {
                    grid-column: 1 !important;
                    width: 22px !important;
                    min-width: 22px !important;
                    max-width: 22px !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
                    grid-column: 2 !important;
                    width: 100% !important;
                    min-width: 0 !important;
                    max-width: 100% !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) {
                    grid-column: 3 !important;
                    width: 24px !important;
                    min-width: 24px !important;
                    max-width: 24px !important;
                    justify-content: flex-end !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {
                    grid-column: 4 !important;
                    width: 24px !important;
                    min-width: 24px !important;
                    max-width: 24px !important;
                    justify-content: flex-end !important;
                }

                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) button,
                [class*="st-key-checklist_item_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) button {
                    box-sizing: border-box !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 24px !important;
                    min-width: 24px !important;
                    max-width: 24px !important;
                    height: 24px !important;
                    min-height: 24px !important;
                    max-height: 24px !important;
                    padding: 0 !important;
                    margin: 0 0 0 auto !important;
                    font-size: 12px !important;
                    line-height: 1 !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        for indice, pendiente in visibles:
            pid = str(pendiente.get("id", indice))
            hecho_actual = bool(pendiente.get("hecho", False))

            with st.container(key=f"checklist_item_{pid}", border=True):

                # Fila: casilla | título y categoría | editar | borrar.
                col_check, col_texto, col_editar, col_borrar = st.columns(
                    [0.55, 8.2, 0.42, 0.42],
                    gap="small",
                    vertical_alignment="center"
                )

                with col_check:
                    marcado = st.checkbox(
                        "Completado",
                        value=hecho_actual,
                        key=f"check_pendiente_{pid}",
                        label_visibility="collapsed"
                    )

                if marcado != hecho_actual:
                    pendientes[indice]["hecho"] = marcado
                    st.session_state.config_viaje["checklist_pendientes"] = pendientes
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.rerun()

                # Nombre y categoría en la misma columna.
                with col_texto:
                    nombre_pnd = html.escape(
                        str(pendiente.get("texto", ""))
                    )

                    estilo_pnd = (
                        "text-decoration:line-through; color:#94A3B8;"
                        if hecho_actual else "color:#0F172A;"
                    )

                    st.markdown(
                        f"<div style='font-weight:750; line-height:1.2; {estilo_pnd}; overflow-wrap:anywhere;'>{nombre_pnd}</div>",
                        unsafe_allow_html=True
                    )

                    tipo_pnd = html.escape(
                        str(pendiente.get("tipo", "Otro"))
                    )
                    nota_pnd = str(
                        pendiente.get("nota", "") or ""
                    ).strip()

                    st.markdown(
                        f"<div style='font-size:0.72rem; color:#64748B; line-height:1.2; margin-top:2px; overflow-wrap:anywhere;'>"
                        f"{tipo_pnd}{' · ' + html.escape(nota_pnd) if nota_pnd else ''}</div>",
                        unsafe_allow_html=True
                    )

                # Lápiz pequeño a la derecha.
                with col_editar:
                    with st.container(key=f"checklist-edit-button-wrap-{pid}"):
                        if st.button(
                            " ",
                            key=f"editar_pendiente_{pid}",
                            help="Editar tarea"
                        ):
                            st.session_state["_checklist_edicion_id"] = pid
                            st.rerun()

                # Papelera al extremo derecho, con el mismo estilo que Guardados.
                with col_borrar:
                    with st.container(key=f"checklist-delete-button-wrap-{pid}"):
                        if st.button(
                            " ",
                            key=f"borrar_pendiente_{pid}",
                            help="Eliminar de la checklist"
                        ):
                            pendientes.pop(indice)
                            st.session_state.config_viaje["checklist_pendientes"] = pendientes

                            if guardar_config_viaje(st.session_state.config_viaje):
                                if st.session_state.get("_checklist_edicion_id") == pid:
                                    st.session_state.pop("_checklist_edicion_id", None)
                                st.rerun()

                # Formulario para editar la tarea.
                if st.session_state.get("_checklist_edicion_id") == pid:
                    with st.form(f"form_editar_pendiente_{pid}"):
                        st.markdown("**Editar tarea pendiente**")

                        texto_editado = st.text_input(
                            "Nombre de la tarea",
                            value=str(pendiente.get("texto", "")),
                            key=f"texto_editar_pendiente_{pid}"
                        )

                        opciones_tipo = [
                            "Hacer", "Ver / Visitar", "Comprar",
                            "Revisar", "Reservar", "Otro"
                        ]

                        tipo_actual = pendiente.get("tipo", "Otro")
                        if tipo_actual not in opciones_tipo:
                            opciones_tipo.append(tipo_actual)

                        tipo_editado = st.selectbox(
                            "Categoría",
                            opciones_tipo,
                            index=opciones_tipo.index(tipo_actual),
                            key=f"tipo_editar_pendiente_{pid}"
                        )

                        nota_editada = st.text_input(
                            "Nota (opcional)",
                            value=str(pendiente.get("nota", "") or ""),
                            key=f"nota_editar_pendiente_{pid}"
                        )

                        col_guardar_ed, col_cancelar_ed = st.columns([1, 1], gap="small")

                        with col_guardar_ed:
                            guardar_edicion = st.form_submit_button(
                                "💾 Guardar cambios",
                                use_container_width=True
                            )

                        with col_cancelar_ed:
                            cancelar_edicion = st.form_submit_button(
                                "Cancelar",
                                use_container_width=True
                            )

                    if guardar_edicion:
                        if not texto_editado.strip():
                            st.warning(
                                "El nombre de la tarea no puede estar vacío."
                            )
                        else:
                            tarea_anterior = dict(pendientes[indice])

                            pendientes[indice]["texto"] = texto_editado.strip()
                            pendientes[indice]["tipo"] = tipo_editado
                            pendientes[indice]["nota"] = nota_editada.strip()

                            st.session_state.config_viaje["checklist_pendientes"] = pendientes

                            if guardar_config_viaje(st.session_state.config_viaje):
                                st.session_state.pop("_checklist_edicion_id", None)
                                st.success("Tarea actualizada.")
                                st.rerun()
                            else:
                                pendientes[indice] = tarea_anterior
                                st.session_state.config_viaje["checklist_pendientes"] = pendientes
                                st.error("No se han podido guardar los cambios.")

                    elif cancelar_edicion:
                        st.session_state.pop("_checklist_edicion_id", None)
                        st.rerun()
