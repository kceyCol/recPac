import React, { useState, useRef, useEffect } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';

const RecordingControls = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      // Configurar análise de áudio para visualização
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      // Função para atualizar nível de áudio
      const updateAudioLevel = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;
          setAudioLevel(average);
          animationRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      updateAudioLevel();
      
      // Configurar MediaRecorder com melhor qualidade
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      };
      
      // Fallback para navegadores que não suportam webm
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/mp4';
      }
      
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mediaRecorderRef.current.mimeType 
        });
        
        // Processar áudio no frontend antes de enviar
        const processedBlob = await processAudioBlob(audioBlob);
        onRecordingComplete(processedBlob);
        
        // Limpar recursos
        stream.getTracks().forEach(track => track.stop());
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };

      mediaRecorderRef.current.start(1000); // Coletar dados a cada segundo
      setIsRecording(true);
      
      // Timer para mostrar tempo de gravação
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Erro ao iniciar gravação:', error);
      alert('Erro ao acessar o microfone. Verifique as permissões.');
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

  // Função para processar áudio no frontend
  const processAudioBlob = async (blob) => {
    try {
      // Converter para ArrayBuffer
      const arrayBuffer = await blob.arrayBuffer();
      
      // Criar contexto de áudio para processamento
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Normalizar áudio
      const channelData = audioBuffer.getChannelData(0);
      let max = 0;
      for (let i = 0; i < channelData.length; i++) {
        if (Math.abs(channelData[i]) > max) {
          max = Math.abs(channelData[i]);
        }
      }
      
      if (max > 0) {
        for (let i = 0; i < channelData.length; i++) {
          channelData[i] = channelData[i] / max * 0.8; // Normalizar para 80%
        }
      }
      
      // Converter de volta para blob
      const processedBuffer = audioContext.createBuffer(
        1, // mono
        audioBuffer.length,
        16000 // 16kHz sample rate
      );
      
      processedBuffer.copyToChannel(channelData, 0);
      
      // Converter para WAV
      const wavBlob = await audioBufferToWav(processedBuffer);
      
      audioContext.close();
      return wavBlob;
      
    } catch (error) {
      console.error('Erro ao processar áudio:', error);
      return blob; // Retornar blob original em caso de erro
    }
  };

  // Função para converter AudioBuffer para WAV
  const audioBufferToWav = (buffer) => {
    const length = buffer.length;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);
    
    // Convert samples
    const channelData = buffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < length; i++) {
      const sample = Math.max(-1, Math.min(1, channelData[i]));
      view.setInt16(offset, sample * 0x7FFF, true);
      offset += 2;
    }
    
    return new Blob([arrayBuffer], { type: 'audio/wav' });
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <MicrophoneIcon className="h-6 w-6 text-blue-500" />
        Controles de Gravação
      </h2>
      
      <p className="text-gray-600 mb-6">
        Clique em "Iniciar" para começar a gravar. O áudio será processado automaticamente no seu navegador.
      </p>
      
      {isRecording && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <span className="font-medium">Gravando: {formatTime(recordingTime)}</span>
          </div>
          
          {/* Visualizador de nível de áudio */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-red-500 h-2 rounded-full transition-all duration-100"
              style={{ width: `${Math.min(100, (audioLevel / 255) * 100)}%` }}
            ></div>
          </div>
        </div>
      )}
      
      <div className="flex gap-4">
        <button
          onClick={startRecording}
          disabled={isRecording}
          className={`bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2 ${
            isRecording ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
          } transition-transform`}
        >
          <MicrophoneIcon className="h-5 w-5" />
          Iniciar Gravação
        </button>
        
        <button
          onClick={stopRecording}
          disabled={!isRecording}
          className={`bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2 ${
            !isRecording ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
          } transition-transform`}
        >
          <StopIcon className="h-5 w-5" />
          Parar Gravação
        </button>
      </div>
    </div>
  );
};

export default RecordingControls;