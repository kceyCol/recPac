import json
import hashlib
from datetime import datetime

def generate_user_id(email):
    """Gera um ID único baseado no email"""
    hash_object = hashlib.md5(email.encode())
    return hash_object.hexdigest()[:8]

def migrate_users():
    """Adiciona user_id único para usuários existentes"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        for email, user_data in users.items():
            if 'user_id' not in user_data:
                user_data['user_id'] = generate_user_id(email)
                print(f"✅ ID gerado para {email}: {user_data['user_id']}")
        
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")

if __name__ == '__main__':
    migrate_users()