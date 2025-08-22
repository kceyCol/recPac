"""
Serviço de gerenciamento de arquivos
Separa as funcionalidades de gerenciamento de arquivos do app.py
"""

import os
import re
from datetime import datetime
from pydub import AudioSegment

class FileManagerService:
    """Serviço para gerenciamento de arquivos de áudio e transcrições"""
    
    def __init__(self, recordings_dir, transcriptions_dir):
        self.recordings_dir = recordings_dir
        self.transcriptions_dir = transcriptions_dir
    
    def sanitize_filename(self, filename):
        """Sanitiza nome de arquivo removendo caracteres inválidos"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def rename_recording(self, old_filename, new_name, user_id):
        """Renomeia um arquivo de gravação e sua transcrição associada"""
        try:
            # Sanitizar novo nome
            safe_new_name = self.sanitize_filename(new_name)
            if not safe_new_name:
                return {
                    'success': False, 
                    'message': 'Nome inválido'
                }
            
            # Gerar novo nome do arquivo
            # Extrair timestamp e user_id do filename antigo
            parts = old_filename.replace('.wav', '').split('_')
            
            # Determinar formato do arquivo baseado na estrutura
            if len(parts) >= 3:
                # Formato: nome_timestamp_userid.wav
                timestamp = parts[-2]
                user_id_from_file = parts[-1]
                new_filename = f'{safe_new_name}_{timestamp}_{user_id_from_file}.wav'
            else:
                # Formato antigo ou simples
                timestamp = parts[-1] if len(parts) > 1 else datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f'{safe_new_name}_{timestamp}_{user_id}.wav'
            
            old_path = os.path.join(self.recordings_dir, old_filename)
            new_path = os.path.join(self.recordings_dir, new_filename)
            
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                
                # Renomear transcrição se existir
                old_transcription = os.path.splitext(old_filename)[0] + '_transcricao.txt'
                new_transcription = os.path.splitext(new_filename)[0] + '_transcricao.txt'
                
                old_transcription_path = os.path.join(self.transcriptions_dir, old_transcription)
                new_transcription_path = os.path.join(self.transcriptions_dir, new_transcription)
                
                if os.path.exists(old_transcription_path):
                    os.rename(old_transcription_path, new_transcription_path)
                
                return {
                    'success': True,
                    'message': 'Arquivo renomeado com sucesso!',
                    'new_filename': new_filename
                }
            else:
                return {
                    'success': False, 
                    'message': 'Arquivo não encontrado'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao renomear: {str(e)}'
            }
    
    def delete_recording(self, filename, user_id):
        """Deleta um arquivo de gravação e arquivos associados"""
        try:
            filepath = os.path.join(self.recordings_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
                # Remover transcrição se existir
                transcription_file = os.path.splitext(filename)[0] + '_transcricao.txt'
                transcription_path = os.path.join(self.transcriptions_dir, transcription_file)
                
                if os.path.exists(transcription_path):
                    os.remove(transcription_path)
                
                # Remover resumo se existir
                summary_file = os.path.splitext(filename)[0] + '_resumo.txt'
                summary_path = os.path.join(self.transcriptions_dir, summary_file)
                
                if os.path.exists(summary_path):
                    os.remove(summary_path)
                
                return {
                    'success': True,
                    'message': 'Arquivo deletado com sucesso!'
                }
            else:
                return {
                    'success': False, 
                    'message': 'Arquivo não encontrado'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao deletar: {str(e)}'
            }
    
    def get_recordings_list(self, user_id):
        """Lista todos os arquivos de gravação do usuário"""
        try:
            recordings = []
            sessions = {}
            
            # Listar arquivos de gravação
            for filename in os.listdir(self.recordings_dir):
                if filename.endswith('.wav') and (user_id in filename or user_id.replace('@', '_').replace('.', '_') in filename):
                    filepath = os.path.join(self.recordings_dir, filename)
                    file_size = os.path.getsize(filepath)
                    
                    # Verificar se existe transcrição
                    transcription_file = os.path.splitext(filename)[0] + '_transcricao.txt'
                    transcription_path = os.path.join(self.transcriptions_dir, transcription_file)
                    has_transcription = os.path.exists(transcription_path)
                    
                    if '_sessao_' in filename:
                        # É um segmento de sessão
                        parts = filename.split('_')
                        session_id = parts[2]  # sessao_ID
                        
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
                        recordings.append({
                            'filename': filename,
                            'size': file_size,
                            'has_transcription': has_transcription
                        })
            
            # Converter sessões para lista
            sessions_list = list(sessions.values())
            
            return {
                'success': True,
                'recordings': recordings,
                'sessions': sessions_list
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao carregar gravações: {str(e)}',
                'recordings': [],
                'sessions': []
            }
    
    def get_transcriptions_list(self, user_id):
        """Lista todas as transcrições do usuário"""
        try:
            transcriptions = []
            
            # Listar arquivos de transcrição
            for filename in os.listdir(self.transcriptions_dir):
                if filename.endswith('_transcricao.txt') and (user_id in filename or user_id.replace('@', '_').replace('.', '_') in filename):
                    filepath = os.path.join(self.transcriptions_dir, filename)
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
                    summary_path = os.path.join(self.transcriptions_dir, summary_filename)
                    has_summary = os.path.exists(summary_path)
                    
                    transcriptions.append({
                        'filename': filename,
                        'audio_filename': audio_filename,
                        'size': file_size,
                        'modified_date': modified_date,
                        'preview': preview,
                        'has_summary': has_summary
                    })
            
            # Ordenar por data de modificação (mais recente primeiro)
            transcriptions.sort(key=lambda x: x['modified_date'], reverse=True)
            
            return {
                'success': True,
                'transcriptions': transcriptions
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao carregar transcrições: {str(e)}',
                'transcriptions': []
            }
    
    def finalize_session(self, session_id, user_id):
        """Finaliza uma sessão combinando todos os segmentos"""
        try:
            # Buscar todos os segmentos da sessão
            segments = []
            for filename in os.listdir(self.recordings_dir):
                if f'_sessao_{session_id}_' in filename and (user_id in filename or user_id.replace('@', '_').replace('.', '_') in filename):
                    segments.append(filename)
            
            if not segments:
                return {
                    'success': False, 
                    'message': 'Nenhum segmento encontrado para esta sessão'
                }
            
            # Ordenar segmentos por timestamp
            segments.sort()
            
            # Combinar áudios usando pydub
            combined_audio = AudioSegment.empty()
            
            for segment_filename in segments:
                segment_path = os.path.join(self.recordings_dir, segment_filename)
                segment_audio = AudioSegment.from_wav(segment_path)
                combined_audio += segment_audio
            
            # Salvar áudio combinado
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_filename = f'Sessao_{session_id}_{timestamp}_{user_id}.wav'
            final_path = os.path.join(self.recordings_dir, final_filename)
            
            # CORREÇÃO: Exportar com configurações específicas para evitar problemas de velocidade
            combined_audio.export(final_path, format="wav", parameters=[
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "44100",  # Sample rate padrão
                "-ac", "1"  # Mono
            ])
            
            return {
                'success': True,
                'message': 'Sessão finalizada com sucesso!',
                'filename': final_filename
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao finalizar sessão: {str(e)}'
            }
