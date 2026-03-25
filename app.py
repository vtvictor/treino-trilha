import time

import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

SESSION_DEFAULTS = {
    "user": None,
    "session": None,
    "treino_selecionado": None,
    "descanso_ate": None,
    "descanso_total": None,
    "editando_treino_id": None,
}


st.set_page_config(
    page_title="Treino em Foco",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="TF",
)


def inject_styles():
    st.markdown(
        """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        .stApp {
            background:
                radial-gradient(circle at top, #1f2937 0%, #0f172a 55%, #020617 100%);
            -webkit-user-select: none;
            color: #e5e7eb;
        }

        [data-testid="stAppViewContainer"] > div {
            padding-top: 1rem;
        }

        .block-container {
            max-width: 480px !important;
            padding: 1rem !important;
            background: rgba(15, 23, 42, 0.92);
            min-height: 100vh;
            box-shadow: 0 0 30px rgba(0,0,0,0.25);
            border-left: 1px solid rgba(148, 163, 184, 0.12);
            border-right: 1px solid rgba(148, 163, 184, 0.12);
        }

        h1 { font-size: 1.6rem; margin-bottom: 0.4rem; color: #f8fafc; }
        h2 { font-size: 1.25rem; margin-top: 0; color: #f8fafc; }
        h3 {
            font-size: 1.02rem;
            color: #94a3b8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.4rem;
        }

        p, label, div[data-testid="stMarkdownContainer"] {
            color: #e5e7eb;
        }

        .eyebrow {
            color: #60a5fa;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            margin-bottom: 0.2rem;
        }

        .card, .card-done, .timer-card {
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 0.8rem;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }

        .card {
            background: rgba(30, 41, 59, 0.9);
        }

        .card-done {
            background:
                linear-gradient(135deg, rgba(22, 163, 74, 0.16), rgba(30, 41, 59, 0.72));
            box-shadow: inset 0 0 0 1px rgba(74, 222, 128, 0.12);
        }

        .timer-card {
            background:
                linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(15, 23, 42, 0.92));
        }

        .exercise-name {
            padding-top: 0.55rem;
            font-weight: 600;
            color: #f8fafc;
        }

        .exercise-name.done {
            color: #bbf7d0;
            text-decoration: line-through;
        }

        .exercise-meta {
            font-size: 0.82rem;
            color: #94a3b8;
            margin-top: 0.15rem;
        }

        .timer-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.2rem;
        }

        div.stButton > button:first-child {
            width: 100%;
            border: none;
            border-radius: 14px;
            height: 3.25rem;
            font-weight: 600;
            font-size: 0.98rem;
            transition: all 0.2s;
            margin-top: 0.5rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.18);
        }

        div.stButton > button:first-child:hover {
            transform: translateY(-1px);
        }

        [data-testid="stForm"] div.stButton > button:first-child {
            background-color: #2563eb;
            color: white;
        }

        div.stButton > button[kind="primary"] {
            background-color: #16a34a;
            color: white;
            height: 3.9rem;
            font-size: 1.05rem;
        }

        .stCheckbox {
            margin-bottom: -8px;
        }

        div[data-baseweb="input"] > div {
            background-color: rgba(15, 23, 42, 0.9);
            color: #f8fafc;
            border-color: rgba(148, 163, 184, 0.25);
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stToggle"] label {
            color: #e5e7eb !important;
        }

        div[data-testid="stAlert"] {
            background-color: rgba(30, 41, 59, 0.95);
            color: #e5e7eb;
            border: 1px solid rgba(148, 163, 184, 0.18);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def init_session_state():
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get_db():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if st.session_state.session:
        client.postgrest.auth(st.session_state.session.access_token)
    return client


def fetch_workouts():
    response = (
        get_db()
        .table("workouts")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .order("nome")
        .execute()
    )
    return response.data or []


def fetch_exercises(workout_id):
    response = (
        get_db()
        .table("exercises")
        .select("*")
        .eq("workout_id", workout_id)
        .order("id")
        .execute()
    )
    return response.data or []


def fetch_history():
    response = (
        get_db()
        .table("workout_history")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .order("data", desc=True)
        .execute()
    )
    return response.data or []


def clear_exercise_checkbox_state(exercises):
    for exercise in exercises or []:
        st.session_state.pop(f"chk_{exercise['id']}", None)


def reset_timer():
    st.session_state.descanso_ate = None
    st.session_state.descanso_total = None


def login(email, senha):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": senha}
        )
        if response.user:
            st.session_state.user = response.user
            st.session_state.session = response.session
            return True
        return False
    except Exception as exc:
        st.error(f"Erro: {exc}")
        return False


def logout():
    treino = st.session_state.treino_selecionado
    if treino:
        clear_exercise_checkbox_state(fetch_exercises(treino["id"]))

    st.session_state.user = None
    st.session_state.session = None
    st.session_state.treino_selecionado = None
    st.session_state.editando_treino_id = None
    reset_timer()
    st.rerun()


def criar_treino(nome):
    get_db().table("workouts").insert(
        {"user_id": st.session_state.user.id, "nome": nome}
    ).execute()


def deletar_treino(workout_id):
    get_db().table("workouts").delete().eq("id", workout_id).execute()


def editar_nome_treino(workout_id, novo_nome):
    get_db().table("workouts").update({"nome": novo_nome}).eq(
        "id", workout_id
    ).execute()


def atualizar_exercicio(exercise_id, done):
    get_db().table("exercises").update({"done": done}).eq(
        "id", exercise_id
    ).execute()


def atualizar_exercicio_callback(exercise_id):
    atualizar_exercicio(exercise_id, st.session_state[f"chk_{exercise_id}"])


def adicionar_exercicio(workout_id, nome):
    get_db().table("exercises").insert(
        {"workout_id": workout_id, "nome": nome, "done": False}
    ).execute()


def excluir_exercicio(exercise_id):
    get_db().table("exercises").delete().eq("id", exercise_id).execute()


def finalizar_treino(treino):
    db = get_db()
    exercises = fetch_exercises(treino["id"])

    db.table("workout_history").insert(
        {
            "user_id": st.session_state.user.id,
            "workout_id": treino["id"],
            "nome": treino["nome"],
        }
    ).execute()
    db.table("exercises").update({"done": False}).eq(
        "workout_id", treino["id"]
    ).execute()

    clear_exercise_checkbox_state(exercises)
    st.session_state.treino_selecionado = None
    reset_timer()
    st.success("Treino finalizado!")
    st.rerun()


def voltar_para_lista():
    treino = st.session_state.treino_selecionado
    if treino:
        clear_exercise_checkbox_state(fetch_exercises(treino["id"]))
    st.session_state.treino_selecionado = None
    st.session_state.editando_treino_id = None
    reset_timer()
    st.rerun()


def render_login():
    st.markdown(
        """
        <div class="eyebrow">Treino em Foco</div>
        <h1 style="text-align: center;">Seu treino, sem distrações</h1>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="******")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            with st.spinner("Autenticando..."):
                if login(email, senha):
                    st.rerun()
                st.error("Dados incorretos.")


