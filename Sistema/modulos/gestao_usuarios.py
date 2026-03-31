import streamlit as st
import bcrypt
from modulos.conexao import conectar

SENHA_PADRAO = "cd@1200"

# ==========================
# CARREGAR USUÁRIOS
# ==========================
@st.cache_data(ttl=60)
def carregar_usuarios():
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nome, usuario, nivel_acesso, ativo, criado_em
            FROM colaboradores
            ORDER BY nome
        """)
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        return []

# ==========================
# CRIAR USUÁRIO
# ==========================
def criar_usuario(nome, usuario, nivel):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM colaboradores WHERE usuario=%s", (usuario,))
        if cursor.fetchone():
            return "existe"

        senha_hash = bcrypt.hashpw(SENHA_PADRAO.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO colaboradores
            (nome, usuario, senha_hash, nivel_acesso, primeiro_acesso, ativo)
            VALUES (%s,%s,%s,%s,TRUE,TRUE)
        """, (nome, usuario, senha_hash, nivel))

        conn.commit()
        cursor.close()
        conn.close()
        return "ok"
    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")
        return "erro"

# ==========================
# RESETAR SENHA
# ==========================
def resetar_senha(usuario):
    try:
        conn = conectar()
        cursor = conn.cursor()
        senha_hash = bcrypt.hashpw(SENHA_PADRAO.encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            UPDATE colaboradores
            SET senha_hash=%s, primeiro_acesso=TRUE
            WHERE usuario=%s
        """, (senha_hash, usuario))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao resetar senha: {e}")

# ==========================
# ALTERAR STATUS
# ==========================
def alterar_status(usuario, status):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE colaboradores
            SET ativo=%s
            WHERE usuario=%s
        """, (status, usuario))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao alterar status: {e}")

# ==========================
# RENDER
# ==========================
def render():

    st.title("👥 Gestão de Usuários")

    # 🔒 Proteção de acesso
    if st.session_state.get("nivel") != "admin":
        st.error("Acesso permitido apenas para administradores")
        return

    abas = st.tabs(["👤 Criar Usuário", "🔄 Reset / Ativar / Desativar", "📜 Logs"])

    # ==========================
    # ABA 1: CRIAR USUÁRIO
    # ==========================
    with abas[0]:
        st.subheader("Criar novo usuário")
        nome = st.text_input("Nome")
        usuario = st.text_input("Usuário")
        nivel = st.selectbox("Nível de acesso", ["usuario", "admin"])

        if st.button("Criar usuário"):
            resultado = criar_usuario(nome, usuario, nivel)
            if resultado == "ok":
                st.success(f"Usuário '{usuario}' criado com sucesso! (Senha padrão: {SENHA_PADRAO})")
                st.cache_data.clear()
                st.experimental_rerun()
            elif resultado == "existe":
                st.error("Usuário já existe")
            else:
                st.error("Erro ao criar usuário")

    # ==========================
    # ABA 2: RESET / ATIVAR / DESATIVAR
    # ==========================
    with abas[1]:
        usuarios = carregar_usuarios()
        st.subheader("Gerenciar usuários existentes")

        if not usuarios:
            st.info("Nenhum usuário encontrado")
        else:
            for u in usuarios:
                col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,1,1,1])
                col1.write(u["nome"])
                col2.write(u["usuario"])
                col3.write(u["nivel_acesso"])
                col4.write("✅" if u["ativo"] else "❌")

                if col5.button("Resetar", key=f"reset_{u['usuario']}"):
                    resetar_senha(u["usuario"])
                    st.cache_data.clear()
                    st.success(f"Senha resetada para {u['usuario']}")
                    st.experimental_rerun()

                if u["ativo"]:
                    if col6.button("Desativar", key=f"des_{u['usuario']}"):
                        alterar_status(u["usuario"], False)
                        st.cache_data.clear()
                        st.experimental_rerun()
                else:
                    if col6.button("Ativar", key=f"ativ_{u['usuario']}"):
                        alterar_status(u["usuario"], True)
                        st.cache_data.clear()
                        st.experimental_rerun()

    # ==========================
    # ABA 3: LOGS
    # ==========================
    with abas[2]:
        st.subheader("📜 Logs de usuário")
        st.info("A aba de logs está pronta, você pode implementar a leitura de logs aqui.")
