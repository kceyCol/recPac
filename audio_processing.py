from flask import Blueprint, request, jsonify, session, send_file, render_template
import os
import base64
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Inches
import time
import io
from auth import login_required
from utils import sanitize_filename, model, RECORDINGS_DIR, TRANSCRIPTIONS_DIR

audio_bp = Blueprint('audio', __name__)

# ==================== FUNÇÕES DE TRANSCRIÇÃO ====================

def transcribe_audio_with_speech_recognition(audio_path):
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
        
        recognizer = sr.Recognizer()
        
        # Configurações otimizadas
        recognizer.energy_threshold = 4000
        recognizer.dynamic_energy_threshold = False
        recognizer.pause_threshold = 0.8
        recognizer.operation_timeout = 30
        
        print("📁 Processando arquivo de áudio...")
        
        # Processar áudio com pydub
        try:
            print("🔧 Carregando arquivo com pydub...")
            audio = AudioSegment.from_file(audio_path)
            
            # Normalizar áudio
            audio = audio.normalize()
            
            # Converter para mono se necessário
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Definir sample rate padrão
            audio = audio.set_frame_rate(16000)
            
            print(f"🎵 Áudio processado: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} canal(is)")
            
            # Se o áudio for muito longo (> 5 minutos), segmentar
            if len(audio) > 300000:  # 5 minutos em ms
                return transcribe_long_audio_in_segments(audio, audio_path)
            
            # Exportar para WAV temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio.export(temp_file.name, format="wav")
                temp_path = temp_file.name
            
            try:
                # Transcrever com speech_recognition
                with sr.AudioFile(temp_path) as source:
                    print("🎤 Ajustando para ruído ambiente...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    print("🎧 Carregando áudio...")
                    audio_data = recognizer.record(source)
                    
                    print("🔄 Iniciando transcrição...")
                    
                    # Tentar múltiplos engines
                    engines = [
                        ('google', lambda: recognizer.recognize_google(audio_data, language='pt-BR')),
                        ('sphinx', lambda: recognizer.recognize_sphinx(audio_data, language='pt-BR'))
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
                    
                    return "[Não foi possível transcrever o áudio. Verifique a qualidade da gravação.]"
                    
            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Erro ao processar áudio com pydub: {e}")
            return f"[Erro ao processar áudio: {str(e)}]"
            
    except Exception as e:
        print(f"❌ Erro geral na transcrição: {e}")
        return f"[Erro na transcrição: {str(e)}]"

def transcribe_long_audio_in_segments(audio, original_path):
    """Transcreve áudio longo dividindo em segmentos"""
    try:
        print("📏 Áudio longo detectado, dividindo em segmentos...")
        
        segment_length = 240000  # 4 minutos em ms
        overlap = 5000  # 5 segundos de sobreposição
        
        segments = []
        start = 0
        
        while start < len(audio):
            end = min(start + segment_length, len(audio))
            segment = audio[start:end]
            segments.append(segment)
            start = end - overlap
            
            if start >= len(audio):
                break
        
        print(f"📊 Dividido em {len(segments)} segmentos")
        
        full_transcription = []
        recognizer = sr.Recognizer()
        
        for i, segment in enumerate(segments):
            print(f"🔄 Processando segmento {i+1}/{len(segments)}...")
            
            try:
                # Exportar segmento para arquivo temporário
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    segment.export(temp_file.name, format="wav")
                    temp_path = temp_file.name
                
                try:
                    with sr.AudioFile(temp_path) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = recognizer.record(source)
                        
                        try:
                            text = recognizer.recognize_google(audio_data, language='pt-BR')
                            if text and text.strip():
                                full_transcription.append(text)
                                print(f"✅ Segmento {i+1} transcrito com sucesso")
                        except sr.UnknownValueError:
                            print(f"⚠️ Segmento {i+1}: Não foi possível entender")
                            full_transcription.append("[Trecho inaudível]")
                        except sr.RequestError as e:
                            print(f"❌ Segmento {i+1}: Erro na requisição: {e}")
                            full_transcription.append("[Erro na transcrição]")
                            
                finally:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
            except Exception as e:
                print(f"❌ Erro no segmento {i+1}: {e}")
                full_transcription.append("[Erro no processamento]")
        
        result = " ".join(full_transcription)
        print(f"✅ Transcrição completa finalizada: {len(result)} caracteres")
        return result
        
    except Exception as e:
        print(f"❌ Erro na transcrição segmentada: {e}")
        return f"[Erro na transcrição segmentada: {str(e)}]"

def improve_transcription_with_gemini(raw_transcription):
    """Melhora a transcrição usando Gemini AI"""
    if not model:
        return raw_transcription
    
    try:
        prompt = f"""
        Por favor, corrija e melhore a seguinte transcrição de áudio médico:
        
        Transcrição original:
        {raw_transcription}
        
        Instruções:
        1. Corrija erros de ortografia e gramática
        2. Adicione pontuação adequada
        3. Organize o texto em parágrafos quando apropriado
        4. Mantenha terminologia médica precisa
        5. Preserve o significado original
        
        Retorne apenas o texto corrigido:
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"❌ Erro ao melhorar transcrição com Gemini: {e}")
        return raw_transcription

# ==================== FUNÇÕES DE GERAÇÃO DE DOCUMENTOS ====================

def create_pdf_from_text(text, title="Resumo da Consulta"):
    """Cria um PDF a partir de texto"""
    try:
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Criar documento PDF
        doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Estilo personalizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=0  # Justificado
        )
        
        # Construir conteúdo
        story = []
        
        # Escapar caracteres especiais no título
        safe_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(safe_title, title_style))
        story.append(Spacer(1, 12))
        
        # Dividir texto em parágrafos e escapar caracteres especiais
        paragraphs = text.split('\n')
        for para in paragraphs:
            if para.strip():
                # Escapar caracteres especiais XML/HTML
                safe_para = para.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Remover caracteres de controle que podem causar problemas
                safe_para = ''.join(char for char in safe_para if ord(char) >= 32 or char in '\t\n\r')
                story.append(Paragraph(safe_para, content_style))
        
        # Gerar PDF
        doc.build(story)
        
        # Ler bytes do PDF
        with open(temp_file.name, 'rb') as f:
            pdf_bytes = f.read()
        
        # Limpar arquivo temporário
        os.unlink(temp_file.name)
        
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ Erro ao criar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def create_docx_from_text(text, title="Resumo da Consulta"):
    """Cria um documento DOCX a partir de texto"""
    try:
        # Criar documento
        doc = Document()
        
        # Adicionar título
        title_para = doc.add_heading(title, 0)
        title_para.alignment = 1  # Centralizado
        
        # Adicionar espaço
        doc.add_paragraph()
        
        # Dividir texto em parágrafos
        paragraphs = text.split('\n')
        for para in paragraphs:
            if para.strip():
                # Limpar caracteres de controle que podem causar problemas
                clean_para = ''.join(char for char in para.strip() if ord(char) >= 32 or char in '\t\n\r')
                if clean_para:  # Só adicionar se ainda houver conteúdo após limpeza
                    doc.add_paragraph(clean_para)
        
        # Salvar em arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file.close()
        
        doc.save(temp_file.name)
        
        # Ler bytes do DOCX
        with open(temp_file.name, 'rb') as f:
            docx_bytes = f.read()
        
        # Limpar arquivo temporário
        os.unlink(temp_file.name)
        
        return docx_bytes
        
    except Exception as e:
        print(f"❌ Erro ao criar DOCX: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ==================== ROTAS DA API ====================

@audio_bp.route('/api/save_recording', methods=['POST'])
@login_required
def api_save_recording():
    try:
        data = request.json
        audio_data = data['audio']
        patient_name = data.get('patient_name', '')
        
        # Decodificar base64
        if audio_data.startswith('data:audio'):
            audio_data = audio_data.split(',')[1]
        
        audio_bytes = base64.b64decode(audio_data)
        
        # Gerar nome do arquivo usando user_id da sessão
        user_id = session.get('user_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if patient_name:
            safe_patient_name = sanitize_filename(patient_name)
            filename = f"{safe_patient_name}_{timestamp}_{user_id}.wav"
        else:
            filename = f"recording_{timestamp}_{user_id}.wav"
        
        # Salvar arquivo
        file_path = os.path.join(RECORDINGS_DIR, filename)
        
        # Converter para WAV usando pydub
        try:
            # Criar AudioSegment a partir dos bytes
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Normalizar e configurar
            audio_segment = audio_segment.normalize()
            audio_segment = audio_segment.set_channels(1)  # Mono
            audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
            
            # Exportar como WAV
            audio_segment.export(file_path, format="wav")
            
        except Exception as e:
            print(f"❌ Erro ao processar áudio: {e}")
            # Fallback: salvar bytes diretamente
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)
        
        return jsonify({
            'success': True,
            'message': 'Gravação salva com sucesso!',
            'filename': filename
        })
        
    except Exception as e:
        print(f"❌ Erro ao salvar gravação: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar gravação: {str(e)}'
        }), 500

@audio_bp.route('/api/recordings', methods=['GET'])
@login_required
def api_get_recordings():
    """Lista gravações do usuário com lógica corrigida"""
    try:
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        recordings = []
        sessions = {}
        
        print(f"🔍 Buscando gravações para user_id: {user_id}, email: {user_email}")
        
        # Verificar se o diretório existe
        if not os.path.exists(RECORDINGS_DIR):
            print(f"❌ Diretório {RECORDINGS_DIR} não existe")
            # Criar diretório se não existir
            os.makedirs(RECORDINGS_DIR, exist_ok=True)
            return jsonify({
                'success': True,
                'recordings': [],
                'sessions': []
            })
        
        # Listar arquivos
        all_files = os.listdir(RECORDINGS_DIR)
        print(f"📋 Arquivos encontrados: {len(all_files)}")
        
        for filename in all_files:
            if not filename.endswith('.wav'):
                continue
            
            print(f"🔍 Analisando arquivo: {filename}")
            
            # CORREÇÃO: Lógica de filtragem mais rigorosa e com debug
            belongs_to_user = False
            
            # Verificar formato novo: nome_timestamp_userid.wav
            if filename.endswith(f"_{user_id}.wav"):
                belongs_to_user = True
                print(f"✅ Arquivo pertence ao usuário (formato novo): {filename}")
            
            # Verificar formato antigo apenas se user_email existir
            elif user_email:
                # Formato antigo: nome_timestamp_email_formatado.wav
                old_format_suffix = f"_{user_email.replace('@', '_').replace('.', '_')}.wav"
                if filename.endswith(old_format_suffix):
                    belongs_to_user = True
                    print(f"✅ Arquivo pertence ao usuário (formato antigo): {filename}")
            
            if not belongs_to_user:
                print(f"❌ Arquivo NÃO pertence ao usuário: {filename}")
                continue
            
            filepath = os.path.join(RECORDINGS_DIR, filename)
            
            try:
                # Verificar se o arquivo existe e é acessível
                if not os.path.exists(filepath):
                    print(f"❌ Arquivo não existe: {filepath}")
                    continue
                    
                file_size = os.path.getsize(filepath)
                
                # Data de modificação
                modified_time = os.path.getmtime(filepath)
                modified_date = datetime.fromtimestamp(modified_time).strftime('%d/%m/%Y %H:%M')
                
                # Verificar transcrição
                transcription_file = os.path.splitext(filename)[0] + '_transcricao.txt'
                transcription_path = os.path.join(TRANSCRIPTIONS_DIR, transcription_file)
                has_transcription = os.path.exists(transcription_path)
                
                # Formatar tamanho de forma legível
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                if '_sessao_' in filename:
                    # Segmento de sessão
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        session_id = parts[2]
                        
                        if session_id not in sessions:
                            sessions[session_id] = {
                                'id': session_id,
                                'segments': [],
                                'total_size': 0
                            }
                        
                        sessions[session_id]['segments'].append({
                            'filename': filename,
                            'size': file_size,
                            'has_transcription': has_transcription
                        })
                        sessions[session_id]['total_size'] += file_size
                else:
                    # Gravação individual
                    recording_data = {
                        'filename': filename,
                        'size': size_str,  # CORREÇÃO: Formato legível
                        'date': modified_date,  # CORREÇÃO: Campo correto para o frontend
                        'has_transcription': has_transcription
                    }
                    recordings.append(recording_data)
                    print(f"✅ Gravação adicionada: {recording_data}")
                    
            except Exception as file_error:
                print(f"❌ Erro ao processar arquivo {filename}: {file_error}")
                continue
        
        # Ordenar por data (mais recente primeiro)
        try:
            recordings.sort(key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y %H:%M'), reverse=True)
        except Exception as sort_error:
            print(f"⚠️ Erro ao ordenar gravações: {sort_error}")
            # Manter ordem original se houver erro na ordenação
        
        # Converter sessões para lista
        session_list = list(sessions.values())
        
        print(f"📊 RESULTADO FINAL: {len(recordings)} gravações e {len(session_list)} sessões")
        print(f"📋 Gravações encontradas: {[r['filename'] for r in recordings]}")
        
        return jsonify({
            'success': True,
            'recordings': recordings,
            'sessions': session_list
        })
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao listar gravações: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # CORREÇÃO: Retornar lista vazia em caso de erro, não falhar
        return jsonify({
            'success': True,  # Manter como True para não quebrar o frontend
            'recordings': [],
            'sessions': [],
            'error_message': f'Erro interno: {str(e)}'
        })

@audio_bp.route('/transcribe', methods=['POST'])
@login_required
def transcribe_recording():
    """Transcreve uma gravação"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'message': 'Nome do arquivo não fornecido'
            }), 400
        
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        # Verificar formato novo ou antigo
        belongs_to_user = (
            filename.endswith(f"_{user_id}.wav") or 
            (user_email and filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        filepath = os.path.join(RECORDINGS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': 'Arquivo não encontrado'
            }), 404
        
        print(f"🎯 Iniciando transcrição de: {filename}")
        
        # Transcrever
        transcription = transcribe_audio_with_speech_recognition(filepath)
        
        # Melhorar com Gemini se disponível
        if model and not transcription.startswith('['):
            print("🤖 Melhorando transcrição com Gemini...")
            transcription = improve_transcription_with_gemini(transcription)
        
        # Salvar transcrição
        transcription_filename = os.path.splitext(filename)[0] + '_transcricao.txt'
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, transcription_filename)
        
        # Criar diretório se não existir
        os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
        
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(transcription)
        
        print(f"✅ Transcrição salva: {transcription_filename}")
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'message': 'Transcrição realizada com sucesso!'
        })
        
    except Exception as e:
        print(f"❌ Erro na transcrição: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro na transcrição: {str(e)}'
        }), 500

