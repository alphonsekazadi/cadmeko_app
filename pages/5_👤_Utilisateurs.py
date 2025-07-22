# Page utilisateurs 
import streamlit as st
import bcrypt
import pathlib
from database import get_connection
from security import login_user, require_role

# ------------------------------------------------------------------
# 1. Authentification & autorisation
# ------------------------------------------------------------------
login_user()
require_role(["Administrateur"])           # ← ACCÈS RÉSERVÉ
st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

st.title("👤 Gestion des utilisateurs")

# ------------------------------------------------------------------
# 2. Fonctions BDD réutilisables
# ------------------------------------------------------------------
def fetch_users():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT id_user, login, role FROM utilisateur ORDER BY login")
    rows = cur.fetchall()
    conn.close()
    return rows

def create_user(login, pwd, role):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO utilisateur (login, pwd_hash, role) VALUES (%s,%s,%s)",
        (login, bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode(), role)
    )
    conn.commit(); conn.close()

def update_role(user_id, role):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE utilisateur SET role=%s WHERE id_user=%s", (role, user_id))
    conn.commit(); conn.close()

def reset_pwd(user_id, new_pwd):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "UPDATE utilisateur SET pwd_hash=%s WHERE id_user=%s",
        (bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode(), user_id)
    )
    conn.commit(); conn.close()

def delete_user(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM utilisateur WHERE id_user=%s", (user_id,))
    conn.commit(); conn.close()

# ------------------------------------------------------------------
# 3. Tableau + actions
# ------------------------------------------------------------------
users = fetch_users()
st.subheader("Liste des utilisateurs")
st.dataframe(users, use_container_width=True)

# ­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­
# 4. Ajout / modification
# ­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­
st.divider()
with st.expander("➕ Ajouter un utilisateur"):
    with st.form("add_user", clear_on_submit=True, border=True):
        login   = st.text_input("Login", max_chars=50)
        role    = st.selectbox("Rôle", ["Administrateur", "Gestionnaire", "Pharmacien", "Agent de saisie"])
        pwd1    = st.text_input("Mot de passe", type="password")
        pwd2    = st.text_input("Confirmer", type="password")
        if st.form_submit_button("💾 Créer"):
            if pwd1 != pwd2:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                try:
                    create_user(login, pwd1, role)
                    st.success("Utilisateur créé ✅")
                except Exception as e:
                    st.error(f"Erreur : {e}")
                st.rerun()

st.divider()
st.subheader("🛠️ Actions rapides")

# Sélection d’un utilisateur
user_options = {f"{u['login']} ({u['role']})": u["id_user"] for u in users}
if user_options:
    selected = st.selectbox("Choisir un utilisateur", list(user_options.keys()))
    uid      = user_options[selected]

    col1, col2, col3, col4 = st.columns(4)

    # ---- Modifier rôle ----
    with col1:
        new_role = st.selectbox("Nouveau rôle", ["Administrateur", "Gestionnaire", "Pharmacien", "Agent de saisie"],
                                key="role_select")
        if st.button("🔄 Modifier rôle"):
            update_role(uid, new_role)
            st.success("Rôle mis à jour ✅")
            st.rerun()

    # ---- Réinitialiser mot de passe ----
    with col2:
        if st.button("🔑 Réinitialiser mot de passe"):
            new_pwd = st.text_input("Nouveau mot de passe :", type="password", key="reset_pwd")
            if new_pwd:
                reset_pwd(uid, new_pwd)
                st.success("Mot de passe réinitialisé ✅")

    # ---- Supprimer ----
    with col3:
        if st.button("🗑️ Supprimer", help="Action irréversible"):
            delete_user(uid)
            st.warning("Utilisateur supprimé.")
            st.rerun()

else:
    st.info("Aucun utilisateur dans la base.")
