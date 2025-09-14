import { Utils } from './utils.js';
import { Components } from './components.js';
import { FileUpload } from './upload.js';
import { JsonVisualizer } from './visualizer.js';
import { ENDPOINTS, MESSAGES } from './config.js';

class PhototypeApp {
    constructor() {
        this.components = {
            fileUpload: null,
            jsonVisualizer: null
        };
        
        this.state = {
            currentPage: this.getCurrentPage(),
            loading: false,
            data: null
        };
        
        this.init();
    }

    init() {
        this.setupGlobalErrorHandling();
        this.initializeCurrentPage();
        this.setupGlobalComponents();
    }

    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/' || path === '/index') return 'home';
        if (path.startsWith('/view')) return 'viewer';
        if (path.includes('/upload')) return 'upload';
        return 'unknown';
    }

    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            Utils.showNotification('An unexpected error occurred', 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            Utils.showNotification('An unexpected error occurred', 'error');
        });
    }

    initializeCurrentPage() {
        switch (this.state.currentPage) {
            case 'home':
                this.initHomePage();
                break;
            case 'viewer':
                this.initViewerPage();
                break;
            case 'upload':
                this.initUploadPage();
                break;
            default:
                console.warn('Unknown page type:', this.state.currentPage);
        }
    }

    initHomePage() {
        this.setupFileUpload();
        this.setupJsonFilesList();
        this.initializeHeroSection();
    }

    initViewerPage() {
        this.setupJsonViewer();
        this.setupBackButton();
    }

    initUploadPage() {
        this.setupFileUpload();
    }

    setupFileUpload() {
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            this.components.fileUpload = new FileUpload('uploadForm', {
                onSuccess: (result) => this.handleUploadSuccess(result),
                onError: (error) => this.handleUploadError(error)
            });
        }
    }

    setupJsonViewer() {
        const viewerContainer = document.getElementById('jsonViewer');
        if (viewerContainer) {
            this.components.jsonVisualizer = new JsonVisualizer('jsonViewer', {
                theme: 'dark',
                showMetadata: true,
                collapsible: true
            });

            // Load JSON data from the current page
            this.loadCurrentJsonData();
        }
    }

    async loadCurrentJsonData() {
        // Check if data is already available in the page (from template)
        if (window.jsonData) {
            try {
                this.setLoadingState(true);
                await this.components.jsonVisualizer.loadData(window.jsonData);
                Utils.showNotification('Data loaded successfully', 'success');
            } catch (error) {
                console.error('Failed to load pre-loaded JSON data:', error);
                Utils.showNotification('Failed to load JSON data', 'error');
            } finally {
                this.setLoadingState(false);
            }
            return;
        }
        
        // Fallback to API loading
        const path = window.location.pathname;
        const matches = path.match(/\/view\/(.+)/);
        
        if (matches && matches[1]) {
            const filename = matches[1];
            try {
                this.setLoadingState(true);
                const apiUrl = ENDPOINTS.apiGetJson(filename);
                await this.components.jsonVisualizer.loadData(apiUrl);
                Utils.showNotification('Data loaded successfully', 'success');
            } catch (error) {
                console.error('Failed to load JSON data:', error);
                Utils.showNotification('Failed to load JSON data', 'error');
            } finally {
                this.setLoadingState(false);
            }
        }
    }

    setupJsonFilesList() {
        const filesList = document.getElementById('jsonFilesList');
        if (filesList) {
            this.loadJsonFilesList();
        }
    }

    async loadJsonFilesList() {
        try {
            const response = await fetch(ENDPOINTS.listJson);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.files) {
                this.renderJsonFilesList(data.files);
            } else {
                console.warn('No files found or API error:', data);
                this.renderEmptyFilesList();
            }
        } catch (error) {
            console.error('Failed to load files list:', error);
            Utils.showNotification('Failed to load file list', 'error');
            this.renderEmptyFilesList();
        }
    }

    renderJsonFilesList(files) {
        const container = document.getElementById('jsonFilesList');
        if (!container) return;

        if (files.length === 0) {
            this.renderEmptyFilesList();
            return;
        }

        const filesHTML = files.map(file => {
            const fileInfo = this.parseFileInfo(file);
            return Components.createFileCard(fileInfo);
        }).join('');

        container.innerHTML = `
            <div class="bg-gray-700 rounded-xl shadow-lg p-6 border border-gray-600">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center">
                        <div class="bg-accent/20 p-3 rounded-lg mr-4">
                            <span class="material-symbols-outlined text-accent">folder_open</span>
                        </div>
                        <div>
                            <h2 class="text-xl font-semibold text-gray-100">Available JSON Files</h2>
                            <p class="text-gray-400">Previously processed contract data</p>
                        </div>
                    </div>
                    <button onclick="window.location.reload()" class="text-gray-400 hover:text-gray-200 transition-colors">
                        <span class="material-symbols-outlined">refresh</span>
                    </button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${filesHTML}
                </div>
            </div>
        `;
    }

    renderEmptyFilesList() {
        const container = document.getElementById('jsonFilesList');
        if (!container) return;

        container.innerHTML = `
            <div class="bg-gray-700 rounded-xl shadow-lg p-6 border border-gray-600 text-center">
                <div class="text-gray-500 mb-4">
                    <span class="material-symbols-outlined text-6xl">folder_open</span>
                </div>
                <h3 class="text-lg font-medium text-gray-300 mb-2">No JSON Files Found</h3>
                <p class="text-gray-500 mb-4">Upload and process PDF contracts to see them here</p>
                <button onclick="document.getElementById('fileInput')?.click()" 
                        class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                    Upload First Contract
                </button>
            </div>
        `;
    }

    parseFileInfo(filename) {
        const nameWithoutExt = filename.replace('.json', '');
        const size = 'Unknown'; // We'd need additional API endpoint for file sizes
        const date = 'Unknown'; // We'd need additional API endpoint for dates
        
        return {
            name: nameWithoutExt,
            filename: filename,
            size: size,
            date: date,
            type: 'Contract Data',
            url: ENDPOINTS.viewJson(filename)
        };
    }

    initializeHeroSection() {
        const heroSection = document.getElementById('heroSection');
        if (heroSection) {
            // Add any hero section interactivity here
            this.setupFeatureCards();
        }
    }

    setupFeatureCards() {
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.classList.add('transform', 'scale-105');
            });
            
            card.addEventListener('mouseleave', () => {
                card.classList.remove('transform', 'scale-105');
            });
        });
    }

    setupBackButton() {
        const backButton = document.getElementById('backButton');
        if (backButton) {
            backButton.addEventListener('click', () => {
                window.history.back();
            });
        }
    }

    setupGlobalComponents() {
        this.setupNotificationSystem();
        this.setupLoadingIndicator();
        this.setupKeyboardShortcuts();
    }

    setupNotificationSystem() {
        // Ensure notification container exists
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    setupLoadingIndicator() {
        // Global loading indicator
        if (!document.getElementById('globalLoading')) {
            const loading = document.createElement('div');
            loading.id = 'globalLoading';
            loading.className = 'fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 hidden items-center justify-center';
            loading.innerHTML = `
                <div class="bg-gray-800 rounded-lg p-6 shadow-xl border border-gray-600">
                    <div class="flex items-center space-x-3">
                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                        <span class="text-gray-100">Loading...</span>
                    </div>
                </div>
            `;
            document.body.appendChild(loading);
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape to clear search
            if (e.key === 'Escape') {
                const searchInput = document.getElementById('searchInput');
                if (searchInput && searchInput === document.activeElement) {
                    searchInput.value = '';
                    searchInput.dispatchEvent(new Event('input'));
                    searchInput.blur();
                }
            }
        });
    }

    handleUploadSuccess(result) {
        Utils.showNotification(MESSAGES.upload.success, 'success');
        
        // Redirect to viewer after a short delay
        setTimeout(() => {
            window.location.href = ENDPOINTS.viewJson(result.filename);
        }, 1500);
    }

    handleUploadError(error) {
        Utils.showNotification(error.message || MESSAGES.upload.error, 'error');
    }

    setLoadingState(loading) {
        this.state.loading = loading;
        const loadingIndicator = document.getElementById('globalLoading');
        if (loadingIndicator) {
            if (loading) {
                loadingIndicator.classList.remove('hidden');
                loadingIndicator.classList.add('flex');
            } else {
                loadingIndicator.classList.add('hidden');
                loadingIndicator.classList.remove('flex');
            }
        }
    }

    // Public API methods
    getState() {
        return { ...this.state };
    }

    getComponent(name) {
        return this.components[name];
    }

    // Static factory method
    static create() {
        return new PhototypeApp();
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.Phototype = PhototypeApp.create();
});

// Export for module usage
export default PhototypeApp;
