/**
 * Video Manager Module
 * Handles video file operations, analysis, and player management
 */

export class VideoManager {
    constructor(apiClient, logger) {
        this.api = apiClient;
        this.logger = logger;
        this.currentVideo = null;
        this.videoInfo = null;
        this.player = null;
    }

    /**
     * Load and analyze video file
     */
    async loadVideo(file) {
        this.currentVideo = file;
        this.logger.info(`📹 Loading video: ${file.name}`);

        try {
            // Initialize player
            await this.initializePlayer(file);

            // Analyze video
            this.logger.info('📊 Analyzing video...');
            const analysis = await this.api.analyzeVideo(file);

            this.videoInfo = analysis.video_info;

            this.logger.success('✅ Video loaded and analyzed');
            this.logger.info(`Format: ${this.videoInfo.format}, Resolution: ${this.videoInfo.resolution}, Duration: ${this.videoInfo.duration_formatted}`);

            return {
                success: true,
                info: this.videoInfo,
                canRemux: analysis.can_remux_to_mp4,
                canConvert: analysis.can_convert_to_mp4
            };

        } catch (error) {
            this.logger.error(`❌ Error loading video: ${error.message}`);
            throw error;
        }
    }

    /**
     * Initialize video player
     */
    async initializePlayer(file) {
        const videoContainer = document.getElementById('videoContainer');

        // Check if MKV
        if (file.name.toLowerCase().endsWith('.mkv')) {
            this.logger.warning('⚡ MKV detected - converting for playback...');

            videoContainer.innerHTML = `
                <div style="aspect-ratio: 16/9; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; padding: 20px;">
                    <div style="font-size: 3em; margin-bottom: 20px;">⚡</div>
                    <div style="font-size: 1.4em; font-weight: bold;">Converting MKV for Playback</div>
                    <div style="margin-top: 20px;">
                        <div class="spinner" style="border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                    </div>
                </div>
            `;

            try {
                const mp4Blob = await this.api.remuxMkvToMp4(file);
                const mp4File = new File([mp4Blob], file.name.replace(/\.mkv$/i, '.mp4'), {
                    type: 'video/mp4'
                });

                await this.createPlayer(mp4File, videoContainer);
                this.logger.success('✅ MKV converted successfully');

            } catch (error) {
                this.logger.error('❌ MKV conversion failed');
                videoContainer.innerHTML = `
                    <div style="aspect-ratio: 16/9; background: #f44336; display: flex; align-items: center; justify-content: center; color: white;">
                        <div style="text-align: center; padding: 20px;">
                            <div style="font-size: 3em;">❌</div>
                            <div>Cannot play this video format</div>
                        </div>
                    </div>
                `;
                throw error;
            }

        } else {
            // Direct playback for supported formats
            await this.createPlayer(file, videoContainer);
        }
    }

    /**
     * Create video player instance
     */
    async createPlayer(file, container) {
        const videoUrl = URL.createObjectURL(file);

        container.innerHTML = `
            <video id="videoPlayer"
                   controls
                   style="width: 100%; height: auto; border-radius: 8px;"
                   preload="metadata">
                <source src="${videoUrl}" type="${file.type}">
            </video>
        `;

        this.player = document.getElementById('videoPlayer');

        // Setup player events
        this.player.addEventListener('loadedmetadata', () => {
            this.logger.info(`⏱️  Duration: ${this.formatDuration(this.player.duration)}`);
        });

        this.player.addEventListener('error', () => {
            this.logger.error('❌ Video playback error');
        });
    }

    /**
     * Extract embedded subtitles from MKV
     */
    async extractMkvSubtitles(file) {
        if (!file.name.toLowerCase().endsWith('.mkv')) {
            this.logger.warning('⚠️  Not an MKV file');
            return [];
        }

        this.logger.info('📤 Extracting embedded subtitles...');

        try {
            const result = await this.api.extractMkvSubtitles(file);

            if (result.success && result.count > 0) {
                this.logger.success(`✅ Found ${result.count} embedded subtitle(s)`);
                return result.subtitles;
            } else {
                this.logger.info('ℹ️  No embedded subtitles found');
                return [];
            }

        } catch (error) {
            this.logger.error(`❌ Extraction error: ${error.message}`);
            return [];
        }
    }

    /**
     * Recognize movie from filename
     */
    async recognizeMovie(imdbId = null) {
        if (!this.currentVideo) {
            throw new Error('No video loaded');
        }

        this.logger.info('🎬 Recognizing movie...');

        try {
            const result = await this.api.recognizeMovie(this.currentVideo.name, imdbId);

            if (result.success) {
                this.logger.success(`✅ Found: ${result.movie.title} (${result.movie.year})`);
                return result.movie;
            } else {
                this.logger.warning('⚠️  Movie not found');
                return null;
            }

        } catch (error) {
            this.logger.error(`❌ Recognition error: ${error.message}`);
            return null;
        }
    }

    /**
     * Get current playback time
     */
    getCurrentTime() {
        return this.player ? this.player.currentTime : 0;
    }

    /**
     * Seek to specific time
     */
    seekTo(time) {
        if (this.player) {
            this.player.currentTime = time;
        }
    }

    /**
     * Format duration in HH:MM:SS
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else {
            return `${minutes}m ${secs}s`;
        }
    }

    /**
     * Get current video file
     */
    getVideoFile() {
        return this.currentVideo;
    }

    /**
     * Get video info
     */
    getVideoInfo() {
        return this.videoInfo;
    }

    /**
     * Check if video is loaded
     */
    isLoaded() {
        return this.currentVideo !== null;
    }

    /**
     * Clear current video
     */
    clear() {
        if (this.player) {
            URL.revokeObjectURL(this.player.src);
        }
        this.currentVideo = null;
        this.videoInfo = null;
        this.player = null;
    }
}
