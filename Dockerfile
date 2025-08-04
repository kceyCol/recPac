# Use uma imagem base do Python
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

# Comando para iniciar a aplicação
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]