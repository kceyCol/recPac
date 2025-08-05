import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import RecordingControls from './RecordingControls';
import { ArrowPathIcon } from '@heroicons/react/24/solid';

function Dashboard() {
  const { user, logout } = useAuth();
  
  // Estados principais
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');
  
  // Estados para gravação
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [currentAudioBlob, setCurrentAudioBlob] = useState(null);
  
  // Sistema de log melhorado
  const [transcriptionLogs, setTranscriptionLogs] = useState({});
  const [activeTranscriptions, setActiveTranscriptions] = useState(new Set());
  const [showLogPanel, setShowLogPanel] = useState(false);
  
  // Carregar gravações ao inicializar
  useEffect(() => {
    fetchRecordings();
  }, []);
  
  // ===== FUNÇÕES DE LOG =====
  
  const addTranscriptionLog = (filename, message, type = 'info', progress = null) => {
    const timestamp = new Date().toLocaleTimeString('pt-BR');
    const logEntry = {
      id: Date.now() + Math.random(),
      timestamp,
      message,
      type, // 'info', 'success', 'error', 'warning', 'progress'
      progress // 0-100 para barra de progresso
    };
    
    setTranscriptionLogs(prev => ({
      ...prev,
      [filename]: [...(prev[filename] || []), logEntry]
    }));
    
    // Auto-mostrar painel quando há atividade
    if (type !== 'success') {
      setShowLogPanel(true);
    }
  };
  
  const clearTranscriptionLogs = (filename) => {
    setTranscriptionLogs(prev => {
      const newLogs = { ...prev };
      delete newLogs[filename];
      return newLogs;
    });
    
    setActiveTranscriptions(prev => {
      const newSet = new Set(prev);
      newSet.delete(filename);
      return newSet;
    });
  };
  
  const clearAllLogs = () => {
    setTranscriptionLogs({});
    setActiveTranscriptions(new Set());
    setShowLogPanel(false);
  };
  
  // ===== FUNÇÕES DE API =====
  
  const fetchRecordings = async () => {
    try {
      console.log('🔍 Buscando gravações...');
      
      // Verificar autenticação
      const authResponse = await fetch('/api/auth/status', {
        credentials: 'include'
      });
      
      if (!authResponse.ok) {
        console.log('❌ Usuário não autenticado');
        window.location.href = '/login';
        return;
      }
      
      // Buscar gravações
      const response = await fetch('/api/recordings', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📊 Gravações encontradas:', data.recordings?.length || 0);
        setRecordings(data.recordings || []);
      } else {
        console.error('❌ Erro ao buscar gravações:', response.status);
      }
    } catch (error) {
      console.error('❌ Erro na requisição:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // ===== HANDLERS DE GRAVAÇÃO =====
  
  const handleRecordingComplete = async (audioBlob) => {
    setCurrentAudioBlob(audioBlob);
    setShowPatientModal(true);
  };
  
  const saveRecordingWithPatientName = async (patientName = '') => {
    if (!currentAudioBlob) return;
    
    try {
      const reader = new FileReader();
      reader.onloadend = async function() {
        const base64Audio = reader.result;
        
        const response = await fetch('/api/save_recording', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            audio_data: base64Audio,
            patient_name: patientName
          })
        });
        
        const result = await response.json();
        if (result.success) {
          console.log('✅ Gravação salva:', result.filename);
          await fetchRecordings();
          setShowPatientModal(false);
          setCurrentAudioBlob(null);
        } else {
          alert('Erro ao salvar: ' + result.message);
        }
      };
      reader.readAsDataURL(currentAudioBlob);
    } catch (error) {
      console.error('Erro ao salvar gravação:', error);
      alert('Erro ao salvar gravação: ' + error.message);
    }
  };
  
  // ===== HANDLERS DE ARQUIVO =====
  
  const handleDownload = async (filename) => {
    try {
      const response = await fetch(`/download/${filename}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Erro ao fazer download do arquivo');
      }
    } catch (error) {
      console.error('Erro no download:', error);
      alert('Erro ao fazer download do arquivo');
    }
  };
  
  const handleRename = async (filename) => {
    let originalName = filename.replace('.wav', '');
    let parts = originalName.split('_');
    let extractedName = '';
    
    if (parts.length >= 3) {
      extractedName = parts.slice(0, -2).join('_');
    } else if (parts.length === 2) {
      extractedName = parts[0];
    } else {
      extractedName = parts[0];
    }
    
    const newName = prompt('Digite o novo nome (sem extensão):', extractedName);
    if (newName && newName.trim()) {
      try {
        const response = await fetch('/api/rename_recording', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            old_filename: filename,
            new_name: newName.trim()
          })
        });
        
        const result = await response.json();
        if (result.success) {
          await fetchRecordings();
          alert('Arquivo renomeado com sucesso!');
        } else {
          alert('Erro ao renomear: ' + result.message);
        }
      } catch (error) {
        alert('Erro ao renomear arquivo: ' + error.message);
      }
    }
  };
  
  const handleDelete = async (filename) => {
    if (window.confirm(`Tem certeza que deseja deletar ${filename}?`)) {
      try {
        const response = await fetch('/delete_recording', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            filename: filename
          })
        });
        
        const result = await response.json();
        if (result.success) {
          await fetchRecordings();
          alert('Arquivo deletado com sucesso!');
        } else {
          alert('Erro ao deletar: ' + result.message);
        }
      } catch (error) {
        alert('Erro ao deletar arquivo: ' + error.message);
      }
    }
  };
  
  // ===== HANDLER DE TRANSCRIÇÃO =====
  
  const handleTranscribe = async (filename) => {
    try {
      // Marcar como ativo e limpar logs anteriores
      setActiveTranscriptions(prev => new Set([...prev, filename]));
      clearTranscriptionLogs(filename);
      
      addTranscriptionLog(filename, `🚀 Iniciando transcrição de ${filename}`, 'info', 0);
      
      // Preparação
      addTranscriptionLog(filename, '📁 Preparando arquivo de áudio...', 'progress', 10);
      
      const response = await fetch('/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          filename: filename
        })
      });
      
      addTranscriptionLog(filename, '🤖 Enviando para processamento de IA...', 'progress', 30);
      
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
      
      addTranscriptionLog(filename, '⚡ Processando com Gemini AI...', 'progress', 60);
      
      const result = await response.json();
      
      if (result.success) {
        addTranscriptionLog(filename, '💾 Salvando resultado...', 'progress', 90);
        
        // Atualizar lista
        await fetchRecordings();
        
        addTranscriptionLog(filename, '✅ Transcrição concluída com sucesso!', 'success', 100);
        
        // Auto-limpar após 5 segundos
        setTimeout(() => {
          clearTranscriptionLogs(filename);
        }, 5000);
        
      } else {
        throw new Error(result.message || 'Erro desconhecido na transcrição');
      }
      
    } catch (error) {
      console.error('Erro na transcrição:', error);
      addTranscriptionLog(filename, `❌ Erro: ${error.message}`, 'error');
      
      // Remover de ativos após erro
      setTimeout(() => {
        setActiveTranscriptions(prev => {
          const newSet = new Set(prev);
          newSet.delete(filename);
          return newSet;
        });
      }, 10000);
    }
  };
  
  const handleDownloadTranscription = async (filename) => {
    try {
      const transcriptionFile = filename.replace('.wav', '_transcricao.txt');
      const response = await fetch(`/download_transcription/${transcriptionFile}`, {
        method: 'GET',
        credentials: 'include'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = transcriptionFile;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Erro ao fazer download da transcrição');
      }
    } catch (error) {
      console.error('Erro no download da transcrição:', error);
      alert('Erro ao fazer download da transcrição');
    }
  };
  
  // ===== COMPONENTE DE LOG =====
  
  const LogPanel = () => {
    const allLogs = Object.entries(transcriptionLogs);
    const hasActiveLogs = allLogs.length > 0;
    
    if (!hasActiveLogs) return null;
    
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center p-4 border-b border-blue-200">
            <h3 className="text-blue-800 font-semibold flex items-center">
              📋 Log de Transcrições
              {activeTranscriptions.size > 0 && (
                <span className="ml-2 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                  {activeTranscriptions.size} ativa(s)
                </span>
              )}
            </h3>
            <div className="space-x-2">
              <button
                onClick={clearAllLogs}
                className="text-blue-600 hover:text-blue-800 text-sm px-3 py-1 rounded hover:bg-blue-100 transition-colors"
              >
                🗑️ Limpar
              </button>
              <button
                onClick={() => setShowLogPanel(false)}
                className="text-blue-600 hover:text-blue-800 text-sm px-3 py-1 rounded hover:bg-blue-100 transition-colors"
              >
                ➖ Minimizar
              </button>
            </div>
          </div>
          
          <div className="p-4 space-y-4 max-h-80 overflow-y-auto">
            {allLogs.map(([filename, logs]) => (
              <div key={filename} className="bg-white rounded-lg p-3 border border-gray-200">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-gray-800 truncate">
                    🎵 {filename}
                  </h4>
                  <button
                    onClick={() => clearTranscriptionLogs(filename)}
                    className="text-gray-400 hover:text-gray-600 text-xs"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-1">
                  {logs.map((log) => (
                    <div key={log.id} className="flex items-center space-x-2 text-sm">
                      <span className="text-gray-500 font-mono text-xs">
                        {log.timestamp}
                      </span>
                      <span className={`flex-1 ${
                        log.type === 'success' ? 'text-green-600' :
                        log.type === 'error' ? 'text-red-600' :
                        log.type === 'warning' ? 'text-yellow-600' :
                        log.type === 'progress' ? 'text-blue-600' :
                        'text-gray-700'
                      }`}>
                        {log.message}
                      </span>
                      
                      {/* Barra de progresso */}
                      {log.type === 'progress' && log.progress !== null && (
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${log.progress}%` }}
                          ></div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };
  
  // ===== RENDER =====
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">🎙️ AudioToText</h1>
              <span className="text-sm text-gray-500">Dashboard</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                👤 Olá, {user?.name || 'Usuário'}
              </span>
              <button
                onClick={fetchRecordings}
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                title="Atualizar lista"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                🚪 Sair
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controles de Gravação */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🎤 Nova Gravação</h2>
          <RecordingControls onRecordingComplete={handleRecordingComplete} />
        </div>
        
        {/* Lista de Gravações */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">📂 Gravações Recentes</h2>
          </div>
          
          <div className="p-6">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="text-gray-500 mt-2">Carregando gravações...</p>
              </div>
            ) : recordings.length > 0 ? (
              <div className="space-y-4">
                {recordings.map((recording, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-1">
                          🎵 {recording.filename}
                        </h3>
                        <div className="text-sm text-gray-500 space-y-1">
                          <p>📅 {recording.date}</p>
                          <p>📏 {recording.size}</p>
                          {recording.has_transcription && (
                            <p className="text-green-600">✅ Transcrito</p>
                          )}
                          {activeTranscriptions.has(recording.filename) && (
                            <p className="text-blue-600">⚡ Transcrevendo...</p>
                          )}
                        </div>
                      </div>
                      
                      {/* Botões de Ação */}
                      <div className="flex flex-wrap gap-2 ml-4">
                        <button
                          onClick={() => handleDownload(recording.filename)}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                        >
                          📥 Download
                        </button>
                        
                        <button
                          onClick={() => handleRename(recording.filename)}
                          className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded text-sm transition-colors"
                        >
                          ✏️ Renomear
                        </button>
                        
                        {/* Botões de Transcrição */}
                        {recording.has_transcription ? (
                          <>
                            <Link
                              to={`/transcription/${recording.filename.replace('.wav', '_transcricao.txt')}`}
                              className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm transition-colors inline-block text-center"
                            >
                              👁️ Ver Transcrição
                            </Link>
                            <button
                              onClick={() => handleDownloadTranscription(recording.filename)}
                              className="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              📄 Download Transcrição
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleTranscribe(recording.filename)}
                            disabled={activeTranscriptions.has(recording.filename)}
                            className={`px-3 py-1 rounded text-sm transition-colors ${
                              activeTranscriptions.has(recording.filename)
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-green-500 hover:bg-green-600'
                            } text-white`}
                          >
                            {activeTranscriptions.has(recording.filename) 
                              ? '⏳ Processando...' 
                              : '🤖 Transcrever'
                            }
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDelete(recording.filename)}
                          className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm transition-colors"
                        >
                          🗑️ Deletar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">📭 Nenhuma gravação encontrada</p>
                <p className="text-sm text-gray-400 mt-1">Faça sua primeira gravação acima!</p>
              </div>
            )}
          </div>
        </div>
      </main>
      
      {/* Sistema de Log */}
      {showLogPanel && <LogPanel />}
      
      {/* Botão flutuante para logs */}
      {!showLogPanel && Object.keys(transcriptionLogs).length > 0 && (
        <div className="fixed bottom-4 right-4 z-40">
          <button
            onClick={() => setShowLogPanel(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-all duration-200 shadow-lg hover:shadow-xl flex items-center space-x-2"
          >
            <span>📋</span>
            <span>Logs ({Object.keys(transcriptionLogs).length})</span>
            {activeTranscriptions.size > 0 && (
              <span className="bg-blue-400 text-white px-2 py-1 rounded-full text-xs">
                {activeTranscriptions.size}
              </span>
            )}
          </button>
        </div>
      )}
      
      {/* Modal de Nome do Paciente */}
      {showPatientModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">👤 Nome do Paciente</h3>
            <input 
              type="text" 
              placeholder="Digite o nome do paciente (opcional)"
              className="w-full p-3 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  saveRecordingWithPatientName(e.target.value.trim());
                }
              }}
              autoFocus
            />
            <div className="flex gap-3">
              <button 
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                onClick={(e) => {
                  const input = e.target.closest('.bg-white').querySelector('input');
                  saveRecordingWithPatientName(input.value.trim());
                }}
              >
                💾 Salvar com Nome
              </button>
              <button 
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                onClick={() => saveRecordingWithPatientName('')}
              >
                📁 Salvar sem Nome
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal de Transcrição (se necessário) */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">{modalTitle}</h3>
                <button
                  onClick={() => setModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <pre className="whitespace-pre-wrap text-sm">{modalContent}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;