import streamlit as st
import pathlib
from security import login_user
from database import get_connection

# Config Streamlit
st.set_page_config(page_title="CADMEKO - Gestion", layout="wide")
st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

# Authentification
login_user()

# Vérifie la session après connexion
if "user" in st.session_state:
    user = st.session_state["user"]

    st.markdown(f"""
        <div style='padding:1rem; background-color:#f3fdf6; border-left:6px solid #27ae60'>
            <h2 style='color:#2e7d32'>Bienvenue, <em>{user['login']}</em> 👋</h2>
            <p style='margin:0'>Vous êtes connecté en tant que <strong>{user['role']}</strong>.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🔎 Aperçu rapide du système")

    # Récupérer des compteurs
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM produit");      produits = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stock");        stock   = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM client");       clients = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM fournisseur");  fournisseurs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM commande");     commandes = cur.fetchone()[0]
    conn.close()

    # Section 1 : Résumés (grilles horizontales)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='card green'><h3>🧾 Produits</h3><p>{}</p></div>".format(produits), unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card orange'><h3>📦 Stock</h3><p>{}</p></div>".format(stock), unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card green'><h3>🏥 Clients</h3><p>{}</p></div>".format(clients), unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='card orange'><h3>🚚 Commandes</h3><p>{}</p></div>".format(commandes), unsafe_allow_html=True)

    st.markdown("---")

    # Section 2 : Lien rapide ou tableau miniature
    st.subheader("📋 Dernières commandes")
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT code_commande, DATE_FORMAT(date_commande, '%%d/%%m/%%Y') AS date, statut
        FROM commande
        ORDER BY date_commande DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    conn.close()

    if rows:
        st.table(rows)
    else:
        st.info("Aucune commande enregistrée.")
else:
    st.info("🔐 Veuillez vous connecter pour accéder à l’application.")
