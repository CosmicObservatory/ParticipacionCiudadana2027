"""Tablero Streamlit: análisis electoral y poblacional de Sonora.

Réplica del tablero Dash (vothmo/dashboard/app.py) sobre los mismos datos tidy.
La ruta ``/`` muestra la portada-historia; la herramienta con las pestañas
vive en ``/herramienta`` (navegación de páginas oculta).

Ejecutar desde la raíz del repo:

    uv run streamlit run vothmo/dashboard/streamlit_app.py
"""

import pandas as pd
import streamlit as st

from vothmo.dashboard import data, figures
from vothmo.dashboard.narrativa import (
    conclusiones_md,
    diccionario_md,
    escenarios_md,
    fuentes_md,
    glosario_md,
)

st.set_page_config(page_title="Votación Sonora", layout="wide")


def historia() -> None:
    """Portada-historia (página predeterminada, ``/``)."""
    st.title("Participación Ciudadana 2027")
    st.markdown(
        "Las elecciones están próximas y conviene conocer la población de "
        "interés para el diseño de la campaña. Aquí exploraremos el "
        "comportamiento de la participación ciudadana de años pasados para "
        "obtener estimaciones para las próximas elecciones. Antes de todo "
        "debemos elegir qué parte de Sonora nos interesa conocer."
    )

    # () = todo el estado; las figuras de la historia leen la selección.
    opciones_mun = {
        0: "Sonora",
        **data.municipios().set_index("mpiocve")["nom_mun"].to_dict(),
    }
    st.multiselect(
        "Zona de Interés",
        list(opciones_mun),
        default=[0],
        format_func=opciones_mun.get,
        key="hs_mun",
    )
    cvess = data.zona_cvess(st.session_state["hs_mun"])

    st.header("Los votantes antes")
    elec_z = data.elec_zona(cvess)
    st.subheader("Distribución")
    st.plotly_chart(
        figures.fig_votantes_zona(elec_z, data.nombre_zona(cvess)),
        width="stretch",
    )

    anio_dist = st.selectbox(
        "Año", data.anios_elec(), index=len(data.anios_elec()) - 1, key="hs_anio_dist"
    )
    st.plotly_chart(
        figures.fig_piramide(
            data.piramide_zona(anio_dist, cvess),
            anio_dist,
            f"Lista nominal por edad y sexo · {data.nombre_zona(cvess)} · {anio_dist}",
        ),
        width="stretch",
    )

    st.subheader("Participación ciudadana")
    anio_int = st.selectbox(
        "Año de interés", data.anios_elec(), index=len(data.anios_elec()) - 1
    )
    estado_ref = data.resumen_anual() if cvess else None
    col_mapa, col_pc = st.columns([3, 2])
    col_mapa.plotly_chart(
        figures.fig_mapa_pc_mun(
            data.municipios_pc_geo(anio_int), anio_int, data.centro_zona(cvess)
        ),
        width="stretch",
    )
    col_pc.plotly_chart(
        figures.fig_pc_anual(elec_z, data.nombre_zona(cvess), estado_ref),
        width="stretch",
    )

    st.header("Los votantes ahora")
    col_mapa, col_dl = st.columns([3, 2])
    gmun_zona = data.municipios_borde()
    if cvess:
        gmun_zona = gmun_zona[gmun_zona["mpiocve"].isin(cvess)]
    col_mapa.plotly_chart(
        figures.fig_mapa_secciones(
            data.secciones_geo(2025, cvess),
            gmun_zona,
            figures.PALETA_DISTRITOS,
            2025,
            data.municipios_de_distrito(2025),
            data.centro_zona(cvess),
        ),
        width="stretch",
    )
    col_dl.plotly_chart(
        figures.fig_barras_ln_dl(
            data.pad_ln_dl(2025, cvess),
            figures.PALETA_DISTRITOS,
            2025,
            data.nombre_zona(cvess),
        ),
        width="stretch",
    )
    st.caption(
        "Los colores de cada distrito se pueden cambiar desde la pestaña "
        "«Distribución Seccional» de la herramienta interactiva."
    )

    st.header("¿Qué podemos esperar de los votantes?")
    g_esc, key_esc = data.escenarios_geo_zona(cvess, 2027, "padronal")
    st.plotly_chart(
        figures.fig_escenarios_zona(
            g_esc,
            data.escenarios_zona_total(cvess, "padronal"),
            key_esc,
            data.nombre_zona(cvess),
            2027,
            2027,
            "padronal",
            data.centro_zona(cvess),
        ),
        width="stretch",
    )

    st.markdown(fuentes_md())
    st.page_link(herramienta_pg, label="Abrir la herramienta interactiva →")


