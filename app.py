import streamlit as st
from supabase import create_client

# ==============================
# 🔑 CONFIG (via secrets)
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

# ==============================
# 🔐 CLIENTE AUTENTICADO (FIX RLS)
# ==============================
def get_supabase():
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
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        res = client.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })

        st.session_state.user = res.user
        st.session_state.session = res.session

        st.success("✅ Login realizado!")
    except Exception as e:
        st.error(f"❌ Erro no login: {e}")


def logout():
    st.session_state.user = None
    st.session_state.session = None
    st.success("Você saiu da conta")


def criar_treino(nome):
    try:
        db = get_supabase()

        db.table("workouts").insert({
            "user_id": st.session_state.user.id,
            "nome": nome
        }).execute()

        st.success("✅ Treino criado!")
        st.rerun()

    except Exception as e:
        st.error("❌ Erro ao criar treino")
        st.write(e)


def deletar_treino(treino_id):
    try:
        db = get_supabase()

        db.table("workouts") \
            .delete() \
            .eq("id", treino_id) \
            .execute()

        st.success("🗑️ Treino excluído!")
        st.rerun()

    except Exception as e:
        st.error("❌ Erro ao excluir treino")
        st.write(e)

# ==============================
# 🖥️ INTERFACE
# ==============================
st.title("🏋️ App de Treino")

# ==============================
# 🔐 LOGIN
# ==============================
if not st.session_state.user:

    st.subheader("🔐 Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if email and senha:
            login(email, senha)
        else:
            st.warning("Preencha email e senha")

# ==============================
# ✅ USUÁRIO LOGADO
# ==============================
else:
    st.success(f"👤 Logado como: {st.session_state.user.email}")

    if st.button("🚪 Sair"):
        logout()

    st.divider()

    # ==============================
    # 🏋️ TREINOS
    # ==============================
    st.subheader("🏋️ Seus Treinos")

    novo_treino = st.text_input("Nome do treino")

    if st.button("➕ Criar treino"):
        if novo_treino:
            criar_treino(novo_treino)
        else:
            st.warning("Digite um nome para o treino")

    # ==============================
    # 📋 LISTAR TREINOS
    # ==============================
    try:
        db = get_supabase()

        res = db.table("workouts") \
            .select("*") \
            .eq("user_id", st.session_state.user.id) \
            .execute()

        st.write("### 📋 Seus treinos:")

        if res.data:
            for treino in res.data:
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"🏋️ {treino['nome']}")

                with col2:
                    if st.button("🗑️", key=treino["id"]):
                        deletar_treino(treino["id"])
        else:
            st.info("Você ainda não criou nenhum treino.")

    except Exception as e:
        st.error("❌ Erro ao buscar treinos")
        st.write(e)