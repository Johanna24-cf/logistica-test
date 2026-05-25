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

# 🌟 INICIALIZACIÓN PREVENTIVA DE SESSION STATE PARA EVITAR ERRORES DE PRESENTACIÓN PPT
if "ppt_Dashboard_de_Despachos" not in st.session_state:
    st.session_state["ppt_Dashboard_de_Despachos"] = False

if "ppt_Importaciones" not in st.session_state:
    st.session_state["ppt_Importaciones"] = False


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
            color: #1a7a4a;
            font-weight: bold; font-size: 1.5rem;
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
            width: 100%;
            display: flex;
            align-items: center; justify-content: space-between;
            margin-bottom: 18px;
        }
        #ppt-header img { height: 56px; object-fit: contain; }
        #ppt-titulo {
            color: #c8e06a;
            font-size: 1.8rem; font-weight: 700;
            text-align: center; flex: 1; padding: 0 24px;
            font-family: Arial, sans-serif;
        }
        #ppt-body { width: 100%; flex: 1; min-height: 0; }
        #ppt-body iframe {
            width: 100%;
            height: 100%; border: none;
            border-radius: 12px; background: #0d1f16;
        }
        #ppt-cerrar {
            position: absolute;
            top: 16px; right: 24px;
            background: transparent; border: 2px solid #c8e06a;
            color: #c8e06a; border-radius: 8px;
            padding: 6px 16px; font-size: 14px;
            font-weight: 700;
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
    """Logo CARGOFLEX alineado a la derecha, misma altura que logo izquierdo."""
    nombre = "CARGOFLEX.png"
    if os.path.exists(nombre):
        with open(nombre, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    
        st.markdown(
            f'''<div style="
                position: fixed;
                top: 80px;
                right: 32px;
                z-index: 99999;
                background: transparent;
            ">
                <img src="data:image/png;base64,{b64}"
                     width="250"
                     style="image-rendering: -webkit-optimize-contrast;
                            image-rendering: crisp-edges;
                            max-width: 250px;">
            </div>''',
            unsafe_allow_html=True,
        )


cargar_estilos()
mostrar_logo_izquierdo()
mostrar_logo_cf_derecha()


# 3. CONEXIÓN Y CARGA
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

client = conectar_google()

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
    if not df_import_raw.empty and "RECUENTO" in df_import_raw.columns:
        df_import_filtered = df_import_raw[df_import_raw["RECUENTO"].isin(["1", "1.0"])].copy()
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

    slides = [(t, f) for t, f in slides if f is not None]
    if not slides:
        return

    logo_izq, logo_der = _logos_b64()
    import re as _re2
    sid = "s" + _re2.sub(r'[^a-zA-Z0-9]', '_', titulo_seccion)[:20]
    logo_izq_tag = f'<img src="{logo_izq}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_izq else ""
    logo_der_tag = f'<img src="{logo_der}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_der else ""

    slides_js_parts = []
    import json as _json
    for t, f in slides:
        if isinstance(f, str):
            slides_js_parts.append('{"titulo":' + _json.dumps(t) + ',"tipo":"html","content":' + _json.dumps(f) + '}')
        else:
            fig_json = pio.to_json(f)
            slides_js_parts.append('{"titulo":' + _json.dumps(t) + ',"tipo":"plotly","fig":' + fig_json + '}')
    slides_js = "[" + ",".join(slides_js_parts) + "]"

    html_completo = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html, body {{ width:100%; height:100%; background:#f0faf4; font-family:Arial,sans-serif; overflow:hidden; }}
  #wrap {{
    width:100%; height:100vh; display:flex; flex-direction:column;
    padding:10px 20px 10px; gap:8px;
  }}
  /* HEADER */
  #hdr {{
    display:flex; align-items:center; justify-content:space-between;
    background:#fff; border-radius:12px;
    border:2px solid #2d9e6b;
    padding:8px 20px; flex-shrink:0;
  }}
  .logo-w {{ width:190px; display:flex; align-items:center; }}
  .logo-w.r {{ justify-content:flex-end; }}
  #titulo {{
    color:#1a7a4a; font-size:1.5rem; font-weight:800;
    text-align:center; flex:1; padding:0 10px;
  }}
  /* PROGRESO */
  #pw {{ width:100%; height:5px; background:#c8e06a; border-radius:3px; flex-shrink:0; }}
  #pb {{ height:5px; background:#1a7a4a; border-radius:3px; width:0%; transition:width 0.05s linear; }}
  /* CUERPO con marco */
  #body {{
    flex:1; min-height:0; border:3px solid #2d9e6b; border-radius:14px;
    background:#fff; overflow:hidden;
    display:flex; align-items:stretch;
  }}
  #plt-div {{ width:100%; height:100%; }}
  #html-div {{ width:100%; height:100%; overflow-y:auto; overflow-x:hidden; display:none; }}
  /* FOOTER */
  #footer {{
    display:flex; align-items:center; justify-content:space-between;
    background:#fff; border-radius:12px; border:2px solid #c8e06a;
    padding:6px 16px; flex-shrink:0;
  }}
  #dots {{ display:flex; gap:8px; align-items:center; }}
  #dots span {{
    width:10px; height:10px; border-radius:50%;
    display:inline-block; cursor:pointer;
    background:#c8e06a; border:2px solid #2d9e6b;
    transition:all 0.25s;
  }}
  #dots span.on {{ background:#1a7a4a; transform:scale(1.35); }}
  #ctr {{ color:#636e72; font-size:12px; font-weight:700; }}
  #nav {{ display:flex; gap:8px; }}
  #nav button {{
    background:#fff; border:2px solid #2d9e6b; color:#2d9e6b;
    border-radius:6px; padding:4px 14px; font-size:13px;
    font-weight:700; cursor:pointer; transition:all 0.2s;
  }}
  #nav button:hover {{ background:#2d9e6b; color:#fff; }}
  #fsb {{
    background:linear-gradient(135deg,#2d9e6b,#c8e06a) !important;
    color:#0d1f16 !important; border:none !important;
  }}
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

