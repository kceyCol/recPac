import json
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Carregar usuários
with open('users.json', 'r', encoding='utf-8') as f:
    users = json.load(f)

# Atualizar senha para alekcey@me.com
users['alekcey@me.com']['password'] = hash_password('123456')

# Salvar
with open('users.json', 'w', encoding='utf-8') as f:
    json.dump(users, f, indent=2, ensure_ascii=False)

print("✅ Senha atualizada para alekcey@me.com")
print("Nova senha: 123456")