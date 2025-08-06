import React, { useState, useRef, useEffect } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';

const RecordingControls = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  const recordingSessionId = useRef(null);

  // Configurações para chunks
  const CHUNK_DURATION = 30000; // 30 segundos por chunk
  const MAX_CHUNK_SIZE = 5 * 1024 * 1024; // 5MB máximo por chunk

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        } 
      });

      // Gerar ID único para esta sessão de gravação
      recordingSessionId.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      // Configurar visualização de áudio
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateAudioLevel = () => {
        if (analyserRef.current && isRecording) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;
          setAudioLevel(average);
          animationRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      updateAudioLevel();
      
      // Configurar MediaRecorder com chunks automáticos
      let options = { 
        audioBitsPerSecond: 128000
      };
      
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options.mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options.mimeType = 'audio/mp4';
      }

      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];
      let chunkIndex = 0;

      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          
          // Se o chunk ficou muito grande, enviar automaticamente
          const currentSize = audioChunksRef.current.reduce((total, chunk) => total + chunk.size, 0);
          if (currentSize > MAX_CHUNK_SIZE) {
            await sendChunk(chunkIndex);
            chunkIndex++;
            audioChunksRef.current = [];
          }
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Enviar último chunk se houver dados
        if (audioChunksRef.current.length > 0) {
          await sendChunk(chunkIndex, true); // true = último chunk
        }
        
        // Limpar recursos
        stream.getTracks().forEach(track => track.stop());
        if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
          audioContextRef.current.close();
        }
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };

      // Iniciar gravação com chunks de 30 segundos
      mediaRecorderRef.current.start(CHUNK_DURATION);
      setIsRecording(true);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('❌ Erro ao iniciar gravação:', error);
      alert('Erro ao acessar o microfone. Verifique as permissões.');
    }
  };

  const sendChunk = async (chunkIndex, isLast = false) => {
    if (audioChunksRef.current.length === 0) return;

    try {
      setIsUploading(true);
      
      const chunkBlob = new Blob(audioChunksRef.current, { 
        type: mediaRecorderRef.current.mimeType 
      });
      
      console.log(`📤 Enviando chunk ${chunkIndex}: ${chunkBlob.size} bytes`);
      
      const reader = new FileReader();
      reader.onloadend = async function() {
        const base64Audio = reader.result;
        
        const response = await fetch('/api/save_chunk', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            session_id: recordingSessionId.current,
            chunk_index: chunkIndex,
            audio: base64Audio,
            is_last: isLast,
            mime_type: mediaRecorderRef.current.mimeType
          })
        });
        
        const result = await response.json();
        if (result.success) {
          console.log(`✅ Chunk ${chunkIndex} enviado com sucesso`);
          
          if (isLast) {
            // Finalizar gravação e solicitar nome do paciente
            setIsUploading(false);
            onRecordingComplete({
              session_id: recordingSessionId.current,
              total_chunks: chunkIndex + 1,
              final_filename: result.final_filename
            });
          }
        } else {
          throw new Error(result.message);
        }
      };
      
      reader.readAsDataURL(chunkBlob);
      
    } catch (error) {
      console.error(`❌ Erro ao enviar chunk ${chunkIndex}:`, error);
      setIsUploading(false);
      alert(`Erro ao enviar parte da gravação: ${error.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingTime(0);
      setAudioLevel(0);
      clearInterval(timerRef.current);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <MicrophoneIcon className="h-6 w-6 mr-2 text-blue-600" />
        Controles de Gravação
      </h2>
      
      <p className="text-gray-600 mb-4">
        Sistema otimizado para gravações longas. O áudio é enviado automaticamente em pequenos pedaços.
      </p>
      
      <div className="flex space-x-4 mb-4">
        <button
          onClick={startRecording}
          disabled={isRecording || isUploading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <MicrophoneIcon className="h-5 w-5 mr-2" />
          Iniciar Gravação
        </button>
        
        <button
          onClick={stopRecording}
          disabled={!isRecording || isUploading}
          className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <StopIcon className="h-5 w-5 mr-2" />
          Parar Gravação
        </button>
      </div>
      
      {(isRecording || isUploading) && (
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium">Tempo:</span>
            <span className="text-lg font-mono">{formatTime(recordingTime)}</span>
          </div>
          
          {isRecording && (
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium">Nível:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-100"
                  style={{ width: `${Math.min(audioLevel, 100)}%` }}
                />
              </div>
            </div>
          )}
          
          {isUploading && (
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium">Enviando:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '100%' }} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RecordingControls;