from dash import callback, Output, Input, State
import apps.admin.usuarios as usuarios
import apps.admin.perfis as perfis
import apps.admin.apps as apps_module
import apps.admin.permissoes as permissoes

@callback(
    Output("admin-content", "children"),
    Input("url", "search"),
    State("login-store", "data")
)
def exibir_pagina_admin(search, session_data):
    if not session_data or session_data.get("perfil_id") != 1:
        return html.Div("Acesso negado")

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

    return html.Div("Selecione uma opção no menu.")
