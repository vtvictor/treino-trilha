import streamlit as st
from supabase import create_client

# ==============================
# 🔑 CONFIG (via secrets)
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 🧠 SESSION
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None

# ==============================
# 🎯 FUNÇÕES
# ==============================
def login(email, senha):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })
        st.session_state.user = res.user
        st.success("✅ Login realizado!")
    except Exception as e:
        st.error(f"❌ Erro no login: {e}")


def logout():
    st.session_state.user = None
    st.success("Você saiu da conta")

# ==============================
# 🖥️ INTERFACE
# ==============================
st.title("🏋️ App de Treino")

# ==============================
# 🔐 TELA DE LOGIN
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

    # 🔍 DEBUG (IMPORTANTE AGORA)
    st.write("### 🧪 Debug usuário")
    st.json(st.session_state.user)

    # ==============================
    # 🏋️ TREINOS
    # ==============================
    st.subheader("🏋️ Seus Treinos")

    # Criar treino
    novo_treino = st.text_input("Nome do treino")

    if st.button("➕ Criar treino"):
        if novo_treino:
            try:
                response = supabase.table("workouts").insert({
                    "user_id": st.session_state.user.id,
                    "nome": novo_treino
                }).execute()

                st.success("✅ Treino criado!")
                st.json(response.data)

            except Exception as e:
                st.error("❌ Erro ao criar treino")
                st.write(e)
        else:
            st.warning("Digite um nome para o treino")

    # Buscar treinos
    try:
        res = supabase.table("workouts") \
            .select("*") \
            .eq("user_id", st.session_state.user.id) \
            .execute()

        st.write("### 📋 Seus treinos:")

        if res.data:
            for treino in res.data:
                st.write(f"🏋️ {treino['nome']}")
        else:
            st.info("Você ainda não criou nenhum treino.")

    except Exception as e:
        st.error("❌ Erro ao buscar treinos")
        st.write(e)