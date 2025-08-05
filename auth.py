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
    import logging
    import sys
    
    # Configurar logging para aparecer no Render
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔍 [LOGIN] Iniciando processo de login")
        logger.info(f"🔍 [LOGIN] Request method: {request.method}")
        logger.info(f"🔍 [LOGIN] Content type: {request.content_type}")
        
        # Verificar se os dados foram enviados
        if not request.json:
            logger.error(f"❌ [LOGIN] Dados não enviados - request.json é None")
            return jsonify({
                'success': False,
                'message': 'Dados não enviados'
            }), 400
        
        logger.info(f"🔍 [LOGIN] Request JSON recebido")
        
        email = request.json.get('email', '').strip().lower()
        password = request.json.get('password', '')
        
        logger.info(f"🔍 [LOGIN] Email: '{email}', Password length: {len(password)}")
        
        # Validar campos obrigatórios
        if not email or not password:
            logger.error(f"❌ [LOGIN] Campos obrigatórios ausentes")
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Carregar usuários
        logger.info(f"🔍 [LOGIN] Carregando usuários...")
        users = load_users()
        logger.info(f"🔍 [LOGIN] Usuários encontrados: {len(users)} usuários")
        logger.info(f"🔍 [LOGIN] Emails disponíveis: {list(users.keys())}")
        
        # Verificar se usuário existe e senha está correta
        if email in users:
            logger.info(f"✅ [LOGIN] Usuário encontrado: {email}")
            stored_hash = users[email]['password']
            input_hash = hash_password(password)
            
            logger.info(f"🔍 [LOGIN] Verificando senha...")
            
            if stored_hash == input_hash:
                logger.info(f"✅ [LOGIN] Senha correta, configurando sessão...")
                
                # Login bem-sucedido - limpar e configurar sessão
                session.clear()
                session['user_email'] = email
                session['user_name'] = users[email]['name']
                session['user_id'] = users[email]['user_id']
                session.permanent = True
                
                logger.info(f"✅ [LOGIN] Sessão configurada com sucesso")
                
                return jsonify({
                    'success': True,
                    'message': 'Login realizado com sucesso!',
                    'user': {
                        'email': email,
                        'name': users[email]['name']
                    }
                }), 200
            else:
                logger.error(f"❌ [LOGIN] Senha incorreta para {email}")
        else:
            logger.error(f"❌ [LOGIN] Usuário não encontrado: {email}")
        
        # Login falhou
        logger.error(f"❌ [LOGIN] Login falhou - retornando erro 401")
        return jsonify({
            'success': False,
            'message': 'Email ou senha incorretos'
        }), 401
        
    except Exception as e:
        logger.error(f"💥 [LOGIN] Erro interno: {str(e)}")
        import traceback
        logger.error(f"💥 [LOGIN] Traceback: {traceback.format_exc()}")
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
    print(f"🔍 [AUTH STATUS DEBUG] Verificando status de autenticação")
    print(f"🔍 [AUTH STATUS DEBUG] Session keys: {list(session.keys())}")
    print(f"🔍 [AUTH STATUS DEBUG] user_email in session: {'user_email' in session}")
    
    if 'user_email' in session:
        user_email = session['user_email']
        user_name = session.get('user_name', 'Usuário')
        print(f"✅ [AUTH STATUS DEBUG] Usuário autenticado: {user_email}")
        
        return jsonify({
            'authenticated': True,
            'user': {
                'email': user_email,
                'name': user_name
            }
        })
    else:
        print(f"❌ [AUTH STATUS DEBUG] Usuário não autenticado")
        return jsonify({'authenticated': False})

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

@auth_bp.route('/api/test', methods=['GET'])
def api_test():
    """Rota de teste para verificar se a API está funcionando"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🧪 [TEST] Rota de teste acessada")
    
    users = load_users()
    return jsonify({
        'status': 'API funcionando',
        'users_count': len(users),
        'users_emails': list(users.keys()),
        'timestamp': datetime.now().isoformat()
    })