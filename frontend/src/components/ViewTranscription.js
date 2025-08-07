import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link, useParams } from 'react-router-dom';

const ViewTranscription = () => {
  const { user, logout } = useAuth();
  const { filename } = useParams();
  const [transcription, setTranscription] = useState('');
  const [originalTranscription, setOriginalTranscription] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sendingToGemini, setSendingToGemini] = useState(false);
  const [geminiResponse, setGeminiResponse] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  
  // Estado para o prompt personalizado
  const [customPrompt, setCustomPrompt] = useState('');
  
  // Estados para prompts personalizados
  const [customPrompts, setCustomPrompts] = useState({
    prompt1: '',
    prompt2: '',
    prompt3: '',
    prompt4: '',
    prompt5: ''
  });
  const [promptLabels, setPromptLabels] = useState({
    label1: 'Prompt 1',
    label2: 'Prompt 2',
    label3: 'Prompt 3', 
    label4: 'Prompt 4',
    label5: 'Prompt 5'
  });
  
  // Estado para o sistema de log
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);

  // Função para adicionar log
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const newLog = {
      id: Date.now(),
      timestamp,
      message,
      type // 'info', 'success', 'error', 'warning'
    };
    setLogs(prev => [...prev, newLog]);
    setShowLogs(true);
  };

  // Função para limpar logs
  const clearLogs = () => {
    setLogs([]);
    setShowLogs(false);
  };

  // Carregar prompts personalizados
  useEffect(() => {
    const savedPrompts = localStorage.getItem('customPrompts');
    const savedLabels = localStorage.getItem('promptLabels');
    
    if (savedPrompts) {
      setCustomPrompts(JSON.parse(savedPrompts));
    }
    
    if (savedLabels) {
      setPromptLabels(JSON.parse(savedLabels));
    }
  }, []);

  // Função para aplicar prompt personalizado
  const applyCustomPrompt = (promptKey) => {
    const prompt = customPrompts[promptKey];
    if (prompt.trim()) {
      setCustomPrompt(prompt);
      addLog(`Prompt "${promptLabels[promptKey.replace('prompt', 'label')]}" aplicado`);
    }
  };

  useEffect(() => {
    if (filename) {
      addLog('Iniciando carregamento da transcrição...');
      fetchTranscription();
      fetchDefaultPrompt();
    }
  }, [filename]);

  const fetchTranscription = async () => {
    try {
      addLog('Buscando arquivo de transcrição...');
      const transcriptionFile = filename.replace('.wav', '_transcricao.txt');
      const response = await fetch(`/view_transcription/${transcriptionFile}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setTranscription(data.content);
          setOriginalTranscription(data.content);
          addLog('Transcrição carregada com sucesso!', 'success');
        } else {
          addLog('Erro: ' + data.message, 'error');
          alert('Erro ao carregar transcrição: ' + data.message);
        }
      } else {
        addLog('Erro na requisição da transcrição', 'error');
        alert('Erro ao carregar transcrição.');
      }
    } catch (error) {
      addLog('Erro de conexão: ' + error.message, 'error');
      alert('Erro ao carregar transcrição: ' + error.message);
    } finally {
      setLoading(false);
      addLog('Carregamento finalizado.');
    }
  };

  // Função para buscar o prompt padrão
  const fetchDefaultPrompt = async () => {
    try {
      addLog('Carregando prompt personalizado...');
      
      // Carregar o primeiro prompt personalizado do localStorage
      const savedPrompts = localStorage.getItem('customPrompts');
      
      if (savedPrompts) {
        const prompts = JSON.parse(savedPrompts);
        if (prompts.prompt1 && prompts.prompt1.trim()) {
          setCustomPrompt(prompts.prompt1);
          addLog('Prompt personalizado (Farmacologia Clínica) carregado!', 'success');
          return;
        }
      }
      
      // Fallback para o prompt padrão se não houver prompt personalizado
      const response = await fetch('/api/default_prompt', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCustomPrompt(data.prompt);
        addLog('Prompt padrão carregado com sucesso!', 'success');
      } else {
        addLog('Erro ao carregar prompt padrão', 'warning');
        console.error('Erro ao carregar prompt padrão');
      }
    } catch (error) {
      addLog('Erro de conexão ao carregar prompt: ' + error.message, 'warning');
      console.error('Erro ao carregar prompt padrão:', error);
    }
  };

  const handleTranscriptionChange = (e) => {
    const newValue = e.target.value;
    setTranscription(newValue);
    setHasChanges(newValue !== originalTranscription);
  };

  const saveTranscription = async () => {
    if (!hasChanges) return;
    
    setSaving(true);
    addLog('Iniciando salvamento da transcrição...');
    
    try {
      addLog('Enviando dados para o servidor...');
      const response = await fetch('/api/save_transcription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          filename: filename.replace('.wav', '_transcricao.txt'),
          content: transcription
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setOriginalTranscription(transcription);
          setHasChanges(false);
          addLog('Transcrição salva com sucesso!', 'success');
        } else {
          addLog('Erro ao salvar: ' + data.message, 'error');
          alert('Erro ao salvar: ' + data.message);
        }
      } else {
        addLog('Erro na requisição de salvamento', 'error');
        alert('Erro ao salvar transcrição.');
      }
    } catch (error) {
      addLog('Erro de conexão no salvamento: ' + error.message, 'error');
      alert('Erro ao salvar: ' + error.message);
    } finally {
      setSaving(false);
      addLog('Processo de salvamento finalizado.');
    }
  };

  const sendToGemini = async () => {
    if (!transcription.trim()) {
      addLog('Transcrição vazia - cancelando envio ao Gemini', 'warning');
      alert('Por favor, certifique-se de que há conteúdo na transcrição.');
      return;
    }

    if (!customPrompt.trim()) {
      addLog('Prompt vazio - cancelando envio ao Gemini', 'warning');
      alert('Por favor, defina um prompt para enviar ao Gemini.');
      return;
    }

    setSendingToGemini(true);
    addLog('Iniciando análise com Gemini AI...');
    
    try {
      addLog('Preparando dados para envio...');
      addLog('Enviando transcrição e prompt para o Gemini...');
      
      const response = await fetch('/api/generate_summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          transcription: transcription,
          custom_prompt: customPrompt,
          filename: filename
        })
      });
      
      if (response.ok) {
        addLog('Processando resposta do Gemini...');
        const data = await response.json();
        setGeminiResponse(data.summary);
        addLog('Análise do Gemini concluída com sucesso!', 'success');
        addLog('Resumo salvo automaticamente no servidor.', 'success');
      } else {
        const errorData = await response.json();
        addLog('Erro na análise do Gemini: ' + errorData.error, 'error');
        alert('Erro na análise do Gemini: ' + errorData.error);
      }
    } catch (error) {
      addLog('Erro de conexão com Gemini: ' + error.message, 'error');
      alert('Erro ao enviar para Gemini: ' + error.message);
    } finally {
      setSendingToGemini(false);
      addLog('Processo de análise finalizado.');
    }
  };

  const exportToPDF = async () => {
    if (!geminiResponse) {
      addLog('Nenhuma análise disponível para exportar', 'warning');
      alert('Nenhuma análise do Gemini disponível para exportar.');
      return;
    }

    addLog('Iniciando exportação para PDF...');
    
    try {
      const transcriptionFilename = filename.replace('.wav', '_transcricao.txt');
      addLog('Solicitando geração do PDF...');
      
      const response = await fetch(`/api/export_summary_pdf/${encodeURIComponent(transcriptionFilename)}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        addLog('PDF gerado com sucesso!');
        addLog('Iniciando download...', 'success');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = transcriptionFilename.replace('_transcricao.txt', '_resumo.pdf');
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        addLog('Download do PDF concluído!', 'success');
      } else {
        const errorData = await response.json();
        addLog('Erro ao exportar PDF: ' + errorData.message, 'error');
        alert('Erro ao exportar PDF: ' + errorData.message);
      }
    } catch (error) {
      addLog('Erro de conexão na exportação PDF: ' + error.message, 'error');
      alert('Erro ao exportar PDF: ' + error.message);
    }
  };

  const exportToWord = async () => {
    if (!geminiResponse) {
      addLog('Nenhuma análise disponível para exportar', 'warning');
      alert('Nenhuma análise do Gemini disponível para exportar.');
      return;
    }

    addLog('Iniciando exportação para Word...');
    
    try {
      const transcriptionFilename = filename.replace('.wav', '_transcricao.txt');
      addLog('Solicitando geração do DOCX...');
      
      const response = await fetch(`/api/export_summary_docx/${encodeURIComponent(transcriptionFilename)}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        addLog('DOCX gerado com sucesso!');
        addLog('Iniciando download...', 'success');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = transcriptionFilename.replace('_transcricao.txt', '_resumo.docx');
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        addLog('Download do DOCX concluído!', 'success');
      } else {
        const errorData = await response.json();
        addLog('Erro ao exportar Word: ' + errorData.message, 'error');
        alert('Erro ao exportar Word: ' + errorData.message);
      }
    } catch (error) {
      addLog('Erro de conexão na exportação Word: ' + error.message, 'error');
      alert('Erro ao exportar Word: ' + error.message);
    }
  };

  const downloadTranscription = async () => {
    try {
      const transcriptionFile = filename.replace('.wav', '_transcricao.txt');
      const response = await fetch(`/download_transcription/${encodeURIComponent(transcriptionFile)}`, {
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
        const errorData = await response.json();
        alert('Erro ao fazer download: ' + errorData.message);
      }
    } catch (error) {
      alert('Erro ao fazer download: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-blue-600 hover:text-blue-800 font-medium">
                ← Voltar para o Dashboard
              </Link>
              <h1 className="text-xl font-semibold text-gray-900">Editar Transcrição</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Olá, {user?.name}</span>
              <Link
                to="/settings"
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                title="Configurações"
              >
                ⚙️
              </Link>
              <button
                onClick={logout}
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Editor de Transcrição */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3" style={{fontSize: '90%'}}>
                Transcrição - {filename}
              </h2>
              <div className="flex space-x-2">
                <button
                  onClick={saveTranscription}
                  disabled={!hasChanges || saving}
                  className={`px-4 py-2 rounded-md text-sm transition-colors ${
                    hasChanges && !saving
                      ? 'bg-green-500 hover:bg-green-600 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {saving ? 'Salvando...' : 'Salvar'}
                </button>
                <button
                  onClick={downloadTranscription}
                  className="px-4 py-2 rounded-md text-sm bg-blue-500 hover:bg-blue-600 text-white transition-colors"
                  title="Baixar arquivo de transcrição"
                >
                  📄 Download Transcrição
                </button>
              </div>
            </div>
            
            <textarea
              value={transcription}
              onChange={handleTranscriptionChange}
              className="w-full h-64 p-4 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Edite sua transcrição aqui..."
            />
            
            {hasChanges && (
              <p className="text-sm text-orange-600 mt-2">
                ⚠️ Você tem alterações não salvas
              </p>
            )}
          </div>

          {/* Seção do Gemini */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4" style={{fontSize: '90%'}}>
              🤖 Análise com Gemini AI
            </h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prompt Personalizado:
              </label>
              
              {/* Botões de prompts personalizados */}
              <div className="mb-3 flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5].map(num => {
                  const promptKey = `prompt${num}`;
                  const labelKey = `label${num}`;
                  const hasPrompt = customPrompts[promptKey]?.trim();
                  
                  return (
                    <button
                      key={num}
                      onClick={() => applyCustomPrompt(promptKey)}
                      disabled={!hasPrompt}
                      className={`px-3 py-1 rounded-md text-xs transition-colors ${
                        hasPrompt
                          ? 'bg-purple-100 hover:bg-purple-200 text-purple-700 border border-purple-300'
                          : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'
                        }`}
                      title={hasPrompt ? customPrompts[promptKey] : 'Prompt não configurado'}
                    >
                      {promptLabels[labelKey] || `Prompt ${num}`}
                    </button>
                  );
                })}
              </div>
              
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="w-full h-32 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Digite seu prompt personalizado aqui..."
              />
              
              <div className="flex justify-between items-center mt-3">
                <button
                  onClick={sendToGemini}
                  disabled={sendingToGemini || !transcription.trim() || !customPrompt.trim()}
                  className={`px-4 py-2 rounded-md text-sm transition-colors ${
                    sendingToGemini || !transcription.trim() || !customPrompt.trim()
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-purple-500 hover:bg-purple-600 text-white'
                  }`}
                >
                  {sendingToGemini ? '🔄 Processando...' : '🚀 Enviar ao Gemini'}
                </button>
                
                {geminiResponse && (
                  <div className="flex space-x-2">
                    <button
                      onClick={exportToPDF}
                      className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded-md text-sm transition-colors flex items-center gap-1"
                      title="Exportar como PDF"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                      PDF
                    </button>
                    
                    <button
                      onClick={exportToWord}
                      className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded-md text-sm transition-colors flex items-center gap-1"
                      title="Exportar como Word"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                      Word
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {geminiResponse ? (
              <div className="bg-purple-50 p-4 rounded-md">
                <h3 className="font-medium text-purple-900 mb-2">Resposta:</h3>
                <div className="text-purple-800 whitespace-pre-wrap">
                  {geminiResponse}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>Configure o prompt e clique em "Enviar ao Gemini" para obter uma análise da transcrição</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Sistema de Log */}
      {showLogs && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-blue-800 font-semibold">📋 Log de Atividades</h3>
              <div className="space-x-2">
                <button
                  onClick={() => setShowLogs(false)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Minimizar
                </button>
                <button
                  onClick={clearLogs}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Limpar
                </button>
              </div>
            </div>
            <div className="max-h-40 overflow-y-auto space-y-1 bg-white rounded p-3 border border-blue-100">
              {logs.map(log => (
                <div key={log.id} className="flex items-start space-x-2 text-sm">
                  <span className="text-gray-500 text-xs font-mono">{log.timestamp}</span>
                  <span className={`${
                    log.type === 'success' ? 'text-green-600' :
                    log.type === 'error' ? 'text-red-600' :
                    log.type === 'warning' ? 'text-yellow-600' :
                    'text-blue-600'
                  }`}>
                    {log.type === 'success' ? '✅' :
                     log.type === 'error' ? '❌' :
                     log.type === 'warning' ? '⚠️' : 'ℹ️'}
                  </span>
                  <span className={`${
                    log.type === 'success' ? 'text-green-700' :
                    log.type === 'error' ? 'text-red-700' :
                    log.type === 'warning' ? 'text-yellow-700' :
                    'text-gray-700'
                  }`}>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Botão para mostrar logs quando minimizado */}
      {!showLogs && logs.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
          <button
            onClick={() => setShowLogs(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors shadow-md"
          >
            📋 Mostrar Log de Atividades ({logs.length} registros)
          </button>
        </div>
      )}
    </div>
  );
};

export default ViewTranscription;