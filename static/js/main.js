// ============================================================================
// DOM Elements
// ============================================================================

const uploadForm = document.getElementById('upload-form');
const uploadSection = document.getElementById('upload-section');
const processingSection = document.getElementById('processing-section');
const resultsSection = document.getElementById('results-section');

const referenceInput = document.getElementById('reference');
const videoInput = document.getElementById('video');
const youtubeInput = document.getElementById('youtube-url');
const sensitivitySelect = document.getElementById('sensitivity');
const themeToggle = document.getElementById('theme-toggle');

const progressFill = document.getElementById('progress-fill');
const progressPercent = document.getElementById('progress-percent');
const progressFrame = document.getElementById('progress-frame');
const processingStatus = document.getElementById('processing-status');

const videoPlayer = document.getElementById('video-player');
const timestampsList = document.getElementById('timestamps-list');
const totalDetections = document.getElementById('total-detections');
const avgConfidence = document.getElementById('avg-confidence');

const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');

const backBtn = document.getElementById('back-btn');
const exportBtn = document.getElementById('export-btn');

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupFileInputs();
    setupTabs();
    setupEventListeners();
});

// ============================================================================
// Theme Management
// ============================================================================

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    themeToggle.innerHTML = currentTheme === 'dark' 
        ? '<i class="fas fa-sun"></i>' 
        : '<i class="fas fa-moon"></i>';
}

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon();
});

// ============================================================================
// File Input Handling
// ============================================================================

function setupFileInputs() {
    referenceInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const preview = document.getElementById('reference-preview');
        if (file) {
            preview.innerHTML = `<span><i class="fas fa-check"></i> ${file.name}</span>`;
        }
    });

    videoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const preview = document.getElementById('video-preview');
        if (file) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            preview.innerHTML = `<span><i class="fas fa-check"></i> ${file.name} (${sizeMB}MB)</span>`;
        }
    });

    // Drag and drop for reference image
    const refLabel = document.querySelector('label[for="reference"]');
    setupDragAndDrop(refLabel, referenceInput);

    // Drag and drop for video
    const videoLabel = document.querySelector('label[for="video"]');
    setupDragAndDrop(videoLabel, videoInput);
}

function setupDragAndDrop(label, input) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        label.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        label.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        label.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        label.style.borderColor = 'var(--accent-primary)';
        label.style.background = 'var(--accent-light)';
    }

    function unhighlight(e) {
        label.style.borderColor = '';
        label.style.background = '';
    }

    label.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        input.files = files;
        const event = new Event('change', { bubbles: true });
        input.dispatchEvent(event);
    }
}

// ============================================================================
// Tab Switching
// ============================================================================

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = btn.getAttribute('data-tab');
            
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Clear the other input
            if (tabName === 'youtube') {
                videoInput.value = '';
            } else {
                youtubeInput.value = '';
            }
        });
    });
}

// ============================================================================
// Event Listeners Setup
// ============================================================================

function setupEventListeners() {
    backBtn.addEventListener('click', () => {
        resetUI();
    });
}

// ============================================================================
// Form Validation
// ============================================================================

async function validateFiles() {
    const formData = new FormData(uploadForm);
    
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        return result.success;
    } catch (error) {
        showError('Validation failed: ' + error.message);
        return false;
    }
}

// ============================================================================
// Form Submission
// ============================================================================

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate files
    if (!await validateFiles()) {
        return;
    }
    
    // Update UI
    uploadSection.classList.add('hidden');
    processingSection.classList.add('show');
    resultsSection.classList.remove('show');
    
    // Reset progress
    updateProgress(0, 'Initializing DeepFace models...');
    
    // Start listening for progress
    const eventSource = new EventSource('/api/progress');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateProgress(data.percent, data.status, data.frame_count, data.total_frames);
        
        if (data.percent >= 100) {
            eventSource.close();
        }
    };
    
    eventSource.onerror = () => {
        eventSource.close();
        showError('Connection lost while processing');
        resetUI();
    };
    
    // Send files to server
    const formData = new FormData(uploadForm);
    
    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            showError(result.error || 'Processing failed');
            resetUI();
        }
    } catch (error) {
        showError('Processing failed: ' + error.message);
        resetUI();
    }
});

