from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# ============================================================
# VULNERABILIDADE PROPOSITAL #1: Banco de dados em memória
# sem prepared statements (SQL Injection)
# ============================================================
def init_db():
    conn = sqlite3.connect(':memory:')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'admin123')")
    conn.execute("INSERT INTO users VALUES (2, 'joao', 'senha456')")
    conn.commit()
    return conn

DB = init_db()

# ============================================================
# Template HTML com vulnerabilidades propositais:
# - Sem Content-Security-Policy
# - Sem X-Frame-Options
# - Sem X-Content-Type-Options
# - Formulário sem CSRF token
# - Campo sem sanitização (XSS)
# ============================================================
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ClickSeguro - Login</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }}
        input {{ width: 100%%; padding: 10px; margin: 8px 0; box-sizing: border-box; }}
        button {{ width: 100%%; padding: 12px; background: #007bff; color: white; border: none; cursor: pointer; }}
        .error {{ color: red; }}
        .info {{ color: gray; font-size: 12px; }}
    </style>
</head>
<body>
    <h2>ClickSeguro - Acesso ao Sistema</h2>
    <form action="/login" method="POST">
        <!-- VULNERABILIDADE: Sem CSRF Token -->
        <label>Usuário:</label>
        <!-- VULNERABILIDADE: Sem atributo autocomplete="off" -->
        <input type="text" name="username" placeholder="Digite seu usuário">
        <label>Senha:</label>
        <input type="password" name="password" placeholder="Digite sua senha">
        <button type="submit">Entrar</button>
    </form>
    {% if error %}
    <!-- VULNERABILIDADE: XSS - Exibe input do usuário sem sanitização -->
    <p class="error">Usuário não encontrado: {{ error|safe }}</p>
    {% endif %}
    <p class="info">Dica: tente admin / admin123</p>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ClickSeguro - Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .card {{ border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Bem-vindo, {{ username }}!</h1>
    <p>Plataforma de Agendamento de Serviços Residenciais</p>
    <div class="card">
        <h3>Agendar Serviço</h3>
        <form action="/agendar" method="POST">
            <!-- VULNERABILIDADE: Sem CSRF Token -->
            <input type="text" name="servico" placeholder="Tipo de serviço">
            <input type="text" name="endereco" placeholder="Endereço">
            <!-- VULNERABILIDADE: Campo de comentário sem limite de tamanho -->
            <textarea name="obs" placeholder="Observações (sem limite de caracteres)"></textarea>
            <button type="submit">Agendar</button>
        </form>
    </div>
    <div class="card">
        <h3>Buscar Agendamentos</h3>
        <form action="/buscar" method="GET">
            <!-- VULNERABILIDADE: Parâmetro de busca sem sanitização -->
            <input type="text" name="q" placeholder="Buscar por nome">
            <button type="submit">Buscar</button>
        </form>
    </div>
    <a href="/logout">Sair</a>
</body>
</html>
"""

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # ============================================================
        # VULNERABILIDADE PROPOSITAL #2: SQL Injection
        # Query concatenada diretamente sem prepared statement
        # Exemplo de ataque: username = ' OR '1'='1
        # ============================================================
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        try:
            cursor = DB.execute(query)
            user = cursor.fetchone()
            if user:
                return render_template_string(DASHBOARD_PAGE, username=username)
            else:
                # VULNERABILIDADE #3: Reflete input do usuário sem escape (XSS)
                return render_template_string(LOGIN_PAGE, error=username)
        except Exception as e:
            return render_template_string(LOGIN_PAGE, error=str(e))
    
    return render_template_string(LOGIN_PAGE, error=None)

@app.route('/agendar', methods=['POST'])
def agendar():
    servico = request.form.get('servico', '')
    endereco = request.form.get('endereco', '')
    # VULNERABILIDADE: sem validação, sem autenticação no endpoint
    return f"<h2>Agendado!</h2><p>Serviço: {servico}</p><p>Endereço: {endereco}</p><a href='/login'>Voltar</a>"

@app.route('/buscar', methods=['GET'])
def buscar():
    q = request.args.get('q', '')
    # VULNERABILIDADE: SQL Injection no parâmetro de busca
    query = f"SELECT * FROM users WHERE username LIKE '%{q}%'"
    try:
        cursor = DB.execute(query)
        results = cursor.fetchall()
        result_html = ''.join([f'<p>{r}</p>' for r in results])
        # VULNERABILIDADE: XSS refletido
        return f"<h2>Resultados para: {q}</h2>{result_html}<a href='/login'>Voltar</a>"
    except Exception as e:
        return f"<p>Erro: {e}</p>"

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# ============================================================
# VULNERABILIDADE #4: Informações sensíveis expostas
# ============================================================
@app.route('/debug')
def debug():
    return {
        "env": dict(os.environ),
        "db_path": ":memory:",
        "version": "ClickSeguro v1.0.0-beta",
        "secret_key": app.secret_key or "nenhuma"
    }

if __name__ == '__main__':
    # VULNERABILIDADE: debug=True em produção
    app.run(host='0.0.0.0', port=8080, debug=True)
