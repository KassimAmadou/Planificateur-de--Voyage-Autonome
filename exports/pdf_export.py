from fpdf import FPDF
from datetime import datetime
from io import BytesIO

# La classe PDF reste inchangée
class PDF(FPDF):
    """Classe personnalisée pour le PDF avec en-tête et pied de page."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, 'Plan de Voyage Autonome', 0, 1, 'C', 1) 
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

# La fonction generate_trip_pdf est corrigée
def generate_trip_pdf(trip_data, final_plan: str) -> bytes:
    """
    Génère un fichier PDF complet à partir des données structurées et du plan final.
    Retourne le contenu binaire du PDF.
    """
    pdf = PDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Préparation du contenu (Nettoyage des caractères non supportés)
    # Remplacement des Euros (€) par "(EUR)" pour éviter l'erreur d'encodage
    content_for_pdf = final_plan.replace("€", " EUR") 
    
    # Nettoyage du Markdown
    content_for_pdf = content_for_pdf.replace("###", "\n\n**").replace("**", "")

    # 2. Ajout des Métadonnées
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"Destination : {trip_data.destination}", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Dates : {trip_data.dates}", 0, 1)
    pdf.cell(0, 7, f"Voyageurs : {trip_data.voyageurs.adultes} adulte(s), {trip_data.voyageurs.enfants} enfant(s)", 0, 1)
    pdf.cell(0, 7, f"Préférences : Style '{trip_data.preferences.style}', Budget '{trip_data.preferences.budget}'", 0, 1)
    pdf.ln(5)

    # 3. Ajout du Plan Final
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Itinéraire Détaillé (Self-Correction appliquée)", 0, 1)
    pdf.set_font('Arial', '', 11)
    
    # Ajout du texte multiligne
    pdf.multi_cell(0, 6, content_for_pdf)
    
    # Écriture dans le buffer
    # CONVERSION FINALE : bytearray (fpdf2) -> bytes (Streamlit)
    return bytes(pdf.output(dest='S'))