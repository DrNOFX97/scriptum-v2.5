/**
 * MKV Subtitle Extractor - Interface para extração de legendas
 */

class MKVExtractorUI {
    constructor() {
        this.tracks = [];
        this.selectedTracks = new Set();
        this.currentMkvFile = null;
        this.mkvFilePath = null;

        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        // File input
        this.fileInput = document.getElementById('srtFile'); // Usar o input principal
        this.fileNameDisplay = document.getElementById('mkvFileName');

        // Tracks list
        this.tracksContainer = document.getElementById('subtitleTracksList');
        this.tracksCard = document.getElementById('subtitleTracksCard');

        // Buttons
        this.analyzeBtn = document.getElementById('analyzeMkvBtn');
        this.extractBtn = document.getElementById('extractSubtitlesBtn');
        this.selectAllBtn = document.getElementById('selectAllTracksBtn');
        this.deselectAllBtn = document.getElementById('deselectAllTracksBtn');

        // Progress
        this.extractProgress = document.getElementById('extractionProgress');
        this.extractedList = document.getElementById('extractedSubtitlesList');

        console.log('🔧 MKV Extractor elementos inicializados');
    }

    setupEventListeners() {
        // Analyze button
        if (this.analyzeBtn) {
            this.analyzeBtn.addEventListener('click', () => this.analyzeMkvFile());
            console.log('✅ Analyze button listener attached');
        }

        // Extract button
        if (this.extractBtn) {
            this.extractBtn.addEventListener('click', () => this.extractSelectedTracks());
        }

        // Select/Deselect all
        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', () => this.selectAllTracks());
        }

