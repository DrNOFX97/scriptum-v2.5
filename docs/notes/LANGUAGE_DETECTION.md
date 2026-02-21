# 🌍 Sistema Inteligente de Detecção de Idiomas

## Visão Geral

O **Scriptum** possui um sistema avançado de detecção de idiomas e variantes linguísticas para legendas MKV, suportando:

- **Códigos ISO 639-1** (2 letras): `en`, `pt`, `es`, `fr`, etc.
- **Códigos ISO 639-2** (3 letras): `eng`, `por`, `spa`, `fra`, etc.
- **Detecção automática de variantes** pelo nome da track
- **+30 idiomas** com bandeiras apropriadas

## 🎯 Detecção de Variantes

### Português
- 🇵🇹 **PT-PT** (Portugal) - padrão se não especificado
- 🇧🇷 **PT-BR** (Brasil)

**Palavras-chave detectadas:**
- Brasil: `brazil`, `brazilian`, `brasil`, `pt-br`, `ptbr`
- Portugal: `portugal`, `european`, `pt-pt`, `ptpt`

**Exemplo:**
```
Track: "Portuguese (Brazilian)" → 🇧🇷 Português (Brasil)
Track: "Portuguese" → 🇵🇹 Português (Portugal)  [assumido por defeito]
```

### Inglês
- 🇬🇧 **UK** (Reino Unido) - padrão
- 🇺🇸 **US** (Estados Unidos)

**Palavras-chave detectadas:**
- US: `us`, `american`
- UK: `uk`, `british`

### Espanhol
- 🇪🇸 **ES** (Espanha) - padrão
- 🇲🇽 **LATAM** (Latinoamérica)

**Palavras-chave detectadas:**
- LATAM: `latin`, `latam`, `latino`, `mx`
- Espanha: `spain`, `castellano`, `españa`

### Francês
- 🇫🇷 **FR** (França) - padrão
- 🇨🇦 **CA** (Canadá)

**Palavras-chave detectadas:**
- Canadá: `canada`, `canadian`, `québec`, `quebec`

### Chinês
- 🇨🇳 **Simplificado** - padrão
- 🇹🇼 **Tradicional**

**Palavras-chave detectadas:**
- Tradicional: `traditional`, `hant`, `tw`, `hk`
- Simplificado: `simplified`, `hans`, `cn`

## 🏷️ Badges Inteligentes

### Padrão (Verde)
Indica que esta é a track padrão do ficheiro MKV.

```css
✅ Padrão
background: rgba(16, 185, 129, 0.2);
color: #10b981;
```

### Forçada (Amarelo)
Legendas obrigatórias para cenas específicas (ex: texto alien, sinais, idiomas estrangeiros dentro do filme).

```css
⚠️ Forçada
background: rgba(251, 191, 36, 0.2);
color: #fbbf24;
```

**Palavras-chave:** `forced`

### SDH (Azul)
Legendas para surdos e deficientes auditivos (incluem descrições sonoras).

```css
🔊 SDH
background: rgba(96, 165, 250, 0.2);
color: #60a5fa;
```

**Palavras-chave:** `sdh`, `cc`, `deaf`

## 📊 Idiomas Suportados

| Código 2 | Código 3 | Idioma | Bandeira |
|----------|----------|--------|----------|
| `en` | `eng` | Inglês | 🇬🇧 🇺🇸 |
| `pt` | `por` | Português | 🇵🇹 🇧🇷 |
| `es` | `spa` | Espanhol | 🇪🇸 🇲🇽 |
| `fr` | `fra` | Francês | 🇫🇷 🇨🇦 |
| `de` | `ger` | Alemão | 🇩🇪 |
| `it` | `ita` | Italiano | 🇮🇹 |
| `ja` | `jpn` | Japonês | 🇯🇵 |
| `zh` | `chi/zho` | Chinês | 🇨🇳 🇹🇼 |
| `ko` | `kor` | Coreano | 🇰🇷 |
| `ru` | `rus` | Russo | 🇷🇺 |
| `ar` | `ara` | Árabe | 🇸🇦 |
| `hi` | `hin` | Hindi | 🇮🇳 |
| `nl` | `dut` | Holandês | 🇳🇱 |
| `sv` | `swe` | Sueco | 🇸🇪 |
| `no` | `nor` | Norueguês | 🇳🇴 |
| `da` | `dan` | Dinamarquês | 🇩🇰 |
| `fi` | `fin` | Finlandês | 🇫🇮 |
| `pl` | `pol` | Polaco | 🇵🇱 |
| `tr` | `tur` | Turco | 🇹🇷 |
| `he` | `heb` | Hebraico | 🇮🇱 |
| `th` | `tha` | Tailandês | 🇹🇭 |
| `vi` | `vie` | Vietnamita | 🇻🇳 |
| `id` | `ind` | Indonésio | 🇮🇩 |
| `cs` | `cze` | Checo | 🇨🇿 |
| `el` | `gre` | Grego | 🇬🇷 |
| `hu` | `hun` | Húngaro | 🇭🇺 |
| `ro` | `rum` | Romeno | 🇷🇴 |
| `uk` | `ukr` | Ucraniano | 🇺🇦 |

