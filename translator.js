/**
 * Gemini Translator - Traduz textos usando a API do Google Gemini
 */

const MAX_LINE_LENGTH = 42;
const TAG_RE = /<[^>]+>/g;
const LITERAL_BREAK_RE = /(\\n|\/n)/gi;
const SPACED_ELLIPSES_RE = /\.\s+\.\s+\./g;
const MULTI_SPACE_RE = /[ \t]{2,}/g;
const DIALOGUE_DASH_RE = /^\s*[-–—]/;

class GeminiTranslator {
    constructor(apiKey, config = {}) {
        this.apiKey = apiKey;
        this.apiUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';

        // Configuração opcional com metadados do filme
        this.config = {
            glossary: config.glossary || {},
            context: config.context || '',
            preserveNames: config.preserveNames !== false,
            useContext: config.useContext !== false,
            sourceLanguage: config.sourceLanguage || 'Inglês', // Idioma de origem (padrão: Inglês)
            sourceLanguageCode: config.sourceLanguageCode || 'eng' // Código ISO do idioma de origem
        };
    }

    /**
     * Traduz um array de textos de EN para PT-PT em lotes
     * @param {Array} texts - Array de textos a traduzir
     * @param {Function} progressCallback - Callback para progresso (opcional)
     * @param {Array} originalSubtitles - Array de objetos de legendas originais (opcional, para correção de linha)
     * @returns {Promise<Array>} Array de textos traduzidos
     */
    async translateBatch(texts, progressCallback = null, originalSubtitles = null) {
        const translatedTexts = [];
        const batchSize = 10; // Traduzir 10 legendas de cada vez para evitar timeouts
        const totalBatches = Math.ceil(texts.length / batchSize);

        for (let i = 0; i < texts.length; i += batchSize) {
            const batch = texts.slice(i, i + batchSize);
            const currentBatch = Math.floor(i / batchSize) + 1;

            // Traduzir o lote
            const translatedBatch = await this.translateTexts(batch);
            translatedTexts.push(...translatedBatch);

            // Callback APENAS após cada lote concluído
            if (progressCallback) {
                progressCallback({
                    current: i + batch.length,
                    total: texts.length,
                    batch: currentBatch,
                    totalBatches: totalBatches,
                    percentage: Math.round(((i + batch.length) / texts.length) * 100),
                    translatedTexts: translatedTexts,
                    justCompleted: translatedBatch // Textos recém traduzidos deste lote
                });
            }
        }

        // Aplicar regras de linha se tivermos as legendas originais
        if (originalSubtitles && originalSubtitles.length === texts.length) {
            console.log('🔧 A aplicar regras de linha...');
            const fixedTexts = this.fixLineBreaks(originalSubtitles, translatedTexts);
            return fixedTexts;
        }

        return translatedTexts;
    }