        if (this.deselectAllBtn) {
            this.deselectAllBtn.addEventListener('click', () => this.deselectAllTracks());
        }
    }


    async analyzeMkvFile() {
        // Pedir ao usuário para colar o caminho completo do ficheiro
        const filePath = prompt(
            '🎬 Cole o caminho completo do ficheiro MKV:\n\n' +
            'Exemplo: /Users/nome/Downloads/filme.mkv',
            this.currentMkvFile ? this.currentMkvFile.name : ''
        );

        if (!filePath || filePath.trim() === '') {
            alert('Caminho do ficheiro não fornecido!');
            return;
        }

        console.log('🔍 Analisando ficheiro MKV:', filePath);

        try {
            // Enviar apenas o caminho do ficheiro
            const response = await fetch('http://localhost:8080/api/mkv/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: filePath.trim() })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Erro HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            console.log('📦 Tracks recebidas:', result);

            if (result.tracks && result.tracks.length > 0) {
                this.tracks = result.tracks;
                this.mkvFilePath = result.file_path; // Guardar caminho para extração
                this.renderTracks();
            } else {
                alert('Nenhuma track de legendas encontrada neste ficheiro!');
            }

        } catch (error) {
            console.error('❌ Erro ao analisar MKV:', error);
            alert(`Erro ao analisar ficheiro: ${error.message}`);
        }
    }

    renderTracks() {
        console.log('🎨 Renderizando tracks de legendas...');

        this.tracksContainer.innerHTML = '';
        this.selectedTracks.clear();

        if (this.tracks.length === 0) {
            this.tracksCard.classList.add('hidden');
            return;
        }

        this.tracksCard.classList.remove('hidden');

        // Criar item para cada track
        this.tracks.forEach(track => {
            const trackItem = this.createTrackItem(track);
            this.tracksContainer.appendChild(trackItem);

            // Selecionar por defeito se for a track padrão
            if (track.is_default) {
                this.selectedTracks.add(track.id);
                trackItem.querySelector('input[type="checkbox"]').checked = true;
            }
        });

        // Atualizar contador
        this.updateSelectionCount();
    }

    createTrackItem(track) {
        const item = document.createElement('div');
        item.className = 'track-item';

        // Detectar idioma usando o sistema centralizado
        const langDisplay = window.languageDetector.getLanguageDisplay(track);
        const flagEmoji = langDisplay.flag;
        const languageName = langDisplay.name;

        // Default marker
        const defaultMarker = track.is_default ? '<span class="default-badge">Padrão</span>' : '';

        // Forced marker (para legendas obrigatórias, ex: sinais, alien text, etc)
        const forcedMarker = track.name && track.name.toLowerCase().includes('forced')
            ? '<span class="forced-badge">Forçada</span>' : '';

        // SDH/CC marker (para legendas para surdos)
        const sdhMarker = track.name && (
            track.name.toLowerCase().includes('sdh') ||
            track.name.toLowerCase().includes('cc') ||
            track.name.toLowerCase().includes('deaf')
        ) ? '<span class="sdh-badge">SDH</span>' : '';

        item.innerHTML = `
            <label class="track-label">
                <input type="checkbox"
                       data-track-id="${track.id}"
                       class="track-checkbox">
                <div class="track-info">
                    <div class="track-header">
                        <span class="track-language">${flagEmoji} ${languageName}</span>
                        <span class="track-codec">${track.codec}</span>
                        ${defaultMarker}
                        ${forcedMarker}
                        ${sdhMarker}
                    </div>
                    ${track.name ? `<div class="track-name">${track.name}</div>` : ''}
                    <div class="track-id">Track ID: ${track.id}</div>
                </div>
            </label>
        `;

        // Listener para checkbox
        const checkbox = item.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedTracks.add(track.id);
            } else {
                this.selectedTracks.delete(track.id);
            }
            this.updateSelectionCount();
        });

        return item;
    }


    selectAllTracks() {
        this.tracks.forEach(track => {
            this.selectedTracks.add(track.id);
        });

        document.querySelectorAll('.track-checkbox').forEach(cb => {
            cb.checked = true;
        });

        this.updateSelectionCount();
    }

    deselectAllTracks() {
        this.selectedTracks.clear();

        document.querySelectorAll('.track-checkbox').forEach(cb => {
            cb.checked = false;
        });

        this.updateSelectionCount();
    }

    updateSelectionCount() {
        const count = this.selectedTracks.size;
        const total = this.tracks.length;

        if (this.extractBtn) {
            this.extractBtn.textContent = `Extrair ${count} Track${count !== 1 ? 's' : ''}`;
            this.extractBtn.disabled = count === 0;
        }

        console.log(`📊 Selecionadas: ${count}/${total} tracks`);
    }

    async extractSelectedTracks() {
        if (this.selectedTracks.size === 0) {
            alert('Por favor selecione pelo menos uma track!');
            return;
        }

        if (!this.mkvFilePath) {
            alert('Caminho do ficheiro MKV não encontrado!');
            return;
        }

        console.log('🚀 Extraindo tracks selecionadas:', Array.from(this.selectedTracks));

        this.extractProgress.classList.remove('hidden');

        try {
            // Enviar caminho do ficheiro e track IDs
            const response = await fetch('http://localhost:8080/api/mkv/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_path: this.mkvFilePath,
                    track_ids: Array.from(this.selectedTracks)
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Erro HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            console.log('✅ Extração concluída:', result);

            this.showExtractedFiles(result.extracted_files);

            // Perguntar sobre tradução
            this.promptTranslation(result.extracted_files);

        } catch (error) {
            console.error('❌ Erro ao extrair tracks:', error);
            alert(`Erro na extração: ${error.message}`);
        } finally {
            this.extractProgress.classList.add('hidden');
        }
    }

    showExtractedFiles(files) {
        this.extractedList.innerHTML = '';

        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'extracted-file-item';
            item.innerHTML = `
                <span class="file-icon">📄</span>
                <span class="file-path">${file.path}</span>
                <span class="file-size">${this.formatFileSize(file.size)}</span>
            `;
            this.extractedList.appendChild(item);
        });
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    async promptTranslation(extractedFiles) {
        // Criar modal de confirmação
        const proceed = confirm(
            `✅ ${extractedFiles.length} ficheiro(s) extraído(s) com sucesso!\n\n` +
            `Deseja traduzir estas legendas agora?`
        );

        if (proceed) {
            console.log('🔄 Iniciando tradução...');

            // Carregar primeira legenda na interface principal
            if (extractedFiles.length > 0) {
                const firstFile = extractedFiles[0];

                // Encontrar a track correspondente para obter info de idioma
                const trackId = firstFile.track_id;
                const track = this.tracks.find(t => t.id === trackId);

                // Detectar idioma da track
                let sourceLanguage = 'Inglês';
                let sourceLanguageCode = 'eng';

                if (track) {
                    const langDisplay = window.languageDetector.getLanguageDisplay(track);
                    sourceLanguage = langDisplay.name;
                    sourceLanguageCode = langDisplay.code;
                    console.log(`🌍 Idioma detectado: ${sourceLanguage} (${sourceLanguageCode})`);
                }

                // Ler o ficheiro extraído
                try {
                    const response = await fetch(`http://localhost:8080/api/file?path=${encodeURIComponent(firstFile.path)}`);
                    const content = await response.text();

                    // Criar um objeto File simulado
                    const blob = new Blob([content], { type: 'text/plain' });
                    const originalMkvName = this.currentMkvFile ? this.currentMkvFile.name.replace('.mkv', '') : 'subtitle';
                    const langCode = sourceLanguageCode.substring(0, 2).toUpperCase();
                    const file = new File([blob], `${originalMkvName}_${langCode}.srt`, { type: 'text/plain' });

                    // Trigger evento para carregar no tradutor com o ficheiro E info de idioma
                    const event = new CustomEvent('loadSubtitleFile', {
                        detail: {
                            file: file,
                            content: content,
                            sourceLanguage: sourceLanguage,
                            sourceLanguageCode: sourceLanguageCode
                        }
                    });
                    document.dispatchEvent(event);

                    // Fechar painel de extração e mostrar área de upload
                    this.tracksCard.classList.add('hidden');
                    const mkvSection = document.getElementById('mkvExtractorSection');
                    if (mkvSection) {
                        mkvSection.classList.add('hidden');
                    }
                    const uploadArea = document.querySelector('.upload-area');
                    if (uploadArea) {
                        uploadArea.classList.remove('hidden');
                    }

                } catch (error) {
                    console.error('❌ Erro ao carregar ficheiro:', error);
                    alert('Erro ao carregar ficheiro para tradução. Tente fazer download manual.');
                }
            }
        } else {
            console.log('💾 Preparando download das legendas...');

            // Oferecer download dos ficheiros
            this.offerDownload(extractedFiles);
        }
    }

    offerDownload(extractedFiles) {
        // Criar interface de download
        const downloadSection = document.createElement('div');
        downloadSection.className = 'download-section';
        downloadSection.style.cssText = `
            margin-top: 20px;
            padding: 20px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 10px;
        `;

        const originalMkvName = this.currentMkvFile ? this.currentMkvFile.name.replace('.mkv', '') : 'subtitle';

        downloadSection.innerHTML = `
            <h4 style="margin-top: 0; color: #10b981;">💾 Guardar Legendas</h4>
            <p style="margin-bottom: 15px;">Escolha onde guardar as legendas extraídas:</p>
        `;

        extractedFiles.forEach((file, index) => {
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-secondary';
            downloadBtn.style.cssText = 'margin: 5px; width: 100%;';

            const suggestedName = index === 0
                ? `${originalMkvName}_EN.srt`
                : `${originalMkvName}_EN_track${file.track_id || index+1}.srt`;

            downloadBtn.innerHTML = `📥 Guardar como: ${suggestedName}`;
            downloadBtn.onclick = () => this.downloadFile(file.path, suggestedName);

            downloadSection.appendChild(downloadBtn);
        });

        // Adicionar à lista de ficheiros extraídos
        this.extractedList.appendChild(downloadSection);
    }

    async downloadFile(filePath, suggestedName) {
        try {
            // Buscar conteúdo do ficheiro
            const response = await fetch(`http://localhost:8080/api/file?path=${encodeURIComponent(filePath)}`);
            const content = await response.text();

            // Criar blob e download
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = suggestedName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            console.log(`✅ Download iniciado: ${suggestedName}`);
        } catch (error) {
            console.error('❌ Erro no download:', error);
            alert('Erro ao fazer download do ficheiro.');
        }
    }
}

// Instância global
let mkvExtractorUI = null;

function initMKVExtractor() {
    if (!mkvExtractorUI) {
        mkvExtractorUI = new MKVExtractorUI();
    }
    return mkvExtractorUI;
}
