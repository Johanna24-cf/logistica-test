import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Sistema Logístico",
    layout="wide"
)

# =====================================================
# GOOGLE SHEETS CONNECTION
# =====================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:

    creds_dict = dict(st.secrets["gcp_service_account"])

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )

except:

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credenciales.json",
        scope
    )

client = gspread.authorize(creds)

# =====================================================
# SHEETS
# =====================================================

sheet_importaciones = client.open(
    "IMPORTACIONES"
).sheet1

sheet_recepcion = client.open(
    "RECEPCION_IMPORTACIONES"
).sheet1

sheet_distribucion = client.open(
    "DISTRIBUCION"
).sheet1

sheet_despacho_asn = client.open(
    "DESPACHO_ASN"
).sheet1

# =====================================================
# HELPERS
# =====================================================

def cargar_df(sheet):

    data = sheet.get_all_records()

    if len(data) == 0:
        return pd.DataFrame()

    return pd.DataFrame(data)

def limpiar_valor(x):

    if pd.isna(x):
        return ""

    if isinstance(x, pd.Timestamp):
        return x.strftime("%d/%m/%Y")

    return str(x)

def generar_id_despacho(df, cuenta):

    fecha_hoy = datetime.now().strftime("%Y%m%d")

    cuenta_cod = (
        str(cuenta)
        .replace(" ", "")
        [:3]
        .upper()
    )

    prefijo = f"{fecha_hoy}-{cuenta_cod}"

    if df.empty:
        correlativo = 1

    else:

        ids = df["ID_DESPACHO"].astype(str)

        ids_hoy = ids[
            ids.str.startswith(prefijo)
        ]

        if len(ids_hoy) == 0:
            correlativo = 1

        else:

            nums = []

            for x in ids_hoy:

                try:
                    nums.append(
                        int(x.split("-")[-1])
                    )
                except:
                    pass

            correlativo = max(nums) + 1

    return f"{prefijo}-{str(correlativo).zfill(3)}"

# =====================================================
# LOAD DATA
# =====================================================

df_import = cargar_df(sheet_importaciones)
df_recep = cargar_df(sheet_recepcion)
df_dist = cargar_df(sheet_distribucion)
df_despacho = cargar_df(sheet_despacho_asn)

# =====================================================
# MENU
# =====================================================

menu = st.sidebar.radio(
    "MÓDULOS",
    [
        "IMPORTACIONES",
        "DISTRIBUCIÓN",
        "APERTURA"
    ]
)

# =====================================================
# IMPORTACIONES
# =====================================================

if menu == "IMPORTACIONES":

    st.title("📦 IMPORTACIONES")

    st.subheader("Actualizar fecha llegada")

    importaciones = sorted(
        df_import["IMPORTACION"]
        .astype(str)
        .unique()
    )

    imp_sel = st.selectbox(
        "Importación",
        importaciones,
        key="imp_sel"
    )

    fecha_llegada = st.date_input(
        "Fecha llegada",
        key="fecha_llegada"
    )

    if st.button(
        "Guardar fecha llegada",
        key="btn_fecha"
    ):

        mask = (
            df_import["IMPORTACION"]
            .astype(str)
            == str(imp_sel)
        )

        df_import.loc[
            mask,
            "FECHA_LLEGADA"
        ] = fecha_llegada.strftime(
            "%d/%m/%Y"
        )

        sheet_importaciones.clear()

        sheet_importaciones.update(
            [
                df_import.columns.values.tolist()
            ] +
            df_import.values.tolist()
        )

        st.success("Actualizado")

    st.divider()

    st.subheader("Recepciones")

    recibidas = df_import[
        df_import["FECHA_LLEGADA"]
        .astype(str)
        != ""
    ]

    if not recibidas.empty:

        resumen = (
            recibidas
            .groupby(
                [
                    "IMPORTACION",
                    "CLIENTE",
                    "FECHA_LLEGADA"
                ]
            )
            .agg(
                TOTAL_ASN=("ASN", "count"),
                TOTAL_UNIDADES=("CANTIDAD", "sum")
            )
            .reset_index()
        )

        st.dataframe(
            resumen,
            width="stretch"
        )

        imp_view = st.selectbox(
            "Ver detalle",
            resumen["IMPORTACION"],
            key="ver_detalle"
        )

        detalle = recibidas[
            recibidas["IMPORTACION"]
            == imp_view
        ]

        cards = (
            detalle
            .groupby("DESTINO")
            .agg(
                ASN=("ASN", "count"),
                UNIDADES=("CANTIDAD", "sum")
            )
            .reset_index()
        )

        st.dataframe(
            cards,
            width="stretch"
        )

