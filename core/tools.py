from typing import List, Dict, Any

# --- OUTIL 1 : Recherche de Vol ---
def rechercher_vols(destination: str, dates: str, adultes: int) -> str:
    """
    Recherche les vols disponibles et simule les résultats pour la destination, les dates
    et le nombre d'adultes spécifiés.
    """
    
    # Simulation des résultats d'API
    if "tokyo" in destination.lower() and "décembre" in dates.lower():
        vols_simules = [
            {"compagnie": "Air France", "prix": "1200€", "escale": "1"},
            {"compagnie": "KLM", "prix": "1100€", "escale": "2"}
        ]
        
    elif "paris" in destination.lower():
        vols_simules = [
            {"compagnie": "EasyJet", "prix": "80€", "escale": "0"},
            {"compagnie": "Ryanair", "prix": "95€", "escale": "0"}
        ]
    else:
        vols_simules = [{"compagnie": "Aucune trouvée", "prix": "N/A", "escale": "N/A"}]

    resultat_str = f"Résultats de vols pour {destination} ({dates}, {adultes} pers.) : \n"
    for vol in vols_simules:
        resultat_str += f"- {vol['compagnie']}: {vol['prix']} (escales: {vol['escale']})\n"
        
    return resultat_str

# --- OUTIL 2 : Consultation Météo ---
def consulter_meteo(destination: str, dates: str) -> str:
    """
    Consulte les conditions météorologiques (simulées) pour une destination donnée.
    """
    destination_lower = destination.lower()
    
    # Simulation de la météo
    if "tokyo" in destination_lower:
        meteo_simulee = "Temps froid et sec (5°C à 10°C). Prévoir des vêtements chauds."
    elif "bali" in destination_lower:
        meteo_simulee = "Saison des pluies. Températures chaudes (25°C à 30°C) avec averses sporadiques."
    elif "paris" in destination_lower:
        meteo_simulee = "Généralement froid et pluvieux (5°C à 8°C). Prévoir parapluie et manteau."
    else:
        meteo_simulee = "Météo non trouvée, prévoyez large."

    return f"Prévisions météo pour {destination} aux dates {dates} : {meteo_simulee}"

# --- MAPPING des fonctions pour l'appel (Utilisé par l'agent) ---
AVAILABLE_TOOLS_MAP = {
    "rechercher_vols": rechercher_vols,
    "consulter_meteo": consulter_meteo,
}

# --- SCHÉMAS JSON pour l'API OpenAI (Utilisé par l'agent) ---
TRAVEL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_vols",
            "description": "Recherche les vols disponibles et simule les résultats pour la destination, les dates et le nombre d'adultes spécifiés.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Destination du voyage (Ville ou Pays)."},
                    "dates": {"type": "string", "description": "Période de voyage."},
                    "adultes": {"type": "integer", "description": "Nombre d'adultes."},
                },
                "required": ["destination", "dates", "adultes"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consulter_meteo",
            "description": "Consulte les conditions météorologiques pour une destination donnée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Destination du voyage (Ville ou Pays)."},
                    "dates": {"type": "string", "description": "Période de voyage."},
                },
                "required": ["destination", "dates"],
            },
        }
    }
]