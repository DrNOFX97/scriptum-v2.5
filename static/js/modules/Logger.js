/**
 * Logger Module
 * Handles application logging with different levels and visual feedback
 */

export class Logger {
    constructor(logContainer, statusContainer) {
        this.logContainer = logContainer;
        this.statusContainer = statusContainer;
        this.logs = [];
        this.maxLogs = 100;
    }

    /**
     * Log info message
     */
    info(message) {
        this.log('info', message, 'ℹ️');
    }

    /**
     * Log success message
     */
    success(message) {
        this.log('success', message, '✅');
    }

    /**
     * Log warning message
     */
    warning(message) {
        this.log('warning', message, '⚠️');
    }

    /**
     * Log error message
     */
    error(message) {
        this.log('error', message, '❌');
    }

    /**
     * Internal log method
     */
    log(level, message, icon) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            level,
            message,
            icon,
            timestamp,
            id: Date.now()
        };

        this.logs.push(logEntry);

        // Limit log history
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        // Add to DOM
        if (this.logContainer) {
            this.addLogToDOM(logEntry);
        }

        // Update status
        if (this.statusContainer) {
            this.updateStatus(level, message, icon);
        }

        // Console log
        console.log(`[${level.toUpperCase()}] ${message}`);
    }

    /**
     * Add log entry to DOM
     */
    addLogToDOM(entry) {
        const logItem = document.createElement('div');
        logItem.className = `log-item log-${entry.level}`;
        logItem.innerHTML = `
            <span class="log-time">${entry.timestamp}</span>
            <span class="log-icon">${entry.icon}</span>
            <span class="log-message">${this.escapeHtml(entry.message)}</span>
        `;

        this.logContainer.appendChild(logItem);

        // Auto-scroll to bottom
        this.logContainer.scrollTop = this.logContainer.scrollHeight;

        // Fade in animation
        setTimeout(() => logItem.classList.add('visible'), 10);

        // Remove old logs
        while (this.logContainer.children.length > this.maxLogs) {
            this.logContainer.removeChild(this.logContainer.firstChild);
        }
    }

    /**
     * Update status bar
     */
    updateStatus(level, message, icon) {
        const colors = {
            info: '#2196F3',
            success: '#4CAF50',
            warning: '#FF9800',
            error: '#F44336'
        };

        this.statusContainer.style.background = colors[level] || colors.info;
        this.statusContainer.innerHTML = `
            <span style="font-size: 1.2em; margin-right: 10px;">${icon}</span>
            <span>${this.escapeHtml(message)}</span>
        `;

        this.statusContainer.style.display = 'block';

        // Auto-hide status after 5 seconds (except errors)
        if (level !== 'error') {
            setTimeout(() => {
                this.statusContainer.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * Clear all logs
     */
    clear() {
        this.logs = [];
        if (this.logContainer) {
            this.logContainer.innerHTML = '';
        }
    }

    /**
     * Get log history
     */
    getHistory() {
        return this.logs;
    }

    /**
     * Export logs as text
     */
    exportLogs() {
        let text = '=== Scriptum Log Export ===\n\n';
        for (const log of this.logs) {
            text += `[${log.timestamp}] ${log.level.toUpperCase()}: ${log.message}\n`;
        }
        return text;
    }

    /**
     * Download logs as file
     */
    downloadLogs() {
        const text = this.exportLogs();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scriptum-logs-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
