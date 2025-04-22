#core/login_callbacks.py
from dash import Input, Output, State, ctx, no_update
from core.auth import check_credentials, get_apps_por_perfil
from core.session import user_session

def registrar_login_callbacks(app):
    @app.callback(
        Output("url", "pathname"),
        Output("login-message", "children"),
        Output("login-store", "data"),
        Input("login-button", "n_clicks"),
        Input("logout-button", "n_clicks"),
        State("username", "value"),
        State("password", "value"),
        prevent_initial_call=True
    )
    def handle_login_logout(n_login, n_logout, username, password):
        trigger = ctx.triggered_id

        if trigger == "logout-button":
            user_session["user"] = None
            user_session["perfil_id"] = None
            user_session["apps_permitidos"] = []
            return "/login", "", {}

        user_data = check_credentials(username, password)
        if user_data:
            apps = get_apps_por_perfil(user_data["perfil_id"])

            user_session["user"] = user_data["username"]
            user_session["perfil_id"] = user_data["perfil_id"]
            user_session["apps_permitidos"] = apps

            data = {
                "user": user_data["username"],
                "perfil_id": user_data["perfil_id"],
                "apps_permitidos": apps
            }

            if user_data["perfil_nome"] == "admin":
                return "/hub", "", data
            elif apps:
                return apps[0]["rota"], "", data
            else:
                return no_update, "Usuário sem permissões definidas", no_update

        return no_update, "Usuário ou senha inválidos", no_update
