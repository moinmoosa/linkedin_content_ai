// Global variables
let currentPostId = null;
let selectedFeedback = null;
let currentBatchId = null;
let batchCheckInterval = null;
let progressInterval = null;

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Form submission
    document.getElementById('generate-form').addEventListener('submit', handleGenerate);
    
    // Feedback buttons
    document.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', () => handleFeedbackSelect(btn));
    });
    
    // Submit feedback button
    document.getElementById('submit-feedback').addEventListener('click', handleFeedbackSubmit);
    
    // History filter
    document.getElementById('history-filter').addEventListener('input', handleHistoryFilter);
    
    // Load initial history
    loadFeedbackHistory();
    
    // Set up form submission for batch generation
    document.getElementById('batchForm').addEventListener('submit', handleBatchGenerate);
    
    // Check for pending batch
    checkPendingBatch();
});

// Handle post generation
async function handleGenerate(event) {
    event.preventDefault();
    
    const companyName = document.getElementById('company-name').value;
    const industry = document.getElementById('industry').value;
    const postType = document.getElementById('post-type').value;
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: companyName,
                industry: industry,
                post_type: postType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentPostId = data.post_id;
            document.getElementById('generated-post').textContent = data.content;
            document.getElementById('post-section').style.display = 'block';
            
            // Reset feedback state
            selectedFeedback = null;
            document.querySelectorAll('.feedback-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById('additional-feedback').value = '';
        } else {
            showToast('Error generating post: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error connecting to server', 'error');
        console.error('Error:', error);
    }
}

// Handle feedback button selection
function handleFeedbackSelect(button) {
    // Remove active class from all buttons
    document.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to selected button
    button.classList.add('active');
    selectedFeedback = button.dataset.feedback;
}

// Handle feedback submission
async function handleFeedbackSubmit() {
    if (!currentPostId || !selectedFeedback) {
        showToast('Please select a feedback option', 'warning');
        return;
    }
    
    const additionalFeedback = document.getElementById('additional-feedback').value;
    
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                post_id: currentPostId,
                feedback_type: parseInt(selectedFeedback),
                additional_text: additionalFeedback
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Feedback submitted successfully', 'success');
            loadFeedbackHistory(); // Reload history
        } else {
            showToast('Error submitting feedback: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error connecting to server', 'error');
        console.error('Error:', error);
    }
}

// Load feedback history
async function loadFeedbackHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.success) {
            displayFeedbackHistory(data.history);
        } else {
            showToast('Error loading history: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error connecting to server', 'error');
        console.error('Error:', error);
    }
}

