# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - VERSIÓN PRO OPTIMIZADA (HORA FECH FIX)
# =========================================================

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Logístico Carcasas", page_icon="📦", layout="wide")

# 2. LOGO Y ESTILOS
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

# 3. CONEXIÓN Y CARGA
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}"); return None

client = conectar_google()

def abrir_archivo_dinamico(nombre_o_id):
    if len(nombre_o_id) > 25:
        return client.open_by_key(nombre_o_id)
    return client.open(nombre_o_id)

@st.cache_data(ttl=600)
def cargar_datos_completos():
    def fetch(nombre_o_id, hoja=None):
        try:
            sh = abrir_archivo_dinamico(nombre_o_id)
            wks = sh.worksheet(hoja) if hoja else sh.sheet1
            data = wks.get_all_records()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df.astype(str)
        except: return pd.DataFrame()
    
    return fetch("Consolidado - Carcasas"), fetch("RECEPCION_IMPORTACIONES", "MOVIMIENTOS"), fetch("TIENDAS CARCASAS")

# 4. FUNCIONES DE PROCESAMIENTO
def update_consolidado_arribo(doc, fecha):
    try:
        sh_cons = abrir_archivo_dinamico("Consolidado - Carcasas")
        wks_cons = sh_cons.sheet1
        all_data = wks_cons.get_all_values()
        headers = [h.upper() for h in all_data[0]]
        
        col_doc = headers.index("DOC")
        col_status = headers.index("STATUS")
        col_fecha = headers.index("FCH LLEGADA")
        
        cells_to_update = []
        filas_para_traspaso = []
        
        for i, row in enumerate(all_data[1:], start=2):
            if row[col_doc] == str(doc):
                cells_to_update.append(gspread.Cell(i, col_status + 1, "ARRIBADO"))
                cells_to_update.append(gspread.Cell(i, col_fecha + 1, str(fecha)))
                filas_para_traspaso.append(row)

        if cells_to_update:
            wks_cons.update_cells(cells_to_update)

            sh_rec = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
            wks_mov = sh_rec.worksheet("MOVIMIENTOS")
            
            bulk_data = []
            for row in filas_para_traspaso:
                tienda = row[headers.index("TIENDA")].strip()
                if tienda == "4298": dest, proc = "ALMACENAJE", "POR ALMACENAR"
                else:
                    dest = "TIENDA"
                    es_ap = any("APERTURA" in str(row[headers.index(f"X{j}")]).upper() 
                                for j in range(1, 10) if f"X{j}" in headers)
                    proc = "APERTURA" if es_ap else "POR DISTRIBUIR"
                
                # Usamos HORA FECH en lugar de ETA para el traspaso de datos
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

# 5. UI Y RENDERIZADO
df_import, df_recep, df_tiendas = cargar_datos_completos()

st.title("📦 Gestión de Importaciones")
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📦 Importaciones", "🚚 Distribución"])

