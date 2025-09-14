/**
 * JSON Comparison Viewer - PDF Excerpts and Validation Functionality
 */

// Excerpt viewer variables
let excerpts = {};
let currentFilename = '';

// Validation state
const validationState = {};

/**
 * Initialize excerpt viewer
 */
async function initExcerptViewer() {
    // Get filename from the page and construct API path
    const filename = document.querySelector('[data-filename]')?.dataset.filename || 
                    document.title.split(' - ')[0] || '';
    currentFilename = filename;
    const excerptPath = `/api/pdf-excerpts/${filename.replace('.json', '.pdf')}`;
    
    console.log('Loading excerpts from:', excerptPath);
    
    try {
        const response = await fetch(excerptPath);
        const data = await response.json();
        
        if (data.success) {
            excerpts = data.excerpts;
            renderExcerpts();
            console.log('Excerpts loaded successfully:', Object.keys(excerpts).length, 'excerpts');
        } else {
            throw new Error(data.error || 'Failed to load excerpts');
        }
    } catch (error) {
        console.error('Error loading excerpts:', error);
        const excerptViewer = document.getElementById('excerptViewer');
        if (excerptViewer) {
            excerptViewer.innerHTML = `
                <div class="flex items-center justify-center h-full text-red-400">
                    <div class="text-center">
                        <span class="material-symbols-outlined text-6xl mb-4 block">error</span>
                        <p class="text-lg">Failed to load PDF excerpts</p>
                        <p class="text-sm mt-2">File: ${currentFilename}</p>
                        <p class="text-xs mt-1 text-gray-500">Error: ${error.message}</p>
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Render excerpts in the viewer
 */
function renderExcerpts() {
    const viewer = document.getElementById('excerptViewer');
    if (!viewer) {
        console.error('Excerpt viewer element not found');
        return;
    }
    
    if (Object.keys(excerpts).length === 0) {
        viewer.innerHTML = `
            <div class="flex items-center justify-center h-full text-gray-500">
                <div class="text-center">
                    <span class="material-symbols-outlined text-6xl mb-4 block">description</span>
                    <p class="text-lg">No excerpts found</p>
                    <p class="text-sm mt-2">No matching text found in PDF</p>
                </div>
            </div>
        `;
        return;
    }
    
    let excerptHtml = '<div class="p-4 space-y-4">';
    excerptHtml += '<h3 class="text-lg font-semibold text-white mb-4">PDF Text Excerpts</h3>';
    
    for (const [fieldPath, excerptData] of Object.entries(excerpts)) {
        excerptHtml += `
            <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div class="mb-2">
                    <span class="text-sm font-medium text-blue-400">${fieldPath}</span>
                    <span class="text-xs text-gray-500 ml-2">(${excerptData.field_type})</span>
                </div>
                <div class="mb-3">
                    <div class="text-sm text-gray-400 mb-1">Field Value:</div>
                    <div class="text-sm text-white bg-gray-700 p-2 rounded">${escapeHtml(excerptData.value)}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-400 mb-1">PDF Excerpt:</div>
                    <div class="text-sm text-green-400 bg-gray-900 p-3 rounded border-l-4 border-green-500">
                        ${escapeHtml(excerptData.excerpt)}
                    </div>
                </div>
            </div>
        `;
    }
    
    excerptHtml += '</div>';
    viewer.innerHTML = excerptHtml;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') {
        return String(unsafe);
    }
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Initialize field highlighting synchronization
 */
function initFieldHighlighting() {
    // Add hover events for approval items
    document.addEventListener('mouseenter', function(e) {
        if (e.target.closest('.approval-item')) {
            const approvalItem = e.target.closest('.approval-item');
            const fieldPath = approvalItem.dataset.field;
            
            if (fieldPath) {
                highlightField(fieldPath, true);
            }
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        if (e.target.closest('.approval-item')) {
            const approvalItem = e.target.closest('.approval-item');
            const fieldPath = approvalItem.dataset.field;
            
            if (fieldPath) {
                highlightField(fieldPath, false);
            }
        }
    }, true);
    
    // Add hover events for JSON fields
    document.addEventListener('mouseenter', function(e) {
        if (e.target.closest('.json-field')) {
            const jsonField = e.target.closest('.json-field');
            const fieldPath = jsonField.dataset.field;
            
            if (fieldPath) {
                highlightField(fieldPath, true);
            }
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        if (e.target.closest('.json-field')) {
            const jsonField = e.target.closest('.json-field');
            const fieldPath = jsonField.dataset.field;
            
            if (fieldPath) {
                highlightField(fieldPath, false);
            }
        }
    }, true);
}

/**
 * Highlight or unhighlight fields with matching field path
 */
function highlightField(fieldPath, highlight) {
    // Find and highlight JSON field
    const jsonField = document.querySelector(`.json-field[data-field="${fieldPath}"]`);
    if (jsonField) {
        if (highlight) {
            jsonField.classList.add('highlighted');
        } else {
            jsonField.classList.remove('highlighted');
        }
    }
    
    // Find and highlight approval item
    const approvalItem = document.querySelector(`.approval-item[data-field="${fieldPath}"]`);
    if (approvalItem) {
        if (highlight) {
            approvalItem.classList.add('highlighted');
        } else {
            approvalItem.classList.remove('highlighted');
        }
    }
}

/**
 * Update validation summary
 */
function updateValidationSummary() {
    const approved = Object.values(validationState).filter(v => v === 'approved').length;
    const disapproved = Object.values(validationState).filter(v => v === 'disapproved').length;
    const totalFields = document.querySelectorAll('.approval-item[data-field]').length;
    const pending = totalFields - approved - disapproved;
    
    const approvedElement = document.getElementById('approvedCount');
    const disapprovedElement = document.getElementById('disapprovedCount');
    const pendingElement = document.getElementById('pendingCount');
    
    if (approvedElement) approvedElement.textContent = approved;
    if (disapprovedElement) disapprovedElement.textContent = disapproved;
    if (pendingElement) pendingElement.textContent = pending;
}

/**
 * Save validation state to server
 */
async function saveValidation(fieldPath, status) {
    const filename = document.querySelector('[data-filename]')?.dataset.filename || 
                    document.title.split(' - ')[0] || '';
    
    try {
        const response = await fetch('/api/validation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                field_path: fieldPath,
                status: status
            })
        });
        
        if (!response.ok) {
            console.error('Failed to save validation');
        }
    } catch (error) {
        console.error('Error saving validation:', error);
    }
}

/**
 * Initialize event listeners
 */
function initEventListeners() {
    // View toggle for layout
    const toggleViewBtn = document.getElementById('toggleViewBtn');
    
    if (toggleViewBtn) {
        toggleViewBtn.addEventListener('click', function() {
            const layout = document.getElementById('comparisonLayout');
            const viewModeText = document.getElementById('viewModeText');
            
            if (layout && viewModeText) {
                if (layout.style.gridTemplateColumns === '1fr') {
                    layout.style.gridTemplateColumns = '1fr auto 1fr';
                    viewModeText.textContent = 'Split View';
                } else {
                    layout.style.gridTemplateColumns = '1fr';
                    viewModeText.textContent = 'JSON Only';
                }
            }
        });
    }

    // Radio button functionality for approval
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('approval-radio')) {
            const fieldPath = e.target.dataset.field;
            const newState = e.target.value;
            
            if (!fieldPath) return;
            
            const approvalItem = e.target.closest('.approval-item');
            
            // Remove all state classes from approval item
            approvalItem.classList.remove('approved', 'disapproved');
            
            // Apply new state
            if (newState === 'approved') {
                approvalItem.classList.add('approved');
                validationState[fieldPath] = 'approved';
            } else if (newState === 'disapproved') {
                approvalItem.classList.add('disapproved');
                validationState[fieldPath] = 'disapproved';
            } else {
                // pending state
                delete validationState[fieldPath];
            }
            
            // Update corresponding JSON field
            const jsonField = document.querySelector(`.json-field[data-field="${fieldPath}"]`);
            if (jsonField) {
                jsonField.classList.remove('approved', 'disapproved');
                
                if (newState === 'approved') {
                    jsonField.classList.add('approved');
                } else if (newState === 'disapproved') {
                    jsonField.classList.add('disapproved');
                }
            }
            
            // Update UI and save to server
            updateValidationSummary();
            saveValidation(fieldPath, newState);
        }
    });
}

/**
 * Initialize the application
 */
function initApp() {
    console.log('Initializing JSON Comparison Viewer with PDF excerpts...');
    
    // Initialize components
    initEventListeners();
    initFieldHighlighting();
    initExcerptViewer();
    updateValidationSummary();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}