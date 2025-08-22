# RecPac - Aplicativo de Gravação e Transcrição de Áudio

RecPac é um aplicativo web completo para gravação, transcrição e gerenciamento de conversas de áudio, com integração de IA para análise e resposta automática.

## 🚀 Tecnologias

- **Frontend**: React 18 + Material-UI + Vite
- **Backend**: Node.js + Express + MongoDB
- **Serviços Python**: Flask + Google Gemini API
- **Containerização**: Docker + Docker Compose
- **Autenticação**: JWT
- **Áudio**: Web Audio API + WAV + **Compatibilidade Multi-Formato**

## 📋 Funcionalidades

- ✅ Sistema de autenticação seguro
- ✅ Gravação de áudio em formato WAV
- ✅ **Compatibilidade Multi-Dispositivo** (iOS, Android, Desktop)
- ✅ **Processamento Robusto de Áudio** (WebM/Opus, MP3, M4A/AAC, etc.)
- ✅ Transcrição automática usando IA
- ✅ Geração de resumos inteligentes
- ✅ Respostas personalizadas via Gemini API
- ✅ Síntese de voz (Text-to-Speech)
- ✅ Gerenciamento completo de arquivos
- ✅ Interface moderna com Material-UI
- ✅ Busca e histórico de conversas

## 🛠️ Instalação e Execução

### Pré-requisitos

- Docker e Docker Compose
- Node.js 18+ (para desenvolvimento local)
- Python 3.11+ (para desenvolvimento local)
- Chave da API Google Gemini

### Execução com Docker (Recomendado)

1. Clone o repositório:
```bash
git clone <repository-url>
cd RecPac
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. Execute o projeto:
```bash
npm run dev
```

### Execução Local (Desenvolvimento)

1. Instale as dependências:
```bash
npm run install:all
```

2. Execute os serviços separadamente:
```bash
# Terminal 1 - MongoDB
docker run -d -p 27017:27017 mongo:6.0

# Terminal 2 - Backend
npm run dev:backend

# Terminal 3 - Python Services
npm run dev:python

# Terminal 4 - Frontend
npm run dev:frontend
```

## 🧪 Testes

```bash
# Executar todos os testes
npm test

# Testes específicos
npm run test:frontend
npm run test:backend
```

## 🔧 Correções de Áudio Implementadas

### **Problema Resolvido:**
- **Velocidade lenta do áudio WAV** durante reprodução e transcrição
- **Incompatibilidade de formatos** entre frontend e backend
- **Processamento inadequado** de áudio de diferentes dispositivos

### **Soluções Implementadas:**
- ✅ **Detecção automática de formato** baseada no cabeçalho do arquivo
- ✅ **Compatibilidade multi-dispositivo** (iOS, Android, Windows, Mac, Linux)
- ✅ **Preservação de sample rate** para evitar problemas de velocidade
- ✅ **Processamento robusto** com fallbacks inteligentes
- ✅ **Exportação WAV otimizada** com parâmetros específicos

### **Formatos Suportados:**
- **WebM/Opus** (Android, Chrome, Firefox)
- **WAV** (Windows, Mac, dispositivos móveis)
- **MP3** (iOS, Android, dispositivos legados)
- **M4A/AAC** (iOS, alguns Android)
- **OGG** (Linux/Android)
- **FLAC** (alta qualidade)
- **AMR** (dispositivos móveis antigos)

### **Documentação Detalhada:**
Para informações completas sobre as correções implementadas, consulte: [`AUDIO_FIXES_DOCUMENTATION.md`](AUDIO_FIXES_DOCUMENTATION.md)

## 📁 Estrutura do Projeto