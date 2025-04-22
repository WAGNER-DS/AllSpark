# pages/hub.py
# pages/hub.py
from dash import html
from core.session import user_session

def layout(session_data=None):
    user = session_data.get("user") if session_data else user_session.get("user")

    if not user:
        return html.Div("⏳ Aguardando sessão...", style={"color": "white", "padding": "40px"})

    # Lista de apps com nomes e rotas
    botoes = [
        ("Postes", "/app_postes"),
        ("Projeto", "/app_projeto"),
        ("Radar_CTO", "/app_radar_cto"),
        ("OTDR View", "/app_otdr_view"),
        ("OSP_Diagnostics", "/app_OSP_diagnostics"),
        ("Alívio_Flash", "/app_alivio"),
        ("Preventiva", "/app_preventiva"),
        ("B2B", "/app_B2B"),
    ]

    return html.Div([
        html.Div("AllSpark Hub", className="hub-title"),

        html.Div([
            html.Div([
                html.Div(className="center-cube"),
                *[
                    html.Div(
                        html.Button(
                            nome,
                            id={"type": "app-button", "rota": rota},
                            className="hub-button",
                            n_clicks=0  # 👈 ESSENCIAL
                        ),
                        className=f"orb orb-{i+1}"
                    )
                    for i, (nome, rota) in enumerate(botoes)
                ]
            ], className="hub-orbit")
        ])
    ], className="hub-container")
