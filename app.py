# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN PRO OPTIMIZADA (RECUENTO=1)
# =========================================================

import streamlit as st
import pandas as pd
import gspread
# LIBRERÍA MODERNA DE GOOGLE AUTH (Soluciona 'No access token in response')
from google.oauth2.service_account import Credentials
from datetime import date, datetime
import os
import base64
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Logístico Carcasas", page_icon="📦", layout="wide")

# 2. LOGO Y ESTILOS
def cargar_estilos():
    # Usamos st.html en lugar de st.markdown para evitar fallos de tipos en Python 3.14
    st.html("""
        <style>
        /* ── Paleta global verde → amarillo ── */
        :root {
            --verde-oscuro:  #1a7a4a;
            --verde-main:    #2d9e6b;
            --verde-medio:   #3dbb7e;
            --verde-claro:   #85dcaa;
            --amarillo-lima: #c8e06a;
            --amarillo:      #e8d44d;
            --naranja-suave: #f0c040;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a7a4a 0%, #2d9e6b 60%, #c8e06a 100%) !important;
        }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        [data-testid="stSidebar"] .stRadio label { color: #fff !important; }
        [data-testid="stSidebar"] button {
            background-color: #e8d44d !important;
            color: #1a7a4a !important;
            border: none !important;
            font-weight: 700 !important;
        }

        /* Título principal */
        h1 { color: #1a7a4a !important; }

        /* Tabs activos */
        .stTabs [data-baseweb="tab-highlight"] { background-color: #2d9e6b !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1a7a4a !important; font-weight: 700; }

        /* Métricas */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #f0faf4, #e8f5ee);
            border-left: 4px solid #2d9e6b;
            border-radius: 10px;
            padding: 12px 16px;
        }
        [data-testid="metric-container"] label { color: #1a7a4a !important; font-weight: 600; }
        [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #1a7a4a !important; font-size: 2rem !important; }

        /* Cards de apertura */
        .apertura-card {
            background: linear-gradient(135deg, #ffffff, #f0faf4);
            padding: 20px; border-radius: 12px;
            border-left: 6px solid #2d9e6b;
            box-shadow: 0 4px 12px rgba(45,158,107,0.15);
            margin-bottom: 15px; min-height: 140px;
        }
        .tienda-titulo { color: #1a7a4a; font-size: 1.1em; font-weight: 700; }
        .desc-tienda   { color: #636e72; font-size: 0.85em; }
        .fecha-est     { color: #e8a020; font-weight: bold; font-size: 0.9em; margin-top: 10px; }

        /* Sección títulos */
        .titulo-seccion {
            color: #1a7a4a; font-weight: bold; font-size: 1.5rem;
            margin-top: 25px; margin-bottom: 15px;
            border-bottom: 3px solid #2d9e6b; padding-bottom: 8px;
        }

        /* Dataframes */
        .stDataFrame { font-size: 12px; }
        .stDataFrame thead tr th {
            background-color: #2d9e6b !important;
            color: white !important;
        }

        /* Botones generales */
        .stButton > button {
            background: linear-gradient(135deg, #2d9e6b, #3dbb7e) !important;
            color: white !important; border: none !important;
            border-radius: 8px !important; font-weight: 600 !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #1a7a4a, #2d9e6b) !important;
        }

        /* Divider */
        hr { border-color: #c8e06a !important; }

        /* ── Overlay presentación tipo PPT ── */
        #ppt-overlay {
            display: none;
            position: fixed; inset: 0; z-index: 99999;
            background: #0d1f16;
            flex-direction: column;
            align-items: center; justify-content: center;
            padding: 32px 48px; box-sizing: border-box;
        }
        #ppt-overlay.activo { display: flex; }
        #ppt-header {
            width: 100%; display: flex;
            align-items: center; justify-content: space-between;
            margin-bottom: 18px;
        }
        #ppt-header img { height: 56px; object-fit: contain; }
        #ppt-titulo {
            color: #c8e06a; font-size: 1.8rem; font-weight: 700;
            text-align: center; flex: 1; padding: 0 24px;
            font-family: Arial, sans-serif;
        }
        #ppt-body { width: 100%; flex: 1; min-height: 0; }
        #ppt-body iframe {
            width: 100%; height: 100%; border: none;
            border-radius: 12px; background: #0d1f16;
        }
        #ppt-cerrar {
            position: absolute; top: 16px; right: 24px;
            background: transparent; border: 2px solid #c8e06a;
            color: #c8e06a; border-radius: 8px;
            padding: 6px 16px; font-size: 14px; font-weight: 700;
            cursor: pointer; z-index: 100000;
        }
        #ppt-cerrar:hover { background: #c8e06a; color: #0d1f16; }

        /* Logo CF Supply — fijo esquina superior derecha, encima del header de Streamlit */
        .logo-cf-fixed {
            position: fixed;
            top: 10px;
            right: 20px;
            z-index: 99999;
            background: transparent;
        }
        /* Empujar el header de streamlit para que no tape el logo */
        header[data-testid="stHeader"] {
            background: rgba(255,255,255,0.95) !important;
        }
        </style>
        """)


