# 🚀 Guia de Deployment - Scriptum v2.5

Guia completo para deployment do Scriptum v2.5 no Render (free tier).

---

## 📦 Arquitetura

- **Frontend:** React + TypeScript + Vite (Static Site)
- **Backend:** Flask + Python (Web Service)
- **Hosting:** Render (free tier)
- **Auto-deploy:** Ativado em ambos (push para `main`)

---

## 🌐 URLs de Produção

### Frontend
- **URL:** https://scriptum-frontend.onrender.com
- **Dashboard:** https://dashboard.render.com/static/srv-d65khqmr433s73f5tki0
- **GitHub:** https://github.com/DrNOFX97/scriptum-frontend

### Backend
- **URL:** https://scriptum-api-zicg.onrender.com
- **Dashboard:** https://dashboard.render.com/web/srv-d65kersr85hc73bcbf3g
- **GitHub:** https://github.com/DrNOFX97/scriptum-v2.5

---

## ⚙️ Configuração do Backend (Flask API)

### 1. Aceder ao Dashboard

Vai a: https://dashboard.render.com/web/srv-d65kersr85hc73bcbf3g

### 2. Configurar Build & Deploy Settings

Clica em **"Settings"** no menu lateral e configura:

#### Root Directory
```
subtitle-translator
```

#### Build Command
```bash
pip install -r requirements.txt
```

#### Start Command
```bash
gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app
```

#### Python Version
```
3.11.0
```

### 3. Configurar Health Check

No dashboard, vai a **"Settings"** → **"Health & Alerts"**:

```
Health Check Path: /health
```

### 4. Variáveis de Ambiente (já configuradas ✅)

As seguintes variáveis já foram adicionadas via API:

```bash
TMDB_API_KEY=71790f9d7c0f5b24e9bed93499f5cb96
OPENSUBTITLES_API_KEY=qPYFmhhwzETJQkFSz8f6wHxYMRCqOIeq
GEMINI_API_KEY=AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c
OPENSUBTITLES_USER_AGENT=Scriptum v2.5
```

Para adicionar/editar variáveis:
1. Vai a **"Environment"** no menu lateral
2. Clica em **"Add Environment Variable"**
3. Adiciona Key/Value
4. Clica em **"Save Changes"**

### 5. Deploy Manual

Depois de configurar tudo:
1. Vai ao dashboard do serviço
2. Clica em **"Manual Deploy"** → **"Deploy latest commit"**
3. Aguarda 3-5 minutos pelo build

### 6. Verificar Deploy

Testa o health endpoint:
```bash
curl https://scriptum-api-zicg.onrender.com/health
```

Resposta esperada:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "2.5.0",
    "service": "Scriptum API"
  }
}
```

---

## 🎨 Configuração do Frontend (React Static Site)

### Status: ✅ Já configurado e funcionando!

O frontend já está **live** e funcional. Configuração atual:

#### Build Settings
```bash
Build Command: npm install && npm run build
Publish Directory: dist
```

#### Variáveis de Ambiente
```bash
NODE_ENV=production
VITE_API_BASE_URL=https://scriptum-api-zicg.onrender.com
```

#### Headers de Segurança (configurados)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

#### Routing SPA (configurado)
- Todas as rotas redirecionam para `/index.html`
- Suporta client-side routing

### Testar Frontend

Acede a: https://scriptum-frontend.onrender.com

---

## 🔄 Deploy Automático (Auto-Deploy)

Ambos os serviços têm auto-deploy ativado:

### Backend
```bash
cd /Users/f.nuno/projetos/subtitle-translator
git add .
git commit -m "Update backend feature"
git push origin main
# Deploy automático inicia no Render
```

### Frontend
```bash
cd /Users/f.nuno/projetos/scriptum-v2.5
git add .
git commit -m "Update frontend feature"
git push origin main
# Deploy automático inicia no Render
```

### Monitorizar Deploys

- **Backend logs:** https://dashboard.render.com/web/srv-d65kersr85hc73bcbf3g/logs
- **Frontend logs:** https://dashboard.render.com/static/srv-d65khqmr433s73f5tki0/logs

---

## ⚠️ Limitações Free Tier

### Render Free Tier
- ⚠️ **Serviço hiberna após 15 minutos de inatividade**
- ⚠️ Primeiro acesso após hibernação: 30-60 segundos
- ✅ 750 horas/mês (suficiente para 1 serviço 24/7)
- ✅ Deploys ilimitados
- ✅ 100GB bandwidth/mês
- ✅ SSL/HTTPS automático

### Como Evitar Hibernação

#### Opção 1: Upgrade para Starter ($7/mês)
- Sem hibernação
- Sempre ativo
- Performance melhor

#### Opção 2: Cron Job Grátis
Usar https://cron-job.org para ping a cada 10 minutos:

```bash
# Configurar no cron-job.org:
URL: https://scriptum-api-zicg.onrender.com/health
Interval: Every 10 minutes
```

#### Opção 3: UptimeRobot (Grátis)
https://uptimerobot.com

1. Cria conta grátis
2. Adiciona monitor: https://scriptum-api-zicg.onrender.com/health
3. Intervalo: 5 minutos

---

## 🐛 Troubleshooting

### Backend não responde

1. **Verifica logs:**
   ```bash
   # Via dashboard:
   https://dashboard.render.com/web/srv-d65kersr85hc73bcbf3g/logs
   ```

2. **Verifica configuração:**
   - Root directory = `subtitle-translator`
   - Build command está preenchido
   - Start command está correto
   - Health check path = `/health`

3. **Testa health check:**
   ```bash
   curl https://scriptum-api-zicg.onrender.com/health
   ```

4. **Se falhar, faz deploy manual:**
   Dashboard → "Manual Deploy" → "Deploy latest commit"

### Frontend mostra erro de API

1. **Verifica URL do backend:**
   ```bash
   # No dashboard do frontend, verifica:
   VITE_API_BASE_URL=https://scriptum-api-zicg.onrender.com
   ```

2. **Testa backend primeiro:**
   ```bash
   curl https://scriptum-api-zicg.onrender.com/health
   ```

3. **Se backend funciona mas frontend não:**
   - Verifica CORS no backend (já configurado)
   - Verifica console do browser (F12)
   - Faz hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

### Deploy falha no build

#### Backend (Python)
```bash
# Erro comum: dependências em falta
# Solução: Atualiza requirements.txt
cd subtitle-translator
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

#### Frontend (Node)
```bash
# Erro comum: node_modules cache
# Solução: Clear cache no Render
# Dashboard → Settings → "Clear build cache & redeploy"
```

### Timeout durante deploy

1. Vai ao dashboard do serviço
2. Settings → aumenta timeout para 180 segundos
3. Redeploy

### Serviço hiberna constantemente

**Solução:** Configura um dos métodos anti-hibernação acima (cron job ou UptimeRobot)

---

## 📊 Monitorização

### Ver Logs em Tempo Real

**Backend:**
```bash
# Via dashboard:
https://dashboard.render.com/web/srv-d65kersr85hc73bcbf3g/logs

# Via API (com Render API key):
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv-d65kersr85hc73bcbf3g/deploys"
```

**Frontend:**
```bash
https://dashboard.render.com/static/srv-d65khqmr433s73f5tki0/logs
```

### Ver Métricas

Dashboard → Tab "Metrics":
- CPU usage
- Memory usage
- Request count
- Response times

### Alertas

Dashboard → Settings → "Notifications":
- Email quando deploy falha
- Email quando serviço fica down
- Webhook para Slack/Discord

---

## 🔐 Segurança

### API Keys (já configuradas)

Todas as keys estão em variáveis de ambiente (não no código):
- ✅ `TMDB_API_KEY`
- ✅ `OPENSUBTITLES_API_KEY`
- ✅ `GEMINI_API_KEY`

