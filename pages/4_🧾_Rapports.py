import streamlit as st
import pandas as pd
from database import get_connection
from security import login_user, require_role
from datetime import date
import pathlib

# Auth + Style
login_user()
require_role(["Administrateur", "Gestionnaire", "Pharmacien"])
st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

st.title("🧾 Rapports et Statistiques")

# Tabs
tab1, tab2 = st.tabs(["📦 Stock Produits", "📑 Commandes Clients"])

# ----------------------------------------------------------
# 📦 RAPPORT STOCK
# ----------------------------------------------------------
with tab1:
    st.subheader("📦 État général du stock")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.nom_produit, p.forme, p.dosage,
               COALESCE(s.quantite, 0) AS quantite
        FROM produit p
        LEFT JOIN stock s ON s.id_produit = p.id_produit
        ORDER BY quantite ASC
    """)
    stock_data = pd.DataFrame(cur.fetchall())
    conn.close()

    if not stock_data.empty:
        st.data_editor(stock_data, use_container_width=True, disabled=True, hide_index=True, height=350)

        st.markdown("#### ⚠️ Produits avec stock faible")
        seuil = st.slider("Seuil d’alerte", min_value=0, max_value=50, value=10)
        faibles = stock_data[stock_data["quantite"] <= seuil]

        st.dataframe(faibles, use_container_width=True)
        st.markdown("#### 📊 Graphique des quantités par produit")
        st.bar_chart(stock_data.set_index("nom_produit")["quantite"])

        csv = stock_data.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger (CSV)", data=csv, file_name="rapport_stock.csv")
    else:
        st.info("Aucune donnée de stock disponible.")

# ----------------------------------------------------------
# 📑 RAPPORT COMMANDES
# ----------------------------------------------------------
with tab2:
    st.subheader("📑 Historique des commandes clients")

    # Filtres
    col1, col2 = st.columns(2)
    date_debut = col1.date_input("📅 Date début", value=date(2024, 1, 1))
    date_fin   = col2.date_input("📅 Date fin", value=date.today())

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.code_commande, c.date_commande,
               cl.nom_client, p.nom_produit, d.quantite_dmd
        FROM commande c
        JOIN client cl ON cl.id_client = c.id_client
        JOIN commande_detail d ON d.id_commande = c.id_commande
        JOIN produit p ON p.id_produit = d.id_produit
        WHERE c.date_commande BETWEEN %s AND %s
        ORDER BY c.date_commande DESC
    """, (date_debut, date_fin))
    data = pd.DataFrame(cur.fetchall())
    conn.close()

    if not data.empty:
        data["date_commande"] = pd.to_datetime(data["date_commande"]).dt.strftime("%d/%m/%Y")
        data.rename(columns={
            "code_commande": "Code",
            "date_commande": "Date",
            "nom_client": "Client",
            "nom_produit": "Produit",
            "quantite_dmd": "Quantité demandée"
        }, inplace=True)

        st.data_editor(data, use_container_width=True, disabled=True, hide_index=True, height=350)

        st.markdown("#### 📊 Produits les plus demandés")
        top_produits = data.groupby("Produit")["Quantité demandée"].sum().sort_values(ascending=False)
        st.bar_chart(top_produits)

        csv_cmd = data.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger (CSV)", data=csv_cmd, file_name="rapport_commandes.csv")
    else:
        st.info("Aucune commande trouvée pour cette période.")
