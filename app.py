# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN FINAL INTEGRAL
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# 2. LOGO Y ESTILOS
@st.cache_data
def mostrar_logo():
    if os.path.exists("CARCASAS.png"):
        st.image("CARCASAS.png", width=250)
    else:
        st.info("Logo CARCASAS.png no encontrado en el repositorio.")

mostrar_logo()

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

# 3. CONEXIÓN A GOOGLE SHEETS
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

client = conectar_google()

@st.cache_data(ttl=300)
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

# 4. FUNCIONES DE PROCESAMIENTO
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

        for idx in indices:
            all_values[idx + 1][col_status_idx] = "ARRIBADO"
            all_values[idx + 1][col_fecha_idx] = str(fecha)
        
        wks_cons.update('A1', all_values)

        # Traspaso con Lógica de Negocio
        sh_rec = client.open("RECEPCION_IMPORTACIONES")
        wks_mov = sh_rec.worksheet("MOVIMIENTOS")
        
        lista_bulk = []
        for _, fila in df_temp[mask].iterrows():
            tienda = str(fila.get("TIENDA", "")).strip()
            # REGLA 4298 vs APERTURA
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
        st.error(f"Error técnico: {e}")
        return False

# 5. CARGA INICIAL
df_import, df_recep, df_tiendas = cargar_datos_completos()

# 6. INTERFAZ DE USUARIO
st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dash Importacion", "📑 Dash Recepción", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas")
        if not df_tiendas.empty:
            try:
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
            except: pass

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total_docs = df_import["DOC"].nunique()
            arr_docs = df_import[df_import["STATUS"] == "ARRIBADO"]["DOC"].nunique()
            m1.metric("Total Docs", total_docs)
            m2.metric("Arribados", arr_docs)
            m3.metric("En Tránsito", total_docs - arr_docs)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("### ⏳ Pendientes")
                df_p = df_import[df_import["STATUS"] != "ARRIBADO"]
                if not df_p.empty:
                    st.dataframe(df_p.groupby(["DOC", "ETA", "STATUS"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)
            with c2:
                st.write("### ✅ Arribados")
                df_a = df_import[df_import["STATUS"] == "ARRIBADO"]
                if not df_a.empty:
                    st.dataframe(df_a.groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Dash Recepción")
        if not df_recep.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("🚨 **PENDIENTE**")
                df_pen = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]
                if not df_pen.empty:
                    st.dataframe(df_pen.groupby(["IMPORTACION", "DESTINO", "PROCESO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            
            with col2:
                st.success("🏢 **EN STOCK**")
                df_stock = df_recep[df_recep["STATUS_REC"].str.upper() == "ALMACENADO"]
                if not df_stock.empty:
                    st.dataframe(df_stock.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            
            with col3:
                st.warning("🚚 **PROGRAMADO / ENTREGADO**")
                # Lógica: Mostrar Programados y Entregados juntos
                df_prog_ent = df_recep[df_recep["STATUS_REC"].str.upper().isin(["PROGRAMADO", "ENTREGADO"])]
                if not df_prog_ent.empty:
                    df_res = df_prog_ent.groupby(["FECHA ENTREGA", "IMPORTACION","STATUS_REC"]).size().reset_index(name="BULTOS")
                    st.dataframe(df_res, use_container_width=True, hide_index=True)
                else:
                    st.write("No hay registros.")

    with tab_ops:
        st.header("⚙️ Operaciones")
        # Fragmento para agilizar la UI
        @st.fragment
        def ops_panel():
            o1, o2 = st.columns(2)
            with o1:
                st.subheader("Confirmar Arribo")
                docs = df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].unique().tolist() if not df_import.empty else []
                if docs:
                    with st.form("arribo_f", clear_on_submit=True):
                        d = st.selectbox("Documento", docs)
                        f = st.date_input("Fecha LLegada", date.today())
                        if st.form_submit_button("Registrar Arribo"):
                            if update_consolidado_arribo(d, f):
                                st.success("Registrado correctamente")
                                st.cache_data.clear()
                                st.rerun()
            with o2:
                st.subheader("Confirmar Stock")
                if not df_recep.empty:
                    asns = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                    if asns:
                        with st.form("stock_f", clear_on_submit=True):
                            a = st.selectbox("ASN", asns)
                            fs = st.date_input("Fecha Stock", date.today())
                            if st.form_submit_button("Confirmar Ingreso"):
                                # Lógica rápida de actualización de stock
                                try:
                                    sh_r = client.open("RECEPCION_IMPORTACIONES")
                                    w_m = sh_r.worksheet("MOVIMIENTOS")
                                    data = w_m.get_all_values()
                                    header = [c.upper() for c in data[0]]
                                    idx_asn = header.index("ASN")
                                    idx_st = header.index("STATUS_REC")
                                    for i, row in enumerate(data):
                                        if row[idx_asn] == str(a):
                                            data[i][idx_st] = "ALMACENADO"
                                    w_m.update('A1', data)
                                    st.success("Stock actualizado")
                                    st.cache_data.clear()
                                    st.rerun()
                                except: st.error("Error al actualizar")
        ops_panel()

if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear()
    st.rerun()
