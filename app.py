# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN PRO OPTIMIZADA (RECUENTO=1)
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import os
import base64
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Logístico Carcasas", page_icon="📦", layout="wide")

# 2. LOGO Y ESTILOS
def cargar_estilos():
    st.markdown("""
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
            background: linear-gradient(180deg, #1a7a4a 0%, #2d9e6b 60%, #c8e06a 100%);
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
        """, unsafe_allow_html=True)


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
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}"); return None

client = conectar_google()

# ── ID Sheet Historial Carcasa ─────────────────────────────────────────────
SHEET_ID_HIST_CARCASA = "1x0jVDMYk9htwttNcpXlXeaQcR0ELoBYeF4iP2qYcs1s"

@st.cache_data(ttl=300)  # ← descomenta esta línea
def cargar_historial_carcasa():
    import re, pandas as pd
    try:
        sh = client.open_by_key(SHEET_ID_HIST_CARCASA)
        # quita los st.write de debug
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
            tmpl = open(__file__).read()
            # El template está embebido como string en la función _ppt_template()
            html = _ppt_template()
            html = (html
                .replace("__SLIDES_JS__", slides_js)
                .replace("__LOGO_IZQ__", logo_izq_tag)
                .replace("__LOGO_DER__", logo_der_tag)
            )
            st.session_state[key_html] = html
        st.rerun()

    if st.session_state.get(key_show) and key_html in st.session_state:
        components.html(st.session_state[key_html], height=860, scrolling=False)


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
  #wrap { width:100%; height:100vh; display:flex; flex-direction:column; padding:10px 20px 10px; gap:8px; }
  #hdr { display:flex; align-items:center; justify-content:space-between; background:#fff; border-radius:12px; border:2px solid #2d9e6b; padding:8px 20px; flex-shrink:0; }
  .logo-w { width:190px; display:flex; align-items:center; }
  .logo-w.r { justify-content:flex-end; }
  #titulo { color:#1a7a4a; font-size:1.5rem; font-weight:800; text-align:center; flex:1; padding:0 10px; }
  #pw { width:100%; height:5px; background:#c8e06a; border-radius:3px; flex-shrink:0; }
  #pb { height:5px; background:#1a7a4a; border-radius:3px; width:0%; }
  #body { flex:1; min-height:0; border:3px solid #2d9e6b; border-radius:14px; background:#fff; overflow:hidden; display:flex; align-items:stretch; }
  #plt-div { width:100%; height:100%; }
  #html-div { width:100%; height:100%; overflow:hidden; display:none; }
  #footer { display:flex; align-items:center; justify-content:space-between; background:#fff; border-radius:12px; border:2px solid #c8e06a; padding:6px 16px; flex-shrink:0; }
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
    // Renderizar divs con data-chart usando Plotly (ya cargado en este documento)
    setTimeout(function(){
      htm.querySelectorAll('[data-chart="bar"]').forEach(function(el){
        var data = JSON.parse(el.getAttribute('data-points') || '[]');
        var color = el.getAttribute('data-color') || '#1D9E75';
        if (!data.length) return;
        // Usar dimensiones fijas si el elemento las define (data-w / data-h)
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
        tabla,
        color_continuous_scale=[[0.0, "#f0faf4"], [0.25, "#85dcaa"], [0.5, "#3dbb7e"], [0.75, "#c8e06a"], [1.0, "#e8a020"]],
        aspect="auto", text_auto=True, labels=dict(color="Unidades"),
    )
    fig.update_traces(texttemplate="%{z:,}", textfont_size=11)
    fig.update_layout(
        height=max(350, len(tabla) * 32 + 80),
        margin=dict(l=10, r=10, t=20, b=40),
        coloraxis_showscale=False,
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
        plot_bgcolor="white", paper_bgcolor="white",
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
    fig_top  = _render_top10(df)
    st.divider()
    fig_evol = _render_evolutivo(df)
    st.divider()
    fig_hm   = _render_heatmap(df)
    st.divider()
    mostrar_seccion_ppt("📊 Dashboard de Despachos", [
        ("🏆 Top SKUs despachados",       fig_top),
        ("📈 Evolutivo mensual",          fig_evol),
        ("🗺️ Mapa de calor tienda × mes", fig_hm),
    ])


# =========================================================
# 4. FUNCIONES DE PROCESAMIENTO
# =========================================================

def update_consolidado_arribo(doc, fecha, asns_sel=None):
    """
    Solo escribe en RECEPCION_IMPORTACIONES → MOVIMIENTOS.
    No modifica el Consolidado - Carcasas.
    asns_sel: lista de ASNs a confirmar, o ["TODAS"] / None para confirmar todos.
    """
    try:
        sh_cons = abrir_archivo_dinamico("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_data = wks_cons.get_all_values()
        headers = [h.upper() for h in all_data[0]]

        col_doc      = headers.index("NOMBRE CORREO")
        col_recuento = headers.index("RECUENTO") if "RECUENTO" in headers else None
        col_asn      = headers.index("ASN") if "ASN" in headers else None

        filtrar_asn = (asns_sel and "TODAS" not in asns_sel)

        filas_para_traspaso = []

        for i, row in enumerate(all_data[1:], start=2):
            if row[col_doc] == str(doc):
                if col_recuento is not None and str(row[col_recuento]).strip() not in ["1", "1.0"]:
                    continue
                if filtrar_asn and col_asn is not None:
                    if str(row[col_asn]).strip() not in [str(a) for a in asns_sel]:
                        continue
                filas_para_traspaso.append(row)

        if filas_para_traspaso:
            sh_rec  = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
            wks_mov = sh_rec.worksheet("MOVIMIENTOS")

            bulk_data = []
            for row in filas_para_traspaso:
                tienda = row[headers.index("TIENDA")].strip() if "TIENDA" in headers else ""
                if tienda == "4298":
                    dest, proc = "ALMACENAJE", "POR ALMACENAR"
                else:
                    dest = "TIENDA"
                    es_ap = any("APERTURA" in str(row[headers.index(f"X{j}")]).upper()
                                for j in range(1, 10) if f"X{j}" in headers)
                    proc = "APERTURA" if es_ap else "POR DISTRIBUIR"

                col_hora_fech_idx = headers.index("ETA") if "ETA" in headers else 0
                bulk_data.append([
                    row[headers.index("ID_DESPACHO")] if "ID_DESPACHO" in headers else row[0],
                    row[col_doc],
                    row[headers.index("ASN")] if "ASN" in headers else "",
                    tienda,
                    row[headers.index("CANTIDAD")] if "CANTIDAD" in headers else "",
                    "Pendiente",
                    str(fecha),
                    row[col_hora_fech_idx],
                    dest, proc, ""
                ])
            wks_mov.append_rows(bulk_data)
            return True
        return False
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False


# =========================================================
# 5. UI Y RENDERIZADO
# =========================================================

df_import, df_recep, df_tiendas = cargar_datos_completos()

st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", [
    "📦 Importaciones",
    "📊 Dash Despachos",
    "📋 Indicadores de Almacén",
])

# ----------------------------------------------------------
# MENÚ: IMPORTACIONES
# ----------------------------------------------------------
if menu == "📦 Importaciones":
    tab_dash, tab_ops = st.tabs(["📊 Dash Importacion", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas de Tiendas - Perú")
        if not df_tiendas.empty:
            columnas_tiendas_req = ["ESTADO", "FCH ESTIMADA", "TIENDA", "DESCRIPCION"]
            if all(col in df_tiendas.columns for col in columnas_tiendas_req):
                df_ap = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
                df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors='coerce')
                df_filtrado = df_ap[df_ap["FCH_DT"] >= datetime.now()].sort_values("FCH_DT").head(4)
                cols = st.columns(4)
                for i, (_, row) in enumerate(df_filtrado.iterrows()):
                    with cols[i % 4]:
                        st.markdown(f'''<div class="apertura-card">
                            <div class="tienda-titulo">🏪 {row["TIENDA"]}</div>
                            <div class="desc-tienda">{row["DESCRIPCION"]}</div>
                            <div class="fecha-est">📅 {row.get("FCH ESTIMADA","")}</div>
                        </div>''', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Columnas faltantes en 'TIENDAS CARCASAS'")

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)

        df_pend = pd.DataFrame()
        df_arr  = pd.DataFrame()

        # Pares (importacion, ASN) ya en recepción — lógica por combinación, no solo por importación
        pares_recibidos = set()
        if not df_recep.empty and "IMPORTACION" in df_recep.columns and "ASN" in df_recep.columns:
            pares_recibidos = set(
                zip(
                    df_recep["IMPORTACION"].astype(str).str.strip().str.lower(),
                    df_recep["ASN"].astype(str).str.strip().str.lower()
                )
            )

        if not df_import.empty and "NOMBRE CORREO" in df_import.columns:
            # Filtrar Recuento = 1
            col_rec = next((c for c in df_import.columns if c.upper() == "RECUENTO"), None)
            df_base = df_import[df_import[col_rec].isin(["1", "1.0"])].copy() if col_rec else df_import.copy()

            # Pendientes = ASNs del consolidado cuyo par (importacion, ASN) NO está en recepción
            if "ASN" in df_base.columns and pares_recibidos:
                par_key = list(zip(
                    df_base["NOMBRE CORREO"].astype(str).str.strip().str.lower(),
                    df_base["ASN"].astype(str).str.strip().str.lower()
                ))
                mask_pend = [p not in pares_recibidos for p in par_key]
            else:
                # Fallback: si no hay ASN en consolidado, filtrar por importación completa
                importaciones_recibidas = set(r[0] for r in pares_recibidos)
                mask_pend = ~df_base["NOMBRE CORREO"].astype(str).str.strip().str.lower().isin(importaciones_recibidas)
            _pend_raw = df_base[mask_pend].copy()

            if not _pend_raw.empty:
                # Detectar columna ETA (buscar variantes de nombre)
                col_eta = next((c for c in _pend_raw.columns if c.upper() in ("ETA", "FECHA ETA", "F. ETA", "FETA")), None)
                # Groupby SIN ETA para no multiplicar filas
                cols_grp = ["NOMBRE CORREO", "STATUS"]
                if "ETA" in _pend_raw.columns:
                    cols_grp.append("ETA")
                agg_col = "ASN" if "ASN" in _pend_raw.columns else "NOMBRE CORREO"
                rename_map = {
                    agg_col: "ASNs",
                    "NOMBRE CORREO": "Importación",
                    "STATUS": "Estado",
                    "ETA": "ETA",
                }
                df_pend = (
                    _pend_raw.groupby(cols_grp)[agg_col].nunique()
                    .reset_index()
                    .rename(columns=rename_map)
                )
                # Agregar ETA como columna aparte (primer valor por importación)
                if col_eta:
                    _eta_map = (
                        _pend_raw.groupby("NOMBRE CORREO")[col_eta]
                        .first()
                        .reset_index()
                        .rename(columns={"NOMBRE CORREO": "Importación", col_eta: "ETA"})
                    )
                    df_pend = df_pend.merge(_eta_map, on="Importación", how="left")
                orden_map = {"ADUANAS": 0, "EN TRÁNSITO": 1, "EN TRANSITO": 1, "ORIGEN": 2, "SUPPLY": 3}
                df_pend["_ord"] = df_pend["Estado"].str.upper().str.strip().map(orden_map).fillna(4)
                df_pend = df_pend.sort_values("_ord").drop(columns=["_ord"]).reset_index(drop=True)

        # Arribados = de recepción, agrupados por importación + fecha llegada
        if not df_recep.empty and "IMPORTACION" in df_recep.columns:
            col_fch = "FCH LLEGADA" if "FCH LLEGADA" in df_recep.columns else None
            cols_arr = ["IMPORTACION"] + ([col_fch] if col_fch else [])
            agg_col2 = "ASN" if "ASN" in df_recep.columns else "IMPORTACION"
            df_arr = (
                df_recep.groupby(cols_arr)[agg_col2].nunique()
                .reset_index()
                .rename(columns={
                    "IMPORTACION": "Importación",
                    agg_col2: "ASNs",
                    col_fch: "Fecha Llegada"
                })
            )
            df_arr = df_arr[df_arr["Importación"].str.strip() != ""].reset_index(drop=True)
            if "Fecha Llegada" in df_arr.columns:
                df_arr["_fch"] = pd.to_datetime(df_arr["Fecha Llegada"], errors="coerce")
                df_arr = df_arr.sort_values("_fch", ascending=False, na_position="last").drop(columns=["_fch"])
            df_arr = df_arr.reset_index(drop=True)

        # Métricas
        total_docs = df_import["NOMBRE CORREO"].nunique() if not df_import.empty and "NOMBRE CORREO" in df_import.columns else 0
        n_pend = df_pend["Importación"].nunique() if not df_pend.empty else 0
        n_arr  = df_arr["Importación"].nunique()  if not df_arr.empty  else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("📋 Total Importaciones", total_docs)
        m2.metric("⏳ Pendientes de Arribo", n_pend)
        m3.metric("✅ Arribados", n_arr)

        st.divider()

        # ── Función tabla HTML bonita ──────────────────────────────────────
        def _render_tabla_html(df, tipo="pend"):
            if df.empty:
                return ""
            STATUS_COLORS = {
                "EN TRÁNSITO": ("#E6F1FB","#185FA5"),
                "EN TRANSITO": ("#E6F1FB","#185FA5"),
                "ORIGEN":      ("#FAEEDA","#854F0B"),
                "SUPPLY":      ("#EEEDFE","#534AB7"),
                "ADUANAS":     ("#FAEEDA","#BA7517"),
            }
            rows_html = ""
            for i, row in df.iterrows():
                bg = "#ffffff" if i % 2 == 0 else "#f9fefb"
                cells = ""
                for col_name, val in row.items():
                    val_str = str(val) if str(val) not in ("nan","None","") else "—"
                    if col_name == "Estado" and val_str.upper() in STATUS_COLORS:
                        pill_bg, pill_fg = STATUS_COLORS[val_str.upper()]
                        cells += (f'<td style="padding:9px 14px;border-bottom:1px solid #f0faf4;">'
                                  f'<span style="background:{pill_bg};color:{pill_fg};padding:3px 10px;'
                                  f'border-radius:20px;font-size:11.5px;font-weight:600;">{val_str}</span></td>')
                    elif col_name == "ASNs":
                        cells += (f'<td style="padding:9px 14px;border-bottom:1px solid #f0faf4;'
                                  f'text-align:right;font-weight:700;color:#1a7a4a;font-size:13px;">{val_str}</td>')
                    elif col_name in ("ETA","Fecha ETD","Fecha Llegada"):
                        cells += (f'<td style="padding:9px 14px;border-bottom:1px solid #f0faf4;'
                                  f'color:#e8a020;font-weight:600;font-size:12.5px;">'
                                  f'<span style="display:inline-flex;align-items:center;gap:4px;">📅 {val_str}</span></td>')
                    else:
                        cells += (f'<td style="padding:9px 14px;border-bottom:1px solid #f0faf4;'
                                  f'color:#2d3436;font-size:12.5px;">{val_str}</td>')
                rows_html += f'<tr style="background:{bg};">{cells}</tr>'

            heads = "".join(
                f'<th style="padding:10px 14px;background:#1a7a4a;color:#fff;font-size:11.5px;'
                f'font-weight:700;text-align:left;letter-spacing:0.5px;">{c}</th>'
                for c in df.columns
            )
            return (
                '<div style="overflow-x:auto;border-radius:10px;border:1px solid #e0f2e9;">'
                '<table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;">'
                f'<thead><tr>{heads}</tr></thead>'
                f'<tbody>{rows_html}</tbody>'
                '</table></div>'
            )

        # ── Gráficos del dashboard: por fecha y por importación ──────────────
        _gcol1, _gcol2 = st.columns(2)

        with _gcol1:
            # Barras: ASNs ARRIBADOS POR FECHA DE LLEGADA
            if not df_arr.empty and "Fecha Llegada" in df_arr.columns:
                _df_fch = df_arr.copy()
                _df_fch["_f"] = pd.to_datetime(_df_fch["Fecha Llegada"], errors="coerce")
                _df_fch = _df_fch.dropna(subset=["_f"]).sort_values("_f")
                if not _df_fch.empty:
                    fig_fecha = go.Figure()
                    fig_fecha.add_trace(go.Bar(
                        x=_df_fch["Fecha Llegada"].astype(str),
                        y=_df_fch["ASNs"],
                        marker_color="#1D9E75",
                        text=_df_fch["ASNs"].astype(str),
                        textposition="outside",
                        textfont=dict(size=11, color="#1a7a4a"),
                        cliponaxis=False
                    ))
                    fig_fecha.update_layout(
                        height=260, showlegend=False,
                        title=dict(text="ASNs arribados por fecha de llegada", font=dict(size=13,color="#1a7a4a"), x=0),
                        margin=dict(l=10, r=10, t=40, b=60),
                        paper_bgcolor="white", plot_bgcolor="white",
                        xaxis=dict(tickfont=dict(size=10), showgrid=False, tickangle=-35),
                        yaxis=dict(gridcolor="#f0faf4", tickfont=dict(size=10)),
                        font=dict(family="Arial")
                    )
                    st.plotly_chart(fig_fecha, use_container_width=True)
            else:
                st.info("Sin datos de fecha de llegada.")

        with _gcol2:
            # Barras: ASNs ARRIBADOS POR IMPORTACIÓN
            if not df_arr.empty:
                fig_imp = go.Figure()
                fig_imp.add_trace(go.Bar(
                    x=df_arr["Importación"].astype(str),
                    y=df_arr["ASNs"],
                    marker_color="#378ADD",
                    text=df_arr["ASNs"].astype(str),
                    textposition="outside",
                    textfont=dict(size=11, color="#185FA5"),
                    cliponaxis=False
                ))
                fig_imp.update_layout(
                    height=260, showlegend=False,
                    title=dict(text="ASNs arribados por importación", font=dict(size=13,color="#1a7a4a"), x=0),
                    margin=dict(l=10, r=10, t=40, b=60),
                    paper_bgcolor="white", plot_bgcolor="white",
                    xaxis=dict(tickfont=dict(size=10), showgrid=False, tickangle=-35),
                    yaxis=dict(gridcolor="#f0faf4", tickfont=dict(size=10)),
                    font=dict(family="Arial")
                )
                st.plotly_chart(fig_imp, use_container_width=True)
            else:
                st.info("Sin datos de arribos aún.")

        # ── Tablas HTML estilizadas ────────────────────────────────────────
        c1, c2 = st.columns(2)

        with c1:
            n_pend_asn = int(df_pend["ASNs"].sum()) if not df_pend.empty and "ASNs" in df_pend.columns else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
                f'<span style="font-size:15px;font-weight:700;color:#1a7a4a;">⏳ Pendientes de Arribo</span>'
                f'<span style="background:#FAEEDA;color:#854F0B;padding:3px 12px;border-radius:20px;'
                f'font-size:12px;font-weight:600;">{len(df_pend)} importaciones · {n_pend_asn} ASNs</span></div>',
                unsafe_allow_html=True
            )
            if not df_pend.empty:
                st.markdown(_render_tabla_html(df_pend, "pend"), unsafe_allow_html=True)
            else:
                st.success("✅ No hay importaciones pendientes.")

        with c2:
            n_arr_asn = int(df_arr["ASNs"].sum()) if not df_arr.empty and "ASNs" in df_arr.columns else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
                f'<span style="font-size:15px;font-weight:700;color:#1a7a4a;">✅ Arribados</span>'
                f'<span style="background:#EAF3DE;color:#3B6D11;padding:3px 12px;border-radius:20px;'
                f'font-size:12px;font-weight:600;">{len(df_arr)} importaciones · {n_arr_asn} ASNs</span></div>',
                unsafe_allow_html=True
            )
            if not df_arr.empty:
                st.markdown(_render_tabla_html(df_arr, "arr"), unsafe_allow_html=True)
            else:
                st.info("Sin registros de recepción aún.")

        # ── Botón presentación importaciones ───────────────────────────────
        st.divider()

        # Slide 1: tarjetas aperturas
        # ══════════════════════════════════════════════════════
        # SLIDE 1: Próximas Aperturas — cards 2x2
        # ══════════════════════════════════════════════════════
        def _card_ap(tienda, desc, fecha):
            return (
                '<div style="background:#fff;border-radius:16px;border-left:6px solid #2d9e6b;'
                'padding:28px 30px;box-shadow:0 4px 16px rgba(45,158,107,0.13);'
                'display:flex;flex-direction:column;justify-content:space-between;">'
                '<div>'
                '<div style="color:#1a7a4a;font-size:1.5rem;font-weight:800;margin-bottom:10px;">🏪 ' + tienda + '</div>'
                '<div style="color:#636e72;font-size:1.05em;line-height:1.5;">' + desc + '</div>'
                '</div>'
                '<div style="color:#e8a020;font-weight:700;font-size:1.1em;margin-top:20px;'
                'padding-top:14px;border-top:2px solid #f0faf4;">📅 ' + fecha + '</div>'
                '</div>'
            )

        apertura_slide = ""
        if not df_tiendas.empty and all(c in df_tiendas.columns for c in ["ESTADO","FCH ESTIMADA","TIENDA","DESCRIPCION"]):
            df_ap2 = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
            df_ap2["FCH_DT"] = pd.to_datetime(df_ap2["FCH ESTIMADA"], dayfirst=True, errors="coerce")
            df_ap2 = df_ap2[df_ap2["FCH_DT"] >= datetime.now()].sort_values("FCH_DT").head(4)
            cards = "".join(_card_ap(str(r["TIENDA"]), str(r["DESCRIPCION"]), str(r.get("FCH ESTIMADA",""))) for _, r in df_ap2.iterrows())
            apertura_slide = (
                '<div style="width:100%;height:100%;padding:20px 28px 16px;background:linear-gradient(135deg,#f0faf4,#e8f5ee);'
                'font-family:Arial,sans-serif;box-sizing:border-box;display:flex;flex-direction:column;gap:14px;overflow:hidden;">'
                '<div style="font-size:11px;font-weight:700;color:#2d9e6b;text-transform:uppercase;letter-spacing:1.5px;flex-shrink:0;">'
                '🏪 Próximas Aperturas de Tiendas</div>'
                '<div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:16px;flex:1;min-height:0;">'
                + cards + '</div></div>'
            )

        # ══════════════════════════════════════════════════════
        # SLIDE 2: Dashboard completo — métricas + gráficos + tablas
        # Replica exactamente la vista del dashboard en Streamlit
        # ══════════════════════════════════════════════════════
        status_slide = ""
        graficos_slide = None
        try:
            import json as _json_g, html as _html_esc

            # ── Datos de métricas ──
            total_i = df_import["NOMBRE CORREO"].nunique() if not df_import.empty else 0
            n_pend_i = len(df_pend) if not df_pend.empty else 0
            n_arr_i  = len(df_arr)  if not df_arr.empty  else 0
            n_pend_asn_i = int(df_pend["ASNs"].sum()) if not df_pend.empty and "ASNs" in df_pend.columns else 0
            n_arr_asn_i  = int(df_arr["ASNs"].sum())  if not df_arr.empty  and "ASNs" in df_arr.columns  else 0

            # ── Datos para gráfico 1: por fecha ──
            _datos_fecha = []
            if not df_arr.empty and "Fecha Llegada" in df_arr.columns:
                _df_fch = df_arr.copy()
                _df_fch["_f"] = pd.to_datetime(_df_fch["Fecha Llegada"], errors="coerce")
                _df_fch = _df_fch.dropna(subset=["_f"]).sort_values("_f")
                for _, row in _df_fch.iterrows():
                    _datos_fecha.append({"x": str(row["Fecha Llegada"]), "y": int(row["ASNs"])})

            # ── Datos para gráfico 2: por importación ──
            _datos_imp = []
            if not df_arr.empty:
                for _, row in df_arr.iterrows():
                    _datos_imp.append({"x": str(row["Importación"]), "y": int(row["ASNs"])})

            _FECHA_ATTR = _html_esc.escape(_json_g.dumps(_datos_fecha), quote=True)
            _IMP_ATTR   = _html_esc.escape(_json_g.dumps(_datos_imp),   quote=True)

            # ── Tablas HTML (reutiliza _tbl del bloque anterior si existe, sino define inline) ──
            _SP = {
                "EN TRÁNSITO": ("#E6F1FB","#185FA5"), "EN TRANSITO": ("#E6F1FB","#185FA5"),
                "ORIGEN": ("#FAEEDA","#854F0B"), "SUPPLY": ("#EEEDFE","#534AB7"),
                "ADUANAS": ("#FAEEDA","#BA7517"),
            }
            def _tbl2(df, mx=15):
                df = df.head(mx)
                heads = "".join(
                    '<th style="padding:7px 12px;background:#1a7a4a;color:#fff;font-size:11px;'
                    'font-weight:700;text-align:left;position:sticky;top:0;z-index:1;font-size:15px;">' + str(c) + '</th>'
                    for c in df.columns
                )
                rows_html = ""
                for i, r in enumerate(df.values):
                    bg = "#ffffff" if i % 2 == 0 else "#f9fefb"
                    cells = ""
                    for ci, v in enumerate(r):
                        cn = df.columns[ci]
                        vs = str(v) if str(v) not in ("nan","None","") else "—"
                        if cn == "Estado" and vs.upper() in _SP:
                            pb,pf = _SP[vs.upper()]
                            cells += ('<td style="padding:6px 12px;border-bottom:1px solid #f0faf4;">'
                                      '<span style="background:'+pb+';color:'+pf+';padding:2px 8px;'
                                      'border-radius:20px;font-size:12px;font-weight:600;">'+vs+'</span></td>')
                        elif cn == "ASNs":
                            cells += ('<td style="padding:6px 12px;border-bottom:1px solid #f0faf4;'
                                      'text-align:right;font-weight:700;color:#1a7a4a;font-size:16px;">'+vs+'</td>')
                        elif cn in ("ETA","Fecha ETD","Fecha Llegada","FCH LLEGADA","HORA FECH"):
                            cells += ('<td style="padding:6px 12px;border-bottom:1px solid #f0faf4;'
                                      'color:#e8a020;font-weight:600;font-size:15px;">📅 '+vs+'</td>')
                        else:
                            cells += ('<td style="padding:6px 12px;border-bottom:1px solid #f0faf4;'
                                      'color:#2d3436;font-size:15px;">'+vs+'</td>')
                    rows_html += '<tr style="background:'+bg+';">'+cells+'</tr>'
                return ('<table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;">'
                        '<thead><tr>'+heads+'</tr></thead>'
                        '<tbody>'+rows_html+'</tbody></table>')

            _tbl_pend = _tbl2(df_pend) if not df_pend.empty else '<p style="color:#888;font-size:12px;padding:10px;">Sin pendientes</p>'
            _tbl_arr  = _tbl2(df_arr)  if not df_arr.empty  else '<p style="color:#888;font-size:12px;padding:10px;">Sin datos</p>'

            # Tabla de arribados: solo 6 filas visibles, el resto con scroll
            _tbl_arr_scroll = _tbl2(df_arr.head(6), mx=6) if not df_arr.empty else '<p style="color:#888;font-size:12px;padding:10px;">Sin datos</p>'

            status_slide = (
                # Outer: fondo completo del iframe
                '<div style="width:100%;height:100%;background:#f0faf4;display:flex;'
                'align-items:center;justify-content:center;font-family:Arial,sans-serif;box-sizing:border-box;overflow:hidden;">'
                # Inner: contenedor fijo 1160x740px — mismo tamaño siempre, no se estira
                '<div style="width:1500px;height:920px;display:flex;flex-direction:column;gap:10px;">'

                # ── Fila 1: 3 métricas — altura fija ──
                '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;height:100px;flex-shrink:0;">'
                + '<div style="background:#fff;border-radius:12px;border-top:4px solid #2d9e6b;padding:10px 16px;">'
                  '<div style="color:#aaa;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;">Total Importaciones</div>'
                  '<div style="color:#1a7a4a;font-size:2.8rem;font-weight:900;line-height:1.1;">'+str(total_i)+'</div>'
                  '</div>'
                + '<div style="background:#fff;border-radius:12px;border-top:4px solid #e8a020;padding:10px 16px;">'
                  '<div style="color:#aaa;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;">Pendientes de Arribo</div>'
                  '<div style="color:#e8a020;font-size:2.8rem;font-weight:900;line-height:1.1;">'+str(n_pend_i)+'</div>'
                  '<div style="color:#aaa;font-size:13px;">'+str(n_pend_asn_i)+' ASNs</div>'
                  '</div>'
                + '<div style="background:#fff;border-radius:12px;border-top:4px solid #1D9E75;padding:10px 16px;">'
                  '<div style="color:#aaa;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;">Arribados</div>'
                  '<div style="color:#1D9E75;font-size:2.8rem;font-weight:900;line-height:1.1;">'+str(n_arr_i)+'</div>'
                  '<div style="color:#aaa;font-size:13px;">'+str(n_arr_asn_i)+' ASNs</div>'
                  '</div>'
                + '</div>'

                # ── Fila 2: 2 gráficos — altura fija 230px ──
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;height:310px;flex-shrink:0;">'
                '<div style="background:#fff;border-radius:12px;padding:10px 14px;display:flex;flex-direction:column;">'
                '<div style="font-size:15px;font-weight:700;color:#1a7a4a;margin-bottom:4px;">📅 ASNs por fecha de llegada</div>'
                '<div id="ppt-gchart-fecha" data-chart="bar" data-color="#1D9E75" data-points="'+_FECHA_ATTR+'" data-w="720" data-h="255"></div>'
                '</div>'
                '<div style="background:#fff;border-radius:12px;padding:10px 14px;display:flex;flex-direction:column;">'
                '<div style="font-size:15px;font-weight:700;color:#1a7a4a;margin-bottom:4px;">📦 ASNs por importación</div>'
                '<div id="ppt-gchart-imp" data-chart="bar" data-color="#378ADD" data-points="'+_IMP_ATTR+'" data-w="720" data-h="255"></div>'
                '</div>'
                '</div>'

                # ── Fila 3: 2 tablas — altura fija, solo arribados con scroll ──
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;flex:1;min-height:0;">'

                # Tabla pendientes — sin scroll (pocos registros)
                '<div style="background:#fff;border-radius:12px;padding:10px 14px;overflow:hidden;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                '<span style="font-size:16px;font-weight:700;color:#1a7a4a;">⏳ Pendientes de Arribo</span>'
                '<span style="background:#FAEEDA;color:#854F0B;padding:2px 8px;border-radius:20px;font-size:13px;font-weight:600;">' 
                +str(n_pend_i)+' importaciones · '+str(n_pend_asn_i)+' ASNs</span></div>'
                + _tbl_pend +
                '</div>'

                # Tabla arribados — con scroll, altura fija
                '<div style="background:#fff;border-radius:12px;padding:10px 14px;display:flex;flex-direction:column;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-shrink:0;">'
                '<span style="font-size:16px;font-weight:700;color:#1a7a4a;">✅ Arribados</span>'
                '<span style="background:#EAF3DE;color:#3B6D11;padding:2px 8px;border-radius:20px;font-size:13px;font-weight:600;">' 
                +str(n_arr_i)+' importaciones · '+str(n_arr_asn_i)+' ASNs</span></div>'
                '<div style="overflow-y:auto;flex:1;">'+_tbl_arr_scroll+'</div>'
                '</div>'

                '</div>'  # fila 3
                '</div>'  # inner fixed
                '</div>'  # outer
            )

        except Exception as _eg_s:
            status_slide = ""

        slides_imp = []
        if apertura_slide:
            slides_imp.append(("🏪 Próximas Aperturas", apertura_slide))
        if status_slide:
            slides_imp.append(("📊 Status Global Importaciones", status_slide))

        if slides_imp:
            mostrar_seccion_ppt("📦 Importaciones", slides_imp)

    # tab_recep oculto (modo pantalla)

    with tab_ops:
        st.markdown('<div class="titulo-seccion">⚙️ Operaciones</div>', unsafe_allow_html=True)

        col_arr, col_stk = st.columns(2)

        # ── CONFIRMAR ARRIBO ──────────────────────────────────────────────
        with col_arr:
            st.markdown("""
            <div style="background:#fff;border-radius:14px;border-top:5px solid #2d9e6b;
                        padding:20px 22px;box-shadow:0 2px 10px rgba(45,158,107,0.1);">
                <div style="color:#1a7a4a;font-size:1.1rem;font-weight:700;margin-bottom:4px;">
                    🚢 Confirmar Arribo de Importación
                </div>
                <div style="color:#636e72;font-size:0.85em;">
                    Solo aparecen las importaciones pendientes (sin registro en Recepción aún).
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

            # Importaciones pendientes = en consolidado y NO en recepción
            imp_en_rec = set()
            if not df_recep.empty and "IMPORTACION" in df_recep.columns:
                imp_en_rec = set(df_recep["IMPORTACION"].astype(str).str.strip().str.lower())

            docs_pendientes = []
            if not df_import.empty and "NOMBRE CORREO" in df_import.columns:
                col_rec3 = next((c for c in df_import.columns if c.upper() == "RECUENTO"), None)
                df_base3 = df_import[df_import[col_rec3].isin(["1","1.0"])].copy() if col_rec3 else df_import.copy()
                docs_pendientes = sorted(set(
                    df_base3[~df_base3["NOMBRE CORREO"].astype(str).str.strip().str.lower().isin(imp_en_rec)]
                    ["NOMBRE CORREO"].astype(str).str.strip().tolist()
                ))

            if not docs_pendientes:
                st.success("✅ No hay importaciones pendientes de arribo.")
            else:
                with st.form("form_arribo", clear_on_submit=True):
                    doc_sel = st.selectbox(f"📋 Importación ({len(docs_pendientes)} pendientes)", docs_pendientes)

                    asns_doc = []
                    if doc_sel and "ASN" in df_import.columns and col_rec3:
                        asns_doc = sorted(
                            df_base3[df_base3["NOMBRE CORREO"].astype(str).str.strip() == doc_sel]
                            ["ASN"].astype(str).str.strip().tolist()
                        )

                    asns_sel = st.multiselect(
                        f"📦 ASNs ({len(asns_doc)} disponibles)",
                        options=["TODAS"] + asns_doc,
                        default=["TODAS"]
                    )
                    fecha_arr = st.date_input("📅 Fecha de llegada", date.today())

                    if st.form_submit_button("✅ Registrar Arribo", use_container_width=True):
                        if update_consolidado_arribo(doc_sel, fecha_arr, asns_sel):
                            st.toast(f"¡Arribo de {doc_sel} registrado!", icon="✅")
                            st.cache_data.clear()
                            st.rerun()

        # ── CONFIRMAR ALMACENAMIENTO ──────────────────────────────────────
        with col_stk:
            st.markdown("""
            <div style="background:#fff;border-radius:14px;border-top:5px solid #3dbb7e;
                        padding:20px 22px;box-shadow:0 2px 10px rgba(45,158,107,0.1);">
                <div style="color:#1a7a4a;font-size:1.1rem;font-weight:700;margin-bottom:4px;">
                    🏢 Confirmar Ingreso a Stock
                </div>
                <div style="color:#636e72;font-size:0.85em;">
                    ASNs en Recepción con STATUS_REC=Pendiente y TIENDA=4298.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

            # Recepción pendiente de almacenamiento: STATUS_REC=Pendiente y TIENDA=4298
            df_recep_stk = pd.DataFrame()
            if not df_recep.empty and "STATUS_REC" in df_recep.columns and "ASN" in df_recep.columns:
                mask_stk = df_recep["STATUS_REC"].astype(str).str.strip().str.upper() == "PENDIENTE"
                if "TIENDA" in df_recep.columns:
                    mask_stk = mask_stk & (df_recep["TIENDA"].astype(str).str.strip() == "4298")
                df_recep_stk = df_recep[mask_stk].copy()

            # Importaciones disponibles (las que tienen ASNs pendientes de stock)
            imps_stk = []
            if not df_recep_stk.empty and "IMPORTACION" in df_recep_stk.columns:
                imps_stk = sorted(df_recep_stk["IMPORTACION"].astype(str).str.strip().unique().tolist())

            if df_recep_stk.empty or not imps_stk:
                st.success("✅ No hay ASNs pendientes de almacenamiento.")
            else:
                # Selector de importación fuera del form para filtrar ASNs dinámicamente
                imp_stk_sel = st.selectbox(
                    f"📋 Importación ({len(imps_stk)} disponibles)",
                    imps_stk,
                    key="sel_imp_stk"
                )

                # Filtrar ASNs según importación seleccionada
                asns_almacen = []
                if imp_stk_sel:
                    asns_almacen = sorted(
                        df_recep_stk[
                            df_recep_stk["IMPORTACION"].astype(str).str.strip() == imp_stk_sel
                        ]["ASN"].astype(str).str.strip().tolist()
                    )

                with st.form("form_stock", clear_on_submit=True):
                    asns_stk = st.multiselect(
                        f"📦 ASNs ({len(asns_almacen)} disponibles)",
                        options=["TODAS"] + asns_almacen,
                        default=["TODAS"]
                    )
                    fecha_stk = st.date_input("📅 Fecha de ingreso", date.today())

                    if st.form_submit_button("🏢 Confirmar Ingreso a Stock", use_container_width=True):
                        try:
                            sh_r  = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
                            w_m   = sh_r.worksheet("MOVIMIENTOS")
                            lista = asns_almacen if "TODAS" in asns_stk else [a for a in asns_stk if a != "TODAS"]
                            errores = []
                            for asn in lista:
                                try:
                                    cell = w_m.find(str(asn))
                                    w_m.update_cell(cell.row, 6, "ALMACENADO")
                                    w_m.update_cell(cell.row, 7, str(fecha_stk))
                                except Exception:
                                    errores.append(asn)
                            if errores:
                                st.warning(f"No se encontraron: {errores}")
                            else:
                                st.toast(f"{len(lista)} ASN(s) de {imp_stk_sel} confirmados en stock ✅", icon="🏢")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

# MENÚ DISTRIBUCIÓN oculto (modo pantalla)

# ----------------------------------------------------------
# MENÚ: DASH DESPACHOS
# ----------------------------------------------------------
if menu == "📊 Dash Despachos":
    render_dash_despachos()

# ----------------------------------------------------------
# MENÚ: INDICADORES DE ALMACÉN
# ----------------------------------------------------------
if menu == "📋 Indicadores de Almacén":
    import plotly.graph_objects as go

    # ── Título sección ─────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
      <div style="background:linear-gradient(135deg,#1a7a4a,#2d9e6b);border-radius:10px;
                  padding:10px 16px;">
        <span style="color:#fff;font-size:24px;">📋</span>
      </div>
      <div>
        <div style="font-size:28px;font-weight:900;color:#1a7a4a;">Indicadores de Almacén</div>
        <div style="font-size:14px;color:#aaa;font-weight:500;">LA CARCASA MOVIL · Inventario Cíclico</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    df_carc = cargar_historial_carcasa()

    if df_carc.empty:
        st.warning("⚠️ Sin datos en el historial de Carcasas.")
    else:
        # ── Filtros ────────────────────────────────────────────────────────
        import datetime as _dt
        _min_fecha = df_carc["Fecha"].min().date() if "Fecha" in df_carc.columns and len(df_carc) > 0 else _dt.date.today()
        _max_fecha = df_carc["Fecha"].max().date() if "Fecha" in df_carc.columns and len(df_carc) > 0 else _dt.date.today()

        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            fecha_ini = st.date_input("📅 Fecha inicio", value=_min_fecha,
                                      min_value=_min_fecha, max_value=_max_fecha, key="ind_fini")
        with col_f2:
            fecha_fin = st.date_input("📅 Fecha fin", value=_max_fecha,
                                      min_value=_min_fecha, max_value=_max_fecha, key="ind_ffin")
        with col_f3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Actualizar", key="ind_refresh"):
                st.cache_data.clear()
                st.rerun()

        # Aplicar filtro de rango de fechas
        import pandas as _pd_f
        df = df_carc.copy()
        if "Fecha" in df.columns:
            df = df[(df["Fecha"].dt.date >= fecha_ini) & (df["Fecha"].dt.date <= fecha_fin)]
        mes_sel = f"{fecha_ini.strftime('%d/%m/%Y')} — {fecha_fin.strftime('%d/%m/%Y')}"

        contados = df[df["Estado"] != "⏳ Pendiente"] if "Estado" in df.columns else df

        # ── Calcular indicadores ───────────────────────────────────────────
        ok_ubic       = (contados["Estado"] == "✅ OK").sum() if "Estado" in contados.columns else 0
        total_contados= len(contados)
        eru           = (ok_ubic / total_contados * 100) if total_contados > 0 else 0

        eri = 0; skus_ok = 0; total_skus = 0
        if "Código SKU" in contados.columns and "Contado" in contados.columns and len(contados) > 0:
            por_sku = contados.groupby("Código SKU").agg(
                total_contado=("Contado", "sum"),
                total_wms=("Stock WMS", "sum"),
            ).reset_index()
            por_sku = por_sku[por_sku["total_wms"] > 0]
            por_sku["eri_val"] = (1 - (por_sku["total_contado"] - por_sku["total_wms"]).abs() / por_sku["total_wms"]).clip(lower=0)
            total_skus = len(por_sku)
            skus_ok    = (por_sku["eri_val"] >= 0.95).sum()
            eri        = por_sku["eri_val"].mean() * 100 if total_skus > 0 else 0

        aj_pos = contados[contados["Diferencia"] > 0]["Diferencia"].sum() if "Diferencia" in contados.columns else 0
        aj_neg = contados[contados["Diferencia"] < 0]["Diferencia"].sum() if "Diferencia" in contados.columns else 0

        # ── KPIs — diseño tipo tarjeta con ícono ──────────────────────────
        eru_color = "#2d9e6b" if eru >= 85 else ("#e8a020" if eru >= 60 else "#c0392b")
        eri_color = "#2d9e6b" if eri >= 85 else ("#e8a020" if eri >= 60 else "#c0392b")

        def _kpi2(col, icon, label, formula, value, sub, color, bg):
            col.markdown(f"""
            <div style="background:{bg};border-radius:14px;padding:18px 20px;
                        border-left:5px solid {color};box-shadow:0 3px 12px rgba(0,0,0,0.07);
                        min-height:130px;display:flex;flex-direction:column;justify-content:space-between;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:22px;">{icon}</span>
                <div>
                  <div style="font-size:15px;font-weight:900;color:{color};text-transform:uppercase;
                              letter-spacing:.6px;">{label}</div>
                  <div style="font-size:11px;color:#aaa;">{formula}</div>
                </div>
              </div>
              <div style="font-size:34px;font-weight:900;color:{color};line-height:1;">{value}</div>
              <div style="font-size:12px;color:#888;margin-top:6px;padding-top:6px;
                          border-top:1px solid rgba(0,0,0,0.06);">{sub}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        _kpi2(k1, "✅", "ERI", "SKU correctos / Total auditados × 100",
              f"{eri:.1f}%", f"{skus_ok} de {total_skus} SKUs ≥ 95%", eri_color, "#f0faf4")
        _kpi2(k2, "📍", "ERU", "Ubicaciones correctas / Total auditadas × 100",
              f"{eru:.1f}%", f"{ok_ubic} OK de {total_contados} contados", eru_color, "#f0faf4")
        _kpi2(k3, "📈", "Ajustes Positivos", "Suma unidades sobrantes",
              f"+{int(aj_pos):,}", "unidades contadas de más vs WMS", "#1a7a4a", "#f0faf4")
        _kpi2(k4, "📉", "Ajustes Negativos", "Suma unidades faltantes",
              f"{int(aj_neg):,}", "unidades contadas de menos vs WMS", "#c0392b", "#fff5f5")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Gráfico de estados ─────────────────────────────────────────────
        if len(contados) > 0 and "Estado" in contados.columns:
            st.markdown("""
            <div style="font-size:14px;font-weight:700;color:#1a7a4a;
                        margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #c8e06a;">
              📊 Distribución de resultados
            </div>""", unsafe_allow_html=True)

            g1, g2 = st.columns([1, 2])

            with g1:
                # ERI evolutivo (línea)
                if "Fecha" in contados.columns and "Código SKU" in contados.columns and len(contados) > 0:
                    import pandas as _pd2
                    _ev2 = []
                    for _d, _grp in contados.groupby(contados["Fecha"].dt.date):
                        _ps = _grp.groupby("Código SKU").agg(tc=("Contado","sum"),tw=("Stock WMS","sum")).reset_index()
                        _ps = _ps[_ps["tw"]>0]
                        _ps["e"] = (1-(_ps["tc"]-_ps["tw"]).abs()/_ps["tw"]).clip(lower=0)
                        _ev2.append({"Fecha":_d,"ERI":round(_ps["e"].mean()*100,1) if len(_ps)>0 else 0})
                    _df_eri = _pd2.DataFrame(_ev2)

                    fig_eri_line = go.Figure()
                    fig_eri_line.add_trace(go.Scatter(
                        x=_df_eri["Fecha"], y=_df_eri["ERI"],
                        mode="lines+markers+text",
                        line=dict(color="#1a7a4a", width=2.5),
                        marker=dict(color="#1a7a4a", size=7),
                        text=_df_eri["ERI"].apply(lambda v: f"{v:.1f}%"),
                        textposition="top center",
                        textfont=dict(size=10, color="#1a7a4a"),
                        hovertemplate="<b>%{x}</b><br>ERI: %{y:.1f}%<extra></extra>",
                    ))
                    fig_eri_line.update_layout(
                        height=240,
                        xaxis=dict(gridcolor="#e8f5ee", color="#888", title=""),
                        yaxis=dict(title="ERI %", range=[0, 110], ticksuffix="%",
                                   gridcolor="#e8f5ee", color="#888"),
                        plot_bgcolor="white", paper_bgcolor="white",
                        font=dict(family="Arial", size=11),
                        showlegend=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig_eri_line, use_container_width=True, key="eri_linea")
                else:
                    st.info("Sin datos suficientes para ERI evolutivo.")

            with g2:
                # Evolución diaria si hay fechas
                if "Fecha" in contados.columns:
                    ev = contados.groupby(contados["Fecha"].dt.date).agg(
                        Contados=("Estado", "count"),
                        OK=("Estado", lambda x: (x == "✅ OK").sum()),
                    ).reset_index()
                    ev.columns = ["Fecha", "Contados", "OK"]
                    ev["ERU %"] = (ev["OK"] / ev["Contados"] * 100).round(1)

                    fig_ev = go.Figure()
                    fig_ev.add_trace(go.Scatter(
                        x=ev["Fecha"], y=ev["ERU %"],
                        name="ERU %",
                        mode="lines+markers+text",
                        line=dict(color="#2d9e6b", width=2.5),
                        marker=dict(color="#2d9e6b", size=7,
                                    line=dict(color="#fff", width=1.5)),
                        text=ev["ERU %"].apply(lambda v: f"{v:.1f}%"),
                        textposition="top center",
                        textfont=dict(size=10, color="#2d9e6b"),
                        hovertemplate="<b>%{x}</b><br>ERU: %{y:.1f}%<extra></extra>",
                    ))
                    fig_ev.update_layout(
                        height=240,
                        xaxis=dict(gridcolor="#e8f5ee", color="#888", title="", showgrid=False),
                        yaxis=dict(title="ERU %", range=[0, 110], ticksuffix="%",
                                   gridcolor="#e8f5ee", color="#888"),
                        plot_bgcolor="white", paper_bgcolor="white",
                        font=dict(family="Arial", size=11),
                        showlegend=False,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig_ev, use_container_width=True, key="evol_eru")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Top SKUs con ajuste ─────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:14px;font-weight:700;color:#1a7a4a;
                    margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #c8e06a;">
          ⚠️ SKUs con mayor diferencia
        </div>""", unsafe_allow_html=True)

        if "Código SKU" in contados.columns and len(contados) > 0:
            df_aj = contados[contados["Estado"].isin(["❌ Ajuste", "⚠ Revisar"])].copy()
            if df_aj.empty:
                st.success("✅ No hay SKUs con ajustes en el período seleccionado.")
            else:
                top_aj = df_aj.groupby(["Código SKU", "Descripción"]).agg(
                    Total_WMS=("Stock WMS", "sum"),
                    Total_contado=("Contado", "sum"),
                    Diferencia_total=("Diferencia", "sum"),
                    Veces=("Estado", "count"),
                ).reset_index()
                top_aj["ERI %"] = ((1 - top_aj["Diferencia_total"].abs() / top_aj["Total_WMS"].replace(0, 1)).clip(lower=0) * 100).round(1)
                top_aj = top_aj.sort_values("Diferencia_total", key=abs, ascending=False).head(10)
                top_aj.columns = ["Código SKU", "Descripción", "Stock WMS", "Contado", "Diferencia", "Veces ajuste", "ERI %"]
                st.dataframe(
                    top_aj, use_container_width=True, hide_index=True,
                    column_config={
                        "Stock WMS"   : st.column_config.NumberColumn(format="%d"),
                        "Contado"     : st.column_config.NumberColumn(format="%d"),
                        "Diferencia"  : st.column_config.NumberColumn(format="%+d"),
                        "Veces ajuste": st.column_config.NumberColumn(format="%d"),
                        "ERI %"       : st.column_config.NumberColumn(format="%.1f%%"),
                    }
                )

        # ── BOTÓN PRESENTACIÓN INDICADORES ────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        _KEY_PPT = "ppt_indicadores"
        _KEY_HTML = "ppt_indicadores_html"
        if _KEY_PPT not in st.session_state:
            st.session_state[_KEY_PPT] = False

        _lbl = "⬇️ Cerrar presentación" if st.session_state[_KEY_PPT] else "🖥️ Ver presentación: Indicadores de Almacén"
        if st.button(_lbl, key="btn_ppt_ind"):
            st.session_state[_KEY_PPT] = not st.session_state[_KEY_PPT]
            if st.session_state[_KEY_PPT]:
                import plotly.io as _pio, json as _json

                # Calcular ERI evolutivo
                _eri_dates, _eri_vals = [], []
                _eru_dates, _eru_vals = [], []
                if "Fecha" in contados.columns and len(contados) > 0:
                    _ev = contados.groupby(contados["Fecha"].dt.date).agg(
                        Contados=("Estado","count"),
                        OK=("Estado", lambda x: (x=="✅ OK").sum()),
                    ).reset_index()
                    _ev.columns = ["Fecha","Contados","OK"]
                    _ev["ERU"] = (_ev["OK"]/_ev["Contados"]*100).round(1)
                    _eru_dates = [str(d) for d in _ev["Fecha"]]
                    _eru_vals  = _ev["ERU"].tolist()

                if "Fecha" in contados.columns and "Código SKU" in contados.columns and len(contados) > 0:
                    _ev2 = []
                    for _d, _grp in contados.groupby(contados["Fecha"].dt.date):
                        _ps = _grp.groupby("Código SKU").agg(tc=("Contado","sum"),tw=("Stock WMS","sum")).reset_index()
                        _ps = _ps[_ps["tw"]>0]
                        _ps["e"] = (1-(_ps["tc"]-_ps["tw"]).abs()/_ps["tw"]).clip(lower=0)
                        _ev2.append({"d":str(_d),"e":round(_ps["e"].mean()*100,1) if len(_ps)>0 else 0})
                    _eri_dates = [x["d"] for x in _ev2]
                    _eri_vals  = [x["e"] for x in _ev2]

                # Logos b64
                _lc = _b64_img("CARCASAS.png")
                _lcf= _b64_img("CARGOFLEX.png")
                _img_c  = f'data:image/png;base64,{_lc}' if _lc else ""
                _img_cf2= f'data:image/png;base64,{_lcf}' if _lcf else ""

                # Colores semáforo
                _ec = "#2d9e6b" if eri>=85 else ("#e8a020" if eri>=60 else "#c0392b")
                _uc = "#2d9e6b" if eru>=85 else ("#e8a020" if eru>=60 else "#c0392b")

                _html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;}}
html,body{{width:100%;height:100%;background:#f0faf4;overflow:hidden;}}
/* Layout: 3 tercios verticales — header / KPIs / gráficos */
#wrap{{
  width:100vw;height:100vh;display:flex;flex-direction:column;
  padding:12px 20px 10px;gap:8px;background:#f4fbf7;
  overflow:hidden;
}}
/* TERCIO 1 — HEADER ~28vh */
#hdr{{
  display:flex;align-items:center;justify-content:space-between;
  background:#fff;border-radius:14px;padding:0 28px;
  border-bottom:5px solid #c8e06a;
  box-shadow:0 2px 12px rgba(26,122,74,0.1);
  flex:0 0 calc(28vh - 16px);
}}
#hdr img{{height:60%;max-height:80px;object-fit:contain;}}
#hdr-mid{{text-align:center;flex:1;padding:0 24px;}}
#hdr-mid .title{{color:#1a7a4a;font-size:clamp(1.1rem,2.2vh,1.8rem);font-weight:900;letter-spacing:.2px;}}
#hdr-mid .sub{{color:#aaa;font-size:clamp(10px,1.4vh,14px);font-weight:500;margin-top:4px;}}
/* TERCIO 2 — KPIs ~28vh */
#kpi-row{{
  display:grid;grid-template-columns:repeat(4,1fr);gap:10px;
  flex:0 0 calc(28vh - 16px);
}}
.kpi-card{{
  background:#fff;border-radius:14px;padding:clamp(10px,1.5vh,20px) clamp(12px,1.8vh,22px);
  border-left:6px solid #2d9e6b;
  box-shadow:0 3px 12px rgba(0,0,0,0.06);
  display:flex;flex-direction:column;justify-content:space-between;
  overflow:hidden;
}}
.kpi-top{{display:flex;align-items:center;gap:8px;}}
.kpi-icon{{font-size:clamp(16px,2vh,22px);}}
.kpi-name{{font-size:clamp(9px,1.2vh,13px);font-weight:800;text-transform:uppercase;letter-spacing:.6px;color:#888;}}
.kpi-formula{{font-size:clamp(8px,1vh,10px);color:#ccc;margin-top:2px;}}
.kpi-val{{font-size:clamp(24px,4vh,44px);font-weight:900;line-height:1;margin-top:4px;}}
.kpi-sub{{font-size:clamp(9px,1.1vh,12px);color:#bbb;padding-top:5px;border-top:1px solid #f0f0f0;}}
/* TERCIO 3 — GRÁFICOS ~44vh */
#charts-row{{
  display:grid;grid-template-columns:1fr 1fr;gap:10px;
  flex:1 1 auto;min-height:0;
}}
.chart-card{{
  background:#fff;border-radius:14px;padding:12px 18px 6px;
  box-shadow:0 3px 12px rgba(0,0,0,0.06);
  display:flex;flex-direction:column;border-top:3px solid #c8e06a;
  overflow:hidden;
}}
.chart-title{{font-size:clamp(11px,1.5vh,15px);font-weight:800;color:#1a7a4a;margin-bottom:2px;flex-shrink:0;}}
.chart-sub{{font-size:clamp(9px,1vh,11px);color:#bbb;margin-bottom:4px;flex-shrink:0;}}
.chart-div{{flex:1;min-height:0;}}
/* BTN FULLSCREEN */
#fsb{{
  position:fixed;bottom:14px;right:18px;
  background:linear-gradient(135deg,#1a7a4a,#2d9e6b);
  border:none;border-radius:10px;padding:8px 20px;
  font-size:13px;font-weight:700;color:#fff;cursor:pointer;
  box-shadow:0 4px 14px rgba(26,122,74,0.35);z-index:9999;
}}
#fsb:hover{{opacity:.9;}}
</style>
</head>
<body>
<div id="wrap">

  <!-- HEADER -->
  <div id="hdr">
    <div>{"<img src='" + _img_c + "' />" if _img_c else ""}</div>
    <div id="hdr-mid">
      <div class="title">📋 Indicadores de Almacén — LA CARCASA MOVIL</div>
      <div class="sub">Inventario Cíclico · Cargoflex Supply · {mes_sel}</div>
    </div>
    <div>{"<img src='" + _img_cf2 + "' />" if _img_cf2 else ""}</div>
  </div>

  <!-- KPI ROW -->
  <div id="kpi-row">
    <div class="kpi-card" style="border-left-color:{_ec};">
      <div class="kpi-top">
        <span class="kpi-icon">✅</span>
        <div><div class="kpi-name">ERI — Exactitud Inventario</div>
          <div class="kpi-formula">SKU correctos / Total auditados × 100</div></div>
      </div>
      <div class="kpi-val" style="color:{_ec};">{eri:.1f}%</div>
      <div class="kpi-sub">{skus_ok} de {total_skus} SKUs ≥ 95%</div>
    </div>
    <div class="kpi-card" style="border-left-color:{_uc};">
      <div class="kpi-top">
        <span class="kpi-icon">📍</span>
        <div><div class="kpi-name">ERU — Exactitud Ubicaciones</div>
          <div class="kpi-formula">Ubicaciones correctas / Total auditadas × 100</div></div>
      </div>
      <div class="kpi-val" style="color:{_uc};">{eru:.1f}%</div>
      <div class="kpi-sub">{ok_ubic} OK de {total_contados} contados</div>
    </div>
    <div class="kpi-card" style="border-left-color:#2d9e6b;">
      <div class="kpi-top">
        <span class="kpi-icon">📈</span>
        <div><div class="kpi-name">Ajustes Positivos</div>
          <div class="kpi-formula">Suma unidades sobrantes vs WMS</div></div>
      </div>
      <div class="kpi-val" style="color:#2d9e6b;">+{int(aj_pos):,}</div>
      <div class="kpi-sub">unidades contadas de más</div>
    </div>
    <div class="kpi-card" style="border-left-color:#c0392b;background:#fff8f8;">
      <div class="kpi-top">
        <span class="kpi-icon">📉</span>
        <div><div class="kpi-name">Ajustes Negativos</div>
          <div class="kpi-formula">Suma unidades faltantes vs WMS</div></div>
      </div>
      <div class="kpi-val" style="color:#c0392b;">{int(aj_neg):,}</div>
      <div class="kpi-sub">unidades contadas de menos</div>
    </div>
  </div>

  <!-- CHARTS ROW -->
  <div id="charts-row">
    <div class="chart-card">
      <div class="chart-title">📊 ERI — Exactitud de Inventario por SKU</div>
      <div class="chart-sub">Evolución diaria · SKU correctos / Total auditados × 100</div>
      <div class="chart-div" id="chart-eri"></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">📊 ERU — Exactitud de Registro de Ubicaciones</div>
      <div class="chart-sub">Evolución diaria · Ubicaciones correctas / Total auditadas × 100</div>
      <div class="chart-div" id="chart-eru"></div>
    </div>
  </div>

</div>

<button id="fsb" onclick="toggleFS()">⛶ Pantalla completa</button>

<script>
var eriDates = {_json.dumps(_eri_dates)};
var eriVals  = {_json.dumps(_eri_vals)};
var eruDates = {_json.dumps(_eru_dates)};
var eruVals  = {_json.dumps(_eru_vals)};

function mkChart(divId, dates, vals, color, label) {{
  var el = document.getElementById(divId);
  if (!el || !dates.length) return;
  var W = el.clientWidth || 500;
  var H = el.clientHeight || 220;
  // Etiquetas solo en algunos puntos para no saturar
  var textArr = vals.map(function(v,i) {{
    return (i===0 || i===vals.length-1 || i%Math.max(1,Math.floor(vals.length/5))===0)
      ? v.toFixed(1)+"%" : "";
  }});
  Plotly.newPlot(divId, [
    {{
      type: "scatter", mode: "lines+markers+text",
      x: dates, y: vals,
      name: label,
      line: {{color: color, width: 3, shape:"spline", smoothing:0.4}},
      marker: {{color: color, size: 7, symbol:"circle",
               line:{{color:"#fff",width:1.5}}}},
      text: textArr,
      textposition: "top center",
      textfont: {{size:11, color:color, family:"Segoe UI,Arial"}},
      hovertemplate: "<b>%{{x}}</b><br>" + label + ": %{{y:.1f}}%<extra></extra>",
      cliponaxis: false
    }}
  ], {{
    autosize: false, width: W, height: H,
    paper_bgcolor: "#ffffff", plot_bgcolor: "#fafffe",
    margin: {{l:48,r:20,t:20,b:58}},
    font: {{family:"Segoe UI,Arial", size:11, color:"#444"}},
    xaxis: {{
      showgrid:false, tickfont:{{size:10,color:"#888"}},
      tickangle:-30, zeroline:false,
      linecolor:"#e0e0e0", linewidth:1
    }},
    yaxis: {{
      range:[Math.max(0,Math.min.apply(null,vals)-10), 105],
      ticksuffix:"%", gridcolor:"#f0f7f4",
      tickfont:{{size:10,color:"#888"}},
      zeroline:false, linecolor:"#e0e0e0", linewidth:1
    }},
    shapes: [],
    annotations: []
  }}, {{displayModeBar:false, responsive:false}});
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
            _comp.html(st.session_state[_KEY_HTML], height=820, scrolling=False)

# ----------------------------------------------------------
# SINCRONIZAR
# ----------------------------------------------------------
if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear(); st.rerun()