# =====================================================
# DISTRIBUCION
# =====================================================

elif menu == "DISTRIBUCIÓN":

    st.title("🚚 DISTRIBUCIÓN")

    tabs = st.tabs(
        [
            "Carga Masiva",
            "Carga Manual",
            "Despachos"
        ]
    )

    # =================================================
    # CARGA MASIVA
    # =================================================

    with tabs[0]:

        archivo = st.file_uploader(
            "Subir Excel",
            type=["xlsx"],
            key="upload"
        )

        if archivo:

            df_excel = pd.read_excel(
                archivo
            )

            st.dataframe(
                df_excel.head(),
                width="stretch"
            )

            if st.button(
                "Guardar carga masiva",
                key="guardar_masiva"
            ):

                for _, row in df_excel.iterrows():

                    cuenta = limpiar_valor(
                        row.get("CUENTA", "")
                    )

                    id_despacho = generar_id_despacho(
                        df_dist,
                        cuenta
                    )

                    fila = [

                        id_despacho,

                        limpiar_valor(
                            row.get(
                                "FECHA ENTREGA",
                                ""
                            )
                        ),

                        cuenta,

                        limpiar_valor(
                            row.get(
                                "CLIENTE",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "HORA DE CITA",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "PROCESO",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "ORIGEN",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "DESTINO",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "T  TRANSPORTE",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "CHOFER",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "DIRECCION",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "CONTACTO",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "TELEFONO",
                                ""
                            )
                        ),

                        limpiar_valor(
                            row.get(
                                "REFERENCIA",
                                ""
                            )
                        ),

                        ""
                    ]

                    sheet_distribucion.append_row(
                        fila
                    )

                st.success("Carga realizada")

    # =================================================
    # MANUAL
    # =================================================

    with tabs[1]:

        st.subheader("Carga manual")

        fecha = st.date_input(
            "Fecha entrega",
            key="manual_fecha"
        )

        cuenta = st.text_input(
            "Cuenta",
            key="manual_cuenta"
        )

        cliente = st.text_input(
            "Cliente",
            key="manual_cliente"
        )

        destino = st.text_input(
            "Destino",
            key="manual_destino"
        )

        if st.button(
            "Guardar despacho",
            key="guardar_manual"
        ):

            id_despacho = generar_id_despacho(
                df_dist,
                cuenta
            )

            fila = [

                id_despacho,
                fecha.strftime("%d/%m/%Y"),
                cuenta,
                cliente,
                "",
                "",
                "",
                destino,
                "",
                "",
                "",
                "",
                "",
                "",
                ""
            ]

            sheet_distribucion.append_row(
                fila
            )

            st.success("Guardado")

    # =================================================
    # DESPACHOS
    # =================================================

    with tabs[2]:

        st.subheader("Resumen despachos")

        if not df_dist.empty:

            resumen = (
                df_dist
                .groupby(
                    [
                        "ID_DESPACHO",
                        "FECHA ENTREGA",
                        "CUENTA"
                    ]
                )
                .agg(
                    CLIENTES=("CLIENTE", "count")
                )
                .reset_index()
            )

            st.dataframe(
                resumen,
                width="stretch"
            )

            despacho_sel = st.selectbox(
                "Despacho",
                resumen["ID_DESPACHO"],
                key="despacho_sel"
            )

            detalle = df_dist[
                df_dist["ID_DESPACHO"]
                == despacho_sel
            ]

            st.dataframe(
                detalle,
                width="stretch"
            )

            st.markdown("### ➕ Agregar ASN")

            pendientes = df_recep[
                (
                    df_recep["STATUS_REC"]
                    .astype(str)
                    .str.upper()
                    == "PENDIENTE"
                )
            ]

            if not pendientes.empty:

                tiendas = sorted(
                    pendientes["TIENDA"]
                    .astype(str)
                    .unique()
                )

                tienda_sel = st.selectbox(
                    "Tienda",
                    tiendas,
                    key="tienda_asn"
                )

                df_tienda = pendientes[
                    pendientes["TIENDA"]
                    == tienda_sel
                ]

                seleccionar_todo = st.checkbox(
                    "Seleccionar todos",
                    key="all_asn"
                )

                lista_asn = (
                    df_tienda["ASN"]
                    .astype(str)
                    .tolist()
                )

                asn_sel = st.multiselect(
                    "ASN",
                    lista_asn,
                    default=(
                        lista_asn
                        if seleccionar_todo
                        else []
                    ),
                    key="asn_multi"
                )

                if st.button(
                    "Agregar ASN",
                    key="guardar_asn"
                ):

                    for _, row in df_tienda.iterrows():

                        if (
                            str(row["ASN"])
                            in asn_sel
                        ):

                            fila = [

                                despacho_sel,
                                row["IMPORTACION"],
                                row["TIENDA"],
                                row["ASN"],
                                "EN RUTA",
                                datetime.now().strftime(
                                    "%d/%m/%Y"
                                ),
                                ""
                            ]

                            sheet_despacho_asn.append_row(
                                fila
                            )

                    st.success(
                        "ASN agregados"
                    )

