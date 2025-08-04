# Estágio 1: Build do frontend
FROM node:18-slim as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Estágio 2: Aplicação Python
FROM python:3.12-slim

# Instala FFmpeg e outras dependências do sistema
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    gcc \
    curl \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho
WORKDIR /app

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Copia o build do frontend da etapa anterior
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]