function goTo(i) {{
  idx=i;
  document.getElementById('titulo').textContent = SLIDES[i].titulo;
  document.getElementById('ctr').textContent = (i+1)+' / '+N;

  var plt = document.getElementById('plt-div');
  var htm = document.getElementById('html-div');
  var body = document.getElementById('body');
  if (SLIDES[i].tipo==='plotly') {{
    plt.style.display='block'; htm.style.display='none';
    var W=body.clientWidth-6, H=body.clientHeight-6;
    var base=SLIDES[i].fig.layout||{{}};
    var isHeatmap = SLIDES[i].fig.data && SLIDES[i].fig.data[0] && SLIDES[i].fig.data[0].type==='heatmap';
    var isScatter = SLIDES[i].fig.data && SLIDES[i].fig.data[0] && SLIDES[i].fig.data[0].type==='scatter';
    var mg = isHeatmap
      ? {{l:160, r:20,  t:50, b:20}}
      : (isScatter
        ? {{l:20,  r:20,  t:60, b:60}}
        : {{l:160, r:100, t:30, b:40}});
    var figData = SLIDES[i].fig.data.map(function(trace) {{
      if (isScatter) {{
        var t = Object.assign({{}}, trace);
        if (t.mode && t.mode.indexOf('text') === -1) t.mode = t.mode + '+text';
        if (!t.mode) t.mode = 'lines+markers+text';
        if (t.y && t.y.length) {{
          t.text = t.y.map(function(v) {{
            return typeof v === 'number' ? v.toLocaleString('es-PE') : (v||'');
          }});
        }}
        t.textposition = 'top center';
        t.textfont = {{size: 13, color: '#1a7a4a', family: 'Arial'}};
        return t;
      }}
      return trace;
    }});
    var lay=Object.assign({{}},base,{{
      autosize:false, width:W, height:H,
      paper_bgcolor:'#ffffff', plot_bgcolor:'#ffffff',
      margin: mg,
      font:{{family:'Arial',size:13}},
      yaxis: isHeatmap
        ? Object.assign({{}}, base.yaxis||{{}}, {{title:'', tickfont:{{size:11.5}}}})
        : (isScatter
          ? Object.assign({{}}, base.yaxis||{{}}, {{visible:false, showticklabels:false, showgrid:false, zeroline:false}})
          : (base.yaxis||{{}})),
      xaxis: isHeatmap
        ? Object.assign({{}}, base.xaxis||{{}}, {{title:'', tickfont:{{size:13}}, side:'top'}})
        : Object.assign({{}}, base.xaxis||{{}}, {{tickfont:{{size:13}}, showgrid:false}})
    }});
    Plotly.react('plt-div', isHeatmap ? SLIDES[i].fig.data : figData, lay, {{displayModeBar:false,responsive:false}});
  }} else {{
    plt.style.display='none'; htm.style.display='block';
    htm.innerHTML=SLIDES[i].content;
  }}

  document.querySelectorAll('#dots span').forEach(function(d,j){{
    d.className=j===i?'on':'';
  }});

  clearInterval(ptmr);
  var pb=document.getElementById('pb'), t0=Date.now();
  pb.style.width='0%';
  ptmr=setInterval(function(){{
    pb.style.width=Math.min(100,(Date.now()-t0)/DL*100)+'%';
  }},50);
}}