def herramienta() -> None:
    """Las pestañas de análisis; solo se renderizan bajo /herramienta."""
    st.title("Participación Ciudadana 2027 · Sonora")

    tab_intro, tab_demo, tab_dist, tab_padron, tab_crec, tab_concl, tab_glos = st.tabs(
        [
            "Primeros Pasos",
            "Demografía Electoral",
            "Distribución Seccional",
            "Padrón vs Población",
            "Crecimiento",
            "Conclusiones",
            "Glosario",
        ]
    )

    # ------------------------------------------------------------ Primeros Pasos
    with tab_intro:
        st.markdown(
            """
            Tablero interactivo sobre los votantes del estado de Sonora a partir de los
            datos tidy generados por el pipeline de libretas (`data/processed/`):
            conteos censales electorales del INE 2009–2024, cartografía electoral
            2019–2025, censos INEGI 2010/2020 y proyecciones CONAPO.

            **Distribución.** Sonora se divide en 21 distritos electorales locales
            (y 7 federales); cada distrito se divide en secciones electorales.

            **Pestañas**

            - *Demografía electoral*: pirámides, participación y mapas por distrito.
            - *Padrón vs población*: razón padrón/población 18+ por municipio.
            - *Crecimiento*: escenarios bajo/base/alto de población y padrón a 2040.

            **Fuentes:** INE (conteos censales y cartografía), INEGI (ITER/censo
            2010 y 2020), CONAPO (proyecciones municipales 1990–2040), IEE Sonora
            (resultados, pendiente).

            *Caveats: `pad` (padrón cartográfico) ≠ `ln` (lista nominal del conteo);
            la clave municipal del INE difiere de la de INEGI (`mun_ine_inegi.csv`).*
            """
        )
        st.markdown(escenarios_md())
        st.markdown(diccionario_md())

    # ------------------------------------------------------ Demografía Electoral
    with tab_demo:
        anio = st.selectbox("Elección", data.anios_elec(), index=len(data.anios_elec()) - 1)

        fila = data.resumen_anual().set_index("aelec").loc[anio]
        n_sec = data.conteos()[data.conteos()["aelec"] == anio]["seccion"].nunique()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lista nominal", f"{fila['ln']:,.0f}")
        c2.metric("Participación", f"{fila['pc']:.1f}%")
        c3.metric("Secciones", f"{n_sec:,}")
        c4.metric("Elección", str(anio))

        st.plotly_chart(figures.fig_ln_anual(data.resumen_anual()), width="stretch")
        st.plotly_chart(figures.fig_piramide(data.piramide(anio), anio), width="stretch")
        st.plotly_chart(
            figures.fig_participacion_edad(data.participacion_edad(anio), anio),
            width="stretch",
        )

        var_mapa = st.radio(
            "Variable del mapa",
            ["pc", "ln"],
            format_func={"pc": "Participación (%)", "ln": "Lista nominal"}.get,
            horizontal=True,
        )
        st.plotly_chart(
            figures.fig_mapa_distritos(data.distritos_geo(anio), var_mapa, anio),
            width="stretch",
        )

        st.plotly_chart(
            figures.fig_ranking_distritos(data.por_distrito(anio), var_mapa, anio),
            width="stretch",
        )
        st.plotly_chart(
            figures.fig_ranking(
                data.por_municipio(anio),
                x="mpionom",
                titulo=f"Municipios con mayor lista nominal · {anio}",
            ),
            width="stretch",
        )

    # --------------------------------------------------- Distribución Seccional
    with tab_dist:
        st.markdown(
            "Cartografía seccional por distrito local (2019–2025). Elige el color de "
            "cada distrito: el mapa y las gráficas de efecto usan la misma paleta. "
            "Los bordes oscuros son los límites municipales."
        )
        with st.expander("Colores por distrito", expanded=True):
            cols = st.columns(7)
            colores = {
                d: cols[i % 7].color_picker(f"D{d}", figures.PALETA_DISTRITOS[d], key=f"ds-{d}")
                for i, d in enumerate(figures.DISTRITOS)
            }

        anio_sec = st.select_slider("Año de cartografía", data.MAP_YEARS, value=2025)
        st.plotly_chart(
            figures.fig_mapa_secciones(
                data.secciones_geo(anio_sec),
                data.municipios_borde(),
                colores,
                anio_sec,
                data.municipios_de_distrito(anio_sec),
            ),
            width="stretch",
        )
        st.caption(
            "En el hover de cada sección, los municipios en *cursiva* están repartidos "
            "entre dos o más distritos; el resto están contenidos por completo en ese distrito."
        )

        st.markdown("**Movimiento de secciones entre distritos**")
        c_de, c_a = st.columns(2)
        de = c_de.selectbox("De", data.MAP_YEARS, index=0)
        a = c_a.selectbox("A", data.MAP_YEARS, index=len(data.MAP_YEARS) - 1)
        st.plotly_chart(
            figures.fig_sankey_distritos(data.transiciones_distrito(de, a), de, a, colores),
            width="stretch",
        )

        st.markdown(
            "**Cambio atribuible al reseccionamiento.** El gap entre las barras y la "
            "línea punteada (contrafactual geografía 2019) mide cuánto gana o pierde "
            "el distrito solo por reacomodo; las etiquetas anotan el cambio interanual."
        )
        c_dl, c_serie = st.columns([1, 3])
        distrito_sel = c_dl.selectbox(
            "Distrito", figures.DISTRITOS, index=5, format_func=lambda d: f"D{d}"
        )
        serie = c_serie.radio(
            "Serie",
            list(figures.SERIES_EFECTO),
            format_func=figures.SERIES_EFECTO.get,
            horizontal=True,
        )
        m = data.efecto_redistrito()
        st.plotly_chart(
            figures.fig_historia_distrito(m, distrito_sel, serie, colores[distrito_sel]),
            width="stretch",
        )
        st.plotly_chart(figures.fig_delta_barras(m, serie, colores), width="stretch")

        st.markdown("**Geografía distrital para los análisis**")
        st.selectbox(
            "Asignación sección → distrito para las pestañas siguientes",
            [None, *data.MAP_YEARS],
            format_func=lambda y: (
                "Distribución del año correspondiente (predeterminado)"
                if y is None
                else f"Fijar distribución {y}"
            ),
            key="geo_fija",
        )
        st.caption(
            "Afecta a Padrón vs Población y Crecimiento. Por defecto cada análisis "
            "usa la distribución de su propio año."
        )

    # ------------------------------------------------------ Padrón vs Población
    with tab_padron:
        geo_fija = st.session_state.get("geo_fija")
        if geo_fija:
            st.info(
                f"Geografía distrital fijada a {geo_fija}: los resultados por distrito "
                f"usan la asignación sección → distrito de {geo_fija} (cámbiala al "
                "final de Distribución Seccional)."
            )
        pad, ln = data.padron_anual()
        st.plotly_chart(
            figures.fig_padron_poblacion(pad, ln, data.conapo_estado(), data.inegi_estado()),
            width="stretch",
        )
        st.plotly_chart(figures.fig_razon_estado(data.razon_estado()), width="stretch")

        anio_map = st.selectbox(
            "Año de cartografía", data.MAP_YEARS, index=len(data.MAP_YEARS) - 1
        )
        st.plotly_chart(
            figures.fig_mapa_razon_mun(data.municipios_geo(anio_map), anio_map),
            width="stretch",
        )

        st.markdown("**Razón padrón / población 18+ por distrito local**")
        anio_dl = geo_fija or anio_map
        st.plotly_chart(
            figures.fig_mapa_razon_dl(data.distritos_razon(anio_dl), anio_dl),
            width="stretch",
        )

        rm = data.razon_mun(anio_map)
        cols = ["nom_mun", "pad", "pob18", "razon_18"]
        extremos = pd.concat([rm.nlargest(6, "razon_18"), rm.nsmallest(6, "razon_18")])[cols]
        st.markdown("**Municipios extremos** (mayor y menor razón padrón/18+)")
        st.dataframe(extremos.round({"pad": 0, "pob18": 0, "razon_18": 3}), hide_index=True)

    # ------------------------------------------------------------- Crecimiento
    with tab_crec:
        geo_fija = st.session_state.get("geo_fija")
        if geo_fija:
            st.info(
                f"Geografía distrital fijada a {geo_fija}: los resultados por distrito "
                f"usan la asignación sección → distrito de {geo_fija} (cámbiala al "
                "final de Distribución Seccional)."
            )
        st.markdown(
            "Escenarios bajo/base/alto a 2040: población por CAGR observado de CONAPO "
            "y padrón por driver padronal (CAGR del padrón 2019–2025) o demográfico "
            "(CAGR de población 18+ CONAPO)."
        )
        driver = st.radio("Driver del padrón", ["padronal", "demografico"], horizontal=True)

        # Factor de crecimiento por escenario (%, sobre el CAGR observado);
        # el radio posiciona los deslizadores en el valor del escenario elegido.
        for clave in ("f_pob", "f_pad"):
            if clave not in st.session_state:
                st.session_state[clave] = {"bajo": -25, "base": 0, "alto": 25}
        for clave in ("d_pob", "d_pad"):
            if clave not in st.session_state:
                st.session_state[clave] = 0

        def _sincroniza_sliders():
            esc_ = st.session_state.esc_sel
            st.session_state.d_pob = st.session_state.f_pob[esc_]
            st.session_state.d_pad = st.session_state.f_pad[esc_]

        escenario = st.radio(
            "Escenario (define qué curva muestran los deslizadores)",
            ["bajo", "base", "alto"],
            index=1,
            key="esc_sel",
            on_change=_sincroniza_sliders,
            horizontal=True,
        )
        c1, c2 = st.columns(2)
        d_pob = c1.slider("Ajuste poblacional del escenario", -50, 50, key="d_pob", format="%+d%%")
        d_pad = c2.slider("Ajuste padronal del escenario", -50, 50, key="d_pad", format="%+d%%")
        st.session_state.f_pob[escenario] = d_pob
        st.session_state.f_pad[escenario] = d_pad

        esc = data.escenarios_custom(
            tuple(1 + st.session_state.f_pob[k] / 100 for k in ("bajo", "base", "alto")),
            tuple(1 + st.session_state.f_pad[k] / 100 for k in ("bajo", "base", "alto")),
            geo_fija,
        )

        st.plotly_chart(
            figures.fig_escenarios_estado(esc["poblacion_est"], esc["padron_est"], driver),
            width="stretch",
        )
        st.plotly_chart(figures.fig_padron_dl(esc["padron_dl"], driver), width="stretch")
        st.plotly_chart(figures.fig_pob_dl(esc["poblacion_dl"], escenario), width="stretch")

        municipios = sorted(esc["poblacion_mun"]["nom_mun"].unique())
        default = [m for m in ["Hermosillo", "Cajeme", "Nogales"] if m in municipios]
        sel_mun = st.multiselect("Municipios", municipios, default=default)
        st.plotly_chart(
            figures.fig_mun_escenario(esc["poblacion_mun"], sel_mun or default),
            width="stretch",
        )

    # ------------------------------------------------------------- Conclusiones
    with tab_concl:
        st.markdown(conclusiones_md())

    # ----------------------------------------------------------------- Glosario
    with tab_glos:
        st.markdown(glosario_md())


historia_pg = st.Page(historia, title="Historia", default=True)
herramienta_pg = st.Page(herramienta, title="Herramienta", url_path="herramienta")
st.navigation([historia_pg, herramienta_pg], position="hidden").run()
