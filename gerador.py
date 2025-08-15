# NOME DO ARQUIVO: gerador.py (Versão Diffusers com SD-Turbo)

import torch
from diffusers import DiffusionPipeline
import requests
import logging
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime
import locale
import os
import cloudinary
import cloudinary.uploader

# --- CONFIGURAÇÕES DE DESIGN ---
# (Ajustadas para uma resolução menor padrão do sd-turbo: 512x512)
TEXT_FILL_COLOR = (255, 255, 255); STROKE_COLOR = (0, 0, 0); STROKE_WIDTH = 1
FONT_FILE_UNIFIED = "Cookie-Regular.ttf"
FONT_SIZE_TITLE = 30; FONT_SIZE_DATE = 15; FONT_SIZE_BODY = 20
LINE_SPACING_BODY = 8; PARAGRAPH_SPACING = 18; MARGIN = 30

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funções ---
def buscar_salmo_api():
    # ... (sem alterações)
    URL = "https://liturgia.up.railway.app/"; logging.info("Buscando o salmo na API...")
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

def compose_final_image(base_image, title, date_str, refrao, body_paragraphs):
    # ... (sem alterações na lógica, apenas nos valores de configuração)
    logging.info("Compondo a imagem final...")
    draw = ImageDraw.Draw(base_image)
    try:
        font_title = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_TITLE)
        font_date = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_DATE)
        font_body = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_BODY)
    except IOError:
        logging.error(f"Fonte '{FONT_FILE_UNIFIED}' não encontrada!"); return base_image
    y_cursor = 50; x_pos = MARGIN; text_area_width_pixels = base_image.width - (2 * MARGIN); avg_char_width = font_body.getlength("a"); wrap_width_chars = int(text_area_width_pixels / avg_char_width) if avg_char_width > 0 else 30
    def draw_text_block(text, font, spacing_after):
        nonlocal y_cursor
        wrapped_text = textwrap.fill(text, width=wrap_width_chars)
        draw.multiline_text((x_pos, y_cursor), wrapped_text, font=font, fill=TEXT_FILL_COLOR, spacing=LINE_SPACING_BODY, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
        block_height = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=LINE_SPACING_BODY)[3]
        y_cursor += block_height + spacing_after
    draw.text((x_pos, y_cursor), title, font=font_title, fill=TEXT_FILL_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
    y_cursor += FONT_SIZE_TITLE + 5
    draw.text((x_pos, y_cursor), date_str, font=font_date, fill=TEXT_FILL_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
    y_cursor += FONT_SIZE_DATE + 30
    draw_text_block(f" {refrao}", font_body, PARAGRAPH_SPACING)
    for paragraph in body_paragraphs:
        draw_text_block(f" {paragraph}", font_body, PARAGRAPH_SPACING)
    return base_image

def upload_to_cloudinary(file_path, public_id):
    # ... (sem alterações)
    logging.info(f"Fazendo upload do arquivo '{file_path}' para o Cloudinary...")
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
    except Exception as e:
        logging.error("ERRO: Credenciais do Cloudinary não encontradas."); exit()

    logging.info("Carregando modelo de IA (SD-Turbo)...")
    # Carrega o modelo SD-Turbo, que é mais leve
    pipe = DiffusionPipeline.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
    pipe = pipe.to("cpu")
    
    refrao_salmo, corpo_paragrafos = buscar_salmo_api()

    if refrao_salmo and corpo_paragrafos:
        prompt_visual = "A beautiful and serene landscape painting of lush green pastures next to calm, crystal-clear still waters. The sun is setting, casting a warm, golden light over the entire scene. Atmosphere is peaceful and deeply comforting. Style: detailed oil painting, soft brush strokes."
        logging.info("Gerando a imagem de fundo...")
        
        # Gera a imagem com parâmetros otimizados para o SD-Turbo
        base_image = pipe(
            prompt=prompt_visual, 
            num_inference_steps=1, 
            guidance_scale=0.0
        ).images[0]
        
        titulo = "Liturgia Diária - Salmo"
        data_hoje = datetime.now().strftime("%d de %B de %Y")
        
        final_image = compose_final_image(base_image, titulo, data_hoje, refrao_salmo, corpo_paragrafos)
        
        nome_arquivo_local = "salmo_do_dia.png"
        final_image.save(nome_arquivo_local)
        logging.info(f"Imagem temporária salva como '{nome_arquivo_local}'")

        public_id = f"salmos/salmo_{datetime.now().strftime('%Y_%m_%d')}"
        
        url_da_imagem_na_nuvem = upload_to_cloudinary(nome_arquivo_local, public_id)

        if url_da_imagem_na_nuvem:
            print(f"URL PÚBLICA: {url_da_imagem_na_nuvem}")
        else:
            print("Falha no upload.")
