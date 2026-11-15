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

  /* Botón pequeño de edición ✏️ junto al nombre */
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

  /* Input de hora compacto y cuadrado (web y móvil) */
  [data-testid="column"]:has(.compact-hora) [data-testid="stTextInput"] {
    max-width: 88px !important;
    width: 100% !important;
    margin: 0 !important;
  }
  [data-testid="column"]:has(.compact-hora) [data-baseweb="input"],
  [data-testid="column"]:has(.compact-hora) [data-baseweb="base-input"] {
    height: 30px !important;
    min-height: 30px !important;
    max-height: 30px !important;
    border-radius: 8px !important;
    border: 1px dashed #94A3B8 !important;
    background: #F8FAFC !important;
    padding: 0 !important;
  }
  [data-testid="column"]:has(.compact-hora) input {
    height: 28px !important;
    min-height: 28px !important;
    max-height: 28px !important;
    padding: 0 4px !important;
    font-size: 0.77rem !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    text-align: center !important;
    background: transparent !important;
    border: none !important;
  }
  [data-testid="column"]:has(.compact-hora) [data-baseweb="input"]:focus-within {
    background: #FFFFFF !important;
    border: 1.5px solid #2563EB !important;
  }

  /* Controles compactos: el marcador identifica la columna del widget. */
  [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] > div {
    min-height: 30px !important;
    height: 30px !important;
    max-height: 30px !important;
    border-radius: 8px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    font-size: 0.78rem !important;
  }
  [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] span,
  [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] div {
    font-size: 0.78rem !important;
    line-height: 1.1 !important;
  }
  [data-testid="column"]:has(.compact-maps) [data-testid="stLinkButton"] > a,
  [data-testid="column"]:has(.compact-maps) .stButton > button {
    min-height: 30px !important;
    height: 30px !important;
    max-height: 30px !important;
    font-size: 0.77rem !important;
    padding: 0 0.45rem !important;
    border-radius: 8px !important;
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
      padding: 11px 12px !important;
      border-radius: 14px !important;
      margin-bottom: 9px !important;
      min-width: 0 !important;
    }
    .hero-title { font-size: 1.32rem !important; line-height: 1.18 !important; }
    .hero-eyebrow {
      font-size: 0.64rem !important;
      letter-spacing: 0.65px !important;
      line-height: 1.35 !important;
    }
    .hero-pill {
      display: inline-flex !important;
      max-width: 100% !important;
      white-space: normal !important;
      overflow-wrap: anywhere !important;
      font-size: 0.71rem !important;
      line-height: 1.25 !important;
      padding: 4px 8px !important;
    }
    .hero-stat-box { min-width: 0 !important; flex: 1 1 28% !important; padding: 5px 4px !important; }
    .hero-stat-val { font-size: 1.08rem !important; }
    .hero-stat-lbl {
      font-size: 0.58rem !important;
      letter-spacing: 0.35px !important;
      overflow-wrap: anywhere !important;
    }

    .ny-card { padding: 10px 11px !important; border-radius: 13px !important; min-width: 0 !important; }
    .ny-card-header { font-size: 0.76rem !important; letter-spacing: 0.7px !important; line-height: 1.3 !important; }
    .place-sheet { padding: 10px 11px !important; border-radius: 13px !important; min-width: 0 !important; }
    .place-note { font-size: 0.76rem !important; line-height: 1.35 !important; overflow-wrap: anywhere !important; }

    /* Regla segura por defecto: filas de formulario y filtros se apilan. */
    [data-testid="stHorizontalBlock"] {
      display: flex !important;
      flex-wrap: wrap !important;
      align-items: flex-start !important;
      gap: 0.5rem !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
      flex: 1 1 100% !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }

    /* Filas de nombre dentro de contenedores con identidad CSS propia. */
    [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 26px minmax(0, 1fr) 36px !important;
      column-gap: 6px !important;
      row-gap: 0 !important;
      align-items: start !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    [class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) 36px !important;
      column-gap: 6px !important;
      row-gap: 0 !important;
      align-items: start !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    [class*="st-key-it-heading-row-"] [data-testid="column"],
    [class*="st-key-saved-heading-row-"] [data-testid="column"] {
      display: block !important;
      flex: none !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    .edit-mini-btn { display: flex !important; justify-content: flex-end !important; width: 100% !important; }
    .edit-mini-btn button,
    [data-testid="column"]:has(.edit-mini-btn) .stButton > button {
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 27px !important;
      min-width: 27px !important;
      max-width: 27px !important;
      height: 27px !important;
      min-height: 27px !important;
      max-height: 27px !important;
      padding: 0 !important;
      font-size: 0.72rem !important;
      line-height: 1 !important;
    }

    /* Hora | Día | Maps: la hora tiene anchura suficiente para HH:MM,
       el día ocupa solo el ancho natural de su opción más larga y Maps es icono. */
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 76px max-content 40px !important;
      justify-content: start !important;
      align-items: center !important;
      column-gap: 6px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      flex: none !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }

    /* Marcadores HTML sin altura; solo sirven para identificar cada columna. */
    .mobile-control-marker { display: block !important; width: 0 !important; height: 0 !important; margin: 0 !important; padding: 0 !important; line-height: 0 !important; overflow: hidden !important; }
    [data-testid="stElementContainer"]:has(.mobile-control-marker) {
      height: 0 !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
    }

    /* Anchos compactos de los widgets de hora, día y mapa. */
    [data-testid="column"]:has(.compact-hora) [data-testid="stTextInput"],
    [data-testid="column"]:has(.compact-hora) [data-baseweb="input"],
    [data-testid="column"]:has(.compact-hora) [data-baseweb="base-input"],
    [data-testid="column"]:has(.compact-maps) [data-testid="stLinkButton"] {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      margin: 0 !important;
      transform: none !important;
    }
    [data-testid="column"]:has(.compact-dia) [data-testid="stSelectbox"],
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] {
      width: max-content !important;
      min-width: 96px !important;
      max-width: 100% !important;
      margin: 0 !important;
      transform: none !important;
    }
    [data-testid="column"]:has(.compact-hora) [data-baseweb="input"],
    [data-testid="column"]:has(.compact-hora) [data-baseweb="base-input"],
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] > div,
    [data-testid="column"]:has(.compact-maps) [data-testid="stLinkButton"] > a {
      min-height: 34px !important;
      height: 34px !important;
      max-height: 34px !important;
      border-radius: 8px !important;
    }
    [data-testid="column"]:has(.compact-hora) input {
      min-width: 0 !important;
      width: 100% !important;
      height: 32px !important;
      min-height: 32px !important;
      padding: 0 4px !important;
      font-size: 0.78rem !important;
      letter-spacing: 0 !important;
      text-align: center !important;
      font-variant-numeric: tabular-nums !important;
    }
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] span,
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] div {
      font-size: 0.72rem !important;
      line-height: 1.1 !important;
    }
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] > div {
      padding-left: 6px !important;
      padding-right: 18px !important;
      width: max-content !important;
      min-width: 96px !important;
      max-width: 100% !important;
    }
    [data-testid="column"]:has(.compact-dia) [data-baseweb="select"] input { caret-color: transparent !important; }
    [data-testid="column"]:has(.compact-maps) [data-testid="stLinkButton"] > a {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 40px !important;
      min-width: 40px !important;
      max-width: 40px !important;
      padding: 0 !important;
      font-size: 1rem !important;
      line-height: 1 !important;
      white-space: nowrap !important;
      overflow: visible !important;
      text-overflow: clip !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
    }

    /* Botón lápiz: suficiente área táctil y glifo siempre visible. */
    .edit-mini-btn button,
    [data-testid="column"]:has(.edit-mini-btn) .stButton > button {
      width: 34px !important;
      min-width: 34px !important;
      max-width: 34px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      font-size: 1.05rem !important;
      line-height: 1.1 !important;
      overflow: visible !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
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
    [class*="st-key-flight-links-"] [data-testid="column"],
    [class*="st-key-gmaps-actions-"] [data-testid="column"] {
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
      min-height: 38px !important;
      height: auto !important;
      padding: 6px 4px !important;
      white-space: normal !important;
      text-align: center !important;
      line-height: 1.15 !important;
      font-size: 0.75rem !important;
      overflow-wrap: anywhere !important;
    }

    /* Botones y campos: contenidos en su columna y con texto envolvente. */
    .stButton, .stFormSubmitButton, [data-testid="stLinkButton"],
    .stSelectbox, .stTextInput, .stNumberInput, .stDateInput,
    .stMultiSelect, .stSlider, [data-testid="stFileUploader"] {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
    }
    .stButton > button, .stFormSubmitButton > button,
    [data-testid="stLinkButton"] > a {
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

  /* Teléfonos estrechos: se conserva el mismo grid de 3 controles, más compacto. */
  @media (max-width: 380px) {
    .block-container { padding-left: 0.45rem !important; padding-right: 0.45rem !important; }
    .hero-title { font-size: 1.2rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.69rem !important; padding: 6px 2px !important; }
    [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: 25px minmax(0, 1fr) 38px !important;
      column-gap: 5px !important;
    }
    [class*="st-key-saved-heading-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: minmax(0, 1fr) 38px !important;
      column-gap: 5px !important;
    }
  }

  /* -----------------------------------------------------------------------
     ÚLTIMO AJUSTE DE CONTROLES PARA ITINERARIO Y GUARDADOS EN MÓVIL.
     Se usan tres pistas fijas y compactas, no max-content ni columnas flexibles:
     hora 80 px, día 94 px y mapa 42 px. Así no quedan botones gigantes,
     recortados o con ancho cero cuando Streamlit recalcula las columnas.
     ----------------------------------------------------------------------- */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 80px 94px 42px !important;
      grid-auto-flow: column !important;
      justify-content: start !important;
      align-items: center !important;
      column-gap: 6px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      flex: none !important;
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
    }

    /* Hora: ancho fijo real para que siempre quepa HH:MM. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) .stTextInput,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) .stTextInput {
      display: block !important;
      width: 80px !important;
      min-width: 80px !important;
      max-width: 80px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="base-input"] {
      width: 80px !important;
      min-width: 80px !important;
      max-width: 80px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      padding: 0 3px !important;
      border: 1.5px solid #94A3B8 !important;
      background: #FFFFFF !important;
      border-radius: 8px !important;
      overflow: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) input {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      height: 34px !important;
      min-height: 34px !important;
      padding: 0 2px !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
      font-family: 'Calibri', 'Carlito', Arial, sans-serif !important;
      font-size: 0.82rem !important;
      font-weight: 800 !important;
      letter-spacing: 0 !important;
      text-align: center !important;
      opacity: 1 !important;
    }

    /* Día: etiqueta corta y ancho ajustado al contenido, sin hueco sobrante. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) .stSelectbox,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) .stSelectbox {
      display: block !important;
      width: 94px !important;
      min-width: 94px !important;
      max-width: 94px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div {
      box-sizing: border-box !important;
      width: 94px !important;
      min-width: 94px !important;
      max-width: 94px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      background: #FFFFFF !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] span {
      color: #0F172A !important;
      font-size: 0.74rem !important;
      font-weight: 800 !important;
      white-space: nowrap !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] svg {
      width: 15px !important;
      min-width: 15px !important;
    }

    /* Mapa: botón táctil de 42 px con icono SVG, independiente de fuentes emoji. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] {
      display: block !important;
      width: 42px !important;
      min-width: 42px !important;
      max-width: 42px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 42px !important;
      min-width: 42px !important;
      max-width: 42px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      padding: 0 !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background-color: #FFFFFF !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%231D4ED8' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15'/%3E%3Cpath d='M15 6v15'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center center !important;
      background-size: 20px 20px !important;
      color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: visible !important;
      text-decoration: none !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a span {
      display: none !important;
    }

    /* Lápiz visible y de tamaño táctil suficiente; SVG no depende de emojis. */
    [class*="st-key-it-heading-row-"] [data-testid="column"]:last-child [data-testid="stButton"] > button,
    [class*="st-key-saved-heading-row-"] [data-testid="column"]:last-child [data-testid="stButton"] > button {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 36px !important;
      min-width: 36px !important;
      max-width: 36px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      margin: 0 !important;
      padding: 0 !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background-color: #F8FAFC !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center center !important;
      background-size: 19px 19px !important;
      color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: visible !important;
      opacity: 1 !important;
    }
    [class*="st-key-it-heading-row-"] [data-testid="column"]:last-child [data-testid="stButton"] > button span,
    [class*="st-key-saved-heading-row-"] [data-testid="column"]:last-child [data-testid="stButton"] > button span {
      display: none !important;
    }
  }

  @media (max-width: 320px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: 78px 92px 40px !important;
      column-gap: 5px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) .stTextInput,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) .stTextInput {
      width: 78px !important;
      min-width: 78px !important;
      max-width: 78px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-baseweb="base-input"] {
      width: 78px !important;
      min-width: 78px !important;
      max-width: 78px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) .stSelectbox,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) .stSelectbox,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-baseweb="select"] > div {
      width: 92px !important;
      min-width: 92px !important;
      max-width: 92px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stLinkButton"] > a {
      width: 40px !important;
      min-width: 40px !important;
      max-width: 40px !important;
    }
  }


  /* ===== FILA DEFINITIVA: EDITAR | MAPA | HORA | DÍA =====
     La información del lugar queda encima; estos cuatro controles van
     inmediatamente debajo y mantienen el mismo orden en Itinerario/Guardados. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 36px 38px 76px 88px !important;
      justify-content: start !important;
      align-items: center !important;
      gap: 5px !important;
      width: 100% !important;
      min-width: 0 !important;
      margin-top: 5px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      flex: none !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    /* Editar: 36 px, SVG integrado en CSS, sin depender de fuentes emoji. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) .stButton,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) .stButton,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] {
      width: 36px !important; min-width: 36px !important; max-width: 36px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button {
      box-sizing: border-box !important; display: flex !important;
      align-items: center !important; justify-content: center !important;
      width: 36px !important; min-width: 36px !important; max-width: 36px !important;
      height: 36px !important; min-height: 36px !important; max-height: 36px !important;
      padding: 0 !important; margin: 0 !important;
      border: 1.5px solid #94A3B8 !important; border-radius: 8px !important;
      background: #F8FAFC !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important; background-position: center !important; background-size: 19px 19px !important;
      color: transparent !important; font-size: 0 !important; line-height: 0 !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button span { display: none !important; }

    /* Mapa: zona de 38 px con icono de mapa dibujado en SVG. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      display: block !important; width: 38px !important; min-width: 38px !important; max-width: 38px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      box-sizing: border-box !important; display: flex !important;
      align-items: center !important; justify-content: center !important;
      width: 38px !important; min-width: 38px !important; max-width: 38px !important;
      height: 36px !important; min-height: 36px !important; max-height: 36px !important;
      padding: 0 !important; margin: 0 !important;
      border: 1.5px solid #94A3B8 !important; border-radius: 8px !important;
      background-color: #FFFFFF !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%231D4ED8' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15'/%3E%3Cpath d='M15 6v15'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important; background-position: center !important; background-size: 20px 20px !important;
      color: transparent !important; font-size: 0 !important; line-height: 0 !important; overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a span { display: none !important; }

    /* Hora: anchura fija suficiente para mostrar HH:MM completo. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) .stTextInput,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) .stTextInput { width: 76px !important; min-width: 76px !important; max-width: 76px !important; margin: 0 !important; }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      box-sizing: border-box !important; width: 76px !important; min-width: 76px !important; max-width: 76px !important;
      height: 36px !important; min-height: 36px !important; max-height: 36px !important;
      padding: 0 3px !important; border: 1.5px solid #94A3B8 !important; border-radius: 8px !important;
      background: #FFFFFF !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      box-sizing: border-box !important; display: block !important; width: 100% !important; min-width: 0 !important;
      height: 34px !important; min-height: 34px !important; padding: 0 2px !important;
      color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;
      font: 700 0.78rem/1 'Calibri', 'Carlito', Arial, sans-serif !important;
      text-align: center !important; letter-spacing: 0 !important; opacity: 1 !important;
    }

    /* Día: columna y desplegable del mismo ancho, sin relleno sobrante. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) .stSelectbox,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) .stSelectbox,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] { width: 88px !important; min-width: 88px !important; max-width: 88px !important; margin: 0 !important; }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      box-sizing: border-box !important; width: 88px !important; min-width: 88px !important; max-width: 88px !important;
      height: 36px !important; min-height: 36px !important; max-height: 36px !important;
      padding: 0 16px 0 6px !important; border: 1.5px solid #94A3B8 !important; border-radius: 8px !important;
      background: #FFFFFF !important; overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;
      font-size: 0.70rem !important; font-weight: 800 !important; white-space: nowrap !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg { width: 13px !important; min-width: 13px !important; }

    /* La fila informativa utiliza todo el ancho; la fila de cuatro controles va debajo. */
    [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important; grid-template-columns: 25px minmax(0, 1fr) !important;
      gap: 5px !important; align-items: start !important; width: 100% !important;
    }
    [class*="st-key-it-heading-row-"] [data-testid="column"] { min-width: 0 !important; width: 100% !important; padding: 0 !important; }
    [class*="st-key-saved-heading-row-"] { width: 100% !important; min-width: 0 !important; }

    /* No permitir que los estilos globales de Streamlit vuelvan a ensanchar los widgets. */
    [class*="st-key-it-controls-row-"] .stButton,
    [class*="st-key-saved-controls-row-"] .stButton,
    [class*="st-key-it-controls-row-"] [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="stLinkButton"] { width: auto !important; min-width: 0 !important; max-width: none !important; }
  }
  @media (max-width: 300px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: 34px 36px 72px 84px !important; gap: 3px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] { width: 72px !important; min-width: 72px !important; max-width: 72px !important; }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div { width: 84px !important; min-width: 84px !important; max-width: 84px !important; }
  }



  /* =====================================================================
     AJUSTE FINAL MÓVIL: LOS CUATRO CONTROLES OCUPAN TODO EL ANCHO DISPONIBLE.
     No se fijan píxeles globales: cada columna crece con el ancho del móvil.
     En escritorio no se modifica la distribución.
     ===================================================================== */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"],
    [class*="st-key-saved-controls-row-"] {
      display: block !important;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      margin: 6px 0 2px !important;
      padding: 0 !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
      grid-auto-flow: row !important;
      justify-content: stretch !important;
      align-items: center !important;
      column-gap: 7px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      flex: none !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] .stButton,
    [class*="st-key-saved-controls-row-"] [data-testid="column"] .stButton,
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stLinkButton"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stSelectbox"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }

    /* EDITAR: ocupa su cuarta parte de la fila; el lápiz se dibuja como SVG. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 40px !important;
      min-height: 40px !important;
      max-height: 40px !important;
      padding: 0 !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background-color: #F8FAFC !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: 21px 21px !important;
      color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button span {
      display: none !important;
    }

    /* MAPA: ocupa la misma anchura que los demás controles; icono centrado. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 40px !important;
      min-height: 40px !important;
      max-height: 40px !important;
      padding: 0 !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background-color: #FFFFFF !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='23' height='23' viewBox='0 0 24 24' fill='none' stroke='%231D4ED8' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15'/%3E%3Cpath d='M15 6v15'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: 22px 22px !important;
      color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a span {
      display: none !important;
    }

    /* HORA: el campo se estira con la pantalla y conserva HH:MM completo. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      box-sizing: border-box !important;
      display: flex !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 40px !important;
      min-height: 40px !important;
      max-height: 40px !important;
      padding: 0 3px !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background: #FFFFFF !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      box-sizing: border-box !important;
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      height: 38px !important;
      min-height: 38px !important;
      padding: 0 1px !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
      font-family: 'Calibri', 'Carlito', Arial, sans-serif !important;
      font-size: clamp(0.68rem, 2.8vw, 0.82rem) !important;
      font-weight: 800 !important;
      letter-spacing: 0 !important;
      text-align: center !important;
      opacity: 1 !important;
    }

    /* DÍA: desplegable ancho completo de su columna, sin anchura fija sobrante. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 40px !important;
      min-height: 40px !important;
      max-height: 40px !important;
      padding: 0 5px !important;
      border: 1.5px solid #94A3B8 !important;
      border-radius: 8px !important;
      background: #FFFFFF !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
      font-size: clamp(0.63rem, 2.7vw, 0.76rem) !important;
      font-weight: 800 !important;
      white-space: nowrap !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg {
      width: 12px !important;
      min-width: 12px !important;
      flex: 0 0 12px !important;
    }
  }



  /* Los widgets conservaban anchuras fijas de reglas antiguas. Este bloque,
     al estar al final, fuerza también sus contenedores internos a ocupar
     exactamente el ancho de cada una de las cuatro columnas. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) .stButton,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) .stButton,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) .stTextInput,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) .stTextInput,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) .stSelectbox,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) .stSelectbox,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      min-width: 0 !important;
      overflow: hidden !important;
      text-overflow: clip !important;
      font-size: clamp(0.60rem, 2.5vw, 0.74rem) !important;
    }
  }


  /* ===== AJUSTE FINO FINAL: ICONOS COMPACTOS Y DÍA SIEMPRE LEGIBLE =====
     Solo afecta a móvil; escritorio conserva sus tamaños y etiquetas normales. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"],
    [class*="st-key-saved-controls-row-"] {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      box-sizing: border-box !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
      grid-auto-flow: column !important;
      align-items: center !important;
      justify-content: stretch !important;
      gap: 4px !important;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      flex: none !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
      box-sizing: border-box !important;
    }

    /* Cuatro widgets compactos y alineados; no heredan mínimos de reglas antiguas. */
    [class*="st-key-it-controls-row-"] [data-testid="column"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"] > div,
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
    }

    /* EDITAR: icono lápiz, botón contenido en su columna. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background-color: #F8FAFC !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: 18px 18px !important;
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button * {
      visibility: hidden !important;
    }

    /* MAPA: icono solo, mismo tamaño y altura que Editar. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background-color: #FFFFFF !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='19' height='19' viewBox='0 0 24 24' fill='none' stroke='%231D4ED8' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15'/%3E%3Cpath d='M15 6v15'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: 18px 18px !important;
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a * {
      visibility: hidden !important;
    }

    /* HORA: HH:MM completo y centrado, con ancho natural de su cuarta parte. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      box-sizing: border-box !important;
      display: flex !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 2px !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      height: 32px !important;
      min-height: 32px !important;
      padding: 0 !important;
      text-align: center !important;
      font-size: clamp(0.60rem, 2.35vw, 0.70rem) !important;
      font-weight: 800 !important;
      letter-spacing: 0 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }

    /* DÍA: texto completo "Día 10" y flecha pequeña; no aplicar ellipsis. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] {
      box-sizing: border-box !important;
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      box-sizing: border-box !important;
      display: flex !important;
      align-items: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 3px !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
      overflow: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      display: inline-block !important;
      min-width: 0 !important;
      max-width: none !important;
      overflow: visible !important;
      text-overflow: clip !important;
      white-space: nowrap !important;
      font-size: clamp(0.57rem, 2.25vw, 0.68rem) !important;
      line-height: 1 !important;
      font-weight: 800 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg {
      width: 10px !important;
      min-width: 10px !important;
      max-width: 10px !important;
      flex: 0 0 10px !important;
    }

    /* Evitar que una regla global aumente de nuevo el ancho/alto de los cuatro widgets. */
    [class*="st-key-it-controls-row-"] button,
    [class*="st-key-saved-controls-row-"] button,
    [class*="st-key-it-controls-row-"] [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="stLinkButton"] > a {
      max-width: 100% !important;
      box-sizing: border-box !important;
    }

    /* Estadística superior: reservar más ancho a la tarjeta "Guardados". */
    .hero-container > div > div:last-child {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) minmax(80px, 1.12fr) minmax(0, 1fr) !important;
      gap: 6px !important;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
    }
    .hero-stat-box {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      padding: 6px 3px !important;
      overflow: visible !important;
    }
    .hero-stat-lbl {
      white-space: nowrap !important;
      word-break: normal !important;
      overflow-wrap: normal !important;
      font-size: clamp(0.52rem, 2.35vw, 0.62rem) !important;
      letter-spacing: 0.1px !important;
    }
  }

  @media (max-width: 320px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      gap: 3px !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      font-size: 0.57rem !important;
    }
    .hero-stat-lbl { font-size: 0.51rem !important; letter-spacing: 0 !important; }
  }


  /* Refinamiento final de tamaño: Editar y Mapa son iconos compactos centrados
     en sus columnas; Hora y Día conservan todo el ancho útil para leerse. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button {
      box-sizing: border-box !important;
      width: 36px !important;
      min-width: 36px !important;
      max-width: 36px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 auto !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      width: 36px !important;
      min-width: 36px !important;
      max-width: 36px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 auto !important;
    }
  }


  /* ===== CORRECCIÓN DEFINITIVA MÓVIL: ICONOS REALES + DÍA LEGIBLE ===== */
  .place-list-title {
    font-size: 0.94rem !important;
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
      font-size: 0.88rem !important;
      line-height: 1.18 !important;
      letter-spacing: 0 !important;
    }
    .place-list-address {
      font-size: 0.68rem !important;
      line-height: 1.25 !important;
      margin-top: 2px !important;
    }
    .place-note {
      font-size: 0.66rem !important;
      line-height: 1.25 !important;
      margin-top: 2px !important;
    }
    .badge-cat, .badge-indoor, .badge-outdoor {
      font-size: 0.63rem !important;
      line-height: 1.15 !important;
      padding: 1px 5px !important;
    }

    /* Los cuatro widgets tienen una cuadrícula fija mínima que cabe incluso
       en un móvil de 280 px: Editar, Mapa, Hora y Día. */
    [class*="st-key-it-controls-row-"],
    [class*="st-key-saved-controls-row-"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: minmax(34px, 0.72fr) minmax(34px, 0.72fr) minmax(74px, 1fr) minmax(100px, 1.38fr) !important;
      grid-auto-flow: column !important;
      align-items: center !important;
      justify-content: stretch !important;
      gap: 4px !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      flex: none !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
      overflow: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stElementContainer"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] .stButton,
    [class*="st-key-saved-controls-row-"] [data-testid="column"] .stButton,
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stLinkButton"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"] [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] [data-testid="stSelectbox"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
      margin: 0 !important;
      padding: 0 !important;
    }

    /* Editar y Mapa llevan ahora emoji como contenido nativo del widget.
       No se oculta ni se sustituye el texto mediante background-image. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      box-sizing: border-box !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background-image: none !important;
      background-color: #FFFFFF !important;
      color: #334155 !important;
      -webkit-text-fill-color: #334155 !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
      font-size: 1.05rem !important;
      line-height: 1 !important;
      font-weight: 400 !important;
      text-decoration: none !important;
      white-space: nowrap !important;
      overflow: visible !important;
      visibility: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button *,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a * {
      display: inline !important;
      visibility: visible !important;
      opacity: 1 !important;
      color: inherit !important;
      -webkit-text-fill-color: currentColor !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
      font-size: inherit !important;
      line-height: 1 !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button p,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button p,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a p,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a p {
      display: inline !important;
      margin: 0 !important;
      font-size: inherit !important;
      line-height: 1 !important;
    }

    /* Hora: conserva HH:MM y no se estrecha por los iconos. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      box-sizing: border-box !important;
      padding: 0 2px !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      width: 100% !important;
      min-width: 0 !important;
      height: 34px !important;
      box-sizing: border-box !important;
      padding: 0 1px !important;
      text-align: center !important;
      font-size: 0.72rem !important;
      font-weight: 800 !important;
      letter-spacing: 0 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
      font-variant-numeric: tabular-nums !important;
    }

    /* Día: se reserva un mínimo real de 100 px para que no se corte "Día 10". */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      display: flex !important;
      align-items: center !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      box-sizing: border-box !important;
      padding: 0 4px 0 6px !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
      overflow: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      white-space: nowrap !important;
      overflow: visible !important;
      text-overflow: clip !important;
      font-size: 0.68rem !important;
      line-height: 1 !important;
      font-weight: 800 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg {
      flex: 0 0 12px !important;
      width: 12px !important;
      min-width: 12px !important;
      max-width: 12px !important;
    }
  }

  @media (max-width: 320px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: minmax(34px, 0.72fr) minmax(34px, 0.72fr) minmax(72px, 1fr) minmax(98px, 1.38fr) !important;
      gap: 3px !important;
    }
    .place-list-title { font-size: 0.86rem !important; }
    .place-list-address, .place-note { font-size: 0.65rem !important; }
  }


  /* Medidas finales de móvil: los dos iconos ocupan solo su tamaño real,
     hora legible y selector de día suficientemente ancho para "Día 10". */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      grid-template-columns: 34px 34px 74px 102px !important;
      grid-auto-flow: column !important;
      justify-content: start !important;
      align-items: center !important;
      column-gap: 4px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      flex: none !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
    }
    /* Botones icono: exactamente 34 px, sin textos ni SVG de fondo ocultando
       el contenido real (✏️ y 🗺️ se renderizan como etiqueta de Streamlit). */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      width: 34px !important;
      min-width: 34px !important;
      max-width: 34px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-sizing: border-box !important;
      width: 34px !important;
      min-width: 34px !important;
      max-width: 34px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
      background-image: none !important;
      color: #334155 !important;
      -webkit-text-fill-color: #334155 !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
      font-size: 1rem !important;
      line-height: 1 !important;
      text-decoration: none !important;
      white-space: nowrap !important;
      overflow: visible !important;
      visibility: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button *,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a * {
      display: inline !important;
      visibility: visible !important;
      opacity: 1 !important;
      color: inherit !important;
      -webkit-text-fill-color: currentColor !important;
      font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
      font-size: inherit !important;
      line-height: 1 !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    /* Hora fija para que HH:MM no se corte en pantallas estrechas. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      width: 74px !important;
      min-width: 74px !important;
      max-width: 74px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      box-sizing: border-box !important;
      padding: 0 2px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      width: 100% !important;
      min-width: 0 !important;
      height: 34px !important;
      padding: 0 1px !important;
      font-size: 0.72rem !important;
      font-weight: 800 !important;
      text-align: center !important;
      letter-spacing: 0 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
    /* Desplegable con anchura mínima real de 102 px. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] {
      width: 102px !important;
      min-width: 102px !important;
      max-width: 102px !important;
      box-sizing: border-box !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      display: flex !important;
      align-items: center !important;
      width: 102px !important;
      min-width: 102px !important;
      max-width: 102px !important;
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      box-sizing: border-box !important;
      padding: 0 4px 0 6px !important;
      overflow: visible !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      white-space: nowrap !important;
      overflow: visible !important;
      text-overflow: clip !important;
      font-size: 0.69rem !important;
      font-weight: 800 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
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



  /* ===== ÚLTIMO AJUSTE MÓVIL: ICONOS SVG FIJOS + HORA LEGIBLE ===== */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 30px 30px 92px minmax(102px, 1fr) !important;
      grid-auto-flow: column !important;
      justify-content: stretch !important;
      align-items: center !important;
      column-gap: 3px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      flex: none !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
      overflow: visible !important;
    }

    /* EDITAR: la etiqueta accesible permanece en el HTML, visualmente se
       sustituye siempre por un lápiz SVG independiente de fuentes/emoji. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] {
      width: 30px !important;
      min-width: 30px !important;
      max-width: 30px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button {
      position: relative !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-sizing: border-box !important;
      width: 30px !important;
      min-width: 30px !important;
      max-width: 30px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      text-indent: -9999px !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button::before,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button::before {
      content: "" !important;
      display: block !important;
      flex: 0 0 17px !important;
      width: 17px !important;
      height: 17px !important;
      margin: 0 !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 4 4 4'/%3E%3Cpath d='M4 20l4-.9L19 8a2.1 2.1 0 0 0-3-3L5 16z'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: contain !important;
      text-indent: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button > *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button > * {
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }

    /* MAPA: enlace real a Google Maps, con icono dibujado por CSS. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] {
      width: 30px !important;
      min-width: 30px !important;
      max-width: 30px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      position: relative !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-sizing: border-box !important;
      width: 30px !important;
      min-width: 30px !important;
      max-width: 30px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      font-size: 0 !important;
      line-height: 0 !important;
      text-indent: -9999px !important;
      text-decoration: none !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a::before,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a::before {
      content: "" !important;
      display: block !important;
      flex: 0 0 18px !important;
      width: 18px !important;
      height: 18px !important;
      margin: 0 !important;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231D4ED8' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z'/%3E%3Cpath d='M9 3v15'/%3E%3Cpath d='M15 6v15'/%3E%3C/svg%3E") !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: contain !important;
      text-indent: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a > *,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a > * {
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }

    /* HORA: 84 px reales para que HH:MM nunca se comprima ni desaparezcan
       los minutos. El campo conserva tamaño de letra legible. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      display: flex !important;
      box-sizing: border-box !important;
      width: 92px !important;
      min-width: 92px !important;
      max-width: 92px !important;
      height: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      padding: 0 3px !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 7px !important;
      background: #FFFFFF !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      height: 32px !important;
      padding: 0 2px !important;
      text-align: center !important;
      font-size: 0.78rem !important;
      font-weight: 800 !important;
      letter-spacing: 0 !important;
      font-variant-numeric: tabular-nums !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
  }



  /* ===== AJUSTE FINAL DE LOS CONTROLES EN MÓVIL =====
     Los botones llevan símbolos Unicode reales (no iconos de fondo ni fuentes
     externas); el CSS solo controla sus dimensiones y la visibilidad. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: 40px 40px 86px 80px !important;
      grid-auto-flow: column !important;
      justify-content: start !important;
      align-items: center !important;
      column-gap: 3px !important;
      row-gap: 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"] {
      display: block !important;
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      flex: none !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
      overflow: visible !important;
    }

    /* Editar: icono lápiz real como etiqueta del botón. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) .stButton,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) .stButton {
      width: 40px !important;
      min-width: 40px !important;
      max-width: 40px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-sizing: border-box !important;
      width: 40px !important;
      min-width: 40px !important;
      max-width: 40px !important;
      height: 38px !important;
      min-height: 38px !important;
      max-height: 38px !important;
      padding: 0 !important;
      margin: 0 !important;
      border: 1px solid #94A3B8 !important;
      border-radius: 8px !important;
      background: #FFFFFF !important;
      color: #334155 !important;
      -webkit-text-fill-color: #334155 !important;
      font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
      font-size: 21px !important;
      line-height: 1 !important;
      letter-spacing: 0 !important;
      text-indent: 0 !important;
      text-decoration: none !important;
      white-space: nowrap !important;
      overflow: visible !important;
      visibility: visible !important;
      opacity: 1 !important;
    }

    /* Reset reglas antiguas que escondían el texto del botón o dibujaban
       SVG pseudo-elemento encima. El símbolo de la etiqueta queda visible. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button::before,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button::before,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a::before,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a::before {
      content: none !important;
      display: none !important;
      background-image: none !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) button span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) button span,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) a span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) a span {
      display: inline !important;
      position: static !important;
      width: auto !important;
      min-width: 0 !important;
      height: auto !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
      clip: auto !important;
      clip-path: none !important;
      white-space: nowrap !important;
      visibility: visible !important;
      opacity: 1 !important;
      color: #334155 !important;
      -webkit-text-fill-color: #334155 !important;
      font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
      font-size: 21px !important;
      line-height: 1 !important;
    }

    /* Hora: mantiene los cinco caracteres HH:MM legibles. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-testid="stTextInput"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="input"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) [data-baseweb="base-input"] {
      display: flex !important;
      box-sizing: border-box !important;
      width: 86px !important;
      min-width: 86px !important;
      max-width: 86px !important;
      height: 38px !important;
      min-height: 38px !important;
      max-height: 38px !important;
      padding: 0 3px !important;
      margin: 0 !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(3) input,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(3) input {
      box-sizing: border-box !important;
      width: 100% !important;
      min-width: 0 !important;
      height: 36px !important;
      padding: 0 2px !important;
      text-align: center !important;
      font-size: 0.78rem !important;
      font-weight: 800 !important;
      font-variant-numeric: tabular-nums !important;
      letter-spacing: 0 !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }

    /* Día: más compacto que antes, pero con espacio para "Día 10" y la flecha. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-testid="stSelectbox"],
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"],
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] {
      display: block !important;
      width: 80px !important;
      min-width: 80px !important;
      max-width: 80px !important;
      margin: 0 !important;
      box-sizing: border-box !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] > div {
      display: flex !important;
      align-items: center !important;
      box-sizing: border-box !important;
      width: 80px !important;
      min-width: 80px !important;
      max-width: 80px !important;
      height: 38px !important;
      min-height: 38px !important;
      max-height: 38px !important;
      padding: 0 3px 0 5px !important;
      overflow: hidden !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] span {
      display: inline !important;
      min-width: 0 !important;
      font-size: 0.68rem !important;
      line-height: 1 !important;
      font-weight: 800 !important;
      white-space: nowrap !important;
      color: #0F172A !important;
      -webkit-text-fill-color: #0F172A !important;
    }
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(4) [data-baseweb="select"] svg {
      flex: 0 0 11px !important;
      width: 11px !important;
      min-width: 11px !important;
      max-width: 11px !important;
    }
  }



  /* Corrección de renderizado: Streamlit envuelve el contenido del botón en
     un div. Se restablece ese contenedor para que no herede el recorte usado
     por las reglas antiguas de iconos CSS. */
  @media (max-width: 768px) {
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button > div,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button > div {
      position: static !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      inset: auto !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 0 !important;
      max-height: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
      clip: auto !important;
      clip-path: none !important;
      transform: none !important;
      white-space: nowrap !important;
      visibility: visible !important;
      opacity: 1 !important;
    }

    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button > div > span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button > div > span,
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a > span,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a > span {
      position: static !important;
      display: inline !important;
      inset: auto !important;
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
      clip: auto !important;
      clip-path: none !important;
      transform: none !important;
      white-space: nowrap !important;
      visibility: visible !important;
      opacity: 1 !important;
      color: #334155 !important;
      -webkit-text-fill-color: #334155 !important;
      font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
      font-size: 22px !important;
      line-height: 1 !important;
    }

    /* Desactiva las pseudo-imágenes SVG antiguas del enlace; el icono visible
       es el emoji que forma parte de la propia etiqueta accesible del enlace. */
    [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a::before,
    [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(2) [data-testid="stLinkButton"] > a::before {
      content: none !important;
      display: none !important;
      background: none !important;
      background-image: none !important;
    }
  }

</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. DEFINICIÓN DEL VIAJE NAVIDEÑO (26 DIC 2026 - 4 ENE 2027)
# =============================================================================
DIAS_VIAJE = {
    1:  {"fecha": "26 Dic", "dia": "Sábado"},
    2:  {"fecha": "27 Dic", "dia": "Domingo"},
    3:  {"fecha": "28 Dic", "dia": "Lunes"},
    4:  {"fecha": "29 Dic", "dia": "Martes"},
    5:  {"fecha": "30 Dic", "dia": "Miércoles"},
    6:  {"fecha": "31 Dic", "dia": "Jueves"},
    7:  {"fecha": "01 Ene", "dia": "Viernes"},
    8:  {"fecha": "02 Ene", "dia": "Sábado"},
    9:  {"fecha": "03 Ene", "dia": "Domingo"},
    10: {"fecha": "04 Ene", "dia": "Lunes"},
}

def etiqueta_dia(d: int) -> str:
    info = DIAS_VIAJE.get(d, {})
    return f"Día {d}: {info.get('fecha', '')} {info.get('dia', '')}".strip()

def etiqueta_dia_corta(d: int) -> str:
    info = DIAS_VIAJE.get(d, {})
    return f"Día {d} · {info.get('fecha', '')}".strip()


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
        if re.match(r"^\d{1,2}:\d{2}$", h):
            partes = h.split(":")
            return (0, int(partes[0]) * 60 + int(partes[1]), item.get("id", 0))
        return (1, 9999, item.get("id", 0))
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
    """Escribe JSON atómicamente y con temporal único por escritura/sesión."""
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
        # No ocultamos fallos de escritura: sin esto no habría sincronización real.
        try:
            st.error(f"No se pudieron guardar los datos compartidos ({os.path.basename(ruta)}): {exc}")
        except Exception:
            pass
        return False


def guardar_config_viaje(cfg):
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
    """Guarda el itinerario que comparten las sesiones de esta publicación."""
    return _guardar_json_atomico(ARCH_ITINERARIO, lugares)


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
            raw = r2.read().decode("utf-8", errors="ignore").lstrip(")]}'\n")
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
    except Exception as e:
        st.warning(f"Aviso de sincronización ({nombre_lista}): {e}")
    return lugares_encontrados


# =============================================================================
# 6B. HERRAMIENTAS PARA AÑADIR Y EDITAR LUGARES
# =============================================================================
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        try:
            req = urllib.request.Request(raw, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
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
            f"<b>✏️ Editando: {spot['nombre']}</b></div>",
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
                    st.error("Formato de hora inválido. Usa HH:MM (ej. 09:30) o déjalo vacío.")
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
                    st.toast(f"¡'{ed_nom}' actualizado!", icon="✅")
                    st.rerun()

            if eliminar_ed:
                nom_borrado = spot["nombre"]
                st.session_state.lugares.pop(idx_real)
                if st.session_state.lugar_activo_id == spot["id"]:
                    st.session_state.lugar_activo_id = None
                st.session_state.editando_spot_key = None
                guardar_itinerario_disco(st.session_state.lugares)
                st.toast(f"Sitio '{nom_borrado}' eliminado.", icon="🗑️")
                st.rerun()

            if cerrar_ed:
                st.session_state.editando_spot_key = None
                st.rerun()

def render_formulario_agregar_lugar(key_sufijo: str = "gen"):
    """Módulo desplegable para añadir sitios desde Google Maps o a mano."""
    with st.expander("➕ Añadir Nuevo Lugar (Google Maps o a Mano)", expanded=False):
        tab_gm, tab_man = st.tabs(["🌐 Google Maps", "✏️ A Mano"])
        dias_asig_opts = ["📌 Bandeja de Guardados"] + [etiqueta_dia(d) for d in range(1, 11)]

        with tab_gm:
            st.caption("Pega el enlace de Google Maps de un sitio o lista:")
            with st.form(f"form_add_gm_{key_sufijo}"):
                url_input = st.text_input("Enlace de Google Maps:", placeholder="https://maps.app.goo.gl/...", key=f"inp_gm_{key_sufijo}")
                cg1, cg2 = st.columns(2)
                with cg1:
                    dia_dest_gm = selectbox_sin_teclado("Asignar a:", dias_asig_opts, key=f"sel_dia_gm_{key_sufijo}")
                with cg2:
                    hora_gm = st.text_input("Hora (opcional, HH:MM):", placeholder="11:00", key=f"hora_gm_{key_sufijo}")
                nota_gm = st.text_input("Nota manual (opcional):", placeholder="Ej: Reserva a las 20:00, probar pastrami...", key=f"nota_gm_{key_sufijo}")

                val_dia_gm = 0 if "Bandeja" in dia_dest_gm else int(re.search(r"Día (\d+)", dia_dest_gm).group(1))

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
                    val_dia_m = 0 if "Bandeja" in dia_dest_m else int(re.search(r"Día (\d+)", dia_dest_m).group(1))
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
    @st.fragment(run_every="5s")
    def _sincronizador_automatico_dispositivos():
        _vigilar_cambios_de_otros_dispositivos()

    _sincronizador_automatico_dispositivos()


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
            "🌐 Todos los Sitios (Itinerario + Guardados + Hotel)",
            "📅 Solo Sitios en Itinerario (Días 1 a 10)",
            "🏨 Solo Hotel Base"
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

    g_hotel_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(h_nom + ' ' + h_dir)}"
    pop_hotel_html = f"""
    <div style="font-family: -apple-system, sans-serif; min-width: 200px; padding: 4px;">
      <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">🏨 TU HOTEL BASE</span>
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
          <div style="font-size: 14px; font-weight: 800; color: #0F172A; margin-bottom: 3px;">{obtener_emoji_categoria(cat_spot)} {nom_spot}</div>
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
        height=470,
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
            nota_sp = sp.get("nota", "")
            dia_sp = sp.get("dia", 0)
            hora_sp = sp.get("hora", "")

            hora_badge_html = f'<span class="badge-hora">🕒 {hora_sp}</span>' if hora_sp else ''
            st.markdown('<div class="place-sheet">', unsafe_allow_html=True)
            st.markdown(f"""
              <div style="display:flex; gap:5px; margin-bottom:5px; flex-wrap:wrap;">
                <span class="badge-dia">{etiqueta_dia(dia_sp) if dia_sp > 0 else "📌 En Guardados"}</span>
                {hora_badge_html}
                <span class="{'badge-indoor' if tipo_sp == 'Interior' else 'badge-outdoor'}">{'🌧️ Interior' if tipo_sp == 'Interior' else '☀️ Exterior'}</span>
                <span class="badge-cat">{cat_sp}</span>
              </div>
            """, unsafe_allow_html=True)

            # Título a la izquierda + botón pequeño ✏️ a la derecha del nombre + cerrar ✕
            c_sh_tit, c_sh_ed, c_sh_cl = st.columns([8.5, 0.75, 0.75])
            with c_sh_tit:
                st.markdown(
                    f"<div style='font-size:1.1rem; font-weight:900; color:#0F172A; line-height:1.25;'>{obtener_emoji_categoria(cat_sp)} {sp['nombre']}</div>",
                    unsafe_allow_html=True
                )
            with c_sh_ed:
                st.markdown('<div class="edit-mini-btn">', unsafe_allow_html=True)
                if st.button("✏", key=f"btn_ed_map_{sp['id']}", help="Editar sitio"):
                    ek = f"map_sheet_{sp['id']}"
                    st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c_sh_cl:
                st.markdown('<div class="edit-mini-btn">', unsafe_allow_html=True)
                if st.button("✕", key="close_place_sheet", help="Cerrar ficha"):
                    st.session_state.lugar_activo_id = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            if dir_sp:
                st.markdown(f'<div style="font-size:0.82rem; color:#334155; font-weight:600; margin-top:2px;">📍 {dir_sp}</div>', unsafe_allow_html=True)
            if nota_sp:
                st.markdown(bloque_nota_html(nota_sp), unsafe_allow_html=True)

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            c_act_hr, c_act_dia, c_act_maps = st.columns([1.0, 2.0, 1.0], gap="small")
            with c_act_hr:
                st.markdown('<span class="mobile-control-marker compact-hora"></span>', unsafe_allow_html=True)
                nueva_h_sh = st.text_input("Hora", value=hora_sp, placeholder="🕒 HH:MM", key=f"hora_sheet_{sp['id']}", label_visibility="collapsed")
                if nueva_h_sh.strip() != hora_sp:
                    hl = nueva_h_sh.strip()
                    if not hl or re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hl):
                        if hl and len(hl) == 4:
                            hl = "0" + hl
                        st.session_state.lugares[idx_p]["hora"] = hl
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()
            with c_act_dia:
                st.markdown('<span class="mobile-control-marker compact-dia"></span>', unsafe_allow_html=True)
                opciones_dias = ["Guardados"] + [etiqueta_dia_corta(d) for d in range(1, 11)]
                idx_dia_act = dia_sp if dia_sp > 0 else 0
                sel_n_dia = selectbox_sin_teclado("Día:", opciones_dias, index=idx_dia_act, key=f"sel_d_sheet_{sp['id']}", label_visibility="collapsed")
                n_dia_val = 0 if sel_n_dia == "Guardados" else int(re.search(r"Día (\d+)", sel_n_dia).group(1))
                if n_dia_val != dia_sp:
                    st.session_state.lugares[idx_p]["dia"] = n_dia_val
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.rerun()
            with c_act_maps:
                st.markdown('<span class="mobile-control-marker compact-maps"></span>', unsafe_allow_html=True)
                g_direct = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(sp['nombre'] + ' New York')}"
                st.link_button("🗺️", g_direct, use_container_width=True)

            render_editor_sitio_panel(sp, idx_p, "map_sheet")
            st.markdown('</div>', unsafe_allow_html=True)


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
            f'Progreso: <b>{len(total_visitados)}</b> / <b>{len(total_itinerario)}</b> paradas ({pct_progreso}%)'
            f'</div>',
            unsafe_allow_html=True
        )

    opciones_filtro_it = ["📋 Todos los Días (Días 1 a 10)"] + [etiqueta_dia(d) for d in range(1, 11)]
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
        <div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-left:6px solid #15803D; border-radius:13px; padding:8px 12px; margin-top:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <div style="font-weight:900; font-size:0.98rem; color:#0F172A;">
            {etiqueta_dia(d)}
          </div>
          <div style="font-weight:800; font-size:0.78rem; color:#0F172A; background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:20px; padding:2px 9px;">
            📍 {len(paradas_dia)} paradas ({len(visitados_dia)} hechas)
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

                # Información completa del lugar: nombre, categoría, entorno,
                # dirección y nota. Los cuatro controles van debajo, en una sola fila.
                with st.container(key=f"it-heading-row-{item['id']}"):
                    c_chk, c_info = st.columns([0.45, 9.55], gap="small")
                    with c_chk:
                        chk_val = st.checkbox("", value=is_visited, key=f"chk_it_{d}_{item['id']}")
                        if chk_val != is_visited and idx_real is not None:
                            st.session_state.lugares[idx_real]["visitado"] = chk_val
                            guardar_itinerario_disco(st.session_state.lugares)
                            st.rerun()

                    with c_info:
                        txt_c = "#334155" if is_visited else "#0F172A"
                        strike = "text-decoration: line-through; opacity: 0.78;" if is_visited else ""
                        tipo_badge = '<span class="badge-indoor">🌧️ Interior</span>' if item.get("tipo") == "Interior" else '<span class="badge-outdoor">☀️ Exterior</span>'
                        dir_html = f'<div class="place-list-address">📍 {html.escape(str(dir_i))}</div>' if dir_i else ''
                        nota_html = bloque_nota_html(nota_i)
                        st.markdown(f"""
                        <div style="{strike}; min-width:0; overflow-wrap:anywhere;">
                          <div class="place-list-title" style="color:{txt_c};">#{seq_idx} · {emoji_i} {item['nombre']}</div>
                          <div style="margin-top:4px; display:flex; flex-wrap:wrap; gap:4px;">
                            <span class="badge-cat">{cat_i}</span>
                            {tipo_badge}
                          </div>
                        </div>
                        {dir_html}
                        {nota_html}
                        """, unsafe_allow_html=True)

                # Los cuatro controles, siempre en el mismo orden: Editar | Mapa | Hora | Día.
                with st.container(key=f"it-controls-row-{item['id']}"):
                    c_edit, c_map, c_hr, c_day = st.columns([0.8, 0.9, 1.7, 1.9], gap="small")
                    with c_edit:
                        if st.button("✏️", key=f"btn_ed_it_{d}_{item['id']}", help="Editar sitio", use_container_width=True):
                            ek = f"it_{d}_{item['id']}"
                            st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                            st.rerun()
                    with c_map:
                        st.link_button("🗺️", gmaps_url, use_container_width=True, key=f"map_it_{item['id']}", help="Abrir en Google Maps")
                    with c_hr:
                        nueva_h = st.text_input(
                            "Hora",
                            value=hora_i,
                            placeholder="HH:MM",
                            key=f"hora_it_{d}_{item['id']}",
                            label_visibility="collapsed"
                        )
                        if nueva_h.strip() != hora_i and idx_real is not None:
                            hl = nueva_h.strip()
                            if not hl or re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hl):
                                if hl and len(hl) == 4:
                                    hl = "0" + hl
                                st.session_state.lugares[idx_real]["hora"] = hl
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.rerun()
                    with c_day:
                        dest_d = selectbox_sin_teclado(
                            "Día",
                            [f"Día {x}" for x in range(1, 11)] + ["Guardados"],
                            index=d - 1,
                            key=f"mvd_it_{d}_{item['id']}",
                            label_visibility="collapsed"
                        )
                        val_dest = 0 if dest_d == "Guardados" else int(re.search(r"Día (\d+)", dest_d).group(1))
                        if val_dest != d and idx_real is not None:
                            st.session_state.lugares[idx_real]["dia"] = val_dest
                            guardar_itinerario_disco(st.session_state.lugares)
                            st.rerun()

                if idx_real is not None:
                    render_editor_sitio_panel(item, idx_real, f"it_{d}")

                st.markdown('<div style="height:1px; background:#CBD5E1; margin:6px 0;"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS (CON BOTÓN DE HORA, DÍA, MAPS Y EDITAR PEQUEÑO)
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[2]:
    render_formulario_agregar_lugar("guardados")
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="ny-card-header">Lugares Guardados & Gestión de Sitios</div>', unsafe_allow_html=True)

    ver_todos_edicion = st.checkbox("Mostrar también los lugares ya asignados a días", value=False, key="chk_ver_todos_guardados")

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

    visibles_pool = [
        l for l in pool_guardados
        if (flt_cat_g == "Todas" or normalizar_categoria(l.get("categoria", "")) == flt_cat_g)
        and (not busq_g.strip() or busq_g.strip().lower() in l.get("nombre", "").lower())
    ]

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
            st.markdown(f"""
            <div class="place-list-title">{obtener_emoji_categoria(cat_p)} {p_spot['nombre']}</div>
            <div style="margin-top:4px; display:flex; flex-wrap:wrap; gap:4px;">
              <span class="badge-cat">{cat_p}</span>{tipo_p_html}
            </div>
            {dir_p_html}
            {nota_p_html}
            """, unsafe_allow_html=True)

        # Cuatro controles uniformes debajo del nombre y de toda su subinformación.
        with st.container(key=f"saved-controls-row-{p_spot['id']}"):
            c_edit, c_map, c_hr, c_day = st.columns([0.8, 0.9, 1.7, 1.9], gap="small")
            with c_edit:
                if st.button("✏️", key=f"btn_ed_pool_{p_spot['id']}", help="Editar sitio", use_container_width=True):
                    ek = f"pool_{p_spot['id']}"
                    st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                    st.rerun()
            with c_map:
                g_url_sp = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p_spot['nombre'] + ' New York')}"
                st.link_button("🗺️", g_url_sp, use_container_width=True, key=f"map_saved_{p_spot['id']}", help="Abrir en Google Maps")
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
                        st.session_state.lugares[idx_sp_real]["hora"] = hl
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()
            with c_day:
                opts_dia_pool = ["— Día —"] + [f"Día {d}" for d in range(1, 11)]
                idx_sel_pool = dia_p if 1 <= dia_p <= 10 else 0
                asig_dia = selectbox_sin_teclado(
                    "Día",
                    opts_dia_pool,
                    index=idx_sel_pool,
                    key=f"asig_dia_pool_{p_spot['id']}",
                    label_visibility="collapsed"
                )
                if asig_dia != "— Día —" and idx_sp_real is not None:
                    d_num = int(re.search(r"Día (\d+)", asig_dia).group(1))
                    if d_num != dia_p:
                        st.session_state.lugares[idx_sp_real]["dia"] = d_num
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()

        if idx_sp_real is not None:
            render_editor_sitio_panel(p_spot, idx_sp_real, "pool")

        st.markdown('<hr style="margin:6px 0; border-color:#E2E8F0;">', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: MODO LLUVIA & CLIMA EN TIEMPO REAL
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[5]:
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
        <div style="background:{color_card}; border: 1.5px solid {border_card}; border-radius:14px; padding:14px 16px;">
          <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">{etiqueta_dia(num_dia_c)} · {desc_dia}</div>
          <div style="font-size:0.84rem; color:#0F172A; margin-top:4px;">
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

            dir_ext_txt = f" · 📍 {spot_ext['direccion']}" if spot_ext.get("direccion") else ""
            nota_ext_html = bloque_nota_html(spot_ext.get("nota", ""))
            st.markdown(f"""
            <div style="background:#FFF5F5; border-left:4px solid #EF4444; border-radius:12px; padding:10px 14px; margin: 8px 0;">
              <div style="font-weight:700; color:#991B1B;">{obtener_emoji_categoria(normalizar_categoria(spot_ext.get('categoria','')))} {spot_ext['nombre']}</div>
              <div style="font-size:0.8rem; color:#7F1D1D;">Plan exterior · Día {num_dia_c}{dir_ext_txt}</div>
              {nota_ext_html}
            </div>
            """, unsafe_allow_html=True)

            c_sust1, c_sust2 = st.columns([3.5, 1.5])
            with c_sust1:
                opciones_cercanas = [f"{x['nombre']} (a {d:.1f} km) — {normalizar_categoria(x.get('categoria',''))}" for d, x in top_cercanos]
                sel_sust = selectbox_sin_teclado("Sustituto a cubierto:", opciones_cercanas, key=f"sel_sust_{spot_ext['id']}", label_visibility="collapsed")
            with c_sust2:
                if st.button("🔄 Cambiar", key=f"btn_swap_{spot_ext['id']}", use_container_width=True):
                    nom_sust = sel_sust.split(" (a ")[0].strip()
                    elegido = next(x for _, x in top_cercanos if x["nombre"] == nom_sust)
                    
                    idx_ext = next(i for i, x in enumerate(st.session_state.lugares) if x["id"] == spot_ext["id"])
                    idx_ind = next(i for i, x in enumerate(st.session_state.lugares) if x["id"] == elegido["id"])
                    
                    hora_heredada = st.session_state.lugares[idx_ext].get("hora", "")
                    st.session_state.lugares[idx_ext]["dia"] = 0
                    st.session_state.lugares[idx_ind]["dia"] = num_dia_c
                    if hora_heredada and not st.session_state.lugares[idx_ind].get("hora"):
                        st.session_state.lugares[idx_ind]["hora"] = hora_heredada
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.toast(f"¡'{elegido['nombre']}' ahora está en el Día {num_dia_c}!", icon="✨")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: DIVISAS EN TIEMPO REAL & CALCULADORA TAX Y PROPINAS NY
# ─────────────────────────────────────────────────────────────────────────────
with pestanas[3]:
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
        es_ropa_exenta = st.checkbox("👕 Prenda de ropa/calzado < $110 (Exenta de Sales Tax en NYC)")

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

        tax_rate = 0.0 if es_ropa_exenta else 0.08875
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
            <span style="color:#0F172A;">NYC Sales Tax ({'Exenta' if es_ropa_exenta else '8.875%'}):</span>
            <b>{'Exenta ($0.00)' if es_ropa_exenta else f'${tax_total:.2f}'}</b>
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

with pestanas[4]:
    c_vl1, c_vl2 = st.columns(2)

    with c_vl1:
        st.markdown('<div class="ny-card-header">✈️ Vuelos & Estado en Tiempo Real</div>', unsafe_allow_html=True)

        cods_ida = extraer_codigos_vuelo(v_ida.get("vuelo", ""))
        cods_vta = extraer_codigos_vuelo(v_vta.get("vuelo", ""))

        st.markdown("""
        <div class="ny-card" style="border-left: 5px solid #2563EB; margin-bottom:10px;">
          <div style="font-weight:800; font-size:0.92rem; color:#0F172A; margin-bottom:4px;">📡 Seguimiento en Vivo (FlightAware / Flightradar24)</div>
          <div style="font-size:0.82rem; color:#0F172A;">Pulsa en el código de vuelo para ver terminal, puerta y retrasos:</div>
        </div>
        """, unsafe_allow_html=True)

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
                    st.session_state.config_viaje["vuelo_ida"] = {"vuelo": ida_v, "fecha": ida_f, "hora": ida_h, "aeropuerto": ida_a}
                    st.session_state.config_viaje["vuelo_vuelta"] = {"vuelo": vta_v, "fecha": vta_f, "hora": vta_h, "aeropuerto": vta_a}
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.toast("Datos de vuelos actualizados.", icon="✈️")
                    st.rerun()

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
          <div style="font-weight:900; font-size:1.05rem; color:#0F172A; margin-bottom:4px;">🏨 {hotel_nom_act}</div>
          <div style="font-size:0.88rem; color:#0F172A; margin-bottom:4px;">📍 {hotel_dir_act}</div>
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
                    st.session_state.config_viaje["hotel"] = {"nombre": h_n, "direccion": h_d, "lat": h_lt, "lon": h_ln}
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.toast("Hotel base actualizado.", icon="🏨")
                    st.rerun()

    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    st.caption("Puedes cambiar el nombre o la URL compartida de cualquier lista aquí mismo. Después pulsa sincronizar para importar los lugares nuevos.")

    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")

    for idx_lst, lst_data in enumerate(listas_config):
        nombre_lista = str(lst_data.get("nombre", f"Lista {idx_lst + 1}"))
        url_lista = str(lst_data.get("url", ""))
        sufijo_edicion = hashlib.sha1(f"{nombre_lista}\0{url_lista}".encode("utf-8")).hexdigest()[:10]
        key_ed_nombre = f"gmaps_edit_nombre_{idx_lst}_{sufijo_edicion}"
        key_ed_url = f"gmaps_edit_url_{idx_lst}_{sufijo_edicion}"

        st.markdown(
            f"<div style='font-weight:800; color:#0F172A; overflow-wrap:anywhere;'>{idx_lst + 1}. {html.escape(nombre_lista)}</div>"
            f"<div class='gmaps-list-url' style='font-size:0.76rem; color:#475569; margin-top:2px; margin-bottom:6px;'>{html.escape(url_lista)}</div>",
            unsafe_allow_html=True
        )
        with st.container(key=f"gmaps-actions-{idx_lst}"):
            col_sync, col_edit = st.columns(2, gap="small")
            with col_sync:
                if st.button("🔄 Sincronizar", key=f"btn_sync_list_{idx_lst}", use_container_width=True):
                    if not url_lista.strip():
                        st.error("Edita la lista e introduce una URL antes de sincronizar.")
                    else:
                        with st.spinner(f"Descargando de {nombre_lista}..."):
                            descargados = extraer_lugares_lista_gmaps(url_lista, nombre_lista)
                            if descargados:
                                existentes = set(x.get("nombre", "").lower() for x in st.session_state.lugares)
                                agregados = 0
                                max_id_act = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
                                for d_item in descargados:
                                    nombre_importado = d_item.get("nombre", "").strip()
                                    if nombre_importado and nombre_importado.lower() not in existentes:
                                        max_id_act += 1
                                        st.session_state.lugares.append({
                                            "id": max_id_act,
                                            "nombre": nombre_importado,
                                            "lat": d_item["lat"],
                                            "lon": d_item["lon"],
                                            "dia": 0,
                                            "hora": "",
                                            "direccion": d_item.get("direccion", ""),
                                            "nota": "",
                                            "categoria": d_item["categoria"],
                                            "tipo": d_item["tipo"],
                                            "visitado": False
                                        })
                                        existentes.add(nombre_importado.lower())
                                        agregados += 1
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.success(f"✓ Sincronizado: {agregados} sitios nuevos añadidos a Guardados.")
                                st.rerun()
                            else:
                                st.warning("No se pudieron extraer lugares. Comprueba que el enlace sea una lista compartida de Google Maps y que tenga acceso público.")
            with col_edit:
                if st.button("✏️ Editar", key=f"btn_edit_list_{idx_lst}", use_container_width=True):
                    actual = st.session_state.get("lista_gmaps_editando")
                    st.session_state.lista_gmaps_editando = None if actual == idx_lst else idx_lst
                    for clave in (key_ed_nombre, key_ed_url):
                        st.session_state.pop(clave, None)
                    st.rerun()

        if st.session_state.get("lista_gmaps_editando") == idx_lst:
            st.markdown(f"**Editar lista: {html.escape(nombre_lista)}**")
            with st.form(f"form_editar_lista_gmaps_{idx_lst}"):
                nuevo_nombre_lista = st.text_input(
                    "Nombre de la lista:",
                    value=nombre_lista,
                    key=key_ed_nombre
                )
                nueva_url_lista = st.text_input(
                    "URL compartida de Google Maps:",
                    value=url_lista,
                    placeholder="https://maps.app.goo.gl/...",
                    key=key_ed_url
                )
                guardar_lista = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
                cancelar_lista = st.form_submit_button("Cancelar", use_container_width=True)

                if guardar_lista:
                    nombre_limpio = nuevo_nombre_lista.strip()
                    url_limpia = nueva_url_lista.strip()
                    partes_url = urllib.parse.urlparse(url_limpia)
                    if not nombre_limpio:
                        st.error("El nombre de la lista no puede estar vacío.")
                    elif partes_url.scheme not in ("http", "https") or not partes_url.netloc:
                        st.error("Introduce una URL completa que empiece por https:// o http://.")
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
                elif partes_url.scheme not in ("http", "https") or not partes_url.netloc:
                    st.error("Introduce una URL completa que empiece por https:// o http://.")
                else:
                    listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                    listas_actualizadas.append({"nombre": n_nombre_l.strip(), "url": url_nueva})
                    st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                    if guardar_config_viaje(st.session_state.config_viaje):
                        st.success("Lista guardada.")
                        st.rerun()
