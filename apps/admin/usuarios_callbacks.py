@callback(
    Output("dropdown-perfil", "options"),
    Input("interval-refresh", "n_intervals")
)
def carregar_perfis(_):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM perfis ORDER BY nome")
    opcoes = [{"label": nome, "value": id} for id, nome in cursor.fetchall()]
    conn.close()
    return opcoes


@callback(
    Output("mensagem-usuario", "children"),
    Output("tabela-usuarios", "children"),
    Input("botao-criar-usuario", "n_clicks"),
    State("input-nome", "value"),
    State("input-email", "value"),
    State("input-senha", "value"),
    State("dropdown-perfil", "value"),
    prevent_initial_call=True
)
def criar_usuario(n_clicks, nome, email, senha, perfil_id):
    if not all([nome, email, senha, perfil_id]):
        raise PreventUpdate

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, senha, email, perfil_id)
            VALUES (%s, %s, %s, %s)
        """, (nome, senha, email, perfil_id))
        conn.commit()
        mensagem = f"✅ Usuário '{nome}' criado com sucesso!"
    except Exception as e:
        conn.rollback()
        mensagem = f"❌ Erro ao criar usuário: {e}"
    finally:
        conn.close()

    return mensagem, gerar_tabela_usuarios()


def gerar_tabela_usuarios():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT u.nome, u.email, p.nome as perfil
        FROM usuarios u
        JOIN perfis p ON u.perfil_id = p.id
        ORDER BY u.nome
    """, conn)
    conn.close()

    return html.Table([
        html.Thead(html.Tr([html.Th(col) for col in df.columns])),
        html.Tbody([
            html.Tr([html.Td(row[col]) for col in df.columns]) for _, row in df.iterrows()
        ])
    ], style={"border": "1px solid #ccc", "width": "100%", "marginTop": "10px", "color": "white"})
