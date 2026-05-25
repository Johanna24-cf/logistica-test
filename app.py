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
        st.error(f"Error de conexión: {e}"); return None

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

    slides = [(t, f) for t, f in slides if f is not None]
    if not slides:
        return

    logo_izq, logo_der = _logos_b64()
    sid = "s" + str(abs(hash(titulo_seccion)) % 100000)
    logo_izq_tag = f'<img src="{logo_izq}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_izq else ""
    logo_der_tag = f'<img src="{logo_der}" style="max-height:56px;max-width:180px;object-fit:contain;">' if logo_der else ""

    slides_js_parts = []
    for t, f in slides:
        if isinstance(f, str):
            slides_js_parts.append(f'{{"titulo":{repr(t)},"tipo":"html","content":{repr(f)}}}')
        else:
            fig_json = pio.to_json(f)
            slides_js_parts.append(f'{{"titulo":{repr(t)},"tipo":"plotly","fig":{fig_json}}}')
    slides_js = "[" + ",".join(slides_js_parts) + "]"

    html_completo = f"""<!DOCTYPE html>
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
    flex:1; min-height:0;
    border:3px solid #2d9e6b; border-radius:14px;
    background:#fff; overflow:hidden;
    display:flex; align-items:stretch;
  }}
  #plt-div {{ width:100%; height:100%; }}
  #html-div {{ width:100%; height:100%; overflow-y:auto; overflow-x:hidden; display:none; }}
  /* FOOTER */
  #footer {{
    display:flex; align-items:center; justify-content:space-between;
    background:#fff; border-radius:12px;
    border:2px solid #c8e06a;
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
    <div class="logo-w">{logo_izq_tag}</div>
    <div id="titulo"></div>
    <div class="logo-w r">{logo_der_tag}</div>
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
var SLIDES={slides_js}, N=SLIDES.length, idx=0, tmr=null, ptmr=null, DL=5000;

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
    // Detectar si es heatmap (imshow tiene 'heatmap' en el tipo)
    var isHeatmap = SLIDES[i].fig.data && SLIDES[i].fig.data[0] && SLIDES[i].fig.data[0].type==='heatmap';
    var mg = isHeatmap
      ? {{l:160, r:20, t:50, b:20}}
      : {{l:20,  r:20, t:60, b:60}};
    // Para scatter: mantener labels sobre puntos, quitar eje Y
    var figData = SLIDES[i].fig.data.map(function(trace) {{
      if (!isHeatmap && trace.type !== 'heatmap') {{
        var t = Object.assign({{}}, trace);
        // Asegurar mode con text
        if (t.mode && t.mode.indexOf('text') === -1) t.mode = t.mode + '+text';
        if (!t.mode) t.mode = 'lines+markers+text';
        // Formatear labels con separador de miles
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
        : Object.assign({{}}, base.yaxis||{{}}, {{visible:false, showticklabels:false, showgrid:false, zeroline:false}}),
      xaxis: isHeatmap
        ? Object.assign({{}}, base.xaxis||{{}}, {{title:'', tickfont:{{size:13}}, side:'top'}})
        : Object.assign({{}}, base.xaxis||{{}}, {{tickfont:{{size:14}}, showgrid:false}})
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

// Construir dots y arrancar
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

    key = f"ppt_show_{abs(hash(titulo_seccion)) % 100000}"
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

def update_consolidado_arribo(doc, fecha):
    try:
        sh_cons = abrir_archivo_dinamico("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_data = wks_cons.get_all_values()
        headers = [h.upper() for h in all_data[0]]

        col_doc    = headers.index("NOMBRE CORREO")
        col_status = headers.index("STATUS")
        col_fecha  = headers.index("FCH LLEGADA")
        col_recuento = headers.index("RECUENTO") if "RECUENTO" in headers else None

        cells_to_update = []
        filas_para_traspaso = []

        for i, row in enumerate(all_data[1:], start=2):
            if row[col_doc] == str(doc):
                if col_recuento is not None and str(row[col_recuento]).strip() not in ["1", "1.0"]:
                    continue
                cells_to_update.append(gspread.Cell(i, col_status + 1, "ARRIBADO"))
                cells_to_update.append(gspread.Cell(i, col_fecha + 1, str(fecha)))
                filas_para_traspaso.append(row)

        if cells_to_update:
            wks_cons.update_cells(cells_to_update)
            sh_rec  = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
            wks_mov = sh_rec.worksheet("MOVIMIENTOS")

            bulk_data = []
            for row in filas_para_traspaso:
                tienda = row[headers.index("TIENDA")].strip()
                if tienda == "4298":
                    dest, proc = "ALMACENAJE", "POR ALMACENAR"
                else:
                    dest = "TIENDA"
                    es_ap = any("APERTURA" in str(row[headers.index(f"X{j}")]).upper()
                                for j in range(1, 10) if f"X{j}" in headers)
                    proc = "APERTURA" if es_ap else "POR DISTRIBUIR"
                col_hora_fech_idx = headers.index("HORA FECH") if "HORA FECH" in headers else 0
                bulk_data.append([
                    row[headers.index("ID_DESPACHO")] if "ID_DESPACHO" in headers else row[0],
                    row[col_doc], row[headers.index("ASN")], tienda,
                    row[headers.index("CANTIDAD")], "Pendiente", str(fecha),
                    row[col_hora_fech_idx], dest, proc, ""
                ])
            wks_mov.append_rows(bulk_data)
            return True
    except Exception as e:
        st.error(f"Error técnico: {e}"); return False


# =========================================================
# 5. UI Y RENDERIZADO
# =========================================================

df_import, df_recep, df_tiendas = cargar_datos_completos()

st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", [
    "📦 Importaciones",
    "📊 Dash Despachos",
])

# ----------------------------------------------------------
# MENÚ: IMPORTACIONES
# ----------------------------------------------------------
if menu == "📦 Importaciones":
    (tab_dash,) = st.tabs(["📊 Dash Importacion"])

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
        if not df_import.empty:
            columnas_import_req = ["NOMBRE CORREO", "HORA FECH", "STATUS", "FCH LLEGADA"]
            columnas_faltantes = [c for c in columnas_import_req if c not in df_import.columns]

            if columnas_faltantes:
                st.error(f"❌ Columnas faltantes: {', '.join(columnas_faltantes)}")
            else:
                m1, m2, m3 = st.columns(3)
                total     = df_import["NOMBRE CORREO"].nunique()
                arribados = df_import[df_import["STATUS"] == "ARRIBADO"]["NOMBRE CORREO"].nunique()
                m1.metric("Total Docs", total)
                m2.metric("Arribados", arribados)
                m3.metric("En Tránsito", total - arribados)

                st.divider()
                c1, c2 = st.columns(2)

                with c1:
                    st.write("### ⏳ Pendientes")
                    df_pend = (
                        df_import[df_import["STATUS"] != "ARRIBADO"]
                        .groupby(["NOMBRE CORREO", "HORA FECH", "STATUS"])
                        .size()
                        .reset_index(name="ASNs")
                    )
                    orden_status = {"ADUANAS": 0, "EN TRÁNSITO": 1, "EN TRANSITO": 1, "ORIGEN": 2}
                    df_pend["_orden"] = df_pend["STATUS"].str.upper().str.strip().map(orden_status).fillna(
                        df_pend["STATUS"].apply(lambda s: 99 if str(s).strip() == "" else 3)
                    )
                    df_pend = df_pend.sort_values("_orden").drop(columns=["_orden"])
                    st.dataframe(df_pend, use_container_width=True, hide_index=True)

                with c2:
                    st.write("### ✅ Arribados")
                    df_arr = (
                        df_import[df_import["STATUS"] == "ARRIBADO"]
                        .groupby(["NOMBRE CORREO", "FCH LLEGADA"])
                        .size()
                        .reset_index(name="ASNs")
                    )
                    df_arr["_fch_dt"] = pd.to_datetime(df_arr["FCH LLEGADA"], errors="coerce")
                    df_arr = df_arr.sort_values("_fch_dt", ascending=False, na_position="last").drop(columns=["_fch_dt"])
                    st.dataframe(df_arr, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ No hay registros con RECUENTO = 1, o la hoja está vacía.")

        # ── Botón presentación importaciones ───────────────────────────────
        st.divider()

        # Slide 1: tarjetas aperturas
        # ── SLIDE 1: Próximas Aperturas ────────────────────────────────────
        def _card_ap(tienda, desc, fecha):
            return (
                '<div style="background:#fff;border-radius:16px;border-top:6px solid #2d9e6b;'
                'padding:28px 30px;box-shadow:0 4px 16px rgba(45,158,107,0.13);'
                'display:flex;flex-direction:column;justify-content:space-between;">'
                '<div>'
                '<div style="color:#1a7a4a;font-size:1.5rem;font-weight:800;margin-bottom:10px;line-height:1.2;">🏪 ' + tienda + '</div>'
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
            df_ap2 = df_ap2[df_ap2["FCH_DT"] >= datetime.now()].sort_values("FCH_DT").head(6)
            cards = "".join(_card_ap(str(r["TIENDA"]), str(r["DESCRIPCION"]), str(r.get("FCH ESTIMADA",""))) for _, r in df_ap2.iterrows())
            apertura_slide = (
                '<div style="width:100%;height:100vh;padding:20px 28px;background:#f0faf4;'
                'font-family:Arial,sans-serif;box-sizing:border-box;display:flex;flex-direction:column;gap:14px;">'
                '<div style="font-size:11px;font-weight:700;color:#2d9e6b;text-transform:uppercase;letter-spacing:1.2px;">🏪 Próximas Aperturas de Tiendas</div>'
                '<div style="display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(2,1fr);gap:16px;flex:1;min-height:0;">'
                + cards +
                '</div></div>'
            )

        # ── SLIDE 2: Status Global — dashboard visual tipo Power BI ─────────
        status_slide = ""
        if not df_import.empty and all(c in df_import.columns for c in ["NOMBRE CORREO","STATUS","HORA FECH","FCH LLEGADA"]):
            total_i = df_import["NOMBRE CORREO"].nunique()
            arr_i   = df_import[df_import["STATUS"]=="ARRIBADO"]["NOMBRE CORREO"].nunique()
            trans_i = total_i - arr_i
            pct     = int(arr_i / total_i * 100) if total_i else 0

            df_pend2 = df_import[df_import["STATUS"]!="ARRIBADO"].groupby(["NOMBRE CORREO","HORA FECH","STATUS"]).size().reset_index(name="ASNs")
            orden_s  = {"ADUANAS":0,"EN TRÁNSITO":1,"EN TRANSITO":1,"ORIGEN":2}
            df_pend2["_o"] = df_pend2["STATUS"].str.upper().str.strip().map(orden_s).fillna(
                df_pend2["STATUS"].apply(lambda s: 99 if str(s).strip()=="" else 3))
            df_pend2 = df_pend2.sort_values("_o").drop(columns=["_o"])
            df_pend2 = df_pend2[df_pend2.apply(lambda row: any(str(v).strip() not in ('','nan','None') for v in row), axis=1)]

            df_arr2 = df_import[df_import["STATUS"]=="ARRIBADO"].groupby(["NOMBRE CORREO","FCH LLEGADA"]).size().reset_index(name="ASNs")
            df_arr2["_f"] = pd.to_datetime(df_arr2["FCH LLEGADA"], errors="coerce")
            df_arr2 = df_arr2.sort_values("_f", ascending=False, na_position="last").drop(columns=["_f"])
            df_arr2 = df_arr2[df_arr2.apply(lambda row: any(str(v).strip() not in ('','nan','None') for v in row), axis=1)]

            def _tbl(df, mx=20):
                df = df.head(mx)
                heads = "".join(
                    '<th style="padding:7px 10px;background:#2d9e6b;color:#fff;font-size:12px;'
                    'font-weight:700;text-align:left;position:sticky;top:0;z-index:1;font-size:13px;">' + str(c) + '</th>'
                    for c in df.columns
                )
                rows = "".join(
                    '<tr>' +
                    "".join(
                        '<td style="padding:8px 12px;border-bottom:1px solid #f0faf4;font-size:13px;color:#2d3436;">' + str(v) + '</td>'
                        for v in r
                    ) + '</tr>' for r in df.values
                )
                return ('<table style="width:100%;border-collapse:collapse;">'
                        '<thead><tr>' + heads + '</tr></thead>'
                        '<tbody>' + rows + '</tbody></table>')

            # Barra circular SVG para % completado
            r_svg, cx, cy = 54, 60, 60
            circ = 2 * 3.14159 * r_svg
            dash = circ * pct / 100
            svg_donut = (
                f'<svg width="120" height="120" viewBox="0 0 120 120">'
                f'<circle cx="{cx}" cy="{cy}" r="{r_svg}" fill="none" stroke="#e8f5ee" stroke-width="14"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r_svg}" fill="none" stroke="url(#g)" stroke-width="14"'
                f' stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-linecap="round"'
                f' transform="rotate(-90 {cx} {cy})"/>'
                f'<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">'
                f'<stop offset="0%" style="stop-color:#2d9e6b"/>'
                f'<stop offset="100%" style="stop-color:#c8e06a"/>'
                f'</linearGradient></defs>'
                f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="20" font-weight="800" fill="#1a7a4a">{pct}%</text>'
                f'</svg>'
            )

            def _kpi(val, label, color, sub=""):
                return (
                    '<div style="background:#fff;border-radius:14px;border-left:5px solid ' + color + ';'
                    'padding:18px 20px;box-shadow:0 2px 8px rgba(45,158,107,.1);display:flex;flex-direction:column;justify-content:center;">'
                    '<div style="color:#aaa;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;">' + label + '</div>'
                    '<div style="color:#1a7a4a;font-size:3rem;font-weight:900;line-height:1.05;">' + str(val) + '</div>'
                    + (f'<div style="color:#aaa;font-size:11px;margin-top:4px;">{sub}</div>' if sub else '') +
                    '</div>'
                )

            kpis = (
                _kpi(total_i, "Total Docs", "#2d9e6b") +
                _kpi(arr_i, "Arribados", "#3dbb7e", f"{pct}% del total") +
                _kpi(trans_i, "En Tránsito", "#e8d44d") +
                '<div style="background:#fff;border-radius:14px;border-left:5px solid #c8e06a;'
                'padding:18px 20px;box-shadow:0 2px 8px rgba(45,158,107,.1);display:flex;align-items:center;gap:12px;">'
                + svg_donut +
                '<div><div style="color:#aaa;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;">Completado</div>'
                '<div style="color:#1a7a4a;font-size:1rem;font-weight:700;margin-top:4px;">' + str(arr_i) + ' de ' + str(total_i) + ' docs</div></div></div>'
            )

            def _panel(title, badge_color, badge_text, tbl_html):
                return (
                    '<div style="background:#fff;border-radius:14px;padding:14px 16px;'
                    'box-shadow:0 2px 8px rgba(45,158,107,.08);display:flex;flex-direction:column;min-height:0;height:100%;">'
                    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
                    '<span style="font-size:15px;font-weight:700;color:#1a7a4a;">' + title + '</span>'
                    '<span style="background:' + badge_color + ';color:#fff;border-radius:20px;'
                    'padding:2px 10px;font-size:11px;font-weight:700;">' + badge_text + '</span></div>'
                    '<div style="overflow-y:auto;flex:1;">' + tbl_html + '</div>'
                    '</div>'
                )

            status_slide = (
                '<div style="width:100%;height:100vh;padding:18px 24px;background:#f0faf4;'
                'font-family:Arial,sans-serif;box-sizing:border-box;display:flex;flex-direction:column;gap:12px;">'
                # KPIs
                '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;flex-shrink:0;">' + kpis + '</div>'
                # Tablas
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;min-height:0;height:100%;">'
                + _panel("⏳ Pendientes", "#e8a020", str(len(df_pend2)) + " docs", _tbl(df_pend2))
                + _panel("✅ Arribados",  "#2d9e6b", str(len(df_arr2)) + " docs",  _tbl(df_arr2))
                + '</div></div>'
            )

        slides_imp = []
        if apertura_slide:
            slides_imp.append(("🏪 Próximas Aperturas", apertura_slide))
        if status_slide:
            slides_imp.append(("📋 Status Global Importaciones", status_slide))

        if slides_imp:
            mostrar_seccion_ppt("📦 Importaciones", slides_imp)

    # tab_recep oculto (modo pantalla)

    # tab_ops oculto (modo pantalla)

# MENÚ DISTRIBUCIÓN oculto (modo pantalla)

# ----------------------------------------------------------
# MENÚ: DASH DESPACHOS
# ----------------------------------------------------------
if menu == "📊 Dash Despachos":
    render_dash_despachos()

# ----------------------------------------------------------
# SINCRONIZAR
# ----------------------------------------------------------
if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear(); st.rerun()
