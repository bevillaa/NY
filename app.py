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

  /* Botón de edición en pestañas (Itinerario, Guardados, Listas) */
  [class*="st-key-it-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
  [class*="st-key-saved-controls-row-"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button,
  [class*="st-key-btn_edit_list_"] > button {
    min-height: 37px !important;
    height: 37px !important;
    font-size: 1.05rem !important;
    padding: 0 0.65rem !important;
  }

  /* Botones generales limpios */
  .stButton > button, .stFormSubmitButton > button, [data-testid="stLinkButton"] > a {
    border-radius: 99px !important;
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
  }
  @media (max-width: 768px) {
    [class*="st-key-guardados-header-row"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) auto !important;
      align-items: center !important;
      gap: 6px !important;
    }
    [class*="st-key-guardados-header-row"] [data-testid="column"] {
      width: auto !important;
      min-width: 0 !important;
      flex: none !important;
    }
    [class*="st-key-btn_sync_guardados_wrap"] button {
      min-height: 30px !important;
      height: 30px !important;
      padding: 0 9px !important;
      font-size: 0.74rem !important;
      white-space: nowrap !important;
      width: auto !important;
    }
  }

  /* Botón pequeño de edición ✏️ junto al nombre */
  .edit-mini-btn {
    display: flex !important;
    justify-content: flex-end !important;
  }
  .edit-mini-btn button {
    min-height: 38px !important;
    height: 38px !important;
    width: 38px !important;
    min-width: 38px !important;
    max-width: 38px !important;
    padding: 0 !important;
    font-size: 1.18rem !important;
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
    border: 1.5px dashed #94A3B8 !important;
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
    .hero-stat-val { font-size: 1.25rem !important; }
    .hero-stat-lbl {
      font-size: 0.58rem !important;
      letter-spacing: 0.35px !important;
      overflow-wrap: anywhere !important;
    }

    .ny-card { padding: 10px 11px !important; border-radius: 13px !important; min-width: 0 !important; }
    .ny-card-header { font-size: 0.76rem !important; letter-spacing: 0.7px !important; line-height: 1.3 !important; }
    .place-sheet { padding: 10px 11px !important; border-radius: 13px !important; min-width: 0 !important; }
    .place-note { font-size: 0.76rem !important; line-height: 1.35 !important; overflow-wrap: anywhere !important; }

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

    [class*="st-key-it-heading-row-"] [data-testid="stHorizontalBlock"],
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

    .mobile-control-marker { display: block !important; width: 0 !important; height: 0 !important; margin: 0 !important; padding: 0 !important; line-height: 0 !important; overflow: hidden !important; }
    [data-testid="stElementContainer"]:has(.mobile-control-marker) {
      height: 0 !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
    }

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

    .gmaps-list-url { overflow-wrap: anywhere !important; word-break: break-all !important; }
  }

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
    [class*="st-key-it-controls-row-"] [data-testid="stHorizontalBlock"],
    [class*="st-key-saved-controls-row-"] [data-testid="stHorizontalBlock"] {
      display: grid !important;
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
  }

  /* Rediseño editorial aesthetic */
  :root {
    --ivory: #F7F5F0;
    --paper: #FFFEFC;
    --ink: #373B35;
    --muted: #85877D;
    --sage: #899681;
    --sage-dark: #68765F;
    --sage-pale: #EEF0E9;
    --line: #E7E4DC;
  }
  html, body, .stApp, [data-testid="stAppViewContainer"],
  [data-testid="stMain"], section.main {
    background: var(--ivory) !important;
    color: var(--ink) !important;
  }

  /* Navegación principal */
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
    cursor: pointer !important;
    white-space: nowrap !important;
  }
  .st-key-seccion_principal_activa [role="radiogroup"] label:has(input:checked) {
    background: #244C38 !important;
    border-color: #244C38 !important;
    color: #FFFFFF !important;
    box-shadow: 0 3px 9px rgba(36, 76, 56, .18) !important;
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
    "🍽️ Gastronomía", "🍪 Dulces", "🍸 Copas", "🎷 Ocio", "🛍️ Compras",
    "🎄 Christmas markets", "🏛️ Cultura", "🏙️ Miradores", "☀️ Spots", "📍 Otros", "🏨 Hotel"
]

