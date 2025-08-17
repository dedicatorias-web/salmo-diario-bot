# NOME DO FICHEIRO: gerador.py (Versão Diffusers com SD-Turbo)

import requests
import logging
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime
import locale
import os
import cloudinary
import cloudinary.uploader
import torch
from diffusers import DiffusionPipeline

# --- CONFIGURAÇÕES DE DESIGN ---
TEXT_FILL_COLOR = (255, 255, 255)
STROKE_COLOR = (0, 0, 0)
STROKE_WIDTH = 2
FONT_FILE_UNIFIED = "Cookie-Regular.ttf"
FONT_SIZE_TITLE = 80
FONT_SIZE_SUBTITLE = 45
FONT_SIZE_DATE = 35
FONT_SIZE_BODY = 40
LINE_SPACING_BODY = 15
PARAGRAPH_SPACING = 30
CARD_OPACITY = 180 # Opacidade do cartão (0=transparente, 255=sólido)
CARD_MARGIN = 60
TEXT_MARGIN = 40

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funções ---
def buscar_salmo_api():
    URL = "https://liturgia.up.railway.app/"
    logging.info("Buscando o salmo na API...")
    try:
        response = requests.get(URL, timeout=15); response.raise_for_status()
        dados = response.json().get('salmo')
        if dados and 'refrao' in dados and 'texto' in dados:
            paragrafos = dados['texto'].split('\n')
            paragrafos_limpos = [p.strip() for p in paragrafos if p.strip()]
            return dados['refrao'], paragrafos_limpos
        return None, None
    except Exception as e:
        logging.error(f"Erro ao buscar salmo: {e}"); return None, None

def compose_final_image(base_image, title, subtitle, date_str, refrao, body_paragraphs):
    logging.info("Compondo a imagem final com layout de cartão translúcido...")
    
    overlay = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    card_area = [(CARD_MARGIN, CARD_MARGIN), (base_image.width - CARD_MARGIN, base_image.height - CARD_MARGIN)]
    draw.rounded_rectangle(card_area, fill=(0, 0, 0, CARD_OPACITY), radius=30)
    
    base_image = Image.alpha_composite(base_image.convert('RGBA'), overlay)
    
    draw = ImageDraw.Draw(base_image)
    try:
        font_title = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_TITLE)
        font_subtitle = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_SUBTITLE)
        font_date = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_DATE)
        font_body = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_BODY)
    except IOError:
        logging.error(f"Fonte '{FONT_FILE_UNIFIED}' não encontrada!")
        return base_image.convert('RGB')

    y_cursor = CARD_MARGIN + TEXT_MARGIN
    text_area_width_pixels = base_image.width - (2 * (CARD_MARGIN + TEXT_MARGIN))
    avg_char_width = font_body.getlength("a")
    wrap_width_chars = int(text_area_width_pixels / avg_char_width) if avg_char_width > 0 else 35

    draw.text((base_image.width / 2, y_cursor), title, font=font_title, fill=TEXT_FILL_COLOR, anchor="mt")
    y_cursor += FONT_SIZE_TITLE
    draw.text((base_image.width / 2, y_cursor), subtitle, font=font_subtitle, fill=TEXT_FILL_COLOR, anchor="mt")
    y_cursor += FONT_SIZE_SUBTITLE + 5
    draw.text((base_image.width / 2, y_cursor), date_str, font=font_date, fill=TEXT_FILL_COLOR, anchor="mt")
    y_cursor += FONT_SIZE_DATE + 50

    full_text = f"{refrao}\n\n" + "\n\n".join(body_paragraphs)
    wrapped_text = textwrap.fill(full_text, width=wrap_width_chars)
    draw.multiline_text((CARD_MARGIN + TEXT_MARGIN, y_cursor), wrapped_text, font=font_body, fill=TEXT_FILL_COLOR, spacing=LINE_SPACING_BODY)

    return base_image.convert('RGB')

def upload_to_cloudinary(file_path, public_id):
    logging.info(f"A fazer o upload do ficheiro '{file_path}' para o Cloudinary...")
    try:
        upload_result = cloudinary.uploader.upload(file_path, public_id=public_id, overwrite=True)
        secure_url = upload_result.get('secure_url')
        if secure_url:
            logging.info(f"Upload bem-sucedido! URL segura: {secure_url}"); return secure_url
        return None
    except Exception as e:
        logging.error(f"Erro durante o upload para o Cloudinary: {e}"); return None

# --- Início do Processo Principal ---
if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        logging.warning("Locale 'pt_BR.UTF-8' não disponível.")
    
    try:
        cloudinary.config(cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), api_key = os.getenv('CLOUDINARY_API_KEY'), api_secret = os.getenv('CLOUDINARY_API_SECRET'))
        logging.info("Credenciais do Cloudinary configuradas.")
    except Exception:
        logging.error("ERRO: Credenciais do Cloudinary não encontradas."); exit()

    refrao_salmo, corpo_paragrafos = buscar_salmo_api()

    if refrao_salmo and corpo_paragrafos:
        logging.info("Carregando modelo de IA (sd-turbo) com diffusers...")
        # Carrega o modelo SD-Turbo, que é mais leve. Usa float32 para CPU.
        pipe = DiffusionPipeline.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
        pipe = pipe.to("cpu")
        
        prompt_visual = f"Uma bela e serena pintura representando o conceito espiritual de '{refrao_salmo}'. Atmosfera pacífica e reconfortante. Estilo de arte digital, cinematográfico."
        
        logging.info("Gerando a imagem de fundo com diffusers...")
        # Gera a imagem base (sd-turbo gera por padrão em 512x512)
        base_image_generated = pipe(
            prompt=prompt_visual, 
            num_inference_steps=2, # 1 ou 2 passos é suficiente para o turbo
            guidance_scale=0.0
        ).images[0]
        
        # Redimensiona a imagem para o nosso formato final
        width, height = 1080, 1920
        base_image = base_image_generated.resize((width, height))
        
        titulo = "Liturgia Diária"
        subtitulo = "Prova de Amor"
        data_hoje = datetime.now().strftime("%d de %B de %Y")
        
        final_image = compose_final_image(base_image, titulo, subtitulo, data_hoje, refrao_salmo, corpo_paragrafos)
        
        nome_arquivo_local = "salmo_do_dia.png"
        final_image.save(nome_arquivo_local)
        logging.info(f"Imagem temporária guardada como '{nome_arquivo_local}'")

        public_id = f"salmos/salmo_{datetime.now().strftime('%Y_%m_%d')}"
        url_da_imagem_na_nuvem = upload_to_cloudinary(nome_arquivo_local, public_id)

        if url_da_imagem_na_nuvem:
            print(f"URL PÚBLICA: {url_da_imagem_na_nuvem}")
        else:
            print("Falha no upload.")
