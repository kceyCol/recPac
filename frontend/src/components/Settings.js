import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

const Settings = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(1);
  const [prompts, setPrompts] = useState({
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
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  // Carregar configurações salvas
  useEffect(() => {
    const savedPrompts = localStorage.getItem('customPrompts');
    const savedLabels = localStorage.getItem('promptLabels');
    
    if (savedPrompts) {
      setPrompts(JSON.parse(savedPrompts));
    }
    
    if (savedLabels) {
      setPromptLabels(JSON.parse(savedLabels));
    }
  }, []);

  const handlePromptChange = (promptKey, value) => {
    setPrompts(prev => ({
      ...prev,
      [promptKey]: value
    }));
  };

  const handleLabelChange = (labelKey, value) => {
    setPromptLabels(prev => ({
      ...prev,
      [labelKey]: value
    }));
  };

  const saveSettings = () => {
    setSaving(true);
    
    try {
      localStorage.setItem('customPrompts', JSON.stringify(prompts));
      localStorage.setItem('promptLabels', JSON.stringify(promptLabels));
      
      setMessage('✅ Configurações salvas com sucesso!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('❌ Erro ao salvar configurações');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    const defaultPrompts = {
      prompt1: 'Atue como um neurocirurgião experiente, com vasta prática clínica, e analise de forma detalhada um paciente em consulta neurocirúrgica. A partir das informações clínicas que vou fornecer, extraia o máximo possível de detalhes relevantes para diagnóstico, conduta e planejamento terapêutico.',
      prompt2: 'Analise esta consulta médica e forneça um resumo estruturado com: 1) Queixa principal, 2) História da doença atual, 3) Exame físico, 4) Hipóteses diagnósticas, 5) Conduta proposta.',
      prompt3: 'Extraia desta transcrição médica todos os sintomas, sinais clínicos, medicamentos mencionados e organize em formato de prontuário médico.',
      prompt4: 'Identifique nesta consulta os principais pontos para seguimento do paciente, incluindo retornos, exames solicitados e orientações dadas.',
      prompt5: 'Crie um relatório médico formal baseado nesta transcrição, adequado para encaminhamentos e documentação hospitalar.'
    };
    
    const defaultLabels = {
      label1: '🧠 Análise Neurocirúrgica',
      label2: '📋 Resumo Estruturado',
      label3: '📝 Prontuário Médico',
      label4: '📅 Seguimento',
      label5: '📄 Relatório Formal'
    };
    
    setPrompts(defaultPrompts);
    setPromptLabels(defaultLabels);
  };

  const renderTabContent = (tabNumber) => {
    const promptKey = `prompt${tabNumber}`;
    const labelKey = `label${tabNumber}`;
    
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nome do Botão:
          </label>
          <input
            type="text"
            value={promptLabels[labelKey]}
            onChange={(e) => handleLabelChange(labelKey, e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder={`Nome para o botão ${tabNumber}`}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Conteúdo do Prompt:
          </label>
          <textarea
            value={prompts[promptKey]}
            onChange={(e) => handlePromptChange(promptKey, e.target.value)}
            className="w-full h-40 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder={`Digite o prompt personalizado ${tabNumber}...`}
          />
        </div>
        
        <div className="text-sm text-gray-500">
          <strong>Dica:</strong> Este prompt será enviado junto com a transcrição para o Gemini AI quando você clicar no botão correspondente.
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="text-blue-500 hover:text-blue-600">
                ← Voltar para Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">⚙️ Configurações</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                👤 Olá, {user?.name || 'Usuário'}
              </span>
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
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Header da seção */}
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              🤖 Prompts Personalizados para Gemini AI
            </h2>
            <p className="text-gray-600 text-sm">
              Configure até 5 prompts personalizados que aparecerão como botões na página de edição de transcrição.
            </p>
          </div>

          {message && (
            <div className="mx-6 mt-4 p-3 rounded-md bg-green-50 border border-green-200 text-green-700">
              {message}
            </div>
          )}

          {/* Abas */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[1, 2, 3, 4, 5].map(num => (
                <button
                  key={num}
                  onClick={() => setActiveTab(num)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === num
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {promptLabels[`label${num}`] || `Prompt ${num}`}
                </button>
              ))}
            </nav>
          </div>

          {/* Conteúdo da aba ativa */}
          <div className="p-6">
            {renderTabContent(activeTab)}
          </div>

          {/* Botões de ação */}
          <div className="flex justify-between items-center p-6 bg-gray-50 border-t border-gray-200">
            <button
              onClick={resetToDefaults}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-md transition-colors"
            >
              🔄 Restaurar Padrões
            </button>
            
            <button
              onClick={saveSettings}
              disabled={saving}
              className={`px-6 py-2 rounded-md transition-colors ${
                saving
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              {saving ? '💾 Salvando...' : '💾 Salvar Configurações'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Settings;