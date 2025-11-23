import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from models.trip_models import VoyageRequest

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_travel_request(user_input: str) -> VoyageRequest:
    """
    Analyse le texte utilisateur et extrait les informations structurées.
    """
    system_prompt = """
    Tu es un expert en extraction de données de voyage.
    Tu dois convertir la demande de l'utilisateur en un objet JSON STRICT correspondant exactement à ce schéma :

    {
        "origin": "string (ex: Paris, Lyon)", 
        "destination": "string (ex: Bali)",
        "dates": "string (ex: du 15 au 22 mars)",
        "voyageurs": {
            "adultes": int,
            "enfants": int
        },
        "preferences": {
            "style": "string",
            "budget": "string"
        }
    }

    RÈGLES IMPORTANTES :
    1. Si l'utilisateur ne précise pas la ville de départ, la valeur par défaut DOIT être "Paris".
    2. Le champ "dates" DOIT être une simple chaîne de caractères.
    3. Imbrique bien voyageurs et preferences.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # ou gpt-4o
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Voici la demande : '{user_input}'. Génère le JSON."}
            ]
        )

        json_content = response.choices[0].message.content
        
        # Debug : Afficher ce que le LLM a renvoyé pour comprendre les erreurs si elles persistent
        print(f"DEBUG JSON REÇU : {json_content}")

        parsed_data = json.loads(json_content)
        
        # Création de l'objet Pydantic
        trip_request = VoyageRequest(raw_input=user_input, **parsed_data)
        
        return trip_request

    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        raise e