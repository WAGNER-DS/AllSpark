#apps/admin/callbacks.py
from dash import callback, Output, Input, State, html
import apps.admin.usuarios as usuarios
import apps.admin.perfis as perfis
import apps.admin.apps as apps_module
import apps.admin.permissoes as permissoes
from apps.admin.usuarios_callbacks import registrar_usuarios_callbacks


def registrar_callbacks_admin(app):
    registrar_usuarios_callbacks(app)
    # 🔧 Aqui registra o callback de exibição também!
    exibir_pagina_admin()


def exibir_pagina_admin():
    @callback(
        Output("admin-content", "children"),
        Input("url", "search"),
        State("login-store", "data")
    )
    def _carregar_view(search, session_data):
        if not session_data or session_data.get("perfil_id") != 1:
            return html.Div("🔒 Acesso restrito a administradores.", style={"color": "red"})

        if search:
            view = search.replace("?view=", "")
            if view == "usuarios":
                return usuarios.layout(session_data)
            elif view == "perfis":
                return perfis.layout(session_data)
            elif view == "apps":
                return apps_module.layout(session_data)
            elif view == "permissoes":
                return permissoes.layout(session_data)

        return html.Div("⚙️ Selecione uma opção no menu à esquerda.")
