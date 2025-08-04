import os
import json

# Carregar usuários para pegar o user_id atual
with open('users.json', 'r') as f:
    users = json.load(f)

# Assumindo que você quer usar admin@test.com
current_user_id = users['admin@test.com']['user_id']
old_user_id = '4cdfe8a1'

recordings_dir = 'recordings'
transcriptions_dir = 'transcriptions'

# Renomear arquivos de gravação
for filename in os.listdir(recordings_dir):
    if filename.endswith(f'_{old_user_id}.wav'):
        new_filename = filename.replace(f'_{old_user_id}.wav', f'_{current_user_id}.wav')
        old_path = os.path.join(recordings_dir, filename)
        new_path = os.path.join(recordings_dir, new_filename)
        os.rename(old_path, new_path)
        print(f"✅ Renomeado: {filename} -> {new_filename}")

# Renomear arquivos de transcrição
for filename in os.listdir(transcriptions_dir):
    if filename.endswith(f'_{old_user_id}_transcricao.txt'):
        new_filename = filename.replace(f'_{old_user_id}_transcricao.txt', f'_{current_user_id}_transcricao.txt')
        old_path = os.path.join(transcriptions_dir, filename)
        new_path = os.path.join(transcriptions_dir, new_filename)
        os.rename(old_path, new_path)
        print(f"✅ Renomeado: {filename} -> {new_filename}")

print("🎯 Migração concluída! Agora faça login com admin@test.com")