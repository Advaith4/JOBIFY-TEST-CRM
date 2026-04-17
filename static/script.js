/**
 * Jobify AI CRM — Frontend Controller
 * All API calls secured with JWT Bearer token stored in localStorage.
 * New endpoints:  /api/auth/login  /api/resume/upload
 *                 /api/jobs/feed   /api/jobs/track   /api/jobs/tracker
 *                 /api/interview/start  /api/interview/answer
 */

// ─── State ────────────────────────────────────────────────────────────────────
let currentUserId = null;
let currentUsername = null;
let authToken = localStorage.getItem("jobify_token") || null;
let interviewSessionId = null;

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const pages = {
    login:   document.getElementById('page-login'),
    home:    document.getElementById('page-home'),
    loading: document.getElementById('page-loading'),
    results: document.getElementById('page-results'),
};

const loginForm    = document.getElementById('modern-login-form');
const loginBtn     = document.getElementById('login-btn');
const loginInput   = document.getElementById('login-username');
const loginPass    = document.getElementById('login-password');
const pwdToggle    = document.getElementById('pwd-toggle');
const emailCheck   = document.querySelector('.auth-check');
const emailError   = document.getElementById('email-error');
const pwdStrength  = document.getElementById('pwd-strength');
const strengthFill = document.querySelector('.strength-fill');
const strengthText = document.querySelector('.strength-text');

const fileInput  = document.getElementById('file-input');
const uploadBtn  = document.getElementById('upload-db-btn');
const fileInfo   = document.getElementById('file-info');
const fileNameSpan = document.getElementById('file-name');
let selectedFile = null;

const displayUser      = document.getElementById('display-user');
const jobsContainer    = document.getElementById('jobs-container');
const trackerContainer = document.getElementById('tracker-container');

// ─── Helpers ──────────────────────────────────────────────────────────────────
function switchPage(pageId) {
    Object.values(pages).forEach(p => {
        p.classList.toggle('hidden', p.id !== pageId);
        p.classList.toggle('active', p.id === pageId);
    });
}

function showLoading(text = 'Processing...') {
    document.getElementById('loading-text').innerText = text;
    switchPage('page-loading');
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
    };
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fa-solid fa-${type === 'success' ? 'check-circle' : 'circle-exclamation'}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3500);
}

// ─── Login UI Enhancements ────────────────────────────────────────────────────
pwdToggle.addEventListener('click', () => {
    const type = loginPass.getAttribute('type') === 'password' ? 'text' : 'password';
    loginPass.setAttribute('type', type);
    pwdToggle.innerHTML = type === 'password'
        ? '<i class="fa-regular fa-eye"></i>'
        : '<i class="fa-regular fa-eye-slash"></i>';
});

loginInput.addEventListener('input', e => {
    const val = e.target.value.trim();
    if (val.length >= 3) {
        emailCheck.classList.remove('hidden');
        emailError.classList.remove('show');
        loginInput.classList.remove('input-error');
    } else {
        emailCheck.classList.add('hidden');
        if (val.length > 0) {
            emailError.innerText = 'Username must be at least 3 characters';
            emailError.classList.add('show');
            loginInput.classList.add('input-error');
        } else {
            emailError.classList.remove('show');
            loginInput.classList.remove('input-error');
        }
    }
});

loginPass.addEventListener('input', e => {
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

// ─── Login Submission ──────────────────────────────────────────────────────────
loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const username = loginInput.value.trim();
    const password = loginPass.value;
    if (!username || !password) return showToast('Please enter both username and password.', 'error');

    const originalHTML = loginBtn.innerHTML;
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Authenticating...</span>';

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Authentication failed.');

        authToken = data.access_token;
        localStorage.setItem('jobify_token', authToken);
        currentUserId = data.user_id;
        currentUsername = data.username;
        displayUser.innerText = currentUsername;

        if (data.has_resume) {
            loadDailyFeed();
        } else {
            switchPage('page-home');
        }
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerHTML = originalHTML;
    }
});

// ─── File Upload ──────────────────────────────────────────────────────────────
fileInput.addEventListener('change', e => {
    if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        fileInfo.classList.remove('hidden');
        fileNameSpan.textContent = selectedFile.name;
        uploadBtn.disabled = false;
    }
});

