/**
 * Retomar tradução a partir de onde parou
 */

const fs = require('fs');

// API Key do Gemini
const GEMINI_API_KEY = 'AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c';
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';

// Parser SRT
class SRTParser {
    static parse(srtContent) {
        const subtitles = [];
        const blocks = srtContent.trim().split(/\n\s*\n/);

        for (const block of blocks) {
            const lines = block.trim().split('\n');
            if (lines.length < 3) continue;

            const id = lines[0].trim();
            const timeframe = lines[1].trim();
            const text = lines.slice(2).join('\n').trim();

            if (this.isValidTimeframe(timeframe)) {
                subtitles.push({ id, timeframe, text });
            }
        }

        return subtitles;
    }

    static isValidTimeframe(timeframe) {
        const pattern = /^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}$/;
        return pattern.test(timeframe);
    }

    static generate(subtitles) {
        let srtContent = '';
        for (const subtitle of subtitles) {
            srtContent += `${subtitle.id}\n${subtitle.timeframe}\n${subtitle.text}\n\n`;
        }
        return srtContent.trim();
    }

    static extractTexts(subtitles) {
        return subtitles.map(sub => sub.text);
    }

    static updateTexts(subtitles, translatedTexts) {
        return subtitles.map((subtitle, index) => ({
            id: subtitle.id,
            timeframe: subtitle.timeframe,
            text: translatedTexts[index]
        }));
    }
}

// Tradutor Gemini com retry
class GeminiTranslator {
    constructor(apiKey) {
        this.apiKey = apiKey;
    }

    async translateBatch(texts, startIndex = 0, progressCallback = null) {
        const translatedTexts = [];
        const batchSize = 10;
        const totalBatches = Math.ceil(texts.length / batchSize);

        for (let i = startIndex; i < texts.length; i += batchSize) {
            const batch = texts.slice(i, i + batchSize);
            const currentBatch = Math.floor(i / batchSize) + 1;

            if (progressCallback) {
                progressCallback({
                    current: i,
                    total: texts.length,
                    batch: currentBatch,
                    totalBatches: totalBatches,
                    percentage: Math.round((i / texts.length) * 100)
                });
            }

            let retries = 0;
            let success = false;
            let translatedBatch = [];

            // Retry até 3 vezes se falhar
            while (!success && retries < 3) {
                try {
                    translatedBatch = await this.translateTexts(batch);
                    success = true;
                } catch (error) {
                    retries++;
                    console.log(`   ⚠️  Erro no lote ${currentBatch}, tentativa ${retries}/3...`);
                    if (retries < 3) {
                        await new Promise(resolve => setTimeout(resolve, 2000)); // Esperar 2s antes de retry
                    } else {
                        throw error; // Se falhar 3 vezes, lançar erro
                    }
                }
            }

            translatedTexts.push(...translatedBatch);

            // Pequena pausa entre batches
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        return translatedTexts;
    }

    async translateTexts(texts) {
        const prompt = this.buildPrompt(texts);

        const response = await fetch(`${GEMINI_API_URL}?key=${this.apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }] }],
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
            throw new Error(`Erro da API: ${errorData.error?.message || response.statusText}`);
        }

        const data = await response.json();
        const translatedText = data.candidates[0].content.parts[0].text;

        return this.parseTranslation(translatedText, texts.length);
    }

    buildPrompt(texts) {
        const numberedTexts = texts.map((text, index) => `${index + 1}. ${text}`).join('\n');

        return `Traduza as seguintes legendas de INGLÊS para PORTUGUÊS DE PORTUGAL (PT-PT).

CONTEXTO: Filme de animação "Zootopia" (em Portugal: "Zootrópolis")

REGRAS IMPORTANTES:
- Use português de Portugal (PT-PT), não brasileiro
- Use SEMPRE a segunda pessoa (tu/você) nas falas, nunca a terceira pessoa
- Linguagem adequada para desenhos animados (clara, direta, expressiva)
- "Zootopia" deve ser traduzido como "Zootrópolis"
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
- Tom adequado para filme familiar/infantil
- Não exceda 2 linhas por legenda

LEGENDAS A TRADUZIR:
${numberedTexts}

TRADUÇÕES (mantenha a numeração):`;
    }

    parseTranslation(translatedText, expectedCount) {
        const translations = [];

        // Dividir por blocos numerados (suporta texto multi-linha)
        const blocks = translatedText.split(/\n(?=\d+\.\s)/);

        for (const block of blocks) {
            const match = block.match(/^\d+\.\s*(.+)$/s);
            if (match) {
                const text = match[1].trim();
                translations.push(text);
            }
        }

        return translations;
    }
}

// Função principal
async function resumeTranslation() {
    console.log('🔄 Retomar tradução do Zootopia 2\n');

    try {
        // Ler ficheiro original
        const originalFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt';
        const oldTranslationFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FULL.srt';
        const outputFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt';

        console.log('📖 A ler ficheiros...');
        const originalContent = fs.readFileSync(originalFile, 'utf8');
        const oldTranslationContent = fs.readFileSync(oldTranslationFile, 'utf8');

        // Parse
        const originalSubs = SRTParser.parse(originalContent);
        const oldTranslatedSubs = SRTParser.parse(oldTranslationContent);

        console.log(`✅ Original: ${originalSubs.length} legendas`);
        console.log(`✅ Tradução antiga: ${oldTranslatedSubs.length} legendas\n`);

        // Parou no lote 121, que é o índice 1200 (121 * 10 - 10)
        const startIndex = 1200;

        console.log(`🌐 Retomando tradução a partir da legenda ${startIndex + 1}...\n`);

        // Pegar textos originais
        const texts = SRTParser.extractTexts(originalSubs);

        // Pegar traduções já feitas
        const alreadyTranslated = SRTParser.extractTexts(oldTranslatedSubs).slice(0, startIndex);

        console.log(`✅ Já traduzidas: ${alreadyTranslated.length} legendas`);
        console.log(`⏳ Faltam: ${texts.length - startIndex} legendas\n`);

        // Traduzir o resto
        const translator = new GeminiTranslator(GEMINI_API_KEY);
        const remainingTranslations = await translator.translateBatch(
            texts.slice(startIndex),
            0,
            (progress) => {
                const actualIndex = startIndex + progress.current;
                const actualBatch = Math.floor(actualIndex / 10) + 1;
                const totalBatches = Math.ceil(texts.length / 10);
                console.log(`   Lote ${actualBatch}/${totalBatches} (${Math.round((actualIndex / texts.length) * 100)}%)`);
            }
        );

        // Combinar traduções antigas com novas
        const allTranslations = [...alreadyTranslated, ...remainingTranslations];

        console.log(`\n✅ Total de traduções: ${allTranslations.length} de ${originalSubs.length} legendas`);

        // Atualizar
        const translatedSubtitles = SRTParser.updateTexts(originalSubs, allTranslations);
        const translatedContent = SRTParser.generate(translatedSubtitles);

        // Guardar
        console.log('\n💾 A guardar ficheiro traduzido...');
        fs.writeFileSync(outputFile, translatedContent, 'utf8');

        if (fs.existsSync(outputFile)) {
            const stats = fs.statSync(outputFile);
            console.log(`✅ Ficheiro criado com sucesso (${stats.size} bytes)`);
        }

        console.log('✅ Tradução concluída!\n');
        console.log(`🎉 Ficheiro guardado em: ${outputFile}`);

    } catch (error) {
        console.error('❌ Erro:', error.message);
        process.exit(1);
    }
}

resumeTranslation();
