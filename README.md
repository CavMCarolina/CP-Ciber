# CP2 - DevSecOps: Testes de Segurança Automatizados

**FIAP - Engenharia de Software | Cibersegurança - DevSecOps**

---

## Estrutura do Projeto

```
cp2-devsecops/
├── app.py                          # Aplicação web Flask (com vulnerabilidades propositais)
├── requirements.txt                # Dependências Python
├── .github/
│   └── workflows/
│       └── zap-scan.yml            # Pipeline GitHub Actions com OWASP ZAP
├── .zap/
│   └── rules.tsv                   # Regras de severidade do ZAP
└── README.md
```

---

## Entregáveis do CP2

### ✅ Requisito 1 — Configurar OWASP ZAP CLI no GitHub Actions

O arquivo `.github/workflows/zap-scan.yml` configura o workflow completo:

- Usa a **action oficial** `zaproxy/action-baseline@v0.12.0`
- Inicia a aplicação Flask localmente na porta `8080`
- Executa o scan na URL `http://localhost:8080`
- Gera relatório em formato **HTML** (`report_html.html`)

**Como funciona o scan:**

```
Push/PR → GitHub Actions → Inicia app Flask → ZAP escaneia → Gera relatório
```

---

### ✅ Requisito 2 — Pipeline falha em vulnerabilidades Altas/Críticas

O step **"Verificar severidade das vulnerabilidades"** analisa o relatório HTML gerado pelo ZAP e:

- Conta ocorrências de `High` e `Critical` no relatório
- **Se encontrar qualquer Critical → exit 1 (pipeline falha)**
- **Se encontrar mais de 2 High → exit 1 (pipeline falha)**
- Exibe mensagem clara: `❌ PIPELINE BLOQUEADO!`

O arquivo `.zap/rules.tsv` também configura regras por ID de alerta:

- `SQL Injection` → **FAIL**
- `XSS Refletido` → **FAIL**
- Headers de segurança ausentes → **WARN** (avisa, não bloqueia)

---

### ✅ Requisito 3 — Análise do relatório

Após executar o pipeline, acesse a aba **"Actions"** do GitHub:

1. Clique no workflow executado
2. Baixe o artefato `zap-security-report-N`
3. Abra o `report_html.html` no navegador

**O que analisar no relatório:**

| Campo                  | Onde encontrar                                 |
| ---------------------- | ---------------------------------------------- |
| Total de alertas       | Seção "Summary" do relatório                   |
| Alertas por severidade | Tabela com High / Medium / Low / Informational |
| Tipos mais comuns      | Lista de alertas com descrição e URL afetada   |

**Vulnerabilidades esperadas na aplicação:**

| Tipo                            | Severidade | Causa                                     |
| ------------------------------- | ---------- | ----------------------------------------- |
| SQL Injection                   | 🔴 High    | Query concatenada sem prepared statement  |
| XSS Refletido                   | 🔴 High    | Exibição de input sem sanitização         |
| CSRF Token ausente              | 🟡 Medium  | Formulários sem proteção CSRF             |
| X-Frame-Options ausente         | 🟡 Medium  | Header não configurado                    |
| Content-Security-Policy ausente | 🟡 Medium  | Header não configurado                    |
| Informações sensíveis expostas  | 🟡 Medium  | Rota `/debug` expõe variáveis de ambiente |
| Cookie sem HttpOnly             | 🟠 Low     | Flags de segurança ausentes               |

---

### ✅ Requisito 4 — Vulnerabilidade Proposital

A aplicação `app.py` contém **4 vulnerabilidades intencionais** para validar o ZAP:

#### 🔴 SQL Injection (linha ~80)

```python
# VULNERABILIDADE: Query concatenada — sem prepared statement
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
DB.execute(query)

# Ataque: username = ' OR '1'='1' --
# Resultado: acesso sem senha
```

#### 🔴 XSS Refletido (linha ~88)

```python
# VULNERABILIDADE: Exibe input do usuário com |safe (sem escape)
return render_template_string(LOGIN_PAGE, error=username)
# No template: {{ error|safe }}
```

#### 🟡 CSRF Token Ausente

```html
<!-- Formulários sem token CSRF -->
<form action="/login" method="POST">
  <!-- Sem: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"> -->
</form>
```

#### 🟡 Endpoint Sensível Exposto

```python
@app.route('/debug')
def debug():
    return {"env": dict(os.environ), ...}  # Expõe variáveis de ambiente!
```

**Como verificar que o ZAP detectou:**

- No relatório HTML, procure por "SQL Injection" e "Cross Site Scripting"
- Eles devem aparecer com severidade **High**
- O pipeline deve ter **falhado** ao detectá-los

---

### ✅ Requisito 5 — Relatório como Artefato do GitHub Actions

O step final do workflow salva automaticamente:

```yaml
- name: Salvar relatório ZAP como artefato
  uses: actions/upload-artifact@v4
  if: always() # Salva mesmo se o pipeline falhar!
  with:
    name: zap-security-report-${{ github.run_number }}
    path: |
      report_html.html
      report_json.json
    retention-days: 30
```

**Como acessar:**

1. GitHub → Repositório → aba **Actions**
2. Clique no workflow
3. Role até **"Artifacts"**
4. Baixe `zap-security-report-N`

---

## Como Configurar no Seu Repositório

### Passo 1 — Copiar os arquivos

```bash
# Clone seu repositório
git clone https://github.com/CavMCarolina/CP-Ciber.git
cd CP-Ciber

# Copie os arquivos deste projeto para o seu repositório
cp app.py requirements.txt .
mkdir -p .github/workflows .zap
cp .github/workflows/zap-scan.yml .github/workflows/
cp .zap/rules.tsv .zap/
```

### Passo 2 — Commit e Push

```bash
git add .
git commit -m "CP2: Adiciona OWASP ZAP ao pipeline de segurança"
git push origin main
```

### Passo 3 — Acompanhar o pipeline

1. Acesse **github.com/CavMCarolina/CP-Ciber**
2. Clique na aba **"Actions"**
3. Veja o workflow **"Security Scan - OWASP ZAP"** executando
4. Após finalizar, acesse os **"Artifacts"** para baixar o relatório

---

## Referências

- [OWASP ZAP](https://www.zaproxy.org/)
- [zaproxy/action-baseline](https://github.com/zaproxy/action-baseline)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow)
