import streamlit as st
from supabase import create_client
import time

# ==============================
# 🔑 CONFIG
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# ==============================
# 🧠 SESSION
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None

if "session" not in st.session_state:
    st.session_state.session = None

if "treino_selecionado" not in st.session_state:
    st.session_state.treino_selecionado = None

if "descanso_ate" not in st.session_state:
    st.session_state.descanso_ate = None

# ==============================
# 🔐 CLIENTE AUTH
# ==============================
def get_db():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if st.session_state.session:
        client.postgrest.auth(
            st.session_state.session.access_token
        )
    return client

# ==============================
# 🎯 FUNÇÕES
# ==============================
def login(email, senha):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    res = client.auth.sign_in_with_password({
        "email": email,
        "password": senha
    })

    st.session_state.user = res.user
    st.session_state.session = res.session
    st.rerun()

def logout():
    st.session_state.user = None
    st.session_state.session = None
    st.rerun()

# ==============================
# 🎨 ESTILO
# ==============================
st.set_page_config(page_title="Treino", layout="centered")

st.markdown("""
<style>
.stButton>button {
    border-radius: 10px;
    padding: 0.5rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 🖥️ APP
# ==============================
st.title("🏋️ Treino")

# ==============================
# 🔐 LOGIN
# ==============================
if not st.session_state.user:

    st.subheader("🔐 Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        login(email, senha)

# ==============================
# ✅ LOGADO
# ==============================
else:
    db = get_db()

    st.success(f"👤 {st.session_state.user.email}")

    if st.button("Sair"):
        logout()

    st.divider()

    # ==============================
    # 📂 LISTA TREINOS
    # ==============================
    if not st.session_state.treino_selecionado:

        st.subheader("🏋️ Seus Treinos")

        novo = st.text_input("Novo treino")

        if st.button("➕ Criar"):
            if novo:
                db.table("workouts").insert({
                    "user_id": st.session_state.user.id,
                    "nome": novo
                }).execute()
                st.rerun()

        res = db.table("workouts") \
            .select("*") \
            .eq("user_id", st.session_state.user.id) \
            .execute()

        for t in res.data or []:
            col1, col2 = st.columns([4,1])

            with col1:
                if st.button(f"🏋️ {t['nome']}", key=t["id"]):
                    st.session_state.treino_selecionado = t
                    st.rerun()

            with col2:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    db.table("workouts").delete().eq("id", t["id"]).execute()
                    st.rerun()

    # ==============================
    # 💪 TREINO
    # ==============================
    else:
        treino = st.session_state.treino_selecionado

        st.subheader(f"🏋️ {treino['nome']}")

        col1, col2 = st.columns([1,1])

        with col1:
            if st.button("⬅️ Voltar"):
                st.session_state.treino_selecionado = None
                st.rerun()

        with col2:
            modo_edicao = st.toggle("✏️ Editar")

        st.divider()

        # ==============================
        # ⏱️ TIMER
        # ==============================
        st.markdown("### ⏱️ Descanso")

        c1, c2, c3 = st.columns(3)

        if c1.button("30s"):
            st.session_state.descanso_ate = time.time() + 30

        if c2.button("60s"):
            st.session_state.descanso_ate = time.time() + 60

        if c3.button("90s"):
            st.session_state.descanso_ate = time.time() + 90

        if st.session_state.descanso_ate:
            restante = int(st.session_state.descanso_ate - time.time())

            if restante > 0:
                st.warning(f"⏳ {restante}s")
                time.sleep(1)
                st.rerun()
            else:
                st.success("🔥 Bora!")
                st.session_state.descanso_ate = None

        st.divider()

        # ==============================
        # ➕ EXERCÍCIO (EDIÇÃO)
        # ==============================
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

        # ==============================
        # 📋 LISTA
        # ==============================
        res = db.table("exercises") \
            .select("*") \
            .eq("workout_id", treino["id"]) \
            .execute()

        st.markdown("### 💪 Exercícios")

        if res.data:
            for ex in res.data:

                col1, col2, col3 = st.columns([4,1,1])

                nome = ex["nome"]
                if ex["done"]:
                    nome = f"~~{nome}~~ ✅"

                with col1:
                    checked = st.checkbox(
                        nome,
                        value=ex["done"],
                        key=f"chk_{ex['id']}"
                    )

                    if checked != ex["done"]:
                        db.table("exercises") \
                            .update({"done": checked}) \
                            .eq("id", ex["id"]) \
                            .execute()

                with col2:
                    if st.button("⏱️", key=f"t_{ex['id']}"):
                        st.session_state.descanso_ate = time.time() + 60
                        st.rerun()

                with col3:
                    if modo_edicao:
                        if st.button("🗑️", key=ex["id"]):
                            db.table("exercises") \
                                .delete() \
                                .eq("id", ex["id"]) \
                                .execute()
                            st.rerun()
        else:
            st.info("Nenhum exercício")

        st.divider()

        # ==============================
        # 🏁 FINALIZAR
        # ==============================
        if st.button("✅ Finalizar treino"):
            db.table("exercises") \
                .update({"done": True}) \
                .eq("workout_id", treino["id"]) \
                .execute()

            st.success("Treino finalizado!")
            st.rerun()