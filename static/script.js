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

const dashboardResumeInput = document.getElementById('dashboard-resume-input');
const chooseDashboardResumeBtn = document.getElementById('choose-dashboard-resume-btn');
const dashboardResumeFileInfo = document.getElementById('dashboard-resume-file-info');
const dashboardResumeFileName = document.getElementById('dashboard-resume-file-name');
const replaceResumeBtn = document.getElementById('replace-resume-btn');
const scoreResumeBtn = document.getElementById('score-resume-btn');
const resumeTargetRole = document.getElementById('resume-target-role');
const resumeScoreContainer = document.getElementById('resume-score-container');
let dashboardSelectedResume = null;

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

function getErrorMessage(data, fallback) {
    if (!data || typeof data !== 'object') return fallback;
    return data.detail || data.error || data.message || fallback;
}

async function readResponseData(res) {
    const text = await res.text();
    if (!text) return {};
    try {
        return JSON.parse(text);
    } catch (_) {
        return { error: text };
    }
}

async function uploadResumeFile(file) {
    const fd = new FormData();
    fd.append('file', file);

    const res = await fetch('/api/resume/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` },
        body: fd,
    });
    const data = await readResponseData(res);
    if (!res.ok) throw new Error(getErrorMessage(data, 'Upload failed.'));
    return data;
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
        const data = await readResponseData(res);
        if (!res.ok) throw new Error(getErrorMessage(data, 'Authentication failed.'));

        authToken = data.access_token;
        localStorage.setItem('jobify_token', authToken);
        currentUserId = data.user_id;
        currentUsername = data.username;
        displayUser.innerText = currentUsername;
        showToast('Login successful.', 'success');

        if (data.has_resume) {
            showLoading('Login successful. Loading your saved job feed...');
            await loadDailyFeed();
        } else {
            switchPage('page-home');
        }
    } catch (err) {
        const message = err.message === 'Failed to fetch'
            ? 'Could not reach the server. Refresh the page and try again.'
            : err.message;
        showToast(message, 'error');
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

    showLoading('Saving resume securely...');
    try {
        await uploadResumeFile(selectedFile);
        loadDailyFeed();
    } catch (err) {
        showToast(err.message, 'error');
        switchPage('page-home');
    }
});

if (chooseDashboardResumeBtn && dashboardResumeInput) {
    chooseDashboardResumeBtn.addEventListener('click', () => dashboardResumeInput.click());
}

if (dashboardResumeInput) {
    dashboardResumeInput.addEventListener('change', e => {
        dashboardSelectedResume = e.target.files?.[0] || null;
        if (!dashboardSelectedResume) return;

        dashboardResumeFileInfo?.classList.remove('hidden');
        if (dashboardResumeFileName) dashboardResumeFileName.textContent = dashboardSelectedResume.name;
        if (replaceResumeBtn) replaceResumeBtn.disabled = false;
    });
}

if (replaceResumeBtn) {
    replaceResumeBtn.addEventListener('click', async () => {
        if (!dashboardSelectedResume || !authToken) return;

        showLoading('Replacing your saved resume...');
        try {
            await uploadResumeFile(dashboardSelectedResume);
            showToast('Resume replaced successfully.', 'success');
            switchPage('page-results');
            document.querySelector('[data-pane="pane-resume"]')?.click();
            dashboardSelectedResume = null;
            if (dashboardResumeInput) dashboardResumeInput.value = '';
            dashboardResumeFileInfo?.classList.add('hidden');
            replaceResumeBtn.disabled = true;
        } catch (err) {
            showToast(err.message, 'error');
            switchPage('page-results');
            document.querySelector('[data-pane="pane-resume"]')?.click();
        }
    });
}

if (scoreResumeBtn) {
    scoreResumeBtn.addEventListener('click', async () => {
        if (!authToken) return;

        const originalHTML = scoreResumeBtn.innerHTML;
        scoreResumeBtn.disabled = true;
        scoreResumeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scoring...';
        if (resumeScoreContainer) {
            resumeScoreContainer.className = 'resume-score-empty';
            resumeScoreContainer.textContent = 'Analyzing resume impact, ATS clarity, and section strength...';
        }

        try {
            const res = await fetch('/api/resume/analyze', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ target_role: resumeTargetRole?.value?.trim() || '' }),
            });
            const data = await readResponseData(res);
            if (!res.ok) throw new Error(getErrorMessage(data, 'Resume scoring failed.'));
            renderResumeScore(data);
        } catch (err) {
            if (resumeScoreContainer) {
                resumeScoreContainer.className = 'resume-score-empty';
                resumeScoreContainer.textContent = err.message;
            }
            showToast(err.message, 'error');
        } finally {
            scoreResumeBtn.disabled = false;
            scoreResumeBtn.innerHTML = originalHTML;
        }
    });
}

