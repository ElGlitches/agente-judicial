import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def check_authentication():
    """
    Maneja el flujo de autenticación completo.
    Retorna el objeto 'authenticator' para usar el botón de logout.
    Detiene la app (st.stop()) si el login falla.
    """
    try:
        # Cargar configuración desde secrets
        auth_config = st.secrets["credentials"]
        cookie_config = st.secrets["cookie"]
        

        # Helper para convertir recursivamente st.secrets (AttrDict) a dict normal
        def to_plain_dict(secrets_obj):
            if isinstance(secrets_obj, dict) or str(type(secrets_obj)).endswith("AttrDict'>"):
                return {k: to_plain_dict(v) for k, v in secrets_obj.items()}
            return secrets_obj

        # Transformar a formato esperado (Mutable)
        credentials = to_plain_dict(st.secrets["credentials"])

        authenticator = stauth.Authenticate(
            credentials,
            cookie_config['name'],
            cookie_config['key'],
            cookie_config['expiry_days']
        )
        
        # Login Widget
        authenticator.login()
        
        if st.session_state["authentication_status"] is False:
            st.error("Usuario o contraseña incorrectos")
            st.stop()
        elif st.session_state["authentication_status"] is None:
            st.warning("Por favor, inicia sesión para continuar")
            st.stop()
            
        return authenticator
        
    except Exception as e:
        st.error(f"Error en sistema de autenticación: {e}")
        st.stop()
