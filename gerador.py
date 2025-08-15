# NOME DO ARQUIVO: gerador.py (Versão com Layout Adaptativo)

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

# --- CONFIGURAÇÕES DE DESIGN (AGORA SÃO OS VALORES MÁXIMOS) ---
# O script tentará usar estes valores, mas os reduzirá se o texto for muito longo.
TEXT_FILL_COLOR = (255, 255, 255); STROKE_COLOR = (0, 0, 0); STROKE_WIDTH = 2
FONT_FILE_UNIFIED = "Cookie-Regular.ttf"
FONT_SIZE_TITLE_MAX = 80
FONT_SIZE_DATE_MAX = 40
FONT_SIZE_BODY_MAX = 50
MIN_FONT_SIZE_BODY = 30 # Tamanho mínimo para garantir a legibilidade
LINE_SPACING_BODY_MAX = 15
PARAGRAPH_SPACING_MAX = 35
MARGIN = 80

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funções ---
def buscar_salmo_api():
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
    logging.info("Iniciando composição de imagem com layout adaptativo...")
    draw = ImageDraw.Draw(base_image)
    
    available_height = base_image.height - (2 * MARGIN)
    
    font_size_body = FONT_SIZE_BODY_MAX
    line_spacing = LINE_SPACING_BODY_MAX
    paragraph_spacing = PARAGRAPH_SPACING_MAX

    while font_size_body >= MIN_FONT_SIZE_BODY:
        try:
            font_title = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_TITLE_MAX)
            font_date = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_DATE_MAX)
            font_body = ImageFont.truetype(FONT_FILE_UNIFIED, font_size_body)
        except IOError:
            logging.error(f"Fonte '{FONT_FILE_UNIFIED}' não encontrada!"); return base_image

        y_cursor_temp = 150
        text_area_width_pixels = base_image.width - (2 * MARGIN)
        avg_char_width = font_body.getlength("a")
        wrap_width_chars = int(text_area_width_pixels / avg_char_width) if avg_char_width > 0 else 30
        
        total_text_height = 0
        
        total_text_height += FONT_SIZE_TITLE_MAX + 10 + FONT_SIZE_DATE_MAX + 60
        
        refrao_wrapped = textwrap.fill(f" {refrao}", width=wrap_width_chars)
        total_text_height += draw.multiline_textbbox((0,0), refrao_wrapped, font=font_body, spacing=line_spacing)[3] + paragraph_spacing

        for paragraph in body_paragraphs:
            para_wrapped = textwrap.fill(f" {paragraph}", width=wrap_width_chars)
            total_text_height += draw.multiline_textbbox((0,0), para_wrapped, font=font_body, spacing=line_spacing)[3] + paragraph_spacing
            
        if total_text_height <= available_height:
            logging.info(f"Layout calculado. Usando fonte tamanho {font_size_body}pt.")
            break
        else:
            font_size_body -= 2
            line_spacing = int(line_spacing * 0.95)
            paragraph_spacing = int(paragraph_spacing * 0.95)
            logging.warning(f"Texto muito longo. Tentando com fonte menor: {font_size_body}pt")
    else:
        logging.error(f"Mesmo com a fonte mínima ({MIN_FONT_SIZE_BODY}pt), o texto não coube na imagem.")

    y_cursor = 150
    x_pos = MARGIN
    def draw_text_block(text, font, spacing_after):
        nonlocal y_cursor
        wrapped_text = textwrap.fill(text, width=wrap_width_chars)
        draw.multiline_text((x_pos, y_cursor), wrapped_text, font=font, fill=TEXT_FILL_COLOR, spacing=line_spacing, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
        block_height = draw.multiline_textbbox((0,0), wrapped_text, font=font, spacing=line_spacing)[3]
        y_cursor += block_height + spacing_after

    draw.text((x_pos, y_cursor), title, font=font_title, fill=TEXT_FILL_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
    y_cursor += FONT_SIZE_TITLE_MAX + 10
    draw.text((x_pos, y_cursor), date_str, font=font_date, fill=TEXT_FILL_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
    y_cursor += FONT_SIZE_DATE_MAX + 60
    draw_text_block(f" {refrao}", font_body, paragraph_spacing)
    for paragraph in body_paragraphs:
        draw_text_block(f" {paragraph}", font_body, paragraph_spacing)
        
    return base_image

def upload_to_cloudinary(file_path, public_id):
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
    pipe = DiffusionPipeline.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
    pipe = pipe.to("cpu")
    
    refrao_salmo, corpo_paragrafos = buscar_salmo_api()

    if refrao_salmo and corpo_paragrafos:
        prompt_visual = (
            f"A beautiful and serene painting representing the spiritual concept of '{refrao_salmo}'. "
            "Atmosphere is peaceful and deeply comforting. "
            "Style: detailed oil painting, soft brush strokes, cinematic lighting. No people, no animals, no text."
        )
        
        logging.info("Gerando a imagem de fundo...")
        
        base_image = pipe(
            prompt=prompt_visual, 
            num_inference_steps=2,
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