def mostrar_logo_izquierdo():
    """Logo CARCASAS en la posición normal (izquierda, flujo normal)."""
    if os.path.exists("CARCASAS.png"):
        st.image("CARCASAS.png", width=250)


def mostrar_logo_cf_derecha():
    """Logo CARGOFLEX alineado a la derecha — inline, no flotante."""
    pass  # Se maneja en mostrar_cabecera()


cargar_estilos()

# ── Cabecera con logos alineados ──────────────────────────────────────────
def _b64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

_b64_carc = _b64_img("CARCASAS.png")
_b64_cf   = _b64_img("CARGOFLEX.png")

_img_carc = f'<img src="data:image/png;base64,{_b64_carc}" style="height:70px;object-fit:contain;">' if _b64_carc else ""
_img_cf   = f'<img src="data:image/png;base64,{_b64_cf}"   style="height:70px;object-fit:contain;">' if _b64_cf   else ""

st.markdown(f'''
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:10px 0 18px;border-bottom:3px solid #c8e06a;margin-bottom:18px;">
  <div>{_img_carc}</div>
  <div>{_img_cf}</div>
</div>''', unsafe_allow_html=True)

# 3. CONEXIÓN Y CARGA
@st.cache_resource
def conectar_google():
    try:
        # Definimos los alcances (scopes) oficiales
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # USAMOS LA LIBRERÍA MODERNA DE GOOGLE AUTH
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}"); return None

client = conectar_google()

# ── ID Sheet Historial Carcasa ─────────────────────────────────────────────
SHEET_ID_HIST_CARCASA = "1x0jVDMYk9htwttNcpXlXeaQcR0ELoBYeF4iP2qYcs1s"

