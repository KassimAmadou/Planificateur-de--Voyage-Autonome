import os
import requests
from serpapi import GoogleSearch
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import json

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# --- CODES IATA ---
IATA_MAPPING = {
    "paris": "CDG", "lyon": "LYS", "nice": "NCE", "marseille": "MRS",
    "londres": "LON", "london": "LON", "rome": "FCO", "milan": "MXP",
    "madrid": "MAD", "barcelone": "BCN", "barcelona": "BCN",
    "lisbonne": "LIS", "porto": "OPO", "berlin": "BER", "munich": "MUC",
    "amsterdam": "AMS", "bruxelles": "BRU", "geneve": "GVA", "zurich": "ZRH",
    "bali": "DPS", "denpasar": "DPS", "tokyo": "NRT", "osaka": "KIX",
    "bangkok": "BKK", "phuket": "HKT", "singapour": "SIN", "singapore": "SIN",
    "dubai": "DXB", "new york": "JFK", "los angeles": "LAX", "miami": "MIA",
    "sydney": "SYD", "hong kong": "HKG", "seoul": "ICN"
}

CITY_TO_COUNTRY = {
    "bali": "Indonesia", "paris": "France", "tokyo": "Japan",
    "bangkok": "Thailand", "new york": "USA", "london": "UK",
    "rome": "Italy", "barcelona": "Spain", "dubai": "UAE"
}

# --- UTILITAIRES ---

def normaliser_ville(ville: str) -> str:
    ville = ville.lower().strip()
    replacements = {"é": "e", "è": "e", "ê": "e", "à": "a", "ï": "i", "ç": "c"}
    for old, new in replacements.items():
        ville = ville.replace(old, new)
    return ville

def trouver_code_iata(ville: str) -> str:
    ville_norm = normaliser_ville(ville)
    code = IATA_MAPPING.get(ville_norm)
    if code:
        print(f"✅ IATA: {ville} -> {code}")
        return code
    print(f"❌ IATA non trouvé: {ville}")
    return None

def extraire_dates(dates_texte: str) -> tuple:
    if re.match(r'\d{4}-\d{2}-\d{2}', dates_texte):
        return dates_texte, None
    
    mois_map = {
        "janvier": "01", "fevrier": "02", "février": "02", "mars": "03",
        "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
        "aout": "08", "août": "08", "septembre": "09", "octobre": "10",
        "novembre": "11", "decembre": "12", "décembre": "12"
    }
    
    match = re.search(r'du?\s+(\d{1,2})\s+(?:au|-)\s+(\d{1,2})\s+(\w+)', dates_texte.lower())
    if match:
        jour_dep = match.group(1).zfill(2)
        jour_ret = match.group(2).zfill(2)
        mois_txt = match.group(3)
        mois = mois_map.get(mois_txt)
        
        if mois:
            annee_actuelle = datetime.now().year
            mois_actuel = datetime.now().month
            annee = annee_actuelle + 1 if int(mois) < mois_actuel else annee_actuelle
            
            date_dep = f"{annee}-{mois}-{jour_dep}"
            date_ret = f"{annee}-{mois}-{jour_ret}"
            return date_dep, date_ret
    
    dep = datetime.now() + timedelta(days=30)
    ret = dep + timedelta(days=7)
    return dep.strftime("%Y-%m-%d"), ret.strftime("%Y-%m-%d")

def get_skyscanner_link(code_dep: str, code_arr: str, date_dep: str, date_ret: str = None, adultes: int = 1, enfants: int = 0) -> str:
    try:
        y1, m1, d1 = date_dep.split('-')
        date_dep_sky = f"{y1[-2:]}{m1}{d1}"
        
        if date_ret:
            y2, m2, d2 = date_ret.split('-')
            date_ret_sky = f"{y2[-2:]}{m2}{d2}"
            url = f"https://www.skyscanner.fr/transport/vols/{code_dep.lower()}/{code_arr.lower()}/{date_dep_sky}/{date_ret_sky}"
        else:
            url = f"https://www.skyscanner.fr/transport/vols/{code_dep.lower()}/{code_arr.lower()}/{date_dep_sky}"
        
        params = []
        if adultes > 1: params.append(f"adults={adultes}")
        if enfants > 0: params.append(f"children={enfants}")
        
        if params: url += "?" + "&".join(params)
        return url
    except:
        return "https://www.skyscanner.fr"

