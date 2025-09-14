/**
 * UI Components for Phototype application
 */
import { CONFIG } from './config.js';
import { Utils } from './utils.js';

export class Components {
    /**
     * Create a card component for displaying JSON files
     * @param {Object} file - File information
     * @returns {string} Card HTML string
     */
    static createFileCard(file) {
        return `
            <div class="bg-gray-700 rounded-xl shadow-lg border border-gray-600 hover:border-primary transition-all duration-200 cursor-pointer group" onclick="window.location.href='/view/${encodeURIComponent(file.filename || file.name)}'">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="bg-primary/20 p-3 rounded-lg group-hover:bg-primary/30 transition-colors duration-200">
                            <span class="material-symbols-outlined text-primary">description</span>
                        </div>
                        <span class="text-xs text-gray-400 bg-gray-600 px-2 py-1 rounded-full">JSON</span>
                    </div>
                    <h3 class="font-semibold text-gray-100 mb-2 group-hover:text-primary transition-colors duration-200">${Utils.sanitizeHtml(file.name || file.filename)}</h3>
                    <p class="text-gray-400 text-sm mb-4">Contract data visualization ready</p>
                    <div class="flex items-center justify-between text-xs text-gray-500">
                        <span class="flex items-center">
                            <span class="material-symbols-outlined text-xs mr-1">schedule</span>
                            ${file.modified || 'Recently added'}
                        </span>
                        <span class="flex items-center">
                            <span class="material-symbols-outlined text-xs mr-1">storage</span>
                            ${file.size ? Utils.formatFileSize(file.size) : 'N/A'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Create an empty state component
     * @param {string} title - Title for empty state
     * @param {string} message - Message for empty state
     * @param {string} icon - Material icon name
     * @returns {HTMLElement} Empty state element
     */
    static createEmptyState(title, message, icon = 'folder_open') {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-12';
        
        emptyState.innerHTML = `
            <div class="mb-6">
                <div class="bg-gray-700 p-6 rounded-full inline-block">
                    <span class="material-symbols-outlined text-gray-400 text-4xl">${icon}</span>
                </div>
            </div>
            <h3 class="text-xl font-semibold text-gray-100 mb-2">${Utils.sanitizeHtml(title)}</h3>
            <p class="text-gray-400 max-w-md mx-auto">${Utils.sanitizeHtml(message)}</p>
        `;
        
        return emptyState;
    }

    /**
     * Create a contract field display component
     * @param {string} label - Field label
     * @param {string} value - Field value
     * @param {string} type - Field type ('default', 'highlight', 'tag')
     * @returns {HTMLElement} Field display element
     */
    static createFieldDisplay(label, value, type = 'default') {
        const field = document.createElement('div');
        
        const baseClasses = 'rounded-lg p-4';
        const typeClasses = {
            default: 'bg-gray-600',
            highlight: 'bg-accent/10 border border-accent/20',
            tag: 'bg-primary/10 border border-primary/20'
        };
        
        field.className = `${baseClasses} ${typeClasses[type] || typeClasses.default}`;
        
        const labelColor = type === 'highlight' ? 'text-accent' : type === 'tag' ? 'text-primary' : 'text-gray-300';
        const valueColor = type === 'highlight' ? 'text-gray-100' : 'text-gray-100';
        
        field.innerHTML = `
            <label class="text-sm font-medium ${labelColor} uppercase tracking-wide">${Utils.sanitizeHtml(label)}</label>
            <p class="text-base ${valueColor} mt-1">${Utils.sanitizeHtml(value)}</p>
        `;
        
        return field;
    }

    /**
     * Create a document tag component
     * @param {string} document - Document name
     * @returns {HTMLElement} Tag element
     */
    static createDocumentTag(document) {
        const tag = document.createElement('span');
        tag.className = 'bg-accent/20 text-accent px-3 py-1 rounded-full text-sm border border-accent/30';
        tag.textContent = document;
        return tag;
    }

    /**
     * Create a section header component
     * @param {string} title - Section title
     * @param {string} description - Section description
     * @param {string} icon - Material icon name
     * @param {string} iconColor - Icon color class
     * @returns {HTMLElement} Section header element
     */
    static createSectionHeader(title, description, icon, iconColor = 'text-primary') {
        const header = document.createElement('div');
        header.className = 'flex items-center mb-4';
        
        header.innerHTML = `
            <div class="bg-${iconColor.includes('primary') ? 'primary' : 'accent'}/20 p-3 rounded-lg mr-4">
                <span class="material-symbols-outlined ${iconColor}">${icon}</span>
            </div>
            <div>
                <h3 class="text-lg font-semibold text-gray-100">${Utils.sanitizeHtml(title)}</h3>
                <p class="text-gray-400">${Utils.sanitizeHtml(description)}</p>
            </div>
        `;
        
        return header;
    }

    /**
     * Create a progress bar component
     * @param {number} progress - Progress percentage (0-100)
     * @param {string} color - Progress color class
     * @returns {HTMLElement} Progress bar element
     */
    static createProgressBar(progress, color = 'bg-primary') {
        const container = document.createElement('div');
        container.className = 'w-full bg-gray-600 rounded-full h-2';
        
        const bar = document.createElement('div');
        bar.className = `${color} h-2 rounded-full transition-all duration-300`;
        bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        
        container.appendChild(bar);
        return container;
    }

    /**
     * Create a button component
     * @param {string} text - Button text
     * @param {string} variant - Button variant ('primary', 'secondary', 'accent')
     * @param {string} icon - Optional material icon name
     * @returns {HTMLElement} Button element
     */
    static createButton(text, variant = 'primary', icon = null) {
        const button = document.createElement('button');
        
        const baseClasses = 'px-4 py-2 rounded-lg transition-colors duration-200 flex items-center font-medium';
        const variantClasses = {
            primary: 'bg-primary hover:bg-blue-600 text-white',
            secondary: 'bg-gray-600 hover:bg-gray-500 text-gray-100',
            accent: 'bg-accent hover:bg-emerald-600 text-white'
        };
        
        button.className = `${baseClasses} ${variantClasses[variant] || variantClasses.primary}`;
        
        let innerHTML = '';
        if (icon) {
            innerHTML += `<span class="material-symbols-outlined mr-2 text-sm">${icon}</span>`;
        }
        innerHTML += Utils.sanitizeHtml(text);
        
        button.innerHTML = innerHTML;
        return button;
    }
}