/**
 * UI Manager Module
 * Handles UI state, button states, and user interactions
 */

export class UIManager {
    constructor(logger) {
        this.logger = logger;
        this.elements = {};
        this.state = {
            videoLoaded: false,
            subtitleLoaded: false,
            processing: false,
            movieInfo: null
        };
    }

    /**
     * Initialize UI elements
     */
    initialize() {
        // Get all UI elements
        this.elements = {
            // Buttons
            syncBtn: document.getElementById('syncBtn'),
            translateBtn: document.getElementById('translateBtn'),
            searchBtn: document.getElementById('searchBtn'),
            clearLogsBtn: document.getElementById('clearLogsBtn'),

            // Inputs
            videoInput: document.getElementById('videoInput'),
            subtitleInput: document.getElementById('subtitleInput'),
            sourceLang: document.getElementById('sourceLang'),
            targetLang: document.getElementById('targetLang'),

            // Containers
            videoContainer: document.getElementById('videoContainer'),
            movieInfoPanel: document.getElementById('movieInfoPanel'),
            analysisPanel: document.getElementById('analysisPanel'),
            subtitlesList: document.getElementById('subtitlesList'),

            // Status
            statusBar: document.getElementById('statusBar'),
            logContainer: document.getElementById('logContainer')
        };

        this.updateButtonStates();
        this.setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Clear logs button
        if (this.elements.clearLogsBtn) {
            this.elements.clearLogsBtn.addEventListener('click', () => {
                this.logger.clear();
            });
        }

        // Language selector validation
        if (this.elements.sourceLang && this.elements.targetLang) {
            const validateLanguages = () => {
                if (this.elements.sourceLang.value === this.elements.targetLang.value) {
                    this.logger.warning('⚠️ Source and target languages must be different');
                }
            };

            this.elements.sourceLang.addEventListener('change', validateLanguages);
            this.elements.targetLang.addEventListener('change', validateLanguages);
        }
    }

    /**
     * Update button states based on current state
     */
    updateButtonStates() {
        const bothLoaded = this.state.videoLoaded && this.state.subtitleLoaded;

        // Sync button
        if (this.elements.syncBtn) {
            this.elements.syncBtn.disabled = !bothLoaded || this.state.processing;
        }

        // Translate button
        if (this.elements.translateBtn) {
            this.elements.translateBtn.disabled = !this.state.subtitleLoaded || this.state.processing;
        }

        // Search button
        if (this.elements.searchBtn) {
            this.elements.searchBtn.disabled = !this.state.videoLoaded || this.state.processing;
        }
    }

    /**
     * Set video loaded state
     */
    setVideoLoaded(loaded) {
        this.state.videoLoaded = loaded;
        this.updateButtonStates();

        if (loaded) {
            this.showElement('analysisPanel');
        }
    }

    /**
     * Set subtitle loaded state
     */
    setSubtitleLoaded(loaded) {
        this.state.subtitleLoaded = loaded;
        this.updateButtonStates();
    }

    /**
     * Set processing state
     */
    setProcessing(processing) {
        this.state.processing = processing;
        this.updateButtonStates();

        // Show/hide loading indicator
        if (processing) {
            this.showLoadingIndicator();
        } else {
            this.hideLoadingIndicator();
        }
    }

