# NOME DO FICHEIRO: gerador.py (Versão com Estilo Caravaggio Reforçado)

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
from vertexai.preview.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

# --- CONFIGURAÇÕES DE DESIGN ---
# Aumentamos a opacidade do cartão e escurecemos o stroke para combinar com o estilo Caravaggio
TEXT_COLOR_HEADER = (255, 255, 255); TEXT_COLOR_BODY = (255, 255, 255)
STROKE_COLOR = (0, 0, 0, 200); STROKE_WIDTH = 2; CARD_OPACITY = 190 # Mais opaco
FONT_FILE_UNIFIED = "Cookie-Regular.ttf"
FONT_SIZE_TITLE = 90; FONT_SIZE_SUBTITLE = 50; FONT_SIZE_DATE = 40
FONT_SIZE_SALMO_HEADER = 55; FONT_SIZE_BODY = 45
LINE_SPACING_BODY = 15; PARAGRAPH_SPACING = 30

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funções ---
def buscar_salmo_api():
    # ... (sem alterações)
    URL = "https://liturgia.up.railway.app/"; logging.info("Buscando o salmo na API...")
    try:
        response = requests.get(URL, timeout=15); response.raise_for_status()
        dados = response.json(); salmo_dados = dados.get('salmo')
        if salmo_dados and 'refrao' in salmo_dados and 'texto' in salmo_dados:
            paragrafos = salmo_dados['texto'].split('\n'); paragrafos_limpos = [p.strip() for p in paragrafos if p.strip()]
            titulo_salmo = salmo_dados.get('titulo', 'Salmo'); texto_completo = salmo_dados['texto']
            return titulo_salmo, salmo_dados['refrao'], paragrafos_limpos, texto_completo
        return None, None, None, None
    except Exception as e:
        logging.error(f"Erro ao buscar salmo: {e}"); return None, None, None, None

# =================================================================
# FUNÇÃO ATUALIZADA COM INSTRUÇÕES DETALHADAS DE ESTILO
# =================================================================
def gerar_prompt_com_gemini(texto_do_salmo):
    """Usa o Gemini para analisar o Salmo e criar um prompt de imagem no estilo de Caravaggio."""
    logging.info("Enviando texto do Salmo para o Gemini para gerar um prompt estilo Caravaggio...")
    try:
        model = GenerativeModel("gemini-1.0-pro")
        
        instrucao = (
            "INSTRUÇÕES PARA A IA:\n"
            "1. Analisa o Salmo fornecido e identifica o seu tema central e a imagem visual mais poderosa.\n"
            "2. Cria um prompt em INGLÊS para uma IA de geração de imagem. O objetivo é criar uma obra de arte digital no estilo do pintor barroco Michelangelo Merisi da Caravaggio.\n"
            "3. O prompt deve obrigatoriamente incluir os seguintes elementos estilísticos:\n"
            "   - Caravaggio\n"
            "   - barroco\n"
            "   - **Tenebrism and Chiaroscuro:** Descreve uma cena a emergir de um fundo muito escuro ou preto, iluminada por uma única fonte de luz forte e direcional, criando sombras profundas e dramáticas.\n"
            "   - **Intense Realism:** Foca em texturas realistas e detalhes crus (rocha, terra, água, luz).\n"
            "   - **Dramatic Moment:** Captura um momento de alta intensidade emocional ou espiritual, não uma cena passiva.\n"
            "   - **Limited Palette:** Menciona o uso de tons terrosos, ocres, vermelhos profundos e a ausência de cores excessivamente brilhantes.\n"
            #"4. O prompt NÃO deve incluir figuras humanas ou anjos. Deve traduzir o tema do Salmo em uma cena simbólica ou de natureza (por exemplo, uma luz a rasgar a escuridão, uma rocha a ser atingida por um raio de sol, etc.).\n"
            "5. O resultado final deve ser apenas o texto do prompt em inglês, nada mais.\n\n"
            f"SALMO PARA ANÁLISE:\n{texto_do_salmo}"
        )
        
        response = model.generate_content(instrucao)
        prompt_gerado = response.text.strip().replace("*", "") # Remove quaisquer asteriscos de formatação
        
        logging.info(f"Prompt gerado pelo Gemini: {prompt_gerado}")
        return prompt_gerado

    except Exception as e:
        logging.error(f"Erro ao gerar prompt com o Gemini: {e}")
        return "An oil painting in the style of Caravaggio. A single, dramatic beam of divine light breaks through a dark, cloudy sky, illuminating a rugged, ancient rock. The scene uses intense chiaroscuro and tenebrism, with deep black shadows and a limited palette of earthy tones."

def gerar_imagem_com_google_ai(prompt):
    # ... (sem alterações)
    logging.info("Enviando prompt para a API do Google AI (Imagen)...")
    try:
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        response = model.generate_images(
            prompt=prompt, number_of_images=1, aspect_ratio="9:16",
            negative_prompt="cartoon, anime, text, words, letters, ugly, poor quality, deformed, people, animals"
        )
        image_bytes = response.images[0]._image_bytes
        logging.info("Imagem recebida com sucesso do Google AI!")
        return Image.open(BytesIO(image_bytes))
    except Exception as e:
        logging.error(f"Erro ao gerar imagem com a API do Google: {e}")
        return None

def compose_final_image(base_image, title, subtitle, date_str, salmo_title, refrao, body_paragraphs):
    # ... (sem alterações)
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
        logging.error(f"Fonte '{FONT_FILE_UNIFIED}' não encontrada!"); return base_image
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

def upload_to_cloudinary(file_path, public_id):
    # ... (sem alterações)
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
    # ... (sem alterações)
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        logging.warning("Locale 'pt_BR.UTF-8' não disponível.")
    project_id = os.getenv('GCP_PROJECT_ID');
    if not project_id:
        logging.error("ERRO: ID do projeto Google (GCP_PROJECT_ID) não encontrado."); exit()
    vertexai.init(project=project_id, location="us-central1")
    try:
        cloudinary.config(cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'), api_key=os.getenv('CLOUDINARY_API_KEY'), api_secret=os.getenv('CLOUDINARY_API_SECRET'))
        logging.info("Credenciais do Cloudinary configuradas.")
    except Exception:
        logging.error("ERRO: Credenciais do Cloudinary não encontradas."); exit()
    titulo_salmo, refrao_salmo, corpo_paragrafos, texto_completo_salmo = buscar_salmo_api()
    if texto_completo_salmo:
        prompt_visual = gerar_prompt_com_gemini(texto_completo_salmo)
        base_image = gerar_imagem_com_google_ai(prompt_visual)
        if base_image:
            titulo = "Liturgia Diária"; subtitulo = "Prova de Amor"; data_hoje = datetime.now().strftime("%d de %B de %Y")
            final_image = compose_final_image(base_image, titulo, subtitulo, data_hoje, titulo_salmo, refrao_salmo, corpo_paragrafos)
            nome_arquivo_local = "salmo_do_dia.png"; final_image.save(nome_arquivo_local)
            logging.info(f"Imagem temporária guardada como '{nome_arquivo_local}'")
            public_id = f"salmos/salmo_{datetime.now().strftime('%Y_%m_%d')}"
            url_da_imagem_na_nuvem = upload_to_cloudinary(nome_arquivo_local, public_id)
            if url_da_imagem_na_nuvem:
                print(f"URL PÚBLICA: {url_da_imagem_na_nuvem}")
            else:
                print("Falha no upload.")
