import json
from openai import OpenAI
from core.parse_input import analyze_travel_request
from core.tools import AVAILABLE_TOOLS_MAP, TRAVEL_TOOL_SCHEMAS 

class TravelAgent:
    def __init__(self):
        self.client = OpenAI()

    def process_request(self, user_input: str):
        """
        Point d'entrée principal de l'agent.
        1. Analyse la demande.
        2. Déclenche la boucle ReAct.
        3. Applique la Self-Correction.
        """
        try:
            # Étape 1 : Analyse des données structurées
            trip_data = analyze_travel_request(user_input)
            
            # --- DEBUG : Début du ReAct ---
            print("\n--- Étape 1 : Démarrage du Raisonnement ReAct ---")
            
            # Étape 2 : Démarrer la boucle de raisonnement (ReAct)
            initial_plan = self._run_reasoning_loop(trip_data)
            
            # --- DEBUG : Affichage du Plan Initial ---
            print("\n--- Étape 2 : Plan Initial (AVANT Self-Correction) ---")
            print(initial_plan)
            
            # --- DEBUG : Début de la Self-Correction ---
            print("\n--- Étape 3 : Démarrage de la Self-Correction ---")
            
            # Étape 3 : Self-Correction (Critique et Correction)
            final_plan = self._critique_and_correct(trip_data, initial_plan)
            
            # --- DEBUG : Affichage du Plan Final ---
            print("\n--- Étape 4 : Plan Final (APRÈS Self-Correction) ---")
            print(final_plan)

            return {
                "success": True,
                "data": trip_data,
                "plan": final_plan,
                "initial_plan": initial_plan, 
                "message": "Itinéraire généré et corrigé avec succès."
            }

        except Exception as e:
            # ... (gestion des erreurs inchangée) ...
            return {
                "success": False,
                "error": str(e),
                "message": "Désolé, je n'ai pas réussi à comprendre ou à générer le plan de voyage."
            }
    def _run_reasoning_loop(self, trip_data):
        """
        Boucle ReAct : L'agent pense, appelle des outils, observe, puis répond.
        (Code ReAct inchangé, il produit un premier plan).
        """
        messages = [
            {"role": "system", "content": f"""
            Tu es le Planificateur de Voyage Autonome. Ton objectif est d'utiliser les outils
            disponibles pour générer un plan de voyage complet.
            
            Les données utilisateur sont : {trip_data.model_dump_json()}.
            
            Tâches :
            1. Commence toujours par rechercher les vols et consulter la météo.
            2. Compile les informations de l'observation dans un plan de voyage initial.
            """}
        ]
        
        for i in range(5):
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=messages,
                tools=TRAVEL_TOOL_SCHEMAS,
                tool_choice="auto" 
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                return response_message.content

            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = AVAILABLE_TOOLS_MAP.get(function_name)
                function_args = json.loads(tool_call.function.arguments)

                function_response = function_to_call(**function_args)
                
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

        return "Erreur : L'agent a atteint la limite d'itérations sans finaliser le plan."

    def _critique_and_correct(self, trip_data, initial_plan: str) -> str:
        """
        Mécanisme de Self-Correction (réflexion).
        L'agent critique son propre plan initial et génère une version finale optimisée.
        """
        
        critique_prompt = f"""
        Tu es l'agent de Self-Correction. Ton rôle est de critiquer et d'améliorer le plan initial
        généré par l'agent planificateur.
        
        Données de la demande : {trip_data.model_dump_json()}
        
        Plan initial à corriger :
        ---
        {initial_plan}
        ---
        
        Instructions :
        1. **Critique :** Identifie les points faibles, les incohérences (ex: proposer un vol trop cher si le budget est 'Faible'), ou les omissions. (Utilise Chain of Thought)[cite: 29].
        2. **Correction :** Ne présente PAS la critique à l'utilisateur. Génère directement la version FINALE du plan de voyage, en appliquant les améliorations que tu as identifiées, pour qu'il soit parfait.
        """
        
        # Envoi de la requête de critique à l'API (pas besoin d'outils ici)
        critique_response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "Tu es un relecteur de haute qualité. Ne réponds que par la version corrigée."},
                {"role": "user", "content": critique_prompt}
            ]
        )
        
        return critique_response.choices[0].message.content