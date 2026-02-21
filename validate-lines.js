/**
 * Script para validar regras de linhas nas legendas traduzidas
 */

const fs = require('fs');

const MAX_LINE_LENGTH = 42;
const TAG_RE = /<[^>]+>/g;
const LITERAL_BREAK_RE = /(\\n|\/n)/gi;
const SPACED_ELLIPSES_RE = /\.\s+\.\s+\./g;
const DIALOGUE_DASH_RE = /^\s*[-–—]/;

function visibleLength(text) {
    return text.replace(TAG_RE, '').length;
}

function normalizeLine(line) {
    return line
        .replace(LITERAL_BREAK_RE, ' ')
        .replace(SPACED_ELLIPSES_RE, '...')
        .replace(/\s+/g, ' ')
        .trim();
}

function isDialogue(text) {
    if (!text) return false;
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    const dashLines = lines.filter(l => DIALOGUE_DASH_RE.test(l)).length;
    return dashLines >= 2;
}

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

console.log('📖 A ler e validar conteúdo das legendas...\n');

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

// Comparar número de linhas dentro de cada legenda
let lineRuleViolations = [];
let tooManyLines = [];
let literalBreaks = [];
let spacedEllipses = [];
let dialogueLineIssues = [];
let emptyTranslations = [];
let correct = 0;

for (const origSub of originalSubs) {
    const transSub = translatedMap.get(origSub.id);

    if (!transSub) {
        continue;
    }

    const transText = transSub.text || '';
    const origIsDialogue = isDialogue(origSub.text);
    const lines = transText.split('\n');
    const transLines = lines.length;
    const normalized = normalizeLine(transText.replace(/\n/g, ' '));

    // Verificar se tradução está vazia ou muito curta
    if (transText.trim().length < 2) {
        emptyTranslations.push({
            id: origSub.id,
            originalText: origSub.text,
            translatedText: transText
        });
    }

    if (LITERAL_BREAK_RE.test(transText)) {
        literalBreaks.push({ id: origSub.id, translatedText: transText });
    }

    if (SPACED_ELLIPSES_RE.test(transText)) {
        spacedEllipses.push({ id: origSub.id, translatedText: transText });
    }

    if (transLines > 2) {
        tooManyLines.push({ id: origSub.id, translatedText: transText });
    }

    if (origIsDialogue && transLines !== 2) {
        dialogueLineIssues.push({ id: origSub.id, translatedText: transText });
    }

    const normalizedLen = visibleLength(normalized);
    if (!origIsDialogue && transLines === 2 && normalizedLen <= MAX_LINE_LENGTH) {
        lineRuleViolations.push({ id: origSub.id, translatedText: transText });
    }

    if (!origIsDialogue && transLines === 1 && normalizedLen > MAX_LINE_LENGTH) {
        lineRuleViolations.push({ id: origSub.id, translatedText: transText });
    }

    if (
        transText.trim().length >= 2 &&
        !LITERAL_BREAK_RE.test(transText) &&
        !SPACED_ELLIPSES_RE.test(transText) &&
        transLines <= 2 &&
        (!origIsDialogue || transLines === 2) &&
        !(transLines === 2 && normalizedLen <= MAX_LINE_LENGTH) &&
        !(transLines === 1 && normalizedLen > MAX_LINE_LENGTH)
    ) {
        correct++;
    }
}

console.log(`✅ Legendas com número de linhas correto: ${correct}`);
console.log(`⚠️  Legendas com regras de linha violadas: ${lineRuleViolations.length}`);
console.log(`⚠️  Legendas com mais de 2 linhas: ${tooManyLines.length}`);
console.log(`⚠️  Legendas com \\n ou /n literais: ${literalBreaks.length}`);
console.log(`⚠️  Legendas com reticências espaçadas: ${spacedEllipses.length}`);
console.log(`⚠️  Diálogos sem 2 linhas: ${dialogueLineIssues.length}`);
console.log(`❌ Traduções vazias ou inválidas: ${emptyTranslations.length}\n`);

// Mostrar traduções vazias
if (emptyTranslations.length > 0) {
    console.log('🚨 TRADUÇÕES VAZIAS/INVÁLIDAS:\n');
    emptyTranslations.slice(0, 10).forEach((issue, index) => {
        console.log(`${index + 1}. ID ${issue.id}`);
        console.log(`   Original: "${issue.originalText}"`);
        console.log(`   Traduzido: "${issue.translatedText}"`);
        console.log('');
    });

    if (emptyTranslations.length > 10) {
        console.log(`... e mais ${emptyTranslations.length - 10} traduções vazias\n`);
    }
}

// Mostrar diferenças no número de linhas
if (lineRuleViolations.length > 0) {
    console.log('⚠️  VIOLAÇÕES DE REGRAS DE LINHA:\n');
    lineRuleViolations.slice(0, 10).forEach((issue, index) => {
        console.log(`${index + 1}. ID ${issue.id}`);
        console.log(`   Traduzido:`);
        console.log(`   ${issue.translatedText.split('\n').map(l => `     "${l}"`).join('\n   ')}`);
        console.log('');
    });

    if (lineRuleViolations.length > 10) {
        console.log(`... e mais ${lineRuleViolations.length - 10} violações\n`);
    }
}

if (
    emptyTranslations.length === 0 &&
    lineRuleViolations.length === 0 &&
    tooManyLines.length === 0 &&
    literalBreaks.length === 0 &&
    spacedEllipses.length === 0 &&
    dialogueLineIssues.length === 0
) {
    console.log('🎉 Todas as legendas cumprem as regras de linhas!');
}
