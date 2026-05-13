# =========================================================
# SISTEMA LOGÍSTICO CARCASAS - STREAMLIT CLOUD
# =========================================================

import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import (
    ServiceAccountCredentials
)

from datetime import (
    date,
    datetime,
    timedelta
)

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Sistema Logístico Carcasas",
    page_icon="📦",
    layout="wide"
)

# =========================================================
# ESTILOS
# =========================================================

st.markdown("""
<style>

.stDataFrame {
    font-size: 12px;
}

.apertura-card {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #6c5ce7;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 15px;
    min-height: 120px;
}

.fecha-est {
    color: #d63031;
    font-weight: bold;
    font-size: 0.9em;
}

.titulo-seccion {
    color: #2d3436;
    font-weight: bold;
    font-size: 1.6em;
    margin-top: 25px;
    margin-bottom: 15px;
    border-bottom: 3px solid #6c5ce7;
    padding-bottom: 8px;
}

.tienda-titulo {
    color: #2d3436;
    font-size: 1.1em;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# GOOGLE SHEETS
# =========================================================

@st.cache_resource
def conectar_google_sheets():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = dict(
        st.secrets["gcp_service_account"]
    )

    creds = (
        ServiceAccountCredentials
        .from_json_keyfile_dict(
            creds_dict,
            scope
        )
    )

    return gspread.authorize(creds)

client = conectar_google_sheets()

# =========================================================
# ABRIR HOJAS
# =========================================================

def abrir_hoja(
    nombre_archivo,
    nombre_pestaña=None
):

    try:

        sh = client.open(
            nombre_archivo
        )

        return (
            sh.worksheet(nombre_pestaña)
            if nombre_pestaña
            else sh.sheet1
        )

    except Exception as e:

        st.error(
            f"Error hoja {nombre_archivo}: {e}"
        )

        return None

# =========================================================
# CARGA DATA
# =========================================================

@st.cache_data(ttl=60)
def cargar_df(
    nombre_archivo,
    pestaña=None
):

    sheet = abrir_hoja(
        nombre_archivo,
        pestaña
    )

    if sheet is None:
        return pd.DataFrame()

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if not df.empty:

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

    return df.astype(str)

# =========================================================
# UPDATE ARRIBO
# =========================================================

def update_consolidado_arribo(
    doc_id,
    fecha
):

    try:

        sheet = abrir_hoja(
            "Consolidado - Carcasas"
        )

        df = pd.DataFrame(
            sheet.get_all_records()
        )

        df.columns = [
            str(c).strip().upper()
            for c in df.columns
        ]

        indices = df[
            df["DOC"].astype(str)
            == str(doc_id)
        ].index

        col_status = (
            df.columns.get_loc("STATUS")
            + 1
        )

        col_fecha = (
            df.columns.get_loc("FCH LLEGADA")
            + 1
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

    except:
        return False

# =========================================================
# UPDATE ALMACENADO
# =========================================================

def update_recepcion_almacenado(
    asn_id,
    fecha
):

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
            df["ASN"].astype(str)
            == str(asn_id)
        ].index

        col_status = (
            df.columns.get_loc("STATUS_REC")
            + 1
        )

        col_fecha = (
            df.columns.get_loc("FCH_ALMACENADO")
            + 1
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

    except:
        return False

# =========================================================
# LOAD DATA
# =========================================================

with st.spinner(
    "Sincronizando con Google Drive..."
):

    df_import = cargar_df(
        "Consolidado - Carcasas"
    )

    df_recepcion = cargar_df(
        "RECEPCION_IMPORTACIONES",
        "MOVIMIENTOS"
    )

    df_tiendas_raw = cargar_df(
        "TIENDAS CARCASAS"
    )

# =========================================================
# MENU
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

    st.title(
        "📦 Gestión de Importaciones"
    )

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

        if not df_tiendas_raw.empty:

            try:

                df_ap = df_tiendas_raw[
                    df_tiendas_raw["ESTADO"]
                    .str.upper()
                    .str.contains(
                        "PENDIENTE",
                        na=False
                    )
                ].copy()

                df_ap["FCH_DT"] = (
                    pd.to_datetime(
                        df_ap["FCH ESTIMADA"],
                        dayfirst=True,
                        errors="coerce"
                    )
                )

                hoy = datetime.now()

                limite = (
                    hoy
                    + timedelta(days=60)
                )

                df_filtrado = df_ap[
                    (
                        df_ap["FCH_DT"]
                        >= hoy
                    )
                    &
                    (
                        df_ap["FCH_DT"]
                        <= limite
                    )
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
                                    {row['TIENDA']}
                                </div>

                                <div style="color:#636e72;font-size:0.85em;">
                                    {row['DESCRIPCION']}
                                </div>

                                <br>

                                <div class="fecha-est">
                                    📅 {row['FCH ESTIMADA']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                else:

                    st.info(
                        "Sin aperturas próximas."
                    )

            except Exception as e:

                st.error(e)

        st.markdown(
            '<div class="titulo-seccion">STATUS IMPORTACIONES</div>',
            unsafe_allow_html=True
        )

        if not df_import.empty:

            m1, m2, m3 = st.columns(3)

            total_docs = (
                df_import["DOC"]
                .nunique()
            )

            arribados = (
                df_import[
                    df_import["STATUS"]
                    .str.upper()
                    .str.contains(
                        "ARRIBADO",
                        na=False
                    )
                ]["DOC"]
                .nunique()
            )

            m1.metric(
                "Total",
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

                st.dataframe(
                    (
                        df_p.groupby("DOC")
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    ),
                    width="stretch",
                    hide_index=True
                )

            with c2:

                st.markdown(
                    "### ✅ Confirmados"
                )

                df_a = df_import[
                    df_import["STATUS"]
                    .str.upper()
                    .str.contains(
                        "ARRIBADO",
                        na=False
                    )
                ]

                st.dataframe(
                    (
                        df_a.groupby(
                            ["DOC", "ETA"]
                        )
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    ),
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

        with col_p:

            st.markdown(
                "#### 🚨 Pendientes"
            )

            df_p = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "PENDIENTE"
            ]

            if not df_p.empty:

                st.dataframe(
                    (
                        df_p.groupby(
                            [
                                "IMPORTACION",
                                "DESTINO"
                            ]
                        )
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    ),
                    width="stretch",
                    hide_index=True
                )

        with col_a:

            st.markdown(
                "#### 🏢 Almacenado"
            )

            df_alm = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "ALMACENADO"
            ]

            if not df_alm.empty:

                st.dataframe(
                    (
                        df_alm.groupby(
                            [
                                "IMPORTACION",
                                "DESTINO"
                            ]
                        )
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    ),
                    width="stretch",
                    hide_index=True
                )

        with col_t:

            st.markdown(
                "#### 🚚 Programado"
            )

            df_prog = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                == "PROGRAMADO"
            ]

            if not df_prog.empty:

                st.dataframe(
                    (
                        df_prog.groupby(
                            [
                                "IMPORTACION",
                                "ID_DESPACHO"
                            ]
                        )
                        .size()
                        .reset_index(
                            name="ASNs"
                        )
                    ),
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

        c_left, c_right = st.columns(2)

        # ARRIBO

        with c_left:

            st.subheader(
                "Confirmar Arribo"
            )

            df_ops_pend = df_import[
                ~df_import["STATUS"]
                .str.upper()
                .str.contains(
                    "ARRIBADO",
                    na=False
                )
            ]

            docs_list = (
                df_ops_pend["DOC"]
                .unique()
                .tolist()
            )

            if docs_list:

                with st.form(
                    "form_arribo"
                ):

                    doc_sel = st.selectbox(
                        "DOC",
                        docs_list
                    )

                    f_arr = st.date_input(
                        "Fecha",
                        date.today(),
                        key="f_arr"
                    )

                    if st.form_submit_button(
                        "Actualizar"
                    ):

                        if update_consolidado_arribo(
                            doc_sel,
                            f_arr
                        ):

                            st.success(
                                "Actualizado"
                            )

                            st.cache_data.clear()

                            st.rerun()

        # ALMACENADO

        with c_right:

            st.subheader(
                "Confirmar Almacenado"
            )

            df_ops_alm = df_recepcion[
                df_recepcion["STATUS_REC"]
                .str.upper()
                .str.contains(
                    "PENDIENTE",
                    na=False
                )
            ]

            asns_list = (
                df_ops_alm["ASN"]
                .unique()
                .tolist()
            )

            if asns_list:

                with st.form(
                    "form_almacen"
                ):

                    asn_sel = st.selectbox(
                        "ASN",
                        asns_list
                    )

                    f_alm = st.date_input(
                        "Fecha",
                        date.today(),
                        key="f_alm"
                    )

                    if st.form_submit_button(
                        "Actualizar"
                    ):

                        if update_recepcion_almacenado(
                            asn_sel,
                            f_alm
                        ):

                            st.success(
                                "Actualizado"
                            )

                            st.cache_data.clear()

                            st.rerun()

# =========================================================
# DISTRIBUCION
# =========================================================

elif menu == "🚚 Distribución":

    st.title(
        "🚚 Distribución"
    )

    st.info(
        "Módulo en construcción."
    )

# =========================================================
# SIDEBAR
# =========================================================

if st.sidebar.button(
    "🔄 Sincronizar"
):

    st.cache_data.clear()

    st.rerun()
