import streamlit as st
from supabase import create_client
import time

# --- CONFIGURAÇÕES ---
# Correção: Certifique-se que as secrets estão configuradas no Streamlit Cloud ou localmente
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Configuração da Página para Mobile
st.set_page_config(
    page_title="Treino em Foco",
    layout="centered",
    initial_sidebar_state="collapsed", # Oculta sidebar no mobile
    page_icon="🏋️"
)

# --- ESTILO (MOBILE APP MODE) ---
st.markdown("""
<style>
    /* REMOVER ELEMENTOS DO STREAMLIT PARA PARECER UM APP NATIVO */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* IMPEDIR ZOOM E AJUSTAR TELA */
    .stApp {
        background-color: #F2F2F7; /* Cinza claro estilo iOS */
        -webkit-user-select: none; /* Evita seleção de texto acidental */
    }
    
    /* METATAG PARA VIEWPORT (Controle de escala) */
    [data-testid="stAppViewContainer"] > div {
        padding-top: 1rem;
    }

    /* CONTAINER PRINCIPAL */
    .block-container {
        max-width: 480px !important; /* Largura máxima de um celular grande */
        padding: 1rem !important;
        background-color: #ffffff;
        min-height: 100vh;
        box-shadow: 0 0 20px rgba(0,0,0,0.05);
    }

    /* TIPOGRAFIA */
    h1 { font-size: 1.5rem; margin-bottom: 0.5rem; color: #1c1c1e; }
    h2 { font-size: 1.25rem; margin-top: 0; color: #1c1c1e; }
    h3 { font-size: 1.1rem; color: #8e8e93; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 1.5rem; }

    /* CARTÕES E ITENS */
    .card {
        background: #ffffff;
        border: 1px solid #e5e5ea;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        transition: transform 0.1s;
    }
    .card:active {
        transform: scale(0.98);
        background-color: #f2f2f7;
    }
    .card-done {
        background: #f2f2f7;
        border: 1px solid #e5e5ea;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        opacity: 0.6;
    }
    .card-done p, .card-done div {
        text-decoration: line-through;
        color: #8e8e93;
    }
    
    /* BOTÕES */
    div.stButton > button:first-child {
        width: 100%;
        border: none;
        border-radius: 12px;
        height: 3.5rem; /* Botões grandes para o dedo */
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s;
        margin-top: 0.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Cores dos Botões */
    [data-testid="stForm"] div.stButton > button:first-child {
        background-color: #007AFF; /* Azul iOS */
        color: white;
    }
    div.stButton > button[kind="primary"] {
        background-color: #34C759; /* Verde iOS */
        color: white;
        height: 4rem; /* Botão de finalizar maior ainda */
        font-size: 1.1rem;
    }

    /* CHECKBOX CUSTOMIZADO (Visual) */
    .stCheckbox { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)

# Injetar meta tag para impedir zoom no mobile ( truque com JS simples se necessário, 
# mas o layout centralizado ajuda. O Streamlit lida bem com viewport agora.)

# --- ESTADO DA SESSÃO ---
for key, default in {
    "user": None,
    "session": None,
    "treino_selecionado": None,
    "descanso_ate": None,
    "descanso_total": None,
    "editando_treino_id": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- BANCO DE DADOS ---
def get_db():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if st.session_state.session:
        client.postgrest.auth(st.session_state.session.access_token)
    return client

# --- AUTENTICAÇÃO ---
def login(email, senha):
    # CORRIGIDO AQUI: estava SSUPABASE_URL
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
            
    except Exception as e:
        st.error(f"Erro: {e}")
        return False

def logout():
    st.session_state.user = None
    st.session_state.session = None
    st.session_state.treino_selecionado = None
    st.rerun()

# --- AÇÕES (CRUD) ---
def criar_treino(nome):
    get_db().table("workouts").insert({
        "user_id": st.session_state.user.id,
        "nome": nome
    }).execute()

def deletar_treino(tid):
    get_db().table("workouts").delete().eq("id", tid).execute()

def editar_nome_treino(tid, novo_nome):
    get_db().table("workouts").update({"nome": novo_nome}).eq("id", tid).execute()

def atualizar_exercicio(eid, done):
    get_db().table("exercises").update({"done": done}).eq("id", eid).execute()

def finalizar_treino(treino):
    db = get_db()
    db.table("workout_history").insert({
        "user_id": st.session_state.user.id,
        "workout_id": treino["id"],
        "nome": treino["nome"]
    }).execute()
    # Reseta exercícios para o próximo treino
    db.table("exercises").update({"done": False}).eq("workout_id", treino["id"]).execute()
    
    st.session_state.treino_selecionado = None
    st.session_state.descanso_ate = None
    st.success("✅ Treino finalizado!")
    time.sleep(1)
    st.rerun()

# --- APLICAÇÃO ---

# TELA DE LOGIN
if not st.session_state.user:
    st.markdown("<h1 style='text-align: center;'>🏋️ Treino em Foco</h1>", unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••")
        # Botão de login estilizado
        submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            with st.spinner("Autenticando..."):
                sucesso = login(email, senha)
                if sucesso:
                    st.rerun()
                else:
                    st.error("❌ Dados incorretos")

# ÁREA LOGADA
else:
    db = get_db()
    
    # Header Simples (Nome do usuário e Sair)
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        # Pega apenas a parte antes do @ para o nome
        display_name = st.session_state.user.email.split('@')[0]
        st.markdown(f"<h3>Olá, {display_name}</h3>", unsafe_allow_html=True)
    with col_logout:
        if st.button("Sair", use_container_width=True):
            logout()

    # Navegação Abas
    aba = st.radio("", ["Treinos", "Histórico"], horizontal=True, label_visibility="collapsed")

    # ABA: HISTÓRICO
    if aba == "Histórico":
        st.markdown("<h3>Histórico</h3>", unsafe_allow_html=True)
        res = db.table("workout_history")\
            .select("*")\
            .eq("user_id", st.session_state.user.id)\
            .order("data", desc=True)\
            .execute()

        if res.data:
            for h in res.data:
                data_formatada = h['data'][:10] # Apenas a data
                st.markdown(f"""
                <div class="card">
                    <div style="font-weight:bold; font-size:1.1rem;">{h['nome']}</div>
                    <div style="color:#8e8e93; font-size:0.9rem;">📅 {data_formatada}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum treino finalizado.")

    # ABA: TREINOS
    else:
        
        # LISTAGEM
        if not st.session_state.treino_selecionado:
            st.markdown("<h3>Meus Treinos</h3>", unsafe_allow_html=True)

            # Criar Novo
            with st.form("novo_treino", clear_on_submit=True):
                col_novo, col_btn = st.columns([3, 1])
                with col_novo:
                    novo_nome = st.text_input("Nome do treino", label_visibility="collapsed", placeholder="Ex: Peito")
                with col_btn:
                    submitted = st.form_submit_button("➕")
                    if submitted and novo_nome:
                        criar_treino(novo_nome)
                        st.rerun()

            # Lista
            res = db.table("workouts")\
                .select("*")\
                .eq("user_id", st.session_state.user.id)\
                .order("nome")\
                .execute()

            for t in res.data or []:
                is_editing = st.session_state.editando_treino_id == t['id']
                
                # Container do Card
                st.markdown(f"""<div class="card" style="display:flex; align-items:center; justify-content:space-between;">""", unsafe_allow_html=True)
                
                if not is_editing:
                    # C1: Nome do Treino (Botão invisível que age como link)
                    # C2: Editar
                    # C3: Deletar
                    c1, c2, c3 = st.columns([3, 1, 1])
                    
                    # Botão principal para entrar
                    if c1.button(t["nome"], key=f"sel_{t['id']}", use_container_width=True):
                        st.session_state.treino_selecionado = t
                        st.rerun()
                    
                    if c2.button("✏️", key=f"btn_edit_{t['id']}", help="Editar"):
                        st.session_state.editando_treino_id = t['id']
                        st.rerun()

                    if c3.button("🗑️", key=f"del_{t['id']}", help="Deletar"):
                        deletar_treino(t["id"])
                        st.rerun()
                else:
                    # Modo Edição
                    with st.form(key=f"form_edit_{t['id']}"):
                        novo_nome_edit = st.text_input("Novo nome", value=t["nome"], label_visibility="collapsed")
                        col_salvar, col_cancelar = st.columns(2)
                        if col_salvar.form_submit_button("Salvar"):
                            editar_nome_treino(t['id'], novo_nome_edit)
                            st.session_state.editando_treino_id = None
                            st.rerun()
                        if col_cancelar.form_submit_button("Cancelar"):
                            st.session_state.editando_treino_id = None
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

        # DETALHES DO TREINO (Dentro do treino)
        else:
            treino = st.session_state.treino_selecionado
            
            # Topo: Voltar e Título
            col_voltar, col_titulo = st.columns([1, 5])
            with col_voltar:
                if st.button("⬅️"):
                    st.session_state.treino_selecionado = None
                    st.rerun()
            with col_titulo:
                st.markdown(f"<h2>{treino['nome']}</h2>", unsafe_allow_html=True)
            
            modo_edicao = st.toggle("✏️ Editar Lista", label_visibility="visible")

            # TIMER (Estilo Widget)
            st.markdown("<h3>⏱️ Cronômetro</h3>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            
            # Botões de Tempo
            if c1.button("30s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 30
                st.session_state.descanso_total = 30
            if c2.button("60s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 60
                st.session_state.descanso_total = 60
            if c3.button("90s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 90
                st.session_state.descanso_total = 90

            # Lógica do Timer
            if st.session_state.descanso_ate:
                restante = int(st.session_state.descanso_ate - time.time())
                total = st.session_state.descanso_total
                
                if restante > 0:
                    progresso = 1 - (restante / total)
                    st.progress(progresso)
                    st.warning(f"⏳ {restante} segundos restantes")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success("🔥 Descanso finalizado!")
                    st.session_state.descanso_ate = None
                    st.session_state.descanso_total = None
                    time.sleep(2)
                    st.rerun()

            # INPUT DE EXERCÍCIO
            if modo_edicao:
                with st.form("add_ex", clear_on_submit=True):
                    ex_nome = st.text_input("Adicionar exercício", label_visibility="collapsed", placeholder="Ex: Supino")
                    if st.form_submit_button("Adicionar", use_container_width=True):
                        if ex_nome:
                            db.table("exercises").insert({
                                "workout_id": treino["id"],
                                "nome": ex_nome,
                                "done": False
                            }).execute()
                            st.rerun()

            # LISTA DE EXERCÍCIOS
            st.markdown("<h3>Exercícios</h3>", unsafe_allow_html=True)

            res = db.table("exercises")\
                .select("*")\
                .eq("workout_id", treino["id"])\
                .order("id")\
                .execute()

            if not res.data:
                st.info("Lista vazia.")

            for ex in res.data or []:
                done = ex["done"]
                css_class = "card-done" if done else "card"
                
                # Layout da linha do exercício
                col_check, col_text, col_del = st.columns([1, 4, 1])
                
                key = f"chk_{ex['id']}"
                if key not in st.session_state:
                    st.session_state[key] = done

                # Checkbox
                checked = col_check.checkbox("", key=key, value=done, label_visibility="collapsed")
                
                if checked != done:
                    atualizar_exercicio(ex["id"], checked)
                    st.rerun()

                # Texto
                col_text.markdown(f"<div style='padding-top:12px; font-weight:500;'>{ex['nome']}</div>", unsafe_allow_html=True)
                
                # Delete
                if modo_edicao:
                    if col_del.button("🗑️", key=f"ex_del_{ex['id']}"):
                        db.table("exercises").delete().eq("id", ex["id"]).execute()
                        st.rerun()
                else:
                    col_del.write("")

            # BOTÃO FINALIZAR GRANDE
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("✅ FINALIZAR TREINO", use_container_width=True, type="primary"):
                finalizar_treino(treino)