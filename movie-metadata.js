/**
 * Movie Metadata Module - Gerencia metadados de filmes e glossário
 */

class MovieMetadataManager {
    constructor() {
        this.metadata = null;
        this.glossary = {};
        this.context = '';
        this.initialized = false;

        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        console.log('🔧 Inicializando elementos...');

        // Card elements
        this.card = document.getElementById('movieMetadataCard');
        this.poster = document.getElementById('moviePoster');
        this.title = document.getElementById('movieTitle');
        this.rating = document.getElementById('movieRating');
        this.year = document.getElementById('movieYear');
        this.runtime = document.getElementById('movieRuntime');
        this.genres = document.getElementById('movieGenres');
        this.overview = document.getElementById('movieOverview');

        // Cast section
        this.castSection = document.getElementById('movieCastSection');
        this.castList = document.getElementById('movieCast');

        // Glossary
        this.glossaryPreview = document.getElementById('glossaryPreview');
        this.glossaryCount = document.getElementById('glossaryCount');
        this.glossaryTerms = document.getElementById('glossaryTerms');

        // Options
        this.preserveNamesCheckbox = document.getElementById('preserveCharacterNames');
        this.useContextCheckbox = document.getElementById('useMovieContext');

        // Verificar TODOS os elementos críticos
        const criticalElements = {
            'movieMetadataCard': this.card,
            'moviePoster': this.poster,
            'movieTitle': this.title,
            'movieRating': this.rating,
            'movieYear': this.year,
            'movieRuntime': this.runtime,
            'movieGenres': this.genres,
            'movieOverview': this.overview
        };

        let allFound = true;
        for (const [name, element] of Object.entries(criticalElements)) {
            if (!element) {
                console.error(`❌ ${name} NÃO encontrado!`);
                allFound = false;
            } else {
                console.log(`✅ ${name} encontrado`);
            }
        }

        if (allFound) {
            console.log('✅✅✅ TODOS os elementos encontrados com sucesso!');
        } else {
            console.error('❌❌❌ ALGUNS elementos NÃO foram encontrados!');
        }
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshMetadataBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refresh());
        }

        // View glossary button
        const viewGlossaryBtn = document.getElementById('viewGlossaryBtn');
        if (viewGlossaryBtn) {
            viewGlossaryBtn.addEventListener('click', () => {
                this.glossaryTerms.classList.toggle('hidden');
            });
        }
    }

    /**
     * Detecta informações do filme a partir do nome do ficheiro
     */
    detectFromFilename(filename) {
        console.log('🎬 Detectando filme do filename:', filename);

        // Remover extensão
        let name = filename.replace(/\.srt$/i, '');

        // Padrões de detecção
        const patterns = {
            // Nome.Ano.qualidade.srt
            yearPattern: /(.+?)[.\s]+(\d{4})/,
            // Nome.S01E01 (série)
            seriesPattern: /(.+?)[.\s]+S(\d{2})E(\d{2})/i
        };

        let info = {
            title: name,
            year: null,
            isSeries: false
        };

        // Tentar detectar ano
        const yearMatch = name.match(patterns.yearPattern);
        if (yearMatch) {
            info.title = yearMatch[1].replace(/[._]/g, ' ').trim();
            info.year = parseInt(yearMatch[2]);
        }

        // Tentar detectar série
        const seriesMatch = name.match(patterns.seriesPattern);
        if (seriesMatch) {
            info.title = seriesMatch[1].replace(/[._]/g, ' ').trim();
            info.isSeries = true;
        }

        // Limpar título
        info.title = this.cleanTitle(info.title);

        console.log('   Detectado:', info);
        return info;
    }

    cleanTitle(title) {
        // Remover marcadores de qualidade
        const qualityMarkers = ['1080p', '720p', '480p', '4k', 'bluray', 'webrip', 'web-dl', 'hdtv'];
        let cleaned = title;

        qualityMarkers.forEach(marker => {
            cleaned = cleaned.replace(new RegExp(marker, 'gi'), '');
        });

        // Remover múltiplos espaços
        cleaned = cleaned.replace(/\s+/g, ' ').trim();

        // Title case
        cleaned = cleaned.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');

        return cleaned;
    }

    /**
     * Carrega metadados do filme do TMDB (via backend Python)
     */
    async loadMetadata(filename) {
        console.log('🔍 Carregando metadados para:', filename);

        try {
            // Fetch metadados do backend Python
            const response = await fetch(`http://localhost:8080/api/metadata?filename=${encodeURIComponent(filename)}`);

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            const result = await response.json();
            console.log('📦 Dados recebidos do TMDB:', result);

            if (result.metadata) {
                // Converter formato do backend para formato do frontend
                this.metadata = {
                    title: result.metadata.title,
                    year: result.metadata.year,
                    rating: result.metadata.rating,
                    runtime: result.metadata.runtime,
                    genres: result.metadata.genres || [],
                    overview: result.metadata.overview,
                    poster: result.metadata.poster_path,
                    cast: result.metadata.cast.map(person => ({
                        character: person.character,
                        actor: person.name
                    }))
                };

                console.log('✅ Metadados convertidos:', this.metadata);

                // Usar glossário do backend
                this.glossary = result.glossary || {};
                this.context = result.context || '';

                this.render();
                return true;
            }

            throw new Error('Metadados não encontrados na resposta');

        } catch (error) {
            console.error('❌ Erro ao carregar metadados:', error);
            this.showError(error.message);
            return false;
        }
    }

    showError(message) {
        // Mostrar erro no card
        if (this.card) {
            this.card.innerHTML = `
                <div class="metadata-header">
                    <h3>⚠️ Erro ao Carregar Metadados</h3>
                </div>
                <div style="padding: 20px; text-align: center;">
                    <p>${message}</p>
                    <p style="font-size: 0.9em; color: #666; margin-top: 10px;">
                        Verifique se o servidor Python está a correr em http://localhost:8080
                    </p>
                </div>
            `;
            this.card.classList.remove('hidden');
        }
    }


    render() {
        if (!this.metadata) {
            console.log('⚠️ Sem metadados para renderizar');
            this.card.classList.add('hidden');
            return;
        }

        console.log('🎨 Renderizando card de metadados...');

        // Mostrar card SEMPRE (mesmo sem todos os dados)
        this.card.classList.remove('hidden');

        // Título
        this.title.textContent = this.metadata.title;

        // Rating
        if (this.metadata.rating) {
            this.rating.textContent = `⭐ ${this.metadata.rating}/10`;
        } else {
            this.rating.textContent = '⭐ -';
        }

        // Ano
        if (this.metadata.year) {
            this.year.textContent = `📅 ${this.metadata.year}`;
        } else {
            this.year.textContent = '📅 -';
        }

        // Runtime
        if (this.metadata.runtime) {
            this.runtime.textContent = `⏱️ ${this.metadata.runtime} min`;
        } else {
            this.runtime.textContent = '⏱️ -';
        }

        // Géneros
        this.genres.innerHTML = '';
        if (this.metadata.genres && this.metadata.genres.length > 0) {
            this.metadata.genres.forEach(genre => {
                const tag = document.createElement('span');
                tag.className = 'genre-tag';
                tag.textContent = genre;
                this.genres.appendChild(tag);
            });
        }

        // Sinopse
        this.overview.textContent = this.metadata.overview || 'Sinopse não disponível.';

        // Poster
        if (this.metadata.poster) {
            this.poster.src = this.metadata.poster;
            this.poster.onload = () => this.poster.classList.add('loaded');
        }

        // Elenco
        if (this.metadata.cast && this.metadata.cast.length > 0) {
            this.castSection.classList.remove('hidden');
            this.castList.innerHTML = '';

            this.metadata.cast.slice(0, 6).forEach(person => {
                const item = document.createElement('div');
                item.className = 'cast-item';
                item.innerHTML = `
                    <div>
                        <div class="character">${person.character}</div>
                        <div class="actor">${person.actor}</div>
                    </div>
                `;
                this.castList.appendChild(item);
            });
        } else {
            this.castSection.classList.add('hidden');
        }

        // Glossário
        const glossarySize = Object.keys(this.glossary).length;
        if (glossarySize > 0) {
            this.glossaryPreview.classList.remove('hidden');
            this.glossaryCount.textContent = glossarySize;

            // Renderizar termos
            this.glossaryTerms.innerHTML = '';
            Object.keys(this.glossary).forEach(term => {
                const termEl = document.createElement('span');
                termEl.className = 'glossary-term';
                termEl.textContent = term;
                this.glossaryTerms.appendChild(termEl);
            });
        } else {
            this.glossaryPreview.classList.add('hidden');
        }

        this.initialized = true;
    }

    refresh() {
        console.log('🔄 Recarregando metadados...');
        // Implementar refresh se necessário
    }

    getTranslationConfig() {
        return {
            preserveNames: this.preserveNamesCheckbox?.checked ?? true,
            useContext: this.useContextCheckbox?.checked ?? true,
            glossary: this.preserveNamesCheckbox?.checked ? this.glossary : {},
            context: this.useContextCheckbox?.checked ? this.context : ''
        };
    }

    isInitialized() {
        return this.initialized && this.metadata !== null;
    }
}

// Instância global
let movieMetadataManager = null;

function initMovieMetadata() {
    if (!movieMetadataManager) {
        movieMetadataManager = new MovieMetadataManager();
    }
    return movieMetadataManager;
}
