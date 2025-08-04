import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import RecordingControls from './RecordingControls';
import { ArrowPathIcon } from '@heroicons/react/24/solid';

function Dashboard() {
  const { user, logout } = useAuth();
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transcriptionStatus, setTranscriptionStatus] = useState({});
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');

  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      console.log('🔍 Fazendo requisição para /api/recordings...');
      
      // Verificar status de autenticação primeiro
      const authResponse = await fetch('/api/auth/status', {
        credentials: 'include'
      });
      
      console.log('🔐 Status de autenticação:', authResponse.status);
      
      if (!authResponse.ok) {
        console.log('❌ Usuário não autenticado, redirecionando...');
        window.location.href = '/login';
        return;
      }
      
      const response = await fetch('/api/recordings', {
        credentials: 'include'
      });
      
      console.log('📡 Status da resposta:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📊 Dados recebidos da API:', data);
        console.log('📋 Gravações encontradas:', data.recordings);
        console.log('📈 Número de gravações:', data.recordings?.length || 0);
        
        setRecordings(data.recordings || []);
      } else {
        console.error('❌ Erro na resposta:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('❌ Erro na requisição:', error);
    } finally {
      setLoading(false);
    }
  };

  const [showPatientModal, setShowPatientModal] = useState(false);
  const [currentAudioBlob, setCurrentAudioBlob] = useState(null);
  
  const handleRecordingComplete = async (audioBlob) => {
    // Armazenar o blob e mostrar o modal
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
            audio: base64Audio,
            patient_name: patientName
          })
        });
        
        const result = await response.json();
        
        if (result.success) {
          console.log('Gravação salva com sucesso!');
          fetchRecordings();
          setShowPatientModal(false);
          setCurrentAudioBlob(null);
        } else {
          console.error('Erro ao salvar:', result.message);
        }
      };
      reader.readAsDataURL(currentAudioBlob);
      
    } catch (error) {
      console.error('Erro ao salvar gravação:', error);
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await fetch(`/download/${filename}`, {
        method: 'GET',
        credentials: 'include', // Importante: inclui cookies de sessão
        headers: {
          'Content-Type': 'application/json'
        }
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
        console.error('Erro no download:', response.status);
        alert('Erro ao fazer download do arquivo');
      }
    } catch (error) {
      console.error('Erro no download:', error);
      alert('Erro ao fazer download do arquivo');
    }
  };

  const handleRename = async (filename) => {
    // Extrair o nome original do arquivo
    let originalName = filename.replace('.wav', '');
    let parts = originalName.split('_');
    let extractedName = '';
    
    if (parts.length >= 3) {
        // Se tem pelo menos 3 partes, pegar tudo exceto as últimas 2 (timestamp e userid)
        extractedName = parts.slice(0, -2).join('_');
    } else if (parts.length === 2) {
        // Se tem 2 partes, pegar a primeira
        extractedName = parts[0];
    } else {
        // Se tem apenas 1 parte, usar ela
        extractedName = parts[0];
    }
    
    // Mostrar prompt com o nome original pré-preenchido
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
                fetchRecordings();
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
          fetchRecordings();
          alert('Arquivo deletado com sucesso!');
        } else {
          alert('Erro ao deletar: ' + result.message);
        }
      } catch (error) {
        alert('Erro ao deletar arquivo: ' + error.message);
      }
    }
  };

  const handleTranscribe = async (filename) => {
    try {
      // Iniciar o status de transcrição
      setTranscriptionStatus(prev => ({
        ...prev,
        [filename]: 'Iniciando transcrição...'
      }));

      // Passo 1: Preparando arquivo
      setTranscriptionStatus(prev => ({
        ...prev,
        [filename]: 'Preparando arquivo de áudio...'
      }));

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
      
      // Passo 2: Processando
      setTranscriptionStatus(prev => ({
        ...prev,
        [filename]: 'Processando transcrição com IA...'
      }));
      
      const result = await response.json();
      
      if (result.success) {
        // Passo 3: Finalizando
        setTranscriptionStatus(prev => ({
          ...prev,
          [filename]: 'Salvando transcrição...'
        }));
        
        await fetchRecordings();
        
        // Sucesso
        setTranscriptionStatus(prev => ({
          ...prev,
          [filename]: 'Transcrição concluída com sucesso!'
        }));
        
        // Limpar status após 3 segundos
        setTimeout(() => {
          setTranscriptionStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[filename];
            return newStatus;
          });
        }, 3000);
        
      } else {
        setTranscriptionStatus(prev => ({
          ...prev,
          [filename]: `Erro na transcrição: ${result.message}`
        }));
        
        // Limpar status de erro após 5 segundos
        setTimeout(() => {
          setTranscriptionStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[filename];
            return newStatus;
          });
        }, 5000);
      }
    } catch (error) {
      setTranscriptionStatus(prev => ({
        ...prev,
        [filename]: `Erro ao transcrever: ${error.message}`
      }));
      
      // Limpar status de erro após 5 segundos
      setTimeout(() => {
        setTranscriptionStatus(prev => {
          const newStatus = { ...prev };
          delete newStatus[filename];
        });
      }, 5000);
    }
  };

  const handleViewTranscription = async (filename) => {
    try {
      const transcriptionFile = filename.replace('.wav', '_transcricao.txt');
      const response = await fetch(`/view_transcription/${transcriptionFile}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setModalTitle(`Transcrição - ${filename}`);
          setModalContent(data.content || 'Transcrição não encontrada.');
          setModalOpen(true);
        } else {
          alert('Erro ao carregar transcrição: ' + data.message);
        }
      } else {
        alert('Erro ao carregar transcrição.');
      }
    } catch (error) {
      alert('Erro ao carregar transcrição: ' + error.message);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalContent('');
    setModalTitle('');
  };

  const handleDownloadTranscription = async (filename) => {
    try {
      const transcriptionFile = filename.replace('.wav', '_transcricao.txt');
      const response = await fetch(`/download_transcription/${transcriptionFile}`, {
        method: 'GET',
        credentials: 'include', // Importante: inclui cookies de sessão
        headers: {
          'Content-Type': 'application/json'
        }
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
        console.error('Erro no download da transcrição:', response.status);
        alert('Erro ao fazer download da transcrição');
      }
    } catch (error) {
      console.error('Erro no download da transcrição:', error);
      alert('Erro ao fazer download da transcrição');
    }
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">RecPac Dashboard</h1>
              {/* REMOVIDO: Botão "Ver Transcrições" do topo */}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Bem-vindo, {user?.username}</span>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Recording Section */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Record Audio</h2>
              <button
                onClick={fetchRecordings}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2 hover:scale-105 transition-transform"
              >
                <ArrowPathIcon className="h-5 w-5" />
                Atualizar
              </button>
            </div>
            <RecordingControls onRecordingComplete={handleRecordingComplete} onRefresh={fetchRecordings} />
          </div>

          {/* Recent Recordings */}
          <div className="lg:col-span-3 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Recordings</h2>
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : recordings.length > 0 ? (
              <div className="space-y-3">
                {recordings.slice(0, 5).map((recording, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-medium text-gray-900">{recording.filename}</p>
                        <p className="text-sm text-gray-500">{recording.modified}</p>
                        {recording.has_transcription && (
                          <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mt-1">
                            ✅ Transcrito
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Botões de Ação */}
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => handleDownload(recording.filename)}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => handleRename(recording.filename)}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        Renomear
                      </button>
                      
                      {/* Botões de transcrição */}
                      {recording.has_transcription && (
                        <>
                          <Link
                            to={`/transcription/${recording.filename.replace('.wav', '_transcricao.txt')}`}
                            className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm transition-colors inline-block text-center"
                          >
                            Ver Transcrição
                          </Link>
                          <button
                            onClick={() => handleDownloadTranscription(recording.filename)}
                            className="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1 rounded text-sm transition-colors"
                          >
                            Download Transcrição
                          </button>
                        </>
                      )}
                      
                      {/* Botão Transcrever - só mostra se não foi transcrito */}
                      {!recording.has_transcription && (
                        <button
                          onClick={() => handleTranscribe(recording.filename)}
                          disabled={transcriptionStatus[recording.filename] || false}
                          className={`px-3 py-1 rounded text-sm transition-colors ${
                            transcriptionStatus[recording.filename]
                              ? 'bg-gray-400 cursor-not-allowed'
                              : 'bg-green-500 hover:bg-green-600'
                          } text-white`}
                        >
                          {transcriptionStatus[recording.filename] 
                            ? 'Processando...' 
                            : 'Transcrever'
                          }
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDelete(recording.filename)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        Deletar
                      </button>
                      
                      {/* Status da transcrição */}
                      {transcriptionStatus[recording.filename] && (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                          <div className="flex items-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                            {transcriptionStatus[recording.filename]}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Remover este bloco duplicado de status da transcrição */}
                    {/* {transcriptionStatus[recording.filename] && (
                      <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          {transcriptionStatus[recording.filename]}
                        </div>
                      </div>
                    )} */}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">Nenhuma gravação encontrada</p>
            )}
          </div>
        </div>
      </main>

      {/* Modal de Transcrição */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Header do Modal */}
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">{modalTitle}</h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Conteúdo do Modal */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="bg-gray-50 rounded-lg p-4 min-h-[200px]">
                <pre className="whitespace-pre-wrap text-gray-800 font-mono text-sm leading-relaxed">
                  {modalContent}
                </pre>
              </div>
            </div>
            
            {/* Footer do Modal */}
            <div className="flex justify-end gap-3 p-6 border-t">
              <button
                onClick={closeModal}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors"
              >
                Fechar
              </button>
              <button
                onClick={() => {
                  const filename = modalTitle.replace('Transcrição - ', '');
                  handleDownloadTranscription(filename);
                }}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors"
              >
                Download
              </button>
            </div>
          </div>
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
              className="w-full p-3 border border-gray-300 rounded-lg mb-4"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  saveRecordingWithPatientName(e.target.value.trim());
                }
              }}
              autoFocus
            />
            <div className="flex gap-3">
              <button 
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                onClick={(e) => {
                  const input = e.target.closest('.bg-white').querySelector('input');
                  saveRecordingWithPatientName(input.value.trim());
                }}
              >
                💾 Salvar com Nome
              </button>
              <button 
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                onClick={() => saveRecordingWithPatientName('')}
              >
                📁 Salvar sem Nome
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
