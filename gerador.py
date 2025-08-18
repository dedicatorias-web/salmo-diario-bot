# NOME DO FICHEIRO: gerador.py (Versão com correção no upload)

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

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# --- CONFIGURAÇÕES DE DESIGN ---
TEXT_COLOR_HEADER = (0, 0, 0)
TEXT_COLOR_BODY = (255, 255, 255)
STROKE_COLOR = (80, 80, 80, 150)
STROKE_WIDTH = 2
CARD_OPACITY = 160
FONT_FILE_UNIFIED = "Cookie-Regular.ttf"
FONT_SIZE_TITLE = 90; FONT_SIZE_SUBTITLE = 50; FONT_SIZE_DATE = 40
FONT_SIZE_SALMO_HEADER = 55; FONT_SIZE_BODY = 45
LINE_SPACING_BODY = 15; PARAGRAPH_SPACING = 30

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
    background = base_image.filter(ImageFilter.GaussianBlur(radius=3))
    draw = ImageDraw.Draw(background)
    try:
        font_title = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_TITLE)
        font_subtitle = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_SUBTITLE)
        font_date = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_DATE)
        font_salmo_header = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_SALMO_HEADER)
        font_body = ImageFont.truetype(FONT_FILE_UNIFIED, FONT_SIZE_BODY)
    except IOError:
        logging.error(f"Fonte '{FONT_FILE_UNIFIED}' não encontrada!")
        return base_image
    y_cursor = 60
    draw.text((background.width / 2 + 2, y_cursor + 2), title, font=font_title, fill=STROKE_COLOR, anchor="mt")
    draw.text((background.width / 2, y_cursor), title, font=font_title, fill=TEXT_COLOR_HEADER, anchor="mt")
    y_cursor += FONT_SIZE_TITLE
    draw.text((background.width / 2 + 1, y_cursor + 1), subtitle, font=font_subtitle, fill=STROKE_COLOR, anchor="mt")
    draw.text((background.width / 2, y_cursor), subtitle, font=font_subtitle, fill=TEXT_COLOR_HEADER, anchor="mt")
    margin_right = 40
    draw.text((background.width - margin_right, 60), date_str, font=font_date, fill=TEXT_COLOR_HEADER, anchor="ra")
    card_height = int(background.height * 0.6); card_margin = 40
    card_area = [(card_margin, background.height - card_height), (background.width - card_margin, background.height - card_margin)]
    overlay = Image.new('RGBA', background.size, (0,0,0,0)); draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.rounded_rectangle(card_area, fill=(0, 0, 0, CARD_OPACITY), radius=20)
    background = Image.alpha_composite(background.convert('RGBA'), overlay).convert('RGB'); draw = ImageDraw.Draw(background)
    y_cursor = background.height - card_height + 40; x_pos = card_margin + 40; text_area_width_pixels = background.width - (2 * (card_margin + 40))
    avg_char_width = font_body.getlength("a"); wrap_width_chars = int(text_area_width_pixels / avg_char_width) if avg_char_width > 0 else 35
    draw.text((x_pos, y_cursor), salmo_title, font=font_salmo_header, fill=TEXT_COLOR_BODY)
    y_cursor += FONT_SIZE_SALMO_HEADER + PARAGRAPH_SPACING
    refrao_wrapped = textwrap.fill(refrao, width=wrap_width_chars)
    draw.multiline_text((x_pos, y_cursor), refrao_wrapped, font=font_body, fill=TEXT_COLOR_BODY, spacing=LINE_SPACING_BODY)
    y_cursor += draw.multiline_textbbox((0,0), refrao_wrapped, font=font_body, spacing=LINE_SPACING_BODY)[3] + PARAGRAPH_SPACING
    for paragraph in body_paragraphs:
        para_wrapped = textwrap.fill(paragraph, width=wrap_width_chars)
        draw.multiline_text((x_pos, y_cursor), para_wrapped, font=font_body, fill=TEXT_COLOR_BODY, spacing=LINE_SPACING_BODY)
        y_cursor += draw.multiline_textbbox((0,0), para_wrapped, font=font_body, spacing=LINE_SPACING_BODY)[3] + PARAGRAPH_SPACING
    return background

# ===============================================
# FUNÇÃO CORRIGIDA AQUI
# ===============================================
def upload_to_cloudinary(file_path, public_id):
    """Faz o upload de um ficheiro para o Cloudinary e retorna a URL segura."""
    logging.info(f"A fazer o upload do ficheiro '{file_path}' para o Cloudinary...")
    try:
        upload_result = cloudinary.uploader.upload(file_path, public_id=public_id, overwrite=True)
        secure_url = upload_result.get('secure_url')
        if secure_url:
            logging.info(f"Upload bem-sucedido! URL segura: {secure_url}")
            return secure_url
        else:
            logging.error("Falha no upload: Nenhuma URL segura retornada.")
            return None
    except Exception as e:
        logging.error(f"Erro durante o upload para o Cloudinary: {e}")
        return None
# ===============================================

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

    titulo_salmo, refrao_salmo, corpo_paragrafos = buscar_salmo_api()

    if refrao_salmo and corpo_paragrafos:
        prompt_visual = f"Uma pintura digital cinematográfica e serena que representa o conceito espiritual de '{refrao_salmo}'. A atmosfera deve ser pacífica e reconfortante, com iluminação suave e etérea, cores suaves. Estilo de arte detalhado e inspirador."
        base_image = gerar_imagem_com_google_ai(prompt_visual)
        if base_image:
            titulo = "Liturgia Diária"; subtitulo = "Prova de Amor"; data_hoje = datetime.now().strftime("%d de %B de %Y")
            final_image = compose_final_image(base_image, titulo, subtitulo, data_hoje, titulo_salmo, refrao_salmo, corpo_paragrafos)
            nome_arquivo_local = "salmo_do_dia.png"
            final_image.save(nome_arquivo_local)
            logging.info(f"Imagem temporária guardada como '{nome_arquivo_local}'")
            public_id = f"salmos/salmo_{datetime.now().strftime('%Y_%m_%d')}"
            url_da_imagem_na_nuvem = upload_to_cloudinary(nome_arquivo_local, public_id)
            if url_da_imagem_na_nuvem:
                print(f"URL PÚBLICA: {url_da_imagem_na_nuvem}")
            else:
                print("Falha no upload.")