// ─── Job Feed ─────────────────────────────────────────────────────────────────
async function loadDailyFeed() {
    switchPage('page-loading');
    const loadingText = document.getElementById('loading-text');
    const steps = [
        'Parsing your resume...',
        'Inferring best-fit roles with AI...',
        'Searching live job listings...',
        'Scoring and ranking your matches...',
        'Almost there...'
    ];
    let stepIdx = 0;
    loadingText.innerText = steps[0];
    const stepTimer = setInterval(() => {
        stepIdx = Math.min(stepIdx + 1, steps.length - 1);
        loadingText.innerText = steps[stepIdx];
    }, 9000);

    try {
        const res = await fetch('/api/jobs/feed', { headers: getAuthHeaders() });
        const data = await readResponseData(res);
        clearInterval(stepTimer);
        if (!res.ok) throw new Error(getErrorMessage(data, 'Feed error'));
        renderJobs(data.jobs || []);
        switchPage('page-results');
        loadTracker();
        return true;
    } catch (err) {
        clearInterval(stepTimer);
        renderJobs([]);
        switchPage('page-results');
        showToast('Job feed unavailable right now: ' + err.message, 'error');
        return false;
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
                <p><strong>Missing Skills:</strong> ${missing || 'None — great fit!'}</p>
                <div class="card-footer-row">
                    <a href="${sanitize(link)}" target="_blank" rel="noopener" class="view-link">View Job <i class="fa-solid fa-arrow-right"></i></a>
                </div>
            </div>`;
        jobsContainer.appendChild(card);
    });

    // Event delegation — handles all track buttons on the page
    jobsContainer.addEventListener('click', e => {
        const btn = e.target.closest('.track-btn');
        if (btn) trackJob(btn.dataset.company, btn.dataset.title, btn.dataset.url);
    });
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
        const data = await readResponseData(res);
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
        const apps = await readResponseData(res);

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

function renderResumeScore(data) {
    if (!resumeScoreContainer) return;

    const score = Math.max(0, Math.min(100, Number(data.score) || 0));
    const issues = Array.isArray(data.issues) ? data.issues : [];
    const improvements = Array.isArray(data.improvements) ? data.improvements : [];
    const sectionFeedback = data.section_feedback && typeof data.section_feedback === 'object'
        ? data.section_feedback
        : {};

    const issueItems = issues.length
        ? issues.map(item => `<li>${sanitize(String(item))}</li>`).join('')
        : '<li>No major issues returned.</li>';
    const improvementItems = improvements.length
        ? improvements.map(item => `<li>${sanitize(String(item))}</li>`).join('')
        : '<li>No improvements returned.</li>';
    const feedbackBoxes = Object.entries(sectionFeedback).map(([section, feedback]) => `
        <div class="resume-feedback-box">
            <strong>${sanitize(section)}</strong>
            <span>${sanitize(String(feedback))}</span>
        </div>
    `).join('');

    resumeScoreContainer.className = 'resume-score-card';
    resumeScoreContainer.innerHTML = `
        <div class="resume-score-top">
            <div class="resume-score-ring" style="--score-angle:${score * 3.6}deg">
                <span>${score}</span>
            </div>
            <div class="resume-score-title">
                <h4>Resume Score: ${score}/100</h4>
                <p>${score >= 80 ? 'Strong resume foundation. Focus on polish and role alignment.' : score >= 60 ? 'Solid base, with clear opportunities to improve ATS and recruiter impact.' : 'Needs focused improvements before applying broadly.'}</p>
            </div>
        </div>
        <div class="resume-analysis-section">
            <h5>Issues</h5>
            <ul>${issueItems}</ul>
        </div>
        <div class="resume-analysis-section">
            <h5>Improvements</h5>
            <ul>${improvementItems}</ul>
        </div>
        ${feedbackBoxes ? `
            <div class="resume-analysis-section">
                <h5>Section Feedback</h5>
                <div class="resume-feedback-grid">${feedbackBoxes}</div>
            </div>
        ` : ''}
    `;
}

// ─── Interview Studio (VOXA-style Chatbot) ───────────────────────────────────
const startBtn        = document.getElementById('start-interview-btn');
const newInterviewBtn = document.getElementById('new-interview-btn');
const activeDiv       = document.getElementById('studio-active');
const chatMessages    = document.getElementById('interview-chat');
const submitAnswerBtn = document.getElementById('submit-answer-btn');
const answerInput     = document.getElementById('interview-answer-input');
const emptyState      = document.getElementById('chat-empty-state');
const diffSlider      = document.getElementById('interview-diff');
const diffLabel       = document.getElementById('diff-label');
const sessionsList    = document.getElementById('sessions-list');
let scores = [];
let activeSidebarItem = null;

// Diff slider live label
if (diffSlider) {
    diffSlider.addEventListener('input', () => {
        diffLabel.textContent = diffSlider.value;
        const pct = ((diffSlider.value - 1) / 9) * 100;
        diffSlider.style.background = `linear-gradient(to right, var(--primary) ${pct}%, rgba(255,255,255,0.1) ${pct}%)`;
    });
}

// Auto-grow textarea
answerInput.addEventListener('input', () => {
    answerInput.style.height = 'auto';
    answerInput.style.height = Math.min(answerInput.scrollHeight, 140) + 'px';
});

// Shift+Enter = new line, Enter = submit
answerInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitAnswerBtn.click(); }
});

// ── Start new session ────────────────────────────────────────
startBtn.addEventListener('click', async () => {
    const role = document.getElementById('interview-role').value.trim() || 'Software Engineer';
    const diff = parseInt(diffSlider?.value) || 5;

    setStartBtnLoading(true);
    try {
        const res = await fetch('/api/interview/start', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ role, difficulty: diff, weak_areas: [] }),
        });
        const data = await readResponseData(res);
        if (!res.ok) throw new Error(data.error || data.detail);

        interviewSessionId = data.session_id;
        scores = [];

        openChatView(role, diff);
        appendMsg('ai', data.question);
        loadSessionsList();  // refresh sidebar
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setStartBtnLoading(false);
    }
});

// ── New interview button (reset form) ────────────────────────
newInterviewBtn.addEventListener('click', () => {
    document.getElementById('sidebar-setup').classList.remove('hidden');
    emptyState.classList.remove('hidden');
    activeDiv.classList.add('hidden');
    if (activeSidebarItem) { activeSidebarItem.classList.remove('active'); activeSidebarItem = null; }
    interviewSessionId = null;
    scores = [];
    chatMessages.innerHTML = '';
    document.getElementById('interview-role').value = '';
    diffSlider.value = 5;
    diffLabel.textContent = '5';
});

// ── Submit answer ────────────────────────────────────────────
submitAnswerBtn.addEventListener('click', async () => {
    const ans = answerInput.value.trim();
    if (!ans || !interviewSessionId) return;

    appendMsg('user', ans);
    answerInput.value = '';
    answerInput.style.height = 'auto';
    submitAnswerBtn.disabled = true;

    const typingId = appendTyping();

    try {
        const res = await fetch('/api/interview/answer', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ session_id: interviewSessionId, answer: ans }),
        });
        const data = await readResponseData(res);
        removeTyping(typingId);
        if (!res.ok) throw new Error(data.error || data.detail);

        const score = data.evaluation?.score ?? null;
        const feedback = data.evaluation?.improvements || '';

        if (feedback) appendMsg('feedback', feedback, score);
        if (data.next_question) appendMsg('ai', data.next_question);

        if (score !== null) {
            scores.push(score);
            const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
            document.getElementById('chat-score-display').textContent = `Avg Score: ${avg.toFixed(1)}/10`;
        }
    } catch (err) {
        removeTyping(typingId);
        showToast(err.message, 'error');
    } finally {
        submitAnswerBtn.disabled = false;
        answerInput.focus();
    }
});

// ── Load past sessions into sidebar ─────────────────────────
async function loadSessionsList() {
    if (!authToken) return;
    try {
        const res = await fetch('/api/interview/sessions', { headers: getAuthHeaders() });
        if (!res.ok) return;
        const sessions = await readResponseData(res);
        sessionsList.innerHTML = '';
        if (sessions.length === 0) {
            sessionsList.innerHTML = '<p class="sidebar-empty">No sessions yet.</p>';
            return;
        }
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = 'session-item';
            item.dataset.id = s.id;
            item.dataset.token = s.session_token;
            const date = new Date(s.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
            const scoreText = s.avg_score !== null ? `<span class="session-score">⭐ ${Number(s.avg_score).toFixed(1)}</span>` : '';
            item.innerHTML = `
                <div class="session-item-info">
                    <div class="session-role">${sanitize(s.role)}</div>
                    <div class="session-meta">
                        <span>${date}</span>
                        <span>D:${s.difficulty}</span>
                        ${scoreText}
                    </div>
                </div>
                <button class="session-delete" title="Delete session" data-id="${s.id}">
                    <i class="fa-solid fa-trash-can"></i>
                </button>`;

            // Delete handler
            item.querySelector('.session-delete').addEventListener('click', async (e) => {
                e.stopPropagation(); // prevent opening chat
                if (!confirm("Are you sure you want to delete this interview session?")) return;

                try {
                    const res = await fetch(`/api/interview/sessions/${s.id}`, {
                        method: 'DELETE',
                        headers: getAuthHeaders()
                    });
                    if (!res.ok) throw new Error("Failed to delete session");
                    item.remove();
                    if (sessionsList.children.length === 0) {
                        sessionsList.innerHTML = '<p class="sidebar-empty">No sessions yet.</p>';
                    }
                    if (activeSidebarItem === item) newInterviewBtn.click(); // clear screen
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });

            // Open session handler
            item.addEventListener('click', () => loadSessionHistory(s.id, s.role, s.difficulty, item));
            sessionsList.appendChild(item);
        });
    } catch (err) {
        console.error('Session list error:', err);
    }
}

// ── Load a specific session's history ────────────────────────
async function loadSessionHistory(sessionDbId, role, difficulty, sidebarEl) {
    try {
        const res = await fetch(`/api/interview/sessions/${sessionDbId}`, { headers: getAuthHeaders() });
        if (!res.ok) return;
        const data = await readResponseData(res);

        interviewSessionId = data.session_token || null;
        scores = data.messages.filter(m => m.score !== undefined).map(m => m.score);

        openChatView(role, difficulty);
        chatMessages.innerHTML = '';

        data.messages.forEach(m => {
            if (m.role === 'ai')       appendMsg('ai', m.content, null, true);
            else if (m.role === 'user') appendMsg('user', m.content, null, true);
            else if (m.role === 'feedback') appendMsg('feedback', m.content, m.score, true);
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (scores.length > 0) {
            const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
            document.getElementById('chat-score-display').textContent = `Avg Score: ${avg.toFixed(1)}/10`;
        }

        if (activeSidebarItem) activeSidebarItem.classList.remove('active');
        sidebarEl.classList.add('active');
        activeSidebarItem = sidebarEl;
    } catch (err) {
        showToast('Failed to load session history', 'error');
    }
}

// ── UI helpers ───────────────────────────────────────────────
function openChatView(role, diff) {
    emptyState.classList.add('hidden');
    activeDiv.classList.remove('hidden');
    chatMessages.innerHTML = '';
    document.getElementById('chat-role-label').textContent = role;
    document.getElementById('chat-diff-badge').textContent = `Difficulty ${diff}/10`;
    document.getElementById('chat-score-display').textContent = '';
}

function appendMsg(role, content, score = null, noScroll = false) {
    const wrap = document.createElement('div');
    wrap.className = `msg ${role}`;

    const senderMap = { ai: '<i class="fa-solid fa-robot"></i> Jobify AI', user: 'You', feedback: '<i class="fa-solid fa-check-circle"></i> AI Analysis' };
    wrap.innerHTML = `
        <span class="msg-sender">${senderMap[role] || role}</span>
        <div class="msg-bubble">${sanitize(content)}</div>
        ${score !== null && role === 'feedback' ? `<span class="msg-score-pill"><i class="fa-solid fa-star"></i> ${score}/10</span>` : ''}`;

    chatMessages.appendChild(wrap);
    if (!noScroll) chatMessages.scrollTop = chatMessages.scrollHeight;
    return wrap;
}

function appendTyping() {
    const id = 'typing-' + Date.now();
    const wrap = document.createElement('div');
    wrap.className = 'msg ai';
    wrap.id = id;
    wrap.innerHTML = `
        <span class="msg-sender"><i class="fa-solid fa-robot"></i> Jobify AI</span>
        <div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTyping(id) { document.getElementById(id)?.remove(); }

function setStartBtnLoading(loading) {
    startBtn.disabled = loading;
    startBtn.innerHTML = loading
        ? '<i class="fa-solid fa-spinner fa-spin"></i> Starting...'
        : '<i class="fa-solid fa-play"></i> Start Interview';
}

// Load sessions list whenever interview tab is clicked
document.querySelector('[data-pane="pane-interview"]')?.addEventListener('click', loadSessionsList, { once: false });



// ─── Tab navigation ───────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.pane').forEach(p => { p.classList.add('hidden'); p.classList.remove('active'); });
        tab.classList.add('active');

        const paneId = tab.dataset.pane;
        const pane = document.getElementById(paneId);
        if (pane) { pane.classList.remove('hidden'); pane.classList.add('active'); }

        // Hide viewport wrapper when on fullscreen interview pane to prevent spacing issues
        const viewport = document.getElementById('scrollable-viewport');
        if (viewport) {
            viewport.style.display = (paneId === 'pane-interview') ? 'none' : 'flex';
        }
    });
});

// ─── Security: XSS sanitizer ─────────────────────────────────────────────────
function sanitize(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