// Display feedback history
function displayFeedbackHistory(history) {
    const container = document.getElementById('feedback-history');
    container.innerHTML = '';
    
    history.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-card';
        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${item.company_name}</strong> - ${item.industry}
                    <br>
                    <small class="text-muted">Post Type: ${item.post_type}</small>
                </div>
                <span class="badge bg-primary">${new Date(item.created_at).toLocaleDateString()}</span>
            </div>
            <div class="mt-2">
                <span class="badge bg-secondary">${item.feedback_text}</span>
            </div>
        `;
        container.appendChild(card);
    });
}

// Handle history filtering
function handleHistoryFilter(event) {
    const filter = event.target.value.toLowerCase();
    const cards = document.querySelectorAll('.history-card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(filter) ? 'block' : 'none';
    });
}

// Show loading spinner
function showLoading() {
    const spinner = document.getElementById('loadingSpinner');
    const progressBar = spinner.querySelector('.progress-bar');
    spinner.style.display = 'block';
    
    // Reset progress bar
    let progress = 0;
    progressBar.style.width = '0%';
    
    // Simulate progress
    progressInterval = setInterval(() => {
        if (progress < 90) {  // Only go up to 90% until actual completion
            progress += Math.random() * 10;
            progress = Math.min(progress, 90);
            progressBar.style.width = `${progress}%`;
        }
    }, 1000);
}

// Hide loading spinner
function hideLoading(success = true) {
    const spinner = document.getElementById('loadingSpinner');
    const progressBar = spinner.querySelector('.progress-bar');
    
    // Complete the progress bar
    if (success) {
        progressBar.style.width = '100%';
    }
    
    // Clear progress interval
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    // Hide spinner after a short delay
    setTimeout(() => {
        spinner.style.display = 'none';
        progressBar.style.width = '0%';
    }, 500);
}

// Handle batch generation
async function handleBatchGenerate(e) {
    e.preventDefault();
    
    const companiesText = document.getElementById('companies').value;
    const industry = document.getElementById('batchIndustry').value;
    
    // Split companies by newline and filter empty lines
    const companies = companiesText.split('\n')
        .map(company => company.trim())
        .filter(company => company.length > 0);
    
    if (companies.length === 0) {
        showToast('Please enter at least one company', 'error');
        return;
    }
    
    if (!industry) {
        showToast('Please select an industry', 'error');
        return;
    }
    
    // Show loading spinner
    showLoading();
    
    try {
        const response = await fetch('/api/generate-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_names: companies,
                industry: industry
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentBatchId = data.batch_id;
            displayBatchPosts(data.posts);
            startBatchCheck();
            hideLoading(true);
        } else {
            if (data.pending_batch) {
                showToast('Previous batch needs feedback first', 'warning');
                loadPendingBatch(data.pending_batch.batch_id);
            } else {
                showToast(data.error || 'Error generating posts', 'error');
            }
            hideLoading(false);
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
        hideLoading(false);
    }
}

// Display batch posts
function displayBatchPosts(posts) {
    const container = document.getElementById('postsContainer');
    const template = document.getElementById('postTemplate');
    const batchPosts = document.getElementById('batchPosts');
    
    // Clear existing posts
    container.innerHTML = '';
    
    // Show the posts section
    batchPosts.classList.remove('d-none');
    
    // Add each post
    posts.forEach(post => {
        const postElement = template.content.cloneNode(true);
        
        postElement.querySelector('.company-name').textContent = post.company_name;
        postElement.querySelector('.post-content').textContent = post.content;
        
        // Set up feedback buttons
        const feedbackButtons = postElement.querySelectorAll('.feedback-btn');
        feedbackButtons.forEach(button => {
            button.addEventListener('click', () => handleFeedback(post.post_id, button));
        });
        
        container.appendChild(postElement);
    });
    
    // Scroll to the posts section
    batchPosts.scrollIntoView({ behavior: 'smooth' });
}

// Handle feedback submission for batch posts
async function handleFeedback(postId, button) {
    const feedbackType = button.dataset.type;
    const card = button.closest('.card');
    const feedbackText = card.querySelector('.feedback-text').value;
    
    try {
        const response = await fetch('/api/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                post_id: postId,
                feedback_type: feedbackType,
                feedback_text: feedbackText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Disable all feedback buttons in this card
            card.querySelectorAll('.feedback-btn').forEach(btn => {
                btn.disabled = true;
                btn.classList.remove('btn-outline-danger', 'btn-outline-warning', 
                                  'btn-outline-info', 'btn-outline-secondary', 
                                  'btn-outline-dark');
                if (btn === button) {
                    btn.classList.add('btn-' + getButtonStyle(feedbackType));
                } else {
                    btn.classList.add('btn-light');
                }
            });
            card.querySelector('.feedback-text').disabled = true;
            
            showToast('Feedback submitted successfully', 'success');
        } else {
            showToast(data.error || 'Error submitting feedback', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Get button style based on feedback type
function getButtonStyle(feedbackType) {
    const styles = {
        'too_technical': 'danger',
        'not_technical': 'warning',
        'wrong_tone': 'info',
        'missing_info': 'secondary',
        'not_engaging': 'dark'
    };
    return styles[feedbackType] || 'primary';
}

// Check for pending batch
async function checkPendingBatch() {
    try {
        const response = await fetch('/api/current-batch');
        const data = await response.json();
        
        if (data.success && data.batch) {
            currentBatchId = data.batch.batch_id;
            loadPendingBatch(currentBatchId);
            startBatchCheck();
        }
    } catch (error) {
        console.error('Error checking pending batch:', error);
    }
}

// Load pending batch
async function loadPendingBatch(batchId) {
    try {
        const response = await fetch(`/api/batch/${batchId}/posts`);
        const data = await response.json();
        
        if (data.success) {
            displayBatchPosts(data.posts);
        }
    } catch (error) {
        console.error('Error loading pending batch:', error);
    }
}

// Start batch check
function startBatchCheck() {
    if (batchCheckInterval) {
        clearInterval(batchCheckInterval);
    }
    
    // Check batch status every 5 minutes
    batchCheckInterval = setInterval(checkBatchStatus, 5 * 60 * 1000);
}

// Check batch status
async function checkBatchStatus() {
    if (!currentBatchId) return;
    
    try {
        const response = await fetch(`/api/batch/${currentBatchId}/status`);
        const data = await response.json();
        
        if (data.success) {
            if (data.status === 'completed') {
                // Batch is complete, stop checking
                clearInterval(batchCheckInterval);
                batchCheckInterval = null;
                currentBatchId = null;
                
                // Clear the form
                document.getElementById('companies').value = '';
                document.getElementById('batchIndustry').value = '';
                
                showToast('Batch complete! You can generate new posts now.', 'success');
            }
        }
    } catch (error) {
        console.error('Error checking batch status:', error);
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    Toastify({
        text: message,
        duration: 3000,
        gravity: 'top',
        position: 'right',
        backgroundColor: type === 'error' ? '#dc3545' :
                        type === 'success' ? '#198754' :
                        type === 'warning' ? '#ffc107' : '#0dcaf0'
    }).showToast();
}
