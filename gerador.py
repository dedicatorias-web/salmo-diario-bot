# NOME DO FICHEIRO: gerador.py (Versão Final com Narração Google Cloud)

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
from google.cloud import texttospeech # Biblioteca para narração

# --- CONFIGURAÇÕES DE DESIGN ---
# ... (as configurações de design permanecem as mesmas)
TEXT_COLOR_HEADER = (0, 0, 0); TEXT_COLOR_BODY = (255, 255, 255)
STROKE_COLOR = (80, 80, 80, 150); STROKE_WIDTH = 2; CARD_OPACITY = 160
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
            titulo_salmo = salmo_dados.get('titulo', 'Salmo'); texto_completo = f"{titulo_salmo}. {salmo_dados['refrao']}. {salmo_dados['texto']}"
            return titulo_salmo, salmo_dados['refrao'], paragrafos_limpos, texto_completo
        return None, None, None, None
    except Exception as e:
        logging.error(f"Erro ao buscar salmo: {e}"); return None, None, None, None

# =================================================================
# NOVA FUNÇÃO PARA GERAR A NARRAÇÃO
# =================================================================
def gerar_narracao_com_google_ai(texto_para_narrar, nome_ficheiro_saida):
    """Gera um ficheiro de áudio a partir do texto usando a API Google Cloud TTS."""
    logging.info("A enviar texto para a API Google Cloud Text-to-Speech...")
    try:
        # Instancia um cliente
        client = texttospeech.TextToSpeechClient()

        # Define o input do texto
        synthesis_input = texttospeech.SynthesisInput(text=texto_para_narrar)

        # Configura a voz (pt-BR, WaveNet, Feminina)
        voice = texttospeech.VoiceSelectionParams(
            language_code="pt-BR",
            name="pt-BR-Wavenet-B"
        )

        # Configura o tipo de áudio (MP3)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Realiza o pedido de síntese de texto
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # O conteúdo de áudio da resposta é binário
        with open(nome_ficheiro_saida, "wb") as out:
            out.write(response.audio_content)
            logging.info(f'Narração gerada e guardada como "{nome_ficheiro_saida}"')
        
        return True
    except Exception as e:
        logging.error(f"Erro ao gerar narração com a API do Google: {e}")
        return False

def gerar_prompt_com_gemini(texto_do_salmo):
    # ... (sem alterações)
    pass # O código desta função está omitido para brevidade

def gerar_imagem_com_google_ai(prompt):
    # ... (sem alterações)
    pass # O código desta função está omitido para brevidade

def compose_final_image(base_image, title, subtitle, date_str, salmo_title, refrao, body_paragraphs):
    # ... (sem alterações)
    pass # O código desta função está omitido para brevidade

def upload_to_cloudinary(file_path, public_id, resource_type="image"):
    """Faz o upload de um ficheiro (imagem ou áudio) para o Cloudinary."""
    logging.info(f"A fazer o upload do ficheiro '{file_path}' ({resource_type}) para o Cloudinary...")
    try:
        upload_result = cloudinary.uploader.upload(
            file_path, 
            public_id=public_id, 
            overwrite=True, 
            resource_type=resource_type
        )
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
    
    project_id = os.getenv('GCP_PROJECT_ID')
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
        # GERAÇÃO DA IMAGEM (como antes)
        prompt_visual = gerar_prompt_com_gemini(texto_completo_salmo)
        base_image = gerar_imagem_com_google_ai(prompt_visual)
        
        # GERAÇÃO DA NARRAÇÃO (novo passo)
        nome_narracao_local = "narracao_do_dia.mp3"
        narracao_sucesso = gerar_narracao_com_google_ai(texto_completo_salmo, nome_narracao_local)
        
        if base_image:
            titulo = "Liturgia Diária"; subtitulo = "Prova de Amor"; data_hoje = datetime.now().strftime("%d de %B de %Y")
            final_image = compose_final_image(base_image, titulo, subtitulo, data_hoje, titulo_salmo, refrao_salmo, corpo_paragrafos)
            
            nome_imagem_local = "salmo_do_dia.png"
            final_image.save(nome_imagem_local)
            
            # FAZ UPLOAD DE AMBOS OS FICHEIROS
            public_id_base = f"salmos/salmo_{datetime.now().strftime('%Y_%m_%d')}"
            
            url_imagem = upload_to_cloudinary(nome_imagem_local, public_id_base, resource_type="image")
            
            url_narracao = None
            if narracao_sucesso:
                url_narracao = upload_to_cloudinary(nome_narracao_local, public_id_base, resource_type="video") # Áudio é tratado como "video" no Cloudinary
            
            if url_imagem:
                print(f"URL PÚBLICA DA IMAGEM: {url_imagem}")
            if url_narracao:
                print(f"URL PÚBLICA DA NARRAÇÃO: {url_narracao}")
