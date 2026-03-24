import streamlit as st
from supabase import create_client

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

# ==============================
# 🔐 CLIENTE AUTENTICADO
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
    db = get_supabase()

    db.table("workouts").insert({
        "user_id": st.session_state.user.id,
        "nome": nome
    }).execute()

    st.success("✅ Treino criado!")
    st.rerun()


def deletar_treino(treino_id):
    db = get_supabase()

    db.table("workouts") \
        .delete() \
        .eq("id", treino_id) \
        .execute()

    st.success("🗑️ Treino excluído!")
    st.rerun()


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
    st.success(f"👤 {st.session_state.user.email}")

    if st.button("🚪 Sair"):
        logout()

    st.divider()

    db = get_supabase()

    # ==============================
    # 📂 SE NÃO TEM TREINO ABERTO
    # ==============================
    if not st.session_state.treino_selecionado:

        st.subheader("🏋️ Seus Treinos")

        novo_treino = st.text_input("Nome do treino")

        if st.button("➕ Criar treino"):
            if novo_treino:
                criar_treino(novo_treino)
            else:
                st.warning("Digite um nome")

        res = db.table("workouts") \
            .select("*") \
            .eq("user_id", st.session_state.user.id) \
            .execute()

        st.write("### 📋 Seus treinos:")

        if res.data:
            for treino in res.data:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    if st.button(treino["nome"], key=f"open_{treino['id']}"):
                        st.session_state.treino_selecionado = treino
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_{treino['id']}"):
                        deletar_treino(treino["id"])

        else:
            st.info("Nenhum treino ainda")

    # ==============================
    # 💪 TELA DE EXERCÍCIOS
    # ==============================
    else:
        treino = st.session_state.treino_selecionado

        st.subheader(f"🏋️ {treino['nome']}")

        if st.button("⬅️ Voltar"):
            st.session_state.treino_selecionado = None
            st.rerun()

        st.divider()

        # Criar exercício
        novo_ex = st.text_input("Nome do exercício")

        if st.button("➕ Adicionar exercício"):
            if novo_ex:
                db.table("exercises").insert({
                    "workout_id": treino["id"],
                    "nome": novo_ex
                }).execute()

                st.success("Exercício adicionado!")
                st.rerun()
            else:
                st.warning("Digite um nome")

        # Listar exercícios
        res = db.table("exercises") \
            .select("*") \
            .eq("workout_id", treino["id"]) \
            .execute()

        st.write("### 📋 Exercícios:")

        if res.data:
            for ex in res.data:
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"💪 {ex['nome']}")

                with col2:
                    if st.button("🗑️", key=ex["id"]):
                        db.table("exercises") \
                            .delete() \
                            .eq("id", ex["id"]) \
                            .execute()

                        st.rerun()
        else:
            st.info("Nenhum exercício ainda")