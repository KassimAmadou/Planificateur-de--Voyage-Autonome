import streamlit as st
import sys
import os
import requests
from datetime import datetime

# Configuration des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from agents.travel_agent import TravelAgent
from exports.pdf_export import generate_trip_pdf
from core.tools import get_lat_lon # On réutilise votre fonction géo existante

# --- FONCTION D'AFFICHAGE MÉTÉO VISUELLE ---
def afficher_widget_meteo(ville):
    """Récupère et affiche la météo avec des métriques Streamlit jolies"""
    lat, lon = get_lat_lon(ville)
    if not lat:
        return

    # Appel API (Similaire à tools.py mais pour l'UI)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params).json()
        curr = response['current']
        daily = response['daily']

        # Mapping Code WMO -> Emoji
        code = curr['weather_code']
        if code == 0: icon = "☀️"  # Soleil
        elif code in [1, 2, 3]: icon = "⛅" # Nuageux
        elif code in [45, 48]: icon = "🌫️" # Brouillard
        elif 51 <= code <= 67: icon = "🌧️" # Pluie
        elif 71 <= code <= 77: icon = "❄️" # Neige
        elif code >= 95: icon = "⛈️" # Orage
        else: icon = "🌡️"

        st.markdown(f"### {icon} Météo en direct à {ville}")
        
        # 3 Colonnes visuelles
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Actuellement", f"{curr['temperature_2m']}°C", f"{curr['wind_speed_10m']} km/h Vent")
        with col2:
            st.metric("Max Demain", f"{daily['temperature_2m_max'][1]}°C", "Chaud")
        with col3:
            st.metric("Min Demain", f"{daily['temperature_2m_min'][1]}°C", "Frais")
            
        st.divider()
        
    except Exception as e:
        print(f"Erreur widget météo: {e}")

# --- APPLICATION PRINCIPALE ---
def main():
    st.set_page_config(page_title="IA Travel Planner", page_icon="✈️", layout="wide")

    st.title("🌍 Planificateur de Voyage IA")
    st.markdown("---")

    # Zone de saisie (Sidebar ou Main)
    with st.sidebar:
        st.header("Votre Voyage")
        user_input = st.text_area(
            "Décrivez votre rêve :", 
            height=200,
            placeholder="Je veux aller à Bali du 15 au 30 décembre depuis Paris..."
        )
        generate_btn = st.button("🚀 Générer l'itinéraire", type="primary")

    if generate_btn and user_input:
        agent = TravelAgent()
        
        # 1. Barre de progression
        with st.status("🤖 L'agent travaille...", expanded=True) as status:
            st.write("🧠 Analyse de la demande...")
            # On lance le processus
            result = agent.process_request(user_input)
            
            if result["success"]:
                st.write("✈️ Recherche des vols (Amadeus/Google)...")
                st.write("⛅ Vérification de la météo...")
                st.write("✍️ Rédaction du plan et des conseils...")
                status.update(label="✅ Voyage planifié !", state="complete", expanded=False)
            else:
                status.update(label="❌ Erreur", state="error")

        # 2. Affichage des Résultats
        if result["success"]:
            trip = result["data"]
            final_plan = result["plan"]

            # --- A. WIDGET MÉTÉO (NOUVEAU) ---
            afficher_widget_meteo(trip.destination)

            # --- B. ONGLETS ---
            tab_plan, tab_details = st.tabs(["📝 Itinéraire & Conseils", "🔍 Détails Techniques"])

            with tab_plan:
                st.markdown(final_plan)
                
                # Bouton PDF
                pdf_bytes = generate_trip_pdf(trip, final_plan)
                st.download_button(
                    label="📄 Télécharger le PDF",
                    data=pdf_bytes,
                    file_name=f"Voyage_{trip.destination}.pdf",
                    mime="application/pdf"
                )

            with tab_details:
                st.json(trip.model_dump())
                st.warning("Trace brute du raisonnement :")
                st.text(result["initial_plan"])

        else:
            st.error(f"Oups ! {result['message']}")
            if 'error' in result:
                st.code(result['error'])

if __name__ == "__main__":
    main()