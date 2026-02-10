# 🚀 Deploy Gratuito no Render

Guia completo para deploy do Scriptum v2.5 (Backend Flask) no Render gratuitamente.

---

## 📋 Pré-requisitos

1. ✅ Código no GitHub: https://github.com/DrNOFX97/scriptum-v2.5
2. ✅ Conta Render: https://render.com (usar conta pessoal)
3. ✅ API Keys (TMDB, OpenSubtitles, Gemini)

---

## 🎯 Passos para Deploy

### 1. Criar Conta no Render

1. Vai a https://render.com
2. Clica em "Get Started for Free"
3. Conecta com GitHub (conta DrNOFX97)
4. Autoriza acesso ao repo `scriptum-v2.5`

### 2. Deploy do Backend (Flask API)

#### Opção A: Usando render.yaml (Recomendado)

1. No dashboard Render, clica em **"New +"** → **"Blueprint"**
2. Conecta o repositório: `DrNOFX97/scriptum-v2.5`
3. O Render deteta automaticamente o `render.yaml`
4. Confirma as configurações
5. Clica em **"Apply"**

#### Opção B: Manual

1. No dashboard Render, clica em **"New +"** → **"Web Service"**
2. Seleciona o repo: `DrNOFX97/scriptum-v2.5`
3. Configurações:
   - **Name:** `scriptum-api`
   - **Region:** Frankfurt (Europa)
   - **Branch:** `main`
   - **Root Directory:** `subtitle-translator`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`
   - **Plan:** Free

4. Clica em **"Create Web Service"**

### 3. Configurar Variáveis de Ambiente

No dashboard do serviço, vai a **"Environment"** e adiciona:

```bash
# Obrigatórias
TMDB_API_KEY=<tua_key_aqui>
OPENSUBTITLES_API_KEY=<tua_key_aqui>
GEMINI_API_KEY=<tua_key_aqui>

# Opcionais
OPENSUBTITLES_USER_AGENT=Scriptum v2.5
LEGENDASDIVX_USER=<teu_user>
LEGENDASDIVX_PASS=<tua_pass>

# Sistema
DEBUG=False
PYTHON_VERSION=3.11.0
```

Clica em **"Save Changes"** → O deploy reinicia automaticamente

### 4. Verificar Deploy

1. Aguarda o deploy terminar (2-5 minutos)
2. Testa o endpoint: `https://scriptum-api.onrender.com/health`
3. Deverás ver:
```json
{
  "status": "ok",
  "version": "2.5.0",
  "service": "Scriptum API"
}
```

---

## 🌐 Deploy do Frontend (React)

### Opção 1: Netlify (Recomendado para Frontend)

```bash
cd /Users/f.nuno/projetos/scriptum-v2.5

# Login no Netlify
netlify login

# Deploy
netlify deploy --prod

# Quando pedir:
# - Build command: npm run build
# - Publish directory: dist
```

### Opção 2: Render Static Site

1. Dashboard Render → **"New +"** → **"Static Site"**
2. Repo: Criar novo repo para frontend ou usar monorepo
3. Configurações:
   - **Build Command:** `cd scriptum-v2.5 && npm install && npm run build`
   - **Publish Directory:** `scriptum-v2.5/dist`

### Opção 3: Vercel (Também grátis e rápido)

```bash
npm install -g vercel
cd scriptum-v2.5
vercel --prod
```

---

## ⚙️ Configurar Frontend para usar API

Edita `scriptum-v2.5/src/lib/constants.ts`:

```typescript
export const API_BASE = import.meta.env.VITE_API_BASE_URL ||
  'https://scriptum-api.onrender.com';
```

Ou cria `.env` no frontend:

```bash
VITE_API_BASE_URL=https://scriptum-api.onrender.com
```

---

## 🔄 Deploy Automático

Render faz deploy automático quando fazes push para `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main

# Render deteta e faz deploy automaticamente
```

---

## 📊 Monitorização

**Ver logs:**
- Dashboard Render → Teu serviço → Tab "Logs"
- Logs em tempo real

**Ver métricas:**
- Dashboard → Tab "Metrics"
- CPU, Memória, Requests

**Health Check:**
- Render verifica `/health` automaticamente
- Se falhar 3x, restart automático

---

## ⚠️ Limitações Free Tier

### Render Free:
- ⚠️ **Hiberna após 15 min inatividade**
- ⚠️ Primeiro acesso demora 10-30s (wake up)
- ✅ 750 horas/mês (suficiente)
- ✅ Deploy ilimitados
- ✅ 100GB bandwidth

### Como evitar hibernação:
1. **Upgrade para Starter ($7/mês)** - Sem hibernação
2. **Usar cron job grátis:**
   ```bash
   # https://cron-job.org (grátis)
   # Ping a cada 10 minutos:
   curl https://scriptum-api.onrender.com/health
   ```

---

## 🐛 Troubleshooting

### Deploy falha:

**Erro:** `ModuleNotFoundError`
```bash
# Verifica requirements.txt tem todas as dependências
pip freeze > requirements.txt
```

**Erro:** `Port already in use`
```python
# Usa a variável PORT do Render
import os
port = int(os.environ.get('PORT', 5001))
```

**Erro:** `Timeout`
```bash
# Aumenta timeout no gunicorn
gunicorn -w 2 --timeout 120 app:app
```

### Serviço não responde:

1. Verifica logs no dashboard
2. Testa health check: `/health`
3. Verifica variáveis ambiente
4. Faz restart manual

### API keys não funcionam:

1. Verifica que adicionaste no dashboard Render
2. Não uses `.env` no código (Render injeta automaticamente)
3. Testa localmente primeiro

---

## 💰 Upgrade para Paid (Opcional)

Se precisares de:
- ❌ Sem hibernação
- ⚡ Performance melhor
- 📈 Mais recursos

**Render Starter: $7/mês**
- Sempre ativo
- 512MB RAM
- Deploy mais rápido

---

## 🔗 URLs Finais

Após deploy:
- **Backend API:** https://scriptum-api.onrender.com
- **Frontend:** https://scriptum.netlify.app (ou Vercel)
- **Docs API:** https://scriptum-api.onrender.com/diagnostics

---

## ✅ Checklist Final

- [ ] Render account criada
- [ ] Repo GitHub conectado
- [ ] Backend deployed no Render
- [ ] Environment variables configuradas
- [ ] Health check funciona (`/health`)
- [ ] Frontend deployed (Netlify/Vercel)
- [ ] Frontend conectado ao backend
- [ ] Testa upload de vídeo
- [ ] Testa search de legendas
- [ ] Testa tradução

---

**🎉 Deploy completo! Tua app está online e grátis! 🚀**
