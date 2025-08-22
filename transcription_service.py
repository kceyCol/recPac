"""
Serviço de transcrição de áudio
Separa as funcionalidades de transcrição do audio_processing.py
"""

import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os

class TranscriptionService:
    """Serviço para transcrição de áudio usando Speech Recognition"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Configurações otimizadas
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = 30
    
    def transcribe_audio(self, audio_path):
        """Transcreve áudio usando Speech Recognition com abordagem robusta"""
        try:
            print(f"🔍 Iniciando transcrição de: {audio_path}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(audio_path):
                return "[Erro: Arquivo de áudio não encontrado]"
            
            # Verificar tamanho do arquivo
            file_size = os.path.getsize(audio_path)
            print(f"📊 Tamanho do arquivo: {file_size} bytes")
            
            if file_size < 1000:  # Arquivo muito pequeno
                return "[Erro: Arquivo de áudio muito pequeno ou vazio]"
            
            print("📁 Processando arquivo de áudio...")
            
            # Processar áudio com pydub
            try:
                print("🔧 Carregando arquivo com pydub...")
                audio = AudioSegment.from_file(audio_path)
                
                # CORREÇÃO: Manter sample rate original para evitar problemas de velocidade
                original_frame_rate = audio.frame_rate
                print(f"🎵 Sample rate original: {original_frame_rate}Hz")
                
                # Normalizar áudio (sem alterar sample rate)
                audio = audio.normalize()
                
                # Converter para mono se necessário (sem alterar sample rate)
                if audio.channels > 1:
                    audio = audio.set_channels(1)
                
                # CORREÇÃO: Só alterar sample rate se for muito baixo (< 16kHz)
                # Isso evita problemas de velocidade com áudios gravados em alta qualidade
                if original_frame_rate < 16000:
                    audio = audio.set_frame_rate(16000)
                    print(f"🔧 Sample rate aumentado para 16kHz (era {original_frame_rate}Hz)")
                else:
                    print(f"✅ Mantendo sample rate original: {original_frame_rate}Hz")
                
                print(f"🎵 Áudio processado: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} canal(is)")
                
                # Se o áudio for muito longo (> 5 minutos), segmentar
                if len(audio) > 300000:  # 5 minutos em ms
                    return self._transcribe_long_audio_in_segments(audio, audio_path)
                
                # CORREÇÃO: Exportar para WAV temporário com configurações específicas para evitar problemas de velocidade
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    print(f"🔧 Exportando WAV temporário com configurações otimizadas...")
                    audio.export(temp_file.name, format="wav", parameters=[
                        "-acodec", "pcm_s16le",  # PCM 16-bit
                        "-ar", str(audio.frame_rate),  # Manter sample rate
                        "-ac", "1"  # Mono
                    ])
                    temp_path = temp_file.name
                
                try:
                    # Transcrever com speech_recognition
                    with sr.AudioFile(temp_path) as source:
                        print("🎤 Ajustando para ruído ambiente...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        
                        print("🎧 Carregando áudio...")
                        audio_data = self.recognizer.record(source)
                        
                        print("🔄 Iniciando transcrição...")
                        
                        # Tentar múltiplos engines
                        engines = [
                            ('google', lambda: self.recognizer.recognize_google(audio_data, language='pt-BR')),
                            ('sphinx', lambda: self.recognizer.recognize_sphinx(audio_data, language='pt-BR'))
                        ]
                        
                        for engine_name, recognize_func in engines:
                            try:
                                print(f"🔍 Tentando com {engine_name}...")
                                text = recognize_func()
                                if text and text.strip():
                                    print(f"✅ Transcrição bem-sucedida com {engine_name}!")
                                    return text
                            except sr.UnknownValueError:
                                print(f"⚠️ {engine_name}: Não foi possível entender o áudio")
                                continue
                            except sr.RequestError as e:
                                print(f"❌ {engine_name}: Erro na requisição: {e}")
                                continue
                            except Exception as e:
                                print(f"❌ {engine_name}: Erro inesperado: {e}")
                                continue
                        
                        return "[Erro: Não foi possível transcrever o áudio com nenhum engine]"
                    
                finally:
                    # Limpar arquivo temporário
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
            except Exception as e:
                print(f"❌ Erro no processamento com pydub: {e}")
                return f"[Erro no processamento de áudio: {str(e)}]"
        
        except Exception as e:
            print(f"❌ Erro geral na transcrição: {e}")
            return f"[Erro na transcrição: {str(e)}]"
    
    def _transcribe_long_audio_in_segments(self, audio, original_path):
        """Transcreve áudio longo dividindo em segmentos"""
        try:
            print("📝 Iniciando transcrição por segmentos...")
            
            segment_length = 30 * 1000  # 30 segundos em millisegundos
            overlap = 2 * 1000  # 2 segundos de sobreposição
            
            transcriptions = []
            total_duration = len(audio)
            
            for start in range(0, total_duration, segment_length - overlap):
                end = min(start + segment_length, total_duration)
                
                print(f"🎯 Processando segmento {start//1000}s - {end//1000}s")
                
                # Extrair segmento
                segment = audio[start:end]
                
                # Criar arquivo temporário para o segmento
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    segment.export(temp_path, format="wav")
                
                try:
                    with sr.AudioFile(temp_path) as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = self.recognizer.record(source)
                    
                    # Tentar transcrever o segmento
                    try:
                        segment_text = self.recognizer.recognize_google(audio_data, language="pt-BR")
                        if segment_text and segment_text.strip():
                            transcriptions.append(segment_text)
                            print(f"✅ Segmento transcrito: {segment_text[:30]}...")
                    except sr.UnknownValueError:
                        print(f"⚠️ Segmento não compreendido")
                    except sr.RequestError as e:
                        print(f"❌ Erro na requisição do segmento: {e}")
                
                finally:
                    # Limpar arquivo temporário
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            if transcriptions:
                full_transcription = " ".join(transcriptions)
                print(f"✅ Transcrição completa obtida: {len(full_transcription)} caracteres")
                return full_transcription
            else:
                return "[Erro: Não foi possível transcrever nenhum segmento do áudio]"
        
        except Exception as e:
            print(f"❌ Erro na transcrição por segmentos: {e}")
            return f"[Erro na transcrição por segmentos: {str(e)}]"
