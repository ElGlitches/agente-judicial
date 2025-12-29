import streamlit as st
from usage_logic import verify_login

class CustomAuthenticator:
    def logout(self, label="Logout", key="logout_btn", location="sidebar"):
        if location == "sidebar":
            if st.sidebar.button(label, key=key):
                st.session_state["authentication_status"] = None
                st.session_state["name"] = None
                st.session_state["username"] = None
                st.rerun()
        else:
             if st.button(label, key=key):
                st.session_state["authentication_status"] = None
                st.session_state["name"] = None
                st.session_state["username"] = None
                st.rerun()

def check_authentication():
    """
    Nuevo flujo de Auth usando SQLite (usage_logic.py).
    Reemplaza a streamlit-authenticator para no depender de config.yaml.
    """
    # Inicializar estado
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    
    # 1. Si ya está logueado, retornar dummy object con metodo logout
    if st.session_state["authentication_status"]:
        return CustomAuthenticator()
    
    # 2. Si no está logueado, mostrar Formulario
    st.markdown("## 🔐 Iniciar Sesión")
    
    # Formulario Login
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            is_valid, name = verify_login(username, password)
            if is_valid:
                st.session_state["authentication_status"] = True
                st.session_state["name"] = name
                st.session_state["username"] = username
                st.rerun()
            else:
                st.session_state["authentication_status"] = False
                st.error("❌ Usuario o contraseña incorrectos")

    if st.session_state["authentication_status"] is False:
        st.stop()
        
    # Detener app si no está logueado
    st.info("Credenciales por defecto: admin / admin123")
    st.stop()
