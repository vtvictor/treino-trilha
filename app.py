import streamlit as st
from supabase import create_client

# ==============================
# 🔑 CONFIG (usar secrets)
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
    except:
        st.error("❌ Email ou senha inválidos")


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

    st.subheader("🏋️ Área do usuário")

    st.info("""
    Próximas funcionalidades:
    - Criar treinos
    - Adicionar exercícios
    - Timer de descanso
    - Histórico
    """)