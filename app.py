import streamlit as st
from supabase import create_client
import time

# --- CONFIGURAÇÕES ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# --- ESTADO DA SESSÃO ---
for key, default in {
    "user": None,
    "session": None,
    "treino_selecionado": None,
    "descanso_ate": None,
    "descanso_total": None,  # Para a barra de progresso
    "editando_treino_id": None # Para controlar edição de nome
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
    client = create_client(SSUPABASE_URL, SUPABASE_KEY)
    
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
        st.error(f"Erro no login: {e}")
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

    # Salvar no histórico
    db.table("workout_history").insert({
        "user_id": st.session_state.user.id,
        "workout_id": treino["id"],
        "nome": treino["nome"]
    }).execute()

    # Resetar exercícios
    db.table("exercises").update({
        "done": False  # Alterado para False para o próximo treino
    }).eq("workout_id", treino["id"]).execute()

    st.session_state.treino_selecionado = None
    st.session_state.descanso_ate = None
    st.success("✅ Treino finalizado e salvo no histórico!")
    time.sleep(1)
    st.rerun()

# --- ESTILO (CSS) ---
st.set_page_config(page_title="Treino em Foco", layout="centered")

st.markdown("""
<style>
    /* Container Mobile-First */
    .block-container {
        max-width: 500px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Cartões */
    .card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 0.8rem;
        border: 1px solid #f0f0f0;
    }
    .card-done {
        background: #f0fff4;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        border: 1px solid #c6f6d5;
        text-decoration: line-through;
        color: #718096;
    }
    
    /* Botões */
    div.stButton > button:first-child {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Tabela Histórico */
    table {width:100%;border-collapse:collapse;margin-top:1rem;}
    th {text-align: left; color: #718096; font-size: 0.9rem;}
    td {padding: 12px 8px; border-bottom: 1px solid #eee;}
</style>
""", unsafe_allow_html=True)

# --- APLICAÇÃO ---

# TELA DE LOGIN
if not st.session_state.user:
    st.title("🏋️ Treino em Foco")
    st.markdown("<br>", unsafe_allow_html=True) # Espaçamento

    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            with st.spinner("Entrando..."):
                sucesso = login(email, senha)
                if sucesso:
                    st.rerun()
                else:
                    st.error("❌ Email ou senha inválidos")

# ÁREA LOGADA
else:
    db = get_db()
    
    # Header
    col_user, col_logout = st.columns([3, 1])
    with col_user:
        st.markdown(f"👤 **{st.session_state.user.email.split('@')[0]}**")
    with col_logout:
        if st.button("Sair", use_container_width=True):
            logout()

    # Navegação
    aba = st.radio("", ["Treinos", "Histórico"], horizontal=True, label_visibility="collapsed")

    # ABA: HISTÓRICO
    if aba == "Histórico":
        st.subheader("📋 Histórico de Treinos")

        res = db.table("workout_history")\
            .select("*")\
            .eq("user_id", st.session_state.user.id)\
            .order("data", desc=True)\
            .execute()

        if res.data:
            for h in res.data:
                # Formatar data para PT-BR
                data_hora = h['data'][:16].replace('T', ' ')
                st.markdown(f"""
                <div class="card">
                    <strong>{h['nome']}</strong><br/>
                    <small style="color:gray;">📅 {data_hora}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum treino finalizado ainda.")

    # ABA: TREINOS
    else:
        
        # LISTAGEM DE TREINOS
        if not st.session_state.treino_selecionado:
            st.subheader("🏋️ Meus Treinos")

            # Criar novo
            with st.form("novo_treino", clear_on_submit=True):
                col_novo, col_btn = st.columns([3, 1])
                with col_novo:
                    novo_nome = st.text_input("Nome do novo treino", label_visibility="collapsed", placeholder="Ex: Peito e Tríceps")
                with col_btn:
                    submitted = st.form_submit_button("➕")
                    if submitted and novo_nome:
                        criar_treino(novo_nome)
                        st.rerun()

            # Listar existentes
            res = db.table("workouts")\
                .select("*")\
                .eq("user_id", st.session_state.user.id)\
                .order("nome")\
                .execute()

            for t in res.data or []:
                # Verifica se está editando este treino
                is_editing = st.session_state.editando_treino_id == t['id']

                st.markdown(f"""<div class="card">""", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([4, 1, 1])

                # Modo de Exibição Normal
                if not is_editing:
                    if c1.button(t["nome"], key=f"sel_{t['id']}", use_container_width=True):
                        st.session_state.treino_selecionado = t
                        st.rerun()
                    
                    if c2.button("✏️", key=f"btn_edit_{t['id']}", help="Editar nome"):
                        st.session_state.editando_treino_id = t['id']
                        st.rerun()

                    if c3.button("🗑️", key=f"del_{t['id']}", help="Deletar"):
                        deletar_treino(t["id"])
                        st.rerun()
                
                # Modo de Edição
                else:
                    with st.form(key=f"form_edit_{t['id']}"):
                        novo_nome_edit = st.text_input("Novo nome", value=t["nome"], label_visibility="collapsed")
                        col_salvar, col_cancelar = st.columns(2)
                        if col_salvar.form_submit_button("💾"):
                            editar_nome_treino(t['id'], novo_nome_edit)
                            st.session_state.editando_treino_id = None
                            st.rerun()
                        if col_cancelar.form_submit_button("❌"):
                            st.session_state.editando_treino_id = None
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        # DETALHES DO TREINO
        else:
            treino = st.session_state.treino_selecionado
            
            # Cabeçalho do Treino
            col_voltar, col_titulo, col_edit = st.columns([1, 3, 1])
            with col_voltar:
                if st.button("⬅️"):
                    st.session_state.treino_selecionado = None
                    st.rerun()
            with col_titulo:
                st.markdown(f"<h2 style='margin:0;'>{treino['nome']}</h2>", unsafe_allow_html=True)
            with col_edit:
                modo_edicao = st.toggle("✏️", label_visibility="collapsed")

            # TIMER MELHORADO
            st.markdown("---")
            st.markdown("### ⏱️ Descanso")
            
            c1, c2, c3 = st.columns(3)
            if c1.button("30s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 30
                st.session_state.descanso_total = 30
            if c2.button("60s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 60
                st.session_state.descanso_total = 60
            if c3.button("90s", use_container_width=True): 
                st.session_state.descanso_ate = time.time() + 90
                st.session_state.descanso_total = 90

            if st.session_state.descanso_ate:
                restante = int(st.session_state.descanso_ate - time.time())
                total = st.session_state.descanso_total
                
                if restante > 0:
                    # Barra de progresso inversa
                    progresso = 1 - (restante / total)
                    st.progress(progresso)
                    st.warning(f"⏳ Faltam {restante}s")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success("🔥 Descanso finalizado! Bora lá!")
                    st.session_state.descanso_ate = None
                    st.session_state.descanso_total = None
                    time.sleep(1.5)
                    st.rerun()

            st.markdown("---")

            # ADICIONAR EXERCÍCIO
            if modo_edicao:
                with st.form("add_ex"):
                    novo_ex = st.text_input("Novo exercício", label_visibility="collapsed", placeholder="Ex: Supino reto")
                    if st.form_submit_button("Adicionar Exercício"):
                        if novo_ex:
                            db.table("exercises").insert({
                                "workout_id": treino["id"],
                                "nome": novo_ex,
                                "done": False
                            }).execute()
                            st.rerun()

            # LISTA DE EXERCÍCIOS
            st.markdown("### 💪 Lista de Exercícios")

            res = db.table("exercises")\
                .select("*")\
                .eq("workout_id", treino["id"])\
                .order("id")\
                .execute()

            if not res.data:
                st.info("Nenhum exercício cadastrado. Ative o modo edição para adicionar.")

            for ex in res.data or []:
                done = ex["done"]
                css_class = "card-done" if done else "card"
                nome_exibicao = ex["nome"]

                # Layout do item
                col_chk, col_txt, col_del = st.columns([1, 4, 1])

                # Checkbox customizado via st.checkbox (melhora acessibilidade)
                # Usamos a chave do session_state para controlar o estado visual
                key = f"chk_{ex['id']}"
                if key not in st.session_state:
                    st.session_state[key] = done

                checked = st.checkbox("", key=key, value=done, label_visibility="collapsed")
                
                # Sync com banco se houver mudança
                if checked != done:
                    atualizar_exercicio(ex["id"], checked)
                    st.rerun()

                # Texto e Delete
                col_txt.markdown(f"<div style='padding-top:10px; font-weight:500;'>{nome_exibicao}</div>", unsafe_allow_html=True)
                
                if modo_edicao:
                    if col_del.button("🗑️", key=f"ex_del_{ex['id']}", help="Remover exercício"):
                        db.table("exercises").delete().eq("id", ex["id"]).execute()
                        st.rerun()
                else:
                    col_del.write("") # Espaçador

            # BOTÃO FINALIZAR
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ FINALIZAR TREINO", use_container_width=True, type="primary"):
                finalizar_treino(treino)