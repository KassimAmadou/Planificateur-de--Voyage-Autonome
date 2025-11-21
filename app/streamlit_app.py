import streamlit as st
import sys
import os
from datetime import datetime

# --- 1. CONFIGURATION DU CHEMIN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# --- 2. IMPORTS DU PROJET ---
from agents.travel_agent import TravelAgent
from exports.pdf_export import generate_trip_pdf

# --- 3. APPLICATION STREAMLIT ---
def main():
    st.set_page_config(page_title="Planificateur de Voyage AI", page_icon="✈️", layout="wide")

    st.title(" Planificateur de Voyage Autonome")
    st.markdown("Décrivez votre voyage idéal, et notre agent s'occupe de tout !")

    user_input = st.text_area(
        "Votre projet de voyage :", 
        height=150,
        placeholder="Ex: Je veux partir à Bali du 15 au 22 mars avec 2 adultes et 1 enfant, budget moyen, on aime bouger..."
    )

    # Bouton d'action
    if st.button("Générer mon itinéraire"):
        if user_input:
            agent = TravelAgent()
            
            with st.spinner("L'agent analyse et planifie votre demande (ReAct & Self-Correction en cours)..."):
                result = agent.process_request(user_input)

            # --- CORRECTION DE LA KEYERROR et Affichage du résultat ---
            if result["success"]:
                trip = result["data"]
                final_plan = result["plan"]
                initial_plan = result["initial_plan"]

                st.success("Analyse, Planification et Self-Correction réussies ! ")
                
                # Génération du PDF
                pdf_bytes = generate_trip_pdf(trip, final_plan)
                filename = f"plan_voyage_{trip.destination.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                # Ajout du bouton de téléchargement
                st.download_button(
                    label="Télécharger le Plan en PDF ",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf"
                )

                st.header("🔍 Données Analysées")
                # Affichage des métriques (inchangé)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Destination", trip.destination)
                    st.metric("Dates", trip.dates)
                    st.metric("Budget", trip.preferences.budget)
                with col2:
                    st.metric("Adultes", trip.voyageurs.adultes)
                    st.metric("Enfants", trip.voyageurs.enfants)
                    st.metric("Style", trip.preferences.style)
                
                st.divider()
                
                # AFFICHAGE DU PROCESSUS DE RAISONNEMENT (Onglets)
                st.header("Trace du Raisonnement : ReAct & Réflexion")
                
                tab1, tab2 = st.tabs(["Plan Initial (ReAct)", "Plan Final (Self-Correction)"])

                with tab1:
                    st.subheader("1. Plan Généré par l'Agent ReAct")
                    st.warning("Ceci est la première version, générée directement après l'appel des outils.")
                    st.markdown(initial_plan)
                    
                with tab2:
                    st.subheader("2. Version Finale après Auto-Critique")
                    st.success("Ceci est le plan optimisé et corrigé.")
                    st.markdown(final_plan)

            else:
                # Bloc d'erreur si l'agent a échoué (plus besoin d'accéder aux clés manquantes)
                st.error(f"Erreur : {result['message']}")
                if 'error' in result:
                    st.exception(result['error'])
        else:
            st.warning("Veuillez décrire votre voyage avant de lancer la génération.")

if __name__ == "__main__":
    main()