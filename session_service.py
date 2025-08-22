"""
Serviço de gerenciamento de sessões de gravação
Separa as funcionalidades de sessões do app.py
"""

import os
import json
from datetime import datetime
from pydub import AudioSegment

class SessionService:
    """Serviço para gerenciamento de sessões de gravação"""
    
    def __init__(self, recordings_dir, transcriptions_dir):
        self.recordings_dir = recordings_dir
        self.transcriptions_dir = transcriptions_dir
    
    def start_new_session(self, user_id):
        """Inicia uma nova sessão de gravação"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_id = f"sessao_{timestamp}"
            
            # Criar arquivo de metadados da sessão
            session_metadata = {
                'session_id': session_id,
                'user_id': user_id,
                'start_time': timestamp,
                'status': 'active',
                'segments': [],
                'total_duration': 0
            }
            
            metadata_filename = f"{session_id}_{user_id}_metadata.json"
            metadata_path = os.path.join(self.recordings_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(session_metadata, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Sessão iniciada com sucesso!'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao iniciar sessão: {str(e)}'
            }
    
    def add_segment_to_session(self, session_id, user_id, audio_data, segment_number):
        """Adiciona um segmento de áudio à sessão"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            segment_filename = f"segmento_{segment_number}_{session_id}_{timestamp}_{user_id}.wav"
            segment_path = os.path.join(self.recordings_dir, segment_filename)
            
            # Salvar segmento de áudio
            with open(segment_path, 'wb') as f:
                f.write(audio_data)
            
            # Atualizar metadados da sessão
            metadata_filename = f"{session_id}_{user_id}_metadata.json"
            metadata_path = os.path.join(self.recordings_dir, metadata_filename)
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Adicionar segmento aos metadados
                segment_info = {
                    'filename': segment_filename,
                    'segment_number': segment_number,
                    'timestamp': timestamp,
                    'size': len(audio_data)
                }
                metadata['segments'].append(segment_info)
                
                # Atualizar arquivo de metadados
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'segment_filename': segment_filename,
                'message': f'Segmento {segment_number} adicionado à sessão!'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao adicionar segmento: {str(e)}'
            }
    
    def get_session_info(self, session_id, user_id):
        """Obtém informações detalhadas de uma sessão"""
        try:
            metadata_filename = f"{session_id}_{user_id}_metadata.json"
            metadata_path = os.path.join(self.recordings_dir, metadata_filename)
            
            if not os.path.exists(metadata_path):
                return {
                    'success': False,
                    'message': 'Sessão não encontrada'
                }
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Calcular duração total dos segmentos
            total_duration = 0
            for segment in metadata['segments']:
                segment_path = os.path.join(self.recordings_dir, segment['filename'])
                if os.path.exists(segment_path):
                    try:
                        audio = AudioSegment.from_wav(segment_path)
                        total_duration += len(audio)
                    except:
                        pass
            
            metadata['total_duration_ms'] = total_duration
            metadata['total_duration_seconds'] = total_duration / 1000.0
            
            return {
                'success': True,
                'session_info': metadata
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao obter informações da sessão: {str(e)}'
            }
    
    def finalize_session(self, session_id, user_id):
        """Finaliza uma sessão combinando todos os segmentos"""
        try:
            # Obter informações da sessão
            session_info = self.get_session_info(session_id, user_id)
            if not session_info['success']:
                return session_info
            
            metadata = session_info['session_info']
            segments = metadata['segments']
            
            if not segments:
                return {
                    'success': False,
                    'message': 'Nenhum segmento encontrado para esta sessão'
                }
            
            # Ordenar segmentos por número
            segments.sort(key=lambda x: x['segment_number'])
            
            # Combinar áudios usando pydub
            combined_audio = AudioSegment.empty()
            
            for segment_info in segments:
                segment_path = os.path.join(self.recordings_dir, segment_info['filename'])
                if os.path.exists(segment_path):
                    try:
                        segment_audio = AudioSegment.from_wav(segment_path)
                        combined_audio += segment_audio
                    except Exception as e:
                        print(f"Erro ao processar segmento {segment_info['filename']}: {e}")
            
            if len(combined_audio) == 0:
                return {
                    'success': False,
                    'message': 'Não foi possível combinar os segmentos de áudio'
                }
            
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
            
            # Atualizar metadados da sessão
            metadata['status'] = 'finalized'
            metadata['final_filename'] = final_filename
            metadata['finalize_time'] = timestamp
            metadata['final_duration_ms'] = len(combined_audio)
            metadata['final_duration_seconds'] = len(combined_audio) / 1000.0
            
            metadata_filename = f"{session_id}_{user_id}_metadata.json"
            metadata_path = os.path.join(self.recordings_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': 'Sessão finalizada com sucesso!',
                'filename': final_filename,
                'duration_seconds': metadata['final_duration_seconds']
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao finalizar sessão: {str(e)}'
            }
    
    def get_user_sessions(self, user_id):
        """Lista todas as sessões do usuário"""
        try:
            sessions = []
            
            # Buscar arquivos de metadados de sessão
            for filename in os.listdir(self.recordings_dir):
                if filename.endswith('_metadata.json') and user_id in filename:
                    try:
                        metadata_path = os.path.join(self.recordings_dir, filename)
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        sessions.append(metadata)
                    except Exception as e:
                        print(f"Erro ao ler metadados de {filename}: {e}")
                        continue
            
            # Ordenar por data de início (mais recente primeiro)
            sessions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
            return {
                'success': True,
                'sessions': sessions
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao listar sessões: {str(e)}',
                'sessions': []
            }
    
    def delete_session(self, session_id, user_id):
        """Deleta uma sessão e todos os seus segmentos"""
        try:
            # Obter informações da sessão
            session_info = self.get_session_info(session_id, user_id)
            if not session_info['success']:
                return session_info
            
            metadata = session_info['session_info']
            
            # Deletar todos os segmentos
            for segment_info in metadata['segments']:
                segment_path = os.path.join(self.recordings_dir, segment_info['filename'])
                if os.path.exists(segment_path):
                    try:
                        os.remove(segment_path)
                    except Exception as e:
                        print(f"Erro ao deletar segmento {segment_info['filename']}: {e}")
            
            # Deletar arquivo de metadados
            metadata_filename = f"{session_id}_{user_id}_metadata.json"
            metadata_path = os.path.join(self.recordings_dir, metadata_filename)
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            # Deletar arquivo final se existir
            if 'final_filename' in metadata:
                final_path = os.path.join(self.recordings_dir, metadata['final_filename'])
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except Exception as e:
                        print(f"Erro ao deletar arquivo final: {e}")
            
            return {
                'success': True,
                'message': 'Sessão deletada com sucesso!'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao deletar sessão: {str(e)}'
            }
