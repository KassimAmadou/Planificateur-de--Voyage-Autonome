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
    
    # Nous donnons un EXEMPLE du JSON attendu pour que le LLM copie la structure exacte.
    system_prompt = """
    Tu es un expert en extraction de données de voyage.
    Tu dois convertir la demande de l'utilisateur en un objet JSON STRICT correspondant exactement à ce schéma :

    {
        "destination": "string (ex: Paris, Bali)",
        "dates": "string (ex: du 15 au 22 mars)",
        "voyageurs": {
            "adultes": int (ex: 2),
            "enfants": int (ex: 0)
        },
        "preferences": {
            "style": "string (ex: Détente, Aventure)",
            "budget": "string (ex: Moyen, Élevé)"
        }
    }

    RÈGLES IMPORTANTES :
    1. Le champ "dates" DOIT être une simple chaîne de caractères (pas d'objet).
    2. Tu DOIS imbriquer les nombres d'adultes et d'enfants DANS l'objet "voyageurs".
    3. Tu DOIS imbriquer le style et le budget DANS l'objet "preferences".
    4. Si une information manque, déduis-la de manière logique ou utilise des valeurs par défaut (1 adulte, budget moyen).
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