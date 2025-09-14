/**
 * Loading Panel Component for Phototype application
 * Shows progress and task information during backend processing
 */

export class LoadingPanel {
    constructor() {
        this.overlay = null;
        this.panel = null;
        this.progressBar = null;
        this.progressText = null;
        this.progressPercentage = null;
        this.taskText = null;
        this.taskDetails = null;
        this.steps = [];
        this.currentStep = 0;
        this.isVisible = false;
        this.pollInterval = null;
        this.taskId = null;
        
        // Default processing steps
        this.processingSteps = [
            { id: 'upload', label: 'Upload', icon: '1' },
            { id: 'preprocess', label: 'Preprocess', icon: '2' },
            { id: 'ocr', label: 'OCR', icon: '3' },
            { id: 'extract', label: 'Extract', icon: '4' },
            { id: 'complete', label: 'Complete', icon: '✓' }
        ];
    }

    show(taskId = null) {
        if (this.isVisible) return;
        
        this.taskId = taskId;
        this.createPanel();
        this.isVisible = true;
        
        // Start with upload step completed
        this.updateProgress(0, 'Starting upload...', 'Preparing file for processing');
        this.setStepActive(0);
    }

    hide() {
        if (!this.isVisible) return;
        
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        
        this.isVisible = false;
        this.taskId = null;
        this.currentStep = 0;
    }

    createPanel() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'loading-overlay';
        
        // Create panel
        this.panel = document.createElement('div');
        this.panel.className = 'loading-panel';
        
        this.panel.innerHTML = `
            <div class="loading-header">
                <div class="loading-icon">
                    <span class="material-symbols-outlined text-white">auto_fix_high</span>
                </div>
                <div>
                    <div class="loading-title">Processing PDF Document</div>
                    <div class="loading-subtitle">Converting to structured JSON data</div>
                </div>
            </div>
            
            <div class="loading-steps">
                ${this.processingSteps.map((step, index) => `
                    <div class="loading-step" data-step="${index}">
                        <div class="step-icon">${step.icon}</div>
                        <div class="step-label">${step.label}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="progress-container">
                <div class="progress-bar-container">
                    <div class="progress-bar"></div>
                </div>
                <div class="progress-text">
                    <span class="task-name">Initializing...</span>
                    <span class="progress-percentage">0%</span>
                </div>
            </div>
            
            <div class="task-status">
                <div class="task-status-header">
                    <span class="material-symbols-outlined task-status-icon">info</span>
                    <span class="task-status-text">Current Task</span>
                </div>
                <div class="task-details">Preparing to process your PDF document...</div>
            </div>
            