function updateProgress(percent, status, frameCount = 0, totalFrames = 0) {
    progressPercent.textContent = Math.round(percent) + '%';
    progressFill.style.width = percent + '%';
    processingStatus.textContent = status;
    
    if (totalFrames > 0) {
        progressFrame.textContent = `${frameCount.toLocaleString()} / ${totalFrames.toLocaleString()} frames`;
    }
}

// ============================================================================
// Display Results
// ============================================================================

function displayResults(data) {
    processingSection.classList.remove('show');
    resultsSection.classList.add('show');
    
    // Set video source
    videoPlayer.src = data.video_url;
    
    // Update stats
    totalDetections.textContent = data.total_detections;
    
    if (data.results.length > 0) {
        const avgConf = (data.results.reduce((sum, r) => sum + r.confidence, 0) / data.results.length * 100).toFixed(1);
        avgConfidence.textContent = avgConf + '%';
    } else {
        avgConfidence.textContent = '0%';
    }
    
    // Display timestamps
    timestampsList.innerHTML = '';
    
    if (data.results.length === 0) {
        timestampsList.innerHTML = '<p style="color: var(--text-secondary); padding: 20px; text-align: center;">No detections found. Try adjusting sensitivity level.</p>';
    } else {
        data.results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'timestamp-item';
            item.innerHTML = `
                <div class="timestamp-time">${result.time}</div>
                <div class="timestamp-confidence">${(result.confidence * 100).toFixed(1)}%</div>
            `;
            
            item.addEventListener('click', () => {
                videoPlayer.currentTime = result.seconds;
                videoPlayer.play();
                
                document.querySelectorAll('.timestamp-item').forEach(el => {
                    el.classList.remove('active');
                });
                item.classList.add('active');
            });
            
            timestampsList.appendChild(item);
        });
    }
    
    // Setup export button
    exportBtn.addEventListener('click', () => {
        exportResults(data.results);
    }, { once: true });
    
    // Update video duration display
    videoPlayer.addEventListener('loadedmetadata', () => {
        const duration = formatTime(videoPlayer.duration);
        document.getElementById('total-duration').textContent = duration;
    }, { once: true });
    
    videoPlayer.addEventListener('timeupdate', () => {
        const current = formatTime(videoPlayer.currentTime);
        document.getElementById('current-time').textContent = current;
    });
}

function formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ============================================================================
// Export Results
// ============================================================================

function exportResults(results) {
    let csv = 'Timestamp,Seconds,Confidence (%)\n';
    
    results.forEach(r => {
        csv += `${r.time},${r.seconds},${(r.confidence * 100).toFixed(1)}\n`;
    });
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv));
    element.setAttribute('download', `face-detection-results-${new Date().toISOString().slice(0,10)}.csv`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// ============================================================================
// Error Handling
// ============================================================================

function showError(message) {
    errorMessage.textContent = message;
    errorModal.classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function resetUI() {
    uploadSection.classList.remove('hidden');
    processingSection.classList.remove('show');
    resultsSection.classList.remove('show');
    uploadForm.reset();
    document.getElementById('reference-preview').innerHTML = '<span id="reference-name">No file selected</span>';
    document.getElementById('video-preview').innerHTML = '<span id="video-name">No file selected</span>';
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Close modal with Escape
    if (e.key === 'Escape') {
        closeModal('error-modal');
    }
    
    // Space bar to play/pause video
    if (e.key === ' ' && resultsSection.classList.contains('show')) {
        e.preventDefault();
        if (videoPlayer.paused) {
            videoPlayer.play();
        } else {
            videoPlayer.pause();
        }
    }
});
