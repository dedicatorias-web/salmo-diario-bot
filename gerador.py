# NOME DO FICHEIRO: gerador.py (Versão com Novo Design de Layout)

import requests
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from datetime import datetime
import locale
import os
import cloudinary
import cloudinary.uploader
from io import BytesIO

# Importa as bibliotecas do Google Cloud
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# --- CONFIGURAÇÕES DE DESIGN ---
TEXT_COLOR_HEADER = (0, 0, 0)      # Cor do texto do cabeçalho (Preto)
TEXT_COLOR_BODY = (255, 255, 255)  # Cor do texto do Salmo (Branco)
STROKE_COLOR = (80, 80, 80, 150)   # Sombra/Contorno suave para o cabeçalho
STROKE_WIDTH = 2
CARD_OPACITY = 160 # Opacidade do cartão (0=transparente, 255=sólido)
FONT_FILE_UNIFIED = "Cookie-Regular.ttf" # Use uma fonte que funcione bem
FONT_SIZE_TITLE = 90
FONT_SIZE_SUBTITLE = 50
FONT_SIZE_DATE = 40
FONT_SIZE_SALMO_HEADER = 55
FONT_SIZE_BODY = 45
LINE_SPACING_BODY = 15
PARAGRAPH_SPACING = 30

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funções ---
def buscar_salmo_api():
    URL = "https://liturgia.up.railway.app/"
    logging.info("Buscando o salmo na API...")
    try:
        response = requests.get(URL, timeout=15); response.raise_for_status()
        dados = response.json()
        salmo_dados = dados.get('salmo')
        if salmo_dados and 'refrao' in salmo_dados and 'texto' in salmo_dados:
            paragrafos = salmo_dados['texto'].split('\n')
            paragrafos_limpos = [p.strip() for p in paragrafos if p.strip()]
            # Extrai o título/número do salmo do campo 'titulo'
            titulo_salmo = salmo_dados.get('titulo', 'Salmo') 
            return titulo_salmo, salmo_dados['refrao'], paragrafos_limpos
        return None, None, None
    except Exception as e:
        logging.error(f"Erro ao buscar salmo: {e}"); return None, None, None

def gerar_imagem_com_google_ai(prompt):
    logging.info("Enviando prompt para a API do Google AI (Imagen)...")
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        vertexai.init(project=project_id, location="us-central1")
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16",
            negative_prompt="texto, palavras, letras, feio, má qualidade, disforme, pessoas, animais"
        )
        image_bytes = response.images[0]._image_bytes
        logging.info("Imagem recebida com sucesso do Google AI!")
        return Image.open(BytesIO(image_bytes))
    except Exception as e:
        logging.error(f"Erro ao gerar imagem com a API do Google: {e}")
        return None

def compose_final_image(base_image, title, subtitle, date_str, salmo_title, refrao, body_paragraphs):
    logging.info("Compondo a imagem final com o novo design...")
    
    # Adiciona um leve desfoque gaussiano no fundo para destacar o texto
    background = base_image.filter(ImageFilter.GaussianBlur(radius=3))
    draw = ImageDraw.Draw(background)
    
    try:
        font_title = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_TITLE)
        font_subtitle = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_SUBTITLE)
        font_date = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_DATE)
        font_salmo_header = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_SALMO_HEADER)
        font_body = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_BODY)
    except IOError:
        logging.error(f"Fonte '{FONT_FILE_UNIFIED}'
