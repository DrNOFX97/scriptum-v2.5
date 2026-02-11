# 🚀 Deploy Scriptum API no GCP Cloud Run (Web Console)

## Guia Passo-a-Passo Visual

### ✅ Pré-requisitos
- Conta Google
- Repositório GitHub com o código (já tens!)
- API Keys: TMDB, OpenSubtitles, Gemini

---

## 📋 Passo 1: Aceder ao Console GCP

1. **Vai a:** https://console.cloud.google.com/
2. **Login** com a tua conta Google
3. Se for a primeira vez:
   - Aceita os termos de serviço
   - Configura faturação (não te preocupes, há free tier!)

---

## 🆕 Passo 2: Criar Novo Projeto

1. Clica no **menu de projetos** (canto superior esquerdo)
2. Clica em **"NEW PROJECT"**
3. Preenche:
   - **Project name:** `scriptum-api`
   - **Organization:** deixa como está
4. Clica em **"CREATE"**
5. Aguarda ~30 segundos até o projeto ser criado
6. **Seleciona o projeto** no menu

---

## 🏃 Passo 3: Ir para Cloud Run

1. No menu lateral (☰), vai a **"Cloud Run"**
   - Ou acede diretamente: https://console.cloud.google.com/run
2. Se aparecer popup para **"Enable API"**, clica em **"ENABLE"**
3. Aguarda ~1 minuto até a API ser ativada

---

## 🔗 Passo 4: Conectar GitHub (Primeira vez)

1. Clica em **"CREATE SERVICE"**
2. Escolhe **"Continuously deploy from a repository (source or function)"**
3. Clica em **"SET UP WITH CLOUD BUILD"**

### 4.1 Conectar Repositório

1. Clica em **"MANAGE CONNECTED REPOSITORIES"**
2. Clica em **"CONNECT REPOSITORY"**
3. Escolhe **"GitHub"**
4. Autoriza o acesso ao GitHub quando pedido
5. Seleciona o repositório: **`DrNOFX97/scriptum-v2.5`**
6. Clica em **"CONNECT"**
7. Clica em **"NEXT"**

### 4.2 Configurar Build

1. **Branch:** `main` (já deve estar selecionado)
2. **Build Type:** `Dockerfile`
3. **Source location:** `/Dockerfile` (raiz do repo)
4. Clica em **"SAVE"**

---

## ⚙️ Passo 5: Configurar o Serviço

### 5.1 Configurações Básicas

1. **Service name:** `scriptum-api` (ou o que quiseres)
2. **Region:** `europe-west1` (Belgium - mais perto de PT)
   - Alternativas: `europe-west4` (Netherlands), `europe-southwest1` (Madrid)
3. **CPU allocation:** `CPU is only allocated during request processing`
4. **Authentication:**
   - ✅ Marca **"Allow unauthenticated invocations"** (para API pública)

### 5.2 Container Configuration

Clica em **"CONTAINER, NETWORKING, SECURITY"** para expandir:

#### Container

1. **Container port:** `8080` (importante!)
2. **Memory:** `2 GiB` (ou mais se precisares)
3. **CPU:** `2` vCPU
4. **Request timeout:** `300` segundos (5 minutos)
5. **Maximum requests per container:** `80`

#### Variables & Secrets

Clica em **"VARIABLES & SECRETS"** tab:

1. Clica em **"+ ADD VARIABLE"** para cada uma:

```
Nome: DEBUG
Valor: False

Nome: TMDB_API_KEY
Valor: [tua chave TMDB]

Nome: OPENSUBTITLES_API_KEY
Valor: [tua chave OpenSubtitles]

Nome: GEMINI_API_KEY
Valor: [tua chave Gemini]
```

⚠️ **IMPORTANTE:** Copia os valores corretos das tuas API keys!

#### Autoscaling

1. **Minimum number of instances:** `0` (para não pagar quando não está em uso)
2. **Maximum number of instances:** `10`

---

## 🚀 Passo 6: Deploy!