uploadBtn.addEventListener('click', async () => {
    if (!selectedFile || !authToken) return;
    const fd = new FormData();
    fd.append('file', selectedFile);

    showLoading('Saving resume securely...');
    try {
        const res = await fetch('/api/resume/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: fd,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Upload failed.');
        loadDailyFeed();
    } catch (err) {
        showToast(err.message, 'error');
        switchPage('page-home');
    }
});

// ─── Job Feed ─────────────────────────────────────────────────────────────────
async function loadDailyFeed() {
    showLoading('AI agents analysing your profile...');
    try {
        const res = await fetch('/api/jobs/feed', { headers: getAuthHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Feed error');
        renderJobs(data.jobs || []);
        switchPage('page-results');
        loadTracker();
    } catch (err) {
        showToast('Feed error: ' + err.message, 'error');
        switchPage('page-login');
    }
}

function renderJobs(jobs) {
    jobsContainer.innerHTML = '';
    if (jobs.length === 0) {
        jobsContainer.innerHTML = '<p class="empty-state">No matching jobs found. Try uploading an updated resume.</p>';
        return;
    }
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'crm-job-card';
        // Sanitize before injecting — prevents XSS from AI-generated content
        const title   = sanitize(job.role || job.title || 'Unknown Role');
        const company = sanitize(job.company || 'Unknown Company');
        const score   = Number(job.match_score) || 0;
        const missing = Array.isArray(job.missing_skills) ? job.missing_skills.map(sanitize).join(', ') : 'None';
        const link    = job.link || job.url || '#';

        card.innerHTML = `
            <div class="card-header">
                <div>
                    <h3>${title}</h3>
                    <p><i class="fa-solid fa-building"></i> ${company}</p>
                    <span class="deep-match-badge">Match: ${score}%</span>
                </div>
                <button class="btn-outline track-btn" data-company="${company}" data-title="${title}" data-url="${sanitize(link)}">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Track &amp; Auto-Tailor
                </button>
            </div>
            <div class="card-footer">
                <p><strong>Missing Skills:</strong> ${missing}</p>
                <a href="${sanitize(link)}" target="_blank" rel="noopener" class="view-link">View Job <i class="fa-solid fa-arrow-right"></i></a>
            </div>`;
        jobsContainer.appendChild(card);
    });

    // Event delegation — no inline onclick
    jobsContainer.addEventListener('click', e => {
        const btn = e.target.closest('.track-btn');
        if (btn) trackJob(btn.dataset.company, btn.dataset.title, btn.dataset.url);
    }, { once: true });
}

// ─── Tracker ──────────────────────────────────────────────────────────────────
async function trackJob(company, title, url) {
    showLoading('Submitting to tracker...');
    try {
        const res = await fetch('/api/jobs/track', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ company_name: company, job_title: title, description_url: url }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        switchPage('page-results');
        document.querySelector('[data-pane="pane-tracker"]').click();
        showToast('Job tracked! AI is tailoring your resume in the background.');
        // Poll tracker every 5 seconds until status changes from "Tailoring..."
        loadTracker();
        const poll = setInterval(async () => {
            await loadTracker();
            const cards = trackerContainer.querySelectorAll('.status-badge');
            const stillTailoring = [...cards].some(c => c.textContent.includes('Tailoring'));
            if (!stillTailoring) clearInterval(poll);
        }, 5000);
    } catch (err) {
        showToast(err.message, 'error');
        switchPage('page-results');
    }
}

async function loadTracker() {
    try {
        const res = await fetch('/api/jobs/tracker', { headers: getAuthHeaders() });
        if (!res.ok) return;
        const apps = await res.json();

        trackerContainer.innerHTML = '';
        if (apps.length === 0) {
            trackerContainer.innerHTML = '<p class="empty-state">No tracked jobs yet. Click "Track & Auto-Tailor" on a job card.</p>';
            return;
        }

        apps.forEach(app => {
            const card = document.createElement('div');
            card.className = 'crm-job-card tracker-card';

            let bulletsHTML = '';
            if (app.tailored_resume_bullets) {
                try {
                    const bullets = JSON.parse(app.tailored_resume_bullets);
                    bulletsHTML = bullets.map(b => `
                        <div class="bullet-item">
                            <i class="fa-solid fa-circle bullet-dot"></i>
                            ${sanitize(b)}
                        </div>`).join('');
                } catch (_) {}
            }

            const statusClass = app.status === 'Draft Ready' ? 'ready' : app.status === 'Tailoring...' ? 'tailoring' : '';
            card.innerHTML = `
                <div class="tracker-header">
                    <div>
                        <h3>${sanitize(app.job_title)}</h3>
                        <p><i class="fa-regular fa-building"></i> ${sanitize(app.company_name || '')}</p>
                    </div>
                    <span class="status-badge ${statusClass}">${sanitize(app.status)}</span>
                </div>
                ${bulletsHTML ? `
                    <div class="tailored-section">
                        <div class="section-label"><i class="fa-solid fa-check-double"></i> AI Tailored Resume Bullets</div>
                        <div class="pre-tailored">${bulletsHTML}</div>
                    </div>` : (app.status === 'Tailoring...' ? '<p class="empty-state" style="margin-top:1rem"><i class="fa-solid fa-spinner fa-spin"></i> AI is tailoring your resume...</p>' : '')}
            `;
            trackerContainer.appendChild(card);
        });
    } catch (err) {
        console.error('Tracker load error:', err);
    }
}

