import json
import datetime
from openai import OpenAI
from core.parse_input import analyze_travel_request
from core.tools import AVAILABLE_TOOLS_MAP, TRAVEL_TOOL_SCHEMAS

class TravelAgent:
    def __init__(self):
        self.client = OpenAI()

    def process_request(self, user_input: str):
        try:
            trip_data = analyze_travel_request(user_input)
            
            print("\n🧠 --- Démarrage ReAct ---")
            initial_plan = self._run_reasoning_loop(trip_data)
            
            print("\n✨ --- Démarrage Self-Correction ---")
            final_plan = self._critique_and_correct(trip_data, initial_plan)
            
            return {
                "success": True,
                "data": trip_data,
                "plan": final_plan,
                "initial_plan": initial_plan,
                "message": "Succès"
            }

        except Exception as e:
            print(f"❌ Erreur agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors du traitement de la demande."
            }

    def _run_reasoning_loop(self, trip_data):
        """Boucle ReAct avec support voyageurs"""
        ville_depart = getattr(trip_data, 'origin', 'Paris')
        adultes = trip_data.voyageurs.adultes
        enfants = trip_data.voyageurs.enfants

        system_prompt = f"""Tu es un Assistant de Voyage Expert utilisant la méthode ReAct.

🎯 DONNÉES DU VOYAGE :
- Départ : {ville_depart}
- Destination : {trip_data.destination}
- Dates : {trip_data.dates}
- Voyageurs : {adultes} adultes, {enfants} enfants
- Style : {trip_data.preferences.style}
- Budget : {trip_data.preferences.budget}

🛠️ TES OUTILS (UTILISE-LES DANS CET ORDRE) :

1️⃣ **rechercher_vols** : OBLIGATOIRE en premier
   - IMPORTANT : Passe TOUJOURS les paramètres adultes et enfants !
   - Exemple d'appel CORRECT :
     rechercher_vols(
         depart="{ville_depart}",
         arrivee="{trip_data.destination}",
         date_depart="{trip_data.dates}",
         adultes={adultes},
         enfants={enfants}
     )

2️⃣ **consulter_meteo** : OBLIGATOIRE pour les conseils vestimentaires
   - consulter_meteo(destination="{trip_data.destination}")

3️⃣ **rechercher_infos_voyage** : Pour activités/hébergements
   - rechercher_infos_voyage(requete="meilleures activités", destination="{trip_data.destination}")

📋 STRUCTURE DE TA RÉPONSE FINALE :

## ✈️ Transport
[Copie EXACTEMENT les vols avec prix TOTAL pour {adultes + enfants} personne(s)]
[Garde TOUS les liens de réservation]

## 🌤️ Météo & Conseils Valise
[Résumé météo + conseils personnalisés selon températures]

## 🏨 Hébergement & Activités
[Suggestions adaptées au style "{trip_data.preferences.style}"]

⚠️ RÈGLES ABSOLUES :
- NE JAMAIS inventer de prix
- Garde TOUS les liens retournés par les outils
- Mentionne clairement que les prix affichés sont pour {adultes + enfants} voyageur(s)
- Si un outil échoue, indique "Informations non disponibles"
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Planifie ce voyage : {trip_data.raw_input}"}
        ]
        
        for iteration in range(8):
            print(f"🔄 ReAct - Itération {iteration + 1}/8")
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    messages=messages,
                    tools=TRAVEL_TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.7
                )
            except Exception as e:
                print(f"❌ Erreur OpenAI: {e}")
                return f"Erreur API OpenAI: {str(e)}"

            message = response.choices[0].message
            
            if not message.tool_calls:
                print("✅ Réponse finale générée")
                return message.content

            messages.append(message)

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                print(f"  🔧 Appel : {fn_name}({fn_args})")
                
                func = AVAILABLE_TOOLS_MAP.get(fn_name)
                
                if func:
                    try:
                        tool_result = func(**fn_args)
                        print(f"  ✅ Résultat obtenu ({len(str(tool_result))} caractères)")
                    except Exception as e:
                        tool_result = f"Erreur {fn_name}: {str(e)}"
                        print(f"  ❌ {tool_result}")
                else:
                    tool_result = f"Outil {fn_name} non disponible"
                    print(f"  ❌ {tool_result}")

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": str(tool_result)
                })

        print("⚠️ Limite d'itérations atteinte")
        return "Le plan a atteint la limite de raisonnement. Relancez pour un résultat complet."

    def _critique_and_correct(self, trip_data, initial_plan: str) -> str:
        """Self-Correction"""
        critique_prompt = f"""Tu es un Éditeur Expert en Voyages. 

📄 PLAN BRUT :
{initial_plan}

🎯 TA MISSION :
1. Vérifie que TOUS les liens sont présents
2. Améliore la mise en forme Markdown (##, **, listes)
3. Ajoute des émojis pertinents
4. Assure-toi que les conseils valise sont basés sur la météo
5. Garde un ton professionnel

⚠️ RÈGLES ABSOLUES :
- NE SUPPRIME AUCUN LIEN
- NE MODIFIE PAS les prix
- Mentionne clairement le nombre de voyageurs
- Si un élément manque, indique "(Non disponible)"

✨ AMÉLIORE LA FORME, PAS LE FOND.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": critique_prompt}],
                temperature=0.3
            )
            
            corrected_plan = response.choices[0].message.content
            print("✅ Self-Correction terminée")
            return corrected_plan
            
        except Exception as e:
            print(f"⚠️ Erreur Self-Correction: {e}")
            return initial_plan