def render_header():
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        display_name = st.session_state.user.email.split("@")[0]
        st.markdown(
            f"<div class='eyebrow'>Area do aluno</div><h2>Ola, {display_name}</h2>",
            unsafe_allow_html=True,
        )
    with col_logout:
        if st.button("Sair", use_container_width=True):
            logout()


def render_history_tab():
    st.markdown("<h3>Historico</h3>", unsafe_allow_html=True)
    history_items = fetch_history()

    if not history_items:
        st.info("Nenhum treino finalizado ainda.")
        return

    for item in history_items:
        data_formatada = item["data"][:10]
        st.markdown(
            f"""
            <div class="card">
                <div style="font-weight: 700; font-size: 1.08rem;">{item['nome']}</div>
                <div class="exercise-meta">Concluido em {data_formatada}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_workout_list():
    st.markdown("<h3>Meus Treinos</h3>", unsafe_allow_html=True)

    with st.form("novo_treino", clear_on_submit=True):
        col_novo, col_btn = st.columns([3, 1])
        with col_novo:
            novo_nome = st.text_input(
                "Nome do treino",
                label_visibility="collapsed",
                placeholder="Ex: Peito",
            )
        with col_btn:
            submitted = st.form_submit_button("+")
            if submitted and novo_nome.strip():
                criar_treino(novo_nome.strip())
                st.rerun()

    workouts = fetch_workouts()
    if not workouts:
        st.info("Crie seu primeiro treino para começar.")
        return

    for treino in workouts:
        is_editing = st.session_state.editando_treino_id == treino["id"]
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if not is_editing:
            c1, c2, c3 = st.columns([3, 1, 1])
            if c1.button(
                treino["nome"],
                key=f"sel_{treino['id']}",
                use_container_width=True,
            ):
                st.session_state.treino_selecionado = treino
                st.rerun()

            if c2.button("Editar", key=f"btn_edit_{treino['id']}"):
                st.session_state.editando_treino_id = treino["id"]
                st.rerun()

            if c3.button("Excluir", key=f"del_{treino['id']}"):
                deletar_treino(treino["id"])
                st.rerun()
        else:
            with st.form(key=f"form_edit_{treino['id']}"):
                novo_nome_edit = st.text_input(
                    "Novo nome",
                    value=treino["nome"],
                    label_visibility="collapsed",
                )
                col_salvar, col_cancelar = st.columns(2)
                if col_salvar.form_submit_button("Salvar"):
                    editar_nome_treino(treino["id"], novo_nome_edit.strip())
                    st.session_state.editando_treino_id = None
                    st.rerun()
                if col_cancelar.form_submit_button("Cancelar"):
                    st.session_state.editando_treino_id = None
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_timer_section():
    st.markdown("<h3>Cronometro</h3>", unsafe_allow_html=True)
    col_30, col_60, col_90 = st.columns(3)

    if col_30.button("30s", key="timer_30", use_container_width=True):
        st.session_state.descanso_ate = time.time() + 30
        st.session_state.descanso_total = 30
        st.rerun()
    if col_60.button("60s", key="timer_60", use_container_width=True):
        st.session_state.descanso_ate = time.time() + 60
        st.session_state.descanso_total = 60
        st.rerun()
    if col_90.button("90s", key="timer_90", use_container_width=True):
        st.session_state.descanso_ate = time.time() + 90
        st.session_state.descanso_total = 90
        st.rerun()

    if not st.session_state.descanso_ate:
        st.caption("Escolha um descanso quando quiser. O cronometro nao trava mais a tela.")
        return

    restante = max(0, int(st.session_state.descanso_ate - time.time()))
    total = max(st.session_state.descanso_total or 1, 1)
    progresso = min(1.0, max(0.0, 1 - (restante / total)))

    if restante == 0:
        st.markdown(
            """
            <div class="timer-card">
                <div class="eyebrow">Descanso</div>
                <div class="timer-value">Pronto</div>
                <div class="exercise-meta">Seu descanso terminou.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Limpar cronometro", key="clear_timer", use_container_width=True):
            reset_timer()
            st.rerun()
        return

    st.markdown(
        f"""
        <div class="timer-card">
            <div class="eyebrow">Descanso em andamento</div>
            <div class="timer-value">{restante}s</div>
            <div class="exercise-meta">
                O tempo continua correndo sem bloquear os outros botoes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progresso)

    col_refresh, col_stop = st.columns(2)
    if col_refresh.button("Atualizar tempo", key="refresh_timer", use_container_width=True):
        st.rerun()
    if col_stop.button("Encerrar descanso", key="stop_timer", use_container_width=True):
        reset_timer()
        st.rerun()


def render_exercise_list(treino, modo_edicao):
    st.markdown("<h3>Exercicios</h3>", unsafe_allow_html=True)
    exercises = fetch_exercises(treino["id"])

    if not exercises:
        st.info("Lista vazia.")
        return

    for ex in exercises:
        key = f"chk_{ex['id']}"
        if key not in st.session_state:
            st.session_state[key] = ex["done"]

        is_done = bool(st.session_state[key])
        card_class = "card-done" if is_done else "card"
        status_text = "Concluido" if is_done else "Pendente"
        name_class = "exercise-name done" if is_done else "exercise-name"

        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        col_check, col_text, col_del = st.columns([1, 4, 1])

        col_check.checkbox(
            "",
            key=key,
            label_visibility="collapsed",
            on_change=atualizar_exercicio_callback,
            args=(ex["id"],),
        )

        col_text.markdown(
            f"""
            <div class="{name_class}">{ex['nome']}</div>
            <div class="exercise-meta">{status_text}</div>
            """,
            unsafe_allow_html=True,
        )

        if modo_edicao:
            if col_del.button("Excluir", key=f"ex_del_{ex['id']}"):
                st.session_state.pop(key, None)
                excluir_exercicio(ex["id"])
                st.rerun()
        else:
            col_del.write("")

        st.markdown("</div>", unsafe_allow_html=True)


def render_workout_detail():
    treino = st.session_state.treino_selecionado

    col_voltar, col_titulo = st.columns([1, 5])
    with col_voltar:
        if st.button("<-", key="voltar_treino"):
            voltar_para_lista()
    with col_titulo:
        st.markdown(f"<h2>{treino['nome']}</h2>", unsafe_allow_html=True)

    modo_edicao = st.toggle("Editar lista")
    render_timer_section()

    if modo_edicao:
        with st.form("add_ex", clear_on_submit=True):
            ex_nome = st.text_input(
                "Adicionar exercicio",
                label_visibility="collapsed",
                placeholder="Ex: Supino",
            )
            if st.form_submit_button("Adicionar", use_container_width=True):
                if ex_nome.strip():
                    adicionar_exercicio(treino["id"], ex_nome.strip())
                    st.rerun()

    render_exercise_list(treino, modo_edicao)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("FINALIZAR TREINO", use_container_width=True, type="primary"):
        finalizar_treino(treino)


def render_authenticated_app():
    render_header()
    aba = st.radio(
        "",
        ["Treinos", "Historico"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if aba == "Historico":
        render_history_tab()
        return

    if st.session_state.treino_selecionado:
        render_workout_detail()
    else:
        render_workout_list()


inject_styles()
init_session_state()

if st.session_state.user:
    render_authenticated_app()
else:
    render_login()