// ─── Interview Studio ────────────────────────────────────────────────────────
const startBtn       = document.getElementById('start-interview-btn');
const setupDiv       = document.getElementById('studio-setup');
const activeDiv      = document.getElementById('studio-active');
const chatArea       = document.getElementById('interview-chat');
const submitAnswerBtn = document.getElementById('submit-answer-btn');
const answerInput    = document.getElementById('interview-answer-input');

startBtn.addEventListener('click', async () => {
    const role = document.getElementById('interview-role').value.trim() || 'Software Engineer';
    const diff = parseInt(document.getElementById('interview-diff').value) || 5;

    showLoading('Initialising AI Interviewer...');
    try {
        const res = await fetch('/api/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, difficulty: diff, weak_areas: [] }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        interviewSessionId = data.session_id;
        setupDiv.classList.add('hidden');
        activeDiv.classList.remove('hidden');
        chatArea.innerHTML = aiChatBubble(data.question);
        switchPage('page-results');
    } catch (err) {
        showToast(err.message, 'error');
        switchPage('page-results');
    }
});

submitAnswerBtn.addEventListener('click', async () => {
    const ans = answerInput.value.trim();
    if (!ans) return;

    chatArea.innerHTML += userChatBubble(ans);
    answerInput.value = '';
    const loaderId = 'loader-' + Date.now();
    chatArea.innerHTML += loadingBubble(loaderId);
    chatArea.scrollTop = chatArea.scrollHeight;

    try {
        const res = await fetch('/api/interview/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: interviewSessionId, answer: ans }),
        });
        const data = await res.json();
        document.getElementById(loaderId)?.remove();
        if (!res.ok) throw new Error(data.error);

        const score = data.evaluation?.score ?? 'N/A';
        const feedback = data.evaluation?.improvements || 'Good answer!';
        chatArea.innerHTML += feedbackBubble(score, sanitize(feedback));
        chatArea.innerHTML += aiChatBubble(sanitize(data.next_question || ''));
        chatArea.scrollTop = chatArea.scrollHeight;
    } catch (err) {
        document.getElementById(loaderId)?.remove();
        showToast(err.message, 'error');
    }
});

// ─── Chat bubble templates ────────────────────────────────────────────────────
const aiChatBubble = q => `
    <div class="chat-bubble ai-bubble">
        <strong><i class="fa-solid fa-robot"></i> Jobify AI</strong>
        <p>${q}</p>
    </div>`;
const userChatBubble = a => `
    <div class="chat-bubble user-bubble">
        <strong>You</strong>
        <p>${sanitize(a)}</p>
    </div>`;
const feedbackBubble = (score, fb) => `
    <div class="chat-bubble feedback-bubble">
        <strong><i class="fa-solid fa-check"></i> Analysis — Score: ${score}/10</strong>
        <p>${fb}</p>
    </div>`;
const loadingBubble = id => `
    <div id="${id}" class="chat-bubble ai-bubble">
        <strong><i class="fa-solid fa-robot"></i> Jobify AI</strong>
        <p><i class="fa-solid fa-spinner fa-spin"></i> Thinking...</p>
    </div>`;

// ─── Tab navigation ───────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.pane').forEach(p => { p.classList.add('hidden'); p.classList.remove('active'); });
        tab.classList.add('active');
        const pane = document.getElementById(tab.dataset.pane);
        if (pane) { pane.classList.remove('hidden'); pane.classList.add('active'); }
    });
});

// ─── Security: XSS sanitizer ─────────────────────────────────────────────────
function sanitize(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
