import streamlit as st
import pandas as pd
import pathlib
from database import get_connection
from security import login_user, require_role
from datetime import date

login_user()
require_role(["Administrateur", "Gestionnaire", "Pharmacien"])

st.markdown(f"<style>{pathlib.Path('assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

st.title("🏷️ Gestion des Produits")

# -----------------------------------------------------
# 🔸 FORMULAIRE D’AJOUT DE PRODUIT
# -----------------------------------------------------
with st.expander("➕ Ajouter un nouveau produit", expanded=True):
    with st.form("form_produit", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        code   = col1.text_input("Code Produit", max_chars=20)
        nom    = col1.text_input("Nom Produit", max_chars=100)
        forme  = col2.text_input("Forme", placeholder="Comprimé, capsule, etc.")
        dosage = col2.text_input("Dosage", placeholder="Ex : 500 mg, 1g")
        date_peremption = col3.date_input("Date de péremption", min_value=date.today())
        prix   = col3.number_input("Prix unitaire (CDF)", step=100.0, min_value=0.0, format="%.2f")

        if st.form_submit_button("💾 Enregistrer le produit"):
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO produit 
                    (code_produit, nom_produit, forme, dosage, date_peremption, prix_unitaire)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (code, nom, forme, dosage, date_peremption, prix))
                conn.commit()
                st.success("✅ Produit enregistré avec succès")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
            finally:
                conn.close()

# -----------------------------------------------------
# 🔍 AFFICHAGE DES PRODUITS
# -----------------------------------------------------
st.divider()
st.subheader("📋 Liste des produits enregistrés")

# Chargement des données
conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM produit ORDER BY id_produit DESC")
rows = cursor.fetchall()
conn.close()

if rows:
    df = pd.DataFrame(rows)
    
    # 👁️ Formatage affichage
    df["prix_unitaire"] = df["prix_unitaire"].apply(lambda x: f"{x:,.0f} CDF".replace(",", " "))
    df["date_peremption"] = pd.to_datetime(df["date_peremption"]).dt.strftime("%d/%m/%Y")

    st.data_editor(df, use_container_width=True, disabled=True, hide_index=True, height=400)

    # -----------------------------------------------------
    # ⬇️ EXPORTS
    # -----------------------------------------------------
    st.markdown("### 📤 Exporter les données")

    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Télécharger en CSV",
            data=csv,
            file_name="produits.csv",
            mime="text/csv",
            use_container_width=True,
            help="Exporter la liste des produits au format CSV"
        )
else:
    st.info("Aucun produit enregistré.")

