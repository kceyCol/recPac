from flask import Blueprint, request, jsonify, session
import hashlib
import json
import os
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)
USERS_FILE = 'users.json'

def load_users():
    """Carrega usuários do arquivo JSON"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Salva usuários no arquivo JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_password(password):
    """Gera hash SHA256 da senha"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============= ROTAS DE API =============

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API de login"""
    try:
        # Verificar se os dados foram enviados
        if not request.json:
            return jsonify({
                'success': False,
                'message': 'Dados não enviados'
            }), 400
        
        email = request.json.get('email', '').strip().lower()
        password = request.json.get('password', '')
        
        # Validar campos obrigatórios
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Carregar usuários
        users = load_users()
        
        # Verificar se usuário existe e senha está correta
        if email in users:
            stored_hash = users[email]['password']
            input_hash = hash_password(password)
            
            if stored_hash == input_hash:
                # Login bem-sucedido - limpar e configurar sessão
                session.clear()
                session['user_email'] = email
                session['user_name'] = users[email]['name']
                session['user_id'] = users[email]['user_id']  # ← LINHA ADICIONADA
                session.permanent = True
                
                return jsonify({
                    'success': True,
                    'message': 'Login realizado com sucesso!',
                    'user': {
                        'email': email,
                        'name': users[email]['name']
                    }
                }), 200
        
        # Login falhou
        return jsonify({
            'success': False,
            'message': 'Email ou senha incorretos'
        }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API de registro"""
    try:
        if not request.json:
            return jsonify({
                'success': False,
                'message': 'Dados não enviados'
            }), 400
        
        name = request.json.get('name', '').strip()
        email = request.json.get('email', '').strip().lower()
        password = request.json.get('password', '')
        
        # Validar campos
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'message': 'Todos os campos são obrigatórios'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Senha deve ter pelo menos 6 caracteres'
            }), 400
        
        # Carregar usuários existentes
        users = load_users()
        
        # Verificar se email já existe
        if email in users:
            return jsonify({
                'success': False,
                'message': 'Este email já está cadastrado'
            }), 400
        
        # Criar novo usuário
        users[email] = {
            'name': name,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat(),
            'user_id': hashlib.md5(email.encode()).hexdigest()[:8]
        }
        
        # Salvar usuários
        save_users(users)
        
        return jsonify({
            'success': True,
            'message': 'Cadastro realizado com sucesso!'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Verificar status de autenticação"""
    try:
        if 'user_email' in session and 'user_name' in session:
            return jsonify({
                'authenticated': True,
                'user': {
                    'email': session['user_email'],
                    'name': session['user_name']
                }
            }), 200
        else:
            return jsonify({
                'authenticated': False
            }), 401
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API de logout"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro no logout: {str(e)}'
        }), 500

# ============= ROTA PARA CRIAR USUÁRIO DE TESTE =============

@auth_bp.route('/create-test-user', methods=['GET'])
def create_test_user():
    """Criar usuário de teste"""
    try:
        users = load_users()
        
        test_users = {
            'admin@test.com': {
                'name': 'Administrador',
                'password': hash_password('123456'),
                'created_at': datetime.now().isoformat(),
                'user_id': 'admin123'
            },
            'user@test.com': {
                'name': 'Usuário Teste',
                'password': hash_password('password'),
                'created_at': datetime.now().isoformat(),
                'user_id': 'user123'
            }
        }
        
        # Adicionar usuários de teste
        users.update(test_users)
        save_users(users)
        
        return '''
        <h2>✅ Usuários de teste criados com sucesso!</h2>
        <p><strong>Credenciais:</strong></p>
        <ul>
            <li>📧 admin@test.com / 123456</li>
            <li>📧 user@test.com / password</li>
        </ul>
        <p><a href="http://localhost:3000">← Voltar para o login</a></p>
        '''
        
    except Exception as e:
        return f'❌ Erro ao criar usuários de teste: {str(e)}'