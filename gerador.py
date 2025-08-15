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
