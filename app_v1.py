# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN 2026 (ACTUALIZADA)
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# =========================================================
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
    <style>
    .stDataFrame {font-size: 12px;}
    .apertura-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #6c5ce7;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        min-height: 120px;
    }
    .fecha-est { color: #d63031; font-weight: bold; font-size: 0.9em; }
    .titulo-seccion {
        color: #2d3436; font-weight: bold; font-size: 1.6em;
        margin-top: 25px; margin-bottom: 15px;
        border-bottom: 3px solid #6c5ce7; padding-bottom: 8px;
    }
    .tienda-titulo { color: #2d3436; font-size: 1.1em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 2. CONEXIÓN A GOOGLE SHEETS
# =========================================================
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Recomiendo usar st.secrets si subes esto a la nube
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    return gspread.authorize(creds)

client = conectar_google_sheets()

def abrir_hoja(nombre_archivo, nombre_pestaña=None):
    try:
        sh = client.open(nombre_archivo)
        return sh.worksheet(nombre_pestaña) if nombre_pestaña else sh.sheet1
    except:
        return None

# =========================================================
# 3. CARGA DE DATOS Y FUNCIONES DE ESCRITURA
# =========================================================
@st.cache_data(ttl=60)
def cargar_df(nombre_archivo, pestaña=None):
    sheet = abrir_hoja(nombre_archivo, pestaña)
    if sheet is None: return pd.DataFrame()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = [str(c).strip().upper() for c in df.columns]
    return df.astype(str)

def update_consolidado_arribo(doc_id, fecha):
    try:
        sheet = abrir_hoja("Consolidado - Carcasas")
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = [str(c).strip().upper() for c in df.columns]
        indices = df[df['DOC'].astype(str) == str(doc_id)].index
        col_status = df.columns.get_loc("STATUS") + 1
        col_fecha = df.columns.get_loc("FCH LLEGADA") + 1
        for idx in indices:
            sheet.update_cell(idx + 2, col_status, "ARRIBADO")
            sheet.update_cell(idx + 2, col_fecha, str(fecha))
        return True
    except: return False

def update_recepcion_almacenado(asn_id, fecha):
    try:
        sheet = abrir_hoja("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(c).strip().upper() for c in df.columns]
        indices = df[df['ASN'].astype(str) == str(asn_id)].index
        col_status = df.columns.get_loc("STATUS_REC") + 1
        col_fecha = df.columns.get_loc("FCH_ALMACENADO") + 1
        for idx in indices:
            sheet.update_cell(idx + 2, col_status, "ALMACENADO")
            sheet.update_cell(idx + 2, col_fecha, str(fecha))
        return True
    except: return False

# CARGA DE DATOS
with st.spinner('Sincronizando con Drive...'):
    df_import = cargar_df("Consolidado - Carcasas")
    df_recepcion = cargar_df("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
    df_tiendas_raw = cargar_df("TIENDAS CARCASAS")

# =========================================================
# 4. ESTRUCTURA DE LA APP
# =========================================================
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    st.title("📦 Gestión de Importaciones")
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dashboard General", "📑 Flujo de Recepción", "⚙️ Operaciones"])

    with tab_dash:
        # SECCIÓN APERTURAS (60 DÍAS)
        st.subheader("🏪 Próximas Aperturas (Filtro: 60 días)")
        if not df_tiendas_raw.empty:
            try:
                df_ap = df_tiendas_raw[df_tiendas_raw["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
                df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors='coerce')
                hoy = datetime.now()
                limite = hoy + timedelta(days=60)
                df_filtrado = df_ap[(df_ap["FCH_DT"] >= hoy) & (df_ap["FCH_DT"] <= limite)].sort_values("FCH_DT")

                if not df_filtrado.empty:
                    cols = st.columns(4)
                    for i, (_, row) in enumerate(df_filtrado.iterrows()):
                        with cols[i % 4]:
                            st.markdown(f"""
                                <div class="apertura-card">
                                    <div class="tienda-titulo">{row['TIENDA']}</div>
                                    <div style="color:#636e72; font-size:0.85em;">{row['DESCRIPCION']}</div><br>
                                    <div class="fecha-est">📅 Est: {row['FCH ESTIMADA']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                else: st.info("No hay aperturas programadas en los próximos 60 días.")
            except Exception as e: st.error(f"Error en Dashboard Aperturas: {e}")

        # SECCIÓN STATUS IMPORTACIONES
        st.markdown('<div class="titulo-seccion">STATUS IMPORTACIONES</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total_docs = df_import["DOC"].nunique()
            arribados = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].nunique()
            m1.metric("Total Importaciones", total_docs)
            m2.metric("Ya Arribados", arribados)
            m3.metric("En Tránsito", total_docs - arribados)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### ⏳ Pendientes por Arribar")
                df_p = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                # ACTUALIZADO: width='stretch'
                st.dataframe(df_p.groupby("DOC").size().reset_index(name='ASNs'), width='stretch', hide_index=True)
            with c2:
                st.markdown("### ✅ Confirmados")
                df_a = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                # ACTUALIZADO: width='stretch'
                st.dataframe(df_a.groupby(["DOC", "ETA"]).size().reset_index(name='ASNs'), width='stretch', hide_index=True)

    with tab_recep:
            st.markdown("### 🗺️ Flujo de AP's Recepcionadas")
            col_p, col_a, col_t = st.columns(3)

            with col_p:
                st.markdown("""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
                    <h4 style="margin:0;">🚨 1. RECEPCIONADO</h4><small>Pendiente</small></div>""", unsafe_allow_html=True)
                df_p = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"].copy()
                if not df_p.empty:
                    col_f = next((c for c in df_p.columns if "FECHA" in c or "FCH" in c), "FECHA_LLEGADA")
                    df_p['FECHA_DT'] = pd.to_datetime(df_p[col_f], errors='coerce')
                    df_p['SEMAFORO'] = (pd.to_datetime(date.today()) - df_p['FECHA_DT']).dt.days.apply(lambda d: "🔴 +3d" if d > 3 else "🟢 OK")
                    # ACTUALIZADO: width='stretch'
                    st.dataframe(df_p.groupby([col_f, "IMPORTACION", "DESTINO", "SEMAFORO"]).size().reset_index(name='CANT'), hide_index=True, width='stretch')

            with col_a:
                st.markdown("""<div style="background-color: #f0fff4; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
                    <h4 style="margin:0;">🏢 2. ALMACENADO</h4><small>En Stock</small></div>""", unsafe_allow_html=True)
                df_alm = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "ALMACENADO"]
                if not df_alm.empty:
                    # ACTUALIZADO: width='stretch'
                    st.dataframe(df_alm.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name='ASNs'), hide_index=True, width='stretch')

            with col_t:
                st.markdown("""<div style="background-color: #fffaf0; padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500;">
                    <h4 style="margin:0;">🚚 3. EN TRÁNSITO</h4><small>Programado</small></div>""", unsafe_allow_html=True)
                df_prog = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PROGRAMADO"]
                if not df_prog.empty:
                    # ACTUALIZADO: width='stretch'
                    st.dataframe(df_prog.groupby(["IMPORTACION", "ID_DESPACHO"]).size().reset_index(name='ASNs'), hide_index=True, width='stretch')

    with tab_ops:
        st.header("⚙️ Panel de Operaciones")
        c_left, c_right = st.columns(2)

        # 1. ACTUALIZAR ARRIBO
        with c_left:
            st.subheader("1. Confirmar Arribo (DOC)")
            df_ops_pend = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
            docs_list = df_ops_pend["DOC"].unique().tolist()
            if docs_list:
                with st.form("form_arribo"):
                    doc_sel = st.selectbox("Seleccione DOC que arribó:", docs_list)
                    f_arr = st.date_input("Fecha Real de Arribo:", date.today())
                    if st.form_submit_button("✅ Marcar como ARRIBADO"):
                        if update_consolidado_arribo(doc_sel, f_arr):
                            st.success(f"¡DOC {doc_sel} actualizado!")
                            st.cache_data.clear()
                            st.rerun()
            else: st.info("No hay documentos pendientes.")

        # 2. ACTUALIZAR ALMACENAJE
        with c_right:
            st.subheader("2. Confirmar Almacenaje (ASN)")
            df_ops_alm = df_recepcion[df_recepcion["STATUS_REC"].str.upper().str.contains("PENDIENTE", na=False)]
            asns_list = df_ops_alm["ASN"].unique().tolist()
            if asns_list:
                with st.form("form_almacen"):
                    asn_sel = st.selectbox("Seleccione ASN a Almacenar:", asns_list)
                    f_alm = st.date_input("Fecha de Almacenamiento:", date.today())
                    if st.form_submit_button("🏢 Marcar como ALMACENADO"):
                        if update_recepcion_almacenado(asn_sel, f_alm):
                            st.success(f"¡ASN {asn_sel} almacenado!")
                            st.cache_data.clear()
                            st.rerun()
            else: st.info("No hay ASNs por almacenar.")

# SIDEBAR
if st.sidebar.button("🔄 Sincronizar Ahora"):
    st.cache_data.clear()
    st.rerun()