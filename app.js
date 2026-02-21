/**
 * Aplicação Principal - Tradutor de Legendas SRT
 */

// Estado da aplicação
const appState = {
    currentFile: null,
    originalContent: null,
    parsedSubtitles: null,
    translatedSubtitles: null,
    translatedContent: null,
    apiKey: 'AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c' // Pré-configurada para teste
};

// Elementos do DOM
const elements = {
    // Secções
    uploadSection: document.getElementById('uploadSection'),
    filePreviewSection: document.getElementById('filePreviewSection'),
    progressSection: document.getElementById('progressSection'),
    resultSection: document.getElementById('resultSection'),
    errorSection: document.getElementById('errorSection'),

    // Upload
    fileInput: document.getElementById('srtFile'),
    fileLabel: document.getElementById('fileLabel'),
    fileName: document.getElementById('fileName'),

    // File Preview
    fileNameDisplay: document.getElementById('fileNameDisplay'),
    fileSizeDisplay: document.getElementById('fileSizeDisplay'),
    subtitleCountDisplay: document.getElementById('subtitleCountDisplay'),
    originalPreview: document.getElementById('originalPreview'),
    startTranslationBtn: document.getElementById('startTranslationBtn'),
    changeFileBtn: document.getElementById('changeFileBtn'),

    // Progress
    progressFill: document.getElementById('progressFill'),
    progressPercentage: document.getElementById('progressPercentage'),
    batchInfo: document.getElementById('batchInfo'),
    subtitleInfo: document.getElementById('subtitleInfo'),
    statusInfo: document.getElementById('statusInfo'),
    liveTranslations: document.getElementById('liveTranslations'),

    // Result
    originalFileName: document.getElementById('originalFileName'),
    translatedCount: document.getElementById('translatedCount'),
    finalFileName: document.getElementById('finalFileName'),
    originalFinalPreview: document.getElementById('originalFinalPreview'),
    translatedPreview: document.getElementById('translatedPreview'),
    downloadBtn: document.getElementById('downloadBtn'),
    newTranslationBtn: document.getElementById('newTranslationBtn'),

    // Error
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),

    // Footer
    clearApiKeyBtn: document.getElementById('clearApiKeyBtn')
};

// Event Listeners
elements.fileInput.addEventListener('change', handleFileSelect);
elements.startTranslationBtn.addEventListener('click', startTranslation);
elements.changeFileBtn.addEventListener('click', resetToUpload);
elements.downloadBtn.addEventListener('click', downloadTranslatedFile);
elements.newTranslationBtn.addEventListener('click', resetToUpload);
elements.retryBtn.addEventListener('click', resetToUpload);
elements.clearApiKeyBtn.addEventListener('click', clearApiKey);

// Drag and Drop
elements.fileLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.fileLabel.classList.add('drag-over');
});

elements.fileLabel.addEventListener('dragleave', () => {
    elements.fileLabel.classList.remove('drag-over');
});

elements.fileLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.fileLabel.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        elements.fileInput.files = files;
        handleFileSelect({ target: elements.fileInput });
    }
});

/**
 * Manipula a seleção do ficheiro
 */
async function handleFileSelect(event) {
    console.log('🔄 handleFileSelect chamado');
    const file = event.target.files[0];

    if (!file) {
        console.log('⚠️ Nenhum ficheiro selecionado');
        return;
    }

    console.log('📁 Ficheiro:', file.name, 'Tipo:', file.type);
    const fileName = file.name.toLowerCase();

    // Verificar tipo de ficheiro
    if (fileName.endsWith('.mkv')) {
        console.log('✅ Detectado ficheiro MKV');
        // Ficheiro MKV - redirecionar para o extractor
        handleMKVFile(file);
        return;
    }

    // Validar extensão SRT
    if (!fileName.endsWith('.srt')) {
        showError('Por favor, selecione um ficheiro SRT ou MKV válido.');
        return;
    }

    appState.currentFile = file;

    try {
        // Ler ficheiro
        appState.originalContent = await readFile(file);

        // Parse
        appState.parsedSubtitles = SRTParser.parse(appState.originalContent);

        if (appState.parsedSubtitles.length === 0) {
            throw new Error('Nenhuma legenda encontrada no ficheiro. Verifique o formato SRT.');
        }

        // Mostrar preview
        showFilePreview();

    } catch (error) {
        showError(error.message);
    }
}

/**
 * Handle MKV file selection
 */
function handleMKVFile(file) {
    console.log('📦 Ficheiro MKV selecionado:', file.name);

    // Ocultar APENAS a área de upload (não toda a secção)
    const uploadArea = document.querySelector('.upload-area');
    console.log('Upload area:', uploadArea);

    if (uploadArea) {
        uploadArea.classList.add('hidden');
    }

    // Mostrar secção do extractor MKV
    const mkvSection = document.getElementById('mkvExtractorSection');
    const mkvFileName = document.getElementById('mkvFileName');

    console.log('MKV Section:', mkvSection);
    console.log('MKV FileName element:', mkvFileName);

    if (mkvSection && mkvFileName) {
        mkvFileName.textContent = file.name;
        mkvSection.classList.remove('hidden');
        console.log('✅ MKV section mostrada');
    } else {
        console.error('❌ Elementos MKV não encontrados!');
    }

    // Passar ficheiro para o MKV extractor
    if (window.mkvExtractorUI) {
        window.mkvExtractorUI.currentMkvFile = file;
        if (window.mkvExtractorUI.fileNameDisplay) {
            window.mkvExtractorUI.fileNameDisplay.textContent = file.name;
        }
        console.log('✅ Ficheiro passado para MKV extractor');
    } else {
        console.error('❌ mkvExtractorUI não inicializado!');
    }
}

/**
 * Mostra o preview do ficheiro carregado
 */
async function showFilePreview() {
    const file = appState.currentFile;
    const subtitles = appState.parsedSubtitles;

    // Informações do ficheiro
    elements.fileNameDisplay.textContent = file.name;
    elements.fileSizeDisplay.textContent = formatFileSize(file.size);
    elements.subtitleCountDisplay.textContent = subtitles.length;

    // Carregar metadados do filme
    if (!window.movieMetadataManager) {
        window.movieMetadataManager = initMovieMetadata();
    }

    // Tentar carregar metadados (assíncrono, não bloqueia)
    try {
        await window.movieMetadataManager.loadMetadata(file.name);
        console.log('✅ Metadados carregados com sucesso');
    } catch (error) {
        console.warn('⚠️ Erro ao carregar metadados:', error);
    }

    // Preview das primeiras 5 legendas
    elements.originalPreview.innerHTML = '';
    subtitles.slice(0, 5).forEach(sub => {
        const item = document.createElement('div');
        item.className = 'subtitle-item';
        item.innerHTML = `
            <div class="subtitle-id">#${sub.id}</div>
            <div class="subtitle-time">${sub.timeframe}</div>
            <div class="subtitle-text">${escapeHtml(sub.text)}</div>
        `;
        elements.originalPreview.appendChild(item);
    });

    // Mostrar secção
    showSection('filePreview');
}

/**
 * Inicia a tradução
 */
async function startTranslation() {
    showSection('progress');

    // Initialize progress manager
    if (!window.progressManager) {
        window.progressManager = initProgressManager();
    }

    const texts = SRTParser.extractTexts(appState.parsedSubtitles);
    const totalBatches = Math.ceil(texts.length / 10);

    // Start progress tracking
    window.progressManager.start(texts.length, totalBatches);

    try {
        // Obter configuração dos metadados do filme
        let translatorConfig = {};
        if (window.movieMetadataManager && window.movieMetadataManager.isInitialized()) {
            translatorConfig = window.movieMetadataManager.getTranslationConfig();
            console.log('📝 Usando glossário com', Object.keys(translatorConfig.glossary).length, 'termos');
            console.log('📄 Contexto:', translatorConfig.context.substring(0, 100) + '...');
        }

        // Adicionar idioma de origem se foi detectado (de extração MKV)
        if (appState.sourceLanguage && appState.sourceLanguageCode) {
            translatorConfig.sourceLanguage = appState.sourceLanguage;
            translatorConfig.sourceLanguageCode = appState.sourceLanguageCode;
            console.log(`🌍 Traduzindo de ${appState.sourceLanguage} → PT-PT`);
        }

        const translator = new GeminiTranslator(appState.apiKey, translatorConfig);

        // Traduzir com callback de progresso e correção robusta de quebras de linha
        const translatedTexts = await translator.translateBatch(
            texts,
            (progress) => {
                // Pegar o último texto traduzido do array que vem no callback
                const lastTranslated = progress.translatedTexts.length > 0
                    ? progress.translatedTexts[progress.translatedTexts.length - 1]
                    : null;

                // Pegar o texto original correspondente à última tradução
                const lastOriginalIndex = progress.translatedTexts.length > 0
                    ? progress.translatedTexts.length - 1
                    : 0;

                updateProgress(
                    progress,
                    texts[lastOriginalIndex] || null,
                    lastTranslated
                );
            },
            appState.parsedSubtitles // Passar legendas originais para correção de linha
        );

        // Atualizar legendas com traduções
        appState.translatedSubtitles = SRTParser.updateTexts(appState.parsedSubtitles, translatedTexts);
        appState.translatedContent = SRTParser.generate(appState.translatedSubtitles);

        // Complete progress tracking
        window.progressManager.complete();

        // Mostrar resultado
        setTimeout(() => showResult(), 500);

    } catch (error) {
        console.error('Erro na tradução:', error);

        // Se for erro de API key, limpar
        if (error.message.includes('API') || error.message.includes('key')) {
            appState.apiKey = null;
        }

        showError(error.message);
    }
}

/**
 * Atualiza o progresso da tradução
 */
function updateProgress(progress, originalText, translatedText) {
    // Use progress manager if available
    if (window.progressManager) {
        window.progressManager.updateProgress(progress.batch, progress.current);

        if (translatedText && originalText) {
            // Get timeframe from current subtitle if available
            const currentSub = appState.parsedSubtitles[progress.current - 1];
            const timeCode = currentSub ? currentSub.timeframe : '';

            window.progressManager.addLiveTranslation(
                originalText,
                translatedText,
                timeCode
            );
        }
    } else {
        // Fallback to old system
        const percentage = progress.percentage;

        elements.progressFill.style.width = `${percentage}%`;
        elements.progressPercentage.textContent = `${percentage}%`;

        elements.batchInfo.textContent = `${progress.batch}/${progress.totalBatches}`;
        elements.subtitleInfo.textContent = `${progress.current}/${progress.total}`;

        if (translatedText && originalText) {
            const item = document.createElement('div');
            item.className = 'translation-item';
            item.innerHTML = `
                <div class="original">🇬🇧 ${escapeHtml(truncateText(originalText, 60))}</div>
                <div class="translated">🇵🇹 ${escapeHtml(truncateText(translatedText, 60))}</div>
            `;

            elements.liveTranslations.insertBefore(item, elements.liveTranslations.firstChild);

            while (elements.liveTranslations.children.length > 5) {
                elements.liveTranslations.removeChild(elements.liveTranslations.lastChild);
            }
        }
    }
}

/**
 * Mostra o resultado final
 */
function showResult() {
    // Atualizar label do idioma original
    const originalLabel = document.getElementById('originalLanguageLabel');
    if (originalLabel) {
        if (appState.sourceLanguage && appState.sourceLanguageCode) {
            // Obter bandeira do idioma
            const langFlag = window.languageDetector ?
                window.languageDetector.getLanguageFlag(appState.sourceLanguageCode) : '';
            originalLabel.textContent = `${langFlag} Original (${appState.sourceLanguage})`;
        } else {
            originalLabel.textContent = '🇬🇧 Original (Inglês)';
        }
    }

    // Informações
    elements.originalFileName.textContent = appState.currentFile.name;
    elements.translatedCount.textContent = appState.translatedSubtitles.length;
    elements.finalFileName.textContent = appState.currentFile.name.replace('.srt', '_PT-PT.srt');

    // Preview das primeiras 5 legendas (original vs traduzido)
    elements.originalFinalPreview.innerHTML = '';
    elements.translatedPreview.innerHTML = '';

    appState.parsedSubtitles.slice(0, 5).forEach((sub, index) => {
        // Original
        const originalItem = document.createElement('div');
        originalItem.className = 'subtitle-item';
        originalItem.innerHTML = `
            <div class="subtitle-id">#${sub.id}</div>
            <div class="subtitle-time">${sub.timeframe}</div>
            <div class="subtitle-text">${escapeHtml(sub.text)}</div>
        `;
        elements.originalFinalPreview.appendChild(originalItem);

        // Traduzido
        const translatedItem = document.createElement('div');
        translatedItem.className = 'subtitle-item';
        translatedItem.innerHTML = `
            <div class="subtitle-id">#${appState.translatedSubtitles[index].id}</div>
            <div class="subtitle-time">${appState.translatedSubtitles[index].timeframe}</div>
            <div class="subtitle-text">${escapeHtml(appState.translatedSubtitles[index].text)}</div>
        `;
        elements.translatedPreview.appendChild(translatedItem);
    });

    showSection('result');
}

/**
 * Download do ficheiro traduzido
 */
function downloadTranslatedFile() {
    if (!appState.translatedContent) return;

    const blob = new Blob([appState.translatedContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = appState.currentFile.name.replace('.srt', '_PT-PT.srt');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Mostra erro
 */
function showError(message) {
    elements.errorMessage.textContent = message;
    showSection('error');
}

/**
 * Reset para upload
 */
function resetToUpload() {
    // Limpar estado
    appState.currentFile = null;
    appState.originalContent = null;
    appState.parsedSubtitles = null;
    appState.translatedSubtitles = null;
    appState.translatedContent = null;

    // Limpar input
    elements.fileInput.value = '';
    elements.fileName.textContent = 'Clique ou arraste o ficheiro SRT aqui';

    // Limpar previews
    elements.originalPreview.innerHTML = '';
    elements.liveTranslations.innerHTML = '';

    // Reset progress
    elements.progressFill.style.width = '0%';
    elements.progressPercentage.textContent = '0%';

    showSection('upload');
}

/**
 * Limpar chave da API
 */
function clearApiKey() {
    if (confirm('Deseja limpar a chave da API? Terá de introduzir uma nova.')) {
        appState.apiKey = null;
        alert('Chave da API removida.');
    }
}

/**
 * Mostra uma secção específica
 */
function showSection(section) {
    elements.uploadSection.classList.add('hidden');
    elements.filePreviewSection.classList.add('hidden');
    elements.progressSection.classList.add('hidden');
    elements.resultSection.classList.add('hidden');
    elements.errorSection.classList.add('hidden');

    switch(section) {
        case 'upload':
            elements.uploadSection.classList.remove('hidden');
            break;
        case 'filePreview':
            elements.filePreviewSection.classList.remove('hidden');
            break;
        case 'progress':
            elements.progressSection.classList.remove('hidden');
            break;
        case 'result':
            elements.resultSection.classList.remove('hidden');
            break;
        case 'error':
            elements.errorSection.classList.remove('hidden');
            break;
    }
}

/**
 * Lê o conteúdo do ficheiro
 */
function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Erro ao ler o ficheiro'));
        reader.readAsText(file);
    });
}

/**
 * Formata o tamanho do ficheiro
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Trunca texto
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Inicializar MKV Extractor quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar MKV extractor
    if (typeof initMKVExtractor === 'function') {
        window.mkvExtractorUI = initMKVExtractor();
        console.log('✅ MKV Extractor UI inicializado');
    }

    // Listener para evento de carregar ficheiro extraído
    document.addEventListener('loadSubtitleFile', async (event) => {
        const { file, content, sourceLanguage, sourceLanguageCode } = event.detail;
        console.log('🔄 Carregando ficheiro extraído:', file.name);

        // Armazenar informação do idioma de origem
        if (sourceLanguage && sourceLanguageCode) {
            appState.sourceLanguage = sourceLanguage;
            appState.sourceLanguageCode = sourceLanguageCode;
            console.log(`🌍 Idioma de origem: ${sourceLanguage} (${sourceLanguageCode})`);

            // Atualizar descrição do header
            const headerDesc = document.getElementById('headerDescription');
            if (headerDesc) {
                headerDesc.textContent = `Traduzindo de ${sourceLanguage} para Português (PT-PT)`;
            }
        }

        // Simular seleção de ficheiro
        appState.currentFile = file;

        try {
            // Parse do conteúdo SRT
            appState.originalContent = content;
            appState.parsedSubtitles = SRTParser.parse(content);

            if (appState.parsedSubtitles.length === 0) {
                throw new Error('Nenhuma legenda encontrada no ficheiro.');
            }

            console.log(`✅ ${appState.parsedSubtitles.length} legendas carregadas`);

            // Mostrar preview
            showFilePreview();

        } catch (error) {
            console.error('❌ Erro ao processar legenda:', error);
            showError(error.message);
        }
    });
});
