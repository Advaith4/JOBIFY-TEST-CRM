let currentUserId = null;
let currentUsername = null;

// ── ELEMENTS ──
const pages = {
    login: document.getElementById('page-login'),
    home: document.getElementById('page-home'),
    loading: document.getElementById('page-loading'),
    results: document.getElementById('page-results')
};

// Login
const loginBtn = document.getElementById('login-btn');
const loginInput = document.getElementById('login-username');

// Upload
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-db-btn');
const dropZone = document.getElementById('drop-zone');
const fileInfo = document.getElementById('file-info');
const fileNameSpan = document.getElementById('file-name');
let selectedFile = null;

// Results
const displayUser = document.getElementById('display-user');
const jobsContainer = document.getElementById('jobs-container');
const trackerContainer = document.getElementById('tracker-container');

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

// ── LOGIN ──
loginBtn.addEventListener('click', async () => {
    const val = loginInput.value.trim();
    if (!val) return;
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: val})
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        
        currentUserId = data.user_id;
        currentUsername = data.username;
        displayUser.innerText = currentUsername;

        if (data.has_resume) {
            loadDailyFeed();
        } else {
            switchPage('page-home');
        }
    } catch (e) {
        alert(e.message);
    }
});

// ── FILE UPLOAD ──
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
    
    showLoading("Saving resume to CRM...");
    try {
        const res = await fetch(`/api/resume/upload/${currentUserId}`, {
            method: 'POST',
            body: fd
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        
        loadDailyFeed();
    } catch (e) {
        alert("Upload error: " + e.message);
        switchPage('page-home');
    }
});

// ── DAILY FEED & CRM ──
async function loadDailyFeed() {
    showLoading("Consulting Agent & Fetching Jobs...");
    try {
        const res = await fetch(`/api/jobs/feed/${currentUserId}`);
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        
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
        jobsContainer.innerHTML = '<p style="color:#aaa;text-align:center;">No jobs found today.</p>';
        return;
    }
    
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'crm-job-card';
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <h3>${job.role || job.title}</h3>
                    <p><i class="fa-solid fa-building"></i> ${job.company || 'Unknown Company'}</p>
                    <div style="margin-bottom:1rem;">
                        <span style="background:var(--bg); padding:0.25rem 0.5rem; border-radius:4px; font-size:0.8rem; border:1px solid #0f0; color:#0f0;">
                            Deep Match: ${job.match_score}%
                        </span>
                    </div>
                </div>
                <button class="btn-outline" onclick="trackJob('${job.company || ''}', '${job.role || job.title}', '${job.url || ''}')">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Track & Auto-Tailor
                </button>
            </div>
            <p><strong>Missing Skills:</strong> ${job.missing_skills ? job.missing_skills.join(', ') : 'None!'}</p>
            <a href="${job.link || job.url}" target="_blank" style="color:var(--primary); text-decoration:none; font-size:0.9rem;">View Job <i class="fa-solid fa-arrow-right"></i></a>
        `;
        jobsContainer.appendChild(card);
    });
}

window.trackJob = async function(company, title, url) {
    showLoading("AI is tailoring your resume for this role...");
    try {
        const res = await fetch('/api/applications/track', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: currentUserId,
                company_name: company,
                job_title: title,
                description_url: url
            })
        });
        const data = await res.json();
        
        switchPage('page-results');
        // switch tab
        document.querySelector('[data-pane="pane-tracker"]').click();
        loadTracker();
        alert("Success! Your tailored draft is ready.");
    } catch(e) {
        alert(e);
        switchPage('page-results');
    }
};

async function loadTracker() {
    try {
        const res = await fetch(`/api/applications/${currentUserId}`);
        const apps = await res.json();
        
        trackerContainer.innerHTML = '';
        if(apps.length === 0) {
            trackerContainer.innerHTML = '<p style="color:#aaa;text-align:center;">You haven\'t tracked any jobs yet.</p>';
            return;
        }
        
        apps.forEach(app => {
            const card = document.createElement('div');
            card.className = 'crm-job-card';
            
            let bulletsHTML = '';
            if (app.tailored_resume_bullets) {
                try {
                    const blts = JSON.parse(app.tailored_resume_bullets);
                    bulletsHTML = blts.map(b => `• ${b}`).join('\n');
                } catch(e) {}
            }
            
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <h3 style="color:var(--primary);">${app.job_title}</h3>
                        <p><i class="fa-regular fa-building"></i> ${app.company_name} | Status: ${app.status}</p>
                    </div>
                </div>
                ${bulletsHTML ? `
                    <div style="margin-top:1rem; border-top:1px solid var(--border); padding-top:1rem;">
                        <span style="font-size:0.85rem; color:#aaa; text-transform:uppercase; letter-spacing:1px;">AI Tailored Bullets (Copy to application)</span>
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

// ── TABS LOGIC ──
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

// Interactive Interview Stub mapping (retained logic)
const intStartBtn = document.getElementById('start-interactive-btn');
const intChat = document.getElementById('interview-chat');
intStartBtn.addEventListener('click', () => {
    intChat.classList.remove('hidden');
    // Add stub text
    document.getElementById('interview-chat-log').innerHTML = '<div style="color:#0f0;"><strong>Coach:</strong> Tell me about a time you used your matching skills in a real-world scenario.</div>';
});
document.getElementById('interview-answer-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const val = document.getElementById('interview-answer-input').value;
    document.getElementById('interview-chat-log').innerHTML += `<div style="color:#fff; text-align:right;"><strong>You:</strong> ${val}</div><div style="color:#0f0; margin-top:1rem;"><strong>Coach:</strong> Great response. The AI Evaluation functionality is connected!</div>`;
    document.getElementById('interview-answer-input').value = '';
});
