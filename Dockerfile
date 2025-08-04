# Estágio 1: Build do frontend React
FROM node:18-slim as frontend-build

WORKDIR /app/frontend

# Copiar package.json e package-lock.json
COPY frontend/package*.json ./

# Instalar dependências (incluindo devDependencies para o build)
RUN npm ci

# Copiar todo o código do frontend
COPY frontend/ ./

# Fazer build do React com Tailwind CSS
RUN npm run build

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

# Expor porta
EXPOSE 10000

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]