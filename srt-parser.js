/**
 * SRT Parser - Extrai e reconstrói legendas mantendo os timeframes
 */

class SRTParser {
    /**
     * Parse um ficheiro SRT para um array de objetos
     * @param {string} srtContent - Conteúdo do ficheiro SRT
     * @returns {Array} Array de objetos com id, timeframe e texto
     */
    static parse(srtContent) {
        const subtitles = [];
        const blocks = srtContent.trim().split(/\n\s*\n/);

        for (const block of blocks) {
            const lines = block.trim().split('\n');

            if (lines.length < 3) continue;

            const id = lines[0].trim();
            const timeframe = lines[1].trim();
            const text = lines.slice(2).join('\n').trim();

            // Validar formato do timeframe
            if (this.isValidTimeframe(timeframe)) {
                subtitles.push({
                    id: id,
                    timeframe: timeframe,
                    text: text
                });
            }
        }

        return subtitles;
    }

    /**
     * Valida se o timeframe está no formato correto
     * @param {string} timeframe - Timeframe a validar
     * @returns {boolean}
     */
    static isValidTimeframe(timeframe) {
        // Formato: 00:00:00,000 --> 00:00:00,000
        const pattern = /^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}$/;
        return pattern.test(timeframe);
    }

    /**
     * Gera um ficheiro SRT a partir de um array de legendas
     * @param {Array} subtitles - Array de objetos com id, timeframe e texto
     * @returns {string} Conteúdo do ficheiro SRT
     */
    static generate(subtitles) {
        let srtContent = '';

        for (const subtitle of subtitles) {
            srtContent += `${subtitle.id}\n`;
            srtContent += `${subtitle.timeframe}\n`;
            srtContent += `${subtitle.text}\n\n`;
        }

        return srtContent.trim();
    }

    /**
     * Extrai apenas os textos das legendas
     * @param {Array} subtitles - Array de legendas
     * @returns {Array} Array de textos
     */
    static extractTexts(subtitles) {
        return subtitles.map(sub => sub.text);
    }

    /**
     * Atualiza os textos das legendas mantendo timeframes
     * @param {Array} subtitles - Array original de legendas
     * @param {Array} translatedTexts - Array de textos traduzidos
     * @returns {Array} Array de legendas com textos atualizados
     */
    static updateTexts(subtitles, translatedTexts) {
        if (subtitles.length !== translatedTexts.length) {
            throw new Error('O número de legendas e traduções não coincide');
        }

        return subtitles.map((subtitle, index) => ({
            id: subtitle.id,
            timeframe: subtitle.timeframe,
            text: translatedTexts[index]
        }));
    }
}
