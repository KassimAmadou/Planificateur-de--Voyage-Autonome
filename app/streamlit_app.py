import streamlit as st
import sys
import os

# --- 1. CONFIGURATION DU CHEMIN (Indispensable pour les imports) ---
# On récupère le dossier courant et on ajoute le dossier parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# --- 2. IMPORTS DU PROJET ---
from agents.travel_agent import TravelAgent

# --- 3. APPLICATION STREAMLIT ---
def main():
    st.set_page_config(page_title="Planificateur de Voyage AI", page_icon="✈️")

    st.title("Planificateur de Voyage Autonome")
    st.markdown("Décrivez votre voyage idéal, et notre agent s'occupe de tout !")

    # Zone de saisie
    user_input = st.text_area(
        "Votre projet de voyage :", 
        height=150,
        placeholder="Ex: Je veux partir à Bali du 15 au 22 mars avec 2 adultes et 1 enfant, budget moyen, on aime bouger..."
    )

    # Bouton d'action (Attention : il ne doit y en avoir qu'un seul avec ce label)
    if st.button("Générer mon itinéraire"):
        if user_input:
            # Instanciation de l'agent
            agent = TravelAgent()
            
            with st.spinner("L'agent analyse votre demande..."):
                # Appel de l'agent
                result = agent.process_request(user_input)

            # Affichage du résultat
            if result["success"]:
                trip = result["data"]
                st.success("Analyse réussie ! Voici ce que j'ai compris :")
                
                # Affichage structuré des données extraites
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
                st.info("Prochaine étape : L'agent va maintenant chercher des vols et des hôtels (Logique à venir).")
                
            else:
                st.error(f"Erreur : {result['message']}")
                if 'error' in result:
                    st.exception(result['error'])
        else:
            st.warning("Veuillez décrire votre voyage avant de lancer la génération.")

if __name__ == "__main__":
    main()