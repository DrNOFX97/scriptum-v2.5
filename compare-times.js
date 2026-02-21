/**
 * Script para comparar timeframes entre original e traduzido
 */

const fs = require('fs');

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
}

// Ler ficheiros
const originalFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt';
const translatedFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt';

console.log('📖 A ler e comparar ficheiros...\n');

const originalContent = fs.readFileSync(originalFile, 'utf8');
const translatedContent = fs.readFileSync(translatedFile, 'utf8');

const originalSubs = SRTParser.parse(originalContent);
const translatedSubs = SRTParser.parse(translatedContent);

console.log(`Original: ${originalSubs.length} legendas`);
console.log(`Traduzido: ${translatedSubs.length} legendas\n`);

// Criar mapa de traduções por ID
const translatedMap = new Map();
translatedSubs.forEach(sub => {
    translatedMap.set(sub.id, sub);
});

// Comparar timeframes
let mismatches = [];
let correct = 0;

for (const origSub of originalSubs) {
    const transSub = translatedMap.get(origSub.id);

    if (!transSub) {
        mismatches.push({
            id: origSub.id,
            issue: 'MISSING',
            original: origSub.timeframe,
            translated: 'N/A'
        });
    } else if (origSub.timeframe !== transSub.timeframe) {
        mismatches.push({
            id: origSub.id,
            issue: 'TIMEFRAME_MISMATCH',
            original: origSub.timeframe,
            translated: transSub.timeframe,
            originalText: origSub.text.substring(0, 60),
            translatedText: transSub.text.substring(0, 60)
        });
    } else {
        correct++;
    }
}

console.log(`✅ Timeframes corretos: ${correct}`);
console.log(`❌ Timeframes diferentes: ${mismatches.length}\n`);

if (mismatches.length > 0) {
    console.log('🔍 Primeiros 10 problemas encontrados:\n');
    mismatches.slice(0, 10).forEach((mismatch, index) => {
        console.log(`${index + 1}. ID ${mismatch.id} - ${mismatch.issue}`);
        console.log(`   Original:  ${mismatch.original}`);
        console.log(`   Traduzido: ${mismatch.translated}`);
        if (mismatch.originalText) {
            console.log(`   Texto orig: "${mismatch.originalText}"`);
            console.log(`   Texto trad: "${mismatch.translatedText}"`);
        }
        console.log('');
    });

    if (mismatches.length > 10) {
        console.log(`... e mais ${mismatches.length - 10} problemas\n`);
    }

    // Estatísticas
    const missing = mismatches.filter(m => m.issue === 'MISSING').length;
    const timeframeDiff = mismatches.filter(m => m.issue === 'TIMEFRAME_MISMATCH').length;

    console.log('📊 Resumo dos problemas:');
    console.log(`   Legendas em falta: ${missing}`);
    console.log(`   Timeframes diferentes: ${timeframeDiff}`);
} else {
    console.log('🎉 Todos os timeframes estão corretos!');
}
