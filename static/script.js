// --- Global State ---
let currentUserId = null;
let currentUsername = null;
let authToken = localStorage.getItem("jobify_token") || null;

// --- Elements ---
const pages = {
    login: document.getElementById('page-login'),
    home: document.getElementById('page-home'),
    loading: document.getElementById('page-loading'),
    results: document.getElementById('page-results')
};

// Login
const loginForm = document.getElementById('modern-login-form');
const loginBtn = document.getElementById('login-btn');
const loginInput = document.getElementById('login-username');
const loginPass = document.getElementById('login-password');
const pwdToggle = document.getElementById('pwd-toggle');
const emailCheck = document.querySelector('.auth-check');
const emailError = document.getElementById('email-error');
const pwdStrength = document.getElementById('pwd-strength');
const strengthFill = document.querySelector('.strength-fill');
const strengthText = document.querySelector('.strength-text');


// Upload
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-db-btn');
const fileInfo = document.getElementById('file-info');
const fileNameSpan = document.getElementById('file-name');
let selectedFile = null;

// Results
const displayUser = document.getElementById('display-user');
const jobsContainer = document.getElementById('jobs-container');
const trackerContainer = document.getElementById('tracker-container');

// --- Helper Functions ---
function switchPage(pageId) {
    Object.values(pages).forEach(p => p.classList.remove('active', 'hidden'));
    Object.values(pages).forEach(p => {
        if (p.id !== pageId) p.classList.add('hidden');
        else p.classList.add('active');
    });
}

function showLoading(text) {
    document.getElementById('loading-text').innerText = text;
    switchPage('page-loading');
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}

// --- Premium Login UI Enhancements ---
// Password Toggle
pwdToggle.addEventListener('click', () => {
    const type = loginPass.getAttribute('type') === 'password' ? 'text' : 'password';
    loginPass.setAttribute('type', type);
    pwdToggle.innerHTML = type === 'password' ? '<i class="fa-regular fa-eye"></i>' : '<i class="fa-regular fa-eye-slash"></i>';
});

// Real-time Username Validation
loginInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    if (val.length >= 3) {
        emailCheck.classList.remove('hidden');
        emailError.classList.remove('show');
        loginInput.classList.remove('input-error');
    } else {
        emailCheck.classList.add('hidden');
        if (val.length > 0) {
            emailError.innerText = "Username must be at least 3 characters";
            emailError.classList.add('show');
            loginInput.classList.add('input-error');
        } else {
            emailError.classList.remove('show');
            loginInput.classList.remove('input-error');
        }
    }
});

// Real-time Password Strength
loginPass.addEventListener('input', (e) => {
    const val = e.target.value;
    if (val.length > 0) {
        pwdStrength.classList.add('show');
        let strength = 0;
        if (val.length > 7) strength += 25;
        if (/[A-Z]/.test(val)) strength += 25;
        if (/[0-9]/.test(val)) strength += 25;
        if (/[^A-Za-z0-9]/.test(val)) strength += 25;
        
        strengthFill.style.width = `${strength}%`;
        
        if (strength <= 25) { strengthFill.style.background = '#ef4444'; strengthText.innerText = 'Weak'; }
        else if (strength <= 50) { strengthFill.style.background = '#f59e0b'; strengthText.innerText = 'Fair'; }
        else if (strength <= 75) { strengthFill.style.background = '#3b82f6'; strengthText.innerText = 'Good'; }
        else { strengthFill.style.background = '#10b981'; strengthText.innerText = 'Strong'; }
    } else {
        pwdStrength.classList.remove('show');
    }
});

// --- Login Form Submission ---
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = loginInput.value.trim();
    const password = loginPass.value.trim();
    
    if (!username || !password) return alert("Please enter both username and password.");
    
    const originalBtnHTML = loginBtn.innerHTML;
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Authenticating Engine...</span>';
    
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, password })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Authentication Failed. Please check your credentials.");
        
        authToken = data.access_token;
        localStorage.setItem("jobify_token", authToken);
        currentUserId = data.user_id;
        currentUsername = data.username;
        displayUser.innerText = currentUsername;

        if (data.has_resume) {
            loadDailyFeed();
        } else {
            switchPage('page-home');
        }
    } catch (err) {
        alert(err.message);
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerHTML = originalBtnHTML;
    }
});

