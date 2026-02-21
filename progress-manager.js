// Progress Manager - Sistema Avançado de Monitoramento de Tradução

class ProgressManager {
    constructor() {
        this.startTime = null;
        this.totalSubtitles = 0;
        this.translatedCount = 0;
        this.currentBatch = 0;
        this.totalBatches = 0;
        this.retries = 0;
        this.speeds = [];
        this.performanceData = {
            timestamps: [],
            speeds: [],
            progress: []
        };
        this.isPaused = false;
        this.chart = null;
        this.streamPaused = false;

        this.initializeElements();
        this.setupEventListeners();
        this.initializeChart();
    }

    initializeElements() {
        // Progress elements
        this.progressFill = document.getElementById('progressFill');
        this.progressPercentage = document.getElementById('progressPercentage');
        this.progressDetails = document.getElementById('progressDetails');
        this.speedInfo = document.getElementById('speedInfo');
        this.etaTime = document.getElementById('etaTime');

        // Stats elements
        this.batchInfo = document.getElementById('batchInfo');
        this.subtitleInfo = document.getElementById('subtitleInfo');
        this.speedStat = document.getElementById('speedStat');
        this.elapsedTime = document.getElementById('elapsedTime');
        this.accuracyStat = document.getElementById('accuracyStat');
        this.retryStat = document.getElementById('retryStat');

        // Live stream elements
        this.liveTranslations = document.getElementById('liveTranslations');

        // Optional elements
        this.statsGrid = document.getElementById('statsGrid');
        this.performanceChart = document.getElementById('performanceChart');
        this.livePreview = document.getElementById('livePreview');
    }

    setupEventListeners() {
        // Toggle options
        const toggleBtn = document.getElementById('toggleOptionsBtn');
        const viewOptions = document.getElementById('viewOptions');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                viewOptions.classList.toggle('hidden');
            });
        }

        // View options checkboxes
        const showLiveStream = document.getElementById('showLiveStream');
        const showStats = document.getElementById('showStats');
        const showPerformance = document.getElementById('showPerformance');
        const autoScroll = document.getElementById('autoScroll');

        if (showLiveStream) {
            showLiveStream.addEventListener('change', (e) => {
                this.livePreview.classList.toggle('hidden', !e.target.checked);
            });
        }

        if (showStats) {
            showStats.addEventListener('change', (e) => {
                this.statsGrid.classList.toggle('hidden', !e.target.checked);
            });
        }

        if (showPerformance) {
            showPerformance.addEventListener('change', (e) => {
                this.performanceChart.classList.toggle('hidden', !e.target.checked);
            });
        }

        // Pause/Resume stream
        const pauseBtn = document.getElementById('pauseStreamBtn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.streamPaused = !this.streamPaused;
                pauseBtn.innerHTML = this.streamPaused ?
                    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M4 2l8 5-8 5V2z" fill="currentColor"/></svg> Retomar' :
                    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="3" y="2" width="3" height="10" fill="currentColor" rx="1"/><rect x="8" y="2" width="3" height="10" fill="currentColor" rx="1"/></svg> Pausar';
            });
        }
    }

    initializeChart() {
        const canvas = document.getElementById('perfCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.chartContext = ctx;
        this.chartWidth = canvas.width;
        this.chartHeight = canvas.height;

        // Draw initial empty chart
        this.drawChart();
    }

    drawChart() {
        if (!this.chartContext) return;

        const ctx = this.chartContext;
        const width = this.chartWidth;
        const height = this.chartHeight;
        const padding = 40;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Background
        ctx.fillStyle = '#f8f9ff';
        ctx.fillRect(0, 0, width, height);

        // Grid lines
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;

        for (let i = 0; i <= 5; i++) {
            const y = padding + (height - 2 * padding) * i / 5;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }

        // Axes
        ctx.strokeStyle = '#999';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        // Plot data if available
        if (this.performanceData.timestamps.length > 1) {
            this.plotData(ctx, width, height, padding);
        }
    }

    plotData(ctx, width, height, padding) {
        const data = this.performanceData;
        const maxPoints = 50;
        const startIdx = Math.max(0, data.timestamps.length - maxPoints);

        const timestamps = data.timestamps.slice(startIdx);
        const speeds = data.speeds.slice(startIdx);
        const progress = data.progress.slice(startIdx);

        if (timestamps.length < 2) return;

        const maxSpeed = Math.max(...speeds, 1);
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;

        // Draw speed line
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 3;
        ctx.beginPath();

        timestamps.forEach((_, i) => {
            const x = padding + (chartWidth * i / (timestamps.length - 1));
            const y = height - padding - (speeds[i] / maxSpeed * chartHeight);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();

        // Draw progress line
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.beginPath();

        timestamps.forEach((_, i) => {
            const x = padding + (chartWidth * i / (timestamps.length - 1));
            const y = height - padding - (progress[i] / 100 * chartHeight);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    }

    start(totalSubtitles, totalBatches) {
        this.startTime = Date.now();
        this.totalSubtitles = totalSubtitles;
        this.totalBatches = totalBatches;
        this.translatedCount = 0;
        this.currentBatch = 0;
        this.retries = 0;

        this.updateElapsedTime();
        this.elapsedTimeInterval = setInterval(() => this.updateElapsedTime(), 1000);
    }

    updateProgress(batch, translated) {
        this.currentBatch = batch;
        this.translatedCount = translated;

        const percentage = Math.round((translated / this.totalSubtitles) * 100);

        // Update progress bar
        this.progressFill.style.width = percentage + '%';
        this.progressPercentage.textContent = percentage + '%';
        this.progressDetails.textContent = `${translated} de ${this.totalSubtitles} legendas traduzidas`;

        // Update batch info
        this.batchInfo.textContent = `${batch}/${this.totalBatches}`;
        this.subtitleInfo.textContent = `${translated}/${this.totalSubtitles}`;

        // Calculate speed and ETA
        this.calculateSpeedAndETA();

        // Update chart
        this.updatePerformanceData(percentage);
    }

    calculateSpeedAndETA() {
        if (!this.startTime) return;

        const elapsed = (Date.now() - this.startTime) / 1000; // seconds
        const speed = this.translatedCount / (elapsed / 60); // per minute
        const speedPerSec = this.translatedCount / elapsed; // per second

        this.speeds.push(speedPerSec);
        if (this.speeds.length > 10) this.speeds.shift();

        const avgSpeed = this.speeds.reduce((a, b) => a + b, 0) / this.speeds.length;

        // Update speed displays
        this.speedInfo.textContent = `${Math.round(speed)} legendas/min`;
        this.speedStat.textContent = `${avgSpeed.toFixed(1)}/s`;

        // Calculate ETA
        const remaining = this.totalSubtitles - this.translatedCount;
        const etaSeconds = remaining / avgSpeed;

        if (etaSeconds > 0 && isFinite(etaSeconds)) {
            const minutes = Math.floor(etaSeconds / 60);
            const seconds = Math.floor(etaSeconds % 60);
            this.etaTime.textContent = `${minutes}m ${seconds}s restantes`;
        } else {
            this.etaTime.textContent = 'Calculando...';
        }
    }

    updateElapsedTime() {
        if (!this.startTime) return;

        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        this.elapsedTime.textContent =
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    updatePerformanceData(percentage) {
        const now = Date.now();
        const avgSpeed = this.speeds.reduce((a, b) => a + b, 0) / this.speeds.length || 0;

        this.performanceData.timestamps.push(now);
        this.performanceData.speeds.push(avgSpeed);
        this.performanceData.progress.push(percentage);

        // Keep last 50 data points
        if (this.performanceData.timestamps.length > 50) {
            this.performanceData.timestamps.shift();
            this.performanceData.speeds.shift();
            this.performanceData.progress.shift();
        }

        this.drawChart();
    }

    addLiveTranslation(original, translated, timeCode) {
        if (this.streamPaused) return;

        const item = document.createElement('div');
        item.className = 'translation-item';
        item.innerHTML = `
            <div class="subtitle-time">${timeCode || ''}</div>
            <div class="original">${this.escapeHtml(original)}</div>
            <div class="translated">${this.escapeHtml(translated)}</div>
        `;

        this.liveTranslations.insertBefore(item, this.liveTranslations.firstChild);

        // Keep only last 20 items
        while (this.liveTranslations.children.length > 20) {
            this.liveTranslations.removeChild(this.liveTranslations.lastChild);
        }

        // Auto scroll if enabled
        const autoScroll = document.getElementById('autoScroll');
        if (autoScroll && autoScroll.checked) {
            this.liveTranslations.scrollTop = 0;
        }
    }

    incrementRetries() {
        this.retries++;
        this.retryStat.textContent = this.retries;
    }

    updateAccuracy(accuracy) {
        this.accuracyStat.textContent = accuracy + '%';
    }

    complete() {
        if (this.elapsedTimeInterval) {
            clearInterval(this.elapsedTimeInterval);
        }

        this.etaTime.textContent = 'Concluído!';
        this.progressFill.style.width = '100%';
        this.progressPercentage.textContent = '100%';
    }

    reset() {
        this.startTime = null;
        this.translatedCount = 0;
        this.currentBatch = 0;
        this.retries = 0;
        this.speeds = [];
        this.performanceData = {
            timestamps: [],
            speeds: [],
            progress: []
        };

        if (this.elapsedTimeInterval) {
            clearInterval(this.elapsedTimeInterval);
        }

        if (this.liveTranslations) {
            this.liveTranslations.innerHTML = '';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize global progress manager
let progressManager = null;

function initProgressManager() {
    progressManager = new ProgressManager();
    return progressManager;
}
