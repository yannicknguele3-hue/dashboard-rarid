from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Dashboard RARID Journal", page_icon="📊", layout="wide"
)

NOM_FICHIER = "Tableau_de_Bord_Campagnes_Appel_Contributions_v3 ok.xlsm"


# --- Fonction de chargement (SANS CACHE pour lecture fraîche à chaque appel) ---
def load_data():
  df = pd.read_excel(
      NOM_FICHIER,
      sheet_name="Campagne de Yannick",
      header=6,
      engine="openpyxl",
  )
  df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
  if "Nom & Prénom" in df.columns:
    df = df.dropna(subset=["Nom & Prénom"])
  return df


# --- Horodatage de la dernière lecture ---
if "last_refresh" not in st.session_state:
  st.session_state.last_refresh = datetime.now()

# Affichage de l'heure + bouton de rafraîchissement manuel
col_refresh, col_info = st.columns([1, 5])
with col_refresh:
  if st.button("🔄 Forcer le rechargement maintenant"):
    st.session_state.last_refresh = datetime.now()
    st.rerun()  # Recharge immédiatement la page

with col_info:
  st.caption(
      f"Dernière mise à jour :"
      f" {st.session_state.last_refresh.strftime('%H:%M:%S')}"
  )

try:
  df = load_data()

  st.title("📊 RARID Journal - Suivi des Contributions")

  # --- BARRE LATÉRALE (FILTRES) ---
  st.sidebar.header("🎛️ Filtres")

  if "Priorité" in df.columns:
    priorite_opt = ["Toutes"] + list(df["Priorité"].dropna().unique())
    filtre_priorite = st.sidebar.selectbox("Priorité / Relance", priorite_opt)
  else:
    filtre_priorite = "Toutes"

  recherche = st.sidebar.text_input("🔍 Rechercher un auteur ou article")

  # Application des filtres
  df_affiche = df.copy()

  if filtre_priorite != "Toutes" and "Priorité" in df_affiche.columns:
    df_affiche = df_affiche[df_affiche["Priorité"] == filtre_priorite]

  if recherche:
    df_affiche = df_affiche[
        df_affiche["Nom & Prénom"]
        .astype(str)
        .str.contains(recherche, case=False, na=False)
        | df_affiche["Nom de l'Article"]
        .astype(str)
        .str.contains(recherche, case=False, na=False)
    ]

  # --- CALCULS DES INDICATEURS ---
  total_contributeurs = len(df_affiche)

  montant_paye = (
      pd.to_numeric(df_affiche.get("Montant Payé", 0), errors="coerce")
      .fillna(0)
      .sum()
  )
  solde_restant = (
      pd.to_numeric(df_affiche.get("Solde Restant", 0), errors="coerce")
      .fillna(0)
      .sum()
  )
  montant_total_du = montant_paye + solde_restant

  # KPIs
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Total Contributeurs", total_contributeurs)
  col2.metric("Montant Total Dû", f"{montant_total_du:,.0f} FCFA".replace(",", " "))
  col3.metric("Montant Encaissé", f"{montant_paye:,.0f} FCFA".replace(",", " "))
  col4.metric("Solde Restant", f"{solde_restant:,.0f} FCFA".replace(",", " "))

  st.divider()

  # --- DIAGRAMME CIRCULAIRE ---
  st.subheader("📈 Répartition par État d'Avancement")
  if "Évolution" in df_affiche.columns and not df_affiche.empty:
    df_chart = df_affiche["Évolution"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(
        df_chart,
        labels=df_chart.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=plt.cm.Pastel1.colors,
    )
    ax.axis("equal")
    st.pyplot(fig)
    plt.close(fig)  # Sécurité pour libérer la mémoire

  st.divider()

  # --- TABLEAU SYNTHÉTIQUE ---
  st.subheader("📋 Vue synthétique des contributions")
  cols_existantes = [
      c
      for c in [
          "Nom & Prénom",
          "Nom de l'Article",
          "Évolution",
          "Solde Restant",
      ]
      if c in df_affiche.columns
  ]
  st.dataframe(df_affiche[cols_existantes], use_container_width=True)

  # Export CSV
  csv = df_affiche[cols_existantes].to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Télécharger le rapport (CSV)",
      data=csv,
      file_name="rapport_contributions_rarid.csv",
      mime="text/csv",
  )

except FileNotFoundError:
  st.error(f"⚠️ Le fichier '{NOM_FICHIER}' est introuvable.")
except Exception as e:
  st.error(f"⚠️ Erreur lors du chargement : {e}")