# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - STREAMLIT CLOUD FINAL
# =========================================================

import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from datetime import date, datetime, timedelta

# =========================================================
# CONFIG PAGE
# =========================================================

st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.stDataFrame {
    font-size: 12px;
}

.apertura-card{
    background:#ffffff;
    padding:15px;
    border-radius:12px;
    border-left:5px solid #6c5ce7;
    box-shadow:0 2px 8px rgba(0,0,0,0.08);
    margin-bottom:15px;
    min-height:120px;
}

.tienda-titulo{
    font-size:1.1rem;
    font-weight:700;
    color:#2d3436;
}

.fecha-est{
    color:#d63031;
    font-weight:bold;
    font-size:0.9rem;
}

.titulo-seccion{
    color:#2d3436;
    font-weight:bold;
    font-size:1.6em;
    margin-top:25px;
    margin-bottom:15px;
    border-bottom:3px solid #6c5ce7;
    padding-bottom:8px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================

@st.cache_resource
def conectar_google():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = dict(st.secrets["gcp_service_account"])

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )

    client = gspread.authorize(creds)

    return client

client = conectar_google()

# =========================================================
# OPEN SHEETS
# =========================================================

def abrir_hoja(nombre_archivo, nombre_hoja=None):

    sh = client.open(nombre_archivo)

    if nombre_hoja:
        return sh.worksheet(nombre_hoja)

    return sh.sheet1

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=60)
def cargar_df(nombre_archivo, hoja=None):

    try:

        sheet = abrir_hoja(nombre_archivo, hoja)

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        if not df.empty:

            df.columns = [
                str(c).strip().upper()
                for c in df.columns
            ]

        return df.astype(str)

    except:

        return pd.DataFrame()

# =========================================================
# UPDATE FUNCTIONS
# =========================================================

def update_consolidado_arribo(doc, fecha):

    try:

        sheet = abrir_hoja(
            "Consolidado - Carcasas"
        )

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

        indices = df[
            df["DOC"].astype(str) == str(doc)
        ].index

        col_status = (
            df.columns.get_loc("STATUS") + 1
        )

        col_fecha = (
            df.columns.get_loc("FCH LLEGADA") + 1
        )

        for idx in indices:

            sheet.update_cell(
                idx + 2,
                col_status,
                "ARRIBADO"
            )

            sheet.update_cell(
                idx + 2,
                col_fecha,
                str(fecha)
            )

        return True

    except Exception as e:

        st.error(e)

        return False

# =========================================================
# UPDATE ASN
# =========================================================

def update_recepcion_almacenado(asn, fecha):

    try:

        sheet = abrir_hoja(
            "RECEPCION_IMPORTACIONES",
            "MOVIMIENTOS"
        )

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

        indices = df[
            df["ASN"].astype(str) == str(asn)
        ].index

        col_status = (
            df.columns.get_loc("STATUS_REC") + 1
        )

        col_fecha = (
            df.columns.get_loc("FCH_ALMACENADO") + 1
        )

        for idx in indices:

            sheet.update_cell(
                idx + 2,
                col_status,
                "ALMACENADO"
            )

            sheet.update_cell(
                idx + 2,
                col_fecha,
                str(fecha)
            )

        return True

    except Exception as e:

        st.error(e)

        return False

# =========================================================
# LOAD TABLES
# =========================================================

with st.spinner("Sincronizando con Google Sheets..."):

    df_import = cargar_df(
        "Consolidado - Carcasas"
    )

    df_recepcion = cargar_df(
        "RECEPCION_IMPORTACIONES",
        "MOVIMIENTOS"
    )

    df_tiendas = cargar_df(
        "TIENDAS CARCASAS"
    )

# =========================================================
# SIDEBAR
# =========================================================

menu = st.sidebar.radio(
    "MENÚ PRINCIPAL",
    [
        "📦 Importaciones",
        "🚚 Distribución"
    ]
)

# =========================================================
# IMPORTACIONES
# =========================================================

