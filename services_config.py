"""
Configuração centralizada dos serviços
Centraliza as configurações dos módulos de serviço criados
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de diretórios
RECORDINGS_DIR = os.getenv('RECORDINGS_DIR', 'recordings')
TRANSCRIPTIONS_DIR = os.getenv('TRANSCRIPTIONS_DIR', 'transcriptions')

# Configurações do Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Configurações de transcrição
TRANSCRIPTION_TIMEOUT = int(os.getenv('TRANSCRIPTION_TIMEOUT', '30'))
TRANSCRIPTION_ENERGY_THRESHOLD = int(os.getenv('TRANSCRIPTION_ENERGY_THRESHOLD', '4000'))
TRANSCRIPTION_PAUSE_THRESHOLD = float(os.getenv('TRANSCRIPTION_PAUSE_THRESHOLD', '0.8'))

# Configurações de áudio
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '44100'))  # CORREÇÃO: Padrão 44.1kHz para evitar problemas de velocidade
AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', '1'))
AUDIO_SEGMENT_LENGTH = int(os.getenv('AUDIO_SEGMENT_LENGTH', '30000'))  # 30 segundos em ms
AUDIO_OVERLAP = int(os.getenv('AUDIO_OVERLAP', '2000'))  # 2 segundos em ms
AUDIO_MIN_SAMPLE_RATE = int(os.getenv('AUDIO_MIN_SAMPLE_RATE', '16000'))  # Sample rate mínimo para conversão

# Configurações de exportação
PDF_PAGE_SIZE = os.getenv('PDF_PAGE_SIZE', 'A4')
PDF_MARGIN = int(os.getenv('PDF_MARGIN', '72'))
PDF_TITLE_FONT_SIZE = int(os.getenv('PDF_TITLE_FONT_SIZE', '16'))
PDF_BODY_FONT_SIZE = int(os.getenv('PDF_BODY_FONT_SIZE', '11'))

# Configurações de sessão
SESSION_SEGMENT_PREFIX = os.getenv('SESSION_SEGMENT_PREFIX', 'segmento')
SESSION_METADATA_SUFFIX = os.getenv('SESSION_METADATA_SUFFIX', '_metadata.json')

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurações de segurança
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '104857600'))  # 100MB
ALLOWED_AUDIO_FORMATS = os.getenv('ALLOWED_AUDIO_FORMATS', 'wav,mp3,m4a,flac').split(',')

# Configurações de cache
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hora

# Configurações de rate limiting
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hora

def get_service_config():
    """Retorna configuração completa dos serviços"""
    return {
        'directories': {
            'recordings': RECORDINGS_DIR,
            'transcriptions': TRANSCRIPTIONS_DIR
        },
        'gemini': {
            'api_key': GEMINI_API_KEY,
            'model': GEMINI_MODEL
        },
        'transcription': {
            'timeout': TRANSCRIPTION_TIMEOUT,
            'energy_threshold': TRANSCRIPTION_ENERGY_THRESHOLD,
            'pause_threshold': TRANSCRIPTION_PAUSE_THRESHOLD
        },
        'audio': {
            'sample_rate': AUDIO_SAMPLE_RATE,
            'channels': AUDIO_CHANNELS,
            'segment_length': AUDIO_SEGMENT_LENGTH,
            'overlap': AUDIO_OVERLAP,
            'min_sample_rate': AUDIO_MIN_SAMPLE_RATE
        },
        'export': {
            'pdf_page_size': PDF_PAGE_SIZE,
            'pdf_margin': PDF_MARGIN,
            'pdf_title_font_size': PDF_TITLE_FONT_SIZE,
            'pdf_body_font_size': PDF_BODY_FONT_SIZE
        },
        'session': {
            'segment_prefix': SESSION_SEGMENT_PREFIX,
            'metadata_suffix': SESSION_METADATA_SUFFIX
        },
        'logging': {
            'level': LOG_LEVEL,
            'format': LOG_FORMAT
        },
        'security': {
            'max_file_size': MAX_FILE_SIZE,
            'allowed_audio_formats': ALLOWED_AUDIO_FORMATS
        },
        'cache': {
            'enabled': CACHE_ENABLED,
            'ttl': CACHE_TTL
        },
        'rate_limit': {
            'enabled': RATE_LIMIT_ENABLED,
            'requests': RATE_LIMIT_REQUESTS,
            'window': RATE_LIMIT_WINDOW
        }
    }

def validate_config():
    """Valida se as configurações estão corretas"""
    errors = []
    
    # Verificar diretórios
    if not os.path.exists(RECORDINGS_DIR):
        try:
            os.makedirs(RECORDINGS_DIR, exist_ok=True)
        except Exception as e:
            errors.append(f"Erro ao criar diretório de gravações: {e}")
    
    if not os.path.exists(TRANSCRIPTIONS_DIR):
        try:
            os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
        except Exception as e:
            errors.append(f"Erro ao criar diretório de transcrições: {e}")
    
    # Verificar configurações críticas
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY não configurada")
    
    if TRANSCRIPTION_TIMEOUT <= 0:
        errors.append("TRANSCRIPTION_TIMEOUT deve ser maior que 0")
    
    if AUDIO_SAMPLE_RATE <= 0:
        errors.append("AUDIO_SAMPLE_RATE deve ser maior que 0")
    
    return errors

def print_config_summary():
    """Imprime um resumo das configurações"""
    config = get_service_config()
    
    print("🔧 Configuração dos Serviços RecPac")
    print("=" * 50)
    
    print(f"📁 Diretórios:")
    print(f"   Gravações: {config['directories']['recordings']}")
    print(f"   Transcrições: {config['directories']['transcriptions']}")
    
    print(f"\n🤖 Gemini AI:")
    print(f"   Modelo: {config['gemini']['model']}")
    print(f"   API Key: {'✅ Configurada' if config['gemini']['api_key'] else '❌ Não configurada'}")
    
    print(f"\n🎵 Transcrição:")
    print(f"   Timeout: {config['transcription']['timeout']}s")
    print(f"   Energy Threshold: {config['transcription']['energy_threshold']}")
    print(f"   Pause Threshold: {config['transcription']['pause_threshold']}")
    
    print(f"\n🔊 Áudio:")
    print(f"   Sample Rate: {config['audio']['sample_rate']}Hz")
    print(f"   Canais: {config['audio']['channels']}")
    print(f"   Segment Length: {config['audio']['segment_length']}ms")
    
    print(f"\n📄 Exportação:")
    print(f"   PDF Page Size: {config['export']['pdf_page_size']}")
    print(f"   PDF Margin: {config['export']['pdf_margin']}pt")
    
    print(f"\n⚙️ Sistema:")
    print(f"   Cache: {'✅ Habilitado' if config['cache']['enabled'] else '❌ Desabilitado'}")
    print(f"   Rate Limit: {'✅ Habilitado' if config['rate_limit']['enabled'] else '❌ Desabilitado'}")
    
    print("=" * 50)

if __name__ == "__main__":
    # Validar configurações
    errors = validate_config()
    
    if errors:
        print("❌ Erros de configuração encontrados:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configurações válidas!")
        print_config_summary()