## 🔍 Exemplos Reais

### Web-DL com múltiplas tracks

```json
{
  "tracks": [
    {
      "id": 2,
      "codec": "SubRip/SRT",
      "language": "eng",
      "name": "English (Forced)",
      "is_default": false
    },
    {
      "id": 3,
      "codec": "SubRip/SRT",
      "language": "eng",
      "name": "English",
      "is_default": true
    },
    {
      "id": 4,
      "codec": "SubRip/SRT",
      "language": "eng",
      "name": "English (SDH)",
      "is_default": false
    },
    {
      "id": 5,
      "codec": "SubRip/SRT",
      "language": "por",
      "name": "Portuguese (Brazilian)",
      "is_default": false
    }
  ]
}
```

**Renderização:**

```
┌─────────────────────────────────────────────────┐
│ 📋 Tracks de Legendas Disponíveis              │
├─────────────────────────────────────────────────┤
│ ☐ 🇬🇧 Inglês             SRT  ⚠️ Forçada       │
│   English (Forced)                              │
│   Track ID: 2                                   │
├─────────────────────────────────────────────────┤
│ ☑ 🇬🇧 Inglês             SRT  ✅ Padrão         │
│   English                                       │
│   Track ID: 3                                   │
├─────────────────────────────────────────────────┤
│ ☐ 🇬🇧 Inglês             SRT  🔊 SDH            │
│   English (SDH)                                 │
│   Track ID: 4                                   │
├─────────────────────────────────────────────────┤
│ ☐ 🇧🇷 Português (Brasil) SRT                    │
│   Portuguese (Brazilian)                        │
│   Track ID: 5                                   │
└─────────────────────────────────────────────────┘
```

## 🧪 Testes

Para testar a detecção de idiomas, use tracks com nomes variados:

```javascript
const testTracks = [
    { language: 'en', name: 'English' },              // 🇬🇧
    { language: 'eng', name: 'English (US)' },        // 🇺🇸
    { language: 'pt', name: 'Portuguese' },           // 🇵🇹 (padrão)
    { language: 'por', name: 'Portuguese (Brazilian)'}, // 🇧🇷
    { language: 'es', name: 'Spanish (LATAM)' },      // 🇲🇽
    { language: 'spa', name: 'Spanish' },             // 🇪🇸 (padrão)
    { language: 'zh', name: 'Chinese (Simplified)' }, // 🇨🇳
    { language: 'chi', name: 'Chinese (Traditional)'} // 🇹🇼
];
```

## 📝 Implementação

### Métodos Principais

**`detectLanguageInfo(track)`**
- Normaliza código de idioma (2→3 letras)
- Analisa nome da track para detectar variante
- Retorna `{ code: 'por', variant: 'BR' }`

**`normalizeLanguageCode(code)`**
- Converte códigos ISO 639-1 → ISO 639-2
- `'en'` → `'eng'`
- `'pt'` → `'por'`

**`getLanguageFlag(langCode, track)`**
- Retorna emoji de bandeira apropriado
- Considera variante se track fornecida
- Fallback: 🏳️ para idiomas desconhecidos

**`getLanguageName(langCode, track)`**
- Retorna nome em português
- Inclui variante no nome: `"Português (Brasil)"`
- Fallback: código em maiúsculas

## 🚀 Casos de Uso

### Caso 1: Web-DL Internacional
MKV de web-dl contém múltiplas legendas em inglês (forced, normal, SDH) + português brasileiro.

**Resultado:** Detecção automática de todas as variantes com bandeiras e badges corretos.

### Caso 2: Anime com Fansubs
MKV com legendas em inglês (código `en`) e japonês (código `ja`).

**Resultado:** Converte `en` → `eng`, mostra 🇬🇧 Inglês e 🇯🇵 Japonês.

### Caso 3: Filme Europeu
MKV com português de Portugal sem especificação explícita.

**Resultado:** Assume PT-PT por defeito, mostra 🇵🇹 Português.

## 🎨 Contribuir

Para adicionar um novo idioma:

1. Adicionar mapeamento em `normalizeLanguageCode()` se for código de 2 letras
2. Adicionar bandeira em `getLanguageFlag()`
3. Adicionar nome em português em `getLanguageName()`
4. Opcionalmente, adicionar detecção de variante em `detectLanguageInfo()`

---

**Versão:** 2.1.0
**Data:** 2026-01-30
**Autor:** Claude Code + User
