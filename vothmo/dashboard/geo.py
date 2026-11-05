"""Geografía distrital fijada globalmente para las pestañas posteriores a
Distribución Seccional (estado compartido del tablero Dash)."""

from dash import html

from vothmo.dashboard import data

# Sentinel del dcc.Store / dropdown: 0 = "distribución del año correspondiente".
OPCIONES_GEO = [
    {"label": "Distribución del año correspondiente (predeterminado)", "value": 0},
    *[{"label": f"Fijar distribución {y}", "value": y} for y in data.MAP_YEARS],
]

_ESTILO_NOTA = {
    "background": "#fff3cd",
    "color": "#5a4500",
    "padding": "0.5rem 0.8rem",
    "borderRadius": "4px",
    "margin": "0.8rem 0",
}


def nota(geo: int | None) -> html.Div | str:
    """Banner visible cuando el usuario fijó una geografía distrital."""
    if not geo:
        return ""
    return html.Div(
        f"Geografía distrital fijada a {geo}: los resultados por distrito usan la "
        f"asignación sección → distrito de {geo} (cámbiala al final de "
        "Distribución Seccional).",
        style=_ESTILO_NOTA,
    )