    /**
     * Display movie information
     */
    displayMovieInfo(movie) {
        if (!this.elements.movieInfoPanel || !movie) return;

        this.state.movieInfo = movie;

        this.elements.movieInfoPanel.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: start;">
                ${movie.poster ? `
                    <img src="${movie.poster}"
                         alt="${movie.title}"
                         style="width: 150px; height: 225px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                ` : ''}
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 10px 0; font-size: 1.5em; color: #333;">
                        ${movie.title} (${movie.year})
                    </h3>
                    ${movie.rating ? `
                        <div style="margin: 10px 0; color: #FF9800; font-weight: bold;">
                            ⭐ ${movie.rating}/10
                        </div>
                    ` : ''}
                    ${movie.overview ? `
                        <p style="color: #666; line-height: 1.6; margin: 10px 0;">
                            ${movie.overview}
                        </p>
                    ` : ''}
                </div>
            </div>
        `;

        this.showElement('movieInfoPanel');
    }

    /**
     * Display video information
     */
    displayVideoInfo(info) {
        const infoHtml = `
            <div class="info-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                <div class="info-card">
                    <div class="info-label">Format</div>
                    <div class="info-value">${info.format}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Resolution</div>
                    <div class="info-value">${info.resolution}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Duration</div>
                    <div class="info-value">${info.duration_formatted}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Codec</div>
                    <div class="info-value">${info.codec}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">FPS</div>
                    <div class="info-value">${info.fps}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Size</div>
                    <div class="info-value">${info.size_mb} MB</div>
                </div>
            </div>
        `;

        const videoInfoContainer = document.getElementById('videoInfoContainer');
        if (videoInfoContainer) {
            videoInfoContainer.innerHTML = infoHtml;
        }
    }

    /**
     * Display subtitle search results
     */
    displaySubtitleResults(subtitles, onDownload) {
        if (!this.elements.subtitlesList || !subtitles || subtitles.length === 0) {
            if (this.elements.subtitlesList) {
                this.elements.subtitlesList.innerHTML = '<p style="text-align: center; color: #999;">No subtitles found</p>';
            }
            return;
        }

        const html = subtitles.map(sub => `
            <div class="subtitle-item" style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s;"
                 onmouseover="this.style.background='#f5f5f5'; this.style.borderColor='#667eea'"
                 onmouseout="this.style.background='white'; this.style.borderColor='#e0e0e0'"
                 onclick="window.downloadSubtitle(${sub.file_id}, '${sub.name}')">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: #333; margin-bottom: 5px;">
                            📄 ${sub.name}
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            Language: ${sub.language} • Downloads: ${sub.downloads} • Rating: ${sub.rating}/10
                        </div>
                    </div>
                    <button style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Download
                    </button>
                </div>
            </div>
        `).join('');

        this.elements.subtitlesList.innerHTML = html;

        // Store callback globally
        window.downloadSubtitle = onDownload;
    }

    /**
     * Display embedded subtitles
     */
    displayEmbeddedSubtitles(subtitles, onLoad) {
        if (!this.elements.subtitlesList || !subtitles || subtitles.length === 0) {
            return;
        }

        const html = `
            <div style="margin-bottom: 20px;">
                <h4 style="color: #667eea; margin-bottom: 10px;">📤 Embedded Subtitles</h4>
                ${subtitles.map((sub, idx) => `
                    <div class="subtitle-item" style="padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 8px; cursor: pointer;"
                         onclick="window.loadEmbeddedSubtitle(${idx})">
                        <div style="font-weight: 500;">${sub.title} (${sub.language})</div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 4px;">
                            Format: ${sub.codec} • Track ${sub.index + 1}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        this.elements.subtitlesList.insertAdjacentHTML('afterbegin', html);

        // Store callback globally
        window.loadEmbeddedSubtitle = onLoad;
    }

    /**
     * Show element
     */
    showElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
            element.classList.add('active');
        }
    }

    /**
     * Hide element
     */
    hideElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
            element.classList.remove('active');
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        let indicator = document.getElementById('loadingIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'loadingIndicator';
            indicator.innerHTML = `
                <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9999;">
                    <div style="background: white; padding: 30px; border-radius: 12px; text-align: center;">
                        <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                        <div style="font-size: 1.2em; color: #333;">Processing...</div>
                    </div>
                </div>
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'flex';
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Reset UI to initial state
     */
    reset() {
        this.state = {
            videoLoaded: false,
            subtitleLoaded: false,
            processing: false,
            movieInfo: null
        };

        this.updateButtonStates();
        this.hideElement('analysisPanel');
        this.hideElement('movieInfoPanel');

        if (this.elements.subtitlesList) {
            this.elements.subtitlesList.innerHTML = '';
        }
    }
}
