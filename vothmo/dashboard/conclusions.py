"""Pestaña de conclusiones del tablero Dash."""

from dash import dcc, html

from vothmo.dashboard.narrativa import conclusiones_md

layout = html.Div(children=[dcc.Markdown(conclusiones_md(), mathjax=True)])