# =====================================================
# APERTURA
# =====================================================

elif menu == "APERTURA":

    st.title("🏪 APERTURA")

    pendientes = df_recep[
        (
            df_recep["DESTINO"]
            .astype(str)
            .str.upper()
            == "APERTURA"
        )
        &
        (
            df_recep["STATUS_REC"]
            .astype(str)
            .str.upper()
            == "PENDIENTE"
        )
    ]

    if pendientes.empty:

        st.info("Sin ASN pendientes")

    else:

        tiendas = sorted(
            pendientes["TIENDA"]
            .astype(str)
            .unique()
        )

        tienda = st.selectbox(
            "Tienda",
            tiendas,
            key="ap_tienda"
        )

        df_tienda = pendientes[
            pendientes["TIENDA"]
            == tienda
        ]

        lista_asn = (
            df_tienda["ASN"]
            .astype(str)
            .tolist()
        )

        sel_all = st.checkbox(
            "Seleccionar todos ASN",
            key="all_ap"
        )

        asn = st.multiselect(
            "ASN",
            lista_asn,
            default=(
                lista_asn
                if sel_all
                else []
            ),
            key="ap_asn"
        )

        fecha_ap = st.date_input(
            "Fecha entrega",
            key="fecha_apertura"
        )

        destino = st.text_input(
            "Destino",
            key="dest_ap"
        )

        chofer = st.text_input(
            "Chofer",
            key="chofer_ap"
        )

        transporte = st.text_input(
            "Transporte",
            key="trans_ap"
        )

        if st.button(
            "Crear despacho apertura",
            key="crear_apertura"
        ):

            id_despacho = generar_id_despacho(
                df_dist,
                tienda
            )

            fila_dist = [

                id_despacho,
                fecha_ap.strftime("%d/%m/%Y"),
                "CASA DE LAS CARCASAS",
                tienda,
                "",
                "OUT",
                "PULMON",
                destino,
                transporte,
                chofer,
                "",
                "",
                "",
                "",
                len(asn)
            ]

            sheet_distribucion.append_row(
                fila_dist
            )

            for _, row in df_tienda.iterrows():

                if str(row["ASN"]) in asn:

                    fila_asn = [

                        id_despacho,
                        row["IMPORTACION"],
                        row["TIENDA"],
                        row["ASN"],
                        "EN RUTA",
                        fecha_ap.strftime(
                            "%d/%m/%Y"
                        ),
                        ""
                    ]

                    sheet_despacho_asn.append_row(
                        fila_asn
                    )

            st.success(
                "Despacho creado"
            )