function next(){{goTo((idx+1)%N);}}
function mNext(){{clearInterval(tmr);next();tmr=setInterval(next,DL);}}
function mPrev(){{clearInterval(tmr);goTo((idx-1+N)%N);tmr=setInterval(next,DL);}}

function toggleFS(){{
  var el=document.documentElement;
  var isFS=document.fullscreenElement||document.webkitFullscreenElement;
  if(isFS){{
    (document.exitFullscreen||document.webkitExitFullscreen||function(){{}}).call(document);
    document.getElementById('fsb').textContent='⛶ Fullscreen';
  }} else {{
    if(el.requestFullscreen){{
      el.requestFullscreen().then(function(){{
        document.getElementById('fsb').textContent='⊠ Salir';
        setTimeout(function(){{goTo(idx);}},300);
      }}).catch(function(){{
        window.parent.postMessage({{type:'requestFullscreen'}},'*');
      }});
    }} else {{
      window.parent.postMessage({{type:'requestFullscreen'}},'*');
    }}
  }}
}}

window.addEventListener('resize',function(){{
  clearTimeout(window._rt);
  window._rt=setTimeout(function(){{goTo(idx);}},200);
}});
document.addEventListener('keydown',function(e){{
  if(e.key==='ArrowRight') mNext();
  if(e.key==='ArrowLeft')  mPrev();
  if(e.key==='f'||e.key==='F') toggleFS();
}});
(function(){{
  var dts=document.getElementById('dots');
  SLIDES.forEach(function(_,j){{
    var d=document.createElement('span');
    d.onclick=function(){{clearInterval(tmr);goTo(j);tmr=setInterval(next,DL);}};
    dts.appendChild(d);
  }});
  goTo(0);
  tmr=setInterval(next,DL);
}})();
</script>
</body>
</html>"""
    html_completo = (html_completo
        .replace("__SLIDES_JS__", slides_js)
        .replace("__LOGO_IZQ__", logo_izq_tag)
        .replace("__LOGO_DER__", logo_der_tag)
    )

    import re as _re
    key = "ppt_" + _re.sub(r'[^a-zA-Z0-9]', '_', titulo_seccion)[:30]
    if key not in st.session_state:
        st.session_state[key] = False

    label = "⬇️ Cerrar presentación" if st.session_state[key] else "🖥️ Ver presentación"
   
    if st.button(f"{label}: {titulo_seccion}", key=f"btn_{key}"):
        st.session_state[key] = not st.session_state[key]
        st.rerun()

    if st.session_state[key]:
        components.html(html_completo, height=860, scrolling=False)
        st.markdown("""
