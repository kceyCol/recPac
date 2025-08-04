# Usar uma imagem que tenha tanto Python quanto Node.js
FROM python:3.12-slim

# Instalar dependências do sistema e Node.js
RUN apt-get update && apt-get install -y \
    curl \
    portaudio19-dev \
    libportaudio2 \
    gcc \
    ffmpeg \
    ca-certificates \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalação do Node.js
RUN node --version && npm --version

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python primeiro
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar apenas os arquivos necessários para o build do frontend
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend

# Instalar dependências do frontend
RUN npm ci --verbose

# Copiar o resto do código do frontend
COPY frontend/ ./

# Debug: Verificar arquivos copiados
RUN echo "=== Arquivos no diretório frontend ===" && ls -la
RUN echo "=== Conteúdo do package.json ===" && cat package.json

# Fazer build do React
RUN echo "=== Iniciando build do React ===" && npm run build --verbose

# Debug: Verificar se o build foi criado
RUN echo "=== Verificando build criado ===" && ls -la build/ && echo "=== Conteúdo do build ===" && find build/ -type f | head -10

# Voltar para o diretório principal e copiar o resto da aplicação
WORKDIR /app
COPY . .

# Debug final: Verificar estrutura completa
RUN echo "=== Estrutura final da aplicação ===" && ls -la
RUN echo "=== Verificando frontend/build ===" && ls -la frontend/build/ || echo "ERRO: frontend/build não existe!"
RUN echo "=== Verificando index.html ===" && ls -la frontend/build/index.html || echo "ERRO: index.html não encontrado!"

# Expor porta
EXPOSE 10000

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]