# Usar imagem oficial do Node.js para garantir compatibilidade
FROM node:18-bullseye-slim

# Instalar Python e dependências do sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    libportaudio2 \
    gcc \
    g++ \
    make \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Criar symlink para python
RUN ln -sf /usr/bin/python3 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip

# Definir diretório de trabalho
WORKDIR /app

# === BUILD DO FRONTEND PRIMEIRO ===
# Copiar package.json do frontend
COPY frontend/package*.json ./frontend/

# Instalar dependências do frontend
RUN cd frontend && npm install

# Copiar código do frontend
COPY frontend/ ./frontend/

# Build do React
RUN cd frontend && npm run build

# Verificar se o build foi criado
RUN ls -la frontend/build/ && echo "Build do React criado com sucesso!"

# === SETUP DO BACKEND ===
# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar resto da aplicação
COPY . .

# Verificação final
RUN echo "=== Verificação final ===" && \
    ls -la frontend/build/index.html && \
    echo "Frontend build encontrado com sucesso!"

# Expor porta
EXPOSE 10000

# Comando para iniciar a aplicação
CMD ["python", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]