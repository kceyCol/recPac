# AudioToText - Pré Lançamento

Este é um aplicativo web para transcrever áudio para texto, utilizando a API Gemini para processamento de linguagem natural.

## Configuração do Ambiente

Para configurar o ambiente de desenvolvimento, siga os passos abaixo:

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd "AudioToText - pré lancamento"
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**

    Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

    ```ini
    # Configurações da API Gemini
    GEMINI_API_KEY=SUA_CHAVE_API_GEMINI
    ```

    Substitua `SUA_CHAVE_API_GEMINI` pela sua chave de API do Google Gemini.

## Executando o Aplicativo

Para iniciar o aplicativo, execute o seguinte comando:

```bash
python app.py
```

O aplicativo estará disponível em `http://127.0.0.1:5000` (ou a porta configurada).

## Estrutura do Projeto

-   `app.py`: O arquivo principal da aplicação Flask.
-   `requirements.txt`: Lista de dependências do Python.
-   `.env`: Variáveis de ambiente (ex: chaves de API).
-   `templates/`: Contém os arquivos HTML (páginas web).
    -   `index.html`: Página inicial.
    -   `login.html`: Página de login.
    -   `register.html`: Página de registro.
    -   `transcriptions.html`: Página para exibir transcrições.
-   `static/`: Contém arquivos estáticos como CSS e JavaScript.
    -   `css/`: Arquivos CSS para estilização.
    -   `js/`: Arquivos JavaScript para funcionalidades do lado do cliente.
-   `recordings/`: Diretório para armazenar gravações de áudio.
-   `transcriptions/`: Diretório para armazenar arquivos de texto transcritos.
-   `render.yaml`: Configuração para deploy no Render (se aplicável).
-   `run.bat`: Script para iniciar o aplicativo no Windows.

## Funcionalidades

-   Gravação de áudio.
-   Transcrições de áudio para texto usando a API Gemini.
-   Gerenciamento de usuários (registro e login).
-   Visualização de transcrições.

## Próximos Passos

-   Implementar a funcionalidade de gravação de áudio no frontend.
-   Integrar a chamada da API Gemini para processamento de áudio.
-   Melhorar a interface do usuário.
-   Adicionar tratamento de erros e validações.


# 📱 AudioToText - Documentação Completa
## 🎯 Sobre o Projeto
O AudioToText é uma aplicação web para gravação, transcrição e gerenciamento de conversas de áudio. Permite gravar conversas, transcrevê-las automaticamente usando IA e gerar resumos inteligentes.

## 🛠️ Pré-requisitos
### Software Necessário:
- Python 3.8+ (recomendado 3.9 ou superior)
- Node.js 16+ (para o frontend React)
- Git (para clonar o repositório)
### Contas/APIs Necessárias:
- Google Gemini API Key (para melhorar transcrições)
## 📦 Instalação do Zero
### 1. Preparar o Ambiente
```
# Criar diretório do projeto
mkdir AudioToText
cd AudioToText

# Clonar ou baixar os arquivos do projeto
# (assumindo que você já tem os arquivos)
```
### 2. Configurar Backend (Python/Flask)
```
# Instalar dependências Python
pip install -r requirements.txt
```
Conteúdo do requirements.txt:

```
Flask==2.3.3
flask-cors==4.0.0
SpeechRecognition==3.10.0
pydub==0.25.1
google-generativeai==0.3.2
reportlab==4.0.4
python-docx==0.8.11
markdown==3.5.1
python-dotenv==1.0.0
```
### 3. Configurar Variáveis de Ambiente
Crie o arquivo .env na raiz do projeto:

```
# Chave secreta do Flask (gere uma aleatória)
FLASK_SECRET_KEY=sua_chave_secreta_muito_segura_aqui_123456789

# API Key do Google Gemini (opcional, mas recomendado)
GEMINI_API_KEY=sua_api_key_do_gemini_aqui

# Configurações de ambiente
FLASK_ENV=development
FLASK_DEBUG=True
```
### 4. Configurar Frontend (React)
```
# Navegar para o diretório frontend
cd frontend

# Instalar dependências
npm install

# Voltar para a raiz
cd ..
```
### 5. Corrigir Problemas Conhecidos Corrigir auth.py (linha 49-50):
```
        if email in users and users[email]['password'] == 
        hash_password(password):
            session['user_id'] = email
            flash('Login realizado com sucesso!', 'success')
            return redirect('/app')
        else:
            flash('Email ou senha incorretos!', 'error')
```
## 🚀 Executando a Aplicação
### Método 1: Usando run.bat (Windows)
```
# Execute o arquivo batch
run.bat
```
### Método 2: Manual
```
# Terminal 1: Backend Flask
python app.py

# Terminal 2: Frontend React (em outro terminal)
cd frontend
npm start
```
### Método 3: Apenas Backend (sem React)
```
python app.py
```
## 🔧 Configuração Inicial
### 1. Criar Usuário de Teste
Acesse: http://localhost:5000/create-test-user

Isso criará:

- Email: test@example.com
- Senha: 123456
### 2. Fazer Login
1. 1.
   Acesse: http://localhost:5000/login
2. 2.
   Use as credenciais criadas
3. 3.
   Será redirecionado para /app
### 3. Testar Funcionalidades
1. 1.
   Gravar áudio - Use o botão de gravação
2. 2.
   Visualizar gravações - Vão aparecer no dashboard
3. 3.
   Transcrever - Clique em "Transcrever" em qualquer gravação
4. 4.
   Gerar resumos - Use a funcionalidade de resumo com IA
## 📁 Estrutura do Projeto
```
AudioToText/
├── app.py                 # Aplicação principal Flask
├── auth.py               # Sistema de autenticação
├── audio_processing.py   # Processamento de áudio
├── utils.py              # Utilitários
├── requirements.txt      # Dependências Python
├── run.bat              # Script de execução
├── .env                 # Variáveis de ambiente
├── users.json           # Banco de dados de usuários
├── recordings/          # Diretório de gravações
├── transcriptions/      # Diretório de transcrições
├── templates/           # Templates HTML
│   ├── index.html
│   ├── login.html
│   └── register.html
├── static/              # Arquivos estáticos
│   ├── css/
│   └── js/
└── frontend/            # Aplicação React (opcional)
    ├── src/
    ├── public/
    └── package.json
```
## 🔑 URLs Importantes
- Login: http://localhost:5000/login
- Aplicação: http://localhost:5000/app
- Criar usuário teste: http://localhost:5000/create-test-user
- Frontend React: http://localhost:3000 (se executando)
## 🐛 Solução de Problemas
### Problema: Login não funciona
Solução: Verifique se corrigiu o auth.py conforme indicado acima

### Problema: Gravações não aparecem
Solução:

1. 1.
   Verifique se está logado
2. 2.
   Verifique se a pasta recordings/ existe
3. 3.
   Verifique se os arquivos têm o formato correto: nome_timestamp_usuario.wav
### Problema: Transcrição não funciona
Solução:

1. 1.
   Instale dependências de áudio: pip install pyaudio
2. 2.
   No Windows, pode precisar instalar: pip install pipwin && pipwin install pyaudio
### Problema: API Gemini não funciona
Solução:

1. 1.
   Obtenha uma API key em: https://makersuite.google.com/app/apikey
2. 2.
   Adicione no arquivo .env
## 📝 Uso Básico
1. 1.
   Fazer Login
2. 2.
   Gravar Áudio - Clique no botão de gravação
3. 3.
   Salvar - Com ou sem nome do paciente
4. 4.
   Transcrever - Clique em "Transcrever" na gravação
5. 5.
   Gerar Resumo - Use a IA para criar resumos
6. 6.
   Exportar - Baixe em PDF ou DOCX
## 🔒 Segurança
- Senhas são hasheadas com SHA-256
- Sessões são seguras com cookies HTTP-only
- Arquivos são isolados por usuário
- Verificação de propriedade em todas as operações
## 🆘 Suporte
Se encontrar problemas:

1. 1.
   Verifique os logs no terminal
2. 2.
   Confirme que todas as dependências estão instaladas
3. 3.
   Verifique se as portas 5000 e 3000 estão livres
4. 4.
   Confirme que o arquivo .env está configurado corretamente