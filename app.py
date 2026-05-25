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
    """
    Un solo botón que abre overlay con carrusel cada 5 seg.
    slides = [(titulo_slide, fig), ...]
    """
    import json
    logo_izq, logo_der = _logos_b64()
    sid = "ppt_" + str(abs(hash(titulo_seccion)) % 100000)

    slides_data = []
    for t, f in slides:
        html = f.to_html(include_plotlyjs=False, full_html=False,
                         config={"displayModeBar": False})
        slides_data.append({"titulo": t, "html": html})

    slides_json = json.dumps(slides_data, ensure_ascii=False)

    logo_izq_tag = f'<img src="{logo_izq}" style="height:56px;object-fit:contain;">' if logo_izq else ""
    logo_der_tag = f'<img src="{logo_der}" style="height:56px;object-fit:contain;">' if logo_der else ""

    st.markdown(f"""
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>

<div id="{sid}-ov" style="display:none;position:fixed;inset:0;z-index:99999;
  background:#ffffff;flex-direction:column;align-items:center;
  justify-content:flex-start;padding:24px 40px 20px;box-sizing:border-box;
  font-family:Arial,sans-serif;">

  <button onclick="pptCerrar_{sid}()"
    style="position:absolute;top:14px;right:20px;background:transparent;
           border:2px solid #2d9e6b;color:#2d9e6b;border-radius:8px;
           padding:5px 14px;font-size:13px;font-weight:700;cursor:pointer;">
    &#x2716; Cerrar
  </button>

  <div style="width:100%;display:flex;align-items:center;
              justify-content:space-between;margin-bottom:10px;">
    <div style="min-width:140px;">{logo_izq_tag}</div>
    <div id="{sid}-titulo" style="color:#1a7a4a;font-size:1.6rem;font-weight:700;
         text-align:center;flex:1;padding:0 16px;"></div>
    <div style="min-width:140px;text-align:right;">{logo_der_tag}</div>
  </div>

  <div style="width:100%;height:5px;background:#e8f5ee;border-radius:3px;margin-bottom:10px;">
    <div id="{sid}-prog" style="height:5px;background:#2d9e6b;border-radius:3px;
         width:0%;transition:width 0.08s linear;"></div>
  </div>

  <div id="{sid}-body" style="width:100%;flex:1;min-height:0;overflow:hidden;"></div>

  <div id="{sid}-dots" style="margin-top:10px;display:flex;gap:10px;"></div>
</div>

<script>
(function(){{
  var SLIDES = {slides_json};
  var N = SLIDES.length;
  var idx = 0, timer = null, progTimer = null, DELAY = 5000;

  function goTo(i) {{
    idx = i;
    document.getElementById('{sid}-titulo').textContent = SLIDES[i].titulo;
    document.getElementById('{sid}-body').innerHTML = SLIDES[i].html;
    document.getElementById('{sid}-dots').querySelectorAll('span').forEach(function(d,j){{
      d.style.background = j===i ? '#2d9e6b' : '#c8e06a';
    }});
    clearInterval(progTimer);
    var prog = document.getElementById('{sid}-prog');
    prog.style.width = '0%';
    var start = Date.now();
    progTimer = setInterval(function(){{
      var p = Math.min(100, (Date.now()-start)/DELAY*100);
      prog.style.width = p + '%';
    }}, 50);
  }}

  function next(){{ goTo((idx+1)%N); }}

  window['pptAbrir_{sid}'] = function(){{
    var ov = document.getElementById('{sid}-ov');
    ov.style.display = 'flex';
    var dotsEl = document.getElementById('{sid}-dots');
    dotsEl.innerHTML = '';
    SLIDES.forEach(function(_,j){{
      var d = document.createElement('span');
      d.style.cssText = 'width:11px;height:11px;border-radius:50%;display:inline-block;cursor:pointer;';
      d.onclick = function(){{ clearInterval(timer); goTo(j); timer=setInterval(next,DELAY); }};
      dotsEl.appendChild(d);
    }});
    goTo(0);
    timer = setInterval(next, DELAY);
    if(document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
  }};

  window['pptCerrar_{sid}'] = function(){{
    clearInterval(timer); clearInterval(progTimer);
    document.getElementById('{sid}-ov').style.display='none';
    if(document.exitFullscreen) document.exitFullscreen();
  }};

  document.addEventListener('keydown', function(e){{
    var fn = window['pptCerrar_{sid}'];
    if(e.key==='Escape' && fn) fn();
    if(e.key==='ArrowRight'){{ clearInterval(timer); next(); timer=setInterval(next,DELAY); }}
    if(e.key==='ArrowLeft'){{ clearInterval(timer); goTo((idx-1+N)%N); timer=setInterval(next,DELAY); }}
  }});
}})();
</script>

<button onclick="window['pptAbrir_{sid}']()"
  style="background:linear-gradient(135deg,#2d9e6b,#c8e06a);
         color:#0d1f16;border:none;border-radius:8px;
         padding:9px 24px;font-size:14px;font-weight:700;cursor:pointer;">
  &#128250; Ver en presentaci&#243;n
</button>
""", unsafe_allow_html=True)

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