def get_google_flights_link(code_dep: str, code_arr: str, date_dep: str, date_ret: str = None, adultes: int = 1, enfants: int = 0) -> str:
    try:
        base = f"https://www.google.com/travel/flights"
        if date_ret:
            query = f"?q=Flights+from+{code_dep}+to+{code_arr}+on+{date_dep}+return+{date_ret}"
        else:
            query = f"?q=Flights+from+{code_dep}+to+{code_arr}+on+{date_dep}"
        
        total = adultes + enfants
        if total > 1: query += f"&passengers={total}"
        return base + query
    except:
        return "https://www.google.com/travel/flights"

def get_lat_lon(city_name: str):
    try:
        geo = Nominatim(user_agent="TravelPlanner_2025")
        loc = geo.geocode(city_name)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return None, None

# --- API SKYSCANNER ---

def search_skyscanner_api(code_dep: str, code_arr: str, date_dep: str, date_ret: str = None, adultes: int = 1, enfants: int = 0) -> list:
    if not RAPIDAPI_KEY:
        print("⚠️ RAPIDAPI_KEY manquante")
        return []
    
    print(f"🔍 Skyscanner API: {code_dep} → {code_arr}")
    url = "https://skyscanner-api.p.rapidapi.com/v3/flights/live/search/create"
    
    query_legs = [{
        "originPlaceId": {"iata": code_dep},
        "destinationPlaceId": {"iata": code_arr},
        "date": {"year": int(date_dep[:4]), "month": int(date_dep[5:7]), "day": int(date_dep[8:10])}
    }]
    
    if date_ret:
        query_legs.append({
            "originPlaceId": {"iata": code_arr},
            "destinationPlaceId": {"iata": code_dep},
            "date": {"year": int(date_ret[:4]), "month": int(date_ret[5:7]), "day": int(date_ret[8:10])}
        })
    
    payload = {
        "query": {
            "market": "FR", "locale": "fr-FR", "currency": "EUR",
            "adults": adultes, "children": enfants, "cabinClass": "CABIN_CLASS_ECONOMY",
            "queryLegs": query_legs
        }
    }
    
    headers = {
        "x-rapidapi-host": "skyscanner-api.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json()
        itineraries = data.get("content", {}).get("results", {}).get("itineraries", {})
        
        vols = []
        for itin_id, itin_data in list(itineraries.items())[:5]:
            try:
                price = itin_data.get("pricingOptions", [{}])[0].get("price", {}).get("amount", 0)
                legs = itin_data.get("legs", [])
                if legs:
                    leg = legs[0]
                    carrier_ids = leg.get("carriers", {}).get("marketing", [])
                    carriers_section = data.get("content", {}).get("results", {}).get("carriers", {})
                    carrier_name = carriers_section.get(carrier_ids[0], {}).get("name", "Compagnie") if carrier_ids else "Compagnie"
                    dep_time = leg.get("departure", "N/A")
                    arr_time = leg.get("arrival", "N/A")
                    
                    vols.append({
                        "source": "Skyscanner",
                        "compagnie": carrier_name,
                        "prix": int(price / 1000) if price else 0,
                        "devise": "EUR",
                        "heure_dep": dep_time[:5] if isinstance(dep_time, str) else "N/A",
                        "heure_arr": arr_time[:5] if isinstance(arr_time, str) else "N/A",
                        "lien": "#", # Lien ignoré ici car on utilise le global
                        "vol_id": itin_id
                    })
            except: continue
        return vols
    except Exception as e:
        print(f"❌ Erreur Skyscanner API: {e}")
        return []

# --- SERPAPI ---

def search_serpapi(code_dep: str, code_arr: str, date_dep: str, date_ret: str = None, adultes: int = 1, enfants: int = 0) -> list:
    if not SERPAPI_KEY: return []
    print(f"🔍 SerpAPI: {code_dep} → {code_arr}")
    
    try:
        params = {
            "engine": "google_flights", "departure_id": code_dep, "arrival_id": code_arr,
            "outbound_date": date_dep, "currency": "EUR", "hl": "fr",
            "adults": adultes, "children": enfants, "api_key": SERPAPI_KEY
        }
        if date_ret:
            params["return_date"] = date_ret
            params["type"] = "1"
        else:
            params["type"] = "2"
        
        search = GoogleSearch(params)
        results = search.get_dict()
        flights = results.get("best_flights", []) or results.get("other_flights", [])
        
        vols = []
        for vol in flights[:5]:
            try:
                compagnie = vol['flights'][0].get('airline', 'Compagnie')
                prix = int(vol.get('price', 0))
                heure_dep = vol['flights'][0]['departure_airport'].get('time', 'N/A')
                heure_arr = vol['flights'][0]['arrival_airport'].get('time', 'N/A')
                
                vols.append({
                    "source": "Google Flights",
                    "compagnie": compagnie,
                    "prix": prix,
                    "devise": "EUR",
                    "heure_dep": heure_dep,
                    "heure_arr": heure_arr,
                    "lien": "#", 
                    "vol_id": f"serp_{hash(compagnie + str(prix))}"
                })
            except: continue
        return vols
    except Exception as e:
        print(f"❌ Erreur SerpAPI: {e}")
        return []

# --- FALLBACK ---

def generer_vols_exemple(code_dep: str, code_arr: str, date_dep: str, date_ret: str = None, adultes: int = 1, enfants: int = 0) -> list:
    print(f"⚠️ FALLBACK: Vols d'exemple")
    prix_base = 600
    multiplicateur = adultes + (enfants * 0.7)
    compagnies = ["Singapore Airlines", "Qatar Airways", "Emirates", "Air France"]
    
    vols = []
    for i, compagnie in enumerate(compagnies, 1):
        prix = int((prix_base + (i*50)) * multiplicateur)
        vols.append({
            "source": "Estimation",
            "compagnie": compagnie,
            "prix": prix,
            "devise": "EUR",
            "heure_dep": f"{8+i}:00",
            "heure_arr": f"{14+i}:30",
            "lien": "#",
            "vol_id": f"ex_{i}"
        })
    return vols

# --- FORMATAGE FINAL ---

def compare_and_format_flights(vols_skyscanner: list, vols_serpapi: list, link_skyscanner: str, link_google: str, adultes: int, enfants: int) -> str:
    """Compare et formate SANS lien individuel"""
    all_flights = vols_skyscanner + vols_serpapi
    
    if not all_flights:
        return (f"⚠️ Aucun vol trouvé.\n\n"
                f"🔗 [Rechercher sur Skyscanner]({link_skyscanner})\n"
                f"🔗 [Rechercher sur Google Flights]({link_google})")
    
    # Déduplication
    seen = set()
    unique_flights = []
    for vol in all_flights:
        vol_id = vol.get('vol_id')
        if vol_id not in seen:
            seen.add(vol_id)
            unique_flights.append(vol)
    
    unique_flights.sort(key=lambda x: x['prix'])
    min_prix = unique_flights[0]['prix'] if unique_flights else 0
    
    total = adultes + enfants
    output = f"## ✈️ Vols pour {total} voyageur(s)\n\n"
    
    for i, vol in enumerate(unique_flights[:6], 1):
        prix = vol['prix']
        icon = "🟦" if vol['source'] == "Skyscanner" else "🔍" if vol['source'] == "Google Flights" else "📊"
        
        # Affichage Prix
        badge = " 🟢 **MEILLEUR PRIX**" if prix == min_prix and prix > 0 else ""
        prix_fmt = f"**🟢 {prix} EUR**" if prix == min_prix else f"**{prix} EUR**"
        
        output += f"### {icon} Vol {i} - {vol['compagnie']}{badge}\n"
        output += f"- **Prix total**: {prix_fmt}\n"
        output += f"- **Horaires**: Départ {vol['heure_dep']} → Arrivée {vol['heure_arr']}\n"
        output += f"- **Source**: {vol['source']}\n\n"
        # AUCUN LIEN INDIVIDUEL ICI (C'est ce qui corrige votre problème)
    
    output += f"---\n"
    output += f"🔗 [Comparer toutes les options sur Skyscanner]({link_skyscanner})\n"
    output += f"🔗 [Voir sur Google Flights]({link_google})\n"
    
    return output

# --- OUTIL PRINCIPAL ---

def rechercher_vols(depart: str, arrivee: str, date_depart: str, adultes: int = 1, enfants: int = 0) -> str:
    date_dep, date_ret = extraire_dates(date_depart)
    code_dep = trouver_code_iata(depart)
    code_arr = trouver_code_iata(arrivee)
    
    if not code_dep or not code_arr: return f"❌ Codes introuvables."
    
    print(f"🚀 RECHERCHE: {code_dep} -> {code_arr}")
    
    link_sky = get_skyscanner_link(code_dep, code_arr, date_dep, date_ret, adultes, enfants)
    link_google = get_google_flights_link(code_dep, code_arr, date_dep, date_ret, adultes, enfants)
    
    vols_sky = search_skyscanner_api(code_dep, code_arr, date_dep, date_ret, adultes, enfants)
    vols_serp = search_serpapi(code_dep, code_arr, date_dep, date_ret, adultes, enfants)
    
    if not vols_sky and not vols_serp:
        vols_ex = generer_vols_exemple(code_dep, code_arr, date_dep, date_ret, adultes, enfants)
        return compare_and_format_flights(vols_ex, [], link_sky, link_google, adultes, enfants)
    
    return compare_and_format_flights(vols_sky, vols_serp, link_sky, link_google, adultes, enfants)

# --- AUTRES OUTILS ---

def consulter_meteo_reelle(destination: str) -> str:
    lat, lon = get_lat_lon(destination)
    if not lat: return "Météo introuvable"
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        p = {"latitude": lat, "longitude": lon, "current": "temperature_2m", "daily": "temperature_2m_max,temperature_2m_min"}
        r = requests.get(url, params=p).json()
        return f"Météo {destination}: Actu {r['current']['temperature_2m']}°C, Demain Max {r['daily']['temperature_2m_max'][1]}°C"
    except: return "Erreur Météo"

def recherche_web_contextuelle(requete: str, destination: str = None) -> str:
    if not SERPAPI_KEY: return "Pas de clé API"
    q = f"{requete} {destination or ''} tourism".strip()
    try:
        params = {"engine": "google", "q": q, "api_key": SERPAPI_KEY, "num": 3}
        res = GoogleSearch(params).get_dict().get("organic_results", [])
        return "\n".join([f"- [{r['title']}]({r['link']})" for r in res]) if res else "Rien trouvé"
    except: return "Erreur Web"

AVAILABLE_TOOLS_MAP = {
    "consulter_meteo": consulter_meteo_reelle,
    "rechercher_infos_voyage": recherche_web_contextuelle,
    "rechercher_vols": rechercher_vols
}

TRAVEL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "consulter_meteo",
            "description": "Météo actuelle.",
            "parameters": {"type": "object", "properties": {"destination": {"type": "string"}}, "required": ["destination"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_infos_voyage",
            "description": "Recherche web.",
            "parameters": {"type": "object", "properties": {"requete": {"type": "string"}, "destination": {"type": "string"}}, "required": ["requete", "destination"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_vols",
            "description": "Recherche vols.",
            "parameters": {
                "type": "object",
                "properties": {
                    "depart": {"type": "string"}, "arrivee": {"type": "string"},
                    "date_depart": {"type": "string"},
                    "adultes": {"type": "integer", "default": 1},
                    "enfants": {"type": "integer", "default": 0}
                },
                "required": ["depart", "arrivee", "date_depart"]
            }
        }
    }
]