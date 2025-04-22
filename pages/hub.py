# pages/hub.py
from dash import html, dcc
from core.session import user_session

def layout(session_data=None):
    user = session_data.get("user") if session_data else user_session.get("user")

    if not user:
        return html.Div("⏳ Aguardando sessão...", style={"color": "white", "padding": "40px"})

    botoes = [
        ("Postes", "/app_postes"),
        ("Projeto", "/app_projeto"),
        ("Radar_CTO", "/app_radar_cto"),
        ("OTDR_View", "/app_otdr_view"),
        ("OSP_Diagnostics", "/app_OSP_diagnostics"),
        ("Alívio_Flash", "/app_alivio"),
        ("Preventiva", "/app_preventiva"),
        ("B2B", "/app_B2B"),
    ]

    return html.Div([
        html.Div("ALLSPARK HUB", className="hub-title"),
        html.Div([
            # Linhas SVG
            html.Div([
                dcc.Markdown("""
                    <svg class="hub-lines" width="600" height="600">
                        <line x1="300" y1="300" x2="300" y2="0" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="460" y2="110" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="580" y2="300" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="460" y2="490" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="300" y2="600" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="140" y2="490" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="20" y2="300" stroke="#00faff" stroke-width="2" class="hub-line"/>
                        <line x1="300" y1="300" x2="140" y2="110" stroke="#00faff" stroke-width="2" class="hub-line"/>
                    </svg>
                """, dangerously_allow_html=True)
            ], className="svg-container"),

            # Cubo central
            html.Img(src="/assets/allspark_cube.png", className="center-cube-img"),

            # Botões com imagem clicável e legenda
            *[
                html.Div([
                    html.A(
                        html.Img(src="/assets/allspark_botao.png", className="orb-glow-btn"),
                        href=rota
                    ),
                    html.Div(nome, className="orb-label")
                ], className=f"orb orb-{i+1}")
                for i, (nome, rota) in enumerate(botoes)
            ]
        ], className="hub-orbit")
    ], className="hub-container")
