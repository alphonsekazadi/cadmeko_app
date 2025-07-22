# Authentification + roles 
import streamlit as st
import bcrypt
from database import get_connection

def login_user():
    if "user" in st.session_state:
        return st.session_state["user"]

    with st.form("login"):
        st.subheader("🔐 Connexion")
        login = st.text_input("Nom d'utilisateur")
        pwd = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM utilisateur WHERE login=%s", (login,))
            user = cursor.fetchone()
            conn.close()

            if user and bcrypt.checkpw(pwd.encode(), user["pwd_hash"].encode()):
                st.session_state["user"] = {"id": user["id_user"], "login": user["login"], "role": user["role"]}
                st.success("Connexion réussie ✅")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

def require_role(roles):
    user = st.session_state.get("user")
    if not user or user["role"] not in roles:
        st.error("⛔ Accès non autorisé")
        st.stop()
