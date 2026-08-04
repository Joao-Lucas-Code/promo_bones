# 🤖 Como Criar seu Bot no Telegram

## Passo a passo (2 minutos)

### 1. Abra o BotFather
- Acesse **https://t.me/BotFather** no Telegram
- Ou pesquise por `@BotFather` no app

### 2. Crie o bot
- Envie o comando: `/newbot`
- Digite um nome para o bot (ex: `Promo Bones`)
- Digite um username único (deve terminar em `bot`, ex: `promo_bones_bot`)

### 3. Copie o TOKEN
- O BotFather vai te enviar uma mensagem assim:

```
Done! Congratulations on your new bot.
You will find it at t.me/promo_bones_bot
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

- **Copie o token** (é a parte depois de "Use this token...")

### 4. Configure no Promo Bones
Crie o arquivo `.env` na pasta `promo_bones/` (copie de `.env.example`):

```bash
cp .env.example .env
```

Edite `.env` e cole o token:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 5. Crie um grupo/canal (opcional)
- Crie um grupo no Telegram
- Adicione o bot ao grupo
- Para descobrir o ID do grupo, acesse:
  ```
  https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
  ```
- Procure por `"chat":{"id":-100...` — esse número é o `TELEGRAM_GROUP_ID`
- Cole o ID no `.env`:
  ```env
  TELEGRAM_GROUP_ID=-1001234567890
  ```

### 6. Teste
- Reinicie o servidor do Promo Bones
- Acesse o painel em http://localhost:5000
- No Dashboard, clique em **"Testar Envio"**
- Você deve receber uma mensagem de teste no grupo!

---

## 🎨 Dica: Personalize o bot

No BotFather, você pode:
- `/setname` — mudar o nome
- `/setdescription` — descrição do bot
- `/setabouttext` — texto "Sobre"
- `/setuserpic` — foto do bot
- `/setcommands` — comandos do bot (ex: `/ofertas`, `/cupons`)

---

## 🛡️ Segurança

**NUNCA** compartilhe seu token publicamente! 
Se vazar, qualquer pessoa pode controlar seu bot.

Se precisar revogar:
- No BotFather, envie `/revoke` e escolha seu bot
- Um novo token será gerado

Lembre-se: o arquivo `.env` não deve ser commitado no repositório.
