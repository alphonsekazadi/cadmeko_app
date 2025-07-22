# Page commandes 
import streamlit as st
from datetime import datetime
from database import get_connection
import pathlib
from security import login_user, require_role

# -------------------------------------------------
# 1. Authentification / rôles
# -------------------------------------------------
login_user()
require_role(["Administrateur", "Gestionnaire", "Pharmacien", "Agent de saisie"])
user_role = st.session_state["user"]["role"]
st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

st.title("📑 Gestion des commandes")

# -------------------------------------------------
# 2. Helpers BDD
# -------------------------------------------------
def get_clients():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id_client, nom_client FROM client ORDER BY nom_client")
    rows = cur.fetchall(); conn.close()
    return rows

def get_produits():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id_produit, p.nom_produit, COALESCE(s.quantite,0) AS quantite
        FROM produit p LEFT JOIN stock s ON s.id_produit=p.id_produit
        ORDER BY p.nom_produit
    """)
    rows = cur.fetchall(); conn.close()
    return rows

def gen_code_commande():
    """CMD-20250709-001"""
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM commande WHERE date_commande=CURRENT_DATE")
    n = cur.fetchone()[0] + 1
    conn.close()
    return f"CMD-{datetime.now():%Y%m%d}-{n:03d}"

# -------------------------------------------------
# 3. Création d'une nouvelle commande (étape 1)
# -------------------------------------------------
if "commande_en_cours" not in st.session_state:
    st.subheader("🆕 Créer une commande")

    clients = get_clients()
    if not clients:
        st.warning("Aucun client enregistré.")
        st.stop()

    client_map = {c["nom_client"]: c["id_client"] for c in clients}
    cli_nom = st.selectbox("Client", list(client_map.keys()))
    if st.button("Créer commande"):
        code = gen_code_commande()
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO commande (code_commande, date_commande, statut, id_client)
            VALUES (%s,CURDATE(),'En attente',%s)
        """, (code, client_map[cli_nom]))
        conn.commit(); last_id = cur.lastrowid; conn.close()
        st.session_state["commande_en_cours"] = last_id
        st.session_state["commande_code"] = code
        st.success(f"Commande {code} créée ✅")
        st.rerun()

# -------------------------------------------------
# 4. Ajout de produits (étape 2)
# -------------------------------------------------
if "commande_en_cours" in st.session_state:
    cmd_id = st.session_state["commande_en_cours"]
    st.subheader(f"🛒 Commande {st.session_state['commande_code']} – Ajout d’articles")

    produits = get_produits()
    prod_map = {f"{p['nom_produit']}  |  Stock : {p['quantite']}": (p["id_produit"], p["quantite"])
                for p in produits}
    prod_label = st.selectbox("Produit", list(prod_map.keys()))
    qty = st.number_input("Quantité demandée", min_value=1, step=1)
    col_add, col_fin = st.columns([1,1])

    # ---- Bouton "Ajouter ligne" ----
    if col_add.button("➕ Ajouter ligne"):
        id_prod, stock_dispo = prod_map[prod_label]
        if qty > stock_dispo:
            st.error("Stock insuffisant !")
        else:
            conn = get_connection(); cur = conn.cursor()
            # 1) Insérer dans commande_detail
            cur.execute("""
                INSERT INTO commande_detail (id_commande,id_produit,quantite_dmd,quantite_livr)
                VALUES (%s,%s,%s,0)
            """, (cmd_id, id_prod, qty))
            # 2) Réserver le stock (décrément immédiat)
            cur.execute("""
                UPDATE stock SET quantite = quantite - %s
                WHERE id_produit = %s
            """, (qty, id_prod))
            conn.commit(); conn.close()
            st.success("Ligne ajoutée ✅")
            st.rerun()

    # -------------------------------------------------
    # 5. Affichage des lignes déjà ajoutées
    # -------------------------------------------------
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.id_detail, p.nom_produit, d.quantite_dmd
        FROM commande_detail d
        JOIN produit p ON p.id_produit=d.id_produit
        WHERE d.id_commande=%s
    """, (cmd_id,))
    lignes = cur.fetchall(); conn.close()

    if lignes:
        st.table(lignes)

    # ---- Bouton "Finaliser commande" ----
    statut_final = "En attente" if user_role == "Agent de saisie" else st.selectbox(
        "Statut final", ["En attente", "Livrée", "Annulée"], index=0
    )

    if col_fin.button("✅ Finaliser"):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("UPDATE commande SET statut=%s WHERE id_commande=%s",
                    (statut_final, cmd_id))
        conn.commit(); conn.close()
        st.success(f"Commande finalisée ({statut_final})")
        # Nettoyer la session
        del st.session_state["commande_en_cours"]
        del st.session_state["commande_code"]
        st.rerun()

# -------------------------------------------------
# 6. Historique des commandes
# -------------------------------------------------
st.subheader("📜 Historique des commandes")
conn = get_connection(); cur = conn.cursor(dictionary=True)
cur.execute("""
    SELECT c.id_commande, c.code_commande, DATE_FORMAT(c.date_commande,'%%d/%%m/%%Y') AS date,
           cl.nom_client, c.statut
    FROM commande c
    JOIN client cl ON cl.id_client=c.id_client
    ORDER BY c.date_commande DESC, c.id_commande DESC
""")
hist = cur.fetchall(); conn.close()
st.dataframe(hist, use_container_width=True)
