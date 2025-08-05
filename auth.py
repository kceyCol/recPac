from flask import Blueprint, request, jsonify, session
import hashlib
import sqlite3
import os
from datetime import datetime
from functools import wraps
import logging

auth_bp = Blueprint('auth', __name__)
USERS_DB = 'users.db'

# Configurar logging
logger = logging.getLogger(__name__)

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    
    # Criar tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            user_id TEXT NOT NULL
        )
    ''')
    
    # Verificar se há usuários, se não, criar os de teste
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        logger.info("🔧 [DB] Criando usuários de teste automaticamente...")
        test_users = [
            ('alekcey@me.com', 'alekcey colione', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '2025-07-23T16:02:10.773243', '4cdfe8a1'),
            ('admin@test.com', 'Administrador', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '2025-07-31T17:25:55.209682', 'admin123'),
            ('user@test.com', 'Usuário Teste', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', '2025-07-31T17:25:55.209682', 'user123'),
            ('test@test.com', 'Usuário Teste', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '2025-07-31T17:25:55.209682', 'b642b421')
        ]
        
        cursor.executemany('''
            INSERT INTO users (email, name, password, created_at, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', test_users)
        
        logger.info("✅ [DB] 4 usuários de teste criados automaticamente!")
    
    conn.commit()
    conn.close()

def load_users():
    """Carrega usuários do banco SQLite"""
    try:
        init_database()  # Garante que o DB existe
        
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT email, name, password, created_at, user_id FROM users')
        rows = cursor.fetchall()
        
        users = {}
        for row in rows:
            email, name, password, created_at, user_id = row
            users[email] = {
                'name': name,
                'password': password,
                'created_at': created_at,
                'user_id': user_id
            }
        
        conn.close()
        logger.info(f"🔍 [DB] Carregados {len(users)} usuários do banco")
        return users
    except Exception as e:
        logger.error(f"❌ [DB] Erro ao carregar usuários: {str(e)}")
        return {}

def save_users(users):
    """Salva usuários no banco SQLite"""
    try:
        init_database()
        
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        
        # Limpar tabela e inserir novos dados
        cursor.execute('DELETE FROM users')
        
        for email, data in users.items():
            cursor.execute('''
                INSERT INTO users (email, name, password, created_at, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, data['name'], data['password'], data['created_at'], data['user_id']))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ [DB] Salvos {len(users)} usuários no banco")
    except Exception as e:
        logger.error(f"❌ [DB] Erro ao salvar usuários: {str(e)}")

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


@auth_bp.route('/fix-users', methods=['GET'])
def fix_users():
    """Rota para corrigir problema de usuários em produção"""
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔧 [FIX] Iniciando correção de usuários")
        
        # Verificar diretório atual
        current_dir = os.getcwd()
        logger.info(f"🔧 [FIX] Diretório atual: {current_dir}")
        
        # Listar arquivos no diretório
        files = os.listdir('.')
        logger.info(f"🔧 [FIX] Arquivos no diretório: {files}")
        
        # Verificar se users.json existe
        users_exists = os.path.exists(USERS_FILE)
        logger.info(f"🔧 [FIX] {USERS_FILE} existe: {users_exists}")
        
        if users_exists:
            # Ler conteúdo do arquivo
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"🔧 [FIX] Conteúdo do arquivo: {content[:200]}...")
        
        # Criar usuários forçadamente
        users_data = {
            'alekcey@me.com': {
                'name': 'alekcey colione',
                'password': '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
                'created_at': '2025-07-23T16:02:10.773243',
                'user_id': '4cdfe8a1'
            },
            'admin@test.com': {
                'name': 'Administrador',
                'password': '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
                'created_at': '2025-07-31T17:25:55.209682',
                'user_id': 'admin123'
            },
            'user@test.com': {
                'name': 'Usuário Teste',
                'password': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
                'created_at': '2025-07-31T17:25:55.209682',
                'user_id': 'user123'
            },
            'test@test.com': {
                'name': 'Usuário Teste',
                'password': '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
                'user_id': 'b642b421'
            }
        }
        
        # Salvar usuários
        logger.info(f"🔧 [FIX] Salvando {len(users_data)} usuários...")
        save_users(users_data)
        
        # Verificar se foi salvo
        users_check = load_users()
        logger.info(f"🔧 [FIX] Verificação: {len(users_check)} usuários carregados")
        
        return f'''
        <html>
        <body>
        <h1>✅ Usuários Corrigidos!</h1>
        <p><strong>Diretório:</strong> {current_dir}</p>
        <p><strong>Arquivo existe:</strong> {users_exists}</p>
        <p><strong>Usuários criados:</strong> {len(users_check)}</p>
        <p><strong>Emails disponíveis:</strong> {list(users_check.keys())}</p>
        
        <h2>🔑 Credenciais para Login:</h2>
        <ul>
            <li><strong>alekcey@me.com</strong> / <strong>hello</strong></li>
            <li><strong>admin@test.com</strong> / <strong>hello</strong></li>
            <li><strong>user@test.com</strong> / <strong>password</strong></li>
            <li><strong>test@test.com</strong> / <strong>hello</strong></li>
        </ul>
        
        <p><a href="/">← Voltar para o Login</a></p>
        </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"💥 [FIX] Erro: {str(e)}")
        import traceback
        logger.error(f"💥 [FIX] Traceback: {traceback.format_exc()}")
        return f'''
        <html>
        <body>
        <h1>❌ Erro na Correção</h1>
        <p><strong>Erro:</strong> {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        ''', 500