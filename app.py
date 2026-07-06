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
    # NOTA: Asegúrate de que NO haya una 'f' antes de las comillas triples de abajo
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
        [data-testid="stSidebar"] * { color: white !important; font-weight: 500; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #ffffff !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        /* Botones de Streamlit */
        div.stButton > button {
            background-color: var(--verde-main) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover {
            background-color: var(--verde-oscuro) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }

        /* Contenedores de KPIs */
        .kpi-container {
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-left: 5px solid var(--verde-main);
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }
        .kpi-container:hover {
            transform: translateY(-3px);
        }
        .kpi-title {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
            margin-bottom: 0.25rem;
            font-weight: 600;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #111;
        }

        /* Títulos */
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--verde-oscuro);
            margin-bottom: 1.5rem;
            border-bottom: 3px solid var(--amarillo-lima);
            padding-bottom: 0.5rem;
        }
        </style>
    """, unsafe_with_html=True)

cargar_estilos()

# 3. LLAVE DE CACHÉ Y VARIABLES CONSTANTES
_KEY_DF = "df_logistico_carcasas"
_KEY_PPT = "modo_presentacion"
_KEY_HTML = "html_presentacion"

# 4. CONEXIÓN A GOOGLE SHEETS (CON CACHÉ)
@st.cache_data(ttl=600)
def cargar_datos_gsheet():
    try:
        # Se asume que el secreto está configurado en Streamlit Cloud o archivo local
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Abre por la URL provista
        sheet_url = "https://docs.google.com/spreadsheets/d/1XlD0T7k7vA78X61m4sB34E57fD8z3i_06-381H9D48E/edit?gid=0#gid=0"
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(0)
        
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Procesar y limpiar columnas
        df.columns = [c.strip() for c in df.columns]
        
        # Convertir fechas de manera segura
        def parse_date(x):
            if pd.isna(x) or str(x).strip() == "":
                return pd.NaT
            s = str(x).split(" ")[0].strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return pd.to_datetime(s, format=fmt).date()
                except:
                    continue
            try:
                return pd.to_datetime(s).date()
            except:
                return pd.NaT

        if 'Fecha' in df.columns:
            df['Fecha'] = df['Fecha'].apply(parse_date)
            df = df.dropna(subset=['Fecha'])
            df = df.sort_values('Fecha', ascending=False)
            
        return df
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return pd.DataFrame()

# Carga inicial de datos si no está en sesión
if _KEY_DF not in st.session_state:
    st.session_state[_KEY_DF] = cargar_datos_gsheet()

df_raw = st.session_state[_KEY_DF]

# 5. SIDEBAR: ACCIONES Y FILTROS
with st.sidebar:
    st.title("⚙️ Control Logístico")
    
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.session_state[_KEY_DF] = cargar_datos_gsheet()
        if _KEY_HTML in st.session_state:
            del st.session_state[_KEY_HTML]
        st.rerun()
        
    st.markdown("---")
    
    # Interruptor Modo Presentación
    modo_p = st.toggle("🖥️ Modo Presentación TV", value=st.session_state.get(_KEY_PPT, False))
    if modo_p != st.session_state.get(_KEY_PPT, False):
        st.session_state[_KEY_PPT] = modo_p
        if not modo_p and _KEY_HTML in st.session_state:
            del st.session_state[_KEY_HTML]
        st.rerun()

    st.markdown("---")
    st.subheader("Filtros de Fecha")
    
    if not df_raw.empty and 'Fecha' in df_raw.columns:
        min_f = min(df_raw['Fecha'])
        max_f = max(df_raw['Fecha'])
        
        f_inicio = st.date_input("Fecha Inicio", min_f, min_value=min_f, max_value=max_f)
        f_fin = st.date_input("Fecha Fin", max_f, min_value=min_f, max_value=max_f)
        
        # Aplicar filtro
        df_filtrado = df_raw[(df_raw['Fecha'] >= f_inicio) & (df_raw['Fecha'] <= f_fin)].copy()
    else:
        df_filtrado = df_raw.copy()
        st.info("No hay fechas válidas para filtrar.")

# 6. PANTALLA PRINCIPAL
if df_filtrado.empty:
    st.title("📦 Sistema Logístico Carcasas")
    st.warning("No hay datos disponibles para mostrar. Verifica la conexión o los filtros.")
else:
    # Si no es modo presentación, renderizado normal de Streamlit
    if not st.session_state.get(_KEY_PPT, False):
        st.markdown('<div class="main-title">📦 Dashboard de Control - Logística Carcasas</div>', unsafe_with_html=True)
        
        # Fila de KPIs
        c1, c2, c3, c4 = st.columns(4)
        
        # Último registro para KPIs puntuales
        ultimo_reg = df_filtrado.iloc[0] if len(df_filtrado) > 0 else None
        
        with c1:
            val = f"{ultimo_reg['ERI %']}%" if ultimo_reg is not None and 'ERI %' in df_filtrado.columns else "N/A"
            st.markdown(f'<div class="kpi-container"><div class="kpi-title">ERI (Último)</div><div class="kpi-value">{val}</div></div>', unsafe_with_html=True)
        with c2:
            val = f"{ultimo_reg['ERU %']}%" if ultimo_reg is not None and 'ERU %' in df_filtrado.columns else "N/A"
            st.markdown(f'<div class="kpi-container"><div class="kpi-title">ERU (Último)</div><div class="kpi-value">{val}</div></div>', unsafe_with_html=True)
        with c3:
            val = int(df_filtrado['Recuento'].sum()) if 'Recuento' in df_filtrado.columns else 0
            st.markdown(f'<div class="kpi-container"><div class="kpi-title">Total Recuento</div><div class="kpi-value">{val}</div></div>', unsafe_with_html=True)
        with c4:
            val = len(df_filtrado)
            st.markdown(f'<div class="kpi-container"><div class="kpi-title">Registros Filt.</div><div class="kpi-value">{val}</div></div>', unsafe_with_html=True)
            
        # Gráficos Evolutivos Históricos
        st.subheader("📈 Evolución Temporal de Indicadores")
        
        df_cron = df_filtrado.sort_values('Fecha', ascending=True)
        df_cron['Fecha_Str'] = df_cron['Fecha'].apply(lambda x: x.strftime('%d/%m'))
        
        # Gráfico ERI
        fig_eri = px.line(df_cron, x='Fecha_Str', y='ERI %', markers=True, title="Evolución Histórica ERI %",
                          labels={'Fecha_Str': 'Fecha', 'ERI %': 'ERI %'})
        fig_eri.update_traces(line_color='#1a7a4a', linewidth=3)
        fig_eri.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_eri, use_container_width=True)
        
        # Gráfico ERU
        fig_eru = px.line(df_cron, x='Fecha_Str', y='ERU %', markers=True, title="Evolución Histórica ERU %",
                          labels={'Fecha_Str': 'Fecha', 'ERU %': 'ERU %'})
        fig_eru.update_traces(line_color='#2d9e6b', linewidth=3)
        fig_eru.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_eru, use_container_width=True)
        
        # Tabla de datos detallada
        st.subheader("📋 Datos Detallados")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

   # 7. MODO PRESENTACIÓN (INYECTADO INTEGRAL EN UN SOLO CONTENEDOR HTML)
    else:
        if _KEY_HTML not in st.session_state or True:
            df_cron = df_filtrado.sort_values('Fecha', ascending=True)
            fechas_js = [x.strftime('%d/%m') for x in df_cron['Fecha']]
            eri_js = [float(x) for x in df_cron['ERI %']] if 'ERI %' in df_cron.columns else []
            eru_js = [float(x) for x in df_cron['ERU %']] if 'ERU %' in df_cron.columns else []
            
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
  
  /* Contenedor del título - Ocupa el 20% de la altura total */
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

  /* Contenedor de gráficos - Ocupa el 80% restante */
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
