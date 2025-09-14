/**
 * File Upload functionality for Phototype application
 */
import { CONFIG, ENDPOINTS, MESSAGES } from './config.js';
import { Utils } from './utils.js';

export class FileUpload {
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        this.options = {
            maxFileSize: CONFIG.MAX_FILE_SIZE,
            allowedExtensions: CONFIG.ALLOWED_EXTENSIONS,
            uploadEndpoint: ENDPOINTS.upload,
            ...options
        };
        
        this.elements = {
            fileInput: null,
            dropZone: null,
            fileInfo: null,
            fileName: null,
            fileSize: null,
            uploadBtn: null,
            uploadBtnText: null
        };
        
        this.init();
    }

    init() {
        if (!this.form) {
            console.error('Upload form not found');
            return;
        }

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.elements.fileInput = this.form.querySelector('#fileInput');
        this.elements.dropZone = this.form.querySelector('#dropZone');
        this.elements.fileInfo = this.form.querySelector('#fileInfo');
        this.elements.fileName = this.form.querySelector('#fileName');
        this.elements.fileSize = this.form.querySelector('#fileSize');
        this.elements.uploadBtn = this.form.querySelector('#uploadBtn');
        this.elements.uploadBtnText = this.form.querySelector('#uploadBtnText');
    }

    bindEvents() {
        // File input change
        if (this.elements.fileInput) {
            this.elements.fileInput.addEventListener('change', () => this.handleFileSelect());
        }

        // Drag and drop events
        if (this.elements.dropZone) {
            this.elements.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.elements.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            this.elements.dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Clear file buttons - bind using event delegation
        this.form.addEventListener('click', (e) => {
            if (e.target.closest('.clear-file-btn')) {
                e.preventDefault();
                this.clearFile();
            }
        });
    }

    handleFileSelect() {
        const file = this.elements.fileInput.files[0];
        if (file) {
            const validation = Utils.validateFile(file);
            if (validation.isValid) {
                this.displayFileInfo(file);
                this.enableUpload();
            } else {
                Utils.showNotification(validation.error, 'error');
                this.clearFile();
            }
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        this.elements.dropZone.classList.add('border-primary', 'bg-primary/5');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.elements.dropZone.classList.remove('border-primary', 'bg-primary/5');
    }

    handleDrop(e) {
        e.preventDefault();
        this.elements.dropZone.classList.remove('border-primary', 'bg-primary/5');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            const validation = Utils.validateFile(file);
            if (validation.isValid) {
                // Create a new FileList-like object
                const dt = new DataTransfer();
                dt.items.add(file);
                this.elements.fileInput.files = dt.files;
                this.handleFileSelect();
            } else {
                Utils.showNotification(validation.error, 'error');
            }
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const file = this.elements.fileInput.files[0];
        if (!file) {
            Utils.showNotification(MESSAGES.upload.noFile, 'error');
            return;
        }

        this.setUploadState(true);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(this.options.uploadEndpoint, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                Utils.showNotification(MESSAGES.upload.success, 'success');
                setTimeout(() => {
                    window.location.href = ENDPOINTS.viewJson(result.filename);
                }, 1500);
            } else {
                Utils.showNotification(result.error || MESSAGES.upload.error, 'error');
                this.setUploadState(false);
            }
        } catch (error) {
            console.error('Upload error:', error);
            Utils.showNotification(MESSAGES.upload.error, 'error');
            this.setUploadState(false);
        }
    }

    displayFileInfo(file) {
        if (this.elements.fileName) {
            this.elements.fileName.textContent = file.name;
        }
        if (this.elements.fileSize) {
            this.elements.fileSize.textContent = `(${Utils.formatFileSize(file.size)})`;
        }
        if (this.elements.fileInfo) {
            this.elements.fileInfo.classList.remove('hidden');
        }
    }

    enableUpload() {
        if (this.elements.uploadBtn) {
            this.elements.uploadBtn.disabled = false;
            this.elements.uploadBtn.classList.remove('disabled:bg-gray-500', 'disabled:cursor-not-allowed');
            this.elements.uploadBtn.classList.add('bg-accent', 'hover:bg-emerald-600');
        }
    }

    clearFile() {
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }
        if (this.elements.fileInfo) {
            this.elements.fileInfo.classList.add('hidden');
        }
        if (this.elements.uploadBtn) {
            this.elements.uploadBtn.disabled = true;
            this.elements.uploadBtn.classList.add('disabled:bg-gray-500', 'disabled:cursor-not-allowed');
            this.elements.uploadBtn.classList.remove('bg-accent', 'hover:bg-emerald-600');
        }
    }

    setUploadState(uploading) {
        if (this.elements.uploadBtn) {
            this.elements.uploadBtn.disabled = uploading;
            if (uploading) {
                this.elements.uploadBtn.classList.add('cursor-not-allowed');
            } else {
                this.elements.uploadBtn.classList.remove('cursor-not-allowed');
            }
        }
        
        if (this.elements.uploadBtnText) {
            this.elements.uploadBtnText.textContent = uploading ? MESSAGES.upload.processing : 'Process PDF';
        }
    }

    // Static method to create upload form HTML
    static createUploadFormHTML() {
        return `
            <div class="bg-gray-700 rounded-xl shadow-lg p-6 border border-gray-600 mb-8">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center">
                        <div class="bg-primary/20 p-3 rounded-lg mr-4">
                            <span class="material-symbols-outlined text-primary">upload_file</span>
                        </div>
                        <div>
                            <h2 class="text-xl font-semibold text-gray-100">Upload PDF Contract</h2>
                            <p class="text-gray-400">Convert PDF contracts to structured JSON data</p>
                        </div>
                    </div>
                </div>
                
                <form id="uploadForm" enctype="multipart/form-data" class="space-y-4">
                    <div class="border-2 border-dashed border-gray-500 rounded-lg p-8 text-center transition-colors duration-200 hover:border-primary" id="dropZone">
                        <div class="space-y-4">
                            <div class="flex justify-center">
                                <div class="bg-gray-600 p-4 rounded-full">
                                    <span class="material-symbols-outlined text-gray-300 text-3xl">cloud_upload</span>
                                </div>
                            </div>
                            <div>
                                <p class="text-lg font-medium text-gray-100 mb-2">Drop your PDF file here or click to browse</p>
                                <p class="text-gray-400 text-sm">Supports PDF files up to 10MB</p>
                            </div>
                            <input type="file" id="fileInput" name="file" accept=".pdf" class="hidden">
                            <button type="button" onclick="document.getElementById('fileInput').click()" 
                                    class="bg-primary hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors duration-200 flex items-center mx-auto">
                                <span class="material-symbols-outlined mr-2">attach_file</span>
                                Select PDF File
                            </button>
                        </div>
                    </div>
                    
                    <div id="fileInfo" class="hidden bg-gray-600 rounded-lg p-4">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <span class="material-symbols-outlined text-accent mr-2">description</span>
                                <span id="fileName" class="text-gray-100 font-medium"></span>
                                <span id="fileSize" class="text-gray-400 text-sm ml-2"></span>
                            </div>
                            <button type="button" class="clear-file-btn text-gray-400 hover:text-red-400 transition-colors">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>
                    </div>
                    
                    <div class="flex justify-end space-x-3">
                        <button type="button" class="clear-file-btn bg-gray-600 hover:bg-gray-500 text-gray-100 px-4 py-2 rounded-lg transition-colors duration-200">
                            Cancel
                        </button>
                        <button type="submit" id="uploadBtn" disabled 
                                class="bg-accent hover:bg-emerald-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors duration-200 flex items-center">
                            <span class="material-symbols-outlined mr-2">rocket_launch</span>
                            <span id="uploadBtnText">Process PDF</span>
                        </button>
                    </div>
                </form>
            </div>
        `;
    }
}