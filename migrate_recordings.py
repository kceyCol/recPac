import os
import json
from utils import RECORDINGS_DIR

def migrate_recordings():
    # Carregar usuários
    with open('users.json', 'r') as f:
        users = json.load(f)
    
    for filename in os.listdir(RECORDINGS_DIR):
        if filename.endswith('.wav'):
            for email, user_data in users.items():
                old_suffix = f"_{email.replace('@', '_').replace('.', '_')}.wav"
                if filename.endswith(old_suffix):
                    new_filename = filename.replace(old_suffix, f"_{user_data['user_id']}.wav")
                    old_path = os.path.join(RECORDINGS_DIR, filename)
                    new_path = os.path.join(RECORDINGS_DIR, new_filename)
                    os.rename(old_path, new_path)
                    print(f"Renomeado: {filename} -> {new_filename}")

if __name__ == '__main__':
    migrate_recordings()