if menu == "📦 Importaciones":
    tab_dash, tab_recep, tab_ops = st.tabs(["📊 Dash Importacion", "📑 Gestión interna", "⚙️ Operaciones"])

    with tab_dash:
        st.subheader("🏪 Próximas Aperturas")
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
                st.warning("⚠️ Columnas faltantes en 'TIENDAS CARCASAS' (Requiere: ESTADO, FCH ESTIMADA, TIENDA, DESCRIPCION)")

        st.markdown('<div class="titulo-seccion">STATUS GLOBAL</div>', unsafe_allow_html=True)
        if not df_import.empty:
            # CAMBIO DETECTADO: Ahora se requiere "HORA FECH" en lugar de "ETA"
            columnas_import_req = ["DOC", "HORA FECH", "STATUS", "FCH LLEGADA"]
            columnas_faltantes = [c for c in columnas_import_req if c not in df_import.columns]
            
            if columnas_faltantes:
                st.error(f"❌ **Estructura incorrecta en la hoja 'Consolidado - Carcasas':** Falta la(s) columna(s): {', '.join(columnas_faltantes)}")
                st.info("Asegúrate de que los encabezados del Google Sheets contengan exactamente estas columnas.")
            else:
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
                    # Agrupación corregida con "HORA FECH"
                    st.dataframe(df_import[df_import["STATUS"] != "ARRIBADO"].groupby(["DOC", "HORA FECH", "STATUS"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)
                with c2:
                    st.write("### ✅ Arribados")
                    st.dataframe(df_import[df_import["STATUS"] == "ARRIBADO"].groupby(["DOC", "FCH LLEGADA"]).size().reset_index(name="ASNs"), use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ La hoja 'Consolidado - Carcasas' está vacía o no se pudo cargar.")

    with tab_recep:
        st.markdown("### 🗺️ Dash Recepción")
        if not df_recep.empty:
            columnas_recep_req = ["STATUS_REC", "IMPORTACION", "DESTINO", "PROCESO"]
            if all(col in df_recep.columns for col in columnas_recep_req):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info("🚨 **PENDIENTE**")
                    df_p = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]
                    if not df_p.empty:
                        st.dataframe(df_p.groupby(["IMPORTACION", "DESTINO", "PROCESO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
                with col2:
                    st.success("🏢 **EN STOCK**")
                    df_s = df_recep[df_recep["STATUS_REC"].str.upper() == "ALMACENADO"]
                    if not df_s.empty:
                        st.dataframe(df_s.groupby(["IMPORTACION", "DESTINO"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
                with col3:
                    st.warning("🚚 **PROGRAMADO / ENTREGADO**")
                    df_pe = df_recep[df_recep["STATUS_REC"].str.upper().isin(["PROGRAMADO", "ENTREGADO"])]
                    if not df_pe.empty and "FECHA ENTREGA" in df_recep.columns:
                        st.dataframe(df_pe.groupby(["FECHA ENTREGA", "IMPORTACION", "STATUS_REC"]).size().reset_index(name="BULTOS"), use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Estructura incorrecta en la hoja 'RECEPCION_IMPORTACIONES'.")

    with tab_ops:
        st.header("⚙️ Operaciones")
        @st.fragment
        def ops_panel():
            o1, o2 = st.columns(2)
            with o1:
                st.subheader("Confirmar Arribo")
                docs = df_import["DOC"].unique().tolist() if not df_import.empty and "DOC" in df_import.columns else []
                if "STATUS" in df_import.columns:
                    docs = df_import[df_import["STATUS"] != "ARRIBADO"]["DOC"].unique().tolist()
                
                with st.form("arribo_f", clear_on_submit=True):
                    d = st.selectbox("Documento", docs)
                    f = st.date_input("Fecha LLegada", date.today())
                    if st.form_submit_button("Registrar Arribo"):
                        if update_consolidado_arribo(d, f):
                            st.toast("¡Arribo registrado!", icon="✅")
                            st.cache_data.clear(); st.rerun()
            with o2:
                st.subheader("Confirmar Stock")
                if not df_recep.empty and "STATUS_REC" in df_recep.columns and "ASN" in df_recep.columns:
                    asns = df_recep[df_recep["STATUS_REC"].str.upper() == "PENDIENTE"]["ASN"].unique().tolist()
                    with st.form("stock_f", clear_on_submit=True):
                        a = st.selectbox("ASN", asns)
                        if st.form_submit_button("Confirmar Ingreso"):
                            try:
                                sh_r = abrir_archivo_dinamico("RECEPCION_IMPORTACIONES")
                                w_m = sh_r.worksheet("MOVIMIENTOS")
                                cell = w_m.find(str(a))
                                w_m.update_cell(cell.row, 6, "ALMACENADO")
                                st.toast("Stock actualizado", icon="🏢")
                                st.cache_data.clear(); st.rerun()
                            except: st.error("ASN no encontrado o error de red")
        ops_panel()

if st.sidebar.button("🔄 Sincronizar Todo"):
    st.cache_data.clear(); st.rerun()
