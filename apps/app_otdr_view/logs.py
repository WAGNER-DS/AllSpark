# apps/app_otdr_view/logs.py
from dash import html, dcc, dash_table
import pandas as pd
import sqlite3

def layout(session_data=None):
    perfil_id = session_data.get("perfil_id") if session_data else None
    if perfil_id != 1:
        return html.Div("🔒 Acesso restrito a administradores.", style={"color": "red", "padding": "40px"})

    try:
        con = sqlite3.connect("logs/otdr_consultas.db")
        df = pd.read_sql("SELECT * FROM consultas_otdr ORDER BY timestamp DESC LIMIT 200", con)
        con.close()

        return html.Div([
            html.H3("📜 Logs de Consultas OTDR", style={"color": "#00ffaa", "marginBottom": "20px"}),

            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "backgroundColor": "#111",
                    "color": "white",
                    "fontSize": "18px",
                    "padding": "8px",
                    "minWidth": "100px",
                    "maxWidth": "250px",
                    "whiteSpace": "normal"
                },
                style_header={
                    "backgroundColor": "#222",
                    "fontWeight": "bold",
                    "color": "#00ffaa",
                    "border": "1px solid #444"
                },
                page_size=20,
                filter_action="native",
                sort_action="native",
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#1a1a1a"
                    }
                ]
            ),

            html.Br(),
            dcc.Link("⬅️ Voltar para OTDR View", href="/app_otdr_view", style={"color": "#00ffaa", "fontWeight": "bold"})
        ], style={"padding": "30px"})
    except Exception as e:
        return html.Div(f"Erro ao carregar logs: {e}", style={"color": "red", "padding": "40px"})