// --- File Upload ---
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        fileInfo.classList.remove('hidden');
        fileNameSpan.textContent = selectedFile.name;
        uploadBtn.disabled = false;
    }
});

uploadBtn.addEventListener('click', async () => {
    if (!selectedFile || !currentUserId) return;
    const fd = new FormData();
    fd.append('file', selectedFile);
    
    showLoading("Saving securely to CRM...");
    try {
        const res = await fetch(`/api/resume/upload/${currentUserId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }, // No Content-Type for FormData
            body: fd
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Upload error");
        
        loadDailyFeed();
    } catch (e) {
        alert("Upload error: " + e.message);
        switchPage('page-home');
    }
});

// --- Dashboard ---
async function loadDailyFeed() {
    showLoading("Consulting Agent & Fetching Jobs...");
    try {
        const res = await fetch(`/api/jobs/feed/${currentUserId}`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.error || "Unknown server error");
        
        renderJobs(data.jobs || []);
        switchPage('page-results');
        loadTracker();
    } catch (e) {
        alert("Error fetching feed: " + e.message);
        switchPage('page-login');
    }
}

function renderJobs(jobs) {
    jobsContainer.innerHTML = '';
    if (jobs.length === 0) {
        jobsContainer.innerHTML = '<p class="empty-state">No jobs found today. AI agents will search again tomorrow.</p>';
        return;
    }
    
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'crm-job-card';
        card.innerHTML = `
            <div class="card-header">
                <div>
                    <h3>${job.role || job.title}</h3>
                    <p><i class="fa-solid fa-building"></i> ${job.company || 'Unknown Company'}</p>
                    <span class="deep-match-badge">Deep Match: ${job.match_score}%</span>
                </div>
                <button class="btn-outline track-btn" onclick="trackJob('${job.company || ''}', '${job.role || job.title}', '${job.url || ''}')">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Track & Auto-Tailor
                </button>
            </div>
            <div class="card-footer">
                <p><strong>Missing Skills:</strong> ${job.missing_skills ? job.missing_skills.join(', ') : 'None!'}</p>
                <a href="${job.link || job.url}" target="_blank" class="view-link">View Job <i class="fa-solid fa-arrow-right"></i></a>
            </div>
        `;
        jobsContainer.appendChild(card);
    });
}

window.trackJob = async function(company, title, url) {
    showLoading("AI is tailoring your resume for this role...");
    try {
        const res = await fetch('/api/applications/track', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ user_id: currentUserId, company_name: company, job_title: title, description_url: url })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);
        
        switchPage('page-results');
        document.querySelector('[data-pane="pane-tracker"]').click();
        loadTracker();
        
        // Show success animation/toast instead of ugly alert in true prod
    } catch(e) {
        alert(e);
        switchPage('page-results');
    }
};

async function loadTracker() {
    try {
        const res = await fetch(`/api/applications/${currentUserId}`, { headers: getHeaders() });
        const apps = await res.json();
        
        trackerContainer.innerHTML = '';
        if(apps.length === 0) {
            trackerContainer.innerHTML = "<p class=\"empty-state\">You haven't tracked any jobs yet.</p>";
            return;
        }
        
        apps.forEach(app => {
            const card = document.createElement('div');
            card.className = 'crm-job-card tracker-card';
            
            let bulletsHTML = '';
            if (app.tailored_resume_bullets) {
                try {
                    const blts = JSON.parse(app.tailored_resume_bullets);
                    bulletsHTML = blts.map(b => `<div class="bullet-item"><i class="fa-solid fa-circle bullet-dot"></i> ${b}</div>`).join('');
                } catch(e) {}
            }
            
            card.innerHTML = `
                <div class="tracker-header">
                    <div>
                        <h3>${app.job_title}</h3>
                        <p><i class="fa-regular fa-building"></i> ${app.company_name}</p>
                    </div>
                    <span class="status-badge ready">${app.status}</span>
                </div>
                ${bulletsHTML ? `
                    <div class="tailored-section">
                        <div class="section-label"><i class="fa-solid fa-check-double"></i> AI Tailored Bullets (Copy to application)</div>
                        <div class="pre-tailored">${bulletsHTML}</div>
                    </div>
                ` : ''}
            `;
            trackerContainer.appendChild(card);
        });
    } catch(e) {
        console.error(e);
    }
}

// --- STUDIO LOGIC ---
let interviewSessionId = null;

const startBtn = document.getElementById('start-interview-btn');
const setupDiv = document.getElementById('studio-setup');
const activeDiv = document.getElementById('studio-active');
const chatArea = document.getElementById('interview-chat');
const submitAnswerBtn = document.getElementById('submit-answer-btn');
const answerInput = document.getElementById('interview-answer-input');

startBtn.addEventListener('click', async () => {
    const role = document.getElementById('interview-role').value || "Senior Software Engineer";
    const diff = document.getElementById('interview-diff').value || 5;

    showLoading("Initiating AI Interviewer...");
    try {
        const res = await fetch('/interview/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ role: role, difficulty: diff, weak_areas: [] })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        interviewSessionId = data.session_id;
        
        setupDiv.classList.add('hidden');
        activeDiv.classList.remove('hidden');
        
        chatArea.innerHTML = `<div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
            <strong style="color: #60a5fa;"><i class="fa-solid fa-robot"></i> Jobify Interview AI:</strong><br><br>${data.question}
        </div>`;
        
        switchPage('page-results');
    } catch(e) {
        alert(e);
        switchPage('page-results');
    }
});

submitAnswerBtn.addEventListener('click', async () => {
    const ans = answerInput.value.trim();
    if (!ans) return;
    
    // Add User bubble
    chatArea.innerHTML += `<div style="background: rgba(255, 255, 255, 0.05); padding: 15px; margin-bottom: 15px; border-radius: 4px; text-align: right;">
        <strong style="color: #9ca3af;">You:</strong><br><br>${ans}
    </div>`;
    answerInput.value = '';
    
    // Loading bubble
    const loaderId = 'loader-' + Date.now();
    chatArea.innerHTML += `<div id="${loaderId}" style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
        <strong style="color: #60a5fa;"><i class="fa-solid fa-robot"></i> Jobify Interview AI:</strong><br><br><i class="fa-solid fa-spinner fa-spin"></i> Analyzing and preparing response...
    </div>`;
    chatArea.scrollTop = chatArea.scrollHeight;

    try {
        const res = await fetch('/interview/answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ session_id: interviewSessionId, answer: ans })
        });
        const data = await res.json();
        
        const loaderElt = document.getElementById(loaderId);
        if (loaderElt) loaderElt.remove();

        if (!res.ok) throw new Error(data.error);

        const evalScore = data.evaluation?.score || "N/A";
        const evalFb = data.evaluation?.improvements || "Good answer.";
        
        chatArea.innerHTML += `<div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
            <strong style="color: #34d399;"><i class="fa-solid fa-check"></i> Analysis (Score: ${evalScore}/10):</strong><br><br>${evalFb}
        </div>`;
        
        chatArea.innerHTML += `<div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
            <strong style="color: #60a5fa;"><i class="fa-solid fa-robot"></i> Jobify Interview AI:</strong><br><br>${data.next_question}
        </div>`;

        chatArea.scrollTop = chatArea.scrollHeight;
    } catch(e) {
        alert("Error: " + e.message);
    }
});

// --- TABS LOGIC ---
const tabs = document.querySelectorAll('.tab');
const panes = document.querySelectorAll('.pane');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active', 'hidden'));
        panes.forEach(p => p.classList.add('hidden'));
        
        tab.classList.add('active');
        const paneId = tab.getAttribute('data-pane');
        document.getElementById(paneId).classList.remove('hidden');
        document.getElementById(paneId).classList.add('active');
    });
});
