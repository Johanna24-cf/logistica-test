# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN FINAL ULTRA-OPTIMIZADA
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Sistema Logístico Carcasas", page_icon="📦", layout="wide")

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

# 4. FUNCIONES DE ACTUALIZACIÓN (BATCH UPDATE PARA EVITAR ERROR 429)
def update_consolidado_arribo(doc, fecha):
    try:
        # A. PROCESAR CONSOLIDADO
        sh_cons = client.open("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        data_cons = wks_cons.get_all_records()
        df_cons = pd.DataFrame(data_cons)
        df_cons.columns = [str(c).strip().upper() for c in df_cons.columns]
        
        mask = df_cons["DOC"].astype(str) == str(doc)
        indices = df_cons[mask].index
        if len(indices) == 0: return False

        # Identificar columnas
        col_status_idx = df_cons.columns.get_loc("STATUS")
        col_fecha_idx = df_cons.columns.get_loc("FCH LLEGADA")

        # B. ACTUALIZACIÓN MASIVA EN CONSOLIDADO (Rango completo)
        # Obtenemos todos los valores actuales, modificamos en memoria y subimos TODO el rango
        all_values = wks_cons.get_all_values()
        for idx in indices:
            all_values[idx + 1][col_status_idx] = "ARRIBADO"
            all_values[idx + 1][col_fecha_idx] = str(fecha)
        
        wks_cons.update('A1', all_values) # Una sola petición de escritura para todo el sheet

        # C. TRASPASO MASIVO A RECEPCIÓN
        sh_rec = client.open("RECEPCION_IMPORTACIONES")
        wks_mov = sh_rec.worksheet("MOVIMIENTOS")
        
        filas_traspaso = df_cons.iloc[indices]
        lista_bulk = []
        
        for _, fila in filas_traspaso.iterrows():
            tienda_val = str(fila.get("TIENDA", "")).strip()
            dest, proc = ("ALMACENAJE", "POR ALMACENAR") if tienda_val == "4298" else ("TIENDA", "POR DISTRIBUIR")
            
            lista_bulk.append([
                fila.get("ID_DESPACHO", fila.get("ID", "")), # A
                fila.get("DOC", ""),                         # B
                fila.get("ASN", ""),                         # C
                tienda_val,                                  # D
                fila.get("CANTIDAD", ""),                    # E
                "Pendiente",                                 # F
                str(fecha),                                  # G
                fila.get("ETA", ""),                         # H
                dest,                                        # I
                proc,                                        # J
                ""                                           # K
            ])
        
        wks_mov.append_rows(lista_bulk) # Una sola petición de escritura
        return True
    except Exception as e:
        st.error(f"Error de Cuota: {e}")
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
with st.spinner("Sincronizando..."):
    df_import = cargar_df("Consolidado - Carcasas")
    df_recepcion = cargar_df("RECEPCION_IMPORTACIONES", "MOVIMIENTOS")
    df_tiendas = cargar_df("TIENDAS CARCASAS")

# 6. INTERFAZ
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
                cols = st.columns(4)
                for i, (_, row) in enumerate(df_filtrado.iterrows()):
                    with cols[i % 4]:
                        st.markdown(f'<div class="apertura-card"><div class="tienda-titulo">🏪 {row["TIENDA"]}</div><div class="desc-tienda">{row["DESCRIPCION"]}</div><div class="fecha-est">📅 {row["FCH ESTIMADA"]}</div></div>', unsafe_allow_html=True)
            except: pass

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total = df_import["DOC"].nunique()
            arr = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].nunique()
            m1.metric("Total Docs", total); m2.metric("Arribados", arr); m3.metric("En Tránsito", total - arr)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### ⏳ Pendientes")
                df_p = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_p.empty: st.dataframe(df_p.groupby(["DOC", "ETA", "STATUS"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)
            with c2:
                st.markdown("### ✅ Arribados")
                df_a = df_import[df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]
                if not df_a.empty: st.dataframe(df_a.groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), width="stretch", hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Flujo de Almacén")
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

    with tab_ops:
        st.header("⚙️ Operaciones")
        o1, o2 = st.columns(2)
        with o1:
            st.subheader("1. Confirmar Arribo")
            docs_pend = df_import[~df_import["STATUS"].str.upper().str.contains("ARRIBADO", na=False)]["DOC"].unique().tolist()
            if docs_pend:
                with st.form("f_arribo"):
                    d_sel = st.selectbox("Seleccione DOC", docs_pend)
                    f_sel = st.date_input("Fecha Arribo Real", date.today())
                    if st.form_submit_button("Confirmar Arribo Masivo"):
                        if update_consolidado_arribo(d_sel, f_sel):
                            st.success("¡Todo actualizado!"); st.cache_data.clear(); st.rerun()
            else: st.info("No hay importaciones pendientes.")
        with o2:
            st.subheader("2. Confirmar Almacenaje")
            if not df_recepcion.empty:
                asns_pend = df_recepcion[df_recepcion["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                if asns_pend:
                    with st.form("f_alm"):
                        a_sel = st.selectbox("ASN", asns_pend); fa_sel = st.date_input("Fecha Stock", date.today())
                        if st.form_submit_button("Confirmar Stock"):
                            if update_recepcion_almacenado(a_sel, fa_sel):
                                st.success("¡Stock actualizado!"); st.cache_data.clear(); st.rerun()

elif menu == "🚚 Distribución":
    st.title("🚚 Distribución")
    st.info("Próximamente.")

if st.sidebar.button("🔄 Sincronizar"):
    st.cache_data.clear(); st.rerun()