MAPA_MIGRACION_CAT = {
    "🍕 Gastronomía": "🍽️ Gastronomía",
    "🍕 Gastronomía & Restaurantes": "🍽️ Gastronomía",
    "🍪 Cafeterías & Dulces": "🍪 Dulces",
    "🍸 Copas": "🍸 Copas",
    "🎷 Jazz, Música & Ocio": "🎷 Ocio",
    "🛍️ Compras & Outlets": "🛍️ Compras",
    "🏛️ Museos & Monumentos": "🏛️ Cultura",
    "🏙️ Miradores & Observatorios": "🏙️ Miradores",
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

    if orig and orig not in ("google maps", "lista", "sin lista"):
        if 'hotel' in orig or 'alojamiento' in orig:
            return "🏨 Hotel", "Interior"
        if any(k in orig for k in ['christmas', 'holiday', 'navidad', 'mercadillo', 'winter village']):
            tipo_nav = "Interior" if 'santaland' in texto_busqueda else "Exterior"
            return "🎄 Christmas markets", tipo_nav
        if any(k in orig for k in ['mirador', 'observator']):
            return "🏙️ Miradores", "Interior"
        if any(k in orig for k in ['ocio', 'jazz', 'música', 'musica', 'teatro', 'show', 'deporte']):
            return "🎷 Ocio", "Interior"
        if any(k in orig for k in ['copas', 'rooftop', 'bar', 'cocktail', 'pub']):
            return "🍸 Copas", "Interior"
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

    if ('hotel' in nom or 'inn' in nom or 'alojamiento' in nom or 'hostel' in nom) and any(k in texto_busqueda for k in ['riu', 'marriott', 'hilton', 'hyatt', 'sheraton', 'base', 'courtyard', 'westin', 'intercontinental']):
        return "🏨 Hotel", "Interior"
    if any(k in texto_busqueda for k in ['christmas market', 'holiday market', 'winter village', 'holiday shops', 'mercadillo navideño', 'mercado navideño', 'navidad', 'santa land', 'santaland', 'dyker heights', 'tree lighting', 'rockefeller tree']):
        tipo_nav = "Interior" if 'santaland' in texto_busqueda else "Exterior"
        return "🎄 Christmas markets", tipo_nav
    if any(k in texto_busqueda for k in ['summit', 'one vanderbilt', 'empire state', 'top of the rock', 'the edge', 'observatory', 'one world observatory', 'mirador', 'observation deck']):
        return "🏙️ Miradores", "Interior"
    if any(k in texto_busqueda for k in ['jazz', 'blue note', 'smalls', 'mezzrow', 'dizzy', "arthur's tavern", 'jazzcultural', 'village vanguard', 'broadway', 'radio city', 'comedy cellar', 'lincoln center', 'teatro', 'theatre', 'madison square garden', 'barclays center', 'cinema', 'cine', 'nba', 'knicks', 'nets', 'rangers', 'hockey', 'musical', 'concierto', 'concert', 'show', 'club', 'arcade']):
        return "🎷 Ocio", "Interior"
    if any(k in texto_busqueda for k in ['rooftop', 'westlight', 'harriet', 'magic hour', '230 fifth', 'bar 54', 'hudson vu', 'buvette', 'dante', 'speakeasy', 'cocktail', 'wine bar', 'tavern', 'brewery', 'pub', 'lounge', 'biergarten', 'taproom', 'saloon', 'copas']) or ('bar' in nom.split() and 'shake' not in nom and 'salad' not in nom and 'sushi' not in nom) or 'm social' in nom:
        return "🍸 Copas", "Interior"
    if any(k in texto_busqueda for k in ['bakery', 'cookie', 'cookies', 'levain', 'granny', 'caffè panna', 'caffe panna', 'krispy kreme', 'sweets', 'sweet', 'pastry', 'pâtisserie', 'donut', 'doughnut', 'helado', 'ice cream', 'gelato', 'louis vuitton nyc', 'café', 'cafe', 'coffee', 'starbucks', 'magnolia', 'chocolate', 'chocolat', 'cupcake', 'cheesecake', 'crepe', 'waffle', 'boba', 'matcha', 'tea room', 'dulce']):
        return "🍪 Dulces", "Interior"
    if any(k in texto_busqueda for k in ['outlet', 'outlets', 'marshalls', 't.j. maxx', 'tj maxx', 'target', 'macy', 'burlington', 'century 21', 'five below', 'goodwill', 'woodbury', 'jersey gardens', 'grand slam', 'shopping', 'store', 'zara', 'uniqlo', 'tanger', 'apple store', 'sephora', 'nordstrom', 'bloomingdale', 'saks', 'nike', 'adidas', 'lego', 'nintendo', 'fao schwarz', 'thrift', 'vintage', 'mall', 'tienda', 'boutique', 'market', 'bazar', 'souvenir']):
        if 'chelsea market' not in texto_busqueda and 'time out market' not in texto_busqueda and 'christmas market' not in texto_busqueda and 'holiday market' not in texto_busqueda:
            return "🛍️ Compras", "Interior"
    if any(k in texto_busqueda for k in ['pizza', 'pizzeria', 'burger', 'katz', 'dumpling', 'motek', 'piada', 'shake shack', 'chelsea market', 'time out market', 'deli', 'pastrami', 'tacos', 'taco', 'restaurant', 'restaurante', 'trader joe', 'eataly', 'food hall', 'bagel', 'ramen', 'sushi', 'diner', 'smokehouse', 'noodle', 'food', 'steakhouse', 'bistro', 'trattoria', 'osteria', 'grill', 'kitchen', 'bbq', 'barbecue', 'brunch', 'cantina', 'taqueria', 'hot dog', 'lobster', 'seafood']):
        return "🍽️ Gastronomía", "Interior"
    if any(k in texto_busqueda for k in ['museum', 'museo', 'the met', 'moma', 'guggenheim', 'whitney', 'natural history', 'morgan library', 'tenement', '9/11 memorial', 'oculus', 'grand central', 'library', 'biblioteca', 'atlas', 'one times square', 'times square', 'memorial', 'statue of liberty', 'estatua de la libertad', 'ellis island', 'trinity church', 'rockefeller center', 'st. patrick', 'cathedral', 'catedral', 'church', 'iglesia', 'united nations', 'onu', 'wall street', 'charging bull', 'federal hall', 'chrysler building', 'flatiron', 'empire state', 'gallery', 'galería']):
        tipo = "Exterior" if any(x in texto_busqueda for x in ['times square', 'atlas', 'statue', 'charging bull', 'wall street', 'memorial']) else "Interior"
        return "🏛️ Cultura", tipo
    if any(k in texto_busqueda for k in ['park', 'parque', 'central park', 'bryant park', 'washington square', 'bridge', 'puente', 'brooklyn bridge', 'manhattan bridge', 'high line', 'little island', 'fulton ferry', 'domino', 'pier 17', 'pier 57', 'pier 35', 'pier', 'muelle', 'pebble beach', 'tudor city', 'squibb', 'battery', 'waterfront', 'picnic', 'botanic', 'coney island', 'boardwalk', 'dumbo', 'soho', 'west village', 'greenwich', 'chinatown', 'little italy', 'hudson yards', 'vessel', 'roosevelt island', 'tram', 'ferry', 'spot', 'mirador callejero']):
        return "☀️ Spots", "Exterior"
    return "📍 Otros", "Exterior"

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
    try:
        token = str(st.secrets.get("GITHUB_TOKEN", "")).strip()
        repo = str(st.secrets.get("GITHUB_REPO", "")).strip()
        branch = str(st.secrets.get("GITHUB_BRANCH", "main")).strip() or "main"
        return token, repo, branch
    except Exception:
        return "", "", "main"

def _github_request(ruta_repo: str, metodo: str = "GET", datos=None):
    import base64
    token, repo, branch = _github_configuracion()
    if not token or not repo or "/" not in repo:
        return None
    ruta = urllib.parse.quote(ruta_repo, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    if metodo == "GET":
        url += "?ref=" + urllib.parse.quote(branch)
    payload = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos is not None else None

    req = urllib.request.Request(
        url, data=payload, method=metodo,
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
        raise RuntimeError(f"GitHub respondió {exc.code}") from exc

def _cargar_json_persistente(ruta: str):
    token, repo, _ = _github_configuracion()
    if token and repo:
        try:
            remoto = _github_request(ruta, "GET")
            if remoto is None:
                raise RuntimeError("No se pudo consultar GitHub.")
            datos_remotos, _sha = remoto
            if datos_remotos is not None:
                _guardar_json_atomico(ruta, datos_remotos)
                return datos_remotos
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    datos_locales = json.load(f)
                _guardar_json_persistente(ruta, datos_locales)
                return datos_locales
            return None
        except Exception as exc:
            raise RuntimeError(f"Error persistencia GitHub ({os.path.basename(ruta)}): {exc}") from exc

    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _guardar_json_persistente(ruta: str, datos):
    token, repo, branch = _github_configuracion()
    if not (token and repo):
        return _guardar_json_atomico(ruta, datos)

    import base64
    try:
        remoto = _github_request(ruta, "GET")
        datos_remotos, sha = remoto if remoto else (None, None)

        if (
            ruta == ARCH_ITINERARIO
            and isinstance(datos_remotos, list)
            and len(datos_remotos) > 0
            and isinstance(datos, list)
            and len(datos) == 0
        ):
            raise RuntimeError("Protección contra vaciado accidental activada.")

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
        if not respuesta.get("content", {}).get("sha"):
            raise RuntimeError("GitHub no confirmó escritura.")

        _guardar_json_atomico(ruta, datos)
        return True
    except Exception as exc:
        st.error(f"Error sincronizando con GitHub: {exc}")
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
        if temporal and os.path.exists(temporal):
            os.remove(temporal)
        return False

def guardar_config_viaje(cfg):
    return _guardar_json_persistente(ARCH_CONFIG, cfg)

def cargar_itinerario_disco():
    datos = _cargar_json_persistente(ARCH_ITINERARIO)
    if isinstance(datos, list):
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
    return []

def guardar_itinerario_disco(lugares):
    return _guardar_json_persistente(ARCH_ITINERARIO, lugares)

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

    antes_por_id = {str(x.get("id")): x for x in anteriores if isinstance(x, dict) and x.get("id") is not None}
    nuevos_por_id = {str(x.get("id")): x for x in nuevos if isinstance(x, dict) and x.get("id") is not None}
    ids_cambiados = set(antes_por_id) | set(nuevos_por_id)
    ids_cambiados = {
        pid for pid in ids_cambiados
        if _huella_datos(antes_por_id.get(pid)) != _huella_datos(nuevos_por_id.get(pid))
    }

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
    if not url_limpia:
        return []

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"),
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
                    elif cand.lower() not in titulo_detectado.lower():
                        titulo_detectado = f"{titulo_detectado} ({cand})"
                    break

        patrones = (
            r'href="(/maps/preview/entitylist/getlist\?[^\"]+)"',
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
            ruta = (
                html.unescape(ruta)
                .replace("\\u0026", "&")
                .replace("\\u003d", "=")
                .replace("\\/", "/")
                .replace("\\?", "?")
            )
            endpoint = ruta if ruta.startswith("http") else "https://www.google.com" + (ruta if ruta.startswith("/") else "/" + ruta)

            try:
                with opener.open(endpoint, timeout=12) as respuesta_lista:
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
                                elif cand_json.lower() not in titulo_detectado.lower():
                                    titulo_detectado = f"{titulo_detectado} ({cand_json})"
                                break
            except Exception:
                continue

            def _recorrer(nodo):
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
                        x.strip() for x in nodo
                        if isinstance(x, str) and len(x.strip()) > 1
                        and not x.strip().startswith(("http", "ChIJ", "/g/", "/m/", "0x"))
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

            _recorrer(data)

    except Exception:
        pass

    return encontrados

def ejecutar_sincronizacion_listas_gmaps():
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

    with st.spinner("Sincronizando todas tus listas de Google Maps y clasificando categorías..."):
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
                        if existente.get("categoria") != cat_final:
                            existente["categoria"] = cat_final
                            cambio_item = True
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

    if nuevos_ids:
        prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
        st.session_state.nuevos_lugares_ids = list(dict.fromkeys(nuevos_ids + prev_nuevos))

    if total_nuevos or total_actualizados:
        if guardar_itinerario_disco(st.session_state.lugares):
            st.toast(f"Sincronizados: {total_nuevos} nuevos, {total_actualizados} actualizados.", icon="🔄")
            st.session_state["_msg_sync_guardados"] = (
                "success",
                f"Sincronización terminada: {total_nuevos} lugares nuevos añadidos y "
                f"{total_actualizados} lugares actualizados."
            )
        else:
            st.session_state["_msg_sync_guardados"] = (
                "error",
                "No se pudieron guardar los lugares sincronizados."
            )
    else:
        st.toast("Listas al día. No hay sitios nuevos.", icon="✅")
        st.session_state["_msg_sync_guardados"] = (
            "info",
            f"Sincronización terminada. Sin cambios ({total_descargados} sitios leídos)."
        )
    if errores_sync:
        st.session_state["_errores_sync_guardados"] = errores_sync
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

    ids_numericos = []
    for existente in st.session_state.lugares:
        try:
            ids_numericos.append(int(existente.get("id", 0)))
        except (TypeError, ValueError, AttributeError):
            continue
    max_id = max(ids_numericos, default=0) + 1
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
        return False, "No se pudo guardar el lugar."
    prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
    st.session_state.nuevos_lugares_ids = list(dict.fromkeys([max_id] + prev_nuevos))
    return True, f"¡'{nom}' añadido con éxito como {nuevo['categoria']}!"

def importar_sitio_desde_gmaps(url_o_texto: str, dia_dest: int = 0, hora: str = "", nota: str = "") -> tuple:
    raw = url_o_texto.strip()
    if not raw:
        return False, "Introduce un enlace de Google Maps válido."

    if "maps" in raw.lower():
        lugares_lst = extraer_lugares_lista_gmaps(raw, "")
        if lugares_lst:
            existentes = {str(x.get("nombre", "")).strip().casefold() for x in st.session_state.lugares}
            nuevos = 0
            max_id = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
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
                    st.session_state.lugares = cargar_itinerario_disco()
                    return False, "No se pudieron guardar en GitHub los lugares importados."
                prev_nuevos = st.session_state.get("nuevos_lugares_ids", [])
                st.session_state.nuevos_lugares_ids = list(dict.fromkeys(ids_imp + prev_nuevos))
                return True, f"¡Se importaron {nuevos} lugares desde la lista de Google Maps!"

    nombre_extraido = ""
    lat_ext, lon_ext = None, None
    dir_ext = ""

    if raw.startswith("http://") or raw.startswith("https://"):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            req = urllib.request.Request(raw, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                url_final = r.geturl()
                html_code = r.read().decode('utf-8', errors='ignore')

                m_coords = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url_final)
                if m_coords:
                    lat_ext = float(m_coords.group(1))
                    lon_ext = float(m_coords.group(2))

                m_nom = re.search(r"/place/([^/@?]+)", url_final)
                if m_nom:
                    nombre_extraido = urllib.parse.unquote_plus(m_nom.group(1)).replace("+", " ")
                elif "<title>" in html_code:
                    m_tit = re.search(r"<title>([^<]+)</title>", html_code)
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
                ed_nota = st.text_input("Nota manual:", value=spot.get("nota", ""))
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
                idx_guardar = next((i for i, x in enumerate(st.session_state.lugares) if str(x.get("id")) == str(spot.get("id"))), None)
                if idx_guardar is not None:
                    hora_limpia = ed_hora.strip()
                    nuevo_dia = 0 if "Bandeja" in ed_dia_str else int(re.search(r"Día (\d+)", ed_dia_str).group(1))
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
                    guardar_itinerario_disco(st.session_state.lugares)
                    st.session_state.editando_spot_key = None
                    st.rerun()

            if eliminar_ed:
                idx_borrar = next((i for i, x in enumerate(st.session_state.lugares) if str(x.get("id")) == str(spot.get("id"))), None)
                if idx_borrar is not None:
                    st.session_state.lugares.pop(idx_borrar)
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
                    hora_gm = st.text_input("Hora (opcional):", placeholder="11:00", key=f"hora_gm_{key_sufijo}")
                nota_gm = st.text_input("Nota manual:", placeholder="Ej: Reserva...", key=f"nota_gm_{key_sufijo}")
                val_dia_gm = 0 if "Bandeja" in dia_dest_gm else int(re.search(r"Día (\d+)", dia_dest_gm).group(1))

                if st.form_submit_button("📥 Importar", use_container_width=True):
                    if url_input:
                        ok, msg = importar_sitio_desde_gmaps(url_input, val_dia_gm, hora_gm.strip(), nota_gm)
                        if ok:
                            st.toast(msg, icon="📍")
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_man:
            with st.form(f"form_add_man_{key_sufijo}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    nom_m = st.text_input("Nombre:", placeholder="Ej: Levain Bakery", key=f"nom_m_{key_sufijo}")
                    dir_m = st.text_input("Dirección:", placeholder="Ej: West Village", key=f"dir_m_{key_sufijo}")
                with c_m2:
                    cat_m = selectbox_sin_teclado("Categoría:", ["⚡ Detección Automática"] + CATEGORIAS_CANONICAS, key=f"cat_m_{key_sufijo}")
                    tipo_m = selectbox_sin_teclado("Tipo:", ["Interior (🌧️ A cubierto)", "Exterior (☀️ Al aire libre)"], key=f"tipo_m_{key_sufijo}")

                c_m3, c_m4 = st.columns(2)
                with c_m3:
                    dia_dest_m = selectbox_sin_teclado("Asignar a:", dias_asig_opts, key=f"sel_dia_m_{key_sufijo}")
                    val_dia_m = 0 if "Bandeja" in dia_dest_m else int(re.search(r"Día (\d+)", dia_dest_m).group(1))
                with c_m4:
                    hora_m = st.text_input("Hora:", placeholder="16:00", key=f"hora_m_{key_sufijo}")

                nota_m = st.text_input("Nota manual:", placeholder="Opcional...", key=f"nota_m_{key_sufijo}")

                if st.form_submit_button("💾 Guardar Lugar", use_container_width=True):
                    if nom_m:
                        t_val = "Interior" if "Interior" in tipo_m else "Exterior"
                        c_val = None if cat_m == "⚡ Detección Automática" else cat_m
                        ok, msg = agregar_sitio_a_lugares(nom_m, dir_m, None, None, c_val, t_val, val_dia_m, hora_m.strip(), nota_m)
                        if ok:
                            st.toast(msg, icon="✨")
                            st.rerun()
                        else:
                            st.error(msg)


# =============================================================================
# 7. INICIALIZACIÓN DE ESTADO & FRAGMENTO DE SINCRONIZACIÓN RÁPIDA
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
    """Vigila de forma optimizada la sincronización multi-dispositivo reduciendo el polling."""
    datos_compartidos = cargar_itinerario_disco()
    cambio_lugares = _huella_datos(datos_compartidos) != _huella_datos(st.session_state.get("lugares", []))
    cambio_config = _huella_datos(cargar_config_viaje()) != _huella_datos(st.session_state.get("config_viaje", {}))

    if cambio_lugares:
        sincronizar_lugares_desde_disco()
    if cambio_config:
        sincronizar_config_desde_disco()

    if cambio_lugares or cambio_config:
        st.rerun()

# 2. Acelerar la sincronización automática bajando el fragmento a 5s
if hasattr(st, "fragment"):
    @st.fragment(run_every="5s")
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
        <span>Madrid  ·  {ahora_madrid}</span>
        <span>New York  ·  {ahora_nueva_york}</span>
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
SECCIONES_PRINCIPALES = [
    "🗺️Mapa",
    "📍Ruta",
    "📎Guardados",
    "💸Divisas",
    "✈️Info",
    "🗒️Listas",
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
            "🌐 Todos los Sitios",
            "📅 Sitios en Itinerario (Días 1 a 10)",
            "🏨 Solo Hotel"
        ] + [etiqueta_dia(d) for d in range(1, 11)]
        sel_vista = selectbox_sin_teclado("Vista en el mapa:", opciones_vista, label_visibility="collapsed")
    sel_capa = "Google Maps Callejero"
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
    }
    tile_url, tile_attr = TILES_GMAPS[sel_capa]

    mapa = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13 if len(sitios_mapa) < 18 else 12,
        tiles=None,
        scrollWheelZoom=False
    )
    folium.TileLayer(tiles=tile_url, attr=tile_attr, max_zoom=20).add_to(mapa)

    pop_hotel_html = f"""
    <div style="font-family: sans-serif; min-width: 200px; padding: 4px;">
      <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">🏨 TU HOTEL BASE</span>
      <div style="font-size: 14px; font-weight: 700; color: #0F172A; margin: 6px 0 2px;">{h_nom}</div>
      <div style="font-size: 12px; color: #0F172A; margin-bottom: 8px;">📍 {h_dir}</div>
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

        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 220px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 4px;">
            <span style="font-size: 11px; font-weight: 800; color: #2563EB;">{dia_txt}</span>
            <span style="font-size: 10px; font-weight: 700; background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 6px;">{tipo_badge}</span>
          </div>
          <div style="font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 3px;">{obtener_emoji_categoria(cat_spot)} {nom_spot}</div>
          {f'<div style="font-size: 11px; color: #0F172A; margin-bottom: 3px;">📍 {dir_spot}</div>' if dir_spot else ''}
          {f'<div style="font-size:10.5px; color:#475569; font-style:italic; line-height:1.3; margin-bottom:6px;">📝 {linkificar_nota(nota_spot)}</div>' if nota_spot else ''}
          <div style="font-size: 11px; color: #0F172A; margin-bottom: 8px;"><b>Categoría:</b> {cat_spot}</div>
          <a href="{g_search}" target="_blank" style="display:block; text-align:center; background:#1A73E8; color:white; padding:6px 4px; border-radius:8px; font-size:11px; font-weight:700; text-decoration:none;">Maps →</a>
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

    st_folium(mapa, use_container_width=True, height=920, returned_objects=[])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ITINERARIO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "📍Ruta":
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
    filtro_it_sel = selectbox_sin_teclado("Ver itinerario:", opciones_filtro_it, key="filtro_itinerario_dia", label_visibility="collapsed")

    if "Todos los Días" in filtro_it_sel:
        dias_a_mostrar = list(range(1, 11))
    else:
        m_d_it = re.search(r"Día (\d+):", filtro_it_sel)
        dias_a_mostrar = [int(m_d_it.group(1))] if m_d_it else [1]

    for d in dias_a_mostrar:
        paradas_dia = ordenar_por_hora([l for l in st.session_state.lugares if l.get("dia", 0) == d])
        visitados_dia = [l for l in paradas_dia if l.get("visitado", False)]

        st.markdown(f'<div id="dia-{d}"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #E5E7EB; border-radius:13px; padding:8px 12px; margin-top:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <div style="font-weight:900; font-size:1.23rem; color:#0F172A;">{etiqueta_dia(d)}</div>
          <div style="font-weight:800; font-size:0.78rem; color:#0F172A; background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:20px; padding:2px 9px;">
            📍 {len(paradas_dia)} lugares ({len(visitados_dia)} visitados)
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

                with st.container(key=f"it-heading-row-{item['id']}"):
                    c_info, c_chk = st.columns([9.55, 0.45], gap="small")
                    with c_info:
                        txt_c = "#334155" if is_visited else "#0F172A"
                        strike = "text-decoration: line-through; opacity: 0.78;" if is_visited else ""
                        dir_html = f'<div class="place-list-address">📍 {html.escape(str(dir_i))}</div>' if dir_i else ''
                        nota_html = bloque_nota_html(nota_i)
                        st.markdown(f"""
                        <div style="{strike}; min-width:0; overflow-wrap:anywhere;">
                          <div class="place-list-title" style="color:{txt_c};">{emoji_i} {item['nombre']}</div>
                        </div>
                        {dir_html}
                        {nota_html}
                        """, unsafe_allow_html=True)

                    with c_chk:
                        chk_val = st.checkbox("", value=is_visited, key=f"chk_it_{d}_{item['id']}")
                        if chk_val != is_visited and idx_real is not None:
                            st.session_state.lugares[idx_real]["visitado"] = chk_val
                            guardar_itinerario_disco(st.session_state.lugares)
                            st.rerun()

                with st.container(key=f"it-controls-row-{item['id']}"):
                    c_edit, c_map, c_hr, c_day = st.columns([0.8, 0.9, 1.7, 1.9], gap="small")
                    with c_edit:
                        with st.container(key=f"it-edit-btn-{item['id']}"):
                            if st.button("✏️", key=f"btn_ed_it_{d}_{item['id']}", help="Editar sitio", use_container_width=True):
                                ek = f"it_{d}_{item['id']}"
                                st.session_state.editando_spot_key = None if st.session_state.editando_spot_key == ek else ek
                                st.rerun()
                    with c_map:
                        st.link_button("🗺️", gmaps_url, use_container_width=True, key=f"map_it_{item['id']}", help="Abrir en Google Maps")
                    with c_hr:
                        nueva_h = st.text_input("Hora", value=hora_i, placeholder="HH:MM", key=f"hora_it_{d}_{item['id']}", label_visibility="collapsed")
                        if nueva_h.strip() != hora_i and idx_real is not None:
                            hl = nueva_h.strip()
                            if not hl or re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hl):
                                st.session_state.lugares[idx_real]["hora"] = hl
                                guardar_itinerario_disco(st.session_state.lugares)
                    with c_day:
                        dest_d = selectbox_sin_teclado("Día", ["Guardados"] + [f"Día {x}" for x in range(1, 11)], index=d, key=f"mvd_it_{d}_{item['id']}", label_visibility="collapsed")
                        val_dest = 0 if dest_d == "Guardados" else int(re.search(r"Día (\d+)", dest_d).group(1))
                        if val_dest != d and idx_real is not None:
                            st.session_state.lugares[idx_real]["dia"] = val_dest
                            guardar_itinerario_disco(st.session_state.lugares)

                if idx_real is not None:
                    render_editor_sitio_panel(item, idx_real, f"it_{d}")

                st.markdown('<div style="height:1px; background:#CBD5E1; margin:6px 0;"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: BANDEJA DE GUARDADOS
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "📎Guardados":
    render_formulario_agregar_lugar("guardados")
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    with st.container(key="guardados-header-row"):
        col_gh1, col_gh2 = st.columns([3.4, 1.2], vertical_alignment="center")
        with col_gh1:
            st.markdown('<div class="ny-card-header" style="margin-bottom:0;">Lugares Guardados & Gestión de Sitios</div>', unsafe_allow_html=True)
        with col_gh2:
            with st.container(key="btn_sync_guardados_wrap"):
                if st.button("🔄 Sincronizar", key="btn_sync_guardados_mini", help="Sincronizar listas de Google Maps"):
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

    ver_todos_edicion = st.checkbox("Mostrar también los lugares ya asignados a días", value=False, key="chk_ver_todos_guardados")

    pool_guardados = list(st.session_state.lugares) if ver_todos_edicion else [l for l in st.session_state.lugares if l.get("dia", 0) == 0]
    cats_en_pool = sorted(set(normalizar_categoria(l.get("categoria", "📍 Otros")) for l in pool_guardados))

    col_flt1, col_flt2 = st.columns(2)
    with col_flt1:
        flt_cat_g = selectbox_sin_teclado("Categoría:", ["Todas"] + cats_en_pool, key="flt_pool_cat")
    with col_flt2:
        busq_g = st.text_input("Buscar:", placeholder="Nombre del sitio...", key="busq_pool_nom")

    nuevos_ids_set = set(st.session_state.get("nuevos_lugares_ids", []))
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

        with st.container(key=f"saved-heading-row-{p_spot['id']}"):
            st.markdown(f"""
            <div class="place-list-title">{obtener_emoji_categoria(cat_p)} {p_spot['nombre']}</div>
            <div style="margin-top:4px; display:flex; flex-wrap:wrap; gap:4px;">
              {'<span class="badge-dia">✨ Nuevo</span>' if p_spot.get("id") in nuevos_ids_set else ''}<span class="badge-cat">{cat_p}</span>{tipo_p_html}
            </div>
            {dir_p_html}
            {nota_p_html}
            """, unsafe_allow_html=True)

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
                nueva_h_pool = st.text_input("Hora", value=hora_p, placeholder="HH:MM", key=f"hora_pool_{p_spot['id']}", label_visibility="collapsed")
                if nueva_h_pool.strip() != hora_p and idx_sp_real is not None:
                    hl = nueva_h_pool.strip()
                    if not hl or re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", hl):
                        st.session_state.lugares[idx_sp_real]["hora"] = hl
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.rerun()
            with c_day:
                opts_dia_pool = ["- Día -"] + [f"Día {d}" for d in range(1, 11)]
                idx_sel_pool = dia_p if 1 <= dia_p <= 10 else 0
                asig_dia = selectbox_sin_teclado("Día", opts_dia_pool, index=idx_sel_pool, key=f"asig_dia_pool_{p_spot['id']}", label_visibility="collapsed")
                if asig_dia != "- Día -" and idx_sp_real is not None:
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
            desc_clima, _ = traducir_codigo_clima(w_code)

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

    with col_w_day:
        st.markdown("#### 🗓️ Pronóstico por Día")
        dia_sel_clima = selectbox_sin_teclado("Selecciona el día:", [etiqueta_dia(d) for d in range(1, 11)], key="sel_dia_clima")
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
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: DIVISAS EN TIEMPO REAL & CALCULADORA TAX Y PROPINAS NY
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "💸Divisas":
    st.markdown('<div class="ny-card-header">💵 Calculadora</div>', unsafe_allow_html=True)
    tasa_eur, fecha_tasa = obtener_tasa_usd_eur()

    col_fx, col_tax = st.columns([2.5, 3])
    with col_fx:
        st.markdown("#### 💱 Conversor de Divisas")
        modo_fx = st.radio("Convertir:", ["USD a EUR ($ ➔ €)", "EUR a USD (€ ➔ $)"], horizontal=True)
        if "USD a EUR" in modo_fx:
            val_usd = st.number_input("Cantidad en Dólares ($):", min_value=0.0, value=50.0, step=5.0)
            res_eur = val_usd * tasa_eur
            st.markdown(f"**Equivalente:** {res_eur:.2f} €")
        else:
            val_eur = st.number_input("Cantidad en Euros (€):", min_value=0.0, value=50.0, step=5.0)
            res_usd = val_eur / tasa_eur if tasa_eur > 0 else 0
            st.markdown(f"**Equivalente:** ${res_usd:.2f} USD")

    with col_tax:
        st.markdown("#### 🧾 Calculadora Tax & Tip")
        subtotal_bill = st.number_input("Subtotal ($ USD):", min_value=0.0, value=65.0, step=5.0)
        pct_propina = st.number_input("Propina (%):", min_value=0.0, max_value=100.0, value=18.0, step=1.0)
        tax_total = subtotal_bill * 0.08875
        tip_total = subtotal_bill * (pct_propina / 100.0)
        gran_total = subtotal_bill + tax_total + tip_total
        st.markdown(f"**Total final:** ${gran_total:.2f} USD (~ {gran_total * tasa_eur:.2f} €)")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: VUELOS, HOTEL & LISTAS
# ─────────────────────────────────────────────────────────────────────────────
def extraer_codigos_vuelo(texto_vuelo: str) -> list:
    return re.findall(r"\b([A-Z]{2}\d{2,4})\b", (texto_vuelo or "").upper())

if seccion_principal == "✈️Info":
    c_vl1, c_vl2 = st.columns(2)
    with c_vl1:
        st.markdown('<div class="ny-card-header">✈️ Vuelos</div>', unsafe_allow_html=True)
        st.markdown(f"**Ida:** {v_ida.get('vuelo')} ({v_ida.get('fecha')})")
        st.markdown(f"**Regreso:** {v_vta.get('vuelo')} ({v_vta.get('fecha')})")

    with c_vl2:
        st.markdown('<div class="ny-card-header">🏨 Hotel Base</div>', unsafe_allow_html=True)
        st.markdown(f"**{hotel.get('nombre')}**\n\n📍 {hotel.get('direccion')}")


# ─────────────────────────────────────────────────────────────────────────────
# NUEVA PESTAÑA: LISTAS DE GOOGLE MAPS
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗒️Listas":
    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")
    else:
        # 1. Sincronización inmediata al pulsar el botón
        if st.button("🔄 Sincronizar todas las listas", key="btn_sync_all_gmaps", use_container_width=True, type="primary"):
            ejecutar_sincronizacion_listas_gmaps()

    for idx_lst, lst_data in enumerate(listas_config):
        nombre_lista = str(lst_data.get("nombre", f"Lista {idx_lst + 1}"))
        url_lista = str(lst_data.get("url", ""))
        
        col_nombre, col_edit = st.columns([9.45, 0.55], gap="small", vertical_alignment="center")
        with col_nombre:
            st.markdown(f"<b>{idx_lst + 1}. {html.escape(nombre_lista)}</b><br><small>{html.escape(url_lista)}</small>", unsafe_allow_html=True)
        with col_edit:
            if st.button("✏️", key=f"btn_edit_list_{idx_lst}"):
                st.session_state.lista_gmaps_editando = idx_lst
                st.rerun()

    with st.expander("➕ Añadir nueva lista de Google Maps"):
        with st.form("form_nueva_lista_gmaps"):
            n_nombre_l = st.text_input("Nombre de la lista:")
            n_url_l = st.text_input("URL compartida de Google Maps:")
            if st.form_submit_button("Añadir Lista"):
                if n_nombre_l and n_url_l:
                    listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                    listas_actualizadas.append({"nombre": n_nombre_l.strip(), "url": n_url_l.strip()})
                    st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                    if guardar_config_viaje(st.session_state.config_viaje):
                        st.toast("Lista guardada. Ejecutando auto-sincronización...", icon="⚡")
                        # 1. Ejecución instantánea tras añadir una lista nueva
                        ejecutar_sincronizacion_listas_gmaps()
