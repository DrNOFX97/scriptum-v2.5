# 🚀 Deploy LegendasDivx API no Google Cloud Run

## Opção 1: Deploy via GCP Console (Recomendado)

### Passo 1: Aceder ao Cloud Run
1. Vai a: https://console.cloud.google.com/run
2. Seleciona o projeto: **scriptum-v2-50**

### Passo 2: Criar Novo Serviço
1. Clica em **"CREATE SERVICE"**
2. Escolhe **"Deploy one revision from an existing container image"**

### Passo 3: Build da Imagem (Local)
No terminal, na pasta `legendasdivx-api`:

```bash
# Build da imagem Docker localmente
docker build -t gcr.io/scriptum-v2-50/legendasdivx-api .

# Push para Google Container Registry
docker push gcr.io/scriptum-v2-50/legendasdivx-api
```

**Se der erro de autenticação:**
```bash
gcloud auth configure-docker
```

### Passo 4: Configurar o Serviço no Console

**Básico:**
- **Container image URL:** `gcr.io/scriptum-v2-50/legendasdivx-api`
- **Service name:** `legendasdivx-api`
- **Region:** `europe-west1` (Belgium)
- **Authentication:** ✅ Allow unauthenticated invocations

**Container:**
- **Container port:** `8080`
- **Memory:** `512 MiB`
- **CPU:** `1`
- **Request timeout:** `300` segundos
- **Max requests per container:** `80`

**Variables & Secrets:**

Adiciona estas variáveis de ambiente:

| Nome | Valor |
|------|-------|
| `LEGENDASDIVX_USER` | `ElHefe` |
| `LEGENDASDIVX_PASS` | `fn1102` |
| `API_HOST` | `0.0.0.0` |
| `API_PORT` | `8080` |
| `API_RELOAD` | `false` |
| `MAX_REQUESTS_PER_MINUTE` | `10` |
| `REQUEST_DELAY_SECONDS` | `3` |
| `CACHE_TTL_HOURS` | `24` |
| `DATABASE_PATH` | `/data/subtitles.db` |
| `LOG_LEVEL` | `INFO` |

**Autoscaling:**
- **Min instances:** `0` (para poupar)
- **Max instances:** `10`

### Passo 5: Deploy
1. Clica em **"CREATE"**
2. Aguarda ~2-3 minutos
3. Copia a URL do serviço (ex: `https://legendasdivx-api-xxxxx.run.app`)

---

## Opção 2: Deploy via Script (se tiveres gcloud instalado)

```bash
cd /Users/f.nuno/projetos/subtitle-translator/legendasdivx-api
./deploy-to-cloudrun.sh
```

---

## Passo Final: Atualizar Backend Principal

Depois do deploy, precisa atualizar o backend principal para usar a nova URL:

1. Editar: `/Users/f.nuno/projetos/subtitle-translator/src/scriptum_api/config.py`
2. Mudar:
   ```python
   LEGENDASDIVX_API_URL = "http://127.0.0.1:8000"  # ❌ Antigo (localhost)
   ```
   Para:
   ```python
   LEGENDASDIVX_API_URL = "https://legendasdivx-api-xxxxx.run.app"  # ✅ Novo
   ```
3. Fazer redeploy do backend principal

---

## Testar

```bash
# Testar health endpoint
curl https://legendasdivx-api-xxxxx.run.app/health

# Testar pesquisa
curl "https://legendasdivx-api-xxxxx.run.app/api/v1/search?query=Inception&language=pt-pt"
```

---

## 💰 Custos Estimados

- **Free tier:** 2 milhões de requests/mês GRÁTIS
- **Após free tier:** ~$0.40 por milhão de requests
- **Idle time:** $0 (com min instances = 0)

**Conclusão:** Praticamente grátis para uso pessoal! 🎉