@audio_bp.route('/api/rename_recording', methods=['POST'])
@login_required
def rename_recording():
    """Renomeia uma gravação"""
    try:
        data = request.json
        old_filename = data.get('old_filename')
        new_name = data.get('new_name', '').strip()
        
        if not old_filename or not new_name:
            return jsonify({
                'success': False,
                'message': 'Nome antigo e novo são obrigatórios'
            }), 400
        
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        belongs_to_user = (
            old_filename.endswith(f"_{user_id}.wav") or 
            (user_email and old_filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        old_filepath = os.path.join(RECORDINGS_DIR, old_filename)
        
        if not os.path.exists(old_filepath):
            return jsonify({
                'success': False,
                'message': 'Arquivo não encontrado'
            }), 404
        
        # Gerar novo nome
        safe_new_name = sanitize_filename(new_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f'{safe_new_name}_{timestamp}_{user_id}.wav'
        new_filepath = os.path.join(RECORDINGS_DIR, new_filename)
        
        # Renomear arquivo
        os.rename(old_filepath, new_filepath)
        
        # Renomear transcrição se existir
        old_transcription = os.path.splitext(old_filename)[0] + '_transcricao.txt'
        old_transcription_path = os.path.join(TRANSCRIPTIONS_DIR, old_transcription)
        
        if os.path.exists(old_transcription_path):
            new_transcription = os.path.splitext(new_filename)[0] + '_transcricao.txt'
            new_transcription_path = os.path.join(TRANSCRIPTIONS_DIR, new_transcription)
            os.rename(old_transcription_path, new_transcription_path)
        
        print(f"✅ Arquivo renomeado: {old_filename} -> {new_filename}")
        
        return jsonify({
            'success': True,
            'new_filename': new_filename,
            'message': 'Arquivo renomeado com sucesso!'
        })
        
    except Exception as e:
        print(f"❌ Erro ao renomear: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao renomear: {str(e)}'
        }), 500

@audio_bp.route('/api/delete_recording', methods=['POST'])
@login_required
def delete_recording():
    """Exclui uma gravação"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'message': 'Nome do arquivo não fornecido'
            }), 400
        
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        belongs_to_user = (
            filename.endswith(f"_{user_id}.wav") or 
            (user_email and filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        filepath = os.path.join(RECORDINGS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': 'Arquivo não encontrado'
            }), 404
        
        # Excluir arquivo
        os.remove(filepath)
        
        # Excluir transcrição se existir
        transcription_file = os.path.splitext(filename)[0] + '_transcricao.txt'
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, transcription_file)
        
        if os.path.exists(transcription_path):
            os.remove(transcription_path)
        
        print(f"✅ Arquivo excluído: {filename}")
        
        return jsonify({
            'success': True,
            'message': 'Arquivo excluído com sucesso!'
        })
        
    except Exception as e:
        print(f"❌ Erro ao excluir: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir: {str(e)}'
        }), 500

@audio_bp.route('/download/<filename>')
@login_required
def download_recording(filename):
    """Download de gravação"""
    try:
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        belongs_to_user = (
            filename.endswith(f"_{user_id}.wav") or 
            (user_email and filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        filepath = os.path.join(RECORDINGS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': 'Arquivo não encontrado'
            }), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ Erro no download: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro no download: {str(e)}'
        }), 500

@audio_bp.route('/download_transcription/<filename>')
@login_required
def download_transcription(filename):
    """Download de transcrição"""
    try:
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        recording_filename = filename.replace('_transcricao.txt', '.wav')
        belongs_to_user = (
            recording_filename.endswith(f"_{user_id}.wav") or 
            (user_email and recording_filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': 'Transcrição não encontrada'
            }), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ Erro no download da transcrição: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro no download: {str(e)}'
        }), 500

@audio_bp.route('/export_pdf/<filename>')
@login_required
def export_pdf(filename):
    """Exporta transcrição como PDF"""
    try:
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        recording_filename = filename.replace('_transcricao.txt', '.wav')
        belongs_to_user = (
            recording_filename.endswith(f"_{user_id}.wav") or 
            (user_email and recording_filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, filename)
        
        if not os.path.exists(transcription_path):
            return jsonify({
                'success': False,
                'message': 'Transcrição não encontrada'
            }), 404
        
        # Ler transcrição
        with open(transcription_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Criar PDF
        pdf_bytes = create_pdf_from_text(text)
        
        if not pdf_bytes:
            return jsonify({
                'success': False,
                'message': 'Erro ao gerar PDF'
            }), 500
        
        # Criar arquivo temporário para download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        pdf_filename = filename.replace('_transcricao.txt', '_transcricao.pdf')
        
        return send_file(temp_file.name, as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        print(f"❌ Erro ao exportar PDF: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar PDF: {str(e)}'
        }), 500

@audio_bp.route('/export_docx/<filename>')
@login_required
def export_docx(filename):
    """Exporta transcrição como DOCX"""
    try:
        # Verificar se o arquivo pertence ao usuário
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        
        recording_filename = filename.replace('_transcricao.txt', '.wav')
        belongs_to_user = (
            recording_filename.endswith(f"_{user_id}.wav") or 
            (user_email and recording_filename.endswith(f"_{user_email.replace('@', '_').replace('.', '_')}.wav"))
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, filename)
        
        if not os.path.exists(transcription_path):
            return jsonify({
                'success': False,
                'message': 'Transcrição não encontrada'
            }), 404
        
        # Ler transcrição
        with open(transcription_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Criar DOCX
        docx_bytes = create_docx_from_text(text)
        
        if not docx_bytes:
            return jsonify({
                'success': False,
                'message': 'Erro ao gerar DOCX'
            }), 500
        
        # Criar arquivo temporário para download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file.write(docx_bytes)
        temp_file.close()
        
        docx_filename = filename.replace('_transcricao.txt', '_transcricao.docx')
        
        return send_file(temp_file.name, as_attachment=True, download_name=docx_filename)
        
    except Exception as e:
        print(f"❌ Erro ao exportar DOCX: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar DOCX: {str(e)}'
        }), 500

@audio_bp.route('/api/transcriptions', methods=['GET'])
@login_required
def api_get_transcriptions():
    """Rota API para listar transcrições - compatibilidade com React"""
    try:
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        safe_user_email = user_email.replace('@', '_').replace('.', '_')
        transcriptions = []
        
        print(f"🔍 Buscando transcrições para user_id: {user_id}")
        print(f"📧 Email do usuário: {user_email}")
        print(f"📁 Diretório de transcrições: {os.path.abspath(TRANSCRIPTIONS_DIR)}")
        
        # Verificar se o diretório existe
        if not os.path.exists(TRANSCRIPTIONS_DIR):
            print(f"❌ Diretório {TRANSCRIPTIONS_DIR} não existe")
            return jsonify({
                'success': True,
                'transcriptions': []
            })
        
        # Listar arquivos de transcrição
        for filename in os.listdir(TRANSCRIPTIONS_DIR):
            if filename.endswith('_transcricao.txt'):
                print(f"🔍 Verificando arquivo: {filename}")
                
                # Verificar se pertence ao usuário (suporta ambos os formatos)
                belongs_to_user = (
                    filename.endswith(f"_{user_id}_transcricao.txt") or
                    safe_user_email in filename
                )
                
                if belongs_to_user:
                    print(f"✅ Arquivo pertence ao usuário: {filename}")
                    
                    filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)
                    file_size = os.path.getsize(filepath)
                    
                    # Obter data de modificação
                    modified_time = os.path.getmtime(filepath)
                    modified_date = datetime.fromtimestamp(modified_time).strftime('%d/%m/%Y %H:%M')
                    
                    # Ler primeiras linhas para preview
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            preview = content[:200] + '...' if len(content) > 200 else content
                    except:
                        preview = "Erro ao ler arquivo"
                    
                    # Nome original do arquivo de áudio
                    audio_filename = filename.replace('_transcricao.txt', '.wav')
                    
                    # Verificar se existe resumo
                    summary_filename = filename.replace('_transcricao.txt', '_resumo.txt')
                    summary_path = os.path.join(TRANSCRIPTIONS_DIR, summary_filename)
                    has_summary = os.path.exists(summary_path)
                    
                    transcriptions.append({
                        'filename': filename,
                        'audio_filename': audio_filename,
                        'size': file_size,
                        'modified_date': modified_date,
                        'preview': preview,
                        'has_summary': has_summary
                    })
                else:
                    print(f"❌ Arquivo não pertence ao usuário: {filename}")
        
        print(f"✅ Encontradas {len(transcriptions)} transcrições")
        
        return jsonify({
            'success': True,
            'transcriptions': transcriptions
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar transcrições: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao listar transcrições: {str(e)}'
        }), 500

@audio_bp.route('/api/view_transcription/<filename>', methods=['GET'])
@login_required
def api_view_transcription(filename):
    """Rota API para visualizar transcrição - compatibilidade com React"""
    try:
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        safe_user_email = user_email.replace('@', '_').replace('.', '_')
        
        # Verificar se o arquivo pertence ao usuário (suporta ambos os formatos)
        belongs_to_user = (
            filename.endswith(f"_{user_id}_transcricao.txt") or
            safe_user_email in filename
        )
        
        if not belongs_to_user:
            return jsonify({
                'success': False, 
                'message': 'Acesso negado - arquivo não pertence ao usuário'
            }), 403
        
        filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Arquivo de transcrição não encontrado'
            }), 404
    
    except Exception as e:
        print(f"❌ Erro ao carregar transcrição: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao carregar transcrição: {str(e)}'
        }), 500

@audio_bp.route('/api/export_summary_pdf/<filename>', methods=['GET'])
@login_required
def api_export_summary_pdf(filename):
    """Exporta resumo como PDF - compatibilidade com React"""
    try:
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        safe_user_email = user_email.replace('@', '_').replace('.', '_')
        
        print(f"🔍 Tentando exportar PDF para: {filename}")
        print(f"👤 User ID: {user_id}")
        
        # Verificar se o arquivo pertence ao usuário
        belongs_to_user = (
            filename.endswith(f"_{user_id}_transcricao.txt") or
            safe_user_email in filename
        )
        
        if not belongs_to_user:
            print(f"❌ Arquivo não pertence ao usuário: {filename}")
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        # Construir nome do arquivo de resumo
        summary_filename = filename.replace('_transcricao.txt', '_resumo.txt')
        summary_path = os.path.join(TRANSCRIPTIONS_DIR, summary_filename)
        
        print(f"📄 Procurando resumo em: {summary_path}")
        
        if not os.path.exists(summary_path):
            print(f"❌ Arquivo de resumo não encontrado: {summary_path}")
            return jsonify({
                'success': False,
                'message': 'Resumo não encontrado. Execute a análise do Gemini primeiro.'
            }), 404
        
        # Ler resumo
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📖 Conteúdo lido: {len(content)} caracteres")
        
        if not content.strip():
            return jsonify({
                'success': False,
                'message': 'Arquivo de resumo está vazio'
            }), 400
        
        # Criar PDF
        pdf_bytes = create_pdf_from_text(content, "Resumo da Consulta")
        
        if not pdf_bytes:
            return jsonify({
                'success': False,
                'message': 'Erro ao gerar PDF - verifique o conteúdo do resumo'
            }), 500
        
        print(f"✅ PDF gerado com sucesso: {len(pdf_bytes)} bytes")
        
        # Criar arquivo temporário para download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        pdf_filename = summary_filename.replace('.txt', '.pdf')
        
        return send_file(temp_file.name, as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        print(f"❌ Erro ao exportar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro interno ao exportar PDF: {str(e)}'
        }), 500

@audio_bp.route('/api/export_summary_docx/<filename>', methods=['GET'])
@login_required
def api_export_summary_docx(filename):
    """Exporta resumo como DOCX - compatibilidade com React"""
    try:
        user_id = session['user_id']
        user_email = session.get('user_email', '')
        safe_user_email = user_email.replace('@', '_').replace('.', '_')
        
        print(f"🔍 Tentando exportar DOCX para: {filename}")
        print(f"👤 User ID: {user_id}")
        
        # Verificar se o arquivo pertence ao usuário
        belongs_to_user = (
            filename.endswith(f"_{user_id}_transcricao.txt") or
            safe_user_email in filename
        )
        
        if not belongs_to_user:
            print(f"❌ Arquivo não pertence ao usuário: {filename}")
            return jsonify({
                'success': False,
                'message': 'Arquivo não pertence ao usuário'
            }), 403
        
        # Construir nome do arquivo de resumo
        summary_filename = filename.replace('_transcricao.txt', '_resumo.txt')
        summary_path = os.path.join(TRANSCRIPTIONS_DIR, summary_filename)
        
        print(f"📄 Procurando resumo em: {summary_path}")
        
        if not os.path.exists(summary_path):
            print(f"❌ Arquivo de resumo não encontrado: {summary_path}")
            return jsonify({
                'success': False,
                'message': 'Resumo não encontrado. Execute a análise do Gemini primeiro.'
            }), 404
        
        # Ler resumo
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📖 Conteúdo lido: {len(content)} caracteres")
        
        if not content.strip():
            return jsonify({
                'success': False,
                'message': 'Arquivo de resumo está vazio'
            }), 400
        
        # Criar DOCX
        docx_bytes = create_docx_from_text(content, "Resumo da Consulta")
        
        if not docx_bytes:
            return jsonify({
                'success': False,
                'message': 'Erro ao gerar DOCX - verifique o conteúdo do resumo'
            }), 500
        
        print(f"✅ DOCX gerado com sucesso: {len(docx_bytes)} bytes")
        
        # Criar arquivo temporário para download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file.write(docx_bytes)
        temp_file.close()
        
        docx_filename = summary_filename.replace('.txt', '.docx')
        
        return send_file(temp_file.name, as_attachment=True, download_name=docx_filename)
        
    except Exception as e:
        print(f"❌ Erro ao exportar DOCX: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro interno ao exportar DOCX: {str(e)}'
        }), 500

@audio_bp.route('/api/debug_files/<filename>', methods=['GET'])
@login_required
def debug_files(filename):
    """Debug: mostra status dos arquivos relacionados"""
    try:
        user_id = session['user_id']
        transcription_filename = filename.replace('.wav', '_transcricao.txt')
        summary_filename = filename.replace('.wav', '_resumo.txt')
        
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, transcription_filename)
        summary_path = os.path.join(TRANSCRIPTIONS_DIR, summary_filename)
        
        debug_info = {
            'user_id': user_id,
            'transcription_filename': transcription_filename,
            'summary_filename': summary_filename,
            'transcription_exists': os.path.exists(transcription_path),
            'summary_exists': os.path.exists(summary_path),
            'transcriptions_dir': os.path.abspath(TRANSCRIPTIONS_DIR),
            'files_in_dir': os.listdir(TRANSCRIPTIONS_DIR) if os.path.exists(TRANSCRIPTIONS_DIR) else []
        }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro no debug: {str(e)}'
        }), 500