if menu == "📦 Importaciones":

    st.title("📦 Gestión de Importaciones")

    tab_dash, tab_recep, tab_ops = st.tabs([
        "📊 Dashboard",
        "📑 Recepción",
        "⚙️ Operaciones"
    ])

    # =====================================================
    # DASHBOARD
    # =====================================================

    with tab_dash:

        st.subheader(
            "🏪 Próximas Aperturas"
        )

        if not df_tiendas.empty:

            try:

                df_ap = df_tiendas[
                    df_tiendas["ESTADO"]
                    .str.upper()
                    .str.contains(
                        "PENDIENTE",
                        na=False
                    )
                ].copy()

                df_ap["FCH_DT"] = pd.to_datetime(
                    df_ap["FCH ESTIMADA"],
                    dayfirst=True,
                    errors="coerce"
                )

                hoy = datetime.now()

                limite = hoy + timedelta(days=60)

                df_filtrado = df_ap[
                    (df_ap["FCH_DT"] >= hoy)
                    &
                    (df_ap["FCH_DT"] <= limite)
                ].sort_values("FCH_DT")

                if not df_filtrado.empty:

                    cols = st.columns(4)

                    for i, (_, row) in enumerate(
                        df_filtrado.iterrows()
                    ):

                        with cols[i % 4]:

                            st.markdown(f"""
                            <div class="apertura-card">

                                <div class="tienda-titulo">
                                    🏪 {row['TIENDA']}
                                </div>

                                <div style="color:#636e72;font-size:0.85em;margin-top:8px;">
                                    {row['DESCRIPCION']}
                                </div>

                                <div class="fecha-est" style="margin-top:15px;">
                                    📅 {row['FCH ESTIMADA']}
                                </div>

                            </div>
                            """, unsafe_allow_html=True)

                else:

                    st.info(
                        "No hay aperturas próximas."
                    )

            except Exception as e:

                st.error(e)

        # =================================================
        # STATUS IMPORTACIONES
        # =================================================

        st.markdown(
            '<div class="titulo-seccion">STATUS IMPORTACIONES</div>',
            unsafe_allow_html=True
        )

        if not df_import.empty:

            m1, m2, m3 = st.columns(3)

            total_docs = (
                df_import["DOC"].nunique()
            )

            arribados = df_import[
                df_import["STATUS"]
                .str.upper()
                .str.contains(
                    "ARRIBADO",
                    na=False
                )
            ]["DOC"].nunique()

            m1.metric(
                "Total Importaciones",
                total_docs
            )

            m2.metric(
                "Arribados",
                arribados
            )

            m3.metric(
                "En tránsito",
                total_docs - arribados
            )

            st.divider()

            c1, c2 = st.columns(2)

            # =============================================
            # PENDIENTES
            # =============================================

            with c1:

                st.markdown(
                    "### ⏳ Pendientes"
                )

                df_p = df_import[
                    ~df_import["STATUS"]
                    .str.upper()
                    .str.contains(
                        "ARRIBADO",
                        na=False
                    )
                ]

                if not df_p.empty:

                    resumen_p = (
                        df_p
                        .groupby("DOC")
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    )

                    st.dataframe(
                        resumen_p,
                        width="stretch",
                        hide_index=True
                    )

            # =============================================
            # ARRIBADOS
            # =============================================

            with c2:

                st.markdown(
                    "### ✅ Arribados"
                )

                df_a = df_import[
                    df_import["STATUS"]
                    .str.upper()
                    .str.contains(
                        "ARRIBADO",
                        na=False
                    )
                ]

                if not df_a.empty:

                    resumen_a = (
                        df_a
                        .groupby(
                            ["DOC", "ETA"]
                        )
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    )

                    st.dataframe(
                        resumen_a,
                        width="stretch",
                        hide_index=True
                    )

    # =====================================================
    # RECEPCION
    # =====================================================

    with tab_recep:

        st.markdown(
            "### 🗺️ Flujo Recepción"
        )

        col_p, col_a, col_t = st.columns(3)

        # =================================================
        # PENDIENTE
        # =================================================

        with col_p:

            st.markdown("""
            <div style="
                background-color:#f8f9fa;
                padding:15px;
                border-radius:10px;
                border-left:5px solid #ff4b4b;
            ">
            <h4>🚨 RECEPCIONADO</h4>
            <small>Pendiente</small>
            </div>
            """, unsafe_allow_html=True)

            df_p = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "PENDIENTE"
            ]

            if not df_p.empty:

                resumen = (
                    df_p
                    .groupby(
                        [
                            "IMPORTACION",
                            "DESTINO"
                        ]
                    )
                    .size()
                    .reset_index(
                        name="ASNs"
                    )
                )

                st.dataframe(
                    resumen,
                    width="stretch",
                    hide_index=True
                )

        # =================================================
        # ALMACENADO
        # =================================================

        with col_a:

            st.markdown("""
            <div style="
                background-color:#f0fff4;
                padding:15px;
                border-radius:10px;
                border-left:5px solid #28a745;
            ">
            <h4>🏢 ALMACENADO</h4>
            <small>En stock</small>
            </div>
            """, unsafe_allow_html=True)

            df_alm = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "ALMACENADO"
            ]

            if not df_alm.empty:

                resumen = (
                    df_alm
                    .groupby(
                        [
                            "IMPORTACION",
                            "DESTINO"
                        ]
                    )
                    .size()
                    .reset_index(
                        name="ASNs"
                    )
                )

                st.dataframe(
                    resumen,
                    width="stretch",
                    hide_index=True
                )

        # =================================================
        # PROGRAMADO
        # =================================================

        with col_t:

            st.markdown("""
            <div style="
                background-color:#fffaf0;
                padding:15px;
                border-radius:10px;
                border-left:5px solid #ffa500;
            ">
            <h4>🚚 PROGRAMADO</h4>
            <small>Despachos</small>
            </div>
            """, unsafe_allow_html=True)

            df_prog = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "PROGRAMADO"
            ]

            if not df_prog.empty:

                resumen = (
                    df_prog
                    .groupby(
                        [
                            "IMPORTACION",
                            "ID_DESPACHO"
                        ]
                    )
                    .size()
                    .reset_index(
                        name="ASNs"
                    )
                )

                st.dataframe(
                    resumen,
                    width="stretch",
                    hide_index=True
                )

    # =====================================================
    # OPERACIONES
    # =====================================================

    with tab_ops:

        st.header(
            "⚙️ Operaciones"
        )

        c1, c2 = st.columns(2)

        # =================================================
        # ARRIBO
        # =================================================

        with c1:

            st.subheader(
                "Confirmar Arribo"
            )

            df_ops = df_import[
                ~df_import["STATUS"]
                .str.upper()
                .str.contains(
                    "ARRIBADO",
                    na=False
                )
            ]

            docs = (
                df_ops["DOC"]
                .unique()
                .tolist()
            )

            if docs:

                with st.form(
                    "form_arribo"
                ):

                    doc_sel = st.selectbox(
                        "DOC",
                        docs
                    )

                    fecha = st.date_input(
                        "Fecha Arribo",
                        date.today()
                    )

                    enviar = st.form_submit_button(
                        "Guardar"
                    )

                    if enviar:

                        ok = update_consolidado_arribo(
                            doc_sel,
                            fecha
                        )

                        if ok:

                            st.success(
                                "Actualizado"
                            )

                            st.cache_data.clear()

                            st.rerun()

            else:

                st.info(
                    "Sin documentos pendientes"
                )

        # =================================================
        # ALMACENADO
        # =================================================

        with c2:

            st.subheader(
                "Confirmar Almacenaje"
            )

            df_ops = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                .str.contains(
                    "PENDIENTE",
                    na=False
                )
            ]

            asns = (
                df_ops["ASN"]
                .unique()
                .tolist()
            )

            if asns:

                with st.form(
                    "form_almacen"
                ):

                    asn_sel = st.selectbox(
                        "ASN",
                        asns
                    )

                    fecha = st.date_input(
                        "Fecha",
                        date.today()
                    )

                    enviar = st.form_submit_button(
                        "Guardar"
                    )

                    if enviar:

                        ok = update_recepcion_almacenado(
                            asn_sel,
                            fecha
                        )

                        if ok:

                            st.success(
                                "ASN almacenado"
                            )

                            st.cache_data.clear()

                            st.rerun()

            else:

                st.info(
                    "Sin ASN pendientes"
                )

# =========================================================
# DISTRIBUCION
# =========================================================

elif menu == "🚚 Distribución":

    st.title("🚚 Distribución")

    st.info(
        "Módulo en construcción"
    )

# =========================================================
# SIDEBAR SYNC
# =========================================================

if st.sidebar.button(
    "🔄 Sincronizar"
):

    st.cache_data.clear()

    st.rerun()
