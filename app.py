# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN FINAL REVISADA
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN INICIAL (Debe ir antes de cualquier otro comando st)
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# 2. ESTILOS CSS
st.markdown("""
    <style>
    .stDataFrame { font-size: 12px; }
    .apertura-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #6c5ce7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        min-height: 140px;
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

# 3. FUNCIONES DE CONEXIÓN Y DATOS
@st.cache_resource
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = conectar_google()

def abrir_hoja(nombre_archivo, nombre_hoja=None):
    try:
        sh = client.open(nombre_archivo)
        return sh.worksheet(nombre_hoja) if nombre_hoja else sh.sheet1
    except:
        return None

@st.cache_data(ttl=60)
def cargar_df(nombre_archivo, hoja=None):
    sheet = abrir_hoja(nombre_archivo, hoja)
    if sheet is None: return pd.DataFrame()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df.astype(str)
    return pd.DataFrame()

# 4. FUNCIONES DE ACTUALIZACIÓN
def update_consolidado_arribo(doc, fecha):
    try:
        sheet = abrir_hoja("Consolidado - Carcasas")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(c).strip().upper() for c in df.columns]
        indices = df[df["DOC"].astype(str) == str(doc)].index
        col_status = df.columns.get_loc("STATUS") + 1
        col_fecha = df.columns.get_loc("FCH LLEGADA") + 1
        for idx in indices:
            sheet.update_cell(idx + 2, col_status, "ARRIBADO")
            sheet.update_cell(idx + 2, col_fecha, str(fecha))
        return True
    except: return False

def update_recepcion_almacenado(asn, fecha):
    try:
        sheet = abrir_hoja("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(c).strip().upper() for c in df.columns]
        indices = df[df["ASN"].astype(str) == str(asn)].index
        col_status = df.columns.get_loc("STATUS_REC") + 1
        col_fecha = df.columns.get_loc("FCH_ALMACENADO") + 1
        for idx in indices:
            sheet.update_cell(idx + 2, col_status, "ALMACENADO")
            sheet.update_cell(idx + 2, col_fecha, str(fecha))
        return True
    except: return False

# 5. CARGA DE DATOS
with st.spinner("Sincronizando..."):
    df_import = cargar_df("Consolidado - Carcasas")
    df_recepcion = cargar_df("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
    df_tiendas = cargar_df("TIENDAS CARCASAS")

# 6. LÓGICA DE NAVEGACIÓN
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    st.title("📦 Gestión de Importaciones")
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dashboard", "📑 Recepción", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas")
        if not df_tiendas.empty:
            try:
                df_ap = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
                df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors="coerce")
                hoy = datetime.now()
                limite = hoy + timedelta(days=60)
                df_filtrado = df_ap[(df_ap["FCH_DT"] >= hoy) & (df_ap["FCH_DT"] <= limite)].sort_values("FCH_DT")

                if not df_filtrado.empty:
                    cols = st.columns(4)
                    for i, (_, row) in enumerate(df_filtrado.iterrows()):
                        with cols[i % 4]:
                            st.markdown(f"""
                                <div class="apertura-card">
                                    <div class="tienda-titulo">🏪 {row['TIENDA']}</div>
                                    <div class="desc-tienda">{row['DESCRIPCION']}</div>
                                    <div class="fecha-est">📅 {row['FCH ESTIMADA']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                else: st.info("No hay aperturas próximas.")
            except: st.error("Error al procesar fechas de tiendas.")

        st.markdown('<div class="titulo-seccion">STATUS IMPORTACIONES</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total = df_import["DOC"].nunique()
            arr = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].nunique()
            m1.metric("Total DOCs", total)
            m2.metric("Arribados", arr)
            m3.metric("En Tránsito", total - arr)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### ⏳ Pendientes")
                df_p = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_p.empty:
                    st.dataframe(df_p.groupby("DOC").size().reset_index(name="ASNs"), width="stretch", hide_index=True)
            with c2:
                st.markdown("### ✅ Arribados")
                df_a = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_a.empty:
                    st.dataframe(df_a.groupby(["DOC", "ETA"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Flujo de Recepción")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div style="background:#fff5f5;padding:10px;border-radius:10px;border-left:5px solid #ff4b4b;"><h4>🚨 RECEPCIONADO</h4></div>', unsafe_allow_html=True)
            df_p = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]
            if not df_p.empty:
                st.dataframe(df_p.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)
        with col2:
            st.markdown('<div style="background:#f0fff4;padding:10px;border-radius:10px;border-left:5px solid #28a745;"><h4>🏢 ALMACENADO</h4></div>', unsafe_allow_html=True)
            df_alm = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "ALMACENADO"]
            if not df_alm.empty:
                st.dataframe(df_alm.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)
        with col3:
            st.markdown('<div style="background:#fffaf0;padding:10px;border-radius:10px;border-left:5px solid #ffa500;"><h4>🚚 PROGRAMADO</h4></div>', unsafe_allow_html=True)
            df_prog = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PROGRAMADO"]
            if not df_prog.empty:
                st.dataframe(df_prog.groupby(["IMPORTACION", "ID_DESPACHO"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)

    with tab_ops:
        st.header("⚙️ Operaciones")
        o1, o2 = st.columns(2)
        with o1:
            st.subheader("Confirmar Arribo")
            docs = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].unique().tolist()
            if docs:
                with st.form("f_arribo"):
                    d_sel = st.selectbox("DOC", docs)
                    f_sel = st.date_input("Fecha", date.today())
                    if st.form_submit_button("Guardar"):
                        if update_consolidado_arribo(d_sel, f_sel):
                            st.success("OK"); st.cache_data.clear(); st.rerun()
            else: st.info("Sin pendientes.")
        with o2:
            st.subheader("Confirmar Almacenaje")
            asns = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
            if asns:
                with st.form("f_alm"):
                    a_sel = st.selectbox("ASN", asns)
                    fa_sel = st.date_input("Fecha Almacenado", date.today())
                    if st.form_submit_button("Guardar"):
                        if update_recepcion_almacenado(a_sel, fa_sel):
                            st.success("OK"); st.cache_data.clear(); st.rerun()
            else: st.info("Sin pendientes.")

elif menu == "🚚 Distribución":
    st.title("🚚 Distribución")
    st.info("Módulo en construcción.")

if st.sidebar.button("🔄 Sincronizar"):
    st.cache_data.clear()
    st.rerun()