    /**
     * Traduz um lote de textos
     * @param {Array} texts - Textos a traduzir
     * @returns {Promise<Array>} Textos traduzidos
     */
    async translateTexts(texts) {
        const prompt = this.buildPrompt(texts);

        try {
            const response = await fetch(`${this.apiUrl}?key=${this.apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: prompt
                        }]
                    }],
                    generationConfig: {
                        temperature: 0.3,
                        topK: 40,
                        topP: 0.95,
                        maxOutputTokens: 8192,
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Erro da API Gemini: ${errorData.error?.message || response.statusText}`);
            }

            const data = await response.json();
            const translatedText = data.candidates[0].content.parts[0].text;

            return this.parseTranslation(translatedText, texts.length);

        } catch (error) {
            console.error('Erro na tradução:', error);
            throw new Error(`Falha na tradução: ${error.message}`);
        }
    }

    /**
     * Constrói o prompt para a API Gemini
     * @param {Array} texts - Textos a traduzir
     * @returns {string} Prompt formatado
     */
    buildPrompt(texts) {
        const numberedTexts = texts.map((text, index) => `${index + 1}. ${text}`).join('\n');

        // Construir contexto dinâmico
        let contextSection = '';
        if (this.config.useContext && this.config.context) {
            contextSection = `\nCONTEXTO DO FILME:\n${this.config.context}\n`;
        }

        // Construir seção de glossário
        let glossarySection = '';
        if (this.config.preserveNames && Object.keys(this.config.glossary).length > 0) {
            const terms = Object.keys(this.config.glossary).slice(0, 20).join(', '); // Limitar a 20 termos
            glossarySection = `\n🎭 NOMES DE PERSONAGENS A PRESERVAR:\n${terms}\nIMPORTANTE: Mantenha estes nomes EXATAMENTE como estão, NÃO os traduza.\n`;
        }

        const sourceLang = this.config.sourceLanguage.toUpperCase();

        return `Traduza as seguintes legendas de ${sourceLang} para PORTUGUÊS DE PORTUGAL (PT-PT).
${contextSection}${glossarySection}
REGRAS IMPORTANTES:
- Use português de Portugal (PT-PT), não brasileiro
- Use SEMPRE a segunda pessoa (tu/você) nas falas, nunca a terceira pessoa
- Máximo de 2 linhas por legenda
- Usa 1 linha sempre que o texto couber numa única linha
- Usa 2 linhas apenas quando o texto for longo, equilibrando as duas linhas
- Diálogos com dois locutores ficam sempre em 2 linhas, cada linha começando por "-"
- Não uses "\\n" ou "/n" literais; usa quebras reais apenas quando necessário
- Reticências sempre juntas: "..." (nunca ".  .  .")
- Preserve tags HTML se existirem (como <i>, <b>, etc.)
- Mantenha a numeração exata
- Não adicione comentários ou explicações
- Retorne apenas as traduções numeradas
- Não exceda 2 linhas por legenda

LEGENDAS A TRADUZIR (${sourceLang}):
${numberedTexts}

TRADUÇÕES EM PT-PT (mantenha a numeração):`;
    }

    /**
     * Parse a resposta da tradução com correção inteligente
     * @param {string} translatedText - Texto traduzido pela API
     * @param {number} expectedCount - Número esperado de traduções
     * @returns {Array} Array de traduções
     */
    parseTranslation(translatedText, expectedCount) {
        let translations = [];

        // Dividir por blocos numerados (suporta texto multi-linha)
        // Match padrão: "1. texto que pode
        //                continuar em várias linhas
        //                2. próximo texto"
        const blocks = translatedText.split(/\n(?=\d+\.\s)/);

        for (const block of blocks) {
            const match = block.match(/^\d+\.\s*(.+)$/s);
            if (match) {
                // Remover o número e limpar espaços extras
                const text = match[1].trim();
                translations.push(text);
            }
        }

        // Validar se obtivemos todas as traduções
        if (translations.length !== expectedCount) {
            console.warn(`⚠️ Parse: Esperado ${expectedCount} traduções, obtido ${translations.length}`);

            // Se temos mais traduções que o esperado, tentar corrigir
            if (translations.length > expectedCount) {
                console.log('🔧 Excesso de traduções - tentando agrupar...');
                // Pode ser que algumas legendas tenham sido divididas
                // O corretor de linha vai arrumar depois
                translations = this.mergeExtraTranslations(translations, expectedCount);
            }

            // Se faltarem traduções, tentar parse alternativo
            if (translations.length < expectedCount && translations.length === 0) {
                console.log('🔧 Fallback: parse alternativo');
                // Fallback: dividir por linhas não vazias
                translations = translatedText
                    .split('\n')
                    .filter(line => line.trim() && !line.match(/^TRADUÇÕES/i))
                    .slice(0, expectedCount);
            }

            // Se ainda faltarem traduções após fallback, preencher com placeholders
            if (translations.length < expectedCount) {
                console.warn(`⚠️ Faltam ${expectedCount - translations.length} traduções - usando originais como fallback`);
            }
        }

        return translations;
    }

    /**
     * Tenta agrupar traduções extras que foram divididas incorretamente
     * @param {Array} translations - Array de traduções parseadas
     * @param {number} expectedCount - Número esperado
     * @returns {Array} Array corrigido
     */
    mergeExtraTranslations(translations, expectedCount) {
        if (translations.length <= expectedCount) {
            return translations;
        }

        const merged = [];
        const excess = translations.length - expectedCount;

        // Estratégia: juntar as últimas 'excess' traduções com as anteriores
        for (let i = 0; i < expectedCount; i++) {
            if (i < expectedCount - excess) {
                // Primeiras N-excess: manter como estão
                merged.push(translations[i]);
            } else {
                // Últimas 'excess': juntar 2 em 1
                const idx = i + (i - (expectedCount - excess));
                const text1 = translations[idx] || '';
                const text2 = translations[idx + 1] || '';
                merged.push(text1 + '\n' + text2);
            }
        }

        console.log(`✅ Agrupadas ${translations.length} traduções em ${merged.length}`);
        return merged.slice(0, expectedCount);
    }

    /**
     * Valida a chave da API
     * @returns {Promise<boolean>}
     */
    async validateApiKey() {
        try {
            const response = await fetch(`${this.apiUrl}?key=${this.apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: 'test'
                        }]
                    }]
                })
            });

            return response.ok || response.status === 400; // 400 = bad request mas key válida
        } catch (error) {
            return false;
        }
    }

    /**
     * Corrige quebras de linha nas traduções (porta do algoritmo Python robusto)
     * @param {Array} originalSubtitles - Array de objetos de legendas originais com propriedade .text
     * @param {Array} translatedTexts - Array de textos traduzidos
     * @returns {Array} Array de textos corrigidos
     */
    fixLineBreaks(originalSubtitles, translatedTexts) {
        const fixed = [];
        let correctionCount = 0;
        let fallbackCount = 0;

        // Verificar se há diferença no tamanho dos arrays
        if (translatedTexts.length !== originalSubtitles.length) {
            console.warn(`⚠️ Tamanhos diferentes: ${originalSubtitles.length} originais vs ${translatedTexts.length} traduções`);
        }

        for (let i = 0; i < originalSubtitles.length; i++) {
            const originalText = originalSubtitles[i].text;

            // Se não houver tradução correspondente, usar original
            if (i >= translatedTexts.length || !translatedTexts[i]) {
                console.warn(`⚠️ Sem tradução para #${i + 1}, usando original`);
                fixed.push(originalText);
                fallbackCount++;
                continue;
            }

            const translatedText = translatedTexts[i];
            const formatted = this.formatSubtitleText(originalText, translatedText);

            if (formatted !== translatedText) {
                correctionCount++;
                if (correctionCount <= 5) {
                    console.log(`🔧 Ajustado #${i + 1} para regras de linha`);
                }
            }

            fixed.push(formatted);
        }

        if (correctionCount > 0) {
            console.log(`✅ Ajustadas ${correctionCount} legendas (${(correctionCount / originalSubtitles.length * 100).toFixed(1)}%)`);
        }

        if (fallbackCount > 0) {
            console.warn(`⚠️ ${fallbackCount} legendas usaram texto original por falta de tradução`);
        }

        if (correctionCount === 0 && fallbackCount === 0) {
            console.log('✅ Todas as traduções cumprem as regras de linha');
        }

        return fixed;
    }

    visibleLength(text) {
        return text.replace(TAG_RE, '').length;
    }

    normalizeLine(line) {
        return line
            .replace(LITERAL_BREAK_RE, ' ')
            .replace(SPACED_ELLIPSES_RE, '...')
            .replace(MULTI_SPACE_RE, ' ')
            .trim();
    }

    normalizeLines(text) {
        if (!text) return [];
        return text
            .split('\n')
            .map(line => this.normalizeLine(line))
            .filter(line => line.length > 0);
    }

    isDialogue(text) {
        if (!text) return false;
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
        const dashLines = lines.filter(l => DIALOGUE_DASH_RE.test(l)).length;
        return dashLines >= 2;
    }

    ensureDash(line) {
        if (!line) return line;
        if (DIALOGUE_DASH_RE.test(line)) return line;
        return `- ${line.trim()}`;
    }

    splitOnSecondDash(text) {
        if (!text) return ['', ''];
        const stripped = text.trim();
        if (!DIALOGUE_DASH_RE.test(stripped)) return ['', ''];

        const seps = [' - ', ' – ', ' — '];
        for (const sep of seps) {
            const idx = stripped.indexOf(sep, 2);
            if (idx !== -1) {
                const line1 = stripped.slice(0, idx).trim();
                let line2 = stripped.slice(idx + sep.length).trim();
                if (line2 && !DIALOGUE_DASH_RE.test(line2)) {
                    line2 = `- ${line2}`;
                }
                return [line1, line2];
            }
        }
        return ['', ''];
    }

    bestSplit(text) {
        const words = text.split(' ').filter(Boolean);
        if (words.length < 2) return [text, ''];

        let best = null;
        for (let i = 1; i < words.length; i++) {
            const l1 = words.slice(0, i).join(' ');
            const l2 = words.slice(i).join(' ');
            const v1 = this.visibleLength(l1);
            const v2 = this.visibleLength(l2);
            const bothFit = v1 <= MAX_LINE_LENGTH && v2 <= MAX_LINE_LENGTH;
            const score = [
                bothFit ? 0 : 1,
                Math.max(v1, v2),
                Math.abs(v1 - v2)
            ];

            if (!best || this.isBetterScore(score, best.score)) {
                best = { score, l1, l2 };
            }
        }

        if (!best) return [text, ''];
        return [best.l1, best.l2];
    }

    isBetterScore(a, b) {
        for (let i = 0; i < Math.max(a.length, b.length); i++) {
            const av = a[i] ?? 0;
            const bv = b[i] ?? 0;
            if (av < bv) return true;
            if (av > bv) return false;
        }
        return false;
    }

    formatDialogue(rawText, normalizedText) {
        const lines = this.normalizeLines(rawText);
        let line1 = '';
        let line2 = '';

        if (lines.length >= 2) {
            line1 = lines[0];
            line2 = lines.slice(1).join(' ').trim();
        } else {
            [line1, line2] = this.splitOnSecondDash(normalizedText);
            if (!line1 && !line2) {
                [line1, line2] = this.bestSplit(normalizedText);
            }
        }

        line1 = this.ensureDash(line1);
        line2 = this.ensureDash(line2);

        if (!line2) return line1;
        return `${line1}\n${line2}`;
    }

    formatNonDialogue(text) {
        if (this.visibleLength(text) <= MAX_LINE_LENGTH) {
            return text;
        }
        const [line1, line2] = this.bestSplit(text);
        if (!line2) return text;
        return `${line1}\n${line2}`;
    }

    formatSubtitleText(originalText, translatedText) {
        if (!translatedText) return '';

        const lines = this.normalizeLines(translatedText);
        let normalized = lines.join(' ').trim();
        normalized = normalized.replace(MULTI_SPACE_RE, ' ');

        if (!normalized) return '';

        if (this.isDialogue(originalText) || this.isDialogue(translatedText)) {
            return this.formatDialogue(translatedText, normalized);
        }

        return this.formatNonDialogue(normalized);
    }
}
