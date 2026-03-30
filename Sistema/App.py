# app.py
import streamlit as st
from modulos import login, inicio  # por enquanto só temos login e inicio

def main():
    st.set_page_config(page_title="Sistema CD", layout="wide")
    
    # Login
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

    if not st.session_state.usuario_logado:
        usuario = login.tela_login()  # função do login.py
        if usuario:
            st.session_state.usuario_logado = usuario

    # Usuário logado -> tela inicial
    if st.session_state.usuario_logado:
        inicio.tela_inicio()

if __name__ == "__main__":
    main()
