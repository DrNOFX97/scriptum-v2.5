/**
 * Scriptum v2.1 - Main Application
 * Entry point that orchestrates all managers
 */

import { APIClient } from './modules/APIClient.js';
import { VideoManager } from './modules/VideoManager.js';
import { SubtitleManager } from './modules/SubtitleManager.js';
import { UIManager } from './modules/UIManager.js';
import { Logger } from './modules/Logger.js';

/**
 * Main Application Class
 */
class ScriptumApp {
    constructor() {
        this.logger = null;
        this.api = null;
        this.videoManager = null;
        this.subtitleManager = null;
        this.uiManager = null;
    }

    /**
     * Initialize application
     */
    async initialize() {
        console.log('🎬 Initializing Scriptum v2.1...');

        try {
            // Initialize Logger first
            const logContainer = document.getElementById('logContainer');
            const statusBar = document.getElementById('statusBar');
            this.logger = new Logger(logContainer, statusBar);

            this.logger.info('🚀 Starting Scriptum v2.1');

            // Initialize API Client
            const apiUrl = window.location.hostname === 'localhost'
                ? 'http://localhost:5001'
                : window.location.origin;

            this.api = new APIClient(apiUrl);
            this.logger.info(`🔌 Connected to API: ${apiUrl}`);

            // Initialize Managers
            this.videoManager = new VideoManager(this.api, this.logger);
            this.subtitleManager = new SubtitleManager(this.api, this.logger);
            this.uiManager = new UIManager(this.logger);

            // Initialize UI
            this.uiManager.initialize();

            // Setup event handlers
            this.setupEventHandlers();

            // Test API connection
            await this.testApiConnection();

            this.logger.success('✅ Scriptum initialized successfully!');

        } catch (error) {
            console.error('Failed to initialize:', error);
            if (this.logger) {
                this.logger.error(`❌ Initialization failed: ${error.message}`);
            }
        }
    }

    /**
     * Test API connection
     */
    async testApiConnection() {
        try {
            const response = await fetch(this.api.baseUrl + '/health');
            const data = await response.json();

            if (data.status === 'healthy') {
                this.logger.success(`✅ API connected: ${data.version}`);
            } else {
                this.logger.warning('⚠️ API health check failed');
            }
        } catch (error) {
            this.logger.error('❌ Cannot connect to API server');
            throw error;
        }
    }

    /**
     * Setup event handlers for file inputs and buttons
     */
    setupEventHandlers() {
        // Video file input
        const videoInput = document.getElementById('videoInput');
        if (videoInput) {
            videoInput.addEventListener('change', (e) => this.handleVideoUpload(e));
        }

        // Subtitle file input
        const subtitleInput = document.getElementById('subtitleInput');
        if (subtitleInput) {
            subtitleInput.addEventListener('change', (e) => this.handleSubtitleUpload(e));
        }

        // Sync button
        const syncBtn = document.getElementById('syncBtn');
        if (syncBtn) {
            syncBtn.addEventListener('click', () => this.handleSync());
        }

        // Translate button
        const translateBtn = document.getElementById('translateBtn');
        if (translateBtn) {
            translateBtn.addEventListener('click', () => this.handleTranslate());
        }

        // Search subtitles button
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleSearchSubtitles());
        }
    }

    /**
     * Handle video file upload
     */
    async handleVideoUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.uiManager.setProcessing(true);

        try {
            // Load and analyze video
            const result = await this.videoManager.loadVideo(file);

            // Update UI state
            this.uiManager.setVideoLoaded(true);

            // Display video info
            this.uiManager.displayVideoInfo(result.info);

            // Try to recognize movie
            const movie = await this.videoManager.recognizeMovie();
            if (movie) {
                this.uiManager.displayMovieInfo(movie);
            }

            // Extract embedded subtitles if MKV
            if (file.name.toLowerCase().endsWith('.mkv')) {
                const embeddedSubs = await this.videoManager.extractMkvSubtitles(file);
                if (embeddedSubs.length > 0) {
                    this.uiManager.displayEmbeddedSubtitles(
                        embeddedSubs,
                        (index) => this.handleLoadEmbeddedSubtitle(embeddedSubs[index])
                    );
                }
            }

        } catch (error) {
            this.logger.error(`❌ Error loading video: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle subtitle file upload
     */
    async handleSubtitleUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.uiManager.setProcessing(true);

        try {
            const result = await this.subtitleManager.loadSubtitle(file);

            // Update UI state
            this.uiManager.setSubtitleLoaded(true);

            // Load into video player if available
            const videoPlayer = this.videoManager.player;
            if (videoPlayer) {
                this.subtitleManager.loadIntoPlayer(videoPlayer, result.entries);
            }

        } catch (error) {
            this.logger.error(`❌ Error loading subtitle: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle subtitle synchronization
     */
    async handleSync() {
        if (!this.videoManager.isLoaded() || !this.subtitleManager.isLoaded()) {
            this.logger.warning('⚠️ Please load both video and subtitle files first');
            return;
        }

        this.uiManager.setProcessing(true);

        try {
            const videoFile = this.videoManager.getVideoFile();
            const result = await this.subtitleManager.syncWithVideo(videoFile);

            // Reload synced subtitle into player
            const videoPlayer = this.videoManager.player;
            if (videoPlayer) {
                this.subtitleManager.loadIntoPlayer(videoPlayer, result.entries);
            }

        } catch (error) {
            this.logger.error(`❌ Sync failed: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle subtitle translation
     */
    async handleTranslate() {
        if (!this.subtitleManager.isLoaded()) {
            this.logger.warning('⚠️ Please load a subtitle file first');
            return;
        }

        const sourceLang = document.getElementById('sourceLang')?.value || 'en';
        const targetLang = document.getElementById('targetLang')?.value || 'pt';

        if (sourceLang === targetLang) {
            this.logger.warning('⚠️ Source and target languages must be different');
            return;
        }

        this.uiManager.setProcessing(true);

        try {
            // Get movie context if available
            const movieInfo = this.uiManager.getState().movieInfo;
            const movieContext = movieInfo ? `${movieInfo.title} (${movieInfo.year})` : null;

            const result = await this.subtitleManager.translate(
                sourceLang,
                targetLang,
                movieContext
            );

            // Reload translated subtitle into player
            const videoPlayer = this.videoManager.player;
            if (videoPlayer) {
                this.subtitleManager.loadIntoPlayer(videoPlayer, result.entries);
            }

        } catch (error) {
            this.logger.error(`❌ Translation failed: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle subtitle search
     */
    async handleSearchSubtitles() {
        if (!this.videoManager.isLoaded()) {
            this.logger.warning('⚠️ Please load a video file first');
            return;
        }

        this.uiManager.setProcessing(true);

        try {
            // Get search query from movie info or filename
            const movieInfo = this.uiManager.getState().movieInfo;
            const query = movieInfo
                ? movieInfo.title
                : this.videoManager.getVideoFile().name;

            const language = document.getElementById('targetLang')?.value || 'pt';

            const subtitles = await this.subtitleManager.searchSubtitles(query, language);

            this.uiManager.displaySubtitleResults(
                subtitles,
                (fileId, filename) => this.handleDownloadSubtitle(fileId, filename)
            );

        } catch (error) {
            this.logger.error(`❌ Search failed: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle subtitle download
     */
    async handleDownloadSubtitle(fileId, filename) {
        this.logger.info(`📥 Downloading: ${filename}...`);
        this.uiManager.setProcessing(true);

        try {
            const result = await this.subtitleManager.downloadSubtitle(fileId, filename);

            // Update UI state
            this.uiManager.setSubtitleLoaded(true);

            // Load into video player if available
            const videoPlayer = this.videoManager.player;
            if (videoPlayer) {
                this.subtitleManager.loadIntoPlayer(videoPlayer, result.entries);
            }

        } catch (error) {
            this.logger.error(`❌ Download failed: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Handle loading embedded subtitle
     */
    async handleLoadEmbeddedSubtitle(subtitle) {
        this.logger.info(`📤 Loading embedded subtitle: ${subtitle.title}`);
        this.uiManager.setProcessing(true);

        try {
            // Decode base64 content
            const content = atob(subtitle.content_base64);
            const blob = new Blob([content], { type: 'text/plain' });
            const file = new File([blob], subtitle.file_name, { type: 'text/plain' });

            const result = await this.subtitleManager.loadSubtitle(file);

            // Update UI state
            this.uiManager.setSubtitleLoaded(true);

            // Load into video player
            const videoPlayer = this.videoManager.player;
            if (videoPlayer) {
                this.subtitleManager.loadIntoPlayer(videoPlayer, result.entries);
            }

        } catch (error) {
            this.logger.error(`❌ Failed to load embedded subtitle: ${error.message}`);
        } finally {
            this.uiManager.setProcessing(false);
        }
    }

    /**
     * Reset application state
     */
    reset() {
        this.videoManager.clear();
        this.subtitleManager.clear();
        this.uiManager.reset();
        this.logger.info('🔄 Application reset');
    }
}

// Initialize app when DOM is ready
let app = null;

document.addEventListener('DOMContentLoaded', async () => {
    app = new ScriptumApp();
    await app.initialize();
});

// Export app instance for debugging
window.scriptumApp = app;
