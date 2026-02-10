# Deploy Scriptum API no Google Cloud Platform (Cloud Run)

## 📋 Pré-requisitos

1. **Conta GCP** com faturação ativada (free tier disponível)
2. **gcloud CLI** instalado: https://cloud.google.com/sdk/docs/install
3. **Docker** instalado: https://docs.docker.com/get-docker/
4. **API Keys** configuradas (TMDB, OpenSubtitles, Gemini)

## 🚀 Opção 1: Deploy Rápido (Script Automático)

### 1. Instalar gcloud CLI (se necessário)

```bash
# macOS
brew install --cask google-cloud-sdk

# Ou download direto
curl https://sdk.cloud.google.com | bash
```

### 2. Login e configuração inicial

```bash
# Login na conta Google
gcloud auth login

# Criar novo projeto (ou usar existente)
gcloud projects create scriptum-api --name="Scriptum API"

# Definir projeto ativo
gcloud config set project scriptum-api
```

### 3. Configurar API Keys

```bash
# Exportar as API keys (temporário)
export TMDB_API_KEY="your-tmdb-key"
export OPENSUBTITLES_API_KEY="your-opensubtitles-key"
export GEMINI_API_KEY="your-gemini-key"
```

### 4. Executar deploy

```bash
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

## 🔧 Opção 2: Deploy Manual (Passo a Passo)

### 1. Autenticar e configurar

```bash
gcloud auth login
gcloud config set project scriptum-api
```

### 2. Ativar APIs necessárias

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Build da imagem Docker

```bash
# Build e push para Container Registry
gcloud builds submit --tag gcr.io/scriptum-api/scriptum-api
```

### 4. Deploy no Cloud Run

```bash
gcloud run deploy scriptum-api \
    --image gcr.io/scriptum-api/scriptum-api \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "DEBUG=False,TMDB_API_KEY=${TMDB_API_KEY},OPENSUBTITLES_API_KEY=${OPENSUBTITLES_API_KEY},GEMINI_API_KEY=${GEMINI_API_KEY}"
```

### 5. Obter URL do serviço

```bash
gcloud run services describe scriptum-api \
    --region europe-west1 \
    --format 'value(status.url)'
```

## 🔐 Gestão de Secrets (Recomendado)

Para maior segurança, use o **Secret Manager** em vez de env vars:

### 1. Criar secrets

```bash
# Criar secrets no Secret Manager
echo -n "your-tmdb-key" | gcloud secrets create tmdb-api-key --data-file=-
echo -n "your-opensubtitles-key" | gcloud secrets create opensubtitles-api-key --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
```

### 2. Deploy com secrets

```bash
gcloud run deploy scriptum-api \
    --image gcr.io/scriptum-api/scriptum-api \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --set-secrets "TMDB_API_KEY=tmdb-api-key:latest,OPENSUBTITLES_API_KEY=opensubtitles-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

## 🌍 Atualizar Frontend

Após o deploy, atualiza o `API_BASE` no frontend:

```typescript
// src/lib/constants.ts
export const API_BASE = 'https://scriptum-api-xxxxxxxxx-ew.a.run.app';
```

## 💰 Custos Estimados (Free Tier)

Cloud Run Free Tier inclui:
- **2 milhões** de requests/mês
- **360,000 GB-segundos** de memória
- **180,000 vCPU-segundos**

Para este projeto: **~€0-5/mês** com uso moderado

## 🔍 Monitorização

Ver logs em tempo real:
```bash
gcloud run services logs tail scriptum-api --region europe-west1
```

Ver métricas no console:
```bash
gcloud run services describe scriptum-api --region europe-west1
```

## 🛠️ Troubleshooting

### Erro: "Permission denied"
```bash
gcloud auth application-default login
```

### Erro: "Quota exceeded"
Aumenta a quota no console GCP ou muda de região

### Erro: "Build failed"
Verifica o Dockerfile e requirements.txt

## 📊 Comparação: Render vs GCP Cloud Run

| Característica | Render | GCP Cloud Run |
|----------------|--------|---------------|
| Free Tier | Limitado | 2M requests/mês |
| Cold Start | ~30s | ~5-10s |
| Escalabilidade | Manual | Auto |
| Região EU | ✅ Frankfurt | ✅ Múltiplas |
| Custo/mês | €7+ | €0-5 |

## 🎯 Próximos Passos

1. ✅ Deploy no Cloud Run
2. 🔄 Configurar CI/CD com GitHub Actions
3. 📊 Setup de monitoring (Cloud Monitoring)
4. 🚀 CDN para assets estáticos
5. 🔐 Adicionar autenticação (opcional)
