# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN PRO OPTIMIZADA
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Logístico Carcasas", page_icon="📦", layout="wide")

# 2. LOGO Y ESTILOS (Refactorizado para limpieza)
def cargar_estilos():
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

@st.cache_data
def mostrar_logo():
    if os.path.exists("CARCASAS.png"): st.image("CARCASAS.png", width=250)

cargar_estilos()
mostrar_logo()

# 3. CONEXIÓN Y CARGA (Optimizado con ttl más agresivo)
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}"); return None

client = conectar_google()

@st.cache_data(ttl=600) # 10 minutos de cache para navegación fluida
def cargar_datos_completos():
    def fetch(nombre, hoja=None):
        try:
            sh = client.open(nombre)
            wks = sh.worksheet(hoja) if hoja else sh.sheet1
            data = wks.get_all_records()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df.astype(str)
        except: return pd.DataFrame()
    return fetch("Consolidado - Carcasas"), fetch("RECEPCION_IMPORTACIONES", "MOVIMIENTOS"), fetch("TIENDAS CARCASAS")

# 4. FUNCIONES DE PROCESAMIENTO (ACTUALIZACIÓN QUIRÚRGICA)
def update_consolidado_arribo(doc, fecha):
    try:
        sh_cons = client.open("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_data = wks_cons.get_all_values()
        headers = [h.upper() for h in all_data[0]]
        
        col_doc = headers.index("DOC")
        col_status = headers.index("STATUS")
        col_fecha = headers.index("FCH LLEGADA")
        
        # Encontrar filas y preparar actualización masiva
        cells_to_update = []
        filas_para_traspaso = []
        
        for i, row in enumerate(all_data[1:], start=2):
            if row[col_doc] == str(doc):
                # Actualizar Status
                cells_to_update.append(gspread.Cell(i, col_status + 1, "ARRIBADO"))
                # Actualizar Fecha
                cells_to_update.append(gspread.Cell(i, col_fecha + 1, str(fecha)))
                filas_para_traspaso.append(row)

        if cells_to_update:
            wks_cons.update_cells(cells_to_update) # Mucho más rápido que update('A1')

            # Traspaso Batch a Recepción
            sh_rec = client.open("RECEPCION_IMPORTACIONES")
            wks_mov = sh_rec.worksheet("MOVIMIENTOS")
            
            bulk_data = []
            for row in filas_para_traspaso:
                tienda = row[headers.index("TIENDA")].strip()
                # Lógica de destino
                if tienda == "4298": dest, proc = "ALMACENAJE", "POR ALMACENAR"
                else:
                    dest = "TIENDA"
                    # Escaneo rápido de APERTURA en columnas X
                    es_ap = any("APERTURA" in str(row[headers.index(f"X{j}")]).upper() 
                                for j in range(1, 10) if f"X{j}" in headers)
                    proc = "APERTURA" if es_ap else "POR DISTRIBUIR"
                
                bulk_data.append([
                    row[headers.index("ID_DESPACHO")] if "ID_DESPACHO" in headers else row[0], 
                    row[col_doc], row[headers.index("ASN")], tienda, 
                    row[headers.index("CANTIDAD")], "Pendiente", str(fecha), 
                    row[headers.index("ETA")], dest, proc, ""
                ])
            wks_mov.append_rows(bulk_data)
            return True
    except Exception as e:
        st.error(f"Error técnico: {e}"); return False

# 5. UI Y RENDERIZADO
df_import, df_recep, df_tiendas = cargar_datos_completos()

st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dash Importacion", "📑 Dash Recepción", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas")
        if not df_tiendas.empty:
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

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        if not df_import.empty:
            m1, m2, m3 = st.columns(3)
            total = df_import["DOC"].nunique()
            arribados = df_import[df_import["STATUS"] == "ARRIBADO"]["DOC"].nunique()
            m1.metric("Total Docs", total)
            m2.metric("Arribados", arribados)
            m3.metric("En Tránsito", total - arribados)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("### ⏳ Pendientes")
                st.dataframe(df_import[df_import["STATUS"] != "ARRIBADO"].groupby(["DOC", "ETA", "STATUS"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)
            with c2:
                st.write("### ✅ Arribados")
                st.dataframe(df_import[df_import["STATUS"] == "ARRIBADO"].groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)

    with tab_recep:
        st.markdown("### 🗺️ Dash Recepción")
        if not df_recep.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("🚨 **PENDIENTE**")
                df_p = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]
                st.dataframe(df_p.groupby(["IMPORTACION", "DESTINO", "PROCESO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            with col2:
                st.success("🏢 **EN STOCK**")
                df_s = df_recep[df_recep["STATUS_REC"].str.upper() == "ALMACENADO"]
                st.dataframe(df_s.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            with col3:
                st.warning("🚚 **PROGRAMADO / ENTREGADO**")
                df_pe = df_recep[df_recep["STATUS_REC"].str.upper().isin(["PROGRAMADO", "ENTREGADO"])]
                st.dataframe(df_pe.groupby(["FECHA ENTREGA", "IMPORTACION", "STATUS_REC"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)

    with tab_ops:
        st.header("⚙️ Operaciones")
        @st.fragment
        def ops_panel():
            o1, o2 = st.columns(2)
            with o1:
                st.subheader("Confirmar Arribo")
                docs = df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].unique().tolist() if not df_import.empty else []
                with st.form("arribo_f", clear_on_submit=True):
                    d = st.selectbox("Documento", docs)
                    f = st.date_input("Fecha LLegada", date.today())
                    if st.form_submit_button("Registrar Arribo"):
                        if update_consolidado_arribo(d, f):
                            st.toast("¡Arribo registrado!", icon="✅")
                            st.cache_data.clear(); st.rerun()
            with o2:
                st.subheader("Confirmar Stock")
                if not df_recep.empty:
                    asns = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                    with st.form("stock_f", clear_on_submit=True):
                        a = st.selectbox("ASN", asns)
                        if st.form_submit_button("Confirmar Ingreso"):
                            try:
                                sh_r = client.open("RECEPCION_IMPORTACIONES")
                                w_m = sh_r.worksheet("MOVIMIENTOS")
                                cell = w_m.find(str(a))
                                # Asumiendo que STATUS_REC es la columna 6 (F)
                                w_m.update_cell(cell.row, 6, "ALMACENADO")
                                st.toast("Stock actualizado", icon="🏢")
                                st.cache_data.clear(); st.rerun()
                            except: st.error("ASN no encontrado o error de red")
        ops_panel()

if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear(); st.rerun()
