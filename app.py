# =========================================================
# APERTURAS
# =========================================================

st.subheader("🏪 Próximas Aperturas")

if not df_tiendas_raw.empty:

    try:

        df_ap = df_tiendas_raw[
            df_tiendas_raw["ESTADO"]
            .str.upper()
            .str.contains("PENDIENTE", na=False)
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

            for i, (_, row) in enumerate(df_filtrado.iterrows()):

                with cols[i % 4]:

                    st.markdown(
                        f"""
                        <div class="apertura-card">

                            <div class="tienda-titulo">
                                🏪 {row['TIENDA']}
                            </div>

                            <div style="
                                color:#636e72;
                                font-size:0.85em;
                                margin-top:8px;
                            ">
                                {row['DESCRIPCION']}
                            </div>

                            <div class="fecha-est" style="
                                margin-top:15px;
                            ">
                                📅 {row['FCH ESTIMADA']}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        else:

            st.info(
                "No hay aperturas programadas"
            )

    except Exception as e:

        st.error(
            f"Error: {e}"
        )
