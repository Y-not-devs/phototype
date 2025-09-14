/**
 * Utility functions for Phototype application
 */
import { CONFIG, MESSAGES } from './config.js';

export class Utils {
    /**
     * Format file size in human readable format
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Validate file type and size
     * @param {File} file - File object to validate
     * @returns {Object} Validation result with isValid and error message
     */
    static validateFile(file) {
        if (!file) {
            return { isValid: false, error: MESSAGES.upload.noFile };
        }

        // Check file type
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!CONFIG.ALLOWED_EXTENSIONS.includes(fileExtension)) {
            return { isValid: false, error: MESSAGES.upload.invalidFile };
        }

        // Check file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            return { isValid: false, error: MESSAGES.upload.fileTooBig };
        }

        return { isValid: true, error: null };
    }

    /**
     * Show notification to user
     * @param {string} message - Message to display
     * @param {string} type - Notification type ('success', 'error', 'info')
     * @param {number} duration - Duration in milliseconds
     */
    static showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = this.getNotificationClasses(type);
        
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="material-symbols-outlined mr-2">${this.getNotificationIcon(type)}</span>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <span class="material-symbols-outlined text-sm">close</span>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    /**
     * Get CSS classes for notification based on type
     * @param {string} type - Notification type
     * @returns {string} CSS classes
     */
    static getNotificationClasses(type) {
        const baseClasses = 'fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 text-white';
        const typeClasses = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            info: 'bg-blue-600',
            warning: 'bg-yellow-600'
        };
        return `${baseClasses} ${typeClasses[type] || typeClasses.info}`;
    }

    /**
     * Get icon for notification based on type
     * @param {string} type - Notification type
     * @returns {string} Icon name
     */
    static getNotificationIcon(type) {
        const icons = {
            success: 'check_circle',
            error: 'error',
            info: 'info',
            warning: 'warning'
        };
        return icons[type] || icons.info;
    }

    /**
     * Create a loading spinner element
     * @returns {HTMLElement} Loading spinner element
     */
    static createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white';
        return spinner;
    }

    /**
     * Debounce function to limit function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Sanitize HTML string to prevent XSS
     * @param {string} str - String to sanitize
     * @returns {string} Sanitized string
     */
    static sanitizeHtml(str) {
        if (str === null || str === undefined) return '';
        const temp = document.createElement('div');
        temp.textContent = String(str);
        return temp.innerHTML;
    }

    /**
     * Escape HTML string to prevent XSS (alias for sanitizeHtml)
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    static escapeHtml(str) {
        return this.sanitizeHtml(str);
    }
}