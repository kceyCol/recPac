# 🛠️ Guia de Troubleshooting - RecPac

Este guia ajuda a resolver problemas comuns relacionados ao processamento de áudio no RecPac.

## 🎵 Problemas de Áudio

### **1. Áudio Reproduzindo Lento**

#### **Sintomas:**
- Áudio gravado soa mais lento que o normal
- Transcrição falha ou é imprecisa
- Duração do arquivo parece incorreta

#### **Causas Possíveis:**
1. **Sample rate incorreto** durante processamento
2. **Formato de arquivo não reconhecido**
3. **Conversão inadequada** de WebM/Opus para WAV

#### **Soluções:**
1. **Verificar logs da aplicação:**
   ```bash
   # Procurar por estas mensagens:
   🎯 Formato detectado: [FORMATO]
   🎵 Sample rate original: [X]Hz
   ✅ Mantendo sample rate original: [X]Hz
   ```

2. **Confirmar formato do arquivo:**
   ```bash
   # Verificar se o arquivo WAV é válido:
   python -c "import wave; w = wave.open('arquivo.wav', 'rb'); print(f'Frame Rate: {w.getframerate()}Hz')"
   ```

3. **Verificar cabeçalho do arquivo:**
   ```python
   # Usar a função de detecção:
   from audio_processing import detect_audio_format_robust
   
   with open('arquivo.wav', 'rb') as f:
       audio_bytes = f.read()
   format_detected = detect_audio_format_robust(audio_bytes)
   print(f"Formato detectado: {format_detected}")
   ```

### **2. Transcrição Falha**

#### **Sintomas:**
- Mensagem: "Não foi possível transcrever o áudio"
- Erro: "missing PocketSphinx module"
- Transcrição retorna texto vazio ou incorreto

#### **Soluções:**
1. **Verificar qualidade do áudio:**
   - Confirmar se o arquivo tem tamanho adequado (> 1KB)
   - Verificar se não está corrompido

2. **Verificar formato de áudio:**
   - Usar `detect_audio_format_robust()` para identificar formato
   - Confirmar se o pydub consegue carregar o arquivo

3. **Verificar dependências:**
   ```bash
   # Instalar dependências necessárias:
   pip install SpeechRecognition pydub
   
   # Para PocketSphinx (opcional):
   pip install pocketsphinx
   ```

### **3. Formato de Arquivo Não Reconhecido**

#### **Sintomas:**
- Log mostra: "Formato Desconhecido (tentando processar)"
- Processamento falha com erro de formato
- Arquivo salvo sem processamento (fallback)

#### **Soluções:**
1. **Adicionar novo formato na função de detecção:**
   ```python
   # Em detect_audio_format_robust(), adicionar:
   if header.startswith(b'SEU_CABEÇALHO'):
       return "SEU_FORMATO"
   ```

2. **Verificar cabeçalho do arquivo:**
   ```python
   with open('arquivo', 'rb') as f:
       header = f.read(12)
       print(f"Cabeçalho (hex): {header.hex()}")
       print(f"Cabeçalho (ascii): {header}")
   ```

3. **Usar fallback genérico:**
   - A função já inclui fallback para formatos não reconhecidos
   - Arquivo será salvo sem processamento se necessário

### **4. Problemas de Compatibilidade com Dispositivos**

#### **Sintomas:**
- Gravação funciona em um dispositivo mas falha em outro
- Formatos diferentes geram problemas diferentes
- Inconsistência entre iOS, Android e Desktop

#### **Soluções:**
1. **Verificar formato específico do dispositivo:**
   - **iOS**: Geralmente M4A/AAC ou MP3
   - **Android**: Geralmente WebM/Opus ou MP3
   - **Desktop**: Geralmente WAV ou MP3

2. **Testar com diferentes navegadores:**
   - Chrome: WebM/Opus
   - Firefox: WebM/Opus
   - Safari: M4A/AAC
   - Edge: WebM/Opus

3. **Verificar configurações do MediaRecorder:**
   ```javascript
   // Configurações recomendadas:
   const options = {
       mimeType: 'audio/webm;codecs=opus',
       audioBitsPerSecond: 128000,
       sampleRate: 44100
   };
   ```

## 🔍 Debugging Avançado

### **1. Logs Detalhados**

