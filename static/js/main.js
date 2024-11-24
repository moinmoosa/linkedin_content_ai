// Global variables
let currentContent = '';
let scheduleModal;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    loadScheduledPosts();
    
    // Set up form submissions
    document.getElementById('generateForm').addEventListener('submit', handleGenerate);
    document.getElementById('exampleForm').addEventListener('submit', handleAddExample);
});

async function handleGenerate(e) {
    e.preventDefault();
    
    const params = {
        topic: document.getElementById('topic').value,
        industry: document.getElementById('industry').value,
        tone: document.getElementById('tone').value,
        story_type: document.getElementById('storyType').value
    };
    
    try {
        const response = await fetch('/generate-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            currentContent = data.content;
            document.getElementById('contentText').textContent = currentContent;
            document.getElementById('generatedContent').classList.remove('d-none');
        } else {
            alert('Error generating content: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function handleAddExample(e) {
    e.preventDefault();
    
    const params = {
        content: document.getElementById('exampleContent').value,
        industry: document.getElementById('exampleIndustry').value,
        topic: document.getElementById('exampleTopic').value,
        story_type: document.getElementById('exampleStoryType').value
    };
    
    try {
        const response = await fetch('/add-example', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            alert('Example added successfully!');
            e.target.reset();
        } else {
            alert('Error adding example: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function copyToClipboard() {
    navigator.clipboard.writeText(currentContent).then(() => {
        alert('Content copied to clipboard!');
    });
}

function schedulePost() {
    scheduleModal.show();
}

async function confirmSchedule() {
    const scheduleDateTime = document.getElementById('scheduleDateTime').value;
    
    try {
        const response = await fetch('/schedule-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: currentContent,
                scheduled_time: scheduleDateTime
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            scheduleModal.hide();
            loadScheduledPosts();
        } else {
            alert('Error scheduling post: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function loadScheduledPosts() {
    try {
        const response = await fetch('/get-scheduled-posts');
        const posts = await response.json();
        
        const container = document.getElementById('scheduledPosts');
        container.innerHTML = '';
        
        posts.forEach(post => {
            const postElement = document.createElement('div');
            postElement.className = 'scheduled-post';
            postElement.innerHTML = `
                <p><strong>Scheduled for:</strong> ${new Date(post.scheduled_time).toLocaleString()}</p>
                <p>${post.content}</p>
                <button class="btn btn-secondary btn-sm" onclick="copyScheduledPost(this)">
                    <i class="bi bi-clipboard"></i> Copy
                </button>
            `;
            container.appendChild(postElement);
        });
    } catch (error) {
        console.error('Error loading scheduled posts:', error);
    }
}

function copyScheduledPost(button) {
    const content = button.parentElement.querySelector('p:nth-child(2)').textContent;
    navigator.clipboard.writeText(content).then(() => {
        alert('Content copied to clipboard!');
    });
}
