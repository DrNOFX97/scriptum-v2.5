# Deploy Instructions - Backend (Audio Extraction)

## Pré-requisitos

1. Google Cloud SDK instalado
2. Autenticação configurada
3. Projeto GCP ativo

## Comandos de Deploy

### 1. Deploy para Cloud Run

```bash
cd /Users/f.nuno/projetos/subtitle-translator

gcloud run deploy scriptum-v2-5 \
  --source . \
  --region=europe-west1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --timeout=900 \
  --max-instances=10 \
  --min-instances=0
```

### 2. Verificar Deploy

```bash
# Obter URL do serviço
gcloud run services describe scriptum-v2-5 \
  --region=europe-west1 \
  --format='value(status.url)'

# Testar health endpoint
curl https://scriptum-v2-5-315653817267.europe-west1.run.app/health
```

### 3. Ver Logs

```bash
# Logs em tempo real
gcloud run logs tail scriptum-v2-5 --region=europe-west1

# Últimas 50 linhas
gcloud run logs read scriptum-v2-5 \
  --region=europe-west1 \
  --limit=50
```

## Novos Endpoints Deployados

Após deploy, estarão disponíveis:

```
POST /extract-convert-audio
  - Inicia extração e conversão de áudio
  - Body: multipart/form-data com 'video' file
  - Response: { job_id, file_size_gb, estimated_time }

GET /extract-audio-status/<job_id>
  - Verifica status da extração
  - Response: { status, progress: { percentage, message, stage } }

GET /extract-audio-download/<job_id>
  - Download do AAC extraído
  - Response: audio/aac file
```

## Teste do Backend

### 1. Teste Local (antes de deploy)

```bash
# Ativar venv
cd /Users/f.nuno/projetos/subtitle-translator
source .venv/bin/activate

# Rodar servidor local
python wsgi_prod.py
```

Em outro terminal:

```bash
# Testar extração
python test_audio_extraction.py ~/Downloads/test_video.mkv
```

### 2. Teste em Produção (após deploy)

```bash
# Upload de teste
curl -X POST https://scriptum-v2-5-315653817267.europe-west1.run.app/extract-convert-audio \
  -F "video=@test_video.mkv" \
  -o response.json

# Obter job_id
JOB_ID=$(cat response.json | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Verificar status
curl "https://scriptum-v2-5-315653817267.europe-west1.run.app/extract-audio-status/$JOB_ID"

# Download (quando completado)
curl "https://scriptum-v2-5-315653817267.europe-west1.run.app/extract-audio-download/$JOB_ID" \
  -o extracted_audio.aac
```

## Monitoramento

### Cloud Run Console

```
https://console.cloud.google.com/run/detail/europe-west1/scriptum-v2-5
```

Verificar:
- ✅ Request count
- ✅ Request latency
- ✅ Memory usage
- ✅ CPU utilization
- ✅ Error rate

### Alertas Importantes

1. **Timeout de 900s**
   - Ficheiros muito grandes podem exceder
   - Considerar aumentar se necessário

2. **Memória 2Gi**
   - Suficiente para ficheiros até ~10GB
   - Ajustar se necessário

3. **Concurrency**
   - Default: 80 requests por instância
   - Pode ser limitado para jobs pesados

## Rollback (se necessário)

```bash
# Listar revisões
gcloud run revisions list \
  --service=scriptum-v2-5 \
  --region=europe-west1

# Rollback para revisão anterior
gcloud run services update-traffic scriptum-v2-5 \
  --region=europe-west1 \
  --to-revisions=scriptum-v2-5-00001-abc=100
```

## Variáveis de Ambiente

Se necessário configurar:

```bash
gcloud run services update scriptum-v2-5 \
  --region=europe-west1 \
  --set-env-vars="CUSTOM_VAR=value"
```

## Custos Estimados

**Cloud Run:**
- Request: $0.40 por 1M requests
- CPU: $0.00002400 por vCPU-second
- Memory: $0.00000250 per GiB-second

**Estimativa para 100 extrações/dia:**
- ~$5-10/mês (dependendo do tamanho dos ficheiros)

## Troubleshooting

### Deploy falha com erro de permissions

```bash
# Verificar IAM
gcloud projects get-iam-policy PROJECT_ID

# Adicionar permissões se necessário
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:EMAIL" \
  --role="roles/run.admin"
```

### Container não inicia

```bash
# Verificar logs de startup
gcloud run logs read scriptum-v2-5 \
  --region=europe-west1 \
  --format="table(timestamp,severity,textPayload)" \
  --limit=100
```

### FFmpeg não encontrado

Verificar que Dockerfile tem:
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

## Checklist de Deploy

- [ ] Backend testado localmente
- [ ] Todos os testes passam
- [ ] Dockerfile correto
- [ ] Requirements.txt atualizado
- [ ] Deploy para Cloud Run
- [ ] Health check OK
- [ ] Teste de extração end-to-end
- [ ] Logs sem erros
- [ ] Frontend atualizado com URL correta

## Próximos Passos

Após deploy bem-sucedido:

1. ✅ Testar com ficheiro real grande (>4GB)
2. ✅ Verificar tempos de extração
3. ✅ Validar sincronização no frontend
4. ✅ Monitorar custos
5. ✅ Configurar alertas se necessário

---

**Status:** Ready for deployment!
