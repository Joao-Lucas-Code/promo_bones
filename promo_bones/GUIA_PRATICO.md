# 🚀 GUIA PRÁTICO — Testar o Promo Bonés do Zero

## Etapa 1: Criar o Bot no Telegram (2 minutos)

### Passo 1.1 — Abra o BotFather
- No Telegram, procure por **@BotFather** ou acesse: https://t.me/BotFather
- Clique em "Iniciar" ou envie `/start`

### Passo 1.2 — Crie o bot
Envie esses comandos em sequência no chat do BotFather:

```
/newbot
```

Ele vai perguntar o **nome** do bot (o que aparece pros usuários):
```
Promo Bonés
```

Depois o **username** (deve terminar em `bot`, único no mundo):
```
promo_bones_bot
```

### Passo 1.3 — Copie o TOKEN
O BotFather vai responder algo assim:

```
Done! Congratulations on your new bot.
You will find it at t.me/promo_bones_bot
Use this token to access the HTTP API:

123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

**Copie esse token inteiro** (a parte depois de "Use this token..."). 
Guarde ele num bloco de notas, você vai usar já já.

---

## Etapa 2: Configurar o Promo Bonés

### Passo 2.1 — Abra o arquivo de configuração
Vá na pasta do projeto e abra o arquivo:

```
C:\Users\João Lucas\Projetos\promo_bones\promo_bones\config.py
```

### Passo 2.2 — Cole o token
Ache essa linha:
```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
```

Mude para:
```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789")
```

(Substitua pelo SEU token real!)

Salve o arquivo.

---

## Etapa 3: Iniciar o Painel

### Passo 3.1 — Abra o terminal
Aperte `Win + R`, digite `cmd` e aperte Enter.

### Passo 3.2 — Vá até a pasta do projeto
```cmd
cd "C:\Users\João Lucas\Projetos\promo_bones\promo_bones"
```

### Passo 3.3 — Rode o servidor
```cmd
python main.py
```

Se aparecer isso, deu certo:
```
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**NÃO FECHE ESSA JANELA!** Deixe o terminal aberto.

### Passo 3.4 — Abra o painel no navegador
Abra o Chrome e digite:
```
http://localhost:8000
```

Você vai ver o Dashboard do Promo Bonés.

---

## Etapa 4: Rodar o Scraper (buscar os bonés)

### Método 1 — Pelo Dashboard
1. No painel (http://localhost:8000), clique no botão **"Rodar Scraper"**
2. Aguarde 10-30 segundos
3. Recarregue a página (F5)
4. Vá na aba **Produtos** — os bonés devem aparecer lá

### Método 2 — Por site específico
1. Vá em **Sites** no menu lateral
2. Clique em **"Scrap"** no site que você quer (ex: The Dust Company)
3. Aguarde e recarregue

---

## Etapa 5: Cadastrar um Cupom

1. Vá em **Cupons** no menu
2. No formulário da esquerda, preencha:
   - **Código**: `MIMODODIA`
   - **Descrição**: `10% OFF em todo site`
   - **Loja**: escolha a loja correspondente
   - **Valor**: `10`
   - **Tipo**: `%`
3. Clique em **"Adicionar Cupom"**

---

## Etapa 6: Gerar e Enviar sua primeira mensagem

1. Vá em **Mensagens**
2. Em "Gerar Nova Mensagem", selecione:
   - **Produto**: escolha um boné da lista
   - **Cupom**: escolha o cupom que cadastrou (ou deixe sem)
3. Clique em **"Gerar Mensagem"**
4. Na lista de mensagens criadas, clique no ícone de **olho** (Preview)
5. Se estiver bom, clique no ícone de **avião** (Enviar)

A mensagem vai pro Telegram! 🎉

---

## Etapa 7: Criar o Grupo no Telegram (opcional, mas recomendado)

Se você quer enviar pro seu grupo de promoções:

### Passo 7.1 — Crie o grupo
- No Telegram, clique no lápis → "Novo Grupo"
- Nomeie (ex: "Promoções Bonés Aba Nenê")
- Adicione o bot `@promo_bones_bot` como membro
- Dê permissão de admin pro bot

### Passo 7.2 — Descobrir o ID do grupo
No navegador, acesse:
```
https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
```

Substitua `<SEU_TOKEN>` pelo seu token real.

Procure por algo assim na resposta:
```json
"chat":{"id":-1001234567890,"title":"Promoções Bonés Aba Nenê"}
```

O número `-1001234567890` é o ID do grupo.

### Passo 7.3 — Configurar no painel
Abra `config.py` e ache:
```python
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "")
```

Mude para:
```python
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "-1001234567890")
```

Salve, pare o servidor (`Ctrl + C` no terminal), rode de novo (`python main.py`).

Agora quando você clicar em "Enviar", a mensagem vai direto pro grupo!

---

## 📋 Checklist rápido

- [ ] Criei o bot no @BotFather
- [ ] Copiei o token
- [ ] Colei o token no `config.py`
- [ ] Rodei `python main.py`
- [ ] Abri http://localhost:8000 no navegador
- [ ] Cliquei em "Rodar Scraper"
- [ ] Vi produtos na aba Produtos
- [ ] Cadastrei um cupom
- [ ] Gerei uma mensagem
- [ ] Mandei pro Telegram!

---

## ❓ Problemas comuns

**"Porta 8000 já em uso"**
```cmd
# Pare tudo e tente de novo
taskkill /F /IM python.exe
python main.py
```

**"Bot não configurado" no Dashboard**
- Verifique se o token está correto no `config.py`
- Reinicie o servidor

**Scraper não encontra produtos**
- Os sites podem ter mudado o layout (isso é normal, precisa ajustar o scraper)
- Tente rodar o scraper do Mercado Livre primeiro (é o mais estável)

**Mensagem não chega no Telegram**
- Verifique se o bot está no grupo (se estiver usando grupo)
- Verifique se o bot tem permissão de enviar mensagens

---

**Boa sorte! 🧢🔥**
