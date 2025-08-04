FROM node:18

# Instalar Python
RUN apt-get update && apt-get install -y python3 python3-pip portaudio19-dev libportaudio2 gcc ffmpeg
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Build frontend
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Install Python deps
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy app
COPY . .

EXPOSE 10000
CMD ["python3", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:10000"]