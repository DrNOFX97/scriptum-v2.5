/**
 * Script de teste para traduzir legendas usando Node.js
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

// Tradutor Gemini
class GeminiTranslator {
    constructor(apiKey) {
        this.apiKey = apiKey;
    }

    async translateBatch(texts, progressCallback = null) {
        const translatedTexts = [];
        const batchSize = 10;
        const totalBatches = Math.ceil(texts.length / batchSize);

        for (let i = 0; i < texts.length; i += batchSize) {
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

            const translatedBatch = await this.translateTexts(batch);
            translatedTexts.push(...translatedBatch);

            // Pequena pausa entre batches
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        return translatedTexts;
    }

    async translateTexts(texts) {
        const prompt = this.buildPrompt(texts);

        try {
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

        } catch (error) {
            throw new Error(`Falha na tradução: ${error.message}`);
        }
    }

    buildPrompt(texts) {
        const numberedTexts = texts.map((text, index) => `${index + 1}. ${text}`).join('\n');

        return `Traduza as seguintes legendas de INGLÊS para PORTUGUÊS DE PORTUGAL (PT-PT).

REGRAS IMPORTANTES:
- Use português de Portugal (PT-PT), não brasileiro
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
async function translateSubtitles(inputPath, outputPath) {
    console.log('🎬 Tradutor de Legendas SRT - EN para PT-PT\n');

    try {
        // Ler ficheiro
        console.log('📖 A ler ficheiro:', inputPath);
        const content = fs.readFileSync(inputPath, 'utf8');

        // Parse
        console.log('🔍 A analisar legendas...');
        const subtitles = SRTParser.parse(content);
        console.log(`✅ ${subtitles.length} legendas encontradas\n`);

        // Mostrar primeiras 3 legendas
        console.log('📝 Primeiras legendas:');
        subtitles.slice(0, 3).forEach(sub => {
            console.log(`[${sub.id}] ${sub.timeframe}`);
            console.log(`   ${sub.text}\n`);
        });

        // Traduzir TODAS as legendas
        const texts = SRTParser.extractTexts(subtitles);

        console.log(`🌐 A traduzir ${subtitles.length} legendas...\n`);

        const translator = new GeminiTranslator(GEMINI_API_KEY);
        const translatedTexts = await translator.translateBatch(texts, (progress) => {
            console.log(`   Lote ${progress.batch}/${progress.totalBatches} (${progress.percentage}%)`);
        });

        // Validar número de traduções
        console.log(`\n✅ Recebidas ${translatedTexts.length} traduções de ${subtitles.length} legendas`);

        if (translatedTexts.length !== subtitles.length) {
            console.error(`⚠️  AVISO: Número de traduções (${translatedTexts.length}) diferente do número de legendas (${subtitles.length})`);
            console.error('Isto pode causar legendas com timeframes incorretos!');
        }

        // Atualizar
        const translatedSubtitles = SRTParser.updateTexts(subtitles, translatedTexts);
        const translatedContent = SRTParser.generate(translatedSubtitles);

        // Guardar
        console.log('\n💾 A guardar ficheiro traduzido...');
        fs.writeFileSync(outputPath, translatedContent, 'utf8');

        // Verificar se ficheiro foi criado
        if (fs.existsSync(outputPath)) {
            const stats = fs.statSync(outputPath);
            console.log(`✅ Ficheiro criado com sucesso (${stats.size} bytes)`);
        } else {
            throw new Error('Ficheiro não foi criado!');
        }

        console.log('✅ Tradução concluída!\n');
        console.log('📝 Primeiras legendas traduzidas:');
        translatedSubtitles.slice(0, 3).forEach(sub => {
            console.log(`[${sub.id}] ${sub.timeframe}`);
            console.log(`   ${sub.text}\n`);
        });

        console.log(`\n🎉 Ficheiro guardado em: ${outputPath}`);

    } catch (error) {
        console.error('❌ Erro:', error.message);
        process.exit(1);
    }
}

// Executar
const inputFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt';
const outputFile = '/Users/f.nuno/projetos/subtitle-translator/Zootopia2_PT-PT_FULL.srt';

translateSubtitles(inputFile, outputFile);
