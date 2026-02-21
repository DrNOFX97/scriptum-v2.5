/**
 * Subtitle Manager Module
 * Handles subtitle file operations, synchronization, and translation
 */

export class SubtitleManager {
    constructor(apiClient, logger) {
        this.api = apiClient;
        this.logger = logger;
        this.currentSubtitle = null;
        this.subtitleTrack = null;
    }

    /**
     * Load subtitle file
     */
    async loadSubtitle(file) {
        if (!file.name.endsWith('.srt')) {
            throw new Error('Only SRT format is supported');
        }

        this.currentSubtitle = file;
        this.logger.info(`📄 Loading subtitle: ${file.name}`);

        try {
            const text = await file.text();
            const entries = this.parseSRT(text);

            this.logger.success(`✅ Loaded ${entries.length} subtitle entries`);

            return {
                success: true,
                entries: entries,
                count: entries.length
            };

        } catch (error) {
            this.logger.error(`❌ Error loading subtitle: ${error.message}`);
            throw error;
        }
    }

    /**
     * Parse SRT content
     */
    parseSRT(content) {
        const entries = [];
        const blocks = content.trim().split('\n\n');

        for (const block of blocks) {
            const lines = block.trim().split('\n');
            if (lines.length >= 3) {
                entries.push({
                    index: parseInt(lines[0]),
                    timestamp: lines[1],
                    text: lines.slice(2).join('\n')
                });
            }
        }

        return entries;
    }

    /**
     * Search subtitles on OpenSubtitles
     */
    async searchSubtitles(query, language = 'pt', limit = 10) {
        this.logger.info(`🔍 Searching subtitles for: ${query}`);

        try {
            const result = await this.api.searchSubtitles(query, language, limit);

            if (result.success && result.count > 0) {
                this.logger.success(`✅ Found ${result.count} subtitle(s)`);
                return result.subtitles;
            } else {
                this.logger.warning('⚠️  No subtitles found');
                return [];
            }

        } catch (error) {
            this.logger.error(`❌ Search error: ${error.message}`);
            return [];
        }
    }

    /**
     * Download subtitle from OpenSubtitles
     */
    async downloadSubtitle(fileId, filename) {
        this.logger.info(`📥 Downloading subtitle (ID: ${fileId})...`);

        try {
            const blob = await this.api.downloadSubtitle(fileId);
            const file = new File([blob], filename || `subtitle_${fileId}.srt`, {
                type: 'text/plain'
            });

            this.logger.success('✅ Subtitle downloaded');

            // Auto-load downloaded subtitle
            return await this.loadSubtitle(file);

        } catch (error) {
            this.logger.error(`❌ Download error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Synchronize subtitle with video
     */
    async syncWithVideo(videoFile) {
        if (!this.currentSubtitle) {
            throw new Error('No subtitle loaded');
        }

        if (!videoFile) {
            throw new Error('No video file provided');
        }

        this.logger.info('🤖 Starting MLX Whisper synchronization...');
        this.logger.warning('⏱️  This may take 5-10 minutes...');

        try {
            const syncedBlob = await this.api.syncSubtitles(videoFile, this.currentSubtitle);

            const syncedFile = new File(
                [syncedBlob],
                this.currentSubtitle.name.replace('.srt', '_synced.srt'),
                { type: 'text/plain' }
            );

            this.logger.success('✅ Synchronization complete!');

            // Download synced subtitle
            this.downloadFile(syncedBlob, syncedFile.name);

            // Load synced subtitle
            return await this.loadSubtitle(syncedFile);

        } catch (error) {
            this.logger.error(`❌ Sync error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Translate subtitle
     */
    async translate(sourceLang, targetLang, movieContext = null) {
        if (!this.currentSubtitle) {
            throw new Error('No subtitle loaded');
        }

        if (sourceLang === targetLang) {
            throw new Error('Source and target languages must be different');
        }

        this.logger.info(`🌐 Translating ${sourceLang.toUpperCase()} → ${targetLang.toUpperCase()}...`);

        if (movieContext) {
            this.logger.info(`📽️  Context: ${movieContext}`);
        }

        try {
            const translatedBlob = await this.api.translateSubtitle(
                this.currentSubtitle,
                sourceLang,
                targetLang,
                movieContext
            );

            const translatedFile = new File(
                [translatedBlob],
                this.currentSubtitle.name.replace('.srt', `_${targetLang}.srt`),
                { type: 'text/plain' }
            );

            this.logger.success('✅ Translation complete!');

            // Download translated subtitle
            this.downloadFile(translatedBlob, translatedFile.name);

            // Load translated subtitle
            return await this.loadSubtitle(translatedFile);

        } catch (error) {
            this.logger.error(`❌ Translation error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Load subtitle into video player
     */
    loadIntoPlayer(videoPlayer, entries) {
        if (!videoPlayer) {
            this.logger.warning('⚠️  No video player available');
            return;
        }

        // Remove existing subtitle track
        if (this.subtitleTrack) {
            videoPlayer.removeChild(this.subtitleTrack);
        }

        // Create VTT from SRT entries
        const vttContent = this.convertToVTT(entries);
        const vttBlob = new Blob([vttContent], { type: 'text/vtt' });
        const vttUrl = URL.createObjectURL(vttBlob);

        // Create track element
        this.subtitleTrack = document.createElement('track');
        this.subtitleTrack.kind = 'subtitles';
        this.subtitleTrack.label = 'Subtitles';
        this.subtitleTrack.srclang = 'pt';
        this.subtitleTrack.src = vttUrl;
        this.subtitleTrack.default = true;

        videoPlayer.appendChild(this.subtitleTrack);

        // Enable text track
        if (videoPlayer.textTracks.length > 0) {
            videoPlayer.textTracks[0].mode = 'showing';
        }

        this.logger.success('✅ Subtitle loaded into player');
    }

    /**
     * Convert SRT to VTT format
     */
    convertToVTT(entries) {
        let vtt = 'WEBVTT\n\n';

        for (const entry of entries) {
            const timestamp = entry.timestamp.replace(/,/g, '.');
            vtt += `${timestamp}\n${entry.text}\n\n`;
        }

        return vtt;
    }

    /**
     * Download file helper
     */
    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Get current subtitle file
     */
    getSubtitleFile() {
        return this.currentSubtitle;
    }

    /**
     * Check if subtitle is loaded
     */
    isLoaded() {
        return this.currentSubtitle !== null;
    }

    /**
     * Clear current subtitle
     */
    clear() {
        if (this.subtitleTrack) {
            URL.revokeObjectURL(this.subtitleTrack.src);
        }
        this.currentSubtitle = null;
        this.subtitleTrack = null;
    }
}
