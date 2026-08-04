# 🧢 Promo Bonés

Sistema de painel administrativo para gerenciamento de promoções de bonés aba nenê e envio automático para grupos/canais do Telegram.

## 📁 Estrutura do Repositório

```
promo_bones/
├── README.md                 # Este arquivo
├── requirements.txt          # Dependências Python
├── .gitignore               # Arquivos ignorados pelo Git
├── bones.md                 # Links das lojas monitoradas (notas)
└── promo_bones/             # Código-fonte do projeto
    ├── main.py              # Flask app + rotas
    ├── config.py            # Configurações (lê do .env)
    ├── database.py          # SQLite + SQLAlchemy models
    ├── scraper.py           # Web scrapers
    ├── message_generator.py # Gerador de mensagens para Telegram
    ├── telegram_bot.py      # Integração Telegram Bot API
    ├── README.md            # Documentação detalhada
    ├── .env.example         # Exemplo de variáveis de ambiente
    ├── GUIA_BOT_TELEGRAM.md # Como criar o bot no Telegram
    ├── static/              # Assets CSS
    └── templates/           # Templates HTML do painel
```

## 🚀 Começando

Veja a documentação completa em [`promo_bones/README.md`](promo_bones/README.md).

Resumo rápido:

```bash
# 1. Crie o ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env
cp promo_bones/.env.example promo_bones/.env
# Edite promo_bones/.env com seu token do Telegram

# 4. Rode o servidor
cd promo_bones
python main.py
```

Acesse o painel em **http://localhost:5000**.

## 🌐 Deploy no Render

O projeto já está configurado para deploy no [Render](https://render.com) usando o arquivo [`render.yaml`](render.yaml).

### Passo a passo

1. Faça commit e push deste repositório no GitHub.
2. Acesse [dashboard.render.com](https://dashboard.render.com) e clique em **New +** → **Blueprint**.
3. Conecte seu repositório `promo_bones`.
4. O Render vai ler o `render.yaml` e criar o Web Service automaticamente.
5. No dashboard do serviço, vá em **Environment** e configure:
   - `TELEGRAM_BOT_TOKEN` — token do @BotFather
   - `TELEGRAM_GROUP_ID` — ID do grupo/canal do Telegram
   - `ML_AFFILIATE_TAG` — (opcional) tag de afiliado do Mercado Livre
   - `AMAZON_AFFILIATE_TAG` — (opcional) tag de afiliado da Amazon
6. Clique em **Deploy**.

Após o deploy, acesse a URL gerada pelo Render. O banco SQLite será criado automaticamente no primeiro acesso.

> ⚠️ **Atenção:** no plano gratuito do Render, o banco SQLite é reiniciado quando o serviço "dorme" ou há novo deploy. Para dados importantes, considere migrar para PostgreSQL.

## ⚙️ Tecnologias

- Python 3.10+
- Flask
- SQLAlchemy + SQLite
- BeautifulSoup4 + Requests
- Telegram Bot API

## 🛡️ Segurança

- Nunca commite o arquivo `.env` com credenciais reais.
- O `.gitignore` já ignora ambientes virtuais, banco de dados local e cache Python.
- Em produção, troque a `secret_key` do Flask.

---

Projeto Promo Bonés