1. Revê todas as configurações
2. Clica em **"CREATE"** no fundo da página
3. Aguarda 3-5 minutos enquanto:
   - ✅ Build da imagem Docker
   - ✅ Push para Container Registry
   - ✅ Deploy no Cloud Run
   - ✅ Health checks

**Vais ver um ecrã com logs em tempo real do deployment.**

---

## 🎉 Passo 7: Obter URL e Testar

### Quando o deploy terminar:

1. Vais ver uma mensagem verde: **"Service scriptum-api has been deployed"**
2. Copia o **Service URL** (algo como: `https://scriptum-api-xxxxxxxxx-ew.a.run.app`)

### Testar a API:

Abre no browser ou usa curl:

```bash
# Health check
curl https://[SEU-URL]/health

# Ou abre no browser:
https://[SEU-URL]/health
```

Deves ver:
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

## 🔧 Passo 8: Atualizar Frontend

Edita o ficheiro do frontend:

**`scriptum-v2.5/src/lib/constants.ts`:**

```typescript
export const API_BASE = 'https://scriptum-api-xxxxxxxxx-ew.a.run.app';
```

(Substitui pelo teu URL real)

Depois faz commit e push:

```bash
cd /Users/f.nuno/projetos/scriptum-v2.5
git add src/lib/constants.ts
git commit -m "Update API_BASE to GCP Cloud Run URL"
git push origin main
```

O Netlify vai fazer auto-deploy do frontend atualizado! 🎯

---

## 📊 Passo 9: Monitorizar

### Ver Logs em Tempo Real

1. No Cloud Run, clica no teu serviço **"scriptum-api"**
2. Vai ao tab **"LOGS"**
3. Vês todos os requests e erros em tempo real

### Ver Métricas

Tab **"METRICS"** mostra:
- 📈 Request count
- ⏱️ Latency
- 💰 Costs
- 🔥 Instance count

---

## 💰 Custos (Free Tier)

Cloud Run Free Tier POR MÊS:
- ✅ **2 milhões** de requests
- ✅ **360,000** GB-segundos de memória
- ✅ **180,000** vCPU-segundos
- ✅ **1 GB** network egress

**Estimativa para este projeto:** €0-3/mês com uso moderado

---

## 🔄 Atualizações Futuras

### Opção A: Auto-Deploy (Recomendado)

Já está configurado! Cada push para `main` faz deploy automático.

### Opção B: Deploy Manual

1. Vai ao Cloud Run
2. Clica no serviço
3. Clica em **"EDIT & DEPLOY NEW REVISION"**
4. Altera o que precisares
5. Clica em **"DEPLOY"**

---

## ❓ Troubleshooting

### Build Failed

- Verifica se o Dockerfile está na raiz do repo
- Verifica se requirements.txt está correto
- Vê os logs de build no console

### 503 Service Unavailable

- Verifica se a porta é 8080
- Verifica se as env vars estão corretas
- Vê os logs para erros de startup

### Timeout

- Aumenta o request timeout para 300s
- Verifica se o código tem loops infinitos

---

## 🎯 Comparação Final

| | Render | GCP Cloud Run |
|---|---|---|
| Setup Time | ✅ 5 min | ✅ 10 min |
| Free Tier | 750h/mês | 2M requests/mês |
| Cold Start | ~30s | ~5-10s ⚡ |
| Max Memory | 512MB | 8GB+ |
| Max Timeout | 120s | 3600s |
| Auto-scaling | ❌ | ✅ |
| Custo estimado | €7/mês | €0-3/mês 💰 |

---

## ✅ Checklist Final

- [ ] Conta GCP criada
- [ ] Projeto criado
- [ ] Cloud Run API ativada
- [ ] GitHub conectado
- [ ] Serviço configurado
- [ ] Variáveis de ambiente definidas
- [ ] Deploy concluído
- [ ] URL obtido e testado
- [ ] Frontend atualizado
- [ ] Teste end-to-end funcionando

---

## 🆘 Precisa de Ajuda?

Se ficares preso em algum passo, avisa! Posso:
- Clarificar qualquer passo
- Resolver problemas específicos
- Ajudar com configurações avançadas

Boa sorte! 🚀
