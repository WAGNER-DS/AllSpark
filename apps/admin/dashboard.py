#apps/admin/dashboard.py
from dash import html, dcc, Input, Output, State, ctx
from dash import register_page

#register_page(__name__, path="/admin_dashboard")

def layout(session_data=None):
    # Protege acesso
    if not session_data or session_data.get("perfil_id") != 1:
        return html.Div("🔒 Acesso restrito a administradores.", style={"color": "red", "padding": "40px"})

    menu = html.Div([
        html.H4("⚙️ Admin"),
        html.Hr(),
        dcc.Link("👤 Usuários", href="/admin_dashboard?view=usuarios"),
        dcc.Link("🧩 Perfis", href="/admin_dashboard?view=perfis"),
        dcc.Link("📦 Apps", href="/admin_dashboard?view=apps"),
        dcc.Link("🔑 Permissões", href="/admin_dashboard?view=permissoes"),
        dcc.Link("📜 Logs", href="/app_otdr_logs")
    ], className="admin-sidebar")


    conteudo = html.Div(id="admin-content", style={"marginLeft": "240px", "padding": "20px"})

    return html.Div([menu, conteudo])
