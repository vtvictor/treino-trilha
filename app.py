import streamlit as st
from supabase import create_client

# ==============================
# 🔑 CONFIG (usar secrets depois)
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


def cadastro(email, senha):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": senha
        })
        st.success("✅ Conta criada! Agora faça login.")
    except:
        st.error("❌ Erro ao criar conta")


def logout():
    st.session_state.user = None
    st.success("Você saiu da conta")

# ==============================
# 🖥️ INTERFACE
# ==============================
st.title("🏋️ App de Treino")

# ==============================
# 🔐 SE NÃO ESTIVER LOGADO
# ==============================
if not st.session_state.user:

    st.subheader("🔐 Acesso")


    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if menu == "Login":
        if st.button("Entrar"):
            login(email, senha)

    if menu == "Cadastro":
        if st.button("Criar conta"):
            cadastro(email, senha)

# ==============================
# ✅ SE ESTIVER LOGADO
# ==============================
else:
    st.success(f"👤 Logado como: {st.session_state.user.email}")

    if st.button("🚪 Sair"):
        logout()

    st.divider()

    st.subheader("🏋️ Seu treino (em breve)")

    st.info("Aqui vamos colocar:\n- Treinos\n- Timer\n- Histórico")