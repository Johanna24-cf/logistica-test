# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN FINAL CON LOGO Y APERTURAS
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN INICIAL Y LOGO
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# Insertar Logo desde el repositorio
try:
    st.image("CARCASAS.png", width=250)
except:
    st.warning("No se encontró el archivo CARCASAS.png en el repositorio.")

# 2. ESTILOS CSS
st.markdown("""
    <style>
    .stDataFrame { font-size: 12px; }
    .apertura-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 6px solid #6c5ce7; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 15px; min-height: 140px;
    }
    .titulo-seccion {
        color: #2d3436; font-weight: bold; font-size: 1.5rem;
        margin-top: 25px; margin-bottom: 15px;
        border-bottom: 3px solid #6c5ce7; padding-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE CONEXIÓN
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
    except: return None

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

# 4. FUNCIONES DE ACTUALIZACIÓN (CON LÓGICA X1-X9 Y ANTI-ERROR 429)
def update_consolidado_arribo(doc, fecha):
    try:
        # A. PROCESAR CONSOLIDADO (Batch Update)
        sh_cons = client.open("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_values = wks_cons.get_all_values()
        
        df_cons = pd.DataFrame(all_values[1:], columns=all_values[0])
        df_cons.columns = [str(c).strip().upper() for c in df_cons.columns]
        
        mask = df_cons["DOC"].astype(str) == str(doc)
        indices = df_cons[mask].index
        if len(indices) == 0: return False

        col_status_idx = df_cons.columns.get_loc("STATUS")
        col_fecha_idx = df_cons.columns.get_loc("FCH LLEGADA")

        for idx in indices:
            all_values[idx + 1][col_status_idx] = "ARRIBADO"
            all_values[idx + 1][col_fecha_idx] = str(fecha)
        
        wks_cons.update('A1', all_values)

        # B. TRASPASO A RECEPCIÓN (Lógica Condicional Completa)
        sh_rec = client.open("RECEPCION_IMPORTACIONES")
        wks_mov = sh_rec.worksheet("MOVIMIENTOS")
        
        filas_traspaso = df_cons.iloc[indices]
        lista_bulk = []
        
        for _, fila in filas_traspaso.iterrows():
            tienda_val = str(fila.get("TIENDA", "")).strip()
            
            # --- LÓGICA DE PROCESO Y DESTINO ---
            if tienda_val == "4298":
                destino_final = "ALMACENAJE"
                proceso_final = "POR ALMACENAR"
            else:
                destino_final = "TIENDA"
                # Regla: Buscar "APERTURA" en columnas X1 a X9
                columnas_x = [f"X{i}" for i in range(1, 10)]
                es_apertura = any("APERTURA" in str(fila.get(col, "")).upper() for col in columnas_x)
                proceso_final = "APERTURA" if es_apertura else "POR DISTRIBUIR"
            
            # Mapeo según image_e72909.png
            lista_bulk.append([
                fila.get("ID_DESPACHO", fila.get("ID", "")), # A: ID_DESPACH
                fila.get("DOC", ""),                         # B: IMPORTACION
                fila.get("ASN", ""),                         # C: ASN
                tienda_val,                                  # D: TIENDA
                fila.get("CANTIDAD", ""),                    # E: CANTIDAD
                "Pendiente",                                 # F: STATUS_REC
                str(fecha),                                  # G: FCH LLEGADA
                fila.get("ETA", ""),                         # H: ETA
                destino_final,                               # I: DESTINO
                proceso_final,                               # J: PROCESO
                ""                                           # K: FECHA ENTREGA
            ])
        
        wks_mov.append_rows(lista_bulk)
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

def update_recepcion_almacenado(asn, fecha):
    try:
        sheet = abrir_hoja("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
        all_data = sheet.get_all_values()
        df = pd.DataFrame(all_data[1:], columns=all_data[0])
        df.columns = [str(c).strip().upper() for c in df.columns]
        indices = df[df["ASN"].astype(str) == str(asn)].index
        col_status_idx = df.columns.get_loc("STATUS_REC")
        col_fecha_idx = df.columns.get_loc("FCH_ALMACENADO") if "FCH_ALMACENADO" in df.columns else 11
        for idx in indices:
            all_data[idx + 1][col_status_idx] = "ALMACENADO"
            all_data[idx + 1][col_fecha_idx] = str(fecha)
        sheet.update('A1', all_data)
        return True
    except: return False

# 5. CARGA DE DATOS
with st.spinner("Actualizando sistema..."):
    df_import = cargar_df("Consolidado - Carcasas")
    df_recepcion = cargar_df("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
    df_tiendas = cargar_df("TIENDAS CARCASAS")

# 6. INTERFAZ
st.title("📦 Gestión Logística de Importaciones")
menu = st.sidebar.radio("MENÚ", ["📊 Dashboard", "⚙️ Operaciones"])

if menu == "📊 Dashboard":
    tab1, tab2 = st.tabs(["📑 Importaciones", "📥 Recepción"])
    
    with tab1:
        st.subheader("🏪 Próximas Aperturas")
        if not df_tiendas.empty:
            try:
                df_ap = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
                df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors="coerce")
                df_filtrado = df_ap[(df_ap["FCH_DT"] >= datetime.now())].sort_values("FCH_DT").head(4)
                cols = st.columns(4)
                for i, (_, row) in enumerate(df_filtrado.iterrows()):
                    with cols[i % 4]:
                        st.markdown(f'<div class="apertura-card"><b>🏪 {row["TIENDA"]}</b><br>{row["DESCRIPCION"]}<br>📅 {row["FCH ESTIMADA"]}</div>', unsafe_allow_html=True)
            except: pass

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2 = st.columns(2)
            m1.metric("Docs Arribados", df_import[df_import["STATUS"] == "ARRIBADO"]["DOC"].nunique())
            m2.metric("Docs en Tránsito", df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].nunique())
            st.dataframe(df_import[["DOC", "ETA", "STATUS"]].drop_duplicates(), hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("Flujo de Almacén")
        if not df_recepcion.empty:
            st.dataframe(df_recepcion[["IMPORTACION", "ASN", "TIENDA", "DESTINO", "PROCESO", "STATUS_REC"]], hide_index=True)

else:
    st.header("⚙️ Operaciones")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Registrar Arribo")
        docs_pend = df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].unique().tolist()
        if docs_pend:
            with st.form("arribo"):
                d = st.selectbox("Seleccione Importación", docs_pend)
                f = st.date_input("Fecha de Arribo", date.today())
                if st.form_submit_button("Confirmar Arribo"):
                    if update_consolidado_arribo(d, f):
                        st.success("¡Datos traspasados correctamente!"); st.cache_data.clear(); st.rerun()
    with col_b:
        st.subheader("Confirmar Almacenaje")
        if not df_recepcion.empty:
            asns = df_recepcion[df_recepcion["STATUS_REC"] == "Pendiente"]["ASN"].unique().tolist()
            if asns:
                with st.form("stock"):
                    a = st.selectbox("ASN", asns)
                    fs = st.date_input("Fecha Stock", date.today())
                    if st.form_submit_button("Confirmar Ingreso"):
                        if update_recepcion_almacenado(a, fs):
                            st.success("¡Stock actualizado!"); st.cache_data.clear(); st.rerun()

if st.sidebar.button("🔄 Refrescar Datos"):
    st.cache_data.clear(); st.rerun()
