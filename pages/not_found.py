# pages/not_found.py

from dash import html

def layout():
    return html.Div([
        html.H2("❌ Página não encontrada"),
        html.P("Verifique a URL digitada."),
    ], style={"color": "red", "padding": "40px"})
