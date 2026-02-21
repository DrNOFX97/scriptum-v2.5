/**
 * Sistema Inteligente de Detecção de Idiomas
 * Suporta ISO 639-1 (2 letras), ISO 639-2/T e ISO 639-2/B (3 letras)
 * Detecção automática de variantes linguísticas
 */

class LanguageDetector {
    constructor() {
        // Mapa de normalização ISO 639-1 (2 letras) → ISO 639-2 (3 letras)
        this.iso2to3 = {
            // Principais idiomas
            'en': 'eng', 'pt': 'por', 'es': 'spa', 'fr': 'fra', 'de': 'ger',
            'it': 'ita', 'ja': 'jpn', 'zh': 'chi', 'ko': 'kor', 'ru': 'rus',
            'ar': 'ara', 'hi': 'hin', 'tr': 'tur', 'he': 'heb', 'th': 'tha',
            'vi': 'vie', 'id': 'ind', 'cs': 'cze', 'el': 'gre', 'hu': 'hun',

            // Europa Ocidental
            'nl': 'dut', 'sv': 'swe', 'no': 'nor', 'da': 'dan', 'fi': 'fin',
            'is': 'ice', 'ga': 'gle', 'cy': 'wel', 'gd': 'gla',

            // Europa Central e Oriental
            'pl': 'pol', 'sk': 'slo', 'ro': 'rum', 'bg': 'bul', 'hr': 'hrv',
            'sr': 'srp', 'sl': 'slv', 'mk': 'mac', 'sq': 'alb', 'bs': 'bos',

            // Ex-URSS
            'uk': 'ukr', 'be': 'bel', 'kk': 'kaz', 'uz': 'uzb', 'hy': 'arm',
            'az': 'aze', 'ka': 'geo', 'et': 'est', 'lv': 'lav', 'lt': 'lit',

            // Médio Oriente
            'fa': 'per', 'ur': 'urd', 'ku': 'kur',

            // Ásia do Sul
            'bn': 'ben', 'pa': 'pan', 'ta': 'tam', 'te': 'tel', 'ml': 'mal',
            'mr': 'mar', 'gu': 'guj', 'kn': 'kan', 'si': 'sin', 'ne': 'nep',

            // Sudeste Asiático
            'ms': 'may', 'tl': 'tgl', 'my': 'bur', 'km': 'khm', 'lo': 'lao',

            // Leste Asiático
            'mn': 'mon',

            // África
            'sw': 'swa', 'am': 'amh', 'ha': 'hau', 'yo': 'yor', 'ig': 'ibo',
            'zu': 'zul', 'xh': 'xho', 'af': 'afr', 'so': 'som',

            // Outros
            'ca': 'cat', 'eu': 'baq', 'gl': 'glg', 'eo': 'epo'
        };

        // Mapa de variações ISO 639-2/B → ISO 639-2/T
        this.iso3variants = {
            'fre': 'fra', 'ger': 'deu', 'dut': 'nld', 'ice': 'isl',
            'wel': 'cym', 'cze': 'ces', 'slo': 'slk', 'rum': 'ron',
            'mac': 'mkd', 'alb': 'sqi', 'gre': 'ell', 'arm': 'hye',
            'geo': 'kat', 'per': 'fas', 'may': 'msa', 'bur': 'mya',
            'baq': 'eus', 'chi': 'zho'
        };

        // Definição única de idiomas (código normalizado → dados)
        this.languages = {
            // Principais idiomas com variantes
            'eng': { name: 'Inglês', flag: '🇬🇧', variants: { 'US': '🇺🇸', 'GB': '🇬🇧' }},
            'por': { name: 'Português', flag: '🇵🇹', variants: { 'BR': '🇧🇷', 'PT': '🇵🇹' }},
            'spa': { name: 'Espanhol', flag: '🇪🇸', variants: { 'LATAM': '🇲🇽', 'ES': '🇪🇸' }},
            'fra': { name: 'Francês', flag: '🇫🇷', variants: { 'CA': '🇨🇦', 'FR': '🇫🇷' }},
            'chi': { name: 'Chinês', flag: '🇨🇳', variants: { 'SIMP': '🇨🇳', 'TRAD': '🇹🇼' }},

            // Europa Ocidental
            'ger': { name: 'Alemão', flag: '🇩🇪' },
            'ita': { name: 'Italiano', flag: '🇮🇹' },
            'dut': { name: 'Holandês', flag: '🇳🇱' },
            'swe': { name: 'Sueco', flag: '🇸🇪' },
            'nor': { name: 'Norueguês', flag: '🇳🇴' },
            'dan': { name: 'Dinamarquês', flag: '🇩🇰' },
            'fin': { name: 'Finlandês', flag: '🇫🇮' },
            'ice': { name: 'Islandês', flag: '🇮🇸' },
            'gle': { name: 'Irlandês', flag: '🇮🇪' },
            'wel': { name: 'Galês', flag: '🏴󠁧󠁢󠁷󠁬󠁳󠁿' },
            'gla': { name: 'Gaélico Escocês', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿' },

            // Europa Central e Oriental
            'pol': { name: 'Polaco', flag: '🇵🇱' },
            'cze': { name: 'Checo', flag: '🇨🇿' },
            'ces': { name: 'Checo', flag: '🇨🇿' },
            'slo': { name: 'Eslovaco', flag: '🇸🇰' },
            'slk': { name: 'Eslovaco', flag: '🇸🇰' },
            'hun': { name: 'Húngaro', flag: '🇭🇺' },
            'rum': { name: 'Romeno', flag: '🇷🇴' },
            'ron': { name: 'Romeno', flag: '🇷🇴' },
            'bul': { name: 'Búlgaro', flag: '🇧🇬' },
            'hrv': { name: 'Croata', flag: '🇭🇷' },
            'srp': { name: 'Sérvio', flag: '🇷🇸' },
            'slv': { name: 'Esloveno', flag: '🇸🇮' },
            'mac': { name: 'Macedónio', flag: '🇲🇰' },
            'alb': { name: 'Albanês', flag: '🇦🇱' },
            'bos': { name: 'Bósnio', flag: '🇧🇦' },
            'gre': { name: 'Grego', flag: '🇬🇷' },

            // Ex-URSS
            'rus': { name: 'Russo', flag: '🇷🇺' },
            'ukr': { name: 'Ucraniano', flag: '🇺🇦' },
            'bel': { name: 'Bielorrusso', flag: '🇧🇾' },
            'kaz': { name: 'Cazaque', flag: '🇰🇿' },
            'uzb': { name: 'Uzbeque', flag: '🇺🇿' },
            'arm': { name: 'Arménio', flag: '🇦🇲' },
            'aze': { name: 'Azerbaijano', flag: '🇦🇿' },
            'geo': { name: 'Georgiano', flag: '🇬🇪' },
            'est': { name: 'Estónio', flag: '🇪🇪' },
            'lav': { name: 'Letão', flag: '🇱🇻' },
            'lit': { name: 'Lituano', flag: '🇱🇹' },

            // Médio Oriente
            'ara': { name: 'Árabe', flag: '🇸🇦' },
            'heb': { name: 'Hebraico', flag: '🇮🇱' },
            'per': { name: 'Persa', flag: '🇮🇷' },
            'urd': { name: 'Urdu', flag: '🇵🇰' },
            'kur': { name: 'Curdo', flag: '🇮🇶' },
            'tur': { name: 'Turco', flag: '🇹🇷' },

            // Ásia do Sul
            'hin': { name: 'Hindi', flag: '🇮🇳' },
            'ben': { name: 'Bengali', flag: '🇧🇩' },
            'pan': { name: 'Punjabi', flag: '🇮🇳' },
            'tam': { name: 'Tâmil', flag: '🇮🇳' },
            'tel': { name: 'Telugu', flag: '🇮🇳' },
            'mal': { name: 'Malaiala', flag: '🇮🇳' },
            'mar': { name: 'Marata', flag: '🇮🇳' },
            'guj': { name: 'Guzerate', flag: '🇮🇳' },
            'kan': { name: 'Canarês', flag: '🇮🇳' },
            'sin': { name: 'Cingalês', flag: '🇱🇰' },
            'nep': { name: 'Nepalês', flag: '🇳🇵' },

            // Sudeste Asiático
            'tha': { name: 'Tailandês', flag: '🇹🇭' },
            'vie': { name: 'Vietnamita', flag: '🇻🇳' },
            'ind': { name: 'Indonésio', flag: '🇮🇩' },
            'may': { name: 'Malaio', flag: '🇲🇾' },
            'tgl': { name: 'Tagalo', flag: '🇵🇭' },
            'bur': { name: 'Birmanês', flag: '🇲🇲' },
            'khm': { name: 'Khmer', flag: '🇰🇭' },
            'lao': { name: 'Laosiano', flag: '🇱🇦' },

            // Leste Asiático
            'jpn': { name: 'Japonês', flag: '🇯🇵' },
            'kor': { name: 'Coreano', flag: '🇰🇷' },
            'mon': { name: 'Mongol', flag: '🇲🇳' },

            // África
            'swa': { name: 'Suaíli', flag: '🇰🇪' },
            'amh': { name: 'Amárico', flag: '🇪🇹' },
            'hau': { name: 'Hauçá', flag: '🇳🇬' },
            'yor': { name: 'Iorubá', flag: '🇳🇬' },
            'ibo': { name: 'Igbo', flag: '🇳🇬' },
            'zul': { name: 'Zulu', flag: '🇿🇦' },
            'xho': { name: 'Xhosa', flag: '🇿🇦' },
            'afr': { name: 'Africânder', flag: '🇿🇦' },
            'som': { name: 'Somali', flag: '🇸🇴' },

            // Outros
            'cat': { name: 'Catalão', flag: '🇪🇸' },
            'baq': { name: 'Basco', flag: '🏴' },
            'glg': { name: 'Galego', flag: '🇪🇸' },
            'epo': { name: 'Esperanto', flag: '🌍' },

            // Desconhecido
            'und': { name: 'Desconhecido', flag: '🏳️' }
        };

        // Palavras-chave para detecção de variantes
        this.variantKeywords = {
            'por': {
                'BR': ['brazil', 'brazilian', 'brasil', 'pt-br', 'ptbr'],
                'PT': ['portugal', 'european', 'pt-pt', 'ptpt']
            },
            'eng': {
                'US': ['us', 'american'],
                'GB': ['uk', 'british']
            },
            'spa': {
                'LATAM': ['latin', 'latam', 'latino', 'mx', 'mexico'],
                'ES': ['spain', 'castellano', 'españa']
            },
            'fra': {
                'CA': ['canada', 'canadian', 'québec', 'quebec'],
                'FR': ['france']
            },
            'chi': {
                'TRAD': ['traditional', 'hant', 'tw', 'hk'],
                'SIMP': ['simplified', 'hans', 'cn']
            }
        };

        // Nomes de variantes em português
        this.variantNames = {
            'BR': '(Brasil)',
            'PT': '(Portugal)',
            'US': '(EUA)',
            'GB': '(Reino Unido)',
            'LATAM': '(Latam)',
            'ES': '(Espanha)',
            'CA': '(Canadá)',
            'FR': '(França)',
            'TRAD': '(Tradicional)',
            'SIMP': '(Simplificado)'
        };
    }

    /**
     * Normaliza código de idioma para ISO 639-2/T (3 letras)
     */
    normalizeLanguageCode(code) {
        if (!code) return 'und';

        const normalized = code.toLowerCase();

        // Se for código de 2 letras, converter para 3
        if (normalized.length === 2 && this.iso2to3[normalized]) {
            return this.iso2to3[normalized];
        }

        // Se for variante ISO 639-2/B, converter para /T
        if (normalized.length === 3 && this.iso3variants[normalized]) {
            return this.iso3variants[normalized];
        }

        return normalized;
    }

    /**
     * Detecta variante linguística pelo nome da track
     */
    detectVariant(langCode, trackName) {
        if (!trackName || !this.variantKeywords[langCode]) {
            return null;
        }

        const name = trackName.toLowerCase();
        const keywords = this.variantKeywords[langCode];

        for (const [variant, terms] of Object.entries(keywords)) {
            if (terms.some(term => name.includes(term))) {
                return variant;
            }
        }

        return null;
    }

    /**
     * Detecta informação completa do idioma
     */
    detectLanguageInfo(track) {
        const langCode = (track.language || 'und').toLowerCase();
        const trackName = track.name || '';

        const normalizedCode = this.normalizeLanguageCode(langCode);
        const variant = this.detectVariant(normalizedCode, trackName);

        return { code: normalizedCode, variant: variant };
    }

    /**
     * Retorna emoji da bandeira apropriada
     */
    getLanguageFlag(langCode, track = null) {
        let variant = null;

        if (track) {
            const info = this.detectLanguageInfo(track);
            langCode = info.code;
            variant = info.variant;
        } else {
            langCode = this.normalizeLanguageCode(langCode);
        }

        const lang = this.languages[langCode];
        if (!lang) return '🏳️';

        // Se tiver variante e o idioma suportar variantes
        if (variant && lang.variants && lang.variants[variant]) {
            return lang.variants[variant];
        }

        return lang.flag;
    }

    /**
     * Retorna nome do idioma em português
     */
    getLanguageName(langCode, track = null) {
        let variant = null;

        if (track) {
            const info = this.detectLanguageInfo(track);
            langCode = info.code;
            variant = info.variant;
        } else {
            langCode = this.normalizeLanguageCode(langCode);
        }

        const lang = this.languages[langCode];
        let baseName = lang ? lang.name : langCode.toUpperCase();

        // Adicionar variante ao nome
        if (variant && this.variantNames[variant]) {
            baseName += ' ' + this.variantNames[variant];
        }

        return baseName;
    }

    /**
     * Retorna informação completa formatada
     */
    getLanguageDisplay(track) {
        const info = this.detectLanguageInfo(track);
        const flag = this.getLanguageFlag(info.code, track);
        const name = this.getLanguageName(info.code, track);

        return {
            code: info.code,
            variant: info.variant,
            flag: flag,
            name: name,
            display: `${flag} ${name}`
        };
    }
}

// Criar instância global
window.languageDetector = new LanguageDetector();