<script>
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'requestFullscreen') {
    var iframes = document.querySelectorAll('iframe');
    var target = iframes[iframes.length-2];
    if (target) {
      target.setAttribute('allowfullscreen','');
      (target.requestFullscreen||target.webkitRequestFullscreen||function(){}).call(target);
    }
  }
});
</script>
""", unsafe_allow_html=True)


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
# 4. FUNCIONES DE PROCESAMIENTO
# =========================================================
def update_consolidado_arribo(doc, fecha):
    try:
        sh_cons = abrir_archivo_dinamico("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_data = wks_cons.get_all_values()
        headers = [h.upper() for h in all_data[0]]
        col_doc = headers.index("NOMBRE CORREO")
        col_status = headers.index("STATUS")
        col_fecha = headers.index("FCH LLEGADA")
        col_recuento = headers.index("RECUENTO") if "RECUENTO" in headers else None
        
        cells_to_update = []
        filas_para_actualizar = []
        
        for idx, row in enumerate(all_data[1:], start=2):
            if len(row) > max(col_doc, col_status, col_fecha):
                if str(row[col_doc]).strip() == str(doc).strip():
                    filas_para_actualizar.append(idx)
                    
        if not filas_para_actualizar:
            return False, "No se encontró el documento en el Consolidado."
            
        for f in filas_para_actualizar:
            cells_to_update.append(gspread.Cell(f, col_status + 1, "ARRIBADO"))
            cells_to_update.append(gspread.Cell(f, col_fecha + 1, str(fecha)))
            if col_recuento is not None:
                cells_to_update.append(gspread.Cell(f, col_recuento + 1, "1"))
                
        wks_cons.update_cells(cells_to_update, value_input_option="USER_ENTERED")
        return True, f"Consolidado actualizado correctamente para {len(filas_para_actualizar)} registros."
    except Exception as e:
        return False, f"Error al actualizar Consolidado: {e}"


# =========================================================
# MÓDULO: IMPORTACIONES
# =========================================================
def render_importaciones():
    st.markdown('<div class="titulo-seccion">🗂️ Módulo de Importaciones (Recuento = 1)</div>', unsafe_allow_html=True)
    df_imp, df_mov, df_tiendas = cargar_datos_completos()
    
    if df_imp.empty:
        st.warning("⚠️ No se encontraron datos en 'Consolidado - Carcasas' o falló la conexión.")
        return

    tab_status, tab_recep, tab_ops = st.tabs([
        "📊 Status Global & Aperturas", 
        "📥 Registro de Recepción (Arribos)", 
        "⚙️ Gestión Operativa (CF)"
    ])
    
    # ── TAB 1: STATUS GLOBAL & APERTURAS ──
    with tab_status:
        # Métricas Generales del Tablero de Importaciones
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Total Docs Filtrados", len(df_imp))
        
        status_counts = df_imp["STATUS"].value_counts().to_dict() if "STATUS" in df_imp.columns else {}
        c2.metric("🚢 En Tránsito", status_counts.get("EN TRANSITO", 0))
        c3.metric("🛬 Arribados", status_counts.get("ARRIBADO", 0))
        c4.metric("🏪 Tiendas Registradas", len(df_tiendas) if not df_tiendas.empty else 0)
        
        st.divider()
        
        # Grid de Próximas Aperturas
        st.markdown('<h3>🏪 Próximas Aperturas (Estado: PRODUCCIÓN / PROCESO)</h3>', unsafe_allow_html=True)
        apertura_slide = ""
        if not df_tiendas.empty:
            cond_tiendas = df_tiendas["ESTADO"].str.strip().str.upper().isin(["PRODUCCION", "PROCESO", "PRODUCCIÓN"])
            df_aperturas = df_tiendas[cond_tiendas].copy()
            
            if not df_aperturas.empty:
                cols_grid = st.columns(3)
                cards_html = []
                for idx, row in df_aperturas.iterrows():
                    tienda = row.get("TIENDA", "S/T")
                    descripcion = row.get("DESCRIPCION", "Sin descripción")
                    fecha_est = row.get("FECHA ESTIMADA", "Sin fecha")
                    
                    card = f"""
                    <div class="apertura-card">
                        <div class="tienda-titulo">🏪 {tienda}</div>
                        <div class="desc-tienda">{descripcion}</div>
                        <div class="fecha-est">📅 Est: {fecha_est}</div>
                    </div>
                    """
                    cards_html.append(card)
                    with cols_grid[idx % 3]:
                        st.markdown(card, unsafe_allow_html=True)
                
                apertura_slide = f"""
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; padding:20px;">
                    {"".join(cards_html)}
                </div>
                """
            else:
                st.info("No hay tiendas configuradas en estado PRODUCCIÓN o PROCESO.")
        else:
            st.info("No se encontró la hoja 'TIENDAS CARCASAS'.")
            
        st.divider()
        
        # Tabla de Status Global
        st.markdown('<h3>📋 Status General de Documentos</h3>', unsafe_allow_html=True)
        st.dataframe(df_imp, use_container_width=True)
        
        def _tbl(df_sub):
            if df_sub.empty: return '<p style="color:#636e72;font-size:12px;padding:8px;">Sin registros</p>'
            cols = ["NOMBRE CORREO", "STATUS", "ETA" if "ETA" in df_sub.columns else df_sub.columns[0]]
            cols = [c for c in cols if c in df_sub.columns]
            html = '<table style="width:100%;border-collapse:collapse;font-size:12px;text-align:left;">'
            html += '<tr style="background:#2d9e6b;color:#fff;">' + "".join(f'<th style="padding:6px;border:1px solid #ddd;">{c}</th>' for c in cols) + '</tr>'
            for _, r in df_sub.iterrows():
                html += '<tr>' + "".join(f'<td style="padding:6px;border:1px solid #ddd;">{r[c]}</td>' for c in cols) + '</tr>'
            html += '</table>'
            return html

        status_col = "STATUS" if "STATUS" in df_imp.columns else None
        status_slide = ""
        if status_col:
            df_trans = df_imp[df_imp[status_col].str.strip().str.upper() == "EN TRANSITO"]
            df_arr2 = df_imp[df_imp[status_col].str.strip().str.upper() == "ARRIBADO"]
            
            status_slide = (
                '<div id="wrap" style="display:flex;flex-direction:column;gap:12px;height:100%;padding:10px;">'
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;flex:1;min-height:0;">'
                
                '<div style="border:2px solid #2d9e6b;border-radius:10px;background:#fff;padding:12px;display:flex;flex-direction:column;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-shrink:0;">'
                '<span style="font-size:14px;font-weight:700;color:#1a7a4a;">🚢 En Tránsito</span>'
                '<span style="background:#e8d44d;color:#1a7a4a;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;">'
                + str(len(df_trans)) + ' docs</span></div>'
                '<div style="overflow-y:auto;flex:1;">' + _tbl(df_trans) + '</div>'
                '</div>'

                '<div style="border:2px solid #2d9e6b;border-radius:10px;background:#fff;padding:12px;display:flex;flex-direction:column;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-shrink:0;">'
                '<span style="font-size:14px;font-weight:700;color:#1a7a4a;">✅ Arribados</span>'
                '<span style="background:#2d9e6b;color:#fff;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;">'
                + str(len(df_arr2)) + ' docs</span></div>'
                '<div style="overflow-y:auto;flex:1;">' + _tbl(df_arr2) + '</div>'
                '</div>'

                + '</div>'
                + '</div>'
            )

        slides_imp = []
        if apertura_slide:
            slides_imp.append(("🏪 Próximas Aperturas", apertura_slide))
        if status_slide:
            slides_imp.append(("📋 Status Global Importaciones", status_slide))

        if slides_imp:
            mostrar_seccion_ppt("📦 Importaciones", slides_imp)

    # ── TAB 2: REGISTRO DE RECEPCIÓN (ARRIBOS) ──
    with tab_recep:
        st.markdown('<h3>📥 Registrar Arribo de Mercadería</h3>', unsafe_allow_html=True)
        col_doc_header = "NOMBRE CORREO" if "NOMBRE CORREO" in df_imp.columns else df_imp.columns[0]
        docs_en_transito = df_imp[df_imp["STATUS"].str.strip().str.upper() == "EN TRANSITO"][col_doc_header].unique().tolist()
        
        if docs_en_transito:
            with st.form("form_arribo", clear_on_submit=True):
                doc_sel = st.selectbox("Seleccione el Documento / Correo que arribó:", options=docs_en_transito)
                fecha_arribo = st.date_input("Fecha de Arribo Real:", value=date.today())
                btn_arribo = st.form_submit_data("Confirmar Arribo Masivo")
                
                if btn_arribo:
                    with st.spinner("Actualizando bases de datos en tiempo real..."):
                        # 1. Intentar actualizar base maestra Consolidado
                        exito, msg = update_consolidado_arribo(doc_sel, fecha_arribo)
                        
                        # 2. Registrar el movimiento en la hoja RECEPCION_IMPORTACIONES
                        if exito:
                            try:
                                sh_rec = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
                                wks_rec = sh_rec.worksheet("MOVIMIENTOS")
                                wks_rec.append_row([
                                    str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    str(doc_sel),
                                    "ARRIBADO",
                                    str(fecha_arribo),
                                    "SISTEMA LOGÍSTICO"
                                ], value_input_option="USER_ENTERED")
                                st.success(f"🎉 ¡Éxito! Documento {doc_sel} marcado como ARRIBADO. {msg}")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as re_err:
                                st.warning(f"Se actualizó el Consolidado pero falló el log de movimientos: {re_err}")
                        else:
                            st.error(f"❌ Error al procesar el arribo: {msg}")
        else:
            st.info("👍 Todos los documentos vigentes se encuentran en estado ARRIBADO. No hay pendientes de recepción.")

    # ── TAB 3: GESTIÓN OPERATIVA (CF) ──
    with tab_ops:
        st.markdown('<h3>⚙️ Panel Operativo y Log de Movimientos (CF Supply)</h3>', unsafe_allow_html=True)
        if not df_mov.empty:
            st.dataframe(df_mov, use_container_width=True)
        else:
            st.info("No se registran movimientos logísticos recientes en la hoja RECEPCION_IMPORTACIONES.")


# =========================================================
# MÓDULOS DE CONTROL COMPLEMENTARIOS
# =========================================================
def render_operaciones():
    st.markdown('<div class="titulo-seccion">⚙️ Ecosistema de Operaciones</div>', unsafe_allow_html=True)
    st.info("Sección modular reservada para flujos operativos avanzados.")

def render_distribucion():
    st.markdown('<div class="titulo-seccion">🚚 Control de Distribución</div>', unsafe_allow_html=True)
    st.info("Sección modular reservada para la trazabilidad de rutas terrestres.")


# =========================================================
# MENÚ NAVEGACIÓN Y CONTROL PRINCIPAL
# =========================================================
def main():
    st.sidebar.title("📦 Menú Logístico")
    st.sidebar.markdown("---")
    opcion = st.sidebar.radio(
        "Seleccione un Módulo:",
        ["📊 Dashboard de Despachos", "🗂️ Módulo de Importaciones", "⚙️ Operaciones", "🚚 Distribución"]
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("v2.1.0 Pro • Sync Activo")

    if opcion == "📊 Dashboard de Despachos":
        render_dash_despachos()
    elif opcion == "🗂️ Módulo de Importaciones":
        render_importaciones()
    elif opcion == "⚙️ Operaciones":
        render_operaciones()
    elif opcion == "🚚 Distribución":
        render_distribucion()

if __name__ == "__main__":
    main()
