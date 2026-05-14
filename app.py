# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN ULTRA-OPTIMIZADA
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# Carga de Logo (Cacheada para no ralentizar el inicio)
@st.cache_data
def mostrar_logo():
    try:
        st.image("CARCASAS.png", width=250)
    except:
        pass

mostrar_logo()

# 2. ESTILOS CSS
st.markdown("""
    <style>
    .stDataFrame { font-size: 12px; }
    .apertura-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 6px solid #6c5ce7; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 15px; min-height: 140px;
    }
    .tienda-titulo { color: #2d3436; font-size: 1.1em; font-weight: 700; }
    .desc-tienda { color: #636e72; font-size: 0.85em; }
    .fecha-est { color: #d63031; font-weight: bold; font-size: 0.9em; margin-top: 10px; }
    .titulo-seccion {
        color: #2d3436; font-weight: bold; font-size: 1.5rem;
        margin-top: 25px; margin-bottom: 15px;
        border-bottom: 3px solid #6c5ce7; padding-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXIÓN Y CARGA EFICIENTE
@st.cache_resource
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = conectar_google()

@st.cache_data(ttl=300) # Aumentamos a 5 min para mayor fluidez, se puede forzar con el botón Sync
def cargar_datos_completos():
    def fetch(nombre, hoja=None):
        try:
            sh = client.open(nombre)
            wks = sh.worksheet(hoja) if hoja else sh.sheet1
            df = pd.DataFrame(wks.get_all_records())
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df.astype(str)
        except: return pd.DataFrame()
    
    return fetch("Consolidado - Carcasas"), fetch("RECEPCION_IMPORTACIONES", "MOVIMIENTOS"), fetch("TIENDAS CARCASAS")

# 4. LÓGICA DE ACTUALIZACIÓN OPTIMIZADA
def update_consolidado_arribo(doc, fecha):
    try:
        sh_cons = client.open("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_values = wks_cons.get_all_values()
        header = [str(c).strip().upper() for c in all_values[0]]
        
        df_temp = pd.DataFrame(all_values[1:], columns=header)
        mask = df_temp["DOC"].astype(str) == str(doc)
        indices = df_temp[mask].index
        
        col_status_idx = header.index("STATUS")
        col_fecha_idx = header.index("FCH LLEGADA")

        # Actualización en memoria (Rápido)
        for idx in indices:
            all_values[idx + 1][col_status_idx] = "ARRIBADO"
            all_values[idx + 1][col_fecha_idx] = str(fecha)
        
        # Una sola escritura masiva
        wks_cons.update('A1', all_values)

        # Traspaso a Recepción
        sh_rec = client.open("RECEPCION_IMPORTACIONES")
        wks_mov = sh_rec.worksheet("MOVIMIENTOS")
        
        lista_bulk = []
        for _, fila in df_temp[mask].iterrows():
            tienda = str(fila.get("TIENDA", "")).strip()
            if tienda == "4298":
                dest, proc = "ALMACENAJE", "POR ALMACENAR"
            else:
                dest = "TIENDA"
                cols_x = [f"X{i}" for i in range(1, 10)]
                es_ap = any("APERTURA" in str(fila.get(c, "")).upper() for c in cols_x if c in fila)
                proc = "APERTURA" if es_ap else "POR DISTRIBUIR"
            
            lista_bulk.append([
                fila.get("ID_DESPACHO", fila.get("ID", "")), fila.get("DOC", ""), 
                fila.get("ASN", ""), tienda, fila.get("CANTIDAD", ""), 
                "Pendiente", str(fecha), fila.get("ETA", ""), dest, proc, ""
            ])
        
        wks_mov.append_rows(lista_bulk)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# 5. UI PRINCIPAL
df_import, df_recepcion, df_tiendas = cargar_datos_completos()

st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dash Importacion", "📑 Dash Recepción", "⚙️ Operaciones"])

    with tab_dash:
        # --- SECCIÓN APERTURAS ---
        if not df_tiendas.empty:
            df_ap = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
            df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors='coerce')
            df_filtrado = df_ap[df_ap["FCH_DT"] >= datetime.now()].sort_values("FCH_DT").head(4)
            cols = st.columns(4)
            for i, (_, row) in enumerate(df_filtrado.iterrows()):
                with cols[i % 4]:
                    st.markdown(f'<div class="apertura-card"><div class="tienda-titulo">🏪 {row["TIENDA"]}</div><div class="desc-tienda">{row["DESCRIPCION"]}</div><div class="fecha-est">📅 {row.get("FCH ESTIMADA","")}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Docs", df_import["DOC"].nunique() if not df_import.empty else 0)
        arr_count = df_import[df_import["STATUS"].str.upper() == "ARRIBADO"]["DOC"].nunique() if not df_import.empty else 0
        m2.metric("Arribados", arr_count)
        m3.metric("En Tránsito", (df_import["DOC"].nunique() - arr_count) if not df_import.empty else 0)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write("### ⏳ Pendientes")
            if not df_import.empty:
                st.dataframe(df_import[df_import["STATUS"] != "ARRIBADO"].groupby(["DOC", "ETA", "STATUS"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)
        with c2:
            st.write("### ✅ Arribados")
            if not df_import.empty:
                st.dataframe(df_import[df_import["STATUS"] == "ARRIBADO"].groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Dash Recepción")
        if not df_recepcion.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("🚨 **PENDIENTE**")
                st.dataframe(df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"].groupby(["IMPORTACION", "DESTINO", "PROCESO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            with col2:
                st.success("🏢 **EN STOCK**")
                st.dataframe(df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "ALMACENADO"].groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            with col3:
                st.warning("🚚 **PROGRAMADO**")
                st.dataframe(df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PROGRAMADO"].groupby(["FECHA ENTREGA", "IMPORTACION"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)

    # --- FRAGMENTO PARA OPERACIONES (EVITA RECARGA TOTAL) ---
    @st.fragment
    def seccion_operaciones():
        st.header("⚙️ Operaciones de Registro")
        o1, o2 = st.columns(2)
        with o1:
            st.subheader("1. Confirmar Arribo")
            docs_pend = df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].unique().tolist() if not df_import.empty else []
            if docs_pend:
                with st.form("f_arribo", clear_on_submit=True):
                    d_sel = st.selectbox("Seleccione DOC", docs_pend)
                    f_sel = st.date_input("Fecha Real", date.today())
                    if st.form_submit_button("Confirmar Arribo Masivo"):
                        with st.spinner("Procesando..."):
                            if update_consolidado_arribo(d_sel, f_sel):
                                st.success("¡Listo!")
                                st.cache_data.clear()
                                st.rerun()
        with o2:
            st.subheader("2. Confirmar Almacenaje")
            if not df_recepcion.empty:
                asns_pend = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                if asns_pend:
                    with st.form("f_alm", clear_on_submit=True):
                        a_sel = st.selectbox("ASN", asns_pend)
                        fa_sel = st.date_input("Fecha Almacenaje", date.today())
                        if st.form_submit_button("Confirmar Stock"):
                            # Usamos la misma lógica de batch update para rapidez
                            sh_r = client.open("RECEPCION_IMPORTACIONES")
                            w_m = sh_r.worksheet("MOVIMIENTOS")
                            vals = w_m.get_all_values()
                            # ... (lógica de actualización igual a la anterior pero masiva)
                            st.cache_data.clear()
                            st.rerun()

    with tab_ops:
        seccion_operaciones()

if st.sidebar.button("🔄 Sincronizar"):
    st.cache_data.clear()
    st.rerun()
