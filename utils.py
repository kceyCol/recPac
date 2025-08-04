import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Configurações globais
RECORDINGS_DIR = 'recordings'
TRANSCRIPTIONS_DIR = 'transcriptions'
model = None

def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip()

def configure_gemini():
    global model
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini configurado com sucesso")
    else:
        model = None
        print("⚠️ AVISO: GEMINI_API_KEY não configurada no arquivo .env")

def create_directories():
    if not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)
        print(f"📁 Diretório {RECORDINGS_DIR} criado")
    if not os.path.exists(TRANSCRIPTIONS_DIR):
        os.makedirs(TRANSCRIPTIONS_DIR)
        # Verificar se TRANSCRIPTIONS_DIR está configurado corretamente
        print(f"Diretório de transcrições configurado: {TRANSCRIPTIONS_DIR}")
        print(f"Caminho absoluto: {os.path.abspath(TRANSCRIPTIONS_DIR)}")
        print(f"📁 Diretório {TRANSCRIPTIONS_DIR} criado")