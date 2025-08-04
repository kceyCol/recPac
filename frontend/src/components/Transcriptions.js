import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

function Transcriptions() {
  const { user, logout } = useAuth();
  const [transcriptions, setTranscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTranscription, setSelectedTranscription] = useState(null);

  useEffect(() => {
    fetchTranscriptions();
  }, []);

  const fetchTranscriptions = async () => {
    try {
      const response = await fetch('/api/transcriptions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTranscriptions(data.transcriptions || []);
      }
    } catch (error) {
      console.error('Error fetching transcriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (transcriptionId, format) => {
    try {
      const response = await fetch(`/api/download/${format}/${transcriptionId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcription.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-blue-500 hover:text-blue-600">
                ← Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">Transcriptions</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user?.username}</span>
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Transcriptions List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">All Transcriptions</h2>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : transcriptions.length > 0 ? (
                <div className="space-y-3">
                  {transcriptions.map((transcription, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-md cursor-pointer transition-colors ${
                        selectedTranscription === transcription
                          ? 'bg-blue-50 border-blue-200 border'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedTranscription(transcription)}
                    >
                      <p className="font-medium text-gray-900">{transcription.filename}</p>
                      <p className="text-sm text-gray-500">{transcription.date}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No transcriptions yet</p>
              )}
            </div>
          </div>

          {/* Transcription Details */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              {selectedTranscription ? (
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">
                        {selectedTranscription.filename}
                      </h3>
                      <p className="text-sm text-gray-500">{selectedTranscription.date}</p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleDownload(selectedTranscription.id, 'pdf')}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        PDF
                      </button>
                      <button
                        onClick={() => handleDownload(selectedTranscription.id, 'docx')}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        DOCX
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Original Transcription</h4>
                      <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-gray-700 whitespace-pre-wrap">
                          {selectedTranscription.original_text || 'No original transcription available'}
                        </p>
                      </div>
                    </div>
                    
                    {selectedTranscription.improved_text && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Improved Transcription</h4>
                        <div className="bg-blue-50 p-4 rounded-md">
                          <p className="text-gray-700 whitespace-pre-wrap">
                            {selectedTranscription.improved_text}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {selectedTranscription.summary && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
                        <div className="bg-green-50 p-4 rounded-md">
                          <p className="text-gray-700 whitespace-pre-wrap">
                            {selectedTranscription.summary}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500">Select a transcription to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Transcriptions;