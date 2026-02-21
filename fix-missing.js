/**
 * Script para corrigir legendas que faltam na tradução
 */

const fs = require('fs');

// Parser SRT (mesmo do test.js)
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
}

// Ler ficheiros
const originalFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt';
const translatedFile = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FULL.srt';

console.log('📖 A ler ficheiros...\n');

const originalContent = fs.readFileSync(originalFile, 'utf8');
const translatedContent = fs.readFileSync(translatedFile, 'utf8');

const originalSubs = SRTParser.parse(originalContent);
const translatedSubs = SRTParser.parse(translatedContent);

console.log(`Original: ${originalSubs.length} legendas`);
console.log(`Traduzido: ${translatedSubs.length} legendas`);
console.log(`Diferença: ${originalSubs.length - translatedSubs.length} legendas em falta\n`);

// Comparar
const missing = [];
const translatedIds = new Set(translatedSubs.map(s => s.id));

for (const sub of originalSubs) {
    if (!translatedIds.has(sub.id)) {
        missing.push(sub);
    }
}

console.log(`❌ Legendas em falta: ${missing.length}\n`);

if (missing.length > 0) {
    console.log('IDs das legendas em falta:');
    missing.slice(0, 20).forEach(sub => {
        console.log(`  - ID ${sub.id}: ${sub.timeframe}`);
        console.log(`    "${sub.text.substring(0, 50)}..."`);
    });

    if (missing.length > 20) {
        console.log(`  ... e mais ${missing.length - 20} legendas`);
    }
}
