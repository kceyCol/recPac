# Usar uma imagem que tenha tanto Python quanto Node.js
FROM python:3.12-slim

# Instalar Node.js
RUN apt-get update && apt-get install -y \
    curl \
    portaudio19-dev \
    libportaudio2 \
    gcc \
    ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Build do frontend React
WORKDIR /app/frontend
RUN npm ci
RUN npm run build

# Voltar para o diretório principal
WORKDIR /app

# Debug: Verificar se o build foi criado
RUN ls -la frontend/build/ || echo "Build not created!"

# Expor porta
EXPOSE 10000

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]