import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import json
import urllib.request
import urllib.parse
import os
import socket
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# Intento de importar Google Generative AI de forma opcional y segura
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

ARCH_PERSISTENCIA = "itinerario_actual.json"

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PREMIUM (ASPECTO DE APP DE PAGO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NYC Voyage Pro 🗽 | Planificador Premium",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo UI de alta gama (inspirado en Notion, Apple Maps y Wanderlog Pro)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ocultar barra superior por defecto de Streamlit para look nativo */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Contenedor Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #091E3A 0%, #173865 50%, #1F4E89 100%);
        border-radius: 18px;
        padding: 24px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 30, 60, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* KPI Cards */
    .kpi-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 16px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        text-align: center;
    }
    .kpi-num {
        font-size: 1.5rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .kpi-lbl {
        font-size: 0.75rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    /* Tarjetas de Sitios Estilo App de Viajes */
    .spot-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .spot-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.1);
    }
    .spot-card.completed {
        background: #F8FAFC;
        border-left: 5px solid #10B981;
        opacity: 0.85;
    }
    .spot-card.active {
        border-left: 5px solid #3B82F6;
    }
    .spot-card.fav {
        border-left: 5px solid #F59E0B;
    }

    /* Badges & Pills */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .pill-indoor { background: #EFF6FF; color: #1D4ED8; border: 1px solid #DBEAFE; }
    .pill-outdoor { background: #ECFDF5; color: #047857; border: 1px solid #D1FAE5; }
    .pill-cost { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .pill-time { background: #F3E8FF; color: #6B21A8; border: 1px solid #E9D5FF; }
    .pill-zone { background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }

    /* Botones táctiles refinados */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        letter-spacing: -0.2px;
        transition: all 0.2s ease !important;
    }
    
    /* Contenedor del mapa */
    iframe {
        border-radius: 16px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. CATÁLOGO BASE DE LUGARES ICÓNICOS DE NUEVA YORK
# -----------------------------------------------------------------------------
CATALOGO_NY = {
    "Empire State Building": {
        "lat": 40.748817, "lon": -73.985428, "tipo": "Interior", "categoria": "🏙️ Mirador", "zona": "Midtown", "notas": "Subir al mirador piso 86 / 102", "costo": 44, "hora": "10:00"
    },
    "Top of the Rock (Rockefeller Center)": {
        "lat": 40.759089, "lon": -73.979401, "tipo": "Interior", "categoria": "🏙️ Mirador", "zona": "Midtown", "notas": "Mejores vistas del Empire State", "costo": 40, "hora": "18:30"
    },
    "Summit One Vanderbilt": {
        "lat": 40.752830, "lon": -73.979140, "tipo": "Interior", "categoria": "🏙️ Mirador", "zona": "Midtown", "notas": "Espejos inmersivos (ideal si llueve)", "costo": 42, "hora": "16:00"
    },
    "Central Park (Bethesda Terrace)": {
        "lat": 40.773820, "lon": -73.970806, "tipo": "Exterior", "categoria": "🌳 Parque", "zona": "Uptown", "notas": "Paseo por The Mall y Bow Bridge", "costo": 0, "hora": "11:00"
    },
    "The Metropolitan Museum of Art (The Met)": {
        "lat": 40.779437, "lon": -73.963244, "tipo": "Interior", "categoria": "🏛️ Museo", "zona": "Upper East Side", "notas": "Templo de Dendur y arte egipcio", "costo": 30, "hora": "14:00"
    },
    "Museum of Modern Art (MoMA)": {
        "lat": 40.761436, "lon": -73.977621, "tipo": "Interior", "categoria": "🏛️ Museo", "zona": "Midtown", "notas": "Noche Estrellada de Van Gogh", "costo": 28, "hora": "11:30"
    },
    "American Museum of Natural History (AMNH)": {
        "lat": 40.781324, "lon": -73.973988, "tipo": "Interior", "categoria": "🏛️ Museo", "zona": "Upper West Side", "notas": "Dinosaurios y ballena azul gigante", "costo": 28, "hora": "10:00"
    },
    "Grand Central Terminal": {
        "lat": 40.752726, "lon": -73.977229, "tipo": "Interior", "categoria": "🚇 Monumento", "zona": "Midtown", "notas": "Galería de los susurros y Dining Concourse", "costo": 0, "hora": "13:00"
    },
    "Times Square": {
        "lat": 40.758896, "lon": -73.985130, "tipo": "Exterior", "categoria": "🎭 Entretenimiento", "zona": "Midtown", "notas": "Luces de neón y escaleras rojas TKTS", "costo": 0, "hora": "21:00"
    },
    "The High Line": {
        "lat": 40.748000, "lon": -74.004800, "tipo": "Exterior", "categoria": "🌳 Parque", "zona": "Chelsea", "notas": "Paseo elevado sobre antiguas vías de tren", "costo": 0, "hora": "10:30"
    },
    "Chelsea Market": {
        "lat": 40.742400, "lon": -74.006200, "tipo": "Interior", "categoria": "🍕 Gastronomía", "zona": "Chelsea", "notas": "Tacos No. 1 o lobster roll fresco", "costo": 25, "hora": "13:30"
    },
    "Little Island": {
        "lat": 40.741900, "lon": -74.009700, "tipo": "Exterior", "categoria": "🌳 Parque", "zona": "Meatpacking", "notas": "Parque flotante sobre el río Hudson", "costo": 0, "hora": "15:30"
    },
    "Brooklyn Bridge (Entrada Manhattan)": {
        "lat": 40.712600, "lon": -74.004800, "tipo": "Exterior", "categoria": "🌳 Monumento", "zona": "Lower Manhattan", "notas": "Cruzar andando hacia DUMBO", "costo": 0, "hora": "17:30"
    },
    "DUMBO - Washington Street": {
        "lat": 40.703400, "lon": -73.989700, "tipo": "Exterior", "categoria": "📸 Fotografía", "zona": "Brooklyn", "notas": "Foto clásica del Manhattan Bridge", "costo": 0, "hora": "18:45"
    },
    "Time Out Market New York (DUMBO)": {
        "lat": 40.703400, "lon": -73.992200, "tipo": "Interior", "categoria": "🍕 Gastronomía", "zona": "Brooklyn", "notas": "Food hall cubierto con terraza panorámica", "costo": 30, "hora": "20:00"
    },
    "9/11 Memorial & Ground Zero": {
        "lat": 40.711500, "lon": -74.013200, "tipo": "Exterior", "categoria": "🏛️ Monumento", "zona": "Financial District", "notas": "Piscinas conmemorativas", "costo": 0, "hora": "10:00"
    },
    "The Oculus (World Trade Center)": {
        "lat": 40.711800, "lon": -74.011300, "tipo": "Interior", "categoria": "🛍️ Compras", "zona": "Financial District", "notas": "Arquitectura de Calatrava y tiendas", "costo": 0, "hora": "11:30"
    },
    "Wall Street & Charging Bull": {
        "lat": 40.705600, "lon": -74.013400, "tipo": "Exterior", "categoria": "🏛️ Monumento", "zona": "Financial District", "notas": "Toro de Wall Street y Bolsa", "costo": 0, "hora": "12:30"
    },
    "Joe's Pizza (Greenwich Village)": {
        "lat": 40.730588, "lon": -74.002143, "tipo": "Interior", "categoria": "🍕 Gastronomía", "zona": "Greenwich Village", "notas": "La mejor porción de queso", "costo": 5, "hora": "14:30"
    },
    "Katz's Delicatessen": {
        "lat": 40.722200, "lon": -73.987400, "tipo": "Interior", "categoria": "🍕 Gastronomía", "zona": "Lower East Side", "notas": "Legendario sándwich de pastrami", "costo": 30, "hora": "13:00"
    },
    "New York Public Library (Stephen A. Schwarzman)": {
        "lat": 40.753200, "lon": -73.982200, "tipo": "Interior", "categoria": "🏛️ Cultura", "zona": "Midtown", "notas": "Rose Main Reading Room", "costo": 0, "hora": "15:00"
    },
    "Macy's Herald Square": {
        "lat": 40.750800, "lon": -73.988900, "tipo": "Interior", "categoria": "🛍️ Compras", "zona": "Midtown", "notas": "Grandes almacenes icónicos", "costo": 0, "hora": "17:00"
    }
}


# -----------------------------------------------------------------------------
# 3. FUNCIONES DE PERSISTENCIA Y UTILIDADES
# -----------------------------------------------------------------------------
def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def guardar_itinerario_disco(lugares):
    try:
        with open(ARCH_PERSISTENCIA, "w", encoding="utf-8") as f:
            json.dump(lugares, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def cargar_itinerario_disco():
    if os.path.exists(ARCH_PERSISTENCIA):
        try:
            with open(ARCH_PERSISTENCIA, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    return None

def inicializar_itinerario_base():
    base = []
    items_def = [
        ("Empire State Building", 1, "09:30", 44, True),
        ("Grand Central Terminal", 1, "12:00", 0, False),
        ("New York Public Library", 1, "14:00", 0, False),
        ("Times Square", 1, "20:00", 0, True),
        ("Central Park (Bethesda Terrace)", 2, "10:00", 0, True),
        ("The Metropolitan Museum of Art (The Met)", 2, "13:00", 30, True),
        ("American Museum of Natural History (AMNH)", 2, "16:30", 28, False),
        ("The High Line", 3, "10:30", 0, True),
        ("Chelsea Market", 3, "12:30", 25, True),
        ("Little Island", 3, "15:00", 0, False),
        ("Joe's Pizza (Greenwich Village)", 3, "19:00", 6, True),
        ("9/11 Memorial & Ground Zero", 4, "09:30", 0, True),
        ("The Oculus (World Trade Center)", 4, "11:30", 0, False),
        ("Brooklyn Bridge (Entrada Manhattan)", 4, "17:00", 0, True),
        ("Time Out Market New York (DUMBO)", 4, "19:30", 30, False)
    ]
    for idx, (nom, dia, hora, costo, fav) in enumerate(items_def, start=1):
        p = CATALOGO_NY.get(nom, {})
        base.append({
            "id": idx,
            "nombre": nom,
            "lat": p.get("lat", 40.758896),
            "lon": p.get("lon", -73.985130),
            "dia": dia,
            "tipo": p.get("tipo", "Interior"),
            "categoria": p.get("categoria", "Atracción"),
            "zona": p.get("zona", "Manhattan"),
            "notas": p.get("notas", ""),
            "costo": costo,
            "hora": hora,
            "favorito": fav,
            "visitado": False
        })
    return base

# Cargar lugares con respaldo en disco
if "lugares" not in st.session_state or not st.session_state.lugares:
    disco_lugares = cargar_itinerario_disco()
    st.session_state.lugares = disco_lugares if disco_lugares else inicializar_itinerario_base()

if "filtro_lluvia_global" not in st.session_state:
    st.session_state.filtro_lluvia_global = False

if "editando_id" not in st.session_state:
    st.session_state.editando_id = None

@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="ny_voyage_pro_v4")

geolocator = get_geolocator()

@st.cache_data(ttl=900)
def obtener_clima_detallado():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060"
            "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
            "&hourly=precipitation_probability,temperature_2m,weather_code"
            "&daily=precipitation_probability_max,temperature_2m_max,temperature_2m_min"
            "&timezone=America%2FNew_York"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'NYVoyagePro/3.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            current = data.get("current", {})
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            
            temp_c = current.get("temperature_2m", 18.0)
            temp_f = (temp_c * 9/5) + 32
            precip = current.get("precipitation", 0.0)
            prob_max_hoy = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
            code = current.get("weather_code", 0)
            lluvia_activa = precip > 0.1 or code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96]
            
            horas_prevision = []
            if "precipitation_probability" in hourly and len(hourly["precipitation_probability"]) >= 12:
                for h in range(0, 6):
                    horas_prevision.append({
                        "hora": f"+{h+1}h",
                        "prob": hourly["precipitation_probability"][h],
                        "temp": hourly["temperature_2m"][h]
                    })
                    
            return {
                "ok": True,
                "temp_c": round(temp_c, 1),
                "temp_f": round(temp_f, 1),
                "precip": precip,
                "prob_max": prob_max_hoy,
                "lluvia_activa": lluvia_activa,
                "humedad": current.get("relative_humidity_2m", 60),
                "viento": current.get("wind_speed_10m", 10),
                "horas": horas_prevision
            }
    except Exception:
        return {
            "ok": False,
            "temp_c": 19.5,
            "temp_f": 67.1,
            "precip": 0.0,
            "prob_max": 25,
            "lluvia_activa": False,
            "humedad": 55,
            "viento": 12,
            "horas": []
        }

clima_actual = obtener_clima_detallado()


# -----------------------------------------------------------------------------
# 4. HERRAMIENTAS DE IMPORTACIÓN DESDE GOOGLE MAPS
# -----------------------------------------------------------------------------
def extraer_coordenadas_de_url_google(url_txt):
    """Extrae latitud y longitud de enlaces estándar de Google Maps."""
    patron_coords = re.search(r'@([0-9.-]+),([0-9.-]+)', url_txt)
    if patron_coords:
        return float(patron_coords.group(1)), float(patron_coords.group(2))
    patron_q = re.search(r'q=([0-9.-]+),([0-9.-]+)', url_txt)
    if patron_q:
        return float(patron_q.group(1)), float(patron_q.group(2))
    return None

def parsear_kml_google_maps(contenido_kml):
    """Parsea archivos KML exportados desde Google My Maps."""
    lugares_extraidos = []
    try:
        root = ET.fromstring(contenido_kml)
        # Namespace handling
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        placemarks = root.findall('.//kml:Placemark', ns)
        if not placemarks:
            placemarks = root.findall('.//Placemark')
            
        for pm in placemarks:
            nombre = pm.findtext('./kml:name', default="", namespaces=ns) or pm.findtext('./name', default="Lugar Google Maps")
            desc = pm.findtext('./kml:description', default="", namespaces=ns) or pm.findtext('./description', default="")
            coords_txt = pm.findtext('.//kml:coordinates', default="", namespaces=ns) or pm.findtext('.//coordinates', default="")
            
            if coords_txt:
                partes = coords_txt.strip().split(',')
                if len(partes) >= 2:
                    lon = float(partes[0].strip())
                    lat = float(partes[1].strip())
                    lugares_extraidos.append({
                        "nombre": nombre.strip() if nombre else "Punto Guardado",
                        "lat": lat,
                        "lon": lon,
                        "notas": desc.strip()
                    })
    except Exception as e:
        st.error(f"Error al analizar archivo KML: {e}")
    return lugares_extraidos

def parsear_csv_google_takeout(df):
    """Parsea archivos CSV exportados desde Google Takeout (Lugares Guardados)."""
    lugares_extraidos = []
    # Detección inteligente de columnas
    cols_nom = [c for c in df.columns if any(k in c.lower() for k in ['title', 'nombre', 'name', 'place', 'lugar'])]
    cols_lat = [c for c in df.columns if any(k in c.lower() for k in ['lat', 'latitude', 'latitud'])]
    cols_lon = [c for c in df.columns if any(k in c.lower() for k in ['lon', 'long', 'longitude', 'lng'])]
    cols_not = [c for c in df.columns if any(k in c.lower() for k in ['comment', 'nota', 'note', 'description'])]
    cols_url = [c for c in df.columns if any(k in c.lower() for k in ['url', 'link', 'enlace'])]

    col_n = cols_nom[0] if cols_nom else df.columns[0]
    col_la = cols_lat[0] if cols_lat else None
    col_lo = cols_lon[0] if cols_lon else None
    col_no = cols_not[0] if cols_not else None
    col_u = cols_url[0] if cols_url else None

    for _, row in df.iterrows():
        nombre = str(row[col_n]) if pd.notna(row[col_n]) else "Sitio"
        notas = str(row[col_no]) if col_no and pd.notna(row[col_no]) else ""
        lat, lon = None, None
        
        if col_la and col_lo and pd.notna(row[col_la]) and pd.notna(row[col_lo]):
            try:
                lat = float(row[col_la])
                lon = float(row[col_lo])
            except Exception:
                pass
                
        # Si no hay coordenadas directas pero hay URL de Google Maps
        if (lat is None or lon is None) and col_u and pd.notna(row[col_u]):
            coords_url = extraer_coordenadas_de_url_google(str(row[col_u]))
            if coords_url:
                lat, lon = coords_url

        lugares_extraidos.append({
            "nombre": nombre,
            "lat": lat,
            "lon": lon,
            "notas": notas
        })
    return lugares_extraidos


# -----------------------------------------------------------------------------
# 5. BARRA LATERAL & HERO HEADER PRO
# -----------------------------------------------------------------------------
ip_local = obtener_ip_local()
url_movil = f"http://{ip_local}:8501"

with st.sidebar:
    st.markdown("### 🗽 NYC Voyage Pro")
    st.caption("Planificador de Viajes Nivel Experto")
    
    st.markdown("#### 📱 Acceso Móvil")
    st.markdown(f"Abre en tu móvil: **`{url_movil}`**")
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(url_movil)}"
    st.image(qr_url, caption="Escanea para abrir en el móvil", width=160)
    
    st.markdown("---")
    st.markdown("#### ⚙️ Acciones Rápidas")
    if st.button("🔄 Refrescar Clima", use_container_width=True):
        obtener_clima_detallado.clear()
        st.rerun()

    if st.button("💾 Guardar Copia en Disco", use_container_width=True):
        guardar_itinerario_disco(st.session_state.lugares)
        st.success("¡Guardado!")

    if st.button("🔄 Restablecer Itinerario Demo", use_container_width=True):
        st.session_state.lugares = inicializar_itinerario_base()
        guardar_itinerario_disco(st.session_state.lugares)
        st.rerun()

# CÁLCULOS KPI GENERALES
total_stops = len(st.session_state.lugares)
visitados = len([l for l in st.session_state.lugares if l.get("visitado", False)])
dias_count = len(set(l["dia"] for l in st.session_state.lugares)) if total_stops > 0 else 0
gasto_estimado = sum(float(l.get("costo", 0)) for l in st.session_state.lugares)
progreso_pct = int((visitados / total_stops * 100)) if total_stops > 0 else 0

# HERO BANNER PROFESIONAL
st.markdown(f"""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="background: rgba(59, 130, 246, 0.3); color: #93C5FD; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                NYC Premium Edition
            </span>
            <h1 style="margin: 8px 0 4px 0; font-size: 1.8rem; font-weight: 800; color: white;">Nueva York Itinerary Master</h1>
            <div style="color: #CBD5E1; font-size: 0.9rem;">
                🌤️ Manhattan: <b>{clima_actual['temp_c']} °C</b> &bull; {'🌧️ Lluvia en curso' if clima_actual['lluvia_activa'] else f'Prob. lluvia: {clima_actual["prob_max"]}%'} &bull; Humedad: {clima_actual['humedad']}%
            </div>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <div class="kpi-card">
                <div class="kpi-num">{dias_count}</div>
                <div class="kpi-lbl">Días</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">{total_stops}</div>
                <div class="kpi-lbl">Paradas</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">{progreso_pct}%</div>
                <div class="kpi-lbl">Progreso</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${gasto_estimado:.0f}</div>
                <div class="kpi-lbl">Presupuesto</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. PESTAÑAS PRINCIPALES DE LA APLICACIÓN
# -----------------------------------------------------------------------------
tabs = st.tabs([
    "🗺️ Mapa Google & Ruta",
    "✏️ Itinerario & Editor Pro",
    "📥 Importar de Google Maps",
    "🌧️ Modo Lluvia",
    "💵 Tax, Tip & Presupuesto",
    "🗽 Consejos & Cloud"
])


# =============================================================================
# TAB 1: MAPA CON CAPA OFICIAL DE GOOGLE MAPS
# =============================================================================
with tabs[0]:
    col_mctl1, col_mctl2, col_mctl3 = st.columns([2, 1.5, 1.5])
    
    dias_disp = sorted(list(set(l["dia"] for l in st.session_state.lugares))) if st.session_state.lugares else [1]
    
    with col_mctl1:
        dia_filtro = st.selectbox(
            "📅 Vista por Día:",
            ["Ver Todo el Viaje"] + [f"Día {d}" for d in dias_disp],
            index=1 if len(dias_disp) > 0 else 0,
            key="filtro_dia_mapa_g"
        )
    with col_mctl2:
        estilo_gmap = st.selectbox(
            "🗺️ Estilo de Mapa:",
            ["Google Maps Callejero", "Google Maps Satélite / Híbrido", "Google Maps Terreno", "OpenStreetMap"]
        )
    with col_mctl3:
        solo_favs = st.checkbox("⭐ Solo Favoritos", value=False)

    # Filtrado de datos
    spots_mapa = list(st.session_state.lugares)
    if dia_filtro != "Ver Todo el Viaje":
        d_n = int(dia_filtro.replace("Día ", ""))
        spots_mapa = [l for l in spots_mapa if l["dia"] == d_n]
    if solo_favs:
        spots_mapa = [l for l in spots_mapa if l.get("favorito", False)]
    if st.session_state.filtro_lluvia_global:
        spots_mapa = [l for l in spots_mapa if l.get("tipo") == "Interior"]

    if spots_mapa:
        avg_lat = sum(l["lat"] for l in spots_mapa) / len(spots_mapa)
        avg_lon = sum(l["lon"] for l in spots_mapa) / len(spots_mapa)
        
        # Mapeo de Capas de Google Maps en Folium
        # lyrs=m (roadmap), lyrs=y (hybrid satellite), lyrs=p (terrain)
        gmap_layers = {
            "Google Maps Callejero": ("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", "Google Maps"),
            "Google Maps Satélite / Híbrido": ("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", "Google Maps Satélite"),
            "Google Maps Terreno": ("https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}", "Google Maps Terreno"),
            "OpenStreetMap": ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap")
        }
        
        tile_url, tile_attr = gmap_layers[estilo_gmap]
        
        mapa = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=13 if dia_filtro != "Ver Todo el Viaje" else 12,
            tiles=None,
            scrollWheelZoom=False,
            zoom_control=True
        )
        
        folium.TileLayer(
            tiles=tile_url,
            attr=tile_attr,
            name=estilo_gmap,
            max_zoom=20
        ).add_to(mapa)

        coords_line = []
        for idx, s in enumerate(spots_mapa, 1):
            pt = (s["lat"], s["lon"])
            coords_line.append(pt)
            
            # Icono temático
            is_done = s.get("visitado", False)
            is_fav = s.get("favorito", False)
            
            if is_done:
                ic_col = "gray"
                ic_sym = "ok"
            elif is_fav:
                ic_col = "orange"
                ic_sym = "star"
            elif s.get("tipo") == "Interior":
                ic_col = "blue"
                ic_sym = "bookmark"
            else:
                ic_col = "green"
                ic_sym = "camera"

            gmaps_nav = f"https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lon']}"
            gmaps_place = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(s['nombre'])}"
            
            popup_html = f"""
            <div style="font-family: -apple-system, sans-serif; min-width: 210px; padding: 4px;">
                <div style="font-size: 11px; font-weight: 700; color: #4F46E5; text-transform: uppercase;">Día {s['dia']} &bull; {s.get('hora', 'Horario libre')}</div>
                <h4 style="margin: 2px 0 6px 0; color: #0F172A; font-size: 14px;">#{idx}. {s['nombre']}</h4>
                <div style="font-size: 12px; color: #475569; margin-bottom: 6px;">
                    📍 {s.get('zona', 'Manhattan')} &bull; {s.get('categoria', 'Visita')}<br>
                    {'🌧️ A cubierto' if s.get('tipo') == 'Interior' else '☀️ Al aire libre'} &bull; Presupuesto: <b>${s.get('costo', 0)}</b>
                </div>
                {f'<p style="font-size: 11px; margin: 4px 0; color: #64748B; font-style: italic;">📝 {s["notas"]}</p>' if s.get('notas') else ''}
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;">
                <div style="display: flex; gap: 4px;">
                    <a href="{gmaps_nav}" target="_blank" style="flex: 1; text-align: center; background: #2563EB; color: white; padding: 6px 4px; border-radius: 6px; font-size: 11px; font-weight: 700; text-decoration: none;">🧭 Ir GPS</a>
                    <a href="{gmaps_place}" target="_blank" style="flex: 1; text-align: center; background: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1; padding: 6px 4px; border-radius: 6px; font-size: 11px; font-weight: 700; text-decoration: none;">Google Maps</a>
                </div>
            </div>
            """
            
            folium.Marker(
                location=pt,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"#{idx} {s['nombre']} (${s.get('costo', 0)})",
                icon=folium.Icon(color=ic_col, icon=ic_sym, prefix="glyphicon")
            ).add_to(mapa)

        # Ruta trazada con estilo Google Maps
        if len(coords_line) > 1 and dia_filtro != "Ver Todo el Viaje":
            folium.PolyLine(
                coords_line,
                color="#2563EB",
                weight=5,
                opacity=0.85,
                dash_array="6, 8"
            ).add_to(mapa)

        st_folium(mapa, use_container_width=True, height=440, returned_objects=[])
    else:
        st.info("No hay sitios para mostrar con los filtros activos.")


# =============================================================================
# TAB 2: ITINERARIO INTERACTIVO & EDITOR COMPLETO (MAXIMA FLEXIBILIDAD)
# =============================================================================
with tabs[1]:
    st.markdown("### 📋 Gestor y Editor Pro del Itinerario")
    st.caption("Modifica cualquier campo con total libertad (día, nombre, hora, presupuesto, notas o prioridad).")

    # Si hay un sitio seleccionado para editar, mostramos el formulario de edición rápida
    if st.session_state.editando_id is not None:
        idx_ed = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == st.session_state.editando_id), None)
        if idx_ed is not None:
            spot_ed = st.session_state.lugares[idx_ed]
            with st.container():
                st.markdown(f"#### ✏️ Editando: **{spot_ed['nombre']}**")
                with st.form("form_edicion_pro"):
                    col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
                    with col_e1:
                        n_nom = st.text_input("Nombre de la atracción:", value=spot_ed["nombre"])
                    with col_e2:
                        n_dia = st.number_input("Día asignado:", min_value=1, max_value=30, value=int(spot_ed["dia"]))
                    with col_e3:
                        n_hora = st.text_input("Horario previsto (HH:MM):", value=spot_ed.get("hora", "12:00"))

                    col_e4, col_e5, col_e6, col_e7 = st.columns(4)
                    with col_e4:
                        n_tipo = st.selectbox("Entorno:", ["Interior", "Exterior"], index=0 if spot_ed.get("tipo") == "Interior" else 1)
                    with col_e5:
                        cats = ["🏛️ Museo / Cultura", "🌳 Parque", "🍕 Gastronomía", "🛍️ Compras", "🏙️ Mirador", "🎭 Entretenimiento", "🚇 Monumento", "🏨 Hotel"]
                        cat_idx = next((i for i, c in enumerate(cats) if spot_ed.get("categoria", "") in c), 0)
                        n_cat = st.selectbox("Categoría:", cats, index=cat_idx)
                    with col_e6:
                        n_costo = st.number_input("Presupuesto / Entrada ($ USD):", min_value=0.0, value=float(spot_ed.get("costo", 0)), step=5.0)
                    with col_e7:
                        n_fav = st.checkbox("⭐ Destacado / Favorito", value=spot_ed.get("favorito", False))

                    n_notas = st.text_area("Notas, enlaces o indicaciones:", value=spot_ed.get("notas", ""))

                    col_eb1, col_eb2 = st.columns(2)
                    with col_eb1:
                        guardar_ed = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    with col_eb2:
                        cancelar_ed = st.form_submit_button("❌ Cancelar", use_container_width=True)

                    if guardar_ed:
                        st.session_state.lugares[idx_ed]["nombre"] = n_nom
                        st.session_state.lugares[idx_ed]["dia"] = int(n_dia)
                        st.session_state.lugares[idx_ed]["hora"] = n_hora
                        st.session_state.lugares[idx_ed]["tipo"] = n_tipo
                        st.session_state.lugares[idx_ed]["categoria"] = n_cat
                        st.session_state.lugares[idx_ed]["costo"] = n_costo
                        st.session_state.lugares[idx_ed]["favorito"] = n_fav
                        st.session_state.lugares[idx_ed]["notas"] = n_notas
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.session_state.editando_id = None
                        st.success("¡Parada actualizada correctamente!")
                        st.rerun()

                    if cancelar_ed:
                        st.session_state.editando_id = None
                        st.rerun()
            st.markdown("---")

    # Controles por lotes y filtros
    col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1.5])
    with col_f1:
        dia_filtro_ed = st.selectbox(
            "Filtrar lista por día:",
            ["Todos los días"] + [f"Día {d}" for d in dias_disp],
            key="filtro_ed_dias"
        )
    with col_f2:
        ordenar_por = st.selectbox("Ordenar por:", ["Día y Horario", "Nombre A-Z", "Mayor Costo", "Favoritos primero"])
    with col_f3:
        # Acción en masa
        accion_masa = st.selectbox("Acciones en lote:", ["-- Seleccionar acción --", "Marcar visibles como completados", "Desmarcar todos", "Limpiar completados"])
        if accion_masa != "-- Seleccionar acción --":
            if st.button("Ejecutar Acción"):
                if accion_masa == "Marcar visibles como completados":
                    for l in st.session_state.lugares:
                        if dia_filtro_ed == "Todos los días" or l["dia"] == int(dia_filtro_ed.replace("Día ", "")):
                            l["visitado"] = True
                elif accion_masa == "Desmarcar todos":
                    for l in st.session_state.lugares:
                        l["visitado"] = False
                elif accion_masa == "Limpiar completados":
                    st.session_state.lugares = [l for l in st.session_state.lugares if not l.get("visitado", False)]
                guardar_itinerario_disco(st.session_state.lugares)
                st.rerun()

    # Obtener lista ordenada
    lugares_editables = list(st.session_state.lugares)
    if dia_filtro_ed != "Todos los días":
        d_val = int(dia_filtro_ed.replace("Día ", ""))
        lugares_editables = [l for l in lugares_editables if l["dia"] == d_val]

    if ordenar_por == "Nombre A-Z":
        lugares_editables.sort(key=lambda x: x["nombre"])
    elif ordenar_por == "Mayor Costo":
        lugares_editables.sort(key=lambda x: x.get("costo", 0), reverse=True)
    elif ordenar_por == "Favoritos primero":
        lugares_editables.sort(key=lambda x: x.get("favorito", False), reverse=True)
    else:
        lugares_editables.sort(key=lambda x: (x["dia"], x.get("hora", "00:00")))

    # Render de tarjetas táctiles y editables
    for idx_item, spot in enumerate(lugares_editables):
        idx_real = next((i for i, x in enumerate(st.session_state.lugares) if x["id"] == spot["id"]), None)
        if idx_real is None:
            continue

        is_done = spot.get("visitado", False)
        is_fav = spot.get("favorito", False)
        card_cls = "spot-card completed" if is_done else ("spot-card fav" if is_fav else "spot-card active")

        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([0.6, 4.5, 1.2, 1, 1])

        with col_c1:
            chk = st.checkbox("Vis", value=is_done, key=f"chk_done_{spot['id']}", label_visibility="collapsed")
            if chk != is_done:
                st.session_state.lugares[idx_real]["visitado"] = chk
                guardar_itinerario_disco(st.session_state.lugares)
                st.rerun()

        with col_c2:
            nom_style = "text-decoration: line-through; color: #94A3B8;" if is_done else "color: #0F172A; font-weight: 700; font-size: 1.05rem;"
            star_lbl = "⭐ " if is_fav else ""
            pill_tipo = f'<span class="pill pill-indoor">🌧️ Interior</span>' if spot.get("tipo") == "Interior" else f'<span class="pill pill-outdoor">☀️ Exterior</span>'
            pill_cost = f'<span class="pill pill-cost">${spot.get("costo", 0):.0f}</span>'
            pill_time = f'<span class="pill pill-time">⏰ {spot.get("hora", "Horario libre")}</span>'
            pill_zone = f'<span class="pill pill-zone">{spot.get("zona", "NY")}</span>'
            
            st.markdown(f"""
            <div style="{nom_style}">{star_lbl}Día {spot['dia']} &bull; {spot['nombre']}</div>
            <div style="margin-top: 4px; display: flex; gap: 6px; flex-wrap: wrap;">
                {pill_time} {pill_tipo} {pill_cost} {pill_zone}
            </div>
            {f'<div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;"><i>📝 {spot["notas"]}</i></div>' if spot.get("notas") else ''}
            """, unsafe_allow_html=True)

        with col_c3:
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={spot['lat']},{spot['lon']}"
            st.markdown(f"""
            <a href="{gmaps_url}" target="_blank" style="display: block; text-align: center; background: #EFF6FF; border: 1px solid #BFDBFE; color: #1D4ED8; font-weight: 700; border-radius: 8px; padding: 6px; font-size: 0.78rem; text-decoration: none;">
                🧭 Google Maps
            </a>
            """, unsafe_allow_html=True)

        with col_c4:
            if st.button("✏️", key=f"btn_edit_{spot['id']}", help="Editar esta atracción"):
                st.session_state.editando_id = spot["id"]
                st.rerun()

        with col_c5:
            if st.button("🗑️", key=f"btn_del_{spot['id']}", help="Eliminar atracción"):
                st.session_state.lugares.pop(idx_real)
                guardar_itinerario_disco(st.session_state.lugares)
                st.rerun()

    # Añadir sitio nuevo personalizado
    st.markdown("---")
    with st.expander("➕ Añadir Nueva Parada Manualmente"):
        with st.form("form_add_manual"):
            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                an_nom = st.text_input("Nombre de la atracción o lugar:", placeholder="Ej: B&H Photo Video")
            with c_a2:
                an_dia = st.number_input("Día del viaje:", min_value=1, max_value=30, value=1)
            with c_a3:
                an_hora = st.text_input("Horario sugerido:", value="11:00")

            c_a4, c_a5, c_a6, c_a7 = st.columns(4)
            with c_a4:
                an_tipo = st.selectbox("Entorno:", ["Interior", "Exterior"])
            with c_a5:
                an_cat = st.selectbox("Categoría:", ["🏛️ Museo / Cultura", "🌳 Parque", "🍕 Gastronomía", "🛍️ Compras", "🏙️ Mirador", "🎭 Entretenimiento", "🚇 Monumento", "🏨 Hotel"])
            with c_a6:
                an_cost = st.number_input("Costo estimado ($):", min_value=0.0, value=0.0, step=5.0)
            with c_a7:
                an_fav = st.checkbox("Favorito ⭐")

            an_zona = st.selectbox("Zona:", ["Midtown", "Lower Manhattan", "Brooklyn / DUMBO", "Upper East Side", "Upper West Side", "Chelsea / Meatpacking", "SoHo / Village"])
            an_notas = st.text_input("Notas u observaciones:")

            btn_crear = st.form_submit_button("💾 Guardar Parada en Itinerario", use_container_width=True)
            if btn_crear:
                if not an_nom.strip():
                    st.error("Introduce el nombre del sitio.")
                else:
                    with st.spinner("Geolocalizando sitio en Nueva York..."):
                        lat_f, lon_f = 40.758896, -73.985130
                        try:
                            loc_res = geolocator.geocode(f"{an_nom}, New York, NY", timeout=5)
                            if loc_res:
                                lat_f, lon_f = loc_res.latitude, loc_res.longitude
                        except Exception:
                            pass
                        
                        nuevo_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0) + 1
                        st.session_state.lugares.append({
                            "id": nuevo_id,
                            "nombre": an_nom.strip(),
                            "lat": lat_f,
                            "lon": lon_f,
                            "dia": int(an_dia),
                            "tipo": an_tipo,
                            "categoria": an_cat,
                            "zona": an_zona,
                            "notas": an_notas.strip(),
                            "costo": float(an_cost),
                            "hora": an_hora,
                            "favorito": an_fav,
                            "visitado": False
                        })
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.success(f"¡'{an_nom}' añadido con éxito!")
                        st.rerun()


# =============================================================================
# TAB 3: IMPORTADOR UNIVERSAL DESDE GOOGLE MAPS
# =============================================================================
with tabs[2]:
    st.markdown("### 📥 Importar Sitios y Listas desde Google Maps")
    st.markdown("""
    Pasa tus sitios guardados de Google Maps directamente a esta app. Puedes usar cualquiera de los tres métodos:
    """)

    metodo_imp = st.radio(
        "Elige el método de importación:",
        [
            "📋 Método 1: Pegar lista de nombres o enlaces de Google Maps (Recomendado y más rápido)",
            "📁 Método 2: Subir archivo KML de Google My Maps",
            "📊 Método 3: Subir archivo CSV de Google Takeout / Guardados"
        ]
    )

    if "Método 1" in metodo_imp:
        st.markdown("##### 📋 Pegar texto o enlaces de Google Maps")
        st.caption("Pega una lista de nombres de sitios (uno por línea) o enlaces compartidos de Google Maps:")
        
        texto_pegado = st.text_area(
            "Pega aquí tus sitios:",
            height=160,
            placeholder="Ejemplo:\nLevain Bakery\nChelsea Market\nhttps://maps.google.com/?q=40.7580,-73.9855\nThe High Line\nKatz's Delicatessen"
        )
        
        col_im1, col_im2 = st.columns(2)
        with col_im1:
            dia_dest_imp = st.number_input("Asignar al Día:", min_value=1, max_value=30, value=1)
        with col_im2:
            tipo_dest_imp = st.selectbox("Entorno por defecto:", ["Interior", "Exterior"])

        if st.button("🚀 Procesar e Importar Sitios", use_container_width=True):
            lineas = [l.strip() for l in texto_pegado.split('\n') if l.strip()]
            if not lineas:
                st.warning("Pega al menos un sitio o enlace.")
            else:
                progreso_imp = st.progress(0, text="Iniciando importación...")
                anadidos = 0
                
                for idx_l, linea in enumerate(lineas):
                    progreso_imp.progress((idx_l + 1) / len(lineas), text=f"Procesando: {linea[:30]}...")
                    coords_u = extraer_coordenadas_de_url_google(linea)
                    
                    nombre_final = linea
                    lat_final = 40.758896
                    lon_final = -73.985130
                    
                    if coords_u:
                        lat_final, lon_final = coords_u
                        nombre_final = f"Punto Google Maps #{idx_l + 1}"
                    else:
                        # Si está en el catálogo, tomar datos directos
                        if linea in CATALOGO_NY:
                            p = CATALOGO_NY[linea]
                            lat_final, lon_final = p["lat"], p["lon"]
                        else:
                            try:
                                loc = geolocator.geocode(f"{linea}, New York, NY", timeout=4)
                                if loc:
                                    lat_final, lon_final = loc.latitude, loc.longitude
                            except Exception:
                                pass
                    
                    nuevo_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0) + 1
                    st.session_state.lugares.append({
                        "id": nuevo_id,
                        "nombre": nombre_final,
                        "lat": lat_final,
                        "lon": lon_final,
                        "dia": int(dia_dest_imp),
                        "tipo": tipo_dest_imp,
                        "categoria": "Atracción Importada",
                        "zona": "Manhattan",
                        "notas": "Importado desde Google Maps",
                        "costo": 0,
                        "hora": "12:00",
                        "favorito": False,
                        "visitado": False
                    })
                    anadidos += 1

                guardar_itinerario_disco(st.session_state.lugares)
                st.success(f"¡Se han importado {anadidos} sitios correctamente al Día {dia_dest_imp}!")
                st.rerun()

    elif "Método 2" in metodo_imp:
        st.markdown("##### 📁 Subir archivo KML (Google My Maps)")
        st.caption("Si tienes un mapa personalizado creado en Google My Maps (mymaps.google.com), expórtalo como KML y súbelo aquí:")
        
        arch_kml = st.file_uploader("Selecciona archivo .kml:", type=["kml"])
        dia_kml = st.number_input("Asignar paradas al Día:", min_value=1, max_value=30, value=1, key="dia_kml_input")
        
        if arch_kml is not None:
            if st.button("📥 Importar desde KML", use_container_width=True):
                contenido = arch_kml.read().decode('utf-8', errors='ignore')
                items = parsear_kml_google_maps(contenido)
                if not items:
                    st.error("No se encontraron puntos válidos en el archivo KML.")
                else:
                    for it in items:
                        nuevo_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0) + 1
                        st.session_state.lugares.append({
                            "id": nuevo_id,
                            "nombre": it["nombre"],
                            "lat": it["lat"],
                            "lon": it["lon"],
                            "dia": int(dia_kml),
                            "tipo": "Interior",
                            "categoria": "Google My Maps",
                            "zona": "NYC",
                            "notas": it.get("notas", ""),
                            "costo": 0,
                            "hora": "12:00",
                            "favorito": False,
                            "visitado": False
                        })
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.success(f"¡Se han importado {len(items)} paradas desde tu mapa de Google!")
                    st.rerun()

    else:
        st.markdown("##### 📊 Subir archivo CSV de Google Takeout")
        st.caption("Sube el archivo CSV de lugares guardados de Google Maps:")
        arch_csv = st.file_uploader("Selecciona archivo .csv:", type=["csv"])
        dia_csv = st.number_input("Asignar paradas al Día:", min_value=1, max_value=30, value=1, key="dia_csv_input")
        
        if arch_csv is not None:
            if st.button("📥 Importar desde CSV", use_container_width=True):
                df_takeout = pd.read_csv(arch_csv)
                items_csv = parsear_csv_google_takeout(df_takeout)
                c_importados = 0
                for it in items_csv:
                    if it["lat"] and it["lon"]:
                        nuevo_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0) + 1
                        st.session_state.lugares.append({
                            "id": nuevo_id,
                            "nombre": it["nombre"],
                            "lat": it["lat"],
                            "lon": it["lon"],
                            "dia": int(dia_csv),
                            "tipo": "Interior",
                            "categoria": "Google Takeout",
                            "zona": "NYC",
                            "notas": it.get("notas", ""),
                            "costo": 0,
                            "hora": "12:00",
                            "favorito": False,
                            "visitado": False
                        })
                        c_importados += 1
                guardar_itinerario_disco(st.session_state.lugares)
                st.success(f"¡Se han importado {c_importados} sitios desde tu archivo de Google Maps!")
                st.rerun()


# =============================================================================
# TAB 4: MODO LLUVIA INTELIGENTE
# =============================================================================
with tabs[3]:
    st.markdown("### 🌧️ Modo Lluvia Inteligente")
    st.caption("Adapta tu ruta en tiempo real según las inclemencias meteorológicas de Manhattan.")

    col_rn1, col_rn2 = st.columns([3, 2])
    with col_rn1:
        st.markdown(f"""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 14px;">
            <h4 style="margin: 0; color: #1E40AF;">🌦️ Estado Meteorológico en Manhattan</h4>
            <div style="font-size: 1.1rem; color: #0F172A; margin-top: 4px;">
                <b>{clima_actual['temp_c']} °C</b> ({clima_actual['temp_f']} °F) &bull; Humedad: {clima_actual['humedad']}% &bull; Viento: {clima_actual['viento']} km/h
            </div>
            <div style="color: {'#DC2626' if clima_actual['prob_max'] >= 50 else '#16A34A'}; font-weight: 700; margin-top: 4px;">
                Probabilidad de lluvia hoy: {clima_actual['prob_max']}% {'(⚠️ Alta)' if clima_actual['prob_max'] >= 50 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_rn2:
        t_lluvia = st.toggle("☔ Activar Filtro de Sitios a Cubierto", value=st.session_state.filtro_lluvia_global)
        st.session_state.filtro_lluvia_global = t_lluvia

    st.markdown("---")
    st.markdown("#### 🔄 Sustituciones Rápidas por Lluvia")
    st.write("Cambia planes exteriores por alternativas cubiertas con 1 clic:")

    reemplazos = [
        ("Central Park ➡️ The Met Museum", "Central Park (Bethesda Terrace)", "The Metropolitan Museum of Art (The Met)"),
        ("The High Line ➡️ Chelsea Market", "The High Line", "Chelsea Market"),
        ("Puente de Brooklyn ➡️ The Oculus WTC", "Brooklyn Bridge (Entrada Manhattan)", "The Oculus (World Trade Center)"),
        ("Top of the Rock ➡️ Summit One Vanderbilt", "Top of the Rock (Rockefeller Center)", "Summit One Vanderbilt")
    ]

    for lbl_r, ext, inn in reemplazos:
        col_sw1, col_sw2 = st.columns([3, 1.2])
        with col_sw1:
            st.markdown(f"**{lbl_r}**")
        with col_sw2:
            if st.button("Sustituir", key=f"btn_swap_{ext}", use_container_width=True):
                for s in st.session_state.lugares:
                    if s["nombre"] == ext:
                        p = CATALOGO_NY[inn]
                        s["nombre"] = inn
                        s["lat"] = p["lat"]
                        s["lon"] = p["lon"]
                        s["tipo"] = "Interior"
                        s["notas"] = "Cambiado por lluvia"
                        break
                guardar_itinerario_disco(st.session_state.lugares)
                st.success(f"¡Cambiado a {inn}!")
                st.rerun()


# =============================================================================
# TAB 5: CALCULADORA DE IMPUESTOS, PROPINAS Y PRESUPUESTO
# =============================================================================
with tabs[4]:
    st.markdown("### 💵 Calculadora de Cuenta NY & Presupuesto del Viaje")
    st.caption("Calcula el 8.875% de impuesto, la propina recomendada y controla el presupuesto total.")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### 🧾 Calculadora de Restaurante")
        subt = st.number_input("Precio base en carta ($ USD):", min_value=0.0, value=55.0, step=5.0, format="%.2f")
        es_ropa = st.checkbox("🛍️ Compra de ropa/calzado < $110 (Exento 0% Tax)")
        tax_rate = 0.0 if es_ropa else 0.08875

        pct_tip = st.radio("Porcentaje de propina:", [15, 18, 20, 22, 25], index=2, horizontal=True)
        monto_tax = subt * tax_rate
        monto_tip = subt * (pct_tip / 100.0)
        gran_total = subt + monto_tax + monto_tip

        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between;"><span>Subtotal:</span><strong>${subt:.2f}</strong></div>
            <div style="display: flex; justify-content: space-between; color: #64748B;"><span>Tax NY ({'0%' if es_ropa else '8.875%'}):</span><span>+ ${monto_tax:.2f}</span></div>
            <div style="display: flex; justify-content: space-between; color: #64748B;"><span>Propina ({pct_tip}%):</span><span>+ ${monto_tip:.2f}</span></div>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #CBD5E1;">
            <div style="display: flex; justify-content: space-between; font-size: 1.2rem; font-weight: 800; color: #0F766E;">
                <span>Total a Pagar:</span><span>${gran_total:.2f} USD</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        num_comensales = st.slider("Dividir cuenta entre:", min_value=1, max_value=10, value=2)
        total_p = gran_total / num_comensales
        st.info(f"👉 **Por persona ({num_comensales} pers):** **${total_p:.2f} USD** (~ {total_p * 0.92:.2f} €)")

    with col_t2:
        st.markdown("#### 📊 Presupuesto Total del Viaje")
        # Desglose de costos del itinerario
        df_costs = pd.DataFrame(st.session_state.lugares)
        if not df_costs.empty and "costo" in df_costs.columns:
            costo_total = df_costs["costo"].sum()
            costo_por_dia = df_costs.groupby("dia")["costo"].sum().reset_index()
            
            st.metric("Gasto Total en Atracciones y Entradas", f"${costo_total:.2f} USD", f"~ {costo_total*0.92:.2f} €")
            
            st.markdown("##### Gasto por Día:")
            st.dataframe(costo_por_dia.rename(columns={"dia": "Día del Viaje", "costo": "Gasto Estimado ($)"}), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 6: CONSEJOS LOCALES Y GUÍA CLOUD
# =============================================================================
with tabs[5]:
    st.markdown("### 🗽 Consejos de Supervivencia & Despliegue en la Nube")

    with st.expander("☁️ ¿Cómo tener la app funcionando 24/7 en NY sin el PC de casa?", expanded=True):
        st.markdown("""
        Para usar esta aplicación en tu móvil en cualquier calle de Manhattan con tus datos móviles (4G/5G, eSIM o Wi-Fi del hotel):
        
        1. **Sube tu carpeta a GitHub:** Entra en [github.com](https://github.com), crea un repositorio privado o público y sube `app.py` y `requirements.txt`.
        2. **Conéctalo a Streamlit Community Cloud (100% Gratis):**
           * Entra en [share.streamlit.io](https://share.streamlit.io).
           * Inicia sesión con GitHub y pulsa **"Deploy an app"**.
           * Selecciona tu repositorio y dale a **Deploy**.
        3. **Listo:** Te dará una URL pública tipo `https://tu-viaje-ny.streamlit.app` que podrás abrir en el navegador de tu móvil o compartir con tus amigos.
        """)

    with st.expander("📥 Descargar Copia Offline (Para el metro sin cobertura)"):
        filas_html = ""
        for l in sorted(st.session_state.lugares, key=lambda x: (x['dia'], x['id'])):
            filas_html += f"""
            <div style="background: white; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid #2563eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <strong>Día {l['dia']} ({l.get('hora', '')}): {l['nombre']}</strong>
                <div>📍 {l.get('zona', '')} &bull; ${l.get('costo', 0)}</div>
                <div style="color: #64748b; font-size: 13px;"><i>{l.get('notas', '')}</i></div>
                <div style="margin-top: 6px;"><a href="https://www.google.com/maps/dir/?api=1&destination={l['lat']},{l['lon']}">🧭 Abrir en Google Maps</a></div>
            </div>
            """
        html_doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Itinerario NY Offline</title></head><body style='font-family: sans-serif; background: #f8fafc; padding: 14px;'><h2>🗽 Itinerario NY Offline</h2>{filas_html}</body></html>"
        st.download_button("📥 Descargar Guía HTML Offline", data=html_doc, file_name="itinerario_offline_ny.html", mime="text/html", use_container_width=True)

    with st.expander("🚇 OMNY y Transporte"):
        st.write("Usa directamente tu móvil con Apple Pay o Google Wallet en los tornos del metro ($2.90 por viaje). A partir del viaje 12 en 7 días, todos los viajes restantes de esa semana son gratis.")
