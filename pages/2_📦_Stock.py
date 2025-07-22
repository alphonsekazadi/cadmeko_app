import streamlit as st
from datetime import datetime
import pandas as pd
import pathlib
from database import get_connection
from security import login_user, require_role

# Authentification et styles
login_user()
require_role(["Administrateur", "Gestionnaire", "Pharmacien"])
st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

st.title("📦 Gestion du Stock")

# -----------------------------------------------
# 🔍 1. Tableau interactif des stocks
# -----------------------------------------------
@st.cache_data(ttl=60)
def fetch_stock():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.code_produit, p.nom_produit,
               COALESCE(s.quantite,0) AS quantite,
               s.maj AS maj
        FROM produit p
        LEFT JOIN stock s ON s.id_produit = p.id_produit
        ORDER BY p.nom_produit
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

st.subheader("📊 État actuel du stock")

stock_rows = fetch_stock()

if stock_rows:
    df = pd.DataFrame(stock_rows)
    df["maj"] = pd.to_datetime(df["maj"]).dt.strftime("%d/%m/%Y %H:%M")
    df.rename(columns={
        "code_produit": "Code",
        "nom_produit": "Produit",
        "quantite": "Quantité",
        "maj": "Dernière mise à jour"
    }, inplace=True)

    st.data_editor(df, use_container_width=True, disabled=True, hide_index=True, height=400)
else:
    st.info("Aucun stock trouvé.")

st.divider()

# -----------------------------------------------
# 📥 2. Formulaire d'enregistrement d’un mouvement
# -----------------------------------------------
st.subheader("📥 Enregistrer un mouvement de stock")

# Liste des produits disponibles
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT id_produit, nom_produit, code_produit FROM produit ORDER BY nom_produit")
produits = cur.fetchall()
conn.close()

prod_dict = {f"{p['nom_produit']} ({p['code_produit']})": p["id_produit"] for p in produits}

with st.form("mvt_form", clear_on_submit=True, border=True):
    col1, col2 = st.columns(2)
    produit_label = col1.selectbox("Produit concerné", list(prod_dict.keys()))
    mvt_type = col2.selectbox("Type de mouvement", ["Entrée", "Sortie", "Ajustement"])
    qty = col1.number_input("Quantité", min_value=1, step=1)
    desc = col2.text_input("Description (optionnel)", placeholder="Ex : réception fournisseur, perte, etc.")

    submitted = st.form_submit_button("💾 Valider le mouvement")

    if submitted:
        id_prod = prod_dict[produit_label]
        qty_signed = qty if mvt_type == "Entrée" else -qty if mvt_type == "Sortie" else qty

        conn = get_connection()
        cur = conn.cursor()
        try:
            # 1. Journal du mouvement
            cur.execute("""
                INSERT INTO mouvement_stock (id_produit, date_mvt, type_mvt, quantite, description)
                VALUES (%s,%s,%s,%s,%s)
            """, (id_prod, datetime.now(), mvt_type, qty_signed, desc))

            # 2. Mise à jour du stock
            cur.execute("SELECT quantite FROM stock WHERE id_produit=%s", (id_prod,))
            row = cur.fetchone()

            if row:
                nouvelle_qte = row[0] + qty_signed
                if nouvelle_qte < 0:
                    st.error("❌ Quantité insuffisante pour cette sortie.")
                    conn.rollback()
                else:
                    cur.execute(
                        "UPDATE stock SET quantite=%s, maj=%s WHERE id_produit=%s",
                        (nouvelle_qte, datetime.now(), id_prod)
                    )
                    conn.commit()
                    st.success("✅ Mouvement enregistré avec succès.")
            else:
                if qty_signed < 0:
                    st.error("❌ Stock inexistant pour ce produit.")
                    conn.rollback()
                else:
                    cur.execute(
                        "INSERT INTO stock (id_produit, quantite, maj) VALUES (%s, %s, %s)",
                        (id_prod, qty_signed, datetime.now())
                    )
                    conn.commit()
                    st.success("✅ Stock créé et mouvement enregistré.")
        except Exception as e:
            conn.rollback()
            st.error(f"Erreur : {e}")
        finally:
            conn.close()
            st.rerun()