@st.cache_data(ttl=300)
def cargar_historial_carcasa():
    import re, pandas as pd
    try:
        sh = client.open_by_key(SHEET_ID_HIST_CARCASA)
        frames = []
        for ws in sh.worksheets():
            if re.match(r"HIST_\d{4}_\d{2}", ws.title):
                data = ws.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    df["_sheet"] = ws.title
                    frames.append(df)
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        df.columns = [c.strip() for c in df.columns]
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
        if "Stock WMS" in df.columns:
            df["Stock WMS"] = pd.to_numeric(df["Stock WMS"], errors="coerce").fillna(0)
        if "Contado" in df.columns:
            df["Contado"] = pd.to_numeric(df["Contado"], errors="coerce")
        if "Diferencia" in df.columns:
            df["Diferencia"] = pd.to_numeric(df["Diferencia"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error cargando historial Carcasa: {type(e).__name__}: {str(e)}")
        return pd.DataFrame()

def abrir_archivo_dinamico(nombre_o_id):
    if len(nombre_o_id) > 25:
        return client.open_by_key(nombre_o_id)
    return client.open(nombre_o_id)

@st.cache_data(ttl=600)
def cargar_datos_completos():
    def fetch(nombre_o_id, hoja=None):
        try:
            sh = abrir_archivo_dinamico(nombre_o_id)
            wks = sh.worksheet(hoja) if hoja else sh.sheet1
            data = wks.get_all_records()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df.astype(str)
        except: return pd.DataFrame()

    df_import_raw = fetch("Consolidado - Carcasas")
    if not df_import_raw.empty:
        col_rec = next((c for c in df_import_raw.columns if c.upper() == "RECUENTO"), None)
        if col_rec:
            df_import_filtered = df_import_raw[df_import_raw[col_rec].isin(["1", "1.0"])].copy()
        else:
            df_import_filtered = df_import_raw
    else:
        df_import_filtered = df_import_raw
    return df_import_filtered, fetch("RECEPCION_IMPORTACIONES", "MOVIMIENTOS"), fetch("TIENDAS CARCASAS")


# =========================================================
# MÓDULO: DASH DESPACHOS
# =========================================================

ORDEN_MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
               "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

COLORES_TIENDAS = [
    "#1a7a4a", "#2d9e6b", "#3dbb7e", "#5dcf96", "#85dcaa",
    "#b5e878", "#cef250", "#e8d44d", "#f0c040", "#f5a623",
    "#f7c948", "#a8d85a", "#72c472", "#4db88c", "#2eaa82",
    "#6bcf85", "#d4e84a", "#f2d740", "#e8b830", "#c8e06a",
]

GREEN_MAIN  = "#2d9e6b"
GREEN_DARK  = "#1a7a4a"
GREEN_LIGHT = "#85dcaa"


@st.cache_data(ttl=600)
def cargar_despachos():
    try:
        sh = client.open("CONSOLIDADO_DESPACHOS")
        wks = sh.sheet1
        all_values = wks.get_all_values()
        if not all_values or len(all_values) < 2:
            return pd.DataFrame()

        raw_headers = all_values[0]
        rows = all_values[1:]
        headers = []
        seen = {}
        for i, h in enumerate(raw_headers):
            h_clean = str(h).strip()
            if h_clean == "":
                h_clean = f"_col_{i}"
            key = h_clean.lower()
            if key in seen:
                seen[key] += 1
                h_clean = f"{h_clean}_{seen[key]}"
            else:
                seen[key] = 0
            headers.append(h_clean)

        df = pd.DataFrame(rows, columns=headers)
        df.columns = [c.strip().lower() for c in df.columns]
        df = df[[c for c in df.columns if not c.startswith("_col_")]]
        df = df[df.apply(lambda r: r.astype(str).str.strip().ne("").any(), axis=1)].reset_index(drop=True)

        df["unidades"] = pd.to_numeric(df.get("unidades", 0), errors="coerce").fillna(0).astype(int)

        col_mes = next((c for c in df.columns if "mes" in c), None)
        df["mes"] = df[col_mes].astype(str).str.strip().str.upper() if col_mes else "SIN MES"

        col_sku = next((c for c in df.columns if "codigo_color_sin_punto" in c), None)
        df["sku"] = df[col_sku].astype(str).str.strip() if col_sku else df.get("codigo_color", pd.Series([""] * len(df))).astype(str).str.strip()

        col_desc = next((c for c in df.columns if "descripci" in c.lower()), None)
        df["descripcion"] = df[col_desc].astype(str).str.strip() if col_desc else ""

        df["codigo_departamento"] = df.get("codigo_departamento", pd.Series([""] * len(df))).astype(str).str.strip()

        if "nombre_departamento" in df.columns:
            df["nombre_tienda"] = df["nombre_departamento"].astype(str).str.replace(r"^\d+\.-\s*", "", regex=True).str.strip()
            df["nombre_departamento_full"] = df["nombre_departamento"].astype(str).str.strip()
        else:
            df["nombre_tienda"] = df["codigo_departamento"]
            df["nombre_departamento_full"] = df["codigo_departamento"]

        # Filtrar solo tiendas aperturadas
        try:
            sh_t   = client.open("TIENDAS CARCASAS")
            data_t = sh_t.sheet1.get_all_records()
            if data_t:
                df_t = pd.DataFrame(data_t)
                df_t.columns = [str(c).strip().upper() for c in df_t.columns]
                aperturadas = set(
                    df_t[df_t["ESTADO"].astype(str).str.strip().str.upper() == "APERTURADAS"]
                    ["TIENDA"].astype(str).str.strip().tolist()
                )
                if aperturadas:
                    df = df[df["codigo_departamento"].isin(aperturadas)].reset_index(drop=True)
        except Exception:
            pass

        return df
    except Exception as e:
        st.error(f"❌ Error cargando CONSOLIDADO_DESPACHOS: {e}")
        return pd.DataFrame()


def _ordenar_meses(df, col="mes"):
    df = df.copy()
    df["_orden_mes"] = df[col].map({m: i for i, m in enumerate(ORDEN_MESES)}).fillna(99)
    return df.sort_values("_orden_mes").drop(columns=["_orden_mes"])


def _render_metricas_despachos(df):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total unidades", f"{int(df['unidades'].sum()):,}")
    c2.metric("🎨 SKUs únicos", f"{df['sku'].nunique():,}")
    c3.metric("🏪 Tiendas activas", df["codigo_departamento"].nunique())
    c4.metric("📅 Meses con data", df["mes"].nunique())


# ── Overlay PPT: contenedor fijo con logos + título + gráfico ──────────────
def _logos_b64():
    """Devuelve (b64_carcasas, b64_cargoflex) como data URIs o '' si no existen."""
    def _b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode()
        return ""
    return _b64("CARCASAS.png"), _b64("CARGOFLEX.png")


def mostrar_seccion_ppt(titulo_seccion, slides):
    import plotly.io as pio
    import streamlit.components.v1 as components
    import json as _json, re as _re, tempfile, os

    slides = [(t, f) for t, f in slides if f is not None]
    if not slides:
        return

    key_show = "ppt_" + _re.sub(r"[^a-z0-9]", "_", titulo_seccion.lower())[:25]
    key_html = key_show + "_html"

    # Construir HTML solo cuando se abre (no en cada rerun)
    if key_show not in st.session_state:
        st.session_state[key_show] = False

    # Botón toggle
    label = "⬇️ Cerrar" if st.session_state[key_show] else "🖥️ Ver presentación"
    if st.button(f"{label}: {titulo_seccion}", key=f"btn_{key_show}"):
        st.session_state[key_show] = not st.session_state[key_show]
        if st.session_state[key_show]:
            # Construir HTML al abrir
            logo_izq, logo_der = _logos_b64()
            sid = _re.sub(r"[^a-z0-9]", "_", titulo_seccion.lower())[:15]
            logo_izq_tag = f'<img src="{logo_izq}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_izq else ""
            logo_der_tag = f'<img src="{logo_der}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_der else ""

            parts = []
            for t, f in slides:
                if isinstance(f, str):
                    parts.append('{"titulo":' + _json.dumps(t) + ',"tipo":"html","content":' + _json.dumps(f) + '}')
                else:
                    parts.append('{"titulo":' + _json.dumps(t) + ',"tipo":"plotly","fig":' + pio.to_json(f) + '}')
            slides_js = "[" + ",".join(parts) + "]"

            # Leer template y reemplazar
            html = _ppt_template()
            html = (html
                .replace("__SLIDES_JS__", slides_js)
                .replace("__LOGO_IZQ__", logo_izq_tag)
                .replace("__LOGO_DER__", logo_der_tag)
            )
            st.session_state[key_html] = html
        st.rerun()

    if st.session_state.get(key_show) and key_html in st.session_state:
        components.html(st.session_state[key_html], height=780, scrolling=False)


def _ppt_template():
    """Retorna el HTML template del PPT como string puro (sin f-string)."""
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  html, body { width:100%; height:100%; background:#f0faf4; font-family:Arial,sans-serif; overflow:hidden; }
  #wrap { width:100%; height:100vh; display:flex; flex-direction:column; padding:6px 12px 6px; gap:5px; }
  #hdr { display:none; }
  .logo-w { width:190px; display:flex; align-items:center; }
  .logo-w.r { justify-content:flex-end; }
  #titulo { color:#1a7a4a; font-size:1.5rem; font-weight:800; text-align:center; flex:1; padding:0 10px; }
  #pw { width:100%; height:4px; background:#c8e06a; border-radius:3px; flex-shrink:0; }
  #pb { height:4px; background:#1a7a4a; border-radius:3px; width:0%; }
  #body { flex:1; min-height:0; border:2px solid #2d9e6b; border-radius:12px; background:#fff; overflow:hidden; display:flex; align-items:stretch; }
  #plt-div { width:100%; height:100%; }
  #html-div { width:100%; height:100%; overflow:hidden; display:none; }
  #footer { display:flex; align-items:center; justify-content:space-between; background:#fff; border-radius:10px; border:1.5px solid #c8e06a; padding:4px 14px; flex-shrink:0; }
  #dots { display:flex; gap:8px; align-items:center; }
  #dots span { width:10px; height:10px; border-radius:50%; display:inline-block; cursor:pointer; background:#c8e06a; border:2px solid #2d9e6b; transition:all 0.25s; }
  #dots span.on { background:#1a7a4a; transform:scale(1.35); }
  #ctr { color:#636e72; font-size:12px; font-weight:700; }
  #nav { display:flex; gap:8px; }
  #nav button { background:#fff; border:2px solid #2d9e6b; color:#2d9e6b; border-radius:6px; padding:4px 14px; font-size:13px; font-weight:700; cursor:pointer; }
  #nav button:hover { background:#2d9e6b; color:#fff; }
  #fsb { background:linear-gradient(135deg,#2d9e6b,#c8e06a) !important; color:#0d1f16 !important; border:none !important; }
</style>
</head>
<body>
<div id="wrap">
  <div id="hdr">
    <div class="logo-w">__LOGO_IZQ__</div>
    <div id="titulo"></div>
    <div class="logo-w r">__LOGO_DER__</div>
  </div>
  <div id="pw"><div id="pb"></div></div>
  <div id="body">
    <div id="plt-div"></div>
    <div id="html-div"></div>
  </div>
  <div id="footer">
    <div id="dots"></div>
    <div id="ctr"></div>
    <div id="nav">
      <button onclick="mPrev()">&#8592;</button>
      <button onclick="mNext()">&#8594;</button>
      <button id="fsb" onclick="toggleFS()">&#x26F6; Fullscreen</button>
    </div>
  </div>
</div>
<script>
var SLIDES=__SLIDES_JS__, N=SLIDES.length, idx=0, tmr=null, ptmr=null, DL=5000;
var isHeatmap=false, isScatter=false;

function goTo(i) {
  idx=i;
  document.getElementById('titulo').textContent=SLIDES[i].titulo;
  document.getElementById('ctr').textContent=(i+1)+' / '+N;
  var plt=document.getElementById('plt-div');
  var htm=document.getElementById('html-div');
  var body=document.getElementById('body');
  if (SLIDES[i].tipo==='plotly') {
    plt.style.display='block'; htm.style.display='none';
    isHeatmap = SLIDES[i].fig.data && SLIDES[i].fig.data[0] && SLIDES[i].fig.data[0].type==='heatmap';
    isScatter  = SLIDES[i].fig.data && SLIDES[i].fig.data[0] && SLIDES[i].fig.data[0].type==='scatter';
    var W=body.clientWidth-6, H=body.clientHeight-6;
    var base=SLIDES[i].fig.layout||{};
    var mg = isHeatmap ? {l:160,r:20,t:50,b:20} : (isScatter ? {l:20,r:20,t:60,b:60} : {l:160,r:100,t:30,b:40});
    var figData = SLIDES[i].fig.data.map(function(trace) {
      if (isScatter) {
        var t=Object.assign({},trace);
        if (t.mode && t.mode.indexOf('text')===-1) t.mode=t.mode+'+text';
        if (!t.mode) t.mode='lines+markers+text';
        if (t.y && t.y.length) t.text=t.y.map(function(v){ return typeof v==='number' ? v.toLocaleString('es-PE') : (v||''); });
        t.textposition='top center';
        t.textfont={size:13,color:'#1a7a4a',family:'Arial'};
        return t;
      }
      return trace;
    });
    var lay=Object.assign({},base,{
      autosize:false,width:W,height:H,
      paper_bgcolor:'#ffffff',plot_bgcolor:'#ffffff',
      margin:mg,font:{family:'Arial',size:13},
      yaxis: isHeatmap ? Object.assign({},base.yaxis||{},{title:'',tickfont:{size:11.5}})
           : (isScatter ? Object.assign({},base.yaxis||{},{visible:false,showticklabels:false,showgrid:false,zeroline:false})
           : (base.yaxis||{})),
      xaxis: isHeatmap ? Object.assign({},base.xaxis||{},{title:'',tickfont:{size:13},side:'top'})
           : Object.assign({},base.xaxis||{},{tickfont:{size:13},showgrid:false})
    });
    Plotly.react('plt-div', figData, lay, {displayModeBar:false,responsive:false});
  } else {
    plt.style.display='none'; htm.style.display='block';
    htm.innerHTML=SLIDES[i].content;
    setTimeout(function(){
      htm.querySelectorAll('[data-chart="bar"]').forEach(function(el){
        var data = JSON.parse(el.getAttribute('data-points') || '[]');
        var color = el.getAttribute('data-color') || '#1D9E75';
        if (!data.length) return;
        var W = parseInt(el.getAttribute('data-w') || '0') || el.parentElement.clientWidth - 28 || 400;
        var H = parseInt(el.getAttribute('data-h') || '0') || 190;
        Plotly.newPlot(el, [{
          type: 'bar',
          x: data.map(function(d){ return d.x; }),
          y: data.map(function(d){ return d.y; }),
          marker: { color: color, opacity: 0.85 },
          text: data.map(function(d){ return String(d.y); }),
          textposition: 'outside', cliponaxis: false,
          textfont: { size: 15, color: '#1a7a4a' }
        }], {
          autosize: false, width: W, height: H,
          paper_bgcolor: '#ffffff', plot_bgcolor: '#ffffff',
          margin: { l: 35, r: 10, t: 18, b: 55 },
          font: { family: 'Arial,sans-serif', size: 10 },
          xaxis: { showgrid: false, tickfont: { size: 13 }, tickangle: -35, automargin: true },
          yaxis: { gridcolor: '#f0faf4', tickfont: { size: 13 }, zeroline: false }
        }, { displayModeBar: false, responsive: false });
      });
    }, 80);
  }
  document.querySelectorAll('#dots span').forEach(function(d,j){ d.className=j===i?'on':''; });
  clearInterval(ptmr);
  var pb=document.getElementById('pb'),t0=Date.now();
  pb.style.width='0%';
  ptmr=setInterval(function(){ pb.style.width=Math.min(100,(Date.now()-t0)/DL*100)+'%'; },50);
}

function next(){ goTo((idx+1)%N); }
function mNext(){ clearInterval(tmr); next(); tmr=setInterval(next,DL); }
function mPrev(){ clearInterval(tmr); goTo((idx-1+N)%N); tmr=setInterval(next,DL); }

function toggleFS() {
  var el=document.documentElement;
  if (document.fullscreenElement) {
    document.exitFullscreen();
    document.getElementById('fsb').textContent='⛶ Fullscreen';
  } else {
    el.requestFullscreen && el.requestFullscreen().then(function(){
      document.getElementById('fsb').textContent='⊠ Salir';
      setTimeout(function(){ goTo(idx); },300);
    });
  }
}

window.addEventListener('resize',function(){ clearTimeout(window._rt); window._rt=setTimeout(function(){ goTo(idx); },200); });
document.addEventListener('keydown',function(e){
  if(e.key==='ArrowRight') mNext();
  if(e.key==='ArrowLeft')  mPrev();
  if(e.key==='f'||e.key==='F') toggleFS();
});

(function(){
  var dts=document.getElementById('dots');
  SLIDES.forEach(function(_,j){
    var d=document.createElement('span');
    d.onclick=function(){ clearInterval(tmr); goTo(j); tmr=setInterval(next,DL); };
    dts.appendChild(d);
  });
  goTo(0);
  tmr=setInterval(next,DL);
})();
</script>
</body>
</html>"""


def _render_top10(df, n=10):
    st.markdown('<div class="titulo-seccion">🏆 Top SKUs despachados</div>', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tiendas_opts = sorted(df["nombre_tienda"].unique().tolist())
        sel_t = st.multiselect("Tienda(s)", options=["TODAS"] + tiendas_opts, default=["TODAS"], key="top10_tienda")
    with col_f2:
        meses_opts = sorted(df["mes"].unique(), key=lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99)
        sel_m = st.multiselect("Mes(es)", options=["TODOS"] + meses_opts, default=["TODOS"], key="top10_mes")
    with col_f3:
        n_top = st.selectbox("Mostrar top", options=[5, 10, 15, 20], index=1, key="top10_n")
    df_f = df.copy()
    df_f["sku"] = df_f["sku"].astype(str).str.strip()
    if "TODAS" not in sel_t and sel_t:
        df_f = df_f[df_f["nombre_tienda"].isin(sel_t)]
    if "TODOS" not in sel_m and sel_m:
        df_f = df_f[df_f["mes"].isin(sel_m)]
    desc_map = df_f.groupby("sku")["descripcion"].first().to_dict()
    top = (df_f.groupby("sku")["unidades"].sum().nlargest(n_top).reset_index().sort_values("unidades", ascending=True))
    top["descripcion"] = top["sku"].astype(str).map(desc_map).fillna("Sin descripción")
    top["sku"] = "SKU-" + top["sku"].astype(str).str.strip()
    n_bars = len(top)
    colores_barra = [f"hsl({int(120 - (i / max(n_bars - 1, 1)) * 60)}, 68%, 42%)" for i in range(n_bars)]
    fig = go.Figure(go.Bar(
        x=top["unidades"], y=top["sku"], orientation="h",
        marker=dict(color=colores_barra),
        text=top["unidades"].apply(lambda v: f"{v:,}"), textposition="outside",
        textfont=dict(size=12, color="#2d3436"),
        customdata=list(zip(top["descripcion"], top["sku"])),
        hovertemplate="<b>%{customdata[0]}</b><br>🔑 SKU: %{customdata[1]}<br>📦 Unidades: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        height=max(400, n_top * 48), margin=dict(l=10, r=90, t=15, b=30),
        xaxis=dict(showgrid=True, gridcolor="#e8f5ee", title="Unidades", tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, title="", tickfont=dict(size=12), automargin=True,
                   type="category", categoryorder="array", categoryarray=top["sku"].tolist()),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", size=12, color="#2d3436"), bargap=0.35,
    )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("📋 Ver tabla detalle"):
        tabla = top.sort_values("unidades", ascending=False).reset_index(drop=True)
        tabla.index += 1
        tabla = tabla.rename(columns={"sku": "SKU", "unidades": "Unidades", "descripcion": "Descripción"})
        tabla["Unidades"] = tabla["Unidades"].apply(lambda v: f"{v:,}")
        st.dataframe(tabla[["SKU", "Descripción", "Unidades"]], use_container_width=True)
    return fig


def _render_evolutivo(df):
    st.markdown('<div class="titulo-seccion">📈 Evolutivo de despachos por mes</div>', unsafe_allow_html=True)
    col_t, col_m = st.columns([2, 2])
    with col_t:
        tiendas_disp = sorted(df["nombre_tienda"].unique().tolist())
        sel_tiendas = st.multiselect("Tienda(s)", options=["TODAS"] + tiendas_disp, default=["TODAS"], key="evol_tiendas")
    with col_m:
        meses_disp = sorted(df["mes"].unique(), key=lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99)
        sel_meses = st.multiselect("Mes(es)", options=meses_disp, default=meses_disp, key="evol_meses")
    if not sel_meses:
        st.info("Selecciona al menos un mes.")
        return None
    df_f = df.copy()
    if "TODAS" not in sel_tiendas and sel_tiendas:
        df_f = df_f[df_f["nombre_tienda"].isin(sel_tiendas)]
    if sel_meses:
        df_f = df_f[df_f["mes"].isin(sel_meses)]
    modo_total = "TODAS" in sel_tiendas or not sel_tiendas
    fig = go.Figure()
    if modo_total:
        pivot = _ordenar_meses(df_f.groupby("mes")["unidades"].sum().reset_index())
        fig.add_trace(go.Scatter(
            x=pivot["mes"], y=pivot["unidades"], mode="lines+markers+text", name="TOTAL",
            line=dict(color=GREEN_MAIN, width=3), marker=dict(size=10, color=GREEN_MAIN),
            text=pivot["unidades"].apply(lambda v: f"{v:,}"), textposition="top center",
            hovertemplate="<b>Total</b><br>Mes: %{x}<br>Unidades: %{y:,}<extra></extra>",
            fill="tozeroy", fillcolor="rgba(45,158,107,0.12)",
        ))
    else:
        pivot = _ordenar_meses(df_f.groupby(["mes", "nombre_tienda"])["unidades"].sum().reset_index())
        for i, tienda in enumerate([t for t in sel_tiendas if t != "TODAS"]):
            df_t = pivot[pivot["nombre_tienda"] == tienda]
            if df_t.empty: continue
            color = COLORES_TIENDAS[i % len(COLORES_TIENDAS)]
            fig.add_trace(go.Scatter(
                x=df_t["mes"], y=df_t["unidades"], mode="lines+markers+text", name=tienda,
                line=dict(color=color, width=2.5), marker=dict(size=8, color=color),
                text=df_t["unidades"].apply(lambda v: f"{v:,}"), textposition="top center",
                hovertemplate=f"<b>{tienda}</b><br>Mes: %{{x}}<br>Unidades: %{{y:,}}<extra></extra>",
            ))
    fig.update_layout(
        height=420, margin=dict(l=10, r=20, t=20, b=80),
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="#e8f5ee", title="Unidades"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", size=12, color="#2d3436"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
        hovermode="x unified",
    )
    fig_evol = fig
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("📋 Ver tabla pivoteada"):
        if modo_total:
            tabla = pivot.set_index("mes")[["unidades"]]
            tabla.columns = ["Unidades"]
            tabla["Unidades"] = tabla["Unidades"].apply(lambda v: f"{v:,}")
            st.dataframe(tabla, use_container_width=True)
        else:
            tabla = pivot.pivot_table(index="nombre_tienda", columns="mes", values="unidades", aggfunc="sum", fill_value=0)
            cols_ord = [m for m in ORDEN_MESES if m in tabla.columns]
            tabla = tabla[cols_ord]
            tabla["TOTAL"] = tabla.sum(axis=1)
            tabla = tabla.sort_values("TOTAL", ascending=False)
            st.dataframe(tabla.style.format("{:,}"), use_container_width=True)
    return fig_evol


def _render_heatmap(df):
    st.markdown('<div class="titulo-seccion">🗺️ Mapa de calor tienda × mes</div>', unsafe_allow_html=True)
    pivot = df.groupby(["nombre_tienda", "mes"])["unidades"].sum().reset_index()
    tabla = pivot.pivot_table(index="nombre_tienda", columns="mes", values="unidades", fill_value=0)
    cols_ord = [m for m in ORDEN_MESES if m in tabla.columns]
    tabla = tabla[cols_ord]
    tabla["TOTAL"] = tabla.sum(axis=1)
    tabla = tabla.sort_values("TOTAL", ascending=False).drop(columns=["TOTAL"])
    fig = px.imshow(
        tabla, color_continuous_scale=[[0.0, "#f0faf4"], [0.25, "#85dcaa"], [0.5, "#3dbb7e"], [0.75, "#c8e06a"], [1.0, "#e8a020"]],
        aspect="auto", text_auto=True, labels=dict(color="Unidades"),
    )
    fig.update_traces(texttemplate="%{z:,}", textfont_size=11)
    fig.update_layout(
        height=max(350, len(tabla) * 32 + 80), margin=dict(l=10, r=10, t=20, b=40),
        coloraxis_showscale=False, xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)), plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", size=11, color="#2d3436"),
    )
    st.plotly_chart(fig, use_container_width=True)
    return fig


def render_dash_despachos():
    df = cargar_despachos()
    if df.empty:
        st.warning("⚠️ Sin datos en CONSOLIDADO_DESPACHOS o error de conexión.")
        return
    faltantes = {"sku", "unidades", "mes"} - set(df.columns)
    if faltantes:
        st.error(f"❌ Columnas faltantes en el sheet: {', '.join(faltantes)}")
        return
    st.markdown('<div class="titulo-seccion">📊 Dashboard de Despachos</div>', unsafe_allow_html=True)
    _render_metricas_despachos(df)
    st.divider()
    fig_top = _render_top10(df)
    st.divider()
    fig_evol = _render_evolutivo(df)
    st.divider()
    fig_hm = _render_heatmap(df)
    st.divider()
    mostrar_seccion_ppt("📊 Dashboard de Despachos", [
        ("🏆 Top SKUs despachados", fig_top),
        ("📈 Evolutivo mensual", fig_evol),
        ("🗺️ Mapa de calor tienda × mes", fig_hm),
    ])


# =========================================================
# 4. FUNCIONES DE PROCESAMIENTO Y MENÚ LATERAL (FINAL DEL SCRIPT)
# =========================================================

# Inicializaciones de variables clave en session_state
_KEY_PPT = "p_mode"
_KEY_HTML = "p_html"

if _KEY_PPT not in st.session_state:
    st.session_state[_KEY_PPT] = False

# Sidebar de Control
with st.sidebar:
    st.markdown("### ⚙️ Panel de Configuración")
    # Toggle de modo presentación integral
    modo_pres = st.toggle("🖥️ Modo Presentación Completo", value=st.session_state[_KEY_PPT], key="toggle_pres")
    if modo_pres != st.session_state[_KEY_PPT]:
        st.session_state[_KEY_PPT] = modo_pres
        st.rerun()

    st.markdown("---")
    opcion_menu = st.radio("Secciones", ["📦 Historial Carcasas", "📊 Dashboard Despachos"])

# Enrutamiento de Vistas principales
if not st.session_state[_KEY_PPT]:
    if opcion_menu == "📦 Historial Carcasas":
        st.title("📦 Control de Historial Carcasas")
        df_hist = cargar_historial_carcasa()
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("No se encontraron registros en el historial.")
    elif opcion_menu == "📊 Dashboard Despachos":
        render_dash_despachos()

# 7. MODO PRESENTACIÓN INTEGRAL (INYECTADO CORREGIDO Y ALINEADO)
else:
    if _KEY_HTML not in st.session_state or True:
        df_hist_cron = cargar_historial_carcasa()
        if not df_hist_cron.empty and 'Fecha' in df_hist_cron.columns:
            df_cron = df_hist_cron.sort_values('Fecha', ascending=True)
            fechas_js = [x.strftime('%d/%m') for x in df_cron['Fecha']]
            eri_js = [float(x) for x in df_cron['ERI %']] if 'ERI %' in df_cron.columns else []
            eru_js = [float(x) for x in df_cron['ERU %']] if 'ERU %' in df_cron.columns else []
        else:
            fechas_js, eri_js, eru_js = [], [], []
        
        _html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
<style>
  html, body {{
    margin: 0; padding: 0; width: 100%; height: 100vh;
    background-color: #0b1e14; color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    overflow: hidden;
  }}
  .header-container {{
    height: 20vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-bottom: 2px solid #2d9e6b;
    box-sizing: border-box;
    background: linear-gradient(180deg, #102a1c 0%, #0b1e14 100%);
  }}
  .header-container h1 {{
    margin: 0;
    font-size: 2.5rem;
    color: #85dcaa;
    text-transform: uppercase;
    letter-spacing: 2px;
    text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
  }}
  .header-container p {{
    margin: 5px 0 0 0;
    font-size: 1.1rem;
    color: #c8e06a;
    opacity: 0.9;
  }}
  .charts-container {{
    height: 80vh;
    display: flex;
    flex-direction: row;
    box-sizing: border-box;
    padding: 15px;
    gap: 15px;
  }}
  .chart-box {{
    flex: 1;
    height: 100%;
    background-color: #102a1c;
    border-radius: 12px;
    border: 1px solid #1a7a4a;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    box-sizing: border-box;
    padding: 10px;
    position: relative;
  }}
  .fs-btn {{
    position: absolute; bottom: 20px; right: 20px;
    background-color: #2d9e6b; color: white; border: none;
    padding: 10px 18px; font-weight: bold; border-radius: 6px;
    cursor: pointer; z-index: 9999; font-size: 0.9rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: background 0.2s;
  }}
  .fs-btn:hover {{ background-color: #3dbb7e; }}
</style>
</head>
<body>
<div class="header-container">
    <h1>📦 Sistema Logístico Carcasas</h1>
    <p>Modo de Visualización en Pantalla de Control</p>
</div>
<div class="charts-container">
  <div class="chart-box" id="chart-eri"></div>
  <div class="chart-box" id="chart-eru"></div>
</div>
<button class="fs-btn" id="fsb" onclick="toggleFS()">⛶ Pantalla completa</button>
<script>
var eriDates = {fechas_js};
var eriVals = {eri_js};
var eruDates = {fechas_js};
var eruVals = {eru_js};

function mkChart(divId, dates, vals, lineColor, titleText) {{
  var trace = {{
    x: dates, y: vals, type: 'scatter', mode: 'lines+markers',
    line: {{ color: lineColor, width: 4 }},
    marker: {{ size: 10, color: '#e8d44d' }},
    name: titleText
  }};
  Plotly.newPlot(divId, [trace], {{
    title: {{ text: titleText, font: {{ color: '#ffffff', size: 22, family: 'sans-serif', weight: 'bold' }} }},
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {{ l: 50, r: 30, t: 60, b: 50 }},
    xaxis: {{
      gridcolor: '#1a7a4a', tickcolor: '#1a7a4a',
      tickfont: {{ color: '#ffffff', size: 14 }},
      linecolor: '#1a7a4a'
    }},
    yaxis: {{
      gridcolor: '#1a7a4a', tickcolor: '#1a7a4a',
      tickfont: {{ color: '#ffffff', size: 14 }},
      linecolor: '#1a7a4a', linewidth: 1
    }},
    shapes: [],
    annotations: []
  }}, {{displayModeBar:false, responsive:true}});
}}

function renderCharts() {{
  mkChart("chart-eri", eriDates, eriVals, "#1a7a4a", "ERI %");
  mkChart("chart-eru", eruDates, eruVals, "#2d9e6b", "ERU %");
}}

function toggleFS() {{
  var el = document.documentElement;
  if (document.fullscreenElement) {{
    document.exitFullscreen();
    document.getElementById("fsb").textContent = "⛶ Pantalla completa";
    setTimeout(renderCharts, 300);
  }} else {{
    el.requestFullscreen && el.requestFullscreen().then(function(){{
      document.getElementById("fsb").textContent = "⊠ Salir";
      setTimeout(renderCharts, 300);
    }});
  }}
}}

document.addEventListener("keydown", function(e){{
  if(e.key==="f"||e.key==="F") toggleFS();
}});

window.addEventListener("resize", function(){{
  clearTimeout(window._rt);
  window._rt = setTimeout(renderCharts, 200);
}});

setTimeout(renderCharts, 120);
</script>
</body>
</html>"""
        st.session_state[_KEY_HTML] = _html
        st.rerun()

    if st.session_state.get(_KEY_PPT) and _KEY_HTML in st.session_state:
        import streamlit.components.v1 as _comp
        _comp.html(st.session_state[_KEY_HTML], height=850, scrolling=False)