            <div class="text-center">
                <button class="loading-cancel-btn" onclick="this.closest('.loading-overlay').remove()">
                    Cancel Processing
                </button>
            </div>
        `;
        
        this.overlay.appendChild(this.panel);
        document.body.appendChild(this.overlay);
        
        // Get references to elements
        this.progressBar = this.panel.querySelector('.progress-bar');
        this.progressText = this.panel.querySelector('.task-name');
        this.progressPercentage = this.panel.querySelector('.progress-percentage');
        this.taskDetails = this.panel.querySelector('.task-details');
        this.steps = this.panel.querySelectorAll('.loading-step');
    }

    updateProgress(percentage, taskText = '', details = '') {
        if (!this.isVisible) return;
        
        // Update progress bar
        if (this.progressBar) {
            this.progressBar.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
        }
        
        // Update percentage text
        if (this.progressPercentage) {
            this.progressPercentage.textContent = `${Math.round(percentage)}%`;
        }
        
        // Update task text
        if (this.progressText && taskText) {
            this.progressText.textContent = taskText;
        }
        
        // Update details
        if (this.taskDetails && details) {
            this.taskDetails.textContent = details;
        }
        
        // Auto-advance steps based on percentage
        this.updateStepsFromProgress(percentage);
    }

    updateStepsFromProgress(percentage) {
        let newStep = 0;
        
        if (percentage >= 20) newStep = 1; // Preprocess
        if (percentage >= 40) newStep = 2; // OCR
        if (percentage >= 70) newStep = 3; // Extract
        if (percentage >= 100) newStep = 4; // Complete
        
        if (newStep !== this.currentStep) {
            this.setStepActive(newStep);
        }
    }

    setStepActive(stepIndex) {
        if (!this.steps || stepIndex < 0 || stepIndex >= this.steps.length) return;
        
        // Mark previous steps as completed
        for (let i = 0; i < stepIndex; i++) {
            this.steps[i].classList.remove('active');
            this.steps[i].classList.add('completed');
        }
        
        // Set current step as active
        this.steps[stepIndex].classList.remove('completed');
        this.steps[stepIndex].classList.add('active');
        
        // Clear future steps
        for (let i = stepIndex + 1; i < this.steps.length; i++) {
            this.steps[i].classList.remove('active', 'completed');
        }
        
        this.currentStep = stepIndex;
    }

    setStepCompleted(stepIndex) {
        if (!this.steps || stepIndex < 0 || stepIndex >= this.steps.length) return;
        
        this.steps[stepIndex].classList.remove('active');
        this.steps[stepIndex].classList.add('completed');
    }

    startProgressPolling(uploadResponse) {
        if (!uploadResponse || !uploadResponse.task_id) {
            // Simulate progress if no task ID
            this.simulateProgress();
            return;
        }
        
        this.taskId = uploadResponse.task_id;
        
        // Poll for progress every 500ms
        this.pollInterval = setInterval(() => {
            this.checkProgress();
        }, 500);
    }

    async checkProgress() {
        if (!this.taskId) return;
        
        try {
            const response = await fetch(`/progress/${this.taskId}`);
            if (response.ok) {
                const progress = await response.json();
                this.updateProgress(
                    progress.percentage || 0,
                    progress.task || 'Processing...',
                    progress.details || 'Working on your document...'
                );
                
                if (progress.percentage >= 100 || progress.status === 'complete') {
                    if (this.pollInterval) {
                        clearInterval(this.pollInterval);
                        this.pollInterval = null;
                    }
                    
                    // Show completion briefly before hiding
                    setTimeout(() => {
                        this.hide();
                    }, 1500);
                }
            }
        } catch (error) {
            console.warn('Progress polling error:', error);
            // Fallback to simulation if polling fails
            this.simulateProgress();
        }
    }

    simulateProgress() {
        let progress = 0;
        const steps = [
            { progress: 10, task: 'File uploaded', details: 'PDF file received successfully' },
            { progress: 25, task: 'Preprocessing document', details: 'Analyzing document structure...' },
            { progress: 45, task: 'Running OCR analysis', details: 'Extracting text from PDF pages...' },
            { progress: 65, task: 'Processing text data', details: 'Identifying contract fields...' },
            { progress: 85, task: 'Structuring JSON output', details: 'Organizing extracted information...' },
            { progress: 100, task: 'Processing complete', details: 'JSON data generated successfully' }
        ];
        
        let stepIndex = 0;
        
        const updateStep = () => {
            if (stepIndex < steps.length) {
                const step = steps[stepIndex];
                this.updateProgress(step.progress, step.task, step.details);
                stepIndex++;
                
                if (stepIndex < steps.length) {
                    // Variable delay between steps (1-3 seconds)
                    const delay = 1000 + Math.random() * 2000;
                    setTimeout(updateStep, delay);
                } else {
                    // Complete - hide after short delay
                    setTimeout(() => {
                        this.hide();
                    }, 1500);
                }
            }
        };
        
        // Start simulation after brief delay
        setTimeout(updateStep, 500);
    }

    // Static method to create and show loading panel
    static show(taskId = null) {
        const loader = new LoadingPanel();
        loader.show(taskId);
        return loader;
    }
}

// Export for global access
window.LoadingPanel = LoadingPanel;