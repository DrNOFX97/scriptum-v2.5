/**
 * Scriptum v2.0 - Frontend JavaScript
 * Sincronização Inteligente de Legendas
 */

// Global state
let videoFile = null;
let subtitleFile = null;
let subtitleData = null;
let currentOffset = 0;

// DOM Elements
const videoInput = document.getElementById('videoInput');
const subtitleInput = document.getElementById('subtitleInput');
const videoUpload = document.getElementById('videoUpload');
const subtitleUpload = document.getElementById('subtitleUpload');
const videoInfo = document.getElementById('videoInfo');
const subtitleInfo = document.getElementById('subtitleInfo');
const videoContainer = document.getElementById('videoContainer');
const movieInfo = document.getElementById('movieInfo');
const offsetSlider = document.getElementById('offsetSlider');
const offsetValue = document.getElementById('offsetValue');
const syncBtn = document.getElementById('syncBtn');
const applyBtn = document.getElementById('applyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const status = document.getElementById('status');
const logContainer = document.getElementById('logContainer');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupDragDrop();
    setupFileInputs();
    setupSlider();
});

// ============================
// File Upload Handlers
// ============================

function setupFileInputs() {
    videoInput.addEventListener('change', (e) => {
        handleVideoFile(e.target.files[0]);
    });

    subtitleInput.addEventListener('change', (e) => {
        handleSubtitleFile(e.target.files[0]);
    });
}

function setupDragDrop() {
    // Video upload
    videoUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        videoUpload.classList.add('dragover');
    });

    videoUpload.addEventListener('dragleave', () => {
        videoUpload.classList.remove('dragover');
    });

    videoUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        videoUpload.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });

    // Subtitle upload
    subtitleUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        subtitleUpload.classList.add('dragover');
    });

    subtitleUpload.addEventListener('dragleave', () => {
        subtitleUpload.classList.remove('dragover');
    });

    subtitleUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        subtitleUpload.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleSubtitleFile(e.dataTransfer.files[0]);
        }
    });
}

function handleVideoFile(file) {
    if (!file) return;

    // Validate video file - accept most common video formats
    const validExtensions = /\.(mp4|mkv|avi|webm|mov|flv|wmv|m4v|mpg|mpeg|3gp|ogv)$/i;
    // Expanded MIME types to include generic ones that might be used for MKV
    const validTypes = [
        'video/mp4', 'video/mkv', 'video/x-matroska', 'application/x-matroska', 'application/octet-stream',
        'video/avi', 'video/x-msvideo', 'video/webm', 'video/quicktime',
        'video/x-flv', 'video/x-ms-wmv', 'video/mpeg'
    ];

    // Accept if either MIME type matches OR file extension is valid
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.test(file.name);

    // Explicitly allow MKV extension regardless of MIME type (safeguard)
    const isMkvExtension = file.name.toLowerCase().endsWith('.mkv');

    if (!hasValidType && !hasValidExtension && !isMkvExtension && file.type && !file.type.startsWith('video/')) {
        console.error(`Rejected file: ${file.name}, Type: ${file.type}`);
        showStatus('error', '❌ Formato de vídeo não suportado');
        addLog('error', `Ficheiro rejeitado: ${file.name} (${file.type || 'sem tipo'})`);
        return;
    }

    videoFile = file;

    // Update UI
    document.getElementById('videoName').textContent = file.name;
    document.getElementById('videoSize').textContent = formatFileSize(file.size);
    videoInfo.classList.add('active');

    // Show extract button if it's an MKV file
    const extractBtn = document.getElementById('extractBtn');
    const isMKV = file.name.toLowerCase().endsWith('.mkv');

    if (isMKV) {
        extractBtn.style.display = 'block';
        extractBtn.disabled = false;
    } else {
        extractBtn.style.display = 'none';
    }

    // If it's MKV, automatically remux to MP4 for playback
    if (isMKV) {
        addLog('info', `✅ Vídeo carregado: ${file.name}`);
        addLog('info', '🚦 Iniciando processamento sequencial para MKV (evita falhas)...');

        // Execute sequentially to avoid choking the connection with multiple large uploads
        (async () => {
            try {
                // 1. Remux for visualization
                addLog('info', '1️⃣ Passo 1/2: Preparando vídeo para visualização...');
                await autoRemuxAndLoad(file);

                // 2. Analyze (and extract subtitles)
                addLog('info', '2️⃣ Passo 2/2: Analisando e buscando legendas...');
                await analyzeVideoFile(file);

                addLog('success', '✅ Processamento MKV concluído!');
            } catch (err) {
                console.error("Sequence error:", err);
            }
        })();
    } else {
        addLog('info', `✅ Vídeo carregado: ${file.name}`);

        // Try to load video in player
        loadVideoPlayer(file);

        // Analyze video
        analyzeVideoFile(file);
    }

    // Try to recognize movie from filename
    recognizeMovie(file.name);

    // Enable buttons if subtitle is also loaded
    updateButtonStates();
}

function handleSubtitleFile(file) {
    if (!file) return;

    // Validate subtitle file
    if (!file.name.endsWith('.srt')) {
        showStatus('error', '❌ Apenas ficheiros .srt são suportados');
        return;
    }

    subtitleFile = file;

    // Update UI
    document.getElementById('subtitleName').textContent = file.name;
    document.getElementById('subtitleSize').textContent = formatFileSize(file.size);
    subtitleInfo.classList.add('active');

    // Load subtitle data
    loadSubtitleData(file);

    // Enable buttons if video is also loaded
    updateButtonStates();

    addLog('info', `✅ Legenda carregada: ${file.name}`);
}

// ============================
// Video Player
// ============================

function loadVideoPlayer(file) {
    const url = URL.createObjectURL(file);

    // Clear placeholder
    videoContainer.innerHTML = '';

    // Create video element with Video.js classes
    const video = document.createElement('video');
    video.id = 'videoPlayer';
    video.className = 'video-js vjs-default-skin';
    video.controls = true;
    video.preload = 'auto';
    video.style.width = '100%';
    video.style.height = 'auto';

    // Create source element
    const source = document.createElement('source');
    source.src = url;

    // Try to detect mime type
    const ext = file.name.split('.').pop().toLowerCase();
    const mimeTypes = {
        'mp4': 'video/mp4',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime'
    };
    source.type = mimeTypes[ext] || 'video/mp4';

    video.appendChild(source);
    videoContainer.appendChild(video);

    // Initialize Video.js player
    if (typeof videojs !== 'undefined') {
        const player = videojs(video, {
            controls: true,
            autoplay: false,
            preload: 'auto',
            fluid: true
        });

        // Add subtitle track overlay
        const subtitleOverlay = document.createElement('div');
        subtitleOverlay.id = 'subtitleOverlay';
        subtitleOverlay.style.cssText = `
            position: absolute;
            bottom: 60px;
            left: 0;
            right: 0;
            text-align: center;
            color: white;
            font-size: 20px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
            padding: 10px;
            pointer-events: none;
            z-index: 1000;
        `;
        videoContainer.style.position = 'relative';
        videoContainer.appendChild(subtitleOverlay);

        // Update subtitles during playback
        player.on('timeupdate', () => {
            updateSubtitleOverlay(player.currentTime());
        });

        // Handle errors
        player.on('error', (e) => {
            console.error('Video error:', e);

            // Check if it's an MKV file
            const isMKV = file.name.toLowerCase().endsWith('.mkv');

            if (isMKV) {
                addLog('warning', '⚡ MKV não pode ser reproduzido diretamente - convertendo...');

                // Show converting message for MKV
                videoContainer.innerHTML = `
                    <div style="aspect-ratio: 16/9; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; text-align: center; padding: 20px;">
                        <div style="font-size: 3em; margin-bottom: 20px;">⚡</div>
                        <div style="font-size: 1.4em; margin-bottom: 15px; font-weight: bold;">Convertendo MKV para Visualização</div>
                        <div style="color: #f0e6ff; font-size: 1em; max-width: 500px; line-height: 1.6;">
                            <p style="margin-bottom: 10px;">🎬 Arquivo MKV detectado</p>
                            <p style="margin-bottom: 10px;">⚡ Fazendo remux instantâneo para MP4...</p>
                            <p style="margin-bottom: 15px;"><strong>Aguarde alguns segundos</strong> - o vídeo aparecerá automaticamente!</p>
                            <div style="margin-top: 20px;">
                                <div class="spinner" style="border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                addLog('error', '❌ Erro ao carregar vídeo. Formato pode não ser suportado pelo browser.');

                // Show error message for other formats
                videoContainer.innerHTML = `
                    <div style="aspect-ratio: 16/9; background: #2d3748; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; text-align: center; padding: 20px;">
                        <div style="font-size: 3em; margin-bottom: 20px;">⚠️</div>
                        <div style="font-size: 1.2em; margin-bottom: 10px;">Formato de vídeo não suportado</div>
                        <div style="color: #a0aec0; font-size: 0.9em; max-width: 500px;">
                            <p>O browser não consegue reproduzir este formato.</p>
                            <p><strong>Solução:</strong> A sincronização funciona mesmo sem pré-visualização!</p>
                            <p>Carregue a legenda e clique em "Sincronizar Automaticamente"</p>
                        </div>
                </div>
            `;
            }
        });
    } else {
        // Fallback to native HTML5
        video.addEventListener('timeupdate', () => {
            updateSubtitleOverlay(video.currentTime);
        });
    }
}

function updateSubtitleOverlay(currentTime) {
    if (!subtitleData) return;

    const adjustedTime = currentTime + currentOffset;
    const overlay = document.getElementById('subtitleOverlay');

    if (!overlay) return;

    // Find subtitle for current time
    const subtitle = subtitleData.find(sub =>
        adjustedTime >= sub.start && adjustedTime <= sub.end
    );

    if (subtitle) {
        overlay.textContent = subtitle.text;
        overlay.style.opacity = '1';
    } else {
        overlay.style.opacity = '0';
    }
}

// ============================
// Subtitle Parsing
// ============================

function loadSubtitleData(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const content = e.target.result;
        subtitleData = parseSRT(content);
        addLog('success', `✅ Legenda parseada: ${subtitleData.length} entradas`);
    };
    reader.readAsText(file);
}

function parseSRT(content) {
    const blocks = content.trim().split('\n\n');
    const subtitles = [];

    for (const block of blocks) {
        const lines = block.split('\n');
        if (lines.length < 3) continue;

        const timeLine = lines[1];
        const match = timeLine.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/);

        if (match) {
            const start = parseTime(match[1], match[2], match[3], match[4]);
            const end = parseTime(match[5], match[6], match[7], match[8]);
            const text = lines.slice(2).join('\n');

            subtitles.push({ start, end, text });
        }
    }

    return subtitles;
}

function parseTime(h, m, s, ms) {
    return parseInt(h) * 3600 + parseInt(m) * 60 + parseInt(s) + parseInt(ms) / 1000;
}

// ============================
// IMDB Recognition
// ============================

async function recognizeMovie(filename) {
    addLog('info', `🔍 A procurar: "${filename}" no TMDB...`);

    try {
        // Use backend API
        const response = await fetch('http://localhost:5001/recognize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: filename })
        });

        if (!response.ok) {
            addLog('info', '⚠️ Filme não encontrado no TMDB');
            return;
        }

        const data = await response.json();

        if (data.success && data.movie) {
            displayMovieInfo(data.movie);
        } else {
            addLog('info', '⚠️ Filme não encontrado no TMDB');
        }
    } catch (error) {
        addLog('error', `❌ Erro: ${error.message}`);
    }
}

function displayMovieInfo(movie) {
    const posterUrl = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : 'https://via.placeholder.com/120x180?text=No+Poster';

    document.getElementById('moviePoster').src = posterUrl;
    document.getElementById('movieTitle').textContent = movie.title;
    document.getElementById('movieYear').textContent = movie.release_date?.split('-')[0] || 'N/A';
    document.getElementById('movieRating').textContent = movie.vote_average?.toFixed(1) || 'N/A';
    document.getElementById('movieDuration').textContent = 'N/A'; // Duration not in search results

    movieInfo.classList.add('active');
    addLog('success', `✅ Filme reconhecido: ${movie.title}`);
}

// ============================
// Sync Controls
// ============================

function setupSlider() {
    offsetSlider.addEventListener('input', (e) => {
        currentOffset = parseFloat(e.target.value);
        offsetValue.textContent = formatOffset(currentOffset);

        // Update subtitle preview in real-time
        const video = document.getElementById('videoPlayer');
        if (video) {
            updateSubtitleOverlay(video.currentTime);
        }
    });
}

function adjustOffset(delta) {
    currentOffset += delta;
    currentOffset = Math.max(-10, Math.min(10, currentOffset)); // Clamp to range
    offsetSlider.value = currentOffset;
    offsetValue.textContent = formatOffset(currentOffset);

    // Update subtitle preview
    const video = document.getElementById('videoPlayer');
    if (video) {
        updateSubtitleOverlay(video.currentTime);
    }
}

function formatOffset(seconds) {
    return `${seconds >= 0 ? '+' : ''}${seconds.toFixed(2)}s`;
}

// ============================
// Synchronization Actions
// ============================

async function startAutoSync() {
    if (!videoFile || !subtitleFile) {
        showStatus('error', '❌ Carregue vídeo e legenda primeiro');
        return;
    }

    addLog('info', '🤖 Iniciando sincronização automática...');
    showStatus('info', '🔄 A sincronizar... isto pode demorar alguns minutos');

    syncBtn.disabled = true;
    progressContainer.classList.add('active');
    logContainer.classList.add('active');

    // Create FormData for backend
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('subtitle', subtitleFile);

    try {
        // Call backend API
        addLog('info', '📡 Enviando para servidor...');
        await simulateProgress(10);

        const response = await fetch('http://localhost:5001/sync', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Sync failed');
        }

        addLog('info', '📊 A analisar vídeo...');
        await simulateProgress(30);

        const result = await response.json();

        addLog('info', '🎙️ A extrair áudio...');
        await simulateProgress(50);

        addLog('info', '🤖 A transcrever com Whisper...');
        await simulateProgress(70);

        addLog('info', '🔍 A calcular offset...');
        await simulateProgress(90);

        addLog('success', '✅ Sincronização concluída!');
        await simulateProgress(100);

        // Log results
        addLog('info', `📊 Vídeo FPS: ${result.video_fps}`);
        addLog('info', `📄 Legenda FPS: ${result.subtitle_fps}`);
        if (result.framerate_converted) {
            addLog('success', '🔧 Framerate convertido automaticamente');
        }
        addLog('info', `🎙️  Idioma detectado: ${result.language}`);
        addLog('info', `📏 Duração: ${Math.floor(result.duration / 60)}min ${result.duration % 60}s`);
        addLog('info', `📈 Offsets detectados: ${result.offsets.join('s, ')}s`);
        addLog('success', `✅ Offset médio: ${result.offset >= 0 ? '+' : ''}${result.offset}s (σ=${result.std_dev}s)`);

        // Update subtitle data with synced content
        subtitleData = parseSRT(result.synced_content);

        // Apply detected offset to UI
        currentOffset = result.offset;
        offsetSlider.value = currentOffset;
        offsetValue.textContent = formatOffset(currentOffset);

        showStatus('success', `✅ Offset detectado: ${formatOffset(result.offset)}`);
        downloadBtn.disabled = false;

        // Update video preview
        const video = document.getElementById('videoPlayer');
        if (video) {
            updateSubtitleOverlay(video.currentTime);
        }

    } catch (error) {
        addLog('error', `❌ Erro: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    } finally {
        syncBtn.disabled = false;
        setTimeout(() => {
            progressContainer.classList.remove('active');
        }, 1000);
    }
}

function applyManualSync() {
    if (!subtitleData) {
        showStatus('error', '❌ Carregue uma legenda primeiro');
        return;
    }

    addLog('info', `🔧 Aplicando offset manual: ${formatOffset(currentOffset)}`);

    // Apply offset to subtitle data
    subtitleData = subtitleData.map(sub => ({
        start: sub.start + currentOffset,
        end: sub.end + currentOffset,
        text: sub.text
    }));

    // Update video preview
    const video = document.getElementById('videoPlayer');
    if (video) {
        updateSubtitleOverlay(video.currentTime);
    }

    showStatus('success', `✅ Offset de ${formatOffset(currentOffset)} aplicado`);
    downloadBtn.disabled = false;
    addLog('success', '✅ Ajuste manual aplicado');
}

function downloadSubtitle() {
    if (!subtitleData) {
        showStatus('error', '❌ Nenhuma legenda para download');
        return;
    }

    // Generate SRT content
    const srtContent = generateSRT(subtitleData);

    // Create download
    const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = subtitleFile.name.replace('.srt', '.sync.srt');
    a.click();

    URL.revokeObjectURL(url);

    addLog('success', `✅ Download: ${a.download}`);
    showStatus('success', '✅ Legenda sincronizada descarregada!');
}

function generateSRT(subtitles) {
    let srt = '';

    for (let i = 0; i < subtitles.length; i++) {
        const sub = subtitles[i];
        srt += `${i + 1}\n`;
        srt += `${formatSRTTime(sub.start)} --> ${formatSRTTime(sub.end)}\n`;
        srt += `${sub.text}\n\n`;
    }

    return srt;
}

function formatSRTTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);

    return `${pad(h, 2)}:${pad(m, 2)}:${pad(s, 2)},${pad(ms, 3)}`;
}

function pad(num, size) {
    return String(num).padStart(size, '0');
}

// ============================
// UI Helpers
// ============================

function updateButtonStates() {
    const bothLoaded = videoFile && subtitleFile;
    syncBtn.disabled = !bothLoaded;
    applyBtn.disabled = !bothLoaded;

    // Enable search button if video is loaded (can search by hash)
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.disabled = !videoFile;
    }

    // Enable translate button if subtitle is loaded
    const translateBtn = document.getElementById('translateBtn');
    if (translateBtn) {
        translateBtn.disabled = !subtitleFile;
    }
}

function showStatus(type, message) {
    status.className = `status ${type} active`;
    status.textContent = message;

    setTimeout(() => {
        status.classList.remove('active');
    }, 5000);
}

function addLog(type, message) {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(line);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

async function simulateProgress(targetPercent) {
    return new Promise(resolve => {
        setTimeout(() => {
            progressBar.style.width = targetPercent + '%';
            resolve();
        }, 800);
    });
}

// ============================
// OpenSubtitles Integration
// ============================

function extractMovieName(filename) {
    /**
     * Extract clean movie name from filename
     * Examples:
     *   "The.Matrix.1999.1080p.BluRay.mkv" → "The Matrix"
     *   "Inception (2010) WEB-DL.mp4" → "Inception"
     */
    let name = filename
        .replace(/\.(mp4|mkv|avi|webm)$/i, '')  // Remove extension
        .replace(/[\._]/g, ' ')                 // Replace dots/underscores with spaces
        .replace(/\d{4}.*$/, '')                 // Remove year and everything after
        .replace(/\b(720p|1080p|2160p|4K|BluRay|WEB-DL|HDTV|x264|x265|HEVC|AAC|DTS)\b.*/gi, '')
        .trim();

    return name;
}

async function searchOpenSubtitles() {
    if (!videoFile) {
        showStatus('error', '❌ Carregue um vídeo primeiro');
        return;
    }

    addLog('info', '🔍 Procurando legendas online...');

    // Show analysis panel if not visible
    const analysisPanel = document.getElementById('analysisPanel');
    analysisPanel.classList.add('show');

    const subtitlesList = document.getElementById('availableSubtitles');
    subtitlesList.innerHTML = '<div class="loading-spinner">Procurando legendas...</div>';

    try {
        // Use quick subtitle search (no upload needed)
        const response = await fetch('http://localhost:5001/quick-subtitle-search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: videoFile.name,
                language: 'pt'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Search failed');
        }

        const result = await response.json();

        if (!result.success || result.count === 0) {
            subtitlesList.innerHTML = '<div class="no-results">Nenhuma legenda encontrada</div>';
            addLog('info', '⚠️  Nenhuma legenda encontrada');
            return;
        }

        addLog('success', `✅ ${result.count} legendas encontradas`);

        // Display subtitles in the panel
        subtitlesList.innerHTML = '';
        result.subtitles.slice(0, 10).forEach(sub => {
            const item = createSubtitleItem(sub);
            subtitlesList.appendChild(item);
        });

    } catch (error) {
        addLog('error', `❌ Erro: ${error.message}`);

        // Check if it's an API key error
        const response = await fetch('http://localhost:5001/search-subtitles', {
            method: 'POST',
            body: formData
        }).catch(() => null);

        if (response && response.status === 403) {
            const errorData = await response.json();
            const instructions = errorData.instructions || {};

            document.getElementById('subtitlesResults').innerHTML = `
                <div style="padding:30px;max-width:600px;margin:0 auto;">
                    <div style="text-align:center;margin-bottom:25px;">
                        <div style="font-size:3em;margin-bottom:10px;">🔑</div>
                        <h3 style="color:#666;margin:0;">API Key Necessária</h3>
                    </div>

                    <p style="text-align:center;color:#666;margin-bottom:30px;">
                        ${errorData.message || 'OpenSubtitles.com requer uma API key gratuita'}
                    </p>

                    <div style="background:#f5f5f5;border-radius:8px;padding:20px;margin-bottom:20px;">
                        <h4 style="margin-top:0;color:#333;">📝 Como configurar (1 minuto):</h4>
                        <ol style="line-height:2;color:#666;margin:15px 0;">
                            <li>${instructions.step1 || 'Crie conta em opensubtitles.com'}</li>
                            <li>${instructions.step2 || 'Gere API key no painel'}</li>
                            <li>${instructions.step3 || 'Configure variável de ambiente'}</li>
                            <li>${instructions.step4 || 'Reinicie o servidor'}</li>
                        </ol>
                    </div>

                    <div style="text-align:center;">
                        <a href="https://www.opensubtitles.com/api" target="_blank"
                           style="display:inline-block;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                  color:white;padding:12px 30px;border-radius:25px;text-decoration:none;
                                  font-weight:bold;margin-right:10px;">
                            🔗 Obter API Key
                        </a>
                        <a href="https://opensubtitles.stoplight.io/docs/opensubtitles-api" target="_blank"
                           style="display:inline-block;background:#e8e8e8;color:#666;padding:12px 30px;
                                  border-radius:25px;text-decoration:none;">
                            📚 Documentação
                        </a>
                    </div>

                    <p style="text-align:center;font-size:0.9em;color:#999;margin-top:20px;">
                        ℹ️ ${instructions.limit || 'Conta gratuita: 20 downloads/dia'}
                    </p>
                </div>
            `;
        } else {
            document.getElementById('subtitlesResults').innerHTML =
                `<div style="text-align:center;padding:40px;color:#ff4d4f;">❌ Erro: ${error.message}</div>`;
        }
    }
}

function displaySubtitleResults(subtitles) {
    const container = document.getElementById('subtitlesResults');
    container.innerHTML = '';

    subtitles.forEach(sub => {
        const item = document.createElement('div');
        item.className = 'subtitle-item';
        item.onclick = () => downloadFromOpenSubtitles(sub.id, sub.release);

        item.innerHTML = `
            <div class="subtitle-header">
                <div class="subtitle-title">${sub.release || 'Unknown Release'}</div>
                <span class="subtitle-badge">${sub.language.toUpperCase()}</span>
            </div>
            <div class="subtitle-meta">
                <div class="subtitle-meta-item">
                    <span>⬇️</span>
                    <span>${sub.downloads.toLocaleString()} downloads</span>
                </div>
                <div class="subtitle-meta-item">
                    <span>⭐</span>
                    <span>${sub.rating}/10 (${sub.votes} votos)</span>
                </div>
                <div class="subtitle-meta-item">
                    <span>🎬</span>
                    <span>${sub.fps} FPS</span>
                </div>
                <div class="subtitle-meta-item">
                    <span>👤</span>
                    <span>${sub.uploader}</span>
                </div>
            </div>
        `;

        container.appendChild(item);
    });
}

async function downloadFromOpenSubtitles(fileId, releaseName) {
    addLog('info', `💾 A descarregar: ${releaseName}...`);
    closeSubtitlesModal();

    try {
        const response = await fetch('http://localhost:5001/download-subtitle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_id: fileId })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Download failed');
        }

        const result = await response.json();

        // Parse and load subtitle
        subtitleData = parseSRT(result.content);
        subtitleFile = new File([result.content], result.filename, { type: 'text/plain' });

        // Update UI
        document.getElementById('subtitleName').textContent = result.filename;
        document.getElementById('subtitleSize').textContent = formatFileSize(result.content.length);
        subtitleInfo.classList.add('active');

        addLog('success', `✅ Legenda descarregada: ${result.filename}`);
        showStatus('success', '✅ Legenda carregada do OpenSubtitles!');

        // Enable buttons
        updateButtonStates();

        // Update video preview
        const video = document.getElementById('videoPlayer');
        if (video) {
            updateSubtitleOverlay(video.currentTime);
        }

    } catch (error) {
        addLog('error', `❌ Erro ao descarregar: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    }
}

function showModal() {
    document.getElementById('subtitlesModal').classList.add('active');
}

function closeSubtitlesModal() {
    document.getElementById('subtitlesModal').classList.remove('active');
}

// Close modal on background click
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('subtitlesModal').addEventListener('click', (e) => {
        if (e.target.id === 'subtitlesModal') {
            closeSubtitlesModal();
        }
    });
});

// ============================
// Video Analysis Functions
// ============================

let analysisData = null;
let selectedConvertQuality = 'balanced';

async function quickSubtitleSearch(filename) {
    addLog('info', '🔍 Buscando legendas...');

    const analysisPanel = document.getElementById('analysisPanel');
    const subtitlesList = document.getElementById('availableSubtitles');

    // Show panel immediately with loading state
    analysisPanel.classList.add('show');
    subtitlesList.innerHTML = '<div class="loading-spinner">Procurando legendas...</div>';

    try {
        const response = await fetch('http://localhost:5001/quick-subtitle-search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: filename,
                language: 'pt'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.subtitles && data.subtitles.length > 0) {
            subtitlesList.innerHTML = '';

            data.subtitles.slice(0, 10).forEach(sub => {
                const item = createSubtitleItem(sub);
                subtitlesList.appendChild(item);
            });

            addLog('success', `✅ ${data.subtitles.length} legendas encontradas`);
        } else {
            subtitlesList.innerHTML = '<div class="no-results">Nenhuma legenda encontrada</div>';
            addLog('warning', '⚠️ Nenhuma legenda disponível');
        }

    } catch (error) {
        console.error('Quick subtitle search error:', error);
        subtitlesList.innerHTML = '<div class="no-results">Erro ao buscar legendas</div>';
        addLog('error', `❌ Erro na busca: ${error.message}`);
    }
}

async function analyzeVideoFile(file) {
    addLog('info', '📊 Analisando informações do vídeo...');

    const analysisPanel = document.getElementById('analysisPanel');
    analysisPanel.classList.add('show');

    try {
        const formData = new FormData();
        formData.append('video', file);
        formData.append('language', 'pt');

        const response = await fetch('http://localhost:5001/analyze-video', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        analysisData = await response.json();

        if (analysisData.success) {
            displayAnalysisResults(analysisData);

            // If it's an MKV file, automatically extract embedded subtitles
            if (file.name.toLowerCase().endsWith('.mkv')) {
                await autoExtractMKVSubtitles(file);
            }

            addLog('success', '✅ Análise completa!');
        } else {
            throw new Error(analysisData.error || 'Analysis failed');
        }

    } catch (error) {
        addLog('error', `❌ Erro na análise: ${error.message}`);
        analysisPanel.classList.remove('show');
    }
}

function displayAnalysisResults(data) {
    // 1. Update video stats
    if (data.video_info) {
        const info = data.video_info;
        document.getElementById('statFormat').textContent = info.format || '-';
        document.getElementById('statSize').textContent = info.size_mb ? `${info.size_mb} MB` : '-';
        document.getElementById('statResolution').textContent = info.resolution || '-';
        document.getElementById('statDuration').textContent = info.duration_formatted || '-';

        addLog('info', `📊 Formato: ${info.format}, ${info.resolution}, ${info.size_mb}MB`);
    }

    // 2. Display movie info (if available)
    if (data.movie) {
        const movie = data.movie;
        const movieInfo = document.getElementById('movieInfo');

        document.getElementById('movieTitle').textContent = movie.title;
        document.getElementById('movieYear').textContent = movie.year;
        document.getElementById('movieRating').textContent = movie.rating.toFixed(1);

        if (data.video_info && data.video_info.duration_formatted) {
            document.getElementById('movieDuration').textContent = data.video_info.duration_formatted;
        }

        if (movie.poster) {
            document.getElementById('moviePoster').src = movie.poster;
            movieInfo.classList.add('active');
        }

        addLog('info', `🎬 Filme: ${movie.title} (${movie.year})`);
    }

    // 3. Show subtitle search prompt (user must click button)
    const subtitlesList = document.getElementById('availableSubtitles');

    // Check if user already searched for subtitles
    const hasExistingSubtitles = subtitlesList.children.length > 0 &&
        !subtitlesList.querySelector('.loading-spinner') &&
        !subtitlesList.querySelector('.no-results') &&
        !subtitlesList.querySelector('.search-prompt');

    if (!hasExistingSubtitles) {
        subtitlesList.innerHTML = `
            <div class="search-prompt" style="text-align: center; padding: 30px 20px; color: #666;">
                <div style="font-size: 3em; margin-bottom: 15px;">🔍</div>
                <p style="font-size: 1.1em; margin-bottom: 10px;">Procurar Legendas Online</p>
                <p style="font-size: 0.9em; color: #999;">
                    Clique no botão<br>"🔍 Buscar Legendas Online"<br>para procurar legendas disponíveis
                </p>
            </div>
        `;
    }

    // 4. Show/hide conversion section
    const convertSection = document.getElementById('convertSection');
    if (data.can_convert_to_mp4) {
        convertSection.style.display = 'block';
        addLog('info', '🎞️ Conversão para MP4 disponível');
    } else {
        convertSection.style.display = 'none';
    }
}

function createSubtitleItem(sub) {
    const item = document.createElement('div');
    item.className = 'subtitle-item';
    item.onclick = () => downloadSubtitleFromAnalysis(sub);

    item.innerHTML = `
        <div class="subtitle-item-header">
            <span class="subtitle-item-name">${sub.name || 'Legenda'}</span>
            <span class="subtitle-item-lang">${sub.language || 'pt'}</span>
        </div>
        <div class="subtitle-item-meta">
            ${sub.downloads ? `<span>⬇️ ${sub.downloads} downloads</span>` : ''}
            ${sub.rating ? `<span>⭐ ${sub.rating}/10</span>` : ''}
        </div>
    `;

    return item;
}

async function downloadSubtitleFromAnalysis(subtitle) {
    addLog('info', `📥 Baixando: ${subtitle.name}`);

    // Highlight selected
    document.querySelectorAll('.subtitle-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');

    try {
        const response = await fetch('http://localhost:5001/download-subtitle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: subtitle.file_id })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Create file from content
            const blob = new Blob([result.content], { type: 'text/plain' });
            const file = new File([blob], result.filename, { type: 'text/plain' });

            // Handle as normal subtitle file
            handleSubtitleFile(file);

            addLog('success', `✅ ${result.filename} carregada`);
        } else {
            throw new Error(result.error || 'Download failed');
        }

    } catch (error) {
        addLog('error', `❌ Erro: ${error.message}`);
        showStatus('error', `❌ Erro ao baixar legenda`);
    }
}

function selectConvertQuality(quality) {
    selectedConvertQuality = quality;

    // Update UI
    document.querySelectorAll('.convert-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    document.querySelector(`[data-quality="${quality}"]`).classList.add('selected');
}

async function startConversion() {
    if (!videoFile) {
        showStatus('error', 'Nenhum vídeo carregado');
        return;
    }

    addLog('info', `🔄 Iniciando conversão (qualidade: ${selectedConvertQuality})...`);
    showStatus('info', '🔄 Convertendo vídeo... Isto pode demorar alguns minutos');

    try {
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('quality', selectedConvertQuality);

        const response = await fetch('http://localhost:5001/convert-to-mp4', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Conversion failed');
        }

        // Download the converted file
        const blob = await response.blob();
        const filename = videoFile.name.replace(/\.[^/.]+$/, '') + '.mp4';

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);

        addLog('success', `✅ Vídeo convertido: ${filename}`);
        showStatus('success', `✅ Conversão completa! Download iniciado`);

    } catch (error) {
        addLog('error', `❌ Erro na conversão: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    }
}

async function autoRemuxAndLoad(file) {
    showStatus('info', '⚡ Convertendo MKV para visualização...');

    try {
        const formData = new FormData();
        formData.append('video', file);

        const response = await fetch('http://localhost:5001/remux-mkv-to-mp4', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();

            // Check if it's a codec incompatibility error
            if (error.error && error.error.includes('codec')) {
                addLog('warning', '⚠️ Codec incompatível para remux rápido');
                showStatus('warning', '⚠️ Este MKV requer conversão completa para visualização');
                return;
            }

            throw new Error(error.error || 'Remux failed');
        }

        // Get the remuxed MP4 as blob
        const blob = await response.blob();

        // Create a File object from the blob
        const mp4File = new File([blob], file.name.replace(/\.mkv$/i, '.mp4'), {
            type: 'video/mp4'
        });

        // Load the MP4 in the player
        loadVideoPlayer(mp4File);

        addLog('success', '✅ Vídeo convertido e pronto para visualização!');
        showStatus('success', '✅ MKV convertido com sucesso!');

    } catch (error) {
        addLog('error', `❌ Erro na conversão automática: ${error.message}`);
        showStatus('error', '❌ Não foi possível carregar o vídeo no player');
    }
}

async function startRemux() {
    if (!videoFile) {
        showStatus('error', 'Nenhum vídeo carregado');
        return;
    }

    addLog('info', '⚡ Iniciando remux MKV → MP4 (sem re-encoding)...');
    showStatus('info', '⚡ Extraindo stream de vídeo... Isto é muito rápido!');

    try {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch('http://localhost:5001/remux-mkv-to-mp4', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();

            // Check if it's a codec incompatibility error
            if (error.error && error.error.includes('codec')) {
                addLog('warning', '⚠️ Codec incompatível - necessária conversão completa');
                showStatus('warning', '⚠️ Codec incompatível. Use a conversão completa abaixo.');
                return;
            }

            throw new Error(error.error || 'Remux failed');
        }

        // Download the remuxed file
        const blob = await response.blob();
        const filename = videoFile.name.replace(/\.[^/.]+$/, '') + '.mp4';

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);

        addLog('success', `✅ MP4 extraído em segundos: ${filename}`);
        showStatus('success', `✅ Remux completo! Download iniciado`);

    } catch (error) {
        addLog('error', `❌ Erro no remux: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    }
}

// ============================
// MKV Subtitle Extraction
// ============================

async function autoExtractMKVSubtitles(file) {
    addLog('info', '📤 Detectando legendas embutidas no MKV...');

    const subtitlesList = document.getElementById('availableSubtitles');
    subtitlesList.innerHTML = '<div class="loading-spinner">Procurando legendas embutidas...</div>';

    try {
        const formData = new FormData();
        formData.append('video', file);

        const response = await fetch('http://localhost:5001/extract-mkv-subtitles', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            // If extraction fails, just show the search prompt
            subtitlesList.innerHTML = `
                <div class="search-prompt" style="text-align: center; padding: 30px 20px; color: #666;">
                    <div style="font-size: 3em; margin-bottom: 15px;">🔍</div>
                    <p style="font-size: 1.1em; margin-bottom: 10px;">Procurar Legendas Online</p>
                    <p style="font-size: 0.9em; color: #999;">
                        Clique no botão<br>"🔍 Buscar Legendas Online"<br>para procurar legendas disponíveis
                    </p>
                </div>
            `;
            return;
        }

        const result = await response.json();

        if (!result.success || result.count === 0) {
            // No embedded subtitles found - show search prompt
            subtitlesList.innerHTML = `
                <div class="search-prompt" style="text-align: center; padding: 30px 20px; color: #666;">
                    <div style="font-size: 3em; margin-bottom: 15px;">🔍</div>
                    <p style="font-size: 1.1em; margin-bottom: 10px;">Sem legendas embutidas</p>
                    <p style="font-size: 0.9em; color: #999;">
                        Clique no botão<br>"🔍 Buscar Legendas Online"<br>para procurar legendas disponíveis
                    </p>
                </div>
            `;
            addLog('info', '📭 MKV não contém legendas embutidas');
            return;
        }

        addLog('success', `✅ ${result.count} legenda(s) embutida(s) encontrada(s)`);

        // Display extracted subtitles in the panel
        subtitlesList.innerHTML = '';

        result.subtitles.forEach((sub, index) => {
            const item = document.createElement('div');
            item.className = 'subtitle-item';
            item.dataset.subtitleIndex = index;
            item.style.cursor = 'pointer';
            item.title = 'Clique para carregar no player e ativar tradução/sincronização';

            item.innerHTML = `
                <div class="subtitle-item-header">
                    <span class="subtitle-item-name">📤 ${sub.title}</span>
                    <span class="subtitle-item-lang">${sub.language}</span>
                </div>
                <div class="subtitle-item-meta">
                    <span>🎬 Track ${sub.track_number}</span>
                    <span>📦 ${(sub.size / 1024).toFixed(1)} KB</span>
                    <span>🔤 ${sub.codec.toUpperCase()}</span>
                </div>
                <div style="margin-top: 8px; display: flex; gap: 8px;">
                    <button class="btn-mini" onclick="event.stopPropagation(); loadExtractedSubtitle(${JSON.stringify(sub).replace(/"/g, '&quot;')})" 
                            style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em;">
                        ▶️ Carregar no Player
                    </button>
                    <button class="btn-mini" onclick="event.stopPropagation(); downloadExtractedSubtitle(${JSON.stringify(sub).replace(/"/g, '&quot;')})" 
                            style="background: white; border: 2px solid #667eea; color: #667eea; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em;">
                        💾 Download
                    </button>
                </div>
            `;

            // Click on item also loads it
            item.onclick = (e) => {
                if (!e.target.closest('button')) {
                    loadExtractedSubtitle(sub);
                }
            };

            subtitlesList.appendChild(item);
        });

    } catch (error) {
        console.error('Auto-extract error:', error);
        // On error, show search prompt
        subtitlesList.innerHTML = `
            <div class="search-prompt" style="text-align: center; padding: 30px 20px; color: #666;">
                <div style="font-size: 3em; margin-bottom: 15px;">🔍</div>
                <p style="font-size: 1.1em; margin-bottom: 10px;">Procurar Legendas Online</p>
                <p style="font-size: 0.9em; color: #999;">
                    Clique no botão<br>"🔍 Buscar Legendas Online"<br>para procurar legendas disponíveis
                </p>
            </div>
        `;
    }
}

async function extractMKVSubtitles() {
    if (!videoFile) {
        showStatus('error', 'Nenhum vídeo carregado');
        return;
    }

    addLog('info', '📤 Extraindo legendas do MKV...');
    showStatus('info', '📤 Extraindo legendas embutidas...');

    const analysisPanel = document.getElementById('analysisPanel');
    const subtitlesList = document.getElementById('availableSubtitles');

    analysisPanel.classList.add('show');
    subtitlesList.innerHTML = '<div class="loading-spinner">Extraindo legendas...</div>';

    try {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch('http://localhost:5001/extract-mkv-subtitles', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Extraction failed');
        }

        const result = await response.json();

        if (!result.success || result.count === 0) {
            subtitlesList.innerHTML = '<div class="no-results">Nenhuma legenda embutida encontrada</div>';
            addLog('warning', '⚠️ Nenhuma legenda embutida');
            showStatus('info', 'ℹ️ MKV não contém legendas embutidas');
            return;
        }

        addLog('success', `✅ ${result.count} legenda(s) extraída(s)`);
        showStatus('success', `✅ ${result.count} legenda(s) encontrada(s) no MKV`);

        // Display extracted subtitles in the panel
        subtitlesList.innerHTML = '';

        result.subtitles.forEach(sub => {
            const item = document.createElement('div');
            item.className = 'subtitle-item';
            item.onclick = () => loadExtractedSubtitle(sub);

            item.innerHTML = `
                <div class="subtitle-item-header">
                    <span class="subtitle-item-name">📤 ${sub.title}</span>
                    <span class="subtitle-item-lang">${sub.language}</span>
                </div>
                <div class="subtitle-item-meta">
                    <span>🎬 Track ${sub.track_number}</span>
                    <span>📦 ${(sub.size / 1024).toFixed(1)} KB</span>
                    <span>🔤 ${sub.codec.toUpperCase()}</span>
                </div>
            `;

            subtitlesList.appendChild(item);
        });

    } catch (error) {
        console.error('MKV extraction error:', error);
        subtitlesList.innerHTML = '<div class="no-results">Erro ao extrair legendas</div>';
        addLog('error', `❌ Erro: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    }
}

function loadExtractedSubtitle(sub) {
    addLog('info', `📥 Carregando: ${sub.title}`);

    // Highlight selected
    document.querySelectorAll('.subtitle-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Find and highlight the item that was clicked
    const clickedItem = document.querySelector(`[data-subtitle-index]`);
    if (clickedItem) {
        document.querySelectorAll('.subtitle-item').forEach((item, idx) => {
            if (item.dataset.subtitleIndex !== undefined) {
                item.classList.remove('selected');
            }
        });
    }

    // Add selected class to current item if available
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('selected');
    }

    // Validate content
    if (!sub.content) {
        addLog('error', '❌ Conteúdo da legenda vazio');
        showStatus('error', '❌ Erro: legenda sem conteúdo');
        return;
    }

    // Create file from content
    const blob = new Blob([sub.content], { type: 'text/plain' });
    const file = new File([blob], sub.filename, { type: 'text/plain' });

    // Handle as normal subtitle file
    handleSubtitleFile(file);

    addLog('success', `✅ ${sub.filename} carregada e ativa no player`);
    showStatus('success', `✅ Legenda carregada! Pronta para sincronização/tradução`);
}

// Download extracted subtitle
function downloadExtractedSubtitle(sub) {
    addLog('info', `💾 Baixando: ${sub.filename}`);

    if (!sub.content) {
        addLog('error', '❌ Conteúdo da legenda vazio');
        showStatus('error', '❌ Erro: legenda sem conteúdo');
        return;
    }

    const blob = new Blob([sub.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = sub.filename;
    a.click();
    URL.revokeObjectURL(url);

    addLog('success', `✅ Download: ${sub.filename}`);
    showStatus('success', `✅ Legenda descarregada!`);
}

// ============================
// Translation Function
// ============================

async function translateSubtitle() {
    if (!subtitleFile) {
        showStatus('error', 'Nenhuma legenda carregada');
        return;
    }

    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;

    if (sourceLang === targetLang) {
        showStatus('error', 'Idioma de origem e destino devem ser diferentes');
        return;
    }

    addLog('info', `🌐 Iniciando tradução ${sourceLang.toUpperCase()} → ${targetLang.toUpperCase()}...`);
    showStatus('info', `🌐 Traduzindo legenda com Google Gemini...`);

    try {
        const formData = new FormData();
        formData.append('subtitle', subtitleFile);
        formData.append('source_lang', sourceLang);
        formData.append('target_lang', targetLang);

        // Add movie context if available
        if (analysisData && analysisData.movie && analysisData.movie.title) {
            formData.append('movie_context', analysisData.movie.title);
            addLog('info', `📽️ Contexto: ${analysisData.movie.title}`);
        }

        const response = await fetch('http://localhost:5001/translate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Translation failed');
        }

        // Download the translated file
        const blob = await response.blob();
        const filename = subtitleFile.name.replace('.srt', `_${targetLang}.srt`);

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);

        addLog('success', `✅ Tradução completa: ${filename}`);
        showStatus('success', `✅ Legenda traduzida com sucesso!`);

        // Optionally load the translated subtitle
        const translatedFile = new File([blob], filename, { type: 'text/plain' });
        handleSubtitleFile(translatedFile);

    } catch (error) {
        addLog('error', `❌ Erro na tradução: ${error.message}`);
        showStatus('error', `❌ Erro: ${error.message}`);
    }
}
