from core.parse_input import analyze_travel_request

class TravelAgent:
    def __init__(self):
        pass

    def process_request(self, user_input: str):
        """
        Point d'entrée principal de l'agent.
        1. Analyse la demande
        2. (Plus tard) Planifie l'itinéraire
        """
        print(f"--- Agent : Réception de la demande : {user_input[:50]}... ---")
        
        # Étape 1 : Comprendre la demande
        try:
            trip_data = analyze_travel_request(user_input)
            return {
                "success": True,
                "data": trip_data,
                "message": "Demande analysée avec succès."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Désolé, je n'ai pas réussi à comprendre votre demande."
            }