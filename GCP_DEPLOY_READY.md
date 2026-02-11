# 🚀 PRONTO PARA DEPLOY NO GCP CLOUD RUN

## Tudo está preparado! Segue estes passos:

---

## 📋 PASSO 1: Aceder ao Console

👉 **Abre:** https://console.cloud.google.com/run

1. Faz login com a tua conta Google
2. Aceita os termos se for a primeira vez

---

## 🆕 PASSO 2: Criar Projeto

1. Clica no **seletor de projetos** (canto superior esquerdo)
2. Clica em **"NEW PROJECT"**
3. Nome: `scriptum-api`
4. Clica **"CREATE"**
5. **Seleciona o projeto** quando criado

---

## 🏃 PASSO 3: Ativar Cloud Run

1. No menu (☰) vai a **"Cloud Run"**
2. Clica em **"ENABLE API"** se aparecer
3. Aguarda ~1 minuto

---

## 🔗 PASSO 4: Conectar GitHub

1. Clica em **"CREATE SERVICE"**
2. Escolhe **"Continuously deploy from a repository"**
3. Clica **"SET UP WITH CLOUD BUILD"**

### Conectar Repo:
1. **"MANAGE CONNECTED REPOSITORIES"**
2. **"CONNECT REPOSITORY"**
3. Escolhe **"GitHub"**
4. Autoriza acesso
5. Seleciona: **`DrNOFX97/scriptum-v2.5`**
6. **"CONNECT"** → **"NEXT"**

### Configurar Build:
1. **Branch:** `main`
2. **Build Type:** `Dockerfile`
3. **Source location:** `/Dockerfile`
4. **"SAVE"**

---

## ⚙️ PASSO 5: Configurar Serviço

### Básico:
- **Service name:** `scriptum-api`
- **Region:** `europe-west1` (Belgium)
- ✅ **Allow unauthenticated invocations**

### Container (expandir "CONTAINER, NETWORKING, SECURITY"):

#### Container:
- **Port:** `8080` ⚠️ IMPORTANTE!
- **Memory:** `2 GiB`
- **CPU:** `2`
- **Timeout:** `300` seconds

#### Variables & Secrets (tab):

Clica **"+ ADD VARIABLE"** para cada uma:

```
Nome: DEBUG
Valor: False

Nome: TMDB_API_KEY
Valor: 71790f9d7c0f5b24e9bed93499f5cb96

Nome: OPENSUBTITLES_API_KEY
Valor: qPYFmhhwzETJQkFSz8f6wHxYMRCqOIeq

Nome: GEMINI_API_KEY
Valor: AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c
```

⚠️ **COPIA E COLA exatamente como está acima!**

#### Autoscaling:
- **Min instances:** `0`
- **Max instances:** `10`

---

## 🚀 PASSO 6: DEPLOY!

1. Revê tudo
2. Clica **"CREATE"** no fundo
3. Aguarda 3-5 minutos ⏳
4. Vês logs em tempo real

---

## 🎉 PASSO 7: Obter URL

Quando terminar:
1. ✅ Mensagem verde: "Service deployed"
2. **Copia o Service URL** (exemplo: `https://scriptum-api-abc123-ew.a.run.app`)

### Testar:
```bash
# No browser ou terminal:
https://[TEU-URL]/health
```

Deves ver:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "2.5.0"
  }
}
```

---

## 🔧 PASSO 8: Atualizar Frontend

Quando tiveres o URL, avisa-me e eu atualizo o frontend automaticamente!

Ou faz manualmente:

1. Edita: `scriptum-v2.5/src/lib/constants.ts`
2. Muda para: `export const API_BASE = 'https://[TEU-URL]';`
3. Commit e push

---

## ✅ Checklist Rápido

- [ ] Console GCP aberto
- [ ] Projeto "scriptum-api" criado
- [ ] Cloud Run ativado
- [ ] GitHub conectado (DrNOFX97/scriptum-v2.5)
- [ ] Dockerfile configurado (/Dockerfile)
- [ ] Region: europe-west1
- [ ] Port: 8080
- [ ] 4 variáveis de ambiente adicionadas
- [ ] Deploy iniciado
- [ ] URL obtido e testado
- [ ] Frontend atualizado

---

## 💡 Dicas:

- **Build demora 3-5 min** na primeira vez
- Se der erro, vê os **logs** no console
- O **cold start** inicial pode demorar ~10s
- Depois fica **super rápido** ⚡

---

## 🆘 Problemas?

Se ficares preso em algum passo, avisa:
- "preso no passo X"
- "erro: [mensagem]"
- "não encontro [opção]"

Estou aqui para ajudar! 🚀

---

## 📊 Depois do Deploy

### Monitoring:
- **Logs:** Tab "LOGS" no serviço
- **Metrics:** Tab "METRICS"
- **Costs:** ~€0-3/mês

### Auto-deploy:
✅ Já está configurado!
Cada push para `main` faz deploy automático.

---

**Boa sorte! Em 10 minutos está no ar! 🎯**
