# pages/hub.py
from dash import html, dcc
from core.session import user_session

def layout(session_data=None):
    user = session_data.get("user") if session_data else user_session.get("user")
    perfil_id = session_data.get("perfil_id") if session_data else user_session.get("perfil_id")

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

    layout_principal = html.Div([
        html.Div("ALLSPARK HUB", className="hub-title"),
        html.Div([
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

            html.Img(src="/assets/allspark_cube.png", className="center-cube-img"),

            *[
                html.Div([
                    html.A(
                        html.Img(src="/assets/allspark_botao.png", className="orb-glow-btn"),
                        href=rota
                    ),
                    html.Div(nome, className="orb-label")
                ], className=f"orb orb-{i+1}")
                for i, (nome, rota) in enumerate(botoes)
            ],

            # ✅ Se for admin, adiciona engrenagem fixa no canto inferior direito
            html.Div([
                dcc.Link(
                    html.I(className="fas fa-cogs"),  # Ícone de engrenagem
                    href="/admin_dashboard",
                    style={
                        "fontSize": "36px",
                        "color": "#00ffaa",
                        "position": "fixed",
                        "bottom": "30px",
                        "right": "30px",
                        "zIndex": "9999",
                        "cursor": "pointer",
                        "backgroundColor": "#111",
                        "padding": "12px",
                        "borderRadius": "50%",
                        "boxShadow": "0 0 10px #00ffaa"
                    }
                )
            ]) if perfil_id == 1 else None
        ], className="hub-orbit")
    ], className="hub-container")

    return layout_principal
