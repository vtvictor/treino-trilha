import time
import json

import streamlit as st
from supabase import create_client

try:
    from streamlit_local_storage import LocalStorage
except ImportError:
    LocalStorage = None


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
AUTH_STORAGE_KEY = "treino_em_foco_auth_session"

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

        .card, .card-done, .timer-card, .summary-card {
            border-radius: 16px;
            padding: 0.85rem;
            margin-bottom: 0.65rem;
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

        .summary-card {
            background:
                linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(15, 23, 42, 0.95));
        }

        .exercise-name {
            font-weight: 600;
            color: #f8fafc;
            font-size: 0.96rem;
            line-height: 1.2;
        }

        .exercise-name.done {
            color: #bbf7d0;
            text-decoration: line-through;
        }

        .exercise-meta {
            font-size: 0.76rem;
            color: #94a3b8;
            margin-top: 0.12rem;
        }

        .progress-copy {
            font-size: 0.92rem;
            font-weight: 700;
            color: #f8fafc;
            text-align: right;
        }

        .dot-row {
            margin-top: 0.22rem;
            letter-spacing: 0.1rem;
            color: #94a3b8;
            font-size: 0.82rem;
            text-align: right;
        }

        .dot-row.done {
            color: #4ade80;
        }

        .series-chip-label {
            font-size: 0.68rem;
            color: #94a3b8;
            margin-top: 0.5rem;
            margin-bottom: -0.2rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .series-choices {
            margin-top: 0.15rem;
            margin-bottom: 0.15rem;
        }

        .series-choices div.stButton > button:first-child {
            height: 2.2rem;
            min-width: 2.2rem;
            margin-top: 0.2rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.14);
            color: #cbd5e1;
            box-shadow: none;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0;
        }

        .series-choices-active div.stButton > button:first-child {
            background: linear-gradient(135deg, #22c55e, #15803d);
            color: #f8fafc;
            border-color: transparent;
            box-shadow: 0 8px 18px rgba(34, 197, 94, 0.18);
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

        div[data-testid="column"] .series-chip button {
            height: 2.45rem !important;
            min-width: 2.45rem;
            margin-top: 0.22rem;
            border-radius: 999px !important;
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.16);
            color: #cbd5e1;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0;
        }

        div[data-testid="column"] .series-chip-active button {
            background: linear-gradient(135deg, #22c55e, #15803d) !important;
            color: #f8fafc !important;
            border-color: transparent !important;
            box-shadow: 0 8px 18px rgba(34, 197, 94, 0.22);
        }

        div[data-testid="column"] .series-chip button:hover {
            border-color: rgba(96, 165, 250, 0.45);
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

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            background-color: rgba(15, 23, 42, 0.9);
            color: #f8fafc;
            border-color: rgba(148, 163, 184, 0.25);
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stToggle"] label,
        div[data-testid="stNumberInput"] label {
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


def update_query_param(name, value):
    if value in (None, ""):
        if name in st.query_params:
            del st.query_params[name]
        return
    st.query_params[name] = str(value)


def get_local_storage_manager():
    if LocalStorage is None:
        return None
    return LocalStorage()


def clear_browser_auth_session():
    local_storage = get_local_storage_manager()
    if local_storage is None:
        return
    local_storage.setItem(AUTH_STORAGE_KEY, "")
    st.session_state.pop("browser_auth_payload", None)


def persist_browser_auth_session(session):
    if session is None:
        return

    payload = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }
    st.session_state["browser_auth_payload"] = payload

    local_storage = get_local_storage_manager()
    if local_storage is None:
        return
    local_storage.setItem(AUTH_STORAGE_KEY, json.dumps(payload))


def get_browser_auth_session():
    if "browser_auth_payload" in st.session_state:
        return st.session_state["browser_auth_payload"]

    local_storage = get_local_storage_manager()
    if local_storage is None:
        return None

    raw_value = local_storage.getItem(
        AUTH_STORAGE_KEY,
        key="local_storage_auth_session",
    )
    if not raw_value:
        return None

    try:
        payload = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
    except (TypeError, json.JSONDecodeError):
        return None

    if not payload or not payload.get("access_token") or not payload.get("refresh_token"):
        return None

    st.session_state["browser_auth_payload"] = payload
    return payload


def try_restore_browser_session():
    if st.session_state.user or st.session_state.session:
        return

    payload = get_browser_auth_session()
    if not payload:
        return

    fingerprint = (
        payload.get("access_token"),
        payload.get("refresh_token"),
    )
    if st.session_state.get("restored_auth_fingerprint") == fingerprint:
        return

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        response = client.auth.set_session(
            payload["access_token"],
            payload["refresh_token"],
        )
        st.session_state.user = response.user
        st.session_state.session = response.session
        st.session_state["restored_auth_fingerprint"] = fingerprint
        persist_browser_auth_session(response.session)
        st.rerun()
    except Exception:
        clear_browser_auth_session()


def sync_active_workout_query_params():
    treino = st.session_state.treino_selecionado
    update_query_param("treino", treino["id"] if treino else None)
    update_query_param("descanso_ate", st.session_state.descanso_ate)
    update_query_param("descanso_total", st.session_state.descanso_total)


def restore_workout_from_query_params():
    if st.session_state.treino_selecionado:
        return

    workout_id = st.query_params.get("treino")
    if not workout_id:
        return

    workouts = fetch_workouts()
    matching_workout = next(
        (workout for workout in workouts if str(workout["id"]) == str(workout_id)),
        None,
    )
    if not matching_workout:
        update_query_param("treino", None)
        update_query_param("descanso_ate", None)
        update_query_param("descanso_total", None)
        return

    st.session_state.treino_selecionado = matching_workout

    rest_until = st.query_params.get("descanso_ate")
    rest_total = st.query_params.get("descanso_total")
    try:
        st.session_state.descanso_ate = float(rest_until) if rest_until else None
        st.session_state.descanso_total = int(float(rest_total)) if rest_total else None
    except ValueError:
        reset_timer()
        sync_active_workout_query_params()


def get_db():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if st.session_state.session:
        client.postgrest.auth(st.session_state.session.access_token)
    return client


def parse_date(date_value):
    if not date_value:
        return ""
    return str(date_value)[:10]


def normalize_exercise(exercise):
    series_total = exercise.get("series_total")
    if series_total is None:
        series_total = 1
    series_total = max(int(series_total), 1)

    series_done = exercise.get("series_done")
    if series_done is None:
        series_done = series_total if exercise.get("done") else 0
    series_done = max(0, min(int(series_done), series_total))

    normalized = dict(exercise)
    normalized["series_total"] = series_total
    normalized["series_done"] = series_done
    normalized["done"] = series_done >= series_total
    return normalized


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
    return [normalize_exercise(item) for item in (response.data or [])]


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


def build_history_stats(history_items):
    stats = {}
    for item in history_items:
        workout_key = item.get("workout_id") or item["nome"]
        if workout_key not in stats:
            stats[workout_key] = {
                "nome": item["nome"],
                "count": 0,
                "last_date": item.get("data"),
                "exercise_total": item.get("exercise_total"),
            }
        stats[workout_key]["count"] += 1
        if item.get("data") and (
            not stats[workout_key]["last_date"]
            or str(item["data"]) > str(stats[workout_key]["last_date"])
        ):
            stats[workout_key]["last_date"] = item["data"]
            stats[workout_key]["exercise_total"] = item.get("exercise_total")
    return stats


def summarize_workout_progress(exercises):
    total_exercises = len(exercises)
    completed_exercises = 0
    total_series = 0
    completed_series = 0

    for exercise in exercises:
        current_series_done = get_current_series_done(exercise)
        total_series += exercise["series_total"]
        completed_series += current_series_done
        if current_series_done >= exercise["series_total"]:
            completed_exercises += 1

    remaining_exercises = max(total_exercises - completed_exercises, 0)
    return {
        "total_exercises": total_exercises,
        "completed_exercises": completed_exercises,
        "remaining_exercises": remaining_exercises,
        "total_series": total_series,
        "completed_series": completed_series,
    }


def clear_exercise_widget_state(exercises):
    for exercise in exercises or []:
        st.session_state.pop(f"series_control_{exercise['id']}", None)


def reset_timer():
    st.session_state.descanso_ate = None
    st.session_state.descanso_total = None
    sync_active_workout_query_params()


def login(email, senha):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": senha}
        )
        if response.user:
            st.session_state.user = response.user
            st.session_state.session = response.session
            persist_browser_auth_session(response.session)
            return True
        return False
    except Exception as exc:
        st.error(f"Erro: {exc}")
        return False


def logout():
    treino = st.session_state.treino_selecionado
    if treino:
        clear_exercise_widget_state(fetch_exercises(treino["id"]))

    st.session_state.user = None
    st.session_state.session = None
    st.session_state.treino_selecionado = None
    st.session_state.editando_treino_id = None
    clear_browser_auth_session()
    reset_timer()
    sync_active_workout_query_params()
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


def adicionar_exercicio(workout_id, nome, series_total):
    get_db().table("exercises").insert(
        {
            "workout_id": workout_id,
            "nome": nome,
            "done": False,
            "series_total": int(series_total),
            "series_done": 0,
        }
    ).execute()


def excluir_exercicio(exercise_id):
    get_db().table("exercises").delete().eq("id", exercise_id).execute()


def atualizar_progresso_exercicio(exercise, series_done):
    series_done = max(0, min(int(series_done), exercise["series_total"]))
    get_db().table("exercises").update(
        {
            "series_done": series_done,
            "done": series_done >= exercise["series_total"],
        }
    ).eq("id", exercise["id"]).execute()


def get_series_done_key(exercise_id):
    return f"series_control_{exercise_id}"


def get_current_series_done(exercise):
    series_key = get_series_done_key(exercise["id"])
    if series_key not in st.session_state:
        st.session_state[series_key] = exercise["series_done"]
    return int(st.session_state[series_key])


def set_exercise_series_done(exercise, series_done):
    clamped_value = max(0, min(int(series_done), exercise["series_total"]))
    st.session_state[get_series_done_key(exercise["id"])] = clamped_value
    atualizar_progresso_exercicio(exercise, clamped_value)


def finalizar_treino(treino):
    db = get_db()
    exercises = fetch_exercises(treino["id"])
    progress = summarize_workout_progress(exercises)

    db.table("workout_history").insert(
        {
            "user_id": st.session_state.user.id,
            "workout_id": treino["id"],
            "nome": treino["nome"],
            "exercise_done": progress["completed_exercises"],
            "exercise_total": progress["total_exercises"],
            "series_done": progress["completed_series"],
            "series_total": progress["total_series"],
        }
    ).execute()
    db.table("exercises").update({"done": False, "series_done": 0}).eq(
        "workout_id", treino["id"]
    ).execute()

    clear_exercise_widget_state(exercises)
    st.session_state.treino_selecionado = None
    reset_timer()
    sync_active_workout_query_params()
    st.success("Treino finalizado!")
    st.rerun()


def voltar_para_lista():
    treino = st.session_state.treino_selecionado
    if treino:
        clear_exercise_widget_state(fetch_exercises(treino["id"]))
    st.session_state.treino_selecionado = None
    st.session_state.editando_treino_id = None
    reset_timer()
    sync_active_workout_query_params()
    st.rerun()


def render_login():
    st.markdown(
        """
        <div class="eyebrow">Treino em Foco</div>
        <h1 style="text-align: center;">Seu treino, sem distracoes</h1>
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


def render_history_tab(history_items, history_stats):
    st.markdown("<h3>Historico</h3>", unsafe_allow_html=True)

    if not history_items:
        st.info("Nenhum treino finalizado ainda.")
        return

    st.markdown("<div class='eyebrow'>Resumo</div>", unsafe_allow_html=True)
    sorted_stats = sorted(
        history_stats.values(),
        key=lambda item: (item["count"], str(item["last_date"] or "")),
        reverse=True,
    )

    for stat in sorted_stats:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="exercise-name">{stat['nome']}</div>
                <div class="exercise-meta">
                    {stat['count']}/{stat.get('exercise_total') or stat['count']} execucoes · ultima em {parse_date(stat['last_date'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='eyebrow'>Ultimas sessoes</div>", unsafe_allow_html=True)
    for item in history_items:
        series_copy = ""
        exercise_copy = ""
        if item.get("exercise_total"):
            exercise_copy = (
                f" · {int(item.get('exercise_done', 0))}/{int(item['exercise_total'])} exercicios"
            )
        if item.get("series_total"):
            series_copy = (
                f" · {int(item.get('series_done', 0))}/{int(item['series_total'])} series"
            )
        st.markdown(
            f"""
            <div class="card">
                <div style="font-weight: 700; font-size: 1.08rem;">{item['nome']}</div>
                <div class="exercise-meta">
                    Concluido em {parse_date(item['data'])}{exercise_copy}{series_copy}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_workout_list(history_stats):
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
        st.info("Crie seu primeiro treino para comecar.")
        return

    for treino in workouts:
        is_editing = st.session_state.editando_treino_id == treino["id"]
        stat = history_stats.get(
            treino["id"], {"count": 0, "last_date": None, "nome": treino["nome"]}
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)

        if not is_editing:
            st.markdown(
                f"""
                <div class="exercise-meta">
                    {stat['count']} execucoes · ultima em {parse_date(stat['last_date']) or '--'}
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns([3, 1, 1])
            if c1.button(
                treino["nome"],
                key=f"sel_{treino['id']}",
                use_container_width=True,
            ):
                st.session_state.treino_selecionado = treino
                sync_active_workout_query_params()
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
        sync_active_workout_query_params()
        st.rerun()
    if col_60.button("60s", key="timer_60", use_container_width=True):
        st.session_state.descanso_ate = time.time() + 60
        st.session_state.descanso_total = 60
        sync_active_workout_query_params()
        st.rerun()
    if col_90.button("90s", key="timer_90", use_container_width=True):
        st.session_state.descanso_ate = time.time() + 90
        st.session_state.descanso_total = 90
        sync_active_workout_query_params()
        st.rerun()

    if not st.session_state.descanso_ate:
        st.caption("Escolha um descanso quando quiser. O cronometro nao trava a tela.")
        return

    @st.fragment(run_every="1s")
    def render_active_timer():
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
                <div class="exercise-meta">O tempo continua correndo sem bloquear o resto.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(progresso)

        if st.button("Encerrar descanso", key="stop_timer", use_container_width=True):
            reset_timer()
            st.rerun()

    render_active_timer()


def render_workout_summary(progress, history_stats, treino_id):
    stat = history_stats.get(treino_id, {"count": 0, "last_date": None})
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="eyebrow">Resumo do treino</div>
            <div class="progress-copy">
                {progress['completed_exercises']}/{progress['total_exercises']} exercicios concluidos
            </div>
            <div class="exercise-meta">
                {progress['remaining_exercises']} restantes ·
                {progress['completed_series']}/{progress['total_series']} series feitas ·
                {stat['count']} execucoes anteriores
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_exercise_progress(exercise):
    dots = []
    current_series_done = get_current_series_done(exercise)
    for index in range(exercise["series_total"]):
        dots.append("●" if index < current_series_done else "○")
    dot_class = "dot-row done" if current_series_done >= exercise["series_total"] else "dot-row"
    st.markdown(
        f"""
        <div class="progress-copy">{current_series_done}/{exercise['series_total']} series</div>
        <div class="{dot_class}">{' '.join(dots)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_exercise_list(treino, modo_edicao):
    st.markdown("<h3>Exercicios</h3>", unsafe_allow_html=True)
    exercises = fetch_exercises(treino["id"])

    if not exercises:
        st.info("Lista vazia.")
        return exercises

    for exercise in exercises:
        current_series_done = get_current_series_done(exercise)
        is_done = current_series_done >= exercise["series_total"]
        card_class = "card-done" if is_done else "card"
        name_class = "exercise-name done" if is_done else "exercise-name"
        status_text = "Concluido" if is_done else "Em andamento"

        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        top_left, top_right = st.columns([4, 2])
        with top_left:
            st.markdown(
                f"""
                <div class="{name_class}">{exercise['nome']}</div>
                <div class="exercise-meta">{status_text}</div>
                """,
                unsafe_allow_html=True,
            )
        with top_right:
            render_exercise_progress(exercise)

        st.markdown("<div class='series-chip-label'>Series</div>", unsafe_allow_html=True)
        series_cols = st.columns(exercise["series_total"] + 1)
        for index, column in enumerate(series_cols):
            button_label = "0" if index == 0 else str(index)
            wrapper_class = (
                "series-choices series-choices-active"
                if index == current_series_done
                else "series-choices"
            )
            column.markdown(f"<div class='{wrapper_class}'>", unsafe_allow_html=True)
            if column.button(
                button_label,
                key=f"series_button_{exercise['id']}_{index}",
                use_container_width=True,
            ):
                set_exercise_series_done(exercise, index)
                st.rerun()
            column.markdown("</div>", unsafe_allow_html=True)

        if modo_edicao:
            if st.button(
                "Excluir",
                key=f"delete_{exercise['id']}",
                use_container_width=True,
            ):
                excluir_exercicio(exercise["id"])
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    return exercises


def render_workout_detail(history_stats):
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
            col_nome, col_series = st.columns([3, 1.2])
            with col_nome:
                ex_nome = st.text_input(
                    "Adicionar exercicio",
                    label_visibility="collapsed",
                    placeholder="Ex: Leg 45",
                )
            with col_series:
                series_total = st.number_input(
                    "Series",
                    min_value=1,
                    max_value=12,
                    value=3,
                    step=1,
                )
            if st.form_submit_button("Adicionar", use_container_width=True):
                if ex_nome.strip():
                    adicionar_exercicio(treino["id"], ex_nome.strip(), series_total)
                    st.rerun()

    exercises = fetch_exercises(treino["id"])
    progress = summarize_workout_progress(exercises)
    render_workout_summary(progress, history_stats, treino["id"])
    render_exercise_list(treino, modo_edicao)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("FINALIZAR TREINO", use_container_width=True, type="primary"):
        finalizar_treino(treino)


def render_authenticated_app():
    history_items = fetch_history()
    history_stats = build_history_stats(history_items)
    restore_workout_from_query_params()
    persist_browser_auth_session(st.session_state.session)

    render_header()
    aba = st.radio(
        "",
        ["Treinos", "Historico"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if aba == "Historico":
        render_history_tab(history_items, history_stats)
        return

    if st.session_state.treino_selecionado:
        render_workout_detail(history_stats)
    else:
        render_workout_list(history_stats)


inject_styles()
init_session_state()
try_restore_browser_session()

if st.session_state.user:
    render_authenticated_app()
else:
    render_login()
