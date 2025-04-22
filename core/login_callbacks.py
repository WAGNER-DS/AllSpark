#core/login_callbacks.py
from dash import Input, Output, State, ctx, no_update
from core.auth import check_credentials, get_apps_por_perfil
from core.session import user_session

def registrar_login_callbacks(app):

    # 🔐 LOGIN
    @app.callback(
        Output("url", "pathname"),
        Output("login-message", "children"),
        Output("login-store", "data"),
        Input("login-button", "n_clicks"),
        State("username", "value"),
        State("password", "value"),
        prevent_initial_call=True
    )
    def handle_login(n_clicks, username, password):
        user_data = check_credentials(username, password)
        if user_data:
            apps = get_apps_por_perfil(user_data["perfil_id"])

            # Salva sessão no servidor
            user_session["user"] = user_data["username"]
            user_session["perfil_id"] = user_data["perfil_id"]
            user_session["apps_permitidos"] = apps

            # Prepara sessão para o navegador
            session_data = {
                "user": user_data["username"],
                "perfil_id": user_data["perfil_id"],
                "apps_permitidos": apps
            }

            # Redirecionamento com base no perfil
            perfil = user_data["perfil_nome"].lower()
            if perfil == "admin" or not apps:
                return "/hub", "", session_data
            else:
                return apps[0]["rota"], "", session_data

        # ❌ Login falhou
        return no_update, "❌ Usuário ou senha inválidos", no_update

    # 🔓 LOGOUT padrão (apenas botão da tela de login)
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Output("login-store", "data", allow_duplicate=True),
        Input("logout-button", "n_clicks"),
        prevent_initial_call=True
    )
    def handle_logout(_):
        print("🚪 Logout solicitado via botão padrão")
        user_session["user"] = None
        user_session["perfil_id"] = None
        user_session["apps_permitidos"] = []
        return "/login", {}