#### **Ativar logs verbosos:**
```python
# Em audio_processing.py, adicionar:
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **Logs importantes para monitorar:**
```
🔍 Processando áudio: [X] bytes
🎯 Formato detectado: [FORMATO]
✅ Áudio carregado com pydub: [X]Hz, [X] canais
🎵 Processando áudio: [X]Hz, [X] canais, [X]ms
✅ Mantendo sample rate original: [X]Hz
🔧 Volume normalizado
✅ Duração preservada: [X]ms
🔧 Exportando WAV com configurações otimizadas...
✅ Gravação processada e salva: [filename] ([X] bytes)
```

### **2. Verificação de Arquivos**

#### **Script de análise de áudio:**
```python
import os
import pydub
from pydub import AudioSegment

def analyze_audio_file(file_path):
    """Analisa um arquivo de áudio para debugging"""
    print(f"=== Analisando: {os.path.basename(file_path)} ===")
    
    try:
        # Verificar tamanho
        file_size = os.path.getsize(file_path)
        print(f"Tamanho: {file_size} bytes")
        
        # Carregar com pydub
        audio = AudioSegment.from_file(file_path)
        print(f"Duração: {len(audio)}ms")
        print(f"Frame Rate: {audio.frame_rate}Hz")
        print(f"Canais: {audio.channels}")
        print(f"Sample Width: {audio.sample_width} bytes")
        
        # Verificar se é WAV válido
        if file_path.endswith('.wav'):
            try:
                import wave
                with wave.open(file_path, 'rb') as wav_file:
                    print(f"WAV Frame Rate: {wav_file.getframerate()}Hz")
                    print(f"WAV Canais: {wav_file.getnchannels()}")
                    print(f"WAV Sample Width: {wav_file.getsampwidth()}")
            except Exception as e:
                print(f"❌ Erro ao ler WAV: {e}")
                
    except Exception as e:
        print(f"❌ Erro ao analisar: {e}")

# Uso:
analyze_audio_file("caminho/para/arquivo.wav")
```

### **3. Teste de Processamento**

#### **Script de teste de compatibilidade:**
```python
from audio_processing import detect_audio_format_robust, process_audio_for_device_compatibility
from pydub import AudioSegment
import io

def test_audio_processing(audio_bytes):
    """Testa o processamento de áudio para debugging"""
    print("=== Teste de Processamento ===")
    
    # 1. Detectar formato
    format_detected = detect_audio_format_robust(audio_bytes)
    print(f"Formato detectado: {format_detected}")
    
    # 2. Tentar carregar com pydub
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        print(f"✅ Pydub carregou: {audio_segment.frame_rate}Hz, {audio_segment.channels} canais")
        
        # 3. Testar processamento
        processed_audio = process_audio_for_device_compatibility(audio_segment, format_detected)
        print(f"✅ Processamento concluído: {processed_audio.frame_rate}Hz, {processed_audio.channels} canais")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        return False

# Uso:
with open("arquivo", "rb") as f:
    audio_bytes = f.read()
test_audio_processing(audio_bytes)
```

## 🚨 Problemas Críticos

### **1. Aplicação Não Inicia**

#### **Soluções:**
1. **Verificar dependências Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verificar porta 5000:**
   ```bash
   netstat -an | findstr :5000
   ```

3. **Verificar logs de erro:**
   ```bash
   python app.py
   ```

### **2. Erro de Importação**

#### **Soluções:**
1. **Verificar estrutura de arquivos:**
   ```bash
   ls -la
   ```

2. **Verificar imports em audio_processing.py:**
   ```python
   # Imports necessários:
   from flask import Blueprint, request, jsonify, session, send_file, render_template
   import os
   import base64
   import random
   from datetime import datetime
   import speech_recognition as sr
   from pydub import AudioSegment
   import tempfile
   import io
   from auth import login_required
   from utils import sanitize_filename, model, RECORDINGS_DIR, TRANSCRIPTIONS_DIR
   ```

## 📞 Suporte

### **Informações para Reportar Problemas:**
1. **Versão da aplicação**
2. **Sistema operacional**
3. **Dispositivo usado para gravação**
4. **Navegador (se aplicável)**
5. **Logs de erro completos**
6. **Arquivo de áudio problemático** (se possível)

### **Arquivos de Log Importantes:**
- **Terminal onde app.py está rodando**
- **AUDIO_FIXES_DOCUMENTATION.md** para referência
- **CHANGELOG.md** para histórico de mudanças

---

**Última Atualização:** 22/08/2025  
**Versão:** 1.0  
**Status:** ✅ Ativo