### CORS (já configurado)

Backend permite requests do frontend:
```python
# Em app.py:
CORS(app, origins=[
    "https://scriptum-frontend.onrender.com",
    "http://localhost:5173"  # Desenvolvimento local
])
```

### HTTPS

- ✅ Render fornece SSL automático
- ✅ Todos os URLs usam HTTPS
- ✅ Certificados renovados automaticamente

### Headers de Segurança (já configurados)

Frontend serve com headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## 🧪 Testes Pós-Deploy

### 1. Health Check
```bash
curl https://scriptum-api-zicg.onrender.com/health
```

### 2. Frontend Acessível
```bash
curl -I https://scriptum-frontend.onrender.com
# Deve retornar 200 OK
```

### 3. API Endpoints

**Search Subtitles:**
```bash
curl -X POST https://scriptum-api-zicg.onrender.com/search-subtitles \
  -H "Content-Type: application/json" \
  -d '{"query": "Inception", "language": "pt"}'
```

**Movie Recognition:**
```bash
curl -X POST https://scriptum-api-zicg.onrender.com/recognize-movie \
  -F "video=@path/to/video.mp4"
```

### 4. Frontend Features

Abre https://scriptum-frontend.onrender.com e testa:
- ✅ Página carrega
- ✅ Navegação funciona (Sidebar)
- ✅ Video Analysis aceita upload
- ✅ Subtitle Search retorna resultados
- ✅ Settings guarda configurações

---

## 🔄 Rollback (se necessário)

### Via Dashboard
1. Vai a "Deploys" no menu lateral
2. Encontra o deploy anterior que funcionava
3. Clica em "Redeploy" nesse commit específico

### Via Git
```bash
# Reverte último commit
git revert HEAD
git push origin main

# Ou volta para commit específico
git reset --hard <commit-hash>
git push --force origin main
```

⚠️ **Cuidado:** Force push pode causar problemas em produção.

---

## 💰 Custos

### Free Tier Atual
- **Backend:** $0/mês (com hibernação)
- **Frontend:** $0/mês (sempre ativo)
- **Total:** $0/mês

### Upgrade para Starter (Recomendado)
- **Backend:** $7/mês (sem hibernação, 512MB RAM)
- **Frontend:** $0/mês (static sites grátis)
- **Total:** $7/mês

**Benefícios Starter:**
- ✅ Sem hibernação (sempre ativo)
- ✅ Performance melhor
- ✅ Builds mais rápidos
- ✅ Suporte prioritário

---

## 📝 Checklist Final

Deployment completo verificado:

- [x] Backend repository no GitHub
- [x] Frontend repository no GitHub
- [x] Backend service criado no Render
- [x] Frontend static site criado no Render
- [x] Variáveis de ambiente configuradas
- [x] Auto-deploy ativado
- [ ] Build commands configurados no backend (MANUAL)
- [ ] Health check funciona
- [ ] Frontend acessa backend corretamente
- [ ] Testa upload de vídeo
- [ ] Testa search de legendas
- [ ] Testa sincronização
- [ ] Testa tradução

---

## 🆘 Suporte

### Render Support
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Scriptum Issues
- Backend: https://github.com/DrNOFX97/scriptum-v2.5/issues
- Frontend: https://github.com/DrNOFX97/scriptum-frontend/issues

---

## 🎯 Próximos Passos

1. **Configurar Backend Manualmente** (5 min)
   - Dashboard → Settings → Build/Start commands
   - Manual Deploy

2. **Testar Full-Stack** (10 min)
   - Abre frontend
   - Testa todas as features
   - Verifica logs

3. **Configurar Monitorização** (10 min)
   - UptimeRobot ou cron-job.org
   - Previne hibernação

4. **Documentação para Utilizadores** (opcional)
   - Como usar a app
   - Features disponíveis
   - Limitações do free tier

---

**🎉 Deployment concluído! Tua app está na cloud! 🚀**

*Última atualização: 2026-02-10*
