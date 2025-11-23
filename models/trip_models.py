from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import BaseModel, Field
class Voyageur(BaseModel):
    adultes: int = Field(description="Nombre d'adultes")
    enfants: int = Field(description="Nombre d'enfants")

class Preferences(BaseModel):
    style: str = Field(description="Style de voyage (ex: dynamique, détente, culturel)")
    budget: str = Field(description="Budget estimé (faible, moyen, élevé)")

class VoyageRequest(BaseModel):
    """Structure des informations extraites de la demande utilisateur"""
    origin: str = Field(description="Paris") 
    destination: str = Field(description="La destination du voyage")
    dates: str = Field(description="Dates ou période du voyage")
    voyageurs: Voyageur
    preferences: Preferences
    raw_input: str = Field(description="Le texte brut saisi par l'utilisateur")