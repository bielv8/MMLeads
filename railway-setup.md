# Como Fazer Deploy no Railway

## Erro que você estava enfrentando
O erro acontece porque o Railway precisa de um banco PostgreSQL configurado.

## Passos para Deploy no Railway:

### 1. **Conecte seu Repositório**
- Acesse [railway.app](https://railway.app)
- Clique em "Start a New Project"
- Conecte seu repositório GitHub

### 2. **Adicione um Banco PostgreSQL**
- No painel do Railway, clique em "Add Service"
- Selecione "PostgreSQL"
- O Railway irá criar automaticamente a variável `DATABASE_URL`

### 3. **Configure as Variáveis de Ambiente**
No painel do Railway, adicione estas variáveis:
- `SESSION_SECRET` = `sua_chave_secreta_aqui` (qualquer string aleatória longa)

### 4. **Deploy Automático**
O Railway irá automaticamente:
- Detectar que é um projeto Python
- Instalar dependências do `pyproject.toml`
- Executar: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1`

### 5. **Verificar o Deploy**
- O Railway mostrará a URL do seu app
- Acesse a URL para ver sua aplicação funcionando

## Estrutura Criada para Railway:
- ✅ `wsgi.py` - Ponto de entrada WSGI
- ✅ `Procfile` - Comando de start
- ✅ `railway.toml` - Configurações do Railway
- ✅ Fallback SQLite para desenvolvimento local

## Credenciais Padrão:
- **Usuário**: admin
- **Senha**: admin123