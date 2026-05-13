# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN FINAL INTEGRAL
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# 2. ESTILOS CSS PARA MEJORAR LA INTERFAZ
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

# 3. FUNCIONES DE CONEXIÓN A GOOGLE SHEETS
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
        # Normalizamos nombres de columnas a Mayúsculas y sin espacios laterales
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df.astype(str)
    return pd.DataFrame()

# 4. FUNCIONES DE ACTUALIZACIÓN CON LÓGICA DE NEGOCIO
def update_consolidado_arribo(doc, fecha):
    try:
        # A. Actualizar Status en el Consolidado
        sh_cons = client.open("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        df_cons = pd.DataFrame(wks_cons.get_all_records())
        df_cons.columns = [str(c).strip().upper() for c in df_cons.columns]
        
        indices = df_cons[df_cons["DOC"].astype(str) == str(doc)].index
        if len(indices) == 0: return False

        col_status_idx = df_cons.columns.get_loc("STATUS") + 1
        col_fecha_idx = df_cons.columns.get_loc("FCH LLEGADA") + 1
        
        for idx in indices:
            wks_cons.update_cell(idx + 2, col_status_idx, "ARRIBADO")
            wks_cons.update_cell(idx + 2, col_fecha_idx, str(fecha))
        
        # B. Traspaso Masivo a RECEPCION_IMPORTACIONES (Hoja MOVIMIENTOS)
        sh_rec = client.open("RECEPCION_IMPORTACIONES")
        wks_mov = sh_rec.worksheet("MOVIMIENTOS")
        
        filas_traspaso = df_cons.iloc[indices]
        lista_bulk = []
        
        for _, fila in filas_traspaso.iterrows():
            tienda_val = str(fila.get("TIENDA", "")).strip()
            
            # --- LÓGICA SOLICITADA ---
            if tienda_val == "4298":
                destino_final = "ALMACENAJE"
                proceso_final = "POR ALMACENAR"
            else:
                destino_final = "TIENDA"
                proceso_final = "POR DISTRIBUIR"
            
            # Mapeo según estructura de columnas en tu Excel
            nueva_fila = [
                fila.get("ID_DESPACHO", fila.get("ID", "")), # A: ID_DESPACH
                fila.get("DOC", ""),                         # B: IMPORTACION
                fila.get("ASN", ""),                         # C: ASN
                tienda_val,                                  # D: TIENDA
                fila.get("CANTIDAD", ""),                    # E: CANTIDAD
                "Pendiente",                                 # F: STATUS_REC
                str(fecha),                                  # G: FCH LLEGADA (ARRIBO)
                fila.get("ETA", ""),                         # H: ETA
                destino_final,                               # I: DESTINO
                proceso_final,                               # J: PROCESO
                ""                                           # K: FECHA ENTREGA
            ]
            lista_bulk.append(nueva_fila)
        
        # Enviamos todo de una vez para evitar errores de cuota de la API
        wks_mov.append_rows(lista_bulk)
        return True
    except Exception as e:
        st.error(f"Error técnico en el proceso: {e}")
        return False

def update_recepcion_almacenado(asn, fecha):
    try:
        sheet = abrir_hoja("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        indices = df[df["ASN"].astype(str) == str(asn)].index
        col_status = df.columns.get_loc("STATUS_REC") + 1
        col_fecha = df.columns.get_loc("FCH_ALMACENADO") + 1 if "FCH_ALMACENADO" in df.columns else 12
        
        for idx in indices:
            sheet.update_cell(idx + 2, col_status, "ALMACENADO")
            sheet.update_cell(idx + 2, col_fecha, str(fecha))
        return True
    except: return False

# 5. CARGA DE DATOS INICIAL
with st.spinner("Sincronizando con base de datos..."):
    df_import = cargar_df("Consolidado - Carcasas")
    df_recepcion = cargar_df("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
    df_tiendas = cargar_df("TIENDAS CARCASAS")

# 6. MENÚ Y NAVEGACIÓN
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    st.title("📦 Gestión de Importaciones")
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dash Importacion", "📑 Dash Recepción", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas")
        if not df_tiendas.empty:
            try:
                df_ap = df_tiendas[df_tiendas["ESTADO"].str.upper().str.contains("PENDIENTE", na=False)].copy()
                df_ap["FCH_DT"] = pd.to_datetime(df_ap["FCH ESTIMADA"], dayfirst=True, errors="coerce")
                hoy = datetime.now()
                df_filtrado = df_ap[(df_ap["FCH_DT"] >= hoy) & (df_ap["FCH_DT"] <= hoy + timedelta(days=60))].sort_values("FCH_DT")
                if not df_filtrado.empty:
                    cols = st.columns(4)
                    for i, (_, row) in enumerate(df_filtrado.iterrows()):
                        with cols[i % 4]:
                            st.markdown(f'<div class="apertura-card"><div class="tienda-titulo">🏪 {row["TIENDA"]}</div><div class="desc-tienda">{row["DESCRIPCION"]}</div><div class="fecha-est">📅 {row["FCH ESTIMADA"]}</div></div>', unsafe_allow_html=True)
                else: st.info("No hay aperturas próximas en los siguientes 60 días.")
            except: st.error("Error al procesar el calendario de aperturas.")

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL IMPORTACIONES</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total = df_import["DOC"].nunique()
            arr = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].nunique()
            m1.metric("Total Importaciones", total)
            m2.metric("Ya Arribados", arr)
            m3.metric("En Nave / Tránsito", total - arr)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### ⏳ Pendientes por Arribar")
                df_p = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_p.empty:
                    st.dataframe(df_p.groupby(["DOC", "ETA", "STATUS"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)
            with c2:
                st.markdown("### ✅ Histórico de Arribos")
                df_a = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_a.empty:
                    st.dataframe(df_a.groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Flujo de Recepción y Almacén")
        if not df_recepcion.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div style="background:#fff5f5;padding:10px;border-radius:10px;border-left:5px solid #ff4b4b;"><h4>🚨 POR ALMACENAR</h4></div>', unsafe_allow_html=True)
                df_p_rec = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]
                if not df_p_rec.empty: st.dataframe(df_p_rec.groupby(["IMPORTACION", "DESTINO", "PROCESO"]).size().reset_index(name="BULTOS"), width="stretch", hide_index=True)
            with col2:
                st.markdown('<div style="background:#f0fff4;padding:10px;border-radius:10px;border-left:5px solid #28a745;"><h4>🏢 EN STOCK</h4></div>', unsafe_allow_html=True)
                df_alm = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "ALMACENADO"]
                if not df_alm.empty: st.dataframe(df_alm.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="BULTOS"), width="stretch", hide_index=True)
            with col3:
                st.markdown('<div style="background:#fffaf0;padding:10px;border-radius:10px;border-left:5px solid #ffa500;"><h4>🚚 PROGRAMADO</h4></div>', unsafe_allow_html=True)
                df_prog = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PROGRAMADO"]
                if not df_prog.empty:
                    cid = "ID_DESPACHO" if "ID_DESPACHO" in df_prog.columns else "DESTINO"
                    st.dataframe(df_prog.groupby(["FECHA ENTREGA", "IMPORTACION", cid]).size().reset_index(name="BULTOS"), width="stretch", hide_index=True)
        else: st.warning("No hay datos registrados en el flujo de recepción.")

    with tab_ops:
        st.header("⚙️ Operaciones de Registro")
        o1, o2 = st.columns(2)
        with o1:
            st.subheader("1. Confirmar Arribo de Nave")
            docs_pend = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].unique().tolist()
            if docs_pend:
                with st.form("f_arribo"):
                    d_sel = st.selectbox("Seleccione DOC / Importación", docs_pend)
                    f_sel = st.date_input("Fecha de Arribo Real", date.today())
                    st.info("Nota: Esta acción moverá automáticamente todos los bultos a la hoja de Recepción.")
                    if st.form_submit_button("Confirmar Arribo Masivo"):
                        if update_consolidado_arribo(d_sel, f_sel):
                            st.success("¡Operación completada con éxito!"); st.cache_data.clear(); st.rerun()
            else: st.info("No hay importaciones pendientes de arribo.")
        with o2:
            st.subheader("2. Confirmar Ingreso a Almacén")
            if not df_recepcion.empty:
                asns_pend = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                if asns_pend:
                    with st.form("f_alm"):
                        a_sel = st.selectbox("Seleccione ASN / Bulto", asns_pend)
                        fa_sel = st.date_input("Fecha de Ingreso a Stock", date.today())
                        if st.form_submit_button("Confirmar Almacenaje"):
                            if update_recepcion_almacenado(a_sel, fa_sel):
                                st.success("¡ASN actualizado!"); st.cache_data.clear(); st.rerun()
                else: st.info("No hay bultos pendientes de almacenamiento en este momento.")

elif menu == "🚚 Distribución":
    st.title("🚚 Módulo de Distribución")
    st.info("Este módulo está destinado a la gestión de rutas y despachos finales (En construcción).")

if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear(); st.rerun()
