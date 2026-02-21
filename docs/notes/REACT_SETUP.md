# React Setup - Scriptum v2.1

## O Que Foi Feito ✅

### 1. Projeto React Criado
```bash
npm create vite@latest frontend -- --template react-ts
```

**Tecnologias:**
- React 18
- TypeScript
- Vite (build tool)

### 2. Dependências Instaladas

```bash
cd frontend
npm install
npm install react-router-dom zustand @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
```

**Packages instalados:**
- `react-router-dom` - Routing
- `zustand` - State management
- `@tanstack/react-query` - API data fetching
- `tailwindcss` - CSS framework

### 3. Tailwind CSS Configurado

Criados:
- `tailwind.config.js` - Configuração do Tailwind
- `postcss.config.js` - PostCSS config
- `src/index.css` - Tailwind directives

### 4. Estrutura de Pastas

```
frontend/src/
├── components/      # React components
├── hooks/           # Custom hooks (useVideo, useSubtitle, etc.)
├── services/        # API client (TypeScript version)
├── pages/           # Page components (Dashboard, Project, etc.)
├── store/           # Zustand stores
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Próximos Passos

### Fase 1: Converter ES6 → TypeScript ⏳

**Prioridade:** Converter managers ES6 para hooks React + TypeScript

1. **APIClient.js → services/api.ts**
   ```typescript
   // De: class APIClient
   // Para: export const api = { ... }
   ```

2. **VideoManager.js → hooks/useVideo.ts**
   ```typescript
   export function useVideo() {
     const [videoFile, setVideoFile] = useState<File | null>(null);
     const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
     // ...
   }
   ```

3. **SubtitleManager.js → hooks/useSubtitle.ts**
   ```typescript
   export function useSubtitle() {
     const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
     // ...
   }
   ```

4. **Logger.js → hooks/useLogger.ts**
   ```typescript
   export function useLogger() {
     const [logs, setLogs] = useState<LogEntry[]>([]);
     // ...
   }
   ```

5. **UIManager.js → Componentes React**
   - Separar em componentes menores
   - Usar state React nativo

### Fase 2: Routing Básico

Criar rotas iniciais:
```typescript
/ → Dashboard (lista de projetos)
/project/new → Criar projeto
/project/:id → Workspace do projeto
```

### Fase 3: Primeira Página Funcional

Implementar Dashboard com:
- Upload de vídeo
- Criar novo projeto
- Lista de projetos recentes (LocalStorage)

### Fase 4: Implementar Sitemap Completo

Seguir o sitemap proposto com todas as rotas.

## Comandos Úteis

```bash
# Desenvolvimento
cd frontend
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview

# Type checking
npm run tsc
```

## Estrutura Final Desejada

```
subtitle-translator/
├── backend/
│   ├── api/
│   │   ├── config.py
│   │   └── services/
│   │       ├── video_service.py
│   │       ├── subtitle_service.py
│   │       ├── translation_service.py
│   │       ├── sync_service.py
│   │       └── movie_service.py
│   └── app_refactored.py
│
├── frontend/ (React + TypeScript)
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
└── static/ (ES6 - legacy)
    └── js/
        ├── app.js
        └── modules/
```

## Integração Backend/Frontend

O frontend React vai consumir a mesma API Flask:

```typescript
// frontend/src/services/api.ts
const API_URL = 'http://localhost:5001';

export const api = {
  analyzeVideo: async (videoFile: File) => {
    const formData = new FormData();
    formData.append('video', videoFile);
    const res = await fetch(`${API_URL}/analyze-video`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },
  // ... outros endpoints
};
```

## Estado Atual

✅ Projeto React criado
✅ Dependências instaladas
✅ Tailwind configurado
✅ Estrutura de pastas criada

⏳ Próximo: Converter managers ES6 → TypeScript hooks

## Como Continuar

Escolhe uma destas opções:

**Opção A: Converter todos os managers agora**
- Vou criar todos os hooks TypeScript
- Vou criar o APIClient em TypeScript
- Timeline: ~2 horas

**Opção B: Implementar uma feature completa**
- Criar Dashboard funcional
- Upload de vídeo
- Análise de vídeo
- Ver resultado
- Timeline: ~1 hora

**Opção C: Setup incremental**
- Criar só o APIClient primeiro
- Testar conexão com backend
- Depois criar hooks conforme necessário
- Timeline: ~30 minutos

**Recomendação:** Opção C (incremental) é mais seguro e permite testar a cada passo.

---

**Próximo comando sugerido:**
```bash
cd frontend
npm run dev
```

Isso vai iniciar o servidor de desenvolvimento Vite em http://localhost:5173
