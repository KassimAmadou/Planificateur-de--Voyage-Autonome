from fpdf import FPDF
from datetime import datetime
from io import BytesIO

class PDF(FPDF):
    """Classe personnalisée pour le PDF avec en-tête et pied de page."""
    def header(self):
        # Utilisation de Helvetica (standard core font) pour éviter les warnings
        self.set_font('Helvetica', 'B', 15)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, 'Plan de Voyage Autonome', border=0, new_x="LMARGIN", new_y="NEXT", align='C', fill=True) 
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

def sanitize_text(text: str) -> str:
    """Nettoie le texte pour l'encodage Latin-1."""
    replacements = {
        "€": " EUR", "œ": "oe", "Œ": "OE", "’": "'", "…": "...",
        "–": "-", "—": "-", "«": '"', "»": '"',
        "ç": "c", "Ç": "C"
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def generate_trip_pdf(trip_data, final_plan: str) -> bytes:
    pdf = PDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Nettoyage
    safe_plan = sanitize_text(final_plan)
    safe_dest = sanitize_text(trip_data.destination)
    safe_dates = sanitize_text(trip_data.dates)
    
    # Remplacer le markdown basique
    content_for_pdf = safe_plan.replace("###", "\n\n").replace("**", "").replace("##", "\n")

    # Métadonnées
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f"Destination : {safe_dest}", new_x="LMARGIN", new_y="NEXT", align='L')
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 7, f"Dates : {safe_dates}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Voyageurs : {trip_data.voyageurs.adultes} ad., {trip_data.voyageurs.enfants} enf.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Budget : {trip_data.preferences.budget}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Contenu
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, "Itineraire Detaille :", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 11)
    
    try:
        pdf.multi_cell(0, 6, content_for_pdf)
    except Exception:
        # Fallback ASCII brutal si latin-1 échoue encore
        pdf.multi_cell(0, 6, content_for_pdf.encode('ascii', 'ignore').decode('ascii'))
    
    # Output compatible Streamlit (sans dest='S')
    return bytes(pdf.output())