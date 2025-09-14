/**
 * JSON Data Visualization module for Phototype application
 */
import { CONFIG, MESSAGES } from './config.js';
import { Utils } from './utils.js';
import { Components } from './components.js';

export class JsonVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            theme: 'dark',
            showMetadata: true,
            collapsible: true,
            ...options
        };
        
        this.data = null;
        this.filteredData = null;
        this.searchQuery = '';
        this.expandedSections = new Set();
    }

    async loadData(source) {
        try {
            let data;
            if (typeof source === 'string') {
                // Assume it's a URL or filename
                const response = await fetch(source);
                if (!response.ok) {
                    throw new Error(`Failed to load data: ${response.statusText}`);
                }
                data = await response.json();
            } else {
                // Assume it's already parsed JSON
                data = source;
            }
            
            this.data = data;
            this.filteredData = data;
            this.render();
            return data;
        } catch (error) {
            console.error('Error loading JSON data:', error);
            Utils.showNotification(MESSAGES.data.loadError, 'error');
            this.renderError(error.message);
            throw error;
        }
    }

    render() {
        if (!this.container) {
            console.error('Container not found');
            return;
        }

        if (!this.data) {
            this.renderEmpty();
            return;
        }

        this.container.innerHTML = this.generateHTML();
        this.bindEvents();
    }

    generateHTML() {
        const metadata = this.generateMetadata();
        const content = this.generateContent(this.filteredData);
        const controls = this.generateControls();

        return `
            <div class="json-visualizer bg-gray-800 rounded-xl shadow-lg border border-gray-600">
                ${controls}
                ${metadata}
                ${content}
            </div>
        `;
    }

    generateControls() {
        return `
            <div class="p-4 border-b border-gray-600 bg-gray-700 rounded-t-xl">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center space-x-4">
                        <h2 class="text-xl font-semibold text-gray-100 flex items-center">
                            <span class="material-symbols-outlined mr-2 text-primary">data_object</span>
                            JSON Data Viewer
                        </h2>
                        <div class="flex items-center space-x-2">
                            <button id="expandAllBtn" class="text-sm bg-primary hover:bg-blue-600 text-white px-3 py-1 rounded transition-colors">
                                <span class="material-symbols-outlined text-sm mr-1">unfold_more</span>
                                Expand All
                            </button>
                            <button id="collapseAllBtn" class="text-sm bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded transition-colors">
                                <span class="material-symbols-outlined text-sm mr-1">unfold_less</span>
                                Collapse All
                            </button>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="relative">
                            <input type="text" id="searchInput" placeholder="Search data..." 
                                   class="bg-gray-700 border border-gray-500 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-primary pl-10">
                            <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
                        </div>
                        <button id="downloadBtn" class="text-sm bg-accent hover:bg-emerald-600 text-white px-3 py-1 rounded transition-colors flex items-center">
                            <span class="material-symbols-outlined text-sm mr-1">download</span>
                            Download
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    generateMetadata() {
        if (!this.options.showMetadata || !this.data) return '';

        const stats = this.calculateStats(this.data);
        return `
            <div class="p-4 border-b border-gray-600 bg-gray-700">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div class="text-center">
                        <div class="text-gray-400">Total Fields</div>
                        <div class="text-xl font-semibold text-primary">${stats.totalFields}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-gray-400">Nested Objects</div>
                        <div class="text-xl font-semibold text-accent">${stats.nestedObjects}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-gray-400">Arrays</div>
                        <div class="text-xl font-semibold text-yellow-400">${stats.arrays}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-gray-400">Data Size</div>
                        <div class="text-xl font-semibold text-gray-100">${Utils.formatFileSize(JSON.stringify(this.data).length)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    generateContent(data, path = '', level = 0) {
        if (data === null || data === undefined) {
            return `<span class="text-gray-500 italic">null</span>`;
        }

        if (typeof data !== 'object') {
            return this.generatePrimitiveValue(data);
        }

        if (Array.isArray(data)) {
            return this.generateArray(data, path, level);
        }

        return this.generateObject(data, path, level);
    }

    generateObject(obj, path, level) {
        const entries = Object.entries(obj);
        if (entries.length === 0) {
            return `<span class="text-gray-500">{}</span>`;
        }

        const isExpanded = this.expandedSections.has(path) || level < 2;
        const toggleIcon = isExpanded ? 'expand_less' : 'expand_more';
        
        let html = `
            <div class="json-object">
                <div class="flex items-center cursor-pointer hover:bg-gray-700 rounded p-1 transition-colors" 
                     data-path="${path}" data-toggle="object">
                    <span class="material-symbols-outlined text-gray-400 text-sm mr-1">${toggleIcon}</span>
                    <span class="text-gray-400 font-medium">Object</span>
                    <span class="text-gray-500 text-sm ml-2">(${entries.length} ${entries.length === 1 ? 'field' : 'fields'})</span>
                </div>
                <div class="json-object-content ml-4 ${isExpanded ? '' : 'hidden'}" data-content="${path}">
        `;

        entries.forEach(([key, value], index) => {
            const keyPath = path ? `${path}.${key}` : key;
            const isLast = index === entries.length - 1;
            
            html += `
                <div class="flex items-start py-1 ${isLast ? '' : 'border-b border-gray-700/50'}">
                    <div class="flex-shrink-0 w-32 pr-4">
                        <span class="text-accent font-medium text-sm">${Utils.sanitizeHtml(key)}:</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        ${this.generateContent(value, keyPath, level + 1)}
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    generateArray(arr, path, level) {
        if (arr.length === 0) {
            return `<span class="text-gray-500">[]</span>`;
        }

        const isExpanded = this.expandedSections.has(path) || level < 2;
        const toggleIcon = isExpanded ? 'expand_less' : 'expand_more';

        let html = `
            <div class="json-array">
                <div class="flex items-center cursor-pointer hover:bg-gray-700 rounded p-1 transition-colors" 
                     data-path="${path}" data-toggle="array">
                    <span class="material-symbols-outlined text-gray-400 text-sm mr-1">${toggleIcon}</span>
                    <span class="text-yellow-400 font-medium">Array</span>
                    <span class="text-gray-500 text-sm ml-2">(${arr.length} ${arr.length === 1 ? 'item' : 'items'})</span>
                </div>
                <div class="json-array-content ml-4 ${isExpanded ? '' : 'hidden'}" data-content="${path}">
        `;

        arr.forEach((item, index) => {
            const itemPath = `${path}[${index}]`;
            html += `
                <div class="flex items-start py-1">
                    <div class="flex-shrink-0 w-8 pr-2">
                        <span class="text-gray-500 text-sm">${index}:</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        ${this.generateContent(item, itemPath, level + 1)}
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    generatePrimitiveValue(value) {
        const type = typeof value;
        let className = 'text-gray-100';
        let displayValue = String(value);

        switch (type) {
            case 'string':
                className = 'text-green-400';
                displayValue = `"${Utils.sanitizeHtml(value)}"`;
                break;
            case 'number':
                className = 'text-blue-400';
                break;
            case 'boolean':
                className = 'text-purple-400';
                break;
            case 'undefined':
                className = 'text-gray-500';
                displayValue = 'undefined';
                break;
        }

        return `<span class="${className}">${displayValue}</span>`;
    }

    calculateStats(data, stats = { totalFields: 0, nestedObjects: 0, arrays: 0 }) {
        if (Array.isArray(data)) {
            stats.arrays++;
            data.forEach(item => this.calculateStats(item, stats));
        } else if (data && typeof data === 'object') {
            stats.nestedObjects++;
            Object.values(data).forEach(value => {
                stats.totalFields++;
                this.calculateStats(value, stats);
            });
        }
        return stats;
    }

    bindEvents() {
        // Toggle expand/collapse
        this.container.addEventListener('click', (e) => {
            const toggle = e.target.closest('[data-toggle]');
            if (toggle) {
                const path = toggle.dataset.path;
                this.toggleSection(path);
            }
        });

        // Search functionality
        const searchInput = this.container.querySelector('#searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }

        // Expand/Collapse all buttons
        const expandAllBtn = this.container.querySelector('#expandAllBtn');
        const collapseAllBtn = this.container.querySelector('#collapseAllBtn');
        
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => this.expandAll());
        }
        
        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => this.collapseAll());
        }

        // Download button
        const downloadBtn = this.container.querySelector('#downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadData());
        }
    }

    toggleSection(path) {
        if (this.expandedSections.has(path)) {
            this.expandedSections.delete(path);
        } else {
            this.expandedSections.add(path);
        }

        const toggle = this.container.querySelector(`[data-path="${path}"]`);
        const content = this.container.querySelector(`[data-content="${path}"]`);
        const icon = toggle?.querySelector('.material-symbols-outlined');

        if (content && icon) {
            const isExpanded = this.expandedSections.has(path);
            content.classList.toggle('hidden', !isExpanded);
            icon.textContent = isExpanded ? 'expand_less' : 'expand_more';
        }
    }

    expandAll() {
        this.container.querySelectorAll('[data-path]').forEach(element => {
            const path = element.dataset.path;
            this.expandedSections.add(path);
        });
        this.render();
    }

    collapseAll() {
        this.expandedSections.clear();
        this.render();
    }

    handleSearch(query) {
        this.searchQuery = query.toLowerCase();
        if (!query) {
            this.filteredData = this.data;
        } else {
            this.filteredData = this.filterData(this.data, query);
        }
        this.render();
    }

    filterData(data, query) {
        if (typeof data === 'string') {
            return data.toLowerCase().includes(query) ? data : null;
        }

        if (Array.isArray(data)) {
            const filtered = data.map(item => this.filterData(item, query)).filter(item => item !== null);
            return filtered.length > 0 ? filtered : null;
        }

        if (data && typeof data === 'object') {
            const filtered = {};
            let hasMatches = false;

            for (const [key, value] of Object.entries(data)) {
                if (key.toLowerCase().includes(query)) {
                    filtered[key] = value;
                    hasMatches = true;
                } else {
                    const filteredValue = this.filterData(value, query);
                    if (filteredValue !== null) {
                        filtered[key] = filteredValue;
                        hasMatches = true;
                    }
                }
            }

            return hasMatches ? filtered : null;
        }

        return String(data).toLowerCase().includes(query) ? data : null;
    }

    downloadData() {
        if (!this.data) return;

        const dataToDownload = this.searchQuery ? this.filteredData : this.data;
        const blob = new Blob([JSON.stringify(dataToDownload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `phototype-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        Utils.showNotification('Data downloaded successfully', 'success');
    }

    renderEmpty() {
        this.container.innerHTML = `
            <div class="text-center py-12">
                <div class="text-gray-500 mb-4">
                    <span class="material-symbols-outlined text-6xl">data_object</span>
                </div>
                <h3 class="text-lg font-medium text-gray-300 mb-2">No Data Available</h3>
                <p class="text-gray-500">Load JSON data to begin visualization</p>
            </div>
        `;
    }

    renderError(message) {
        this.container.innerHTML = `
            <div class="text-center py-12">
                <div class="text-red-400 mb-4">
                    <span class="material-symbols-outlined text-6xl">error</span>
                </div>
                <h3 class="text-lg font-medium text-gray-300 mb-2">Error Loading Data</h3>
                <p class="text-gray-500">${Utils.sanitizeHtml(message)}</p>
            </div>
        `;
    }

    // Static method to create container HTML
    static createContainerHTML(id = 'jsonVisualizer') {
        return `<div id="${id}" class="json-visualizer-container"></div>`;
    }
}