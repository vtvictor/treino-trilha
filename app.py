import streamlit as st
from supabase import create_client
import time

# CONFIG
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# SESSION
for key, default in {
    "user": None,
    "session": None,
    "treino_selecionado": None,
    "descanso_ate": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# DB
def get_db():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if st.session_state.session:
        client.postgrest.auth(st.session_state.session.access_token)
    return client

# AUTH
def login(email, senha):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        res = client.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })
        
        if res.user:
            st.session_state.user = res.user
            st.session_state.session = res.session
            return True
        else:
            return False
            
    except:
        return False

def logout():
    st.session_state.user = None
    st.session_state.session = None
    st.session_state.treino_selecionado = None
    st.rerun()

# ACTIONS
def criar_treino(nome):
    get_db().table("workouts").insert({
        "user_id": st.session_state.user.id,
        "nome": nome
    }).execute()

def deletar_treino(tid):
    get_db().table("workouts").delete().eq("id", tid).execute()

def atualizar_exercicio(eid, done):
    get_db().table("exercises").update({"done": done}).eq("id", eid).execute()

def finalizar_treino(treino):
    db = get_db()

    db.table("workout_history").insert({
        "user_id": st.session_state.user.id,
        "workout_id": treino["id"],
        "nome": treino["nome"]
    }).execute()

    db.table("exercises").update({
        "done": True
    }).eq("workout_id", treino["id"]).execute()

    st.session_state.treino_selecionado = None
    st.success("✅ Treino finalizado!")
    st.rerun()

# STYLE
st.set_page_config(page_title="Treino em Foco")
st.markdown("""
<style>
.card {background:#f5f5f5;padding:1rem;border-radius:12px;margin-bottom:1rem;}
.card-done {background:#d4edda;padding:1rem;border-radius:12px;margin-bottom:1rem;}
table {width:100%;border-collapse:collapse;}
td,th {padding:8px;border-bottom:1px solid #ddd;}
</style>
""", unsafe_allow_html=True)

# APP
st.title("🏋️ Treino em Foco")

# LOGIN
if not st.session_state.user:

    with st.form("login_form"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            sucesso = login(email, senha)
            if sucesso:
                st.rerun()
            else:
                st.error("Email ou senha inválidos")

# LOGADO
else:
    db = get_db()

    st.success(f"👤 {st.session_state.user.email}")

    if st.button("🚪 Sair"):
        logout()

    aba = st.radio("", ["Treinos", "Histórico"], horizontal=True)

    # HISTÓRICO
    if aba == "Histórico":
        st.subheader("📋 Histórico")

        res = db.table("workout_history")\
            .select("*")\
            .eq("user_id", st.session_state.user.id)\
            .order("data", desc=True)\
            .execute()

        if res.data:
            st.markdown("<table><tr><th>Treino</th><th>Data</th></tr>", unsafe_allow_html=True)
            for h in res.data:
                st.markdown(f"<tr><td>{h['nome']}</td><td>{h['data'][:16]}</td></tr>", unsafe_allow_html=True)
            st.markdown("</table>", unsafe_allow_html=True)
        else:
            st.info("Sem histórico")

    # TREINOS
    else:

        if not st.session_state.treino_selecionado:

            st.subheader("🏋️ Treinos")

            novo = st.text_input("Novo treino")

            if st.button("➕ Criar") and novo:
                criar_treino(novo)
                st.rerun()

            res = db.table("workouts")\
                .select("*")\
                .eq("user_id", st.session_state.user.id)\
                .execute()

            for t in res.data or []:

                c1, c2 = st.columns([4,1])

                if c1.button(t["nome"], key=t["id"]):
                    st.session_state.treino_selecionado = t
                    st.rerun()

                if c2.button("🗑️", key=f"del{t['id']}"):
                    deletar_treino(t["id"])
                    st.rerun()

        else:
            treino = st.session_state.treino_selecionado

            st.subheader(treino["nome"])

            col1, col2 = st.columns([1,1])

            with col1:
                if st.button("⬅️ Voltar"):
                    st.session_state.treino_selecionado = None
                    st.rerun()

            with col2:
                modo_edicao = st.toggle("✏️ Editar")

            # TIMER
            st.markdown("### ⏱️ Descanso")

            c1, c2, c3 = st.columns(3)

            if c1.button("30s"): st.session_state.descanso_ate = time.time()+30
            if c2.button("60s"): st.session_state.descanso_ate = time.time()+60
            if c3.button("90s"): st.session_state.descanso_ate = time.time()+90

            if st.session_state.descanso_ate:
                restante = int(st.session_state.descanso_ate - time.time())
                if restante > 0:
                    st.warning(f"⏳ {restante}s")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success("🔥 Bora!")
                    st.session_state.descanso_ate = None

            # EDITAR
            if modo_edicao:
                novo_ex = st.text_input("Novo exercício")
                if st.button("Adicionar"):
                    if novo_ex:
                        db.table("exercises").insert({
                            "workout_id": treino["id"],
                            "nome": novo_ex,
                            "done": False
                        }).execute()
                        st.rerun()

            # EXERCÍCIOS
            st.markdown("### 💪 Exercícios")

            res = db.table("exercises")\
                .select("*")\
                .eq("workout_id", treino["id"])\
                .execute()

            for ex in res.data or []:

                done = ex["done"]
                nome = ex["nome"]

                if done:
                    nome = f"~~{nome}~~ ✅"

                key = f"chk_{ex['id']}"

                if key not in st.session_state:
                    st.session_state[key] = done

                checked = st.checkbox(nome, key=key)

                if checked != done:
                    atualizar_exercicio(ex["id"], checked)

                if modo_edicao:
                    if st.button("🗑️", key=ex["id"]):
                        db.table("exercises").delete().eq("id", ex["id"]).execute()
                        st.rerun()

            # FINALIZAR
            if st.button("✅ Finalizar treino"):
                finalizar_treino(treino)