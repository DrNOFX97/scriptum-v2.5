# Scriptum v2.0 - Referência Rápida

## Sistema Completo de Sincronização de Legendas

### Ficheiros Principais
```
subtitle-translator/
├── sync_api.py          # API REST
├── smart_sync.py        # Motor de sincronização  
├── config.py            # Configurações ✨
├── utils.py             # Utilidades ✨
├── opensubtitles_api.py # Cliente OpenSubtitles
├── sync.html + sync.js  # Interface web
├── .env                 # API_KEY=qPYFmhhwzETJQkFSz8f6wHxYMRCqOIeq ✨
└── README.md            # Documentação ✨
```

### Uso
```bash
./start_sync_web.sh  # Inicia tudo automaticamente
```

### O Que Funciona
✅ Sincronização automática com MLX Whisper  
✅ OpenSubtitles.com (100 downloads/dia)  
✅ Suporte MKV/MP4/AVI/WebM  
✅ Interface web moderna  
✅ Ajustes manuais ±10s/±1s/±0.1s  

### Bugs Corrigidos
✅ MKV agora carrega (sync.js:93-108, sync.html:610)  
✅ OpenSubtitles integrado  
✅ API key em .env  

### Código Novo
- config.py (167 linhas) - Configurações centralizadas
- utils.py (230 linhas) - Funções reutilizáveis
- README.md - Documentação completa
- SESSAO_RESUMO.md - Histórico detalhado

### Estado
🟢 100% Funcional | Servidor: localhost:5001 | API Key: Configurada
