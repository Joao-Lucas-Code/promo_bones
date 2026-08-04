# 🧢 Promo Bonés - Painel Admin

Sistema completo para gerenciamento de grupo de promoções de bonés aba nenê no Telegram.

## 📁 Estrutura do Projeto

```
promo_bones/
├── main.py                 # Flask app + rotas
├── config.py               # Configurações (lê do .env)
├── database.py             # SQLite + SQLAlchemy models
├── scraper.py              # Web scrapers (Dust, Midas, Soleil, ML)
├── message_generator.py    # Gerador de mensagens para Telegram
├── telegram_bot.py         # Integração Telegram Bot API
├── requirements.txt        # Dependências Python
├── .env.example            # Exemplo de variáveis de ambiente
├── GUIA_BOT_TELEGRAM.md    # Como criar o bot no Telegram
├── static/
│   └── style.css
└── templates/              # Templates HTML do painel
    ├── base.html
    ├── dashboard.html
    ├── sites.html
    ├── products.html
    ├── coupons.html
    └── messages.html
```

## 🚀 Como rodar

### 1. Requisitos
- Python 3.10 ou superior (recomendado: 3.11 ou 3.12)
- pip

### 2. Crie e ative um ambiente virtual (recomendado)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_GROUP_ID=id_do_grupo_ou_canal
ML_AFFILIATE_TAG=sua_tag_ml
AMAZON_AFFILIATE_TAG=sua_tag_amazon
```

> Para criar o bot e descobrir o `TELEGRAM_GROUP_ID`, siga o [GUIA_BOT_TELEGRAM.md](GUIA_BOT_TELEGRAM.md).

### 5. Inicie o servidor
Na raiz do projeto, execute:
```bash
python run.py
```

O painel estará disponível em: **http://localhost:5000**

## 🌐 Deploy no Render

Este projeto pode ser deployado no [Render](https://render.com) usando o `render.yaml` da raiz do repositório.

1. Suba o código no GitHub.
2. No Render, crie um novo **Blueprint** e conecte o repositório.
3. Configure as variáveis de ambiente no dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_GROUP_ID`
   - `ML_AFFILIATE_TAG` (opcional)
   - `AMAZON_AFFILIATE_TAG` (opcional)
4. Faça o deploy.

> No plano gratuito, o banco SQLite é reiniciado quando o serviço "dorme". Use PostgreSQL se precisar de persistência garantida.

## 🟢 Keep Alive

O repositório inclui um workflow do GitHub Actions (`.github/workflows/keep-alive.yml`) que pinga o endpoint `/api/health` a cada 15 minutos para manter o serviço do Render acordado.

Configure o secret `RENDER_URL` nas configurações do GitHub com a URL do seu serviço (ex: `https://promo-bones.onrender.com`).

## 🖥️ Funcionalidades do Painel

| Página | O que faz |
|--------|-----------|
| **Dashboard** | Visão geral: estatísticas, melhores ofertas, logs do scraper, status do bot |
| **Sites** | Ativar/desativar lojas monitoradas, rodar scraper individual |
| **Produtos** | Lista todos os bonés encontrados com filtros por loja/desconto |
| **Cupons** | Cadastrar cupons de desconto (com % ou valor fixo) |
| **Mensagens** | Gerar mensagens no formato dos grupos de promoção e enviar para o Telegram |

## 🔧 Como usar o Scraper

### Manual (pelo painel)
1. Acesse o Dashboard
2. Clique em **"Rodar Scraper"**
3. Aguarde a execução
4. Os produtos aparecerão na aba "Produtos"

### Por site específico
1. Vá em **Sites**
2. Clique em **"Scrap"** no site desejado

### Automático (agendado)
O projeto já inclui a dependência `APScheduler`. Para ativar, adicione em `main.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_all_scrapers, 'interval', minutes=SCRAPER_INTERVAL_MINUTES)
scheduler.start()
```

## 💬 Como enviar mensagens para o Telegram

1. **Execute o scraper** para popular o banco de dados
2. Vá em **Mensagens**
3. Selecione um **produto** e um **cupom** (opcional)
4. Clique em **"Gerar Mensagem"**
5. Clique em **Preview** para ver como vai ficar
6. Clique em **Enviar** para postar no grupo!

O formato da mensagem segue o padrão dos grupos de promoção:
- Headline chamativa
- Nome do produto
- Preço original riscado
- Preço atual
- Cupom (se houver)
- Link de compra

## 🛒 Sites monitorados

| Loja | URL |
|------|-----|
| The Dust Company | https://www.thedustcompany.com.br/categoria/bones/ |
| Midas Touch | https://midastouch.com.br/bones/ |
| Soleil Passionnés | https://soleilpassionnes.com |
| Mercado Livre | Busca por "boné aba curva" |

## ⚙️ Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram | (vazio) |
| `TELEGRAM_GROUP_ID` | ID do grupo/canal | (vazio) |
| `ML_AFFILIATE_TAG` | Tag de afiliado ML | (vazio) |
| `AMAZON_AFFILIATE_TAG` | Tag de afiliado Amazon | (vazio) |
| `SCRAPER_INTERVAL` | Intervalo do scraper (min) | 60 |

## 🛡️ Segurança

- **NUNCA** commit o arquivo `.env` com credenciais reais.
- Troque a `secret_key` do Flask em produção (`main.py`, variável `app.secret_key`).
- O arquivo `.gitignore` já ignora `.env`, `venv/`, `*.db` e `__pycache__/`.

---

**Criado para o projeto Promo Bonés**
