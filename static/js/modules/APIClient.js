/**
 * API Client Module
 * Handles all HTTP requests to the Scriptum API
 */

export class APIClient {
    constructor(baseURL = 'http://localhost:5001') {
        this.baseURL = baseURL;
    }

    /**
     * Health check
     */
    async healthCheck() {
        const response = await fetch(`${this.baseURL}/health`);
        return await response.json();
    }

    /**
     * Analyze video file
     * @param {File} videoFile - Video file to analyze
     * @returns {Promise<Object>} Video analysis data
     */
    async analyzeVideo(videoFile) {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch(`${this.baseURL}/analyze-video`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }

        return await response.json();
    }

    /**
     * Recognize movie from filename
     * @param {string} filename - Video filename
     * @param {string} imdbId - Optional IMDB ID
     * @returns {Promise<Object>} Movie data
     */
    async recognizeMovie(filename, imdbId = null) {
        const response = await fetch(`${this.baseURL}/recognize-movie`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                imdb_id: imdbId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Movie recognition failed');
        }

        return await response.json();
    }

    /**
     * Remux MKV to MP4 (fast, no re-encoding)
     * @param {File} videoFile - MKV file
     * @returns {Promise<Blob>} MP4 file blob
     */
    async remuxMkvToMp4(videoFile) {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch(`${this.baseURL}/remux-mkv-to-mp4`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Remux failed');
        }

        return await response.blob();
    }

    /**
     * Convert video to MP4
     * @param {File} videoFile - Video file
     * @param {string} quality - Conversion quality (fast, balanced, high)
     * @returns {Promise<Blob>} MP4 file blob
     */
    async convertToMp4(videoFile, quality = 'balanced') {
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('quality', quality);

        const response = await fetch(`${this.baseURL}/convert-to-mp4`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Conversion failed');
        }

        return await response.blob();
    }

    /**
     * Extract subtitles from MKV
     * @param {File} videoFile - MKV file
     * @returns {Promise<Object>} Subtitle tracks data
     */
    async extractMkvSubtitles(videoFile) {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch(`${this.baseURL}/extract-mkv-subtitles`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Extraction failed');
        }

        return await response.json();
    }

    /**
     * Translate subtitle
     * @param {File} subtitleFile - SRT file
     * @param {string} sourceLang - Source language code (en, pt)
     * @param {string} targetLang - Target language code (en, pt)
     * @param {string} movieContext - Optional movie context
     * @returns {Promise<Blob>} Translated SRT file blob
     */
    async translateSubtitle(subtitleFile, sourceLang, targetLang, movieContext = null) {
        const formData = new FormData();
        formData.append('subtitle', subtitleFile);
        formData.append('source_lang', sourceLang);
        formData.append('target_lang', targetLang);

        if (movieContext) {
            formData.append('movie_context', movieContext);
        }

        const response = await fetch(`${this.baseURL}/translate`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Translation failed');
        }

        return await response.blob();
    }

    /**
     * Sync subtitles using MLX Whisper
     * @param {File} videoFile - Video file
     * @param {File} subtitleFile - SRT file
     * @returns {Promise<Object>} Sync results
     */
    async syncSubtitles(videoFile, subtitleFile) {
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('subtitle', subtitleFile);

        const response = await fetch(`${this.baseURL}/sync`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Sync failed');
        }

        return await response.json();
    }

    /**
     * Search subtitles on OpenSubtitles
     * @param {string} query - Search query
     * @param {string} language - Language code
     * @returns {Promise<Object>} Search results
     */
    async searchSubtitles(query, language = 'pt') {
        const response = await fetch(`${this.baseURL}/search-subtitles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                language: language
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Search failed');
        }

        return await response.json();
    }

    /**
     * Download subtitle from OpenSubtitles
     * @param {number} fileId - OpenSubtitles file ID
     * @returns {Promise<Blob>} Subtitle file blob
     */
    async downloadSubtitle(fileId) {
        const response = await fetch(`${this.baseURL}/download-subtitle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: fileId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Download failed');
        }

        return await response.blob();
    }
}
