# Estágio 1: Build do frontend React
FROM node:18-slim as frontend-build

WORKDIR /app/frontend

# Debug: Verificar versão do Node
RUN node --version && npm --version

# Copiar package.json e package-lock.json
COPY frontend/package*.json ./

# Debug: Mostrar conteúdo do package.json
RUN cat package.json

# Instalar dependências (incluindo devDependencies para o build)
RUN npm ci --verbose

# Copiar todo o código do frontend
COPY frontend/ ./

# Debug: Listar arquivos copiados
RUN ls -la

# Fazer build do React com Tailwind CSS
RUN npm run build --verbose

# Debug: Verificar se o build foi criado
RUN ls -la build/ || echo "Build directory not created!"

# Estágio 2: Aplicação Python
FROM python:3.12-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    gcc \
    curl \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Copiar build do frontend do estágio anterior
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Debug: Verificar se o build foi copiado
RUN ls -la frontend/ || echo "Frontend directory not found!"
RUN ls -la frontend/build/ || echo "Frontend build directory not found!"
RUN ls -la frontend/build/index.html || echo "Frontend index.html not found!"

# Expor porta
EXPOSE 10000

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]