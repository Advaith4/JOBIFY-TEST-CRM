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
const usernameError = document.getElementById('username-error');
const pwdStrength  = document.getElementById('pwd-strength');
const strengthFill = document.querySelector('.strength-fill');
const strengthText = document.querySelector('.strength-text');

const fileInput  = document.getElementById('file-input');
const uploadBtn  = document.getElementById('upload-db-btn');
const fileInfo   = document.getElementById('file-info');
const fileNameSpan = document.getElementById('file-name');
const dropZone = document.getElementById('drop-zone');
let selectedFile = null;

const displayUser      = document.getElementById('display-user');
const jobsContainer    = document.getElementById('jobs-container');
const trackerContainer = document.getElementById('tracker-container');
const jobsFeedHeadline = document.getElementById('jobs-feed-headline');
const jobsFeedNote = document.getElementById('jobs-feed-note');
const jobsRoleMix = document.getElementById('jobs-role-mix');
const jobsGapFocus = document.getElementById('jobs-gap-focus');
const jobsGapNote = document.getElementById('jobs-gap-note');
const jobsBestMatch = document.getElementById('jobs-best-match');
const jobsBestMatchNote = document.getElementById('jobs-best-match-note');

const coachStreakCount = document.getElementById('coach-streak-count');
const coachStreakCopy = document.getElementById('coach-streak-copy');
const coachResumeScore = document.getElementById('coach-resume-score');
const coachResumeScoreCopy = document.getElementById('coach-resume-score-copy');
const coachResumeScoreDelta = document.getElementById('coach-resume-score-delta');
const coachConfidenceScore = document.getElementById('coach-confidence-score');
const coachConfidenceCopy = document.getElementById('coach-confidence-copy');
const coachConfidenceDelta = document.getElementById('coach-confidence-delta');
const coachSessionCount = document.getElementById('coach-session-count');
const coachPlanHeadline = document.getElementById('coach-plan-headline');
const coachPlanNote = document.getElementById('coach-plan-note');
const coachDailyTasks = document.getElementById('coach-daily-tasks');
const coachWeakAreas = document.getElementById('coach-weak-areas');
const coachWeakDrill = document.getElementById('coach-weak-drill');
const coachScoreTrend = document.getElementById('coach-score-trend');
const coachConfidenceTrend = document.getElementById('coach-confidence-trend');
const coachFeedbackSummary = document.getElementById('coach-feedback-summary');
const coachTrainingMode = document.getElementById('coach-training-mode');
const coachPersona = document.getElementById('coach-persona');
const coachDomainFocus = document.getElementById('coach-domain-focus');
const coachTargetRole = document.getElementById('coach-target-role');
const coachStartInterviewBtn = document.getElementById('coach-start-interview-btn');
const coachFixResumeBtn = document.getElementById('coach-fix-resume-btn');
const coachRefreshPlanBtn = document.getElementById('coach-refresh-plan-btn');
const coachDailyGain = document.getElementById('coach-daily-gain');
const coachReadyState = document.getElementById('coach-ready-state');
const coachNextActionBtn = document.getElementById('coach-next-action-btn');
const coachNextActionCopy = document.getElementById('coach-next-action-copy');
const coachProgressToggle = document.getElementById('coach-progress-toggle');
const coachAdvancedToggle = document.getElementById('coach-advanced-toggle');
const coachProgressPanel = document.getElementById('coach-progress-panel');
const coachAdvancedPanel = document.getElementById('coach-advanced-panel');
const coachProgressArrow = document.getElementById('coach-progress-arrow');
const coachAdvancedArrow = document.getElementById('coach-advanced-arrow');

const resumeHealthBadge = document.getElementById('resume-health-badge');
const resumeStrengthEl = document.getElementById('resume-strength');
const resumeCriticalCountEl = document.getElementById('resume-critical-count');
const resumeHealthBreakdown = document.getElementById('resume-health-breakdown');
const resumeHealthHint = document.getElementById('resume-health-hint');

const dashboardResumeInput = document.getElementById('dashboard-resume-input');
const chooseDashboardResumeBtn = document.getElementById('choose-dashboard-resume-btn');
const dashboardResumeFileInfo = document.getElementById('dashboard-resume-file-info');
const dashboardResumeFileName = document.getElementById('dashboard-resume-file-name');
const replaceResumeBtn = document.getElementById('replace-resume-btn');
const scoreResumeBtn = document.getElementById('score-resume-btn');
const resumeTargetRole = document.getElementById('resume-target-role');
const resumeScoreContainer = document.getElementById('resume-score-container');
const resumeScoreRing = document.getElementById('resume-score-ring');
const resumeScoreValue = document.getElementById('resume-score-value');
const resumeScoreHeadline = document.getElementById('resume-score-headline');
const resumeScoreCaption = document.getElementById('resume-score-caption');
const resumeAppliedCount = document.getElementById('resume-applied-count');
const resumeOpenIssues = document.getElementById('resume-open-issues');
const resumeWordCount = document.getElementById('resume-word-count');
const resumeStreakCount = document.getElementById('resume-streak-count');
const resumeConfidenceLabel = document.getElementById('resume-confidence-label');
const resumeConfidenceBar = document.getElementById('resume-confidence-bar');
const resumeSectionHeatmap = document.getElementById('resume-section-heatmap');
const resumeNextActionText = document.getElementById('resume-next-action-text');
const resumeNextActionBtn = document.getElementById('resume-next-action-btn');
const resumeFixPacks = document.getElementById('resume-fix-packs');
const resumePriorityFixes = document.getElementById('resume-priority-fixes');
const resumePriorityCount = document.getElementById('resume-priority-count');
const resumePriorityGuidance = document.getElementById('resume-priority-guidance');
const resumeFixProgressBar = document.getElementById('resume-fix-progress-bar');
const resumeFixProgressText = document.getElementById('resume-fix-progress-text');
const resumeScoreDelta = document.getElementById('resume-score-delta');
const resumeCompletionState = document.getElementById('resume-completion-state');
const resumeInlineFeedback = document.getElementById('resume-inline-feedback');
const resumeDraftPreview = document.getElementById('resume-draft-preview');
const resumeStatusBadge = document.getElementById('resume-status-badge');
const resumeViewModeTag = document.getElementById('resume-view-mode-tag');
const fixTopIssuesBtn = document.getElementById('fix-top-issues-btn');
const toggleFixModeBtn = document.getElementById('toggle-fix-mode-btn');
const rescoreResumeBtn = document.getElementById('rescore-resume-btn');
const downloadResumeBtn = document.getElementById('download-resume-btn');
const resumeStartInterviewBtn = document.getElementById('resume-start-interview-btn');
const resumeExportSummary = document.getElementById('resume-export-summary');
const resumeCompareToggle = document.getElementById('resume-compare-toggle');
const resumeEditorPanel = document.getElementById('resume-editor-panel');
const resumeSummaryText = document.getElementById('resume-summary-text');
const resumeExperienceText = document.getElementById('resume-experience-text');
const resumeProjectsText = document.getElementById('resume-projects-text');
const resumeSkillsText = document.getElementById('resume-skills-text');
const saveResumeTextBtn = document.getElementById('save-resume-text-btn');
const cancelFixModeBtn = document.getElementById('cancel-fix-mode-btn');
const resumeSuggestionBanner = document.getElementById('resume-suggestion-banner');
const resumeSuggestionText = document.getElementById('resume-suggestion-text');
let dashboardSelectedResume = null;
let resumeLabState = {
    has_resume: false,
    original_resume: '',
    current_resume: '',
    parsed_resume: {},
    last_analysis: null,
    applied_fixes: [],
    stats: {},
    ui: { pendingRescoreTimer: null },
};
let resumeLabLoaded = false;
let resumeCompareView = 'after';
let resumeFeedbackTimer = null;
let resumeStreakState = { count: 0, lastDate: null };
let dailyProgressState = { date: null, points: 0, completed: 0, lastEvent: '' };
let coachDashboardLoaded = false;
let coachState = {
    memory: null,
    plan: null,
    modes: null,
    resumeLab: null,
    latestFeedback: null,
    ui: { lastAvgScore: null, lastConfidence: null },
};
const appUIState = {
    currentView: 'dashboard',
    panels: {
        progress: false,
        advanced: false,
    },
};

function setPanelExpanded(panel, expanded) {
    if (!panel) return;
    panel.classList.toggle('is-collapsed', !expanded);
}

function updateCoachDisclosureUI() {
    const progressOpen = !!appUIState.panels.progress;
    const advancedOpen = !!appUIState.panels.advanced;
    setPanelExpanded(coachProgressPanel, progressOpen);
    setPanelExpanded(coachAdvancedPanel, advancedOpen);
    if (coachProgressArrow) coachProgressArrow.textContent = progressOpen ? '▴' : '▾';
    if (coachAdvancedArrow) coachAdvancedArrow.textContent = advancedOpen ? '▴' : '▾';
}

function setCurrentView(view) {
    const safeView = ['dashboard', 'resume', 'interview'].includes(view) ? view : 'dashboard';
    appUIState.currentView = safeView;
    document.body.dataset.view = safeView;
}

function getResumeStrengthLabel(score) {
    const value = Number(score);
    if (!Number.isFinite(value)) return { label: '--', tone: 'moderate' };
    if (value >= 80) return { label: 'Strong', tone: 'strong' };
    if (value >= 65) return { label: 'Moderate', tone: 'moderate' };
    return { label: 'Weak', tone: 'weak' };
}

function normalizeHealthStatus(level) {
    if (level === 'pass' || level === 'ok') return 'pass';
    if (level === 'fail' || level === 'error') return 'fail';
    return 'warn';
}

function deriveHealthCategoryStatus(analysis, category) {
    if (!analysis) {
        return { level: 'warn', label: 'Needs analysis', count: 0 };
    }

    const breakdown = analysis.breakdown || {};
    const score = clampScore(analysis.score);
    const openIssues = countOpenIssues(analysis);

    const metricScore = key => clampScore(breakdown?.[key] ?? 0);
    const impact = metricScore('impact');
    const clarity = metricScore('clarity');
    const structure = metricScore('structure');
    const ats = metricScore('ats');

    const allIssues = getAllResumeIssues(analysis);
    const matchIssue = issue => categorizeIssue(issue) === category;
    const categoryOpen = allIssues.filter(issue => matchIssue(issue) && issue.status !== 'applied' && !getAppliedIssueIds().has(issue.id));

    // Prefer metric score mapping when available; otherwise fall back to issue counts.
    let base = null;
    if (category === 'formatting') base = clarity || null;
    if (category === 'metrics') base = impact || null;
    if (category === 'keywords') base = ats || null;
    if (category === 'structure') base = structure || null;

    const count = categoryOpen.length;

    if (base !== null) {
        const level = base >= 78 ? 'pass' : base >= 62 ? 'warn' : 'fail';
        const label = level === 'pass' ? 'Good' : level === 'warn' ? 'Improve' : 'Critical';
        return { level, label, count };
    }

    // No breakdown data; infer from issues + overall score.
    if (openIssues === 0 && score >= 75) return { level: 'pass', label: 'Good', count };
    if (count === 0) return { level: 'pass', label: 'Good', count: 0 };
    if (count <= 2) return { level: 'warn', label: 'Improve', count };
    return { level: 'fail', label: 'Critical', count };
}

function categorizeIssue(issue) {
    const problem = String(issue?.problem || '').toLowerCase();
    const actionType = String(issue?.action_type || '').toLowerCase();
    const combined = `${problem} ${actionType}`;

    const has = (...needles) => needles.some(n => combined.includes(n));

    if (has('keyword', 'ats', 'match', 'search', 'missing keyword', 'recruiter')) return 'keywords';
    if (has('metric', 'quantif', 'number', 'impact', '%', 'measur')) return 'metrics';
    if (has('format', 'spacing', 'typo', 'grammar', 'punct', 'readability')) return 'formatting';
    if (has('structure', 'section', 'order', 'layout', 'flow', 'bullets')) return 'structure';
    return 'structure';
}

function renderResumeHealthPanel(analysis) {
    if (!resumeHealthBadge || !resumeStrengthEl || !resumeCriticalCountEl || !resumeHealthBreakdown) return;

    if (!analysis) {
        resumeHealthBadge.className = 'health-badge';
        resumeHealthBadge.textContent = '--';
        resumeStrengthEl.textContent = '--';
        resumeCriticalCountEl.textContent = '--';
        if (resumeHealthHint) resumeHealthHint.textContent = 'Run Resume Lab analysis to generate a diagnosis.';

        resumeHealthBreakdown.querySelectorAll('.health-row').forEach(row => {
            row.classList.remove('pass', 'warn', 'fail');
            row.classList.add('warn');
            row.querySelector('.health-icon').textContent = '⚠';
            row.querySelector('.health-status').textContent = 'Needs analysis';
        });
        return;
    }

    const score = clampScore(analysis.score);
    const strength = getResumeStrengthLabel(score);
    const openIssues = countOpenIssues(analysis);
    const criticalIssues = getAllResumeIssues(analysis).filter(issue => {
        const status = String(issue?.status || '').toLowerCase();
        const isApplied = getAppliedIssueIds().has(issue?.id) || status === 'applied';
        if (isApplied) return false;
        const problem = String(issue?.problem || '').toLowerCase();
        return problem.includes('critical') || problem.includes('must') || problem.includes('severe');
    });

    resumeStrengthEl.textContent = strength.label;
    resumeCriticalCountEl.textContent = String(criticalIssues.length || Math.min(openIssues, 6));

    resumeHealthBadge.className = `health-badge ${strength.tone}`;
    resumeHealthBadge.textContent = strength.label;
    if (resumeHealthHint) {
        resumeHealthHint.textContent = openIssues
            ? 'Click an item to jump to the most relevant fix.'
            : 'Looking good — keep polishing with one targeted fix.';
    }

    const categories = ['formatting', 'metrics', 'keywords', 'structure'];
    const iconFor = level => (level === 'pass' ? '✓' : level === 'warn' ? '⚠' : '✕');
    categories.forEach(cat => {
        const row = resumeHealthBreakdown.querySelector(`[data-health-area="${cat}"]`);
        if (!row) return;
        const status = deriveHealthCategoryStatus(analysis, cat);
        const level = normalizeHealthStatus(status.level);
        row.classList.remove('pass', 'warn', 'fail');
        row.classList.add(level);
        row.querySelector('.health-icon').textContent = iconFor(level);
        row.querySelector('.health-status').textContent = status.count ? `${status.label} · ${status.count}` : status.label;
    });
}

async function openResumeLabAndFocusCategory(category) {
    document.querySelector('[data-pane="pane-resume"]')?.click();
    await loadResumeLab(false);

    const analysis = resumeLabState.last_analysis;
    if (!analysis) return;

    const allIssues = getAllResumeIssues(analysis);
    const firstMatch = allIssues.find(issue => categorizeIssue(issue) === category && issue.status !== 'applied' && !getAppliedIssueIds().has(issue.id));
    if (firstMatch) {
        focusEditorOnIssue(firstMatch);
        resumeScoreContainer?.scrollIntoView({ block: 'start', behavior: 'smooth' });
        return;
    }
    resumeScoreContainer?.scrollIntoView({ block: 'start', behavior: 'smooth' });
}
let latestJobsFeed = [];
let trackerPollTimer = null;
let authRedirectInProgress = false;

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
    const headers = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers.Authorization = `Bearer ${authToken}`;
    }
    return headers;
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

function handleAuthExpired() {
    if (authRedirectInProgress) return;
    authRedirectInProgress = true;
    authToken = null;
    localStorage.removeItem('jobify_token');
    showToast('Session expired. Please sign in again.', 'error');
    switchPage('page-login');
    setTimeout(() => { authRedirectInProgress = false; }, 500);
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

function patchResumeLabState(patch = {}) {
    resumeLabState = {
        ...resumeLabState,
        ...patch,
        ui: {
            ...(resumeLabState.ui || {}),
            ...(patch.ui || {}),
        },
    };
    return resumeLabState;
}

function patchCoachState(patch = {}) {
    coachState = {
        ...coachState,
        ...patch,
        ui: {
            ...(coachState.ui || {}),
            ...(patch.ui || {}),
        },
    };
    return coachState;
}

function cloneState(value) {
    if (typeof structuredClone === 'function') {
        return structuredClone(value);
    }
    return JSON.parse(JSON.stringify(value));
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function shouldRetryRequest(method, status, attempt, retries) {
    if (attempt >= retries) return false;
    if (method !== 'GET') return false;
    return status === 429 || status >= 500;
}

async function api(url, options = {}, config = {}) {
    const method = String(options.method || 'GET').toUpperCase();
    const retries = Number.isInteger(config.retries) ? config.retries : (method === 'GET' ? 1 : 0);
    const retryDelay = Number(config.retryDelay) || 450;
    const isFormData = options.body instanceof FormData;
    const headers = options.headers || {};
    const authHeader = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
    const mergedHeaders = isFormData
        ? { ...authHeader, ...headers }
        : { ...getAuthHeaders(), ...headers };

    let lastError = null;

    for (let attempt = 0; attempt <= retries; attempt += 1) {
        try {
            const res = await fetch(url, { ...options, method, headers: mergedHeaders });
            const data = config.expect === 'blob' ? await res.blob() : await readResponseData(res);

            if (!res.ok) {
                if (res.status === 401) {
                    handleAuthExpired();
                }
                const message = getErrorMessage(data, 'Request failed.');
                if (shouldRetryRequest(method, res.status, attempt, retries)) {
                    lastError = new Error(message);
                    await wait(retryDelay * (attempt + 1));
                    continue;
                }
                const error = new Error(message);
                error.retryable = false;
                throw error;
            }

            return data;
        } catch (err) {
            lastError = err instanceof Error ? err : new Error('Network request failed.');
            if (attempt >= retries || err?.retryable === false) break;
            await wait(retryDelay * (attempt + 1));
        }
    }

    throw lastError || new Error('Request failed.');
}

async function uploadResumeFile(file) {
    const fd = new FormData();
    fd.append('file', file);
    return api('/api/resume/upload', {
        method: 'POST',
        body: fd,
    });
}

async function apiJSON(url, options = {}, config = {}) {
    return api(url, options, config);
}

function setButtonLoading(btn, loading, loadingLabel = 'Working...') {
    if (!btn) return;
    if (loading) {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${loadingLabel}`;
        return;
    }
    btn.disabled = false;
    if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
        delete btn.dataset.originalHtml;
    }
}

function clampScore(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return 0;
    return Math.max(0, Math.min(100, Math.round(num)));
}

function showResumeFeedback(message, type = 'info') {
    if (!resumeInlineFeedback) return;
    if (resumeFeedbackTimer) clearTimeout(resumeFeedbackTimer);
    const icon = type === 'success'
        ? 'circle-check'
        : type === 'error'
            ? 'triangle-exclamation'
            : 'circle-info';
    resumeInlineFeedback.className = `resume-inline-feedback ${type}`;
    resumeInlineFeedback.innerHTML = `<i class="fa-solid fa-${icon}"></i><span>${sanitize(message)}</span>`;
    resumeInlineFeedback.classList.remove('hidden');
    resumeFeedbackTimer = setTimeout(() => {
        resumeInlineFeedback.classList.add('hidden');
    }, 3200);
}

function getAllResumeIssues(analysis) {
    if (!analysis || !Array.isArray(analysis.sections)) return [];
    return analysis.sections.flatMap(section => Array.isArray(section.issues) ? section.issues : []);
}

function getAppliedIssueIds() {
    return new Set((resumeLabState.applied_fixes || []).map(fix => fix.issue_id));
}

function getOptimisticIssueIds() {
    return new Set(
        (resumeLabState.applied_fixes || [])
            .filter(fix => fix.optimistic)
            .map(fix => fix.issue_id)
    );
}

const RESUME_SEGMENT_ACRONYMS = {
    ai: 'AI',
    api: 'API',
    apis: 'APIs',
    ats: 'ATS',
    aws: 'AWS',
    css: 'CSS',
    cv: 'CV',
    db: 'DB',
    gpa: 'GPA',
    html: 'HTML',
    ios: 'iOS',
    java: 'Java',
    js: 'JS',
    json: 'JSON',
    llm: 'LLM',
    ml: 'ML',
    nlp: 'NLP',
    oop: 'OOP',
    pdf: 'PDF',
    python: 'Python',
    rag: 'RAG',
    react: 'React',
    rest: 'REST',
    sql: 'SQL',
    ui: 'UI',
    ux: 'UX',
};

const RESUME_WORD_LEXICON = new Set([
    'a', 'ability', 'able', 'about', 'across', 'add', 'agent', 'agents', 'analysis', 'and',
    'app', 'application', 'applications', 'as', 'backend', 'build', 'building', 'can',
    'clean', 'clear', 'code', 'coding', 'comma', 'computer', 'data', 'deep', 'design',
    'designed', 'detected', 'development', 'efficient', 'engineer', 'engineering', 'experience',
    'fast', 'focus', 'foundations', 'framework', 'frameworks', 'functionalities', 'generative', 'impact',
    'improved', 'in', 'integrate', 'intelligent', 'is', 'job', 'keyword', 'keywords',
    'knowledge', 'languages', 'large', 'maintainable', 'matching', 'model', 'models', 'multi',
    'no', 'of', 'on', 'platforms', 'possesses', 'problem', 'problem-solving', 'programming',
    'project', 'projects', 'readable', 'recruiter', 'reduce', 'science', 'section',
    'separated', 'skills', 'skilled', 'software', 'solving', 'strong', 'strongest', 'student',
    'summary', 'system', 'systems', 'the', 'third', 'to', 'tools', 'was', 'with', 'working',
    'year', 'your', ...Object.keys(RESUME_SEGMENT_ACRONYMS),
]);

const MAX_RESUME_SEGMENT_WORD_LEN = Math.max(...Array.from(RESUME_WORD_LEXICON, word => word.length));
const RESUME_LONG_ALPHA_RUN_RE = /[A-Za-z]{8,}/g;
const RESUME_CHARACTER_SPACED_TOKEN_RE = /^[A-Za-z0-9&/(),.;:+-]$/;
const RESUME_COMPACT_TERM_FIXES = [
    [/\bFast API\b/g, 'FastAPI'],
    [/\bJava Script\b/g, 'JavaScript'],
    [/\bType Script\b/g, 'TypeScript'],
    [/\bNode JS\b/g, 'Node.js'],
    [/\bNext JS\b/g, 'Next.js'],
];
const resumeSegmentCache = new Map();

function repairResumeDisplayText(text) {
    if (!text) return '';

    return String(text)
        .replace(/\r\n?/g, '\n')
        .split('\n')
        .map(rawLine => {
            let line = collapseCharacterSpacedLine(rawLine);
            line = line.replace(/(?<=[a-z])(?=[A-Z])/g, ' ');
            line = line.replace(/(?<=[A-Z])(?=[A-Z][a-z])/g, ' ');
            line = line.replace(/(?<=[,;:])(?=[A-Za-z0-9])/g, ' ');
            line = line.replace(/(?<=[.!?])(?=[A-Z])/g, ' ');
            line = line.replace(/\/(?=[A-Za-z]{8,})/g, '/ ');
            line = line.replace(RESUME_LONG_ALPHA_RUN_RE, token => segmentResumeAlphaRun(token));
            RESUME_COMPACT_TERM_FIXES.forEach(([pattern, replacement]) => {
                line = line.replace(pattern, replacement);
            });
            line = line.replace(/[ \t]{2,}/g, ' ');
            return line.trim();
        })
        .join('\n')
        .trim();
}

function collapseCharacterSpacedLine(line) {
    const tokens = String(line || '').trim().split(/\s+/).filter(Boolean);
    if (tokens.length < 6) return String(line || '');

    const characterTokens = tokens.filter(token => RESUME_CHARACTER_SPACED_TOKEN_RE.test(token)).length;
    if ((characterTokens / tokens.length) < 0.65) return String(line || '');

    return tokens.join('');
}

function segmentResumeAlphaRun(token) {
    const lowered = String(token || '').toLowerCase();
    if (lowered.length < 8 || RESUME_WORD_LEXICON.has(lowered)) return token;

    const parts = fullySegmentResumeAlphaRun(lowered);
    if (!Array.isArray(parts) || parts.length < 2) return token;
    return restoreResumeSegmentCase(parts, token);
}

function fullySegmentResumeAlphaRun(lowered) {
    if (resumeSegmentCache.has(lowered)) return resumeSegmentCache.get(lowered);

    const memo = new Map();
    const solve = index => {
        if (index === lowered.length) return { score: 0, parts: [] };
        if (memo.has(index)) return memo.get(index);

        let best = null;
        const maxEnd = Math.min(lowered.length, index + MAX_RESUME_SEGMENT_WORD_LEN);
        for (let end = maxEnd; end > index; end -= 1) {
            const word = lowered.slice(index, end);
            if (!RESUME_WORD_LEXICON.has(word)) continue;
            const tail = solve(end);
            if (!tail) continue;
            const score = word.length * word.length + tail.score;
            if (!best || score > best.score) {
                best = { score, parts: [word, ...tail.parts] };
            }
        }

        memo.set(index, best);
        return best;
    };

    const result = solve(0);
    const parts = result ? result.parts : null;
    resumeSegmentCache.set(lowered, parts);
    return parts;
}

function restoreResumeSegmentCase(parts, original) {
    const source = String(original || '');
    const originalIsUpper = source && source.toUpperCase() === source;
    return parts.map((part, index) => {
        if (RESUME_SEGMENT_ACRONYMS[part]) return RESUME_SEGMENT_ACRONYMS[part];
        if (originalIsUpper) return part.toUpperCase();
        if (index === 0 && /^[A-Z]/.test(source)) return part.charAt(0).toUpperCase() + part.slice(1);
        return part;
    }).join(' ');
}

function normalizeResumeTextList(values) {
    return Array.isArray(values)
        ? values.map(value => repairResumeDisplayText(String(value || '').trim())).filter(Boolean)
        : [];
}

function normalizeParsedResume(parsed, fallbackText = '') {
    const fallback = fallbackText
        ? parseResumeTextForPreview(fallbackText)
        : { summary: '', experience: [], projects: [], skills: [], education: [], other: [] };
    const source = parsed && typeof parsed === 'object' ? parsed : {};
    return {
        summary: repairResumeDisplayText(source.summary || fallback.summary || ''),
        experience: normalizeResumeTextList(source.experience || fallback.experience || []),
        projects: normalizeResumeTextList(source.projects || fallback.projects || []),
        skills: normalizeResumeTextList(source.skills || fallback.skills || []),
        education: normalizeResumeTextList(source.education || fallback.education || []),
        other: normalizeResumeTextList(source.other || fallback.other || []),
    };
}

function normalizeAppliedFixes(appliedFixes) {
    return Array.isArray(appliedFixes)
        ? appliedFixes.map(fix => ({
            ...fix,
            original: repairResumeDisplayText(fix?.original || ''),
            improved: repairResumeDisplayText(fix?.improved || ''),
        }))
        : [];
}

function getDisplayScore(analysis) {
    if (!analysis) return 0;
    const totalIssues = getAllResumeIssues(analysis).length;
    const appliedCount = getAppliedIssueIds().size;
    const progressBoost = totalIssues ? Math.round((appliedCount / totalIssues) * 15) : 0;
    return clampScore(clampScore(analysis.score) + progressBoost);
}

function getDisplayBreakdown(analysis) {
    if (!analysis) {
        return { impact: 0, clarity: 0, structure: 0, ats: 0 };
    }
    const totalIssues = getAllResumeIssues(analysis).length;
    const appliedCount = getAppliedIssueIds().size;
    const ratio = totalIssues ? appliedCount / totalIssues : 0;
    const nudges = {
        impact: Math.round(ratio * 10),
        clarity: Math.round(ratio * 8),
        structure: Math.round(ratio * 7),
        ats: Math.round(ratio * 6),
    };
    return {
        impact: clampScore((analysis.breakdown?.impact || 0) + nudges.impact),
        clarity: clampScore((analysis.breakdown?.clarity || 0) + nudges.clarity),
        structure: clampScore((analysis.breakdown?.structure || 0) + nudges.structure),
        ats: clampScore((analysis.breakdown?.ats || 0) + nudges.ats),
    };
}

function parseResumeTextForPreview(text) {
    const lines = String(repairResumeDisplayText(text) || '')
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean);

    const parsed = {
        summary: '',
        experience: [],
        projects: [],
        skills: [],
        education: [],
        other: [],
    };

    const headingMap = {
        summary: 'summary',
        profile: 'summary',
        objective: 'summary',
        experience: 'experience',
        'work experience': 'experience',
        projects: 'projects',
        project: 'projects',
        skills: 'skills',
        education: 'education',
    };

    let current = 'summary';
    const summaryLines = [];

    lines.forEach(line => {
        const normalized = line.toLowerCase().replace(/[^a-z\s]/g, '').trim();
        if (headingMap[normalized]) {
            current = headingMap[normalized];
            return;
        }

        if (current === 'skills') {
            line.split(/[|,]/).map(item => item.trim()).filter(Boolean).forEach(item => parsed.skills.push(item));
            return;
        }

        const clean = line.replace(/^[-*•]\s*/, '').trim();
        if (!clean) return;

        if (current === 'summary' && summaryLines.length < 3) {
            summaryLines.push(clean);
            return;
        }

        if (Array.isArray(parsed[current])) {
            parsed[current].push(clean);
        } else {
            parsed.other.push(clean);
        }
    });

    parsed.summary = summaryLines.join(' ');
    return parsed;
}

function getResumeEditorFieldMap() {
    return {
        summary: resumeSummaryText,
        experience: resumeExperienceText,
        projects: resumeProjectsText,
        skills: resumeSkillsText,
    };
}

function isResumeEditorField(element) {
    return Object.values(getResumeEditorFieldMap()).includes(element);
}

function getResumeSectionsForEditing() {
    const parsed = resumeLabState.parsed_resume && Object.keys(resumeLabState.parsed_resume).length
        ? resumeLabState.parsed_resume
        : parseResumeTextForPreview(resumeLabState.current_resume || resumeLabState.original_resume || '');

    return {
        summary: String(parsed.summary || '').trim(),
        experience: Array.isArray(parsed.experience) ? parsed.experience.map(item => String(item).trim()).filter(Boolean) : [],
        projects: Array.isArray(parsed.projects) ? parsed.projects.map(item => String(item).trim()).filter(Boolean) : [],
        skills: Array.isArray(parsed.skills) ? parsed.skills.map(item => String(item).trim()).filter(Boolean) : [],
    };
}

function setResumeEditorValues(force = false) {
    const active = document.activeElement;
    if (!force && isResumeEditorField(active)) return;

    const sections = getResumeSectionsForEditing();
    if (resumeSummaryText) resumeSummaryText.value = sections.summary;
    if (resumeExperienceText) resumeExperienceText.value = sections.experience.join('\n');
    if (resumeProjectsText) resumeProjectsText.value = sections.projects.join('\n');
    if (resumeSkillsText) resumeSkillsText.value = sections.skills.join('\n');
}

function splitResumeEditorLines(value, { splitComma = false } = {}) {
    return String(value || '')
        .split(splitComma ? /\r?\n|,/ : /\r?\n/)
        .map(line => line.trim())
        .filter(Boolean);
}

function buildResumeTextFromEditor() {
    const sections = [
        {
            label: 'Summary',
            lines: splitResumeEditorLines(resumeSummaryText?.value || ''),
            asBullets: false,
        },
        {
            label: 'Experience',
            lines: splitResumeEditorLines(resumeExperienceText?.value || ''),
            asBullets: true,
        },
        {
            label: 'Projects',
            lines: splitResumeEditorLines(resumeProjectsText?.value || ''),
            asBullets: true,
        },
        {
            label: 'Skills',
            lines: splitResumeEditorLines(resumeSkillsText?.value || '', { splitComma: true }),
            asBullets: false,
        },
    ];

    return sections
        .filter(section => section.lines.length)
        .map(section => {
            const body = section.asBullets
                ? section.lines.map(line => `- ${line.replace(/^[-*•]\s*/, '')}`).join('\n')
                : section.label === 'Skills'
                    ? section.lines.join(', ')
                    : section.lines.join('\n');
            return `${section.label}\n${body}`;
        })
        .join('\n\n')
        .trim();
}

function syncResumeDraftFromEditor() {
    const currentResume = buildResumeTextFromEditor();
    patchResumeLabState({
        current_resume: currentResume,
        parsed_resume: parseResumeTextForPreview(currentResume),
    });
    renderResumePreview();
    if (resumeWordCount) resumeWordCount.textContent = String(countWords(currentResume));
}

function setRecentPreviewHighlights(lines = []) {
    const highlights = [...new Set(lines.map(line => String(line || '').trim()).filter(Boolean))];
    const existingTimer = resumeLabState.ui?.recentHighlightTimer;
    if (existingTimer) clearTimeout(existingTimer);

    patchResumeLabState({
        ui: {
            recentHighlightLines: highlights,
            recentHighlightTimer: null,
        },
    });

    if (!highlights.length) return;

    const timer = setTimeout(() => {
        patchResumeLabState({
            ui: {
                recentHighlightLines: [],
                recentHighlightTimer: null,
            },
        });
        renderResumePreview();
    }, 1800);

    patchResumeLabState({
        ui: {
            recentHighlightLines: highlights,
            recentHighlightTimer: timer,
        },
    });
}

function getLocalDateKey(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function getPreviousDateKey(date = new Date()) {
    const previous = new Date(date);
    previous.setDate(previous.getDate() - 1);
    return getLocalDateKey(previous);
}

function recordResumeLabStreak() {
    const storageKey = 'jobify_resume_lab_streak';
    const today = getLocalDateKey();
    let stored = {};
    try {
        stored = JSON.parse(localStorage.getItem(storageKey) || '{}');
    } catch (_) {
        stored = {};
    }

    if (stored.lastDate === today) {
        resumeStreakState = { count: Number(stored.count) || 1, lastDate: today };
    } else if (stored.lastDate === getPreviousDateKey()) {
        resumeStreakState = { count: (Number(stored.count) || 0) + 1, lastDate: today };
    } else {
        resumeStreakState = { count: 1, lastDate: today };
    }

    localStorage.setItem(storageKey, JSON.stringify(resumeStreakState));
    renderResumeStreak();
}

function renderResumeStreak() {
    if (resumeStreakCount) resumeStreakCount.textContent = String(resumeStreakState.count || 0);
}

function getDailyProgressSnapshot() {
    const storageKey = 'jobify_daily_progress';
    const today = getLocalDateKey();
    let stored = {};
    try {
        stored = JSON.parse(localStorage.getItem(storageKey) || '{}');
    } catch (_) {
        stored = {};
    }

    if (stored.date !== today) {
        dailyProgressState = { date: today, points: 0, completed: 0, lastEvent: '' };
        localStorage.setItem(storageKey, JSON.stringify(dailyProgressState));
        return dailyProgressState;
    }

    dailyProgressState = {
        date: today,
        points: Number(stored.points) || 0,
        completed: Number(stored.completed) || 0,
        lastEvent: String(stored.lastEvent || ''),
    };
    return dailyProgressState;
}

function recordDailyProgress(points, eventLabel) {
    const snapshot = getDailyProgressSnapshot();
    dailyProgressState = {
        ...snapshot,
        points: Math.max(0, snapshot.points + Math.max(0, Number(points) || 0)),
        completed: snapshot.completed + 1,
        lastEvent: String(eventLabel || snapshot.lastEvent || '').trim(),
    };
    localStorage.setItem('jobify_daily_progress', JSON.stringify(dailyProgressState));
}

function getOpenResumeIssues(analysis) {
    const appliedIds = getAppliedIssueIds();
    return getAllResumeIssues(analysis).filter(issue => !appliedIds.has(issue.id) && issue.status !== 'applied');
}

function getSectionScoreMap(analysis) {
    if (!analysis) return {};
    const rawScores = analysis.section_scores || {};
    if (rawScores && typeof rawScores === 'object' && !Array.isArray(rawScores)) {
        return Object.fromEntries(
            Object.entries(rawScores).map(([key, value]) => [String(key).toLowerCase(), clampScore(value)])
        );
    }

    const displayBreakdown = getDisplayBreakdown(analysis);
    const fallbackBase = Math.round((displayBreakdown.impact + displayBreakdown.clarity + displayBreakdown.structure + displayBreakdown.ats) / 4);
    const appliedIds = getAppliedIssueIds();
    const scores = {};
    (analysis.sections || []).forEach(section => {
        const sectionName = String(section.section || 'section').toLowerCase();
        const issues = Array.isArray(section.issues) ? section.issues : [];
        const openCount = issues.filter(issue => !appliedIds.has(issue.id) && issue.status !== 'applied').length;
        scores[sectionName] = clampScore(fallbackBase - Math.min(openCount * 8, 32));
    });
    return scores;
}

function getSectionScore(sectionName, analysis) {
    const scores = getSectionScoreMap(analysis);
    return clampScore(scores[String(sectionName || '').toLowerCase()] ?? 0);
}

function getHeatClass(score) {
    if (score >= 75) return 'heat-high';
    if (score >= 55) return 'heat-mid';
    return 'heat-low';
}

function getConfidenceScore(analysis) {
    if (!analysis) return 0;
    const totalIssues = getAllResumeIssues(analysis).length;
    const appliedCount = getAppliedIssueIds().size;
    const progress = totalIssues ? Math.round((appliedCount / totalIssues) * 100) : 0;
    return clampScore((getDisplayScore(analysis) * 0.72) + (progress * 0.28));
}

function getConfidenceLabel(score) {
    if (score >= 85) return 'Application-ready';
    if (score >= 70) return 'Strong draft';
    if (score >= 50) return 'Improving fast';
    if (score > 0) return 'Needs focus';
    return 'Not ready yet';
}

function setDeltaBadge(element, delta, suffix = '', decimals = 0) {
    if (!element) return;
    const safeDelta = Number.isFinite(Number(delta)) ? Number(delta) : 0;
    const value = decimals > 0 ? safeDelta.toFixed(decimals) : String(Math.round(safeDelta));
    const prefix = safeDelta > 0 ? '+' : safeDelta < 0 ? '' : '+';
    element.textContent = `${prefix}${value}${suffix}`;
    element.classList.remove('positive', 'negative', 'neutral');
    element.classList.add(safeDelta > 0 ? 'positive' : safeDelta < 0 ? 'negative' : 'neutral');
}

function getProgressMilestone(progress) {
    if (progress >= 100) return 'Milestone: all surfaced fixes are done.';
    if (progress >= 75) return 'Milestone: polish round reached.';
    if (progress >= 50) return 'Milestone: halfway through the high-impact fixes.';
    if (progress >= 25) return 'Milestone: strong early lift unlocked.';
    if (progress > 0) return 'Milestone: momentum started.';
    return 'Milestone: analysis unlocks your first sprint.';
}

function replaceFirstOccurrence(text, search, replacement) {
    const source = String(text || '');
    const target = String(search || '').trim();
    if (!source || !target || !source.includes(target)) return source;
    return source.replace(target, String(replacement || '').trim());
}

function markIssueAppliedLocally(issueId) {
    const snapshot = cloneState(resumeLabState);
    const analysis = snapshot?.last_analysis ? normalizeResumeAnalysis(snapshot.last_analysis) : null;
    if (!analysis) return null;

    let matchedIssue = null;
    analysis.sections.forEach(section => {
        (section.issues || []).forEach(issue => {
            if (issue.id === issueId) {
                issue.status = 'applied';
                matchedIssue = issue;
            }
        });
    });

    if (!matchedIssue) return null;

    const currentResume = replaceFirstOccurrence(snapshot.current_resume, matchedIssue.original, matchedIssue.improved);
    const appliedFixes = Array.isArray(snapshot.applied_fixes) ? [...snapshot.applied_fixes] : [];
    if (!appliedFixes.some(fix => fix.issue_id === issueId)) {
        appliedFixes.push({
            issue_id: issueId,
            original: matchedIssue.original || '',
            improved: matchedIssue.improved || '',
            optimistic: true,
        });
    }

    patchResumeLabState({
        current_resume: currentResume,
        parsed_resume: parseResumeTextForPreview(currentResume),
        applied_fixes: appliedFixes,
        last_analysis: analysis,
    });
    setRecentPreviewHighlights([matchedIssue.improved]);

    return snapshot;
}

async function performResumeRescore() {
    if (!authToken || !resumeLabState?.has_resume) return;

    setButtonLoading(rescoreResumeBtn, true, 'Re-scoring...');
    setResumeStatus('Analyzing');
    showResumeFeedback('Refreshing your score from the latest draft...', 'info');
    try {
        const data = await apiJSON('/api/resume/rescore', {
            method: 'POST',
            body: JSON.stringify({ target_role: resumeTargetRole?.value?.trim() || '' }),
        });
        mergeResumeLabState({
            has_resume: true,
            current_resume: data.current_resume,
            parsed_resume: data.parsed_resume,
            applied_fixes: data.applied_fixes,
            last_analysis: data,
        });
        recordResumeLabStreak();
        recordDailyProgress(2, 'Re-scored resume draft');
        renderResumeWorkbench();
        if (coachDashboardLoaded) renderCoachDashboard();
        showResumeFeedback('Fresh score loaded from your latest resume draft.', 'success');
        showToast('Resume re-scored successfully.', 'success');
    } catch (err) {
        setResumeStatus('Error');
        showResumeFeedback(err.message, 'error');
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(rescoreResumeBtn, false);
    }
}

function scheduleResumeRescore(options = {}) {
    if (!authToken || !resumeLabState?.has_resume) return;
    const immediate = !!options.immediate;
    const existingTimer = resumeLabState.ui?.pendingRescoreTimer;
    if (existingTimer) clearTimeout(existingTimer);

    if (immediate) {
        patchResumeLabState({ ui: { pendingRescoreTimer: null } });
        performResumeRescore();
        return;
    }

    setResumeStatus('Analyzing');
    showResumeFeedback('Queued a quick re-score. Keep fixing and we will refresh once you pause.', 'info');
    const timer = setTimeout(() => {
        patchResumeLabState({ ui: { pendingRescoreTimer: null } });
        performResumeRescore();
    }, 650);
    patchResumeLabState({ ui: { pendingRescoreTimer: timer } });
}

function findIssueSection(issueId, analysis) {
    for (const section of analysis?.sections || []) {
        if ((section.issues || []).some(issue => issue.id === issueId)) {
            return section.section || 'resume';
        }
    }
    return 'resume';
}

function getNextBestIssue(analysis) {
    const openIssues = getOpenResumeIssues(analysis);
    if (!openIssues.length) return null;
    return openIssues
        .map(issue => ({
            issue,
            score: /impact|metric|measurable|weak|result|quant/i.test(`${issue.problem} ${issue.improved}`) ? 3
                : /ats|keyword|skill/i.test(`${issue.problem} ${issue.improved}`) ? 2
                    : 1,
        }))
        .sort((a, b) => b.score - a.score)[0].issue;
}

function getPriorityGuidance(analysis) {
    const openIssues = getOpenResumeIssues(analysis);
    if (!openIssues.length) {
        return 'Next: Your highest-priority fixes are complete. Step into a resume-based interview while this draft is fresh.';
    }

    const metricHeavy = openIssues.filter(issue => /metric|measurable|quant|result|impact|outcome/i.test(`${issue.problem} ${issue.improved}`));
    if (metricHeavy.length >= 2) {
        return 'Next: Add measurable metrics to at least 2 sections so recruiters can see impact immediately.';
    }

    const atsHeavy = openIssues.filter(issue => /ats|keyword|skill|tool|technology/i.test(`${issue.problem} ${issue.improved}`));
    if (atsHeavy.length >= 2) {
        return 'Next: Strengthen ATS alignment by adding missing keywords to skills and experience bullets.';
    }

    const nextIssue = getNextBestIssue(analysis);
    const sectionName = nextIssue ? findIssueSection(nextIssue.id, analysis) : 'resume';
    return `Next: Tighten ${sectionName} first. That is the fastest path to a stronger, more trustworthy draft.`;
}

function buildFixPacks(analysis) {
    const openIssues = getOpenResumeIssues(analysis);
    const openIds = new Set(openIssues.map(issue => issue.id));
    const createPackPreview = issues => issues.slice(0, 2).map(issue => ({
        before: repairResumeDisplayText(issue.original || ''),
        after: repairResumeDisplayText(issue.improved || ''),
    }));
    const estimatePackGain = issues => issues.reduce((sum, issue) => (
        sum + (/high/i.test(issue.severity || '') ? 5 : /medium/i.test(issue.severity || '') ? 3 : 2)
    ), 0);
    const packs = [
        {
            id: 'impact',
            title: 'Impact Pack',
            description: 'Upgrade weak bullets with stronger verbs, outcomes, and measurable value.',
            details: [
                'Rewrites vague lines into outcome-driven bullets',
                'Adds stronger action verbs and clearer ownership',
                'Makes achievements easier for recruiters to believe fast',
            ],
            impact: 'Before: generic contribution blur. After: sharper ownership, clearer result, stronger credibility.',
            why_this_matters: 'Recruiters and interviewers look for measurable impact — this pack converts vague contributions into concrete outcomes that are easier to probe and trust.',
            real_world_impact: 'Improving impact phrasing makes your interview examples more persuasive and can increase callback rates by making achievements credible and scannable.',
            matcher: issue => /impact|metric|measurable|weak|verb|result|achievement/i.test(`${issue.problem} ${issue.improved}`),
        },
        {
            id: 'clarity',
            title: 'Clarity Pack',
            description: 'Make confusing or vague lines easier for recruiters to understand quickly.',
            details: [
                'Simplifies wording without losing technical depth',
                'Makes each bullet faster to scan',
                'Reduces ambiguity in role and project descriptions',
            ],
            impact: 'Before: dense or unclear lines. After: cleaner sentences that read like a polished real resume.',
            why_this_matters: 'Clear wording reduces ambiguity and the chance an interviewer will misinterpret your role or impact.',
            real_world_impact: 'Clearer bullets make it easier to narrate answers under pressure and reduce the likelihood of follow-up clarification questions.',
            matcher: issue => /clarity|vague|specific|clear|concise|structure/i.test(`${issue.problem} ${issue.improved}`),
        },
        {
            id: 'ats',
            title: 'ATS Pack',
            description: 'Improve keyword alignment and machine-readable resume signals.',
            details: [
                'Adds missing keywords recruiters and ATS tools look for',
                'Improves ATS readability with cleaner, clearer phrasing',
                'Optimizes skills and experience wording without changing your story',
            ],
            impact: 'Before: weaker keyword coverage. After: stronger ATS scanability and clearer role alignment.',
            why_this_matters: 'ATS and quick recruiter screens filter many resumes; stronger keyword alignment helps your resume pass initial automated and human filters.',
            real_world_impact: 'Better ATS fit increases the number of screened resumes that reach recruiters, improving the top-of-funnel for real interviews.',
            matcher: issue => /ats|keyword|skills|tool|technology/i.test(`${issue.problem} ${issue.improved}`),
        },
    ];

    const semanticPacks = packs
        .map(pack => ({
            ...pack,
            issues: openIssues.filter(pack.matcher).slice(0, 3),
        }))
        .map(pack => ({
            ...pack,
            preview: createPackPreview(pack.issues),
            estimated_gain: estimatePackGain(pack.issues),
        }))
        .filter(pack => pack.issues.length);

    const usedIds = new Set(semanticPacks.flatMap(pack => pack.issues.map(issue => issue.id)));
    const sectionPacks = (analysis?.sections || [])
        .map(section => {
            const issues = (section.issues || [])
                .filter(issue => !usedIds.has(issue.id))
                .filter(issue => openIds.has(issue.id))
                .slice(0, 3);
            return {
                id: `section-${String(section.section || 'resume').toLowerCase().replace(/\s+/g, '-')}`,
                title: `${section.section || 'Resume'} Pack`,
                description: `Clean up related issues in the ${section.section || 'resume'} section together.`,
                details: [
                    `Targets the ${section.section || 'resume'} section only`,
                    'Turns multiple related fixes into one focused sprint',
                    'Shows before vs after wording before you apply it',
                ],
                impact: `Before: scattered issues inside ${section.section || 'your resume'}. After: one tighter, more coherent section.`,
                issues,
                preview: createPackPreview(issues),
                estimated_gain: estimatePackGain(issues),
            };
        })
        .filter(pack => pack.issues.length >= 2);

    return [...semanticPacks, ...sectionPacks].slice(0, 4);
}

// ─── Login UI Enhancements ────────────────────────────────────────────────────
if (pwdToggle && loginPass) {
    pwdToggle.addEventListener('click', () => {
        const type = loginPass.getAttribute('type') === 'password' ? 'text' : 'password';
        loginPass.setAttribute('type', type);
        pwdToggle.innerHTML = type === 'password'
            ? '<i class="fa-regular fa-eye"></i>'
            : '<i class="fa-regular fa-eye-slash"></i>';
    });
}

if (loginInput) {
    loginInput.addEventListener('input', e => {
        const val = e.target.value.trim();
        if (val.length >= 3) {
            emailCheck?.classList.remove('hidden');
            usernameError?.classList.remove('show');
            loginInput.classList.remove('input-error');
        } else {
            emailCheck?.classList.add('hidden');
            if (val.length > 0) {
                if (usernameError) usernameError.innerText = 'Username must be at least 3 characters';
                usernameError?.classList.add('show');
                loginInput.classList.add('input-error');
            } else {
                usernameError?.classList.remove('show');
                loginInput.classList.remove('input-error');
            }
        }
    });
}

if (loginPass && pwdStrength && strengthFill && strengthText) {
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
}

// ─── Login Submission ──────────────────────────────────────────────────────────
loginForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const username = loginInput.value.trim();
    const password = loginPass.value;
    if (!username || !password) return showToast('Please enter both username and password.', 'error');

    const originalHTML = loginBtn.innerHTML;
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Authenticating...</span>';

    try {
        const data = await apiJSON('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        }, {
            retries: 1,
            retryDelay: 700,
        });

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
        const message = err.message === 'Failed to fetch' || err.message === 'Network request failed.'
            ? 'Could not reach the server. Refresh the page and try again.'
            : err.message;
        showToast(message, 'error');
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerHTML = originalHTML;
    }
});

// ─── File Upload ──────────────────────────────────────────────────────────────
fileInput?.addEventListener('change', e => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
        if (!isPdf) {
            selectedFile = null;
            uploadBtn.disabled = true;
            fileInfo.classList.add('hidden');
            showToast('Please select a PDF file.', 'error');
            return;
        }
        selectedFile = file;
        fileInfo.classList.remove('hidden');
        fileNameSpan.textContent = selectedFile.name;
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Ingest into Jobify Core';
    }
});

if (dropZone && fileInput) {
    dropZone.addEventListener('click', event => {
        if (event.target.closest('button, a, input')) return;
        fileInput.click();
    });
    dropZone.addEventListener('dragover', event => {
        event.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', event => {
        event.preventDefault();
        dropZone.classList.remove('dragover');
        const file = event.dataTransfer?.files?.[0];
        if (!file) return;
        const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
        if (!isPdf) {
            showToast('Please drop a PDF file.', 'error');
            return;
        }
        selectedFile = file;
        fileInfo?.classList.remove('hidden');
        if (fileNameSpan) fileNameSpan.textContent = file.name;
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Ingest into Jobify Core';
        }
    });
}

async function skipUploadAndGoToDashboard() {
    resumeLabState.has_resume = false;
    showLoading('Skipping upload, loading dashboard...');
    await loadDailyFeed();
}

const skipUploadBtn = document.getElementById('skip-upload-btn');
skipUploadBtn?.addEventListener('click', () => {
    skipUploadAndGoToDashboard();
});

uploadBtn?.addEventListener('click', async () => {
    if (!selectedFile || !authToken) return;

    showLoading('Saving resume securely...');
    try {
        await uploadResumeFile(selectedFile);
        await loadDailyFeed();
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

        setButtonLoading(replaceResumeBtn, true, 'Replacing...');
        setResumeStatus('Analyzing');
        showResumeFeedback('Uploading your new resume and rebuilding the workspace...', 'info');
        try {
            const data = await uploadResumeFile(dashboardSelectedResume);
            if (data.lab) {
                mergeResumeLabState(data.lab);
                resumeLabLoaded = true;
            }
            showToast('Resume replaced successfully.', 'success');
            showResumeFeedback('New resume loaded. Run analysis to generate fresh fixes.', 'success');
            switchPage('page-results');
            document.querySelector('[data-pane="pane-resume"]')?.click();
            renderResumeWorkbench();
            dashboardSelectedResume = null;
            if (dashboardResumeInput) dashboardResumeInput.value = '';
            dashboardResumeFileInfo?.classList.add('hidden');
            replaceResumeBtn.disabled = true;
        } catch (err) {
            showToast(err.message, 'error');
            switchPage('page-results');
            document.querySelector('[data-pane="pane-resume"]')?.click();
        } finally {
            setButtonLoading(replaceResumeBtn, false);
            if (!dashboardSelectedResume) replaceResumeBtn.disabled = true;
        }
    });
}

if (scoreResumeBtn) {
    scoreResumeBtn.addEventListener('click', async () => {
        if (!authToken) return;

        setButtonLoading(scoreResumeBtn, true, 'Analyzing...');
        setResumeStatus('Analyzing');
        renderResumeWorkbenchLoading('Analyzing your resume and building fix cards...');

        try {
            const data = await apiJSON('/api/resume/analyze', {
                method: 'POST',
                body: JSON.stringify({ target_role: resumeTargetRole?.value?.trim() || '' }),
            });
            mergeResumeLabState({
                has_resume: true,
                current_resume: data.current_resume,
                parsed_resume: data.parsed_resume,
                applied_fixes: data.applied_fixes,
                last_analysis: data,
            });
            recordResumeLabStreak();
            renderResumeWorkbench();
            showResumeFeedback('Analysis complete. Start with the priority fixes for the fastest lift.', 'success');
        } catch (err) {
            renderResumeWorkbenchError(err.message);
            setResumeStatus('Error');
            showResumeFeedback(err.message, 'error');
            showToast(err.message, 'error');
        } finally {
            setButtonLoading(scoreResumeBtn, false);
        }
    });
}

if (fixTopIssuesBtn) {
    fixTopIssuesBtn.addEventListener('click', async () => {
        if (!authToken || !resumeLabState?.has_resume) return;

        setButtonLoading(fixTopIssuesBtn, true, 'Applying...');
        setResumeStatus('Fixing');
        try {
            const data = await apiJSON('/api/resume/fixes/apply-top', {
                method: 'POST',
                body: JSON.stringify({ limit: 3, target_role: resumeTargetRole?.value?.trim() || '' }),
            });
            mergeResumeLabState(data);
            recordResumeLabStreak();
            recordDailyProgress(6, 'Applied top resume fixes');
            renderResumeWorkbench();
            showResumeFeedback(data.message || 'Top fixes applied.', 'success');
            showToast(data.message || 'Top fixes applied.', 'success');
        } catch (err) {
            setResumeStatus('Error');
            showResumeFeedback(err.message, 'error');
            showToast(err.message, 'error');
        } finally {
            setButtonLoading(fixTopIssuesBtn, false);
        }
    });
}

if (toggleFixModeBtn) {
    toggleFixModeBtn.addEventListener('click', () => toggleFixMode());
}

if (cancelFixModeBtn) {
    cancelFixModeBtn.addEventListener('click', () => toggleFixMode(false));
}

if (saveResumeTextBtn) {
    saveResumeTextBtn.addEventListener('click', async () => {
        if (!authToken) return;

        const currentResume = buildResumeTextFromEditor();
        if (!currentResume) {
            showResumeFeedback('Add at least one resume section before saving.', 'error');
            return;
        }

        setButtonLoading(saveResumeTextBtn, true, 'Saving...');
        try {
            const data = await apiJSON('/api/resume/text', {
                method: 'PUT',
                body: JSON.stringify({ current_resume: currentResume }),
            });
            mergeResumeLabState(data);
            recordResumeLabStreak();
            recordDailyProgress(3, 'Saved resume draft');
            renderResumeWorkbench();
            setResumeStatus('Saved');
            scheduleResumeRescore();
            showResumeFeedback('Draft saved. A fresh score refresh is queued automatically.', 'success');
            showToast('Resume draft saved.', 'success');
        } catch (err) {
            setResumeStatus('Error');
            showResumeFeedback(err.message, 'error');
            showToast(err.message, 'error');
        } finally {
            setButtonLoading(saveResumeTextBtn, false);
        }
    });
}

Object.values(getResumeEditorFieldMap()).forEach(field => {
    field?.addEventListener('input', () => {
        if (!resumeEditorPanel || resumeEditorPanel.classList.contains('hidden')) return;
        syncResumeDraftFromEditor();
    });
});

if (rescoreResumeBtn) {
    rescoreResumeBtn.addEventListener('click', () => {
        scheduleResumeRescore();
    });
}

if (resumeCompareToggle) {
    resumeCompareToggle.addEventListener('click', event => {
        const button = event.target.closest('[data-compare-view]');
        if (!button) return;
        resumeCompareView = button.dataset.compareView === 'before' ? 'before' : 'after';
        renderResumeWorkbench();
    });
}

// ─── Job Feed (deduplicated) ─────────────────────────────────────────────────
/*
 * Legacy/duplicate job-feed functions removed. The canonical `loadDailyFeed`
 * and `renderJobs` implementations are present later in this file and are
 * used by the application. Removing older duplicates prevents shadowing and
 * duplicate event bindings that caused layout and behavioral inconsistencies.
 */

// ─── Tracker ──────────────────────────────────────────────────────────────────
async function trackJob(company, title, url) {
    showLoading('Saving job and preparing tailored resume bullets...');
    try {
        const res = await fetch('/api/jobs/track', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ company_name: company, job_title: title, description_url: url }),
        });
        const data = await readResponseData(res);
        if (!res.ok) throw new Error(getErrorMessage(data, 'Could not save this job right now.'));

        switchPage('page-results');
        document.querySelector('[data-pane="pane-tracker"]').click();
        showToast('Job saved. Resume tailoring has started.', 'success');
        // Poll tracker every 5 seconds until status changes from "Tailoring..."
        await loadTracker();
        if (trackerPollTimer) clearInterval(trackerPollTimer);
        trackerPollTimer = setInterval(async () => {
            await loadTracker();
            const cards = trackerContainer.querySelectorAll('.status-badge');
            const stillTailoring = [...cards].some(c => c.textContent.includes('Tailoring'));
            if (!stillTailoring && trackerPollTimer) {
                clearInterval(trackerPollTimer);
                trackerPollTimer = null;
            }
        }, 5000);
    } catch (err) {
        showToast(err.message, 'error');
        switchPage('page-results');
    }
}

async function loadTracker() {
    try {
        const res = await fetch('/api/jobs/tracker', { headers: getAuthHeaders() });
        if (!res.ok) {
            if (res.status === 401) handleAuthExpired();
            return;
        }
        const apps = await readResponseData(res);
        const safeApps = Array.isArray(apps) ? apps : [];

        trackerContainer.innerHTML = '';
        if (safeApps.length === 0) {
            trackerContainer.innerHTML = '<p class="empty-state">No saved jobs yet. Use "Save Job & Tailor Resume" on any job card.</p>';
            return;
        }

        safeApps.forEach(app => {
            const card = document.createElement('div');
            card.className = 'crm-job-card tracker-card';

            let bulletsHTML = '';
            if (app.tailored_resume_bullets) {
                try {
                    const rawBullets = typeof app.tailored_resume_bullets === 'string'
                        ? JSON.parse(app.tailored_resume_bullets)
                        : app.tailored_resume_bullets;
                    const bullets = Array.isArray(rawBullets) ? rawBullets : [];
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
                        <div class="section-label"><i class="fa-solid fa-check-double"></i> Tailored Resume Bullets</div>
                        <div class="pre-tailored">${bulletsHTML}</div>
                    </div>` : (app.status === 'Tailoring...' ? '<p class="empty-state" style="margin-top:1rem"><i class="fa-solid fa-spinner fa-spin"></i> Tailoring your resume for this job...</p>' : '')}
            `;
            trackerContainer.appendChild(card);
        });
    } catch (err) {
        console.error('Tracker load error:', err);
    }
}

async function loadResumeLab(force = false) {
    if (!authToken) return;
    if (resumeLabLoaded && !force) {
        renderResumeWorkbench();
        return;
    }

    renderResumeWorkbenchLoading('Loading your stored resume workspace...');
    try {
        const data = await apiJSON('/api/resume/lab');
        const pendingRescoreTimer = resumeLabState.ui?.pendingRescoreTimer || null;
        const currentResume = repairResumeDisplayText(data.current_resume || '');
        const originalResume = repairResumeDisplayText(data.original_resume || currentResume || '');
        resumeLabState = {
            has_resume: !!data.has_resume || !!currentResume,
            original_resume: originalResume,
            current_resume: currentResume,
            parsed_resume: normalizeParsedResume(data.parsed_resume, currentResume || originalResume),
            last_analysis: data.last_analysis ? normalizeResumeAnalysis(data.last_analysis) : null,
            applied_fixes: normalizeAppliedFixes(data.applied_fixes),
            stats: data.stats || {},
            ui: { pendingRescoreTimer },
        };
        resumeLabLoaded = true;
        recordResumeLabStreak();
        renderResumeWorkbench();
    } catch (err) {
        renderResumeWorkbenchError(err.message);
    }
}

function normalizeResumeAnalysis(data) {
    return {
        score: clampScore(data?.score),
        breakdown: {
            impact: clampScore(data?.breakdown?.impact),
            clarity: clampScore(data?.breakdown?.clarity),
            structure: clampScore(data?.breakdown?.structure),
            ats: clampScore(data?.breakdown?.ats),
        },
        summary_feedback: {
            strengths: normalizeResumeTextList(data?.summary_feedback?.strengths),
            weaknesses: normalizeResumeTextList(data?.summary_feedback?.weaknesses),
            priority_fixes: normalizeResumeTextList(data?.summary_feedback?.priority_fixes),
        },
        section_scores: data?.section_scores || data?.sectionScores || {},
        sections: Array.isArray(data?.sections)
            ? data.sections.map((section, sectionIndex) => ({
                section: section?.section || `Section ${sectionIndex + 1}`,
                issues: Array.isArray(section?.issues)
                    ? section.issues.map((issue, issueIndex) => ({
                        ...issue,
                        id: issue?.id || `${section?.section || 'section'}-${issueIndex}`,
                        original: repairResumeDisplayText(issue?.original || ''),
                        problem: repairResumeDisplayText(issue?.problem || ''),
                        improved: repairResumeDisplayText(issue?.improved || ''),
                    }))
                    : [],
            }))
            : [],
    };
}

function mergeResumeLabState(data) {
    if ('has_resume' in data) resumeLabState.has_resume = !!data.has_resume;
    if ('original_resume' in data) resumeLabState.original_resume = repairResumeDisplayText(data.original_resume || '');
    if ('current_resume' in data) resumeLabState.current_resume = repairResumeDisplayText(data.current_resume || '');
    if ('parsed_resume' in data) {
        resumeLabState.parsed_resume = normalizeParsedResume(
            data.parsed_resume,
            data.current_resume || resumeLabState.current_resume || data.original_resume || resumeLabState.original_resume || '',
        );
    }
    if ('last_analysis' in data) {
        resumeLabState.last_analysis = data.last_analysis ? normalizeResumeAnalysis(data.last_analysis) : null;
    }
    if (data.analysis) resumeLabState.last_analysis = normalizeResumeAnalysis(data.analysis);
    if (Array.isArray(data.applied_fixes)) resumeLabState.applied_fixes = normalizeAppliedFixes(data.applied_fixes);
    if (data.stats) resumeLabState.stats = data.stats;
    if (!resumeLabState.original_resume) resumeLabState.original_resume = resumeLabState.current_resume || '';
    if (!resumeLabState.parsed_resume || !Object.keys(resumeLabState.parsed_resume).length) {
        resumeLabState.parsed_resume = normalizeParsedResume(
            resumeLabState.parsed_resume,
            resumeLabState.current_resume || resumeLabState.original_resume || '',
        );
    }
    resumeLabState.has_resume = resumeLabState.has_resume || !!resumeLabState.current_resume;
}

function renderResumeWorkbenchLoading(message) {
    if (!resumeScoreContainer) return;
    resumeScoreContainer.className = 'resume-score-empty';
    resumeScoreContainer.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${sanitize(message)}`;
    if (resumePriorityFixes) {
        resumePriorityFixes.innerHTML = '<p class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i> Preparing your highest-impact fixes...</p>';
    }
    if (resumeSectionHeatmap) {
        resumeSectionHeatmap.innerHTML = '<p class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i> Reading section strength...</p>';
    }
    if (resumeFixPacks) {
        resumeFixPacks.innerHTML = '<p class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i> Building fix packs...</p>';
    }
    if (resumeFixProgressBar) resumeFixProgressBar.style.width = '0%';
    if (resumeFixProgressText) resumeFixProgressText.textContent = 'Loading progress tracker...';
}

function renderResumeWorkbenchError(message) {
    if (!resumeScoreContainer) return;
    resumeScoreContainer.className = 'resume-score-empty';
    resumeScoreContainer.textContent = message || 'Resume Lab could not load.';
    if (resumePriorityFixes) {
        resumePriorityFixes.innerHTML = `<p class="empty-state">${sanitize(message || 'Resume Lab could not load.')}</p>`;
    }
    if (resumeSectionHeatmap) {
        resumeSectionHeatmap.innerHTML = `<p class="empty-state">${sanitize(message || 'Heatmap could not load.')}</p>`;
    }
    if (resumeFixPacks) {
        resumeFixPacks.innerHTML = `<p class="empty-state">${sanitize(message || 'Fix packs could not load.')}</p>`;
    }
}

function renderResumeWorkbench() {
    const hasResume = !!resumeLabState?.has_resume;
    const analysis = resumeLabState?.last_analysis ? normalizeResumeAnalysis(resumeLabState.last_analysis) : null;

    if (!hasResume) {
        renderScoreDashboard(null);
        renderBreakdownBars(null);
        renderConfidenceMeter(null);
        renderSectionHeatmap(null);
        renderNextAction(null);
        renderFixPacks(null);
        renderPriorityFixes(null);
        renderProgressTracker(null);
        if (resumeDraftPreview) {
            resumeDraftPreview.innerHTML = '<p class="empty-state">Upload a resume first to start the workbench.</p>';
        }
        if (resumeScoreContainer) {
            resumeScoreContainer.className = 'resume-score-empty';
            resumeScoreContainer.textContent = 'No stored resume found yet.';
        }
        if (resumeCompletionState) resumeCompletionState.classList.add('hidden');
        setResumeStatus('Idle');
        return;
    }

    renderScoreDashboard(analysis);
    renderBreakdownBars(analysis);
    renderConfidenceMeter(analysis);
    renderSectionHeatmap(analysis);
    renderNextAction(analysis);
    renderFixPacks(analysis);
    renderPriorityFixes(analysis);
    renderProgressTracker(analysis);
    renderResumePreview();
    renderIssueSections(analysis);

    setResumeEditorValues(false);
    if (resumeAppliedCount) resumeAppliedCount.textContent = String(resumeLabState.applied_fixes?.length || 0);
    if (resumeOpenIssues) resumeOpenIssues.textContent = String(countOpenIssues(analysis));
    if (resumeWordCount) resumeWordCount.textContent = String(countWords(resumeLabState.current_resume || ''));
    if (!resumeEditorPanel?.classList.contains('hidden')) {
        setResumeViewMode('Fix Mode');
    } else {
        setResumeViewMode(resumeCompareView === 'before' ? 'Original View' : 'Improved View');
    }
    setResumeStatus(analysis ? 'Ready' : 'Waiting');
}

function renderScoreDashboard(analysis) {
    const score = analysis ? getDisplayScore(analysis) : 0;
    if (resumeScoreRing) {
        resumeScoreRing.style.setProperty('--score-angle', `${score * 3.6}deg`);
    }
    if (resumeScoreValue) {
        resumeScoreValue.textContent = analysis ? String(score) : '--';
    }
    if (resumeScoreHeadline) {
        resumeScoreHeadline.textContent = !analysis
            ? 'Ready for analysis'
            : score >= 80
                ? 'Strong resume, with a few sharp fixes left'
                : score >= 60
                    ? 'Good base, but several lines need more punch'
                    : 'Needs focused improvement before wide applying';
    }
    if (resumeScoreCaption) {
        resumeScoreCaption.textContent = !analysis
            ? 'Run analysis to load your resume breakdown and issue cards.'
            : `${countOpenIssues(analysis)} open issues found across ${analysis.sections.length} sections.`;
    }
}

function renderBreakdownBars(breakdown) {
    const scores = breakdown ? getDisplayBreakdown(breakdown) : null;
    const metrics = ['impact', 'clarity', 'structure', 'ats'];
    metrics.forEach(metric => {
        const value = scores ? clampScore(scores[metric]) : 0;
        const scoreEl = document.getElementById(`score-${metric}`);
        const barEl = document.getElementById(`bar-${metric}`);
        if (scoreEl) scoreEl.textContent = scores ? String(value) : '--';
        if (barEl) barEl.style.width = `${value}%`;
    });
}

function renderConfidenceMeter(analysis) {
    const confidence = getConfidenceScore(analysis);
    if (resumeConfidenceBar) resumeConfidenceBar.style.width = `${confidence}%`;
    if (resumeConfidenceLabel) {
        resumeConfidenceLabel.textContent = analysis
            ? `${getConfidenceLabel(confidence)} (${confidence}%)`
            : 'Not ready yet';
    }
}

function renderSectionHeatmap(analysis) {
    if (!resumeSectionHeatmap) return;
    if (!analysis || !Array.isArray(analysis.sections) || !analysis.sections.length) {
        resumeSectionHeatmap.innerHTML = '<p class="empty-state">Analyze your resume to reveal section scores.</p>';
        return;
    }

    resumeSectionHeatmap.innerHTML = analysis.sections.map(section => {
        const name = section.section || 'section';
        const score = getSectionScore(name, analysis);
        const openCount = (section.issues || []).filter(issue => !getAppliedIssueIds().has(issue.id) && issue.status !== 'applied').length;
        const caption = openCount
            ? `${openCount} open issue${openCount === 1 ? '' : 's'}`
            : 'No open issues';
        return `
            <article class="heatmap-item ${getHeatClass(score)}">
                <strong>${sanitize(name)}</strong>
                <span>${caption}</span>
                <div class="heatmap-score">
                    <i class="fa-solid fa-circle"></i> ${score || '--'}${score ? '%' : ''}
                </div>
            </article>
        `;
    }).join('');
}

function renderNextAction(analysis) {
    if (!resumeNextActionText || !resumeNextActionBtn) return;
    const issue = getNextBestIssue(analysis);
    if (!issue) {
        resumeNextActionText.textContent = analysis
            ? 'No high-impact fixes remain in this analysis. Re-score to find the next layer of improvements.'
            : 'Run analysis and Jobify will guide the next improvement.';
        resumeNextActionBtn.disabled = !analysis;
        resumeNextActionBtn.dataset.issueId = '';
        resumeNextActionBtn.innerHTML = analysis
            ? '<i class="fa-solid fa-rotate"></i> Re-score Next'
            : '<i class="fa-solid fa-arrow-right"></i> Do Next Action';
        return;
    }

    const sectionName = findIssueSection(issue.id, analysis);
    resumeNextActionText.textContent = `Next, improve ${sectionName}: ${issue.problem || issue.original || 'apply the strongest remaining fix.'}`;
    resumeNextActionBtn.disabled = false;
    resumeNextActionBtn.dataset.issueId = issue.id;
    resumeNextActionBtn.innerHTML = '<i class="fa-solid fa-arrow-right"></i> Apply Recommended Fix';
}



function renderFixPacks(analysis) {
    if (!resumeFixPacks) return;
    const packs = buildFixPacks(analysis);
    if (!packs.length) {
        resumeFixPacks.innerHTML = analysis
            ? '<p class="empty-state">No related fix packs left. Re-score to uncover new groups.</p>'
            : '<p class="empty-state">Fix packs appear after analysis.</p>';
        return;
    }

    resumeFixPacks.innerHTML = packs.map(pack => `
        <article class="fix-pack-card" data-pack-id="${sanitize(pack.id)}">
            <div class="fix-pack-topline">
                <strong>${sanitize(pack.title)}</strong>
                <span class="fix-pack-gain">+${Number(pack.estimated_gain || 0)} lift</span>
            </div>
            <p>${sanitize(pack.description)}</p>
            <div class="fix-pack-impact">
                <span class="fix-pack-kicker">What changes</span>
                <p>${sanitize(pack.impact || 'This pack groups related edits into one meaningful improvement sprint.')}</p>
            </div>
            <div class="fix-pack-trust">
                <span class="fix-pack-kicker">Why this matters</span>
                <p>${sanitize(pack.why_this_matters || '')}</p>
                <span class="fix-pack-kicker">Real-world impact</span>
                <p>${sanitize(pack.real_world_impact || '')}</p>
            </div>
            ${Array.isArray(pack.details) && pack.details.length
                ? `
                    <div class="fix-pack-benefits">
                        <span class="fix-pack-kicker">What it does</span>
                        <ul>${pack.details.map(item => `<li>✔ ${sanitize(item)}</li>`).join('')}</ul>
                    </div>
                `
                : ''}
            ${Array.isArray(pack.preview) && pack.preview.length
                ? `
                    <div class="fix-pack-preview">
                        <span class="fix-pack-kicker">Before vs After Preview</span>
                        ${pack.preview.map(item => `
                            <div class="fix-pack-preview-row">
                                <div class="fix-pack-preview-pane before">
                                    <label>Before</label>
                                    <p>${sanitize(item.before || '')}</p>
                                </div>
                                <div class="fix-pack-preview-pane after">
                                    <label>After</label>
                                    <p>${sanitize(item.after || '')}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `
                : ''}
            <div class="fix-pack-meta">
                <span>${pack.issues.length} fix${pack.issues.length === 1 ? '' : 'es'}</span>
                <span>${sanitize(pack.issues.map(issue => findIssueSection(issue.id, analysis)).filter(Boolean)[0] || 'mixed')}</span>
            </div>
            <button class="btn-outline fix-pack-apply-btn" data-issue-ids="${sanitize(pack.issues.map(issue => issue.id).join(','))}">
                <i class="fa-solid fa-layer-group"></i> Apply Pack
            </button>
        </article>
    `).join('');
}

function renderPriorityFixes(analysis) {
    if (!resumePriorityFixes || !resumePriorityCount) return;
    if (!analysis) {
        resumePriorityFixes.innerHTML = '<p class="empty-state">Run an analysis to surface the highest-impact fixes.</p>';
        resumePriorityCount.textContent = '0 queued';
        resumePriorityCount.className = 'status-badge';
        if (resumePriorityGuidance) {
            resumePriorityGuidance.innerHTML = '<i class="fa-solid fa-bolt"></i><span>Next: Run analysis to reveal the highest-value fixes first.</span>';
        }
        return;
    }

    const appliedIds = getAppliedIssueIds();
    const optimisticIds = getOptimisticIssueIds();
    const topIssues = getAllResumeIssues(analysis)
        .filter(issue => !appliedIds.has(issue.id) && issue.status !== 'applied')
        .slice(0, 3);

    if (!topIssues.length) {
        resumePriorityFixes.innerHTML = '<p class="empty-state">Top issues are already handled. Re-score to uncover the next layer.</p>';
        resumePriorityCount.textContent = 'All clear';
        resumePriorityCount.className = 'status-badge ready';
        if (resumePriorityGuidance) {
            resumePriorityGuidance.innerHTML = `<i class="fa-solid fa-circle-check"></i><span>${sanitize(getPriorityGuidance(analysis))}</span>`;
        }
        return;
    }

    resumePriorityCount.textContent = `${topIssues.length} queued`;
    resumePriorityCount.className = 'status-badge info';
    if (resumePriorityGuidance) {
        resumePriorityGuidance.innerHTML = `<i class="fa-solid fa-bolt"></i><span>${sanitize(getPriorityGuidance(analysis))}</span>`;
    }
    resumePriorityFixes.innerHTML = topIssues.map(issue => {
        const problemText = repairResumeDisplayText(issue.problem || 'Needs improvement.');
        const originalText = repairResumeDisplayText(issue.original || '');
        const improvedText = repairResumeDisplayText(issue.improved || '');
        return `
        <article class="priority-fix-card ${optimisticIds.has(issue.id) ? 'optimistic' : ''}" data-priority-id="${sanitize(issue.id || '')}">
            <div class="priority-fix-copy">
                <strong>${sanitize(problemText)}</strong>
                <p>${sanitize(originalText)}</p>
                <p class="priority-improved">${sanitize(improvedText)}</p>
            </div>
            <div class="priority-fix-actions">
                <button class="btn-outline priority-edit-btn" data-issue-id="${sanitize(issue.id || '')}">
                    <i class="fa-solid fa-pen"></i> Edit
                </button>
                <button class="btn-modern-primary priority-apply-btn" data-issue-id="${sanitize(issue.id || '')}">
                    <i class="fa-solid fa-bolt"></i> Quick Apply
                </button>
            </div>
        </article>
    `;
    }).join('');
}

function renderProgressTracker(analysis) {
    const totalIssues = getAllResumeIssues(analysis).length;
    const appliedCount = getAppliedIssueIds().size;
    const progress = totalIssues ? Math.round((appliedCount / totalIssues) * 100) : 0;
    const displayScore = analysis ? getDisplayScore(analysis) : 0;
    const baseScore = analysis ? clampScore(analysis.score) : 0;
    const delta = analysis ? Math.max(0, displayScore - baseScore) : 0;

    if (resumeFixProgressBar) resumeFixProgressBar.style.width = `${progress}%`;
    if (resumeFixProgressText) {
        resumeFixProgressText.textContent = totalIssues
            ? `${appliedCount} of ${totalIssues} fixes applied. ${countOpenIssues(analysis)} still open. ${getProgressMilestone(progress)}`
            : `No issues tracked yet. ${getProgressMilestone(progress)}`;
    }
    if (resumeScoreDelta) {
        resumeScoreDelta.textContent = analysis ? `🚀 Resume Strength +${delta}` : 'Resume Strength +0';
        resumeScoreDelta.classList.remove('positive', 'negative', 'neutral');
        resumeScoreDelta.classList.add(delta > 0 ? 'positive' : delta < 0 ? 'negative' : 'neutral');
    }
    if (resumeCompletionState) {
        const ready = !!analysis && totalIssues > 0 && countOpenIssues(analysis) === 0;
        resumeCompletionState.classList.toggle('hidden', !ready);
    }
}

/* Duplicate `renderResumePreview` removed — canonical implementation exists later in file. */

function renderIssueSections(analysis) {
    if (!resumeScoreContainer) return;
    if (!analysis || !Array.isArray(analysis.sections) || analysis.sections.length === 0) {
        resumeScoreContainer.className = 'resume-score-empty';
        resumeScoreContainer.textContent = 'Run an analysis to load section-wise fixes.';
        return;
    }

    const content = analysis.sections.map(section => {
        const issues = Array.isArray(section.issues) ? section.issues : [];
        return `
            <details class="section-block" ${issues.length ? 'open' : ''}>
                <summary class="section-toggle">
                    <span>${sanitize(section.section || 'Section')}</span>
                    <span class="section-pill">${issues.length} issue${issues.length === 1 ? '' : 's'}</span>
                </summary>
                <div class="issue-stack">
                    ${issues.length ? issues.map(issue => renderIssueCard(issue)).join('') : '<p class="empty-issues">No issues found in this section.</p>'}
                </div>
            </details>
        `;
    }).join('');

    resumeScoreContainer.className = '';
    resumeScoreContainer.innerHTML = content;
}

function renderIssueCard(issue) {
    const applied = getAppliedIssueIds().has(issue.id) || issue.status === 'applied';
    const optimistic = getOptimisticIssueIds().has(issue.id);
    const problemText = repairResumeDisplayText(issue.problem || 'Needs improvement.');
    const originalText = repairResumeDisplayText(issue.original || '');
    const improvedText = repairResumeDisplayText(issue.improved || '');
    return `
        <article class="issue-card ${applied ? 'applied' : ''} ${optimistic ? 'optimistic' : ''}" data-issue-id="${sanitize(issue.id || '')}">
            <div class="issue-card-head">
                <strong>${sanitize(issue.action_type || 'replace')}</strong>
                <span>${optimistic ? 'Syncing...' : applied ? 'Applied' : 'Suggested Fix'}</span>
            </div>
            <div class="issue-card-body">
                <p class="issue-problem">${sanitize(problemText)}</p>
                <div class="issue-compare">
                    <div class="issue-pane original-pane">
                        <label>Original Text</label>
                        <p>${sanitize(originalText)}</p>
                    </div>
                    <div class="issue-pane improved-pane">
                        <label>Improved Version</label>
                        <p>${sanitize(improvedText)}</p>
                    </div>
                </div>
                <div class="issue-actions">
                    <button class="btn-outline edit-fix-btn" data-issue-id="${sanitize(issue.id || '')}">
                        <i class="fa-solid fa-pen"></i> Edit
                    </button>
                    <button class="btn-modern-primary apply-fix-btn" data-issue-id="${sanitize(issue.id || '')}" ${applied ? 'disabled' : ''}>
                        <i class="fa-solid fa-wand-magic-sparkles"></i> ${optimistic ? 'Syncing...' : applied ? 'Applied' : 'Apply Fix'}
                    </button>
                </div>
            </div>
        </article>
    `;
}

function countOpenIssues(analysis) {
    const appliedIds = getAppliedIssueIds();
    return getAllResumeIssues(analysis).filter(issue => !appliedIds.has(issue.id) && issue.status !== 'applied').length;
}

function countWords(text) {
    return String(text || '').trim().split(/\s+/).filter(Boolean).length;
}

function setResumeStatus(label) {
    if (!resumeStatusBadge) return;
    resumeStatusBadge.textContent = label;
    resumeStatusBadge.className = 'status-badge';
    if (label === 'Ready' || label === 'Saved') resumeStatusBadge.classList.add('ready');
    if (label === 'Analyzing' || label === 'Fixing' || label === 'Applying') resumeStatusBadge.classList.add('tailoring');
    if (label === 'Waiting' || label === 'Idle') resumeStatusBadge.classList.add('info');
    if (label === 'Error') resumeStatusBadge.classList.add('error');
}

function setResumeViewMode(label) {
    if (resumeViewModeTag) resumeViewModeTag.textContent = label;
    if (toggleFixModeBtn) {
        toggleFixModeBtn.innerHTML = label === 'Fix Mode'
            ? '<i class="fa-solid fa-eye"></i> Normal View'
            : '<i class="fa-solid fa-pen-to-square"></i> Fix Mode';
    }
}

function toggleFixMode(force) {
    if (!resumeEditorPanel) return;
    const shouldOpen = typeof force === 'boolean'
        ? force
        : resumeEditorPanel.classList.contains('hidden');

    resumeEditorPanel.classList.toggle('hidden', !shouldOpen);
    if (shouldOpen) setResumeEditorValues(true);
    if (!shouldOpen) {
        resumeSuggestionBanner?.classList.add('hidden');
    }
    setResumeViewMode(shouldOpen ? 'Fix Mode' : (resumeCompareView === 'before' ? 'Original View' : 'Improved View'));
}

function getIssueById(issueId) {
    const analysis = resumeLabState.last_analysis;
    if (!analysis || !Array.isArray(analysis.sections)) return null;
    for (const section of analysis.sections) {
        for (const issue of section.issues || []) {
            if (issue.id === issueId) return issue;
        }
    }
    return null;
}

function focusEditorOnIssue(issue) {
    if (!issue) return;
    toggleFixMode(true);
    setResumeEditorValues(true);
    resumeSuggestionText.textContent = `${issue.original} -> ${issue.improved}`;
    resumeSuggestionBanner?.classList.remove('hidden');

    const original = issue.original || '';
    const targetField = [resumeExperienceText, resumeProjectsText, resumeSummaryText, resumeSkillsText]
        .find(field => field && String(field.value || '').includes(original));
    if (targetField) {
        const index = targetField.value.indexOf(original);
        targetField.focus();
        if (index >= 0) targetField.setSelectionRange(index, index + original.length);
        return;
    }
    resumeSummaryText?.focus();
}

async function applyResumeIssue(issueId, button) {
    if (!issueId || !authToken) return;

    setButtonLoading(button, true, 'Applying...');
    setResumeStatus('Applying');
    const snapshot = markIssueAppliedLocally(issueId);
    if (snapshot) {
        renderResumeWorkbench();
        if (coachDashboardLoaded) renderCoachDashboard();
        showResumeFeedback('✨ Improvement applied!', 'success');
    }
    try {
        const data = await apiJSON('/api/resume/fixes/apply', {
            method: 'POST',
            body: JSON.stringify({
                issue_id: issueId,
                target_role: resumeTargetRole?.value?.trim() || '',
            }),
        });
        mergeResumeLabState(data);
        recordResumeLabStreak();
        recordDailyProgress(4, 'Applied one resume fix');
        renderResumeWorkbench();
        if (coachDashboardLoaded) renderCoachDashboard();
        const nextIssue = getNextBestIssue(resumeLabState.last_analysis);
        const message = nextIssue
            ? `✨ Improvement applied! Next: ${nextIssue.problem || nextIssue.original}`
            : '✨ Improvement applied! Your strongest surfaced fixes are done.';
        showResumeFeedback(message, data.success ? 'success' : 'error');
        showToast('✨ Improvement applied!', data.success ? 'success' : 'error');
    } catch (err) {
        if (snapshot) {
            resumeLabState = snapshot;
            renderResumeWorkbench();
            if (coachDashboardLoaded) renderCoachDashboard();
        }
        setResumeStatus('Error');
        showResumeFeedback(err.message, 'error');
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

async function applyResumeIssuePack(issueIds, button) {
    const ids = [...new Set(issueIds.filter(Boolean))];
    if (!ids.length || !authToken) return;

    setButtonLoading(button, true, 'Applying pack...');
    setResumeStatus('Fixing');
    let appliedCount = 0;

    try {
        for (const issueId of ids) {
            const data = await apiJSON('/api/resume/fixes/apply', {
                method: 'POST',
                body: JSON.stringify({
                    issue_id: issueId,
                    target_role: resumeTargetRole?.value?.trim() || '',
                }),
            });
            mergeResumeLabState(data);
            if (data.success) appliedCount += 1;
        }

        recordResumeLabStreak();
        recordDailyProgress(Math.max(3, appliedCount * 3), `Applied ${appliedCount} resume pack fix${appliedCount === 1 ? '' : 'es'}`);
        renderResumeWorkbench();
        const nextIssue = getNextBestIssue(resumeLabState.last_analysis);
        showResumeFeedback(
            nextIssue
                ? `Applied ${appliedCount} fixes from this pack. Next: ${nextIssue.problem || nextIssue.original}`
                : `Applied ${appliedCount} fixes from this pack. Re-score to discover the next set.`,
            'success'
        );
        showToast(`Applied ${appliedCount} pack fixes.`, 'success');
    } catch (err) {
        setResumeStatus('Error');
        showResumeFeedback(err.message, 'error');
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

function renderExportSummary() {
    if (!resumeExportSummary) return;
    const analysis = resumeLabState.last_analysis;
    const confidence = getConfidenceScore(analysis);
    const appliedCount = getAppliedIssueIds().size;
    const totalIssues = getAllResumeIssues(analysis).length;
    const score = analysis ? getDisplayScore(analysis) : 0;

    resumeExportSummary.classList.remove('hidden');
    resumeExportSummary.innerHTML = `
        <strong>Export Summary</strong>
        Downloaded your improved resume at ${score || '--'} score with ${confidence}% confidence.
        ${appliedCount} of ${totalIssues || 0} suggested fixes are applied, and your Resume Lab streak is ${resumeStreakState.count || 0} day${resumeStreakState.count === 1 ? '' : 's'}.
    `;
}

async function downloadImprovedResume(button) {
    if (!authToken || !resumeLabState?.has_resume) return;

    setButtonLoading(button, true, 'Downloading...');
    try {
        const res = await fetch('/api/resume/download', {
            headers: { 'Authorization': `Bearer ${authToken}` },
        });
        if (!res.ok) {
            const data = await readResponseData(res);
            throw new Error(getErrorMessage(data, 'Download failed.'));
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'jobify-improved-resume.txt';
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

        recordResumeLabStreak();
        renderExportSummary();
        showResumeFeedback('Download ready. Your improvement summary is shown below the export controls.', 'success');
    } catch (err) {
        showResumeFeedback(err.message, 'error');
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

async function loadCoachDashboard(force = false) {
    if (!authToken) return;
    if (coachDashboardLoaded && !force) {
        renderCoachDashboard();
        return;
    }

    if (coachDailyTasks) coachDailyTasks.innerHTML = '<p class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i> Loading your coach dashboard...</p>';
    try {
        recordResumeLabStreak();
        const [memoryRes, planRes, modesRes, resumeRes] = await Promise.allSettled([
            apiJSON('/api/interview/coach-memory'),
            apiJSON('/api/interview/daily-plan'),
            apiJSON('/api/interview/modes'),
            apiJSON('/api/resume/lab'),
        ]);

        coachState.memory = memoryRes.status === 'fulfilled' ? memoryRes.value.memory : null;
        coachState.plan = planRes.status === 'fulfilled' ? planRes.value.plan : null;
        coachState.modes = modesRes.status === 'fulfilled' ? modesRes.value : null;
        coachState.resumeLab = resumeRes.status === 'fulfilled' ? resumeRes.value : null;

        if (coachState.resumeLab?.has_resume) {
            mergeResumeLabState(coachState.resumeLab);
            resumeLabLoaded = true;
        }

        coachDashboardLoaded = true;
        renderCoachDashboard();
    } catch (err) {
        showToast(err.message || 'Coach dashboard unavailable.', 'error');
    }
}

function renderCoachDashboard() {
    renderResumeStreak();
    const dailySnapshot = getDailyProgressSnapshot();
    const memory = coachState.memory || {};
    const plan = coachState.plan || {};
    const resumeAnalysis = resumeLabState.last_analysis
        ? normalizeResumeAnalysis(resumeLabState.last_analysis)
        : (coachState.resumeLab?.last_analysis ? normalizeResumeAnalysis(coachState.resumeLab.last_analysis) : null);
    const confidence = resumeAnalysis ? getConfidenceScore(resumeAnalysis) : 0;
    const scoreTrend = Array.isArray(memory.score_trend) ? memory.score_trend : [];
    const latestScore = scoreTrend.length
        ? Number(scoreTrend[scoreTrend.length - 1]?.score || 0)
        : Number(memory.avg_answer_score || 0);
    const previousScore = scoreTrend.length > 1
        ? Number(scoreTrend[scoreTrend.length - 2]?.score || latestScore)
        : Number(coachState.ui?.lastAvgScore ?? latestScore);
    const scoreDelta = scoreTrend.length > 1 ? latestScore - previousScore : 0;
    const resumeScore = resumeAnalysis ? clampScore(resumeAnalysis.score) : 0;
    const previousResumeScore = Number.isFinite(Number(coachState.ui?.lastResumeScore))
        ? Number(coachState.ui.lastResumeScore)
        : resumeScore;
    const resumeScoreDelta = resumeAnalysis ? resumeScore - previousResumeScore : 0;
    const previousConfidence = Number.isFinite(Number(coachState.ui?.lastConfidence))
        ? Number(coachState.ui.lastConfidence)
        : confidence;
    const confidenceDelta = resumeAnalysis ? confidence - previousConfidence : 0;
    const nextIssue = getNextBestIssue(resumeAnalysis);
    const firstTask = Array.isArray(plan?.tasks) ? plan.tasks[0] : null;
    let nextActionType = 'interview';
    let nextActionLabel = 'Start Interview';
    let nextActionCopy = firstTask?.title
        ? `${firstTask.title}. ${firstTask.why || 'Keep moving with one small task right now.'}`
        : 'Start an interview to turn today\'s feedback into practice.';

    if (nextIssue) {
        nextActionType = 'resume_fix';
        nextActionLabel = 'Fix Resume';
        nextActionCopy = `Quick win: ${findIssueSection(nextIssue.id, resumeAnalysis)} - ${nextIssue.problem || nextIssue.original}`;
    } else if (resumeAnalysis && countOpenIssues(resumeAnalysis) === 0 && resumeAnalysis.score >= 80) {
        nextActionType = 'interview';
        nextActionLabel = 'Practice Interview';
        nextActionCopy = 'Your draft looks strong. Practice with an interview while the improvements are still fresh.';
    }

    if (coachStreakCount) coachStreakCount.textContent = String(resumeStreakState.count || 0);
    if (coachStreakCopy) coachStreakCopy.textContent = resumeStreakState.count > 1
        ? 'You are building a steady prep habit.'
        : 'Come back daily to keep the streak alive.';
    if (coachResumeScore) coachResumeScore.textContent = resumeAnalysis ? String(resumeScore) : '--';
    if (coachResumeScoreCopy) coachResumeScoreCopy.textContent = resumeAnalysis
        ? 'Latest score from Resume Lab.'
        : 'Run Resume Lab to calculate your score.';
    setDeltaBadge(coachResumeScoreDelta, resumeAnalysis ? resumeScoreDelta : 0, '');
    if (coachConfidenceScore) coachConfidenceScore.textContent = resumeAnalysis ? `${confidence}%` : '--';
    if (coachConfidenceCopy) coachConfidenceCopy.textContent = resumeAnalysis
        ? getConfidenceLabel(confidence)
        : 'Analyze your resume to unlock readiness scoring.';
    setDeltaBadge(coachConfidenceDelta, resumeAnalysis ? confidenceDelta : 0, '%');
    if (coachSessionCount) coachSessionCount.textContent = String(memory.session_count || 0);
    if (coachDailyGain) coachDailyGain.textContent = `+${Math.round(dailySnapshot.points || 0)} today`;
    if (coachReadyState) {
        coachReadyState.textContent = resumeAnalysis && confidence >= 85
            ? 'Your resume looks ready. Next, practice your strongest stories in an interview round.'
            : latestScore >= 8
                ? 'Your interview answers are improving. Push into deeper follow-up questions today.'
                : dailySnapshot.lastEvent
                    ? `Latest progress: ${dailySnapshot.lastEvent}. Keep going with one more focused step.`
                    : 'Your coach will turn today\'s resume and interview signals into a simple next step.';
    }
    // Guided UI: keep dashboard focused (no secondary next-action CTA duplication).
    if (coachNextActionCopy) coachNextActionCopy.textContent = '';
    if (coachNextActionBtn) {
        coachNextActionBtn.dataset.action = '';
        coachNextActionBtn.dataset.issueId = '';
    }

    renderCoachControls(coachState.modes);
    renderCoachDailyPlan(plan);
    renderCoachWeakAreas(memory.recurring_weak_areas || []);
    renderCoachTrends(scoreTrend, confidence);
    renderCoachFeedback(coachState.latestFeedback);
    renderResumeHealthPanel(resumeAnalysis);
    patchCoachState({
        ui: {
            lastAvgScore: Number.isFinite(latestScore) ? latestScore : coachState.ui?.lastAvgScore,
            lastConfidence: resumeAnalysis ? confidence : coachState.ui?.lastConfidence,
            lastResumeScore: resumeAnalysis ? resumeScore : coachState.ui?.lastResumeScore,
        },
    });
}

function renderCoachControls(modesData) {
    if (modesData?.training_modes && coachTrainingMode) {
        const current = coachTrainingMode.value || 'adaptive';
        coachTrainingMode.innerHTML = Object.entries(modesData.training_modes).map(([value, label]) => (
            `<option value="${sanitize(value)}">${sanitize(value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()))}</option>`
        )).join('');
        coachTrainingMode.value = modesData.training_modes[current] ? current : 'adaptive';
    }
    if (modesData?.personas && coachPersona) {
        const current = coachPersona.value || 'balanced';
        coachPersona.innerHTML = Object.entries(modesData.personas).map(([value, profile]) => (
            `<option value="${sanitize(value)}">${sanitize(profile.label || value)}</option>`
        )).join('');
        coachPersona.value = modesData.personas[current] ? current : 'balanced';
    }
}

function renderCoachDailyPlan(plan) {
    if (coachPlanHeadline) coachPlanHeadline.textContent = plan?.headline || 'Your plan will appear here.';
    if (coachPlanNote) coachPlanNote.textContent = plan?.coach_note || 'Start with one resume fix or one interview answer today.';
    if (!coachDailyTasks) return;
    const tasks = Array.isArray(plan?.tasks) ? plan.tasks : [];
    if (!tasks.length) {
        coachDailyTasks.innerHTML = '<p class="empty-state">No plan yet. Analyze your resume or start an interview to generate one.</p>';
        return;
    }
    coachDailyTasks.innerHTML = tasks.map((task, index) => `
        <article class="coach-task-card">
            <div class="coach-task-index">${index + 1}</div>
            <div>
                <strong>${sanitize(task.title || 'Coach task')}</strong>
                <p>${sanitize(task.why || 'This task helps your interview readiness compound.')}</p>
            </div>
            <span class="coach-task-time">${Number(task.duration_minutes || 10)}m</span>
        </article>
    `).join('');
}

function renderCoachWeakAreas(areas) {
    if (!coachWeakAreas) return;
    if (!Array.isArray(areas) || !areas.length) {
        coachWeakAreas.innerHTML = '<p class="empty-state">No weak areas saved yet. Start a resume-based interview to build this list.</p>';
        if (coachWeakDrill) {
            coachWeakDrill.innerHTML = `
                <strong>Next drill</strong>
                <p>Answer one interview question and the next drill will appear here.</p>
            `;
        }
        return;
    }
    coachWeakAreas.innerHTML = areas.slice(0, 8).map(item => `
        <span class="coach-chip">
            ${sanitize(item.area || String(item))}
            ${item.count ? `<small>x${Number(item.count)}</small>` : ''}
        </span>
    `).join('');

    const nextArea = sanitize(areas[0]?.area || String(areas[0] || 'communication clarity'));
    if (coachWeakDrill) {
        coachWeakDrill.innerHTML = `
            <strong>Next drill</strong>
            <p>Practice <span>${nextArea}</span> with one focused round. It is the fastest way to improve a repeated weak spot.</p>
            <button class="btn-outline coach-drill-btn" data-area="${nextArea}">
                <i class="fa-solid fa-bullseye"></i> Start Weak-Area Drill
            </button>
        `;
    }
}

function renderCoachTrends(scoreTrend, currentConfidence) {
    const trend = Array.isArray(scoreTrend) ? scoreTrend.slice(-10) : [];
    if (coachScoreTrend) {
        coachScoreTrend.innerHTML = trend.length
            ? trend.map(item => {
                const score = Math.max(1, Math.min(10, Number(item.score) || 1));
                return `<div class="coach-trend-bar" style="height:${score * 10}%"><span>${score}</span></div>`;
            }).join('')
            : '<p class="empty-state">Interview score history appears after answers.</p>';
    }
    if (coachConfidenceTrend) {
        const latest = trend.slice(-3);
        const rows = latest.length ? latest : [{ focus_area: 'Resume confidence', score: Math.round(currentConfidence / 10) }];
        coachConfidenceTrend.innerHTML = rows.map((item, index) => {
            const value = item.confidence ? Number(item.confidence) : Math.max(0, Math.min(100, Number(item.score || 0) * 10));
            return `
                <div class="coach-confidence-row">
                    <span>${sanitize(item.focus_area || `Signal ${index + 1}`)}</span>
                    <div class="coach-confidence-track"><div style="width:${value}%"></div></div>
                    <strong>${Math.round(value)}%</strong>
                </div>
            `;
        }).join('');
    }
}

function renderCoachFeedback(feedbackData) {
    if (!coachFeedbackSummary) return;
    if (!feedbackData) {
        coachFeedbackSummary.innerHTML = '<p class="empty-state">Answer one interview question to see your latest feedback here.</p>';
        return;
    }
    const evaluation = feedbackData.feedback || feedbackData.evaluation || {};
    const score = evaluation.score ?? feedbackData.evaluation?.score ?? feedbackData.score ?? '--';
    const why = evaluation.how_to_improve || evaluation.improvement || feedbackData.feedback || 'Keep adding specific examples, tradeoffs, and measurable outcomes.';
    const strengths = Array.isArray(evaluation.what_went_well) ? evaluation.what_went_well.slice(0, 2) : (Array.isArray(evaluation.strengths) ? evaluation.strengths.slice(0,2) : []);
    const weaknesses = Array.isArray(evaluation.what_was_missing) ? evaluation.what_was_missing.slice(0, 2) : (Array.isArray(evaluation.weaknesses) ? evaluation.weaknesses.slice(0,2) : []);
    const missing = Array.isArray(evaluation.missing_concepts) ? evaluation.missing_concepts : [];
    const verdict = feedbackData.final_verdict || feedbackData.verdict || null;
    const verdictNote = verdict ? `<div class="coach-final-verdict"><strong>${sanitize(String(verdict))}</strong><p>${sanitize(feedbackData.verdict_explanation || '')}</p></div>` : '';

    coachFeedbackSummary.innerHTML = `
        ${verdictNote}
        <div class="coach-feedback-score"><i class="fa-solid fa-star"></i> ${sanitize(String(score))}/10</div>
        <p><strong>Why:</strong> ${sanitize(why)}</p>
        ${feedbackData.focus_area ? `<p><strong>Focus:</strong> ${sanitize(feedbackData.focus_area)}</p>` : ''}
        ${strengths.length ? `<p><strong>What landed:</strong> ${sanitize(strengths.join('; '))}</p>` : ''}
        ${weaknesses.length ? `<p><strong>What felt weak:</strong> ${sanitize(weaknesses.join('; '))}</p>` : ''}
        ${missing.length ? `<ul>${missing.map(item => `<li>${sanitize(item)}</li>`).join('')}</ul>` : ''}
    `;
}



if (resumeScoreContainer) {
    resumeScoreContainer.addEventListener('click', async e => {
        const applyBtn = e.target.closest('.apply-fix-btn');
        const editBtn = e.target.closest('.edit-fix-btn');

        if (editBtn) {
            const issue = getIssueById(editBtn.dataset.issueId);
            focusEditorOnIssue(issue);
            return;
        }

        if (!applyBtn) return;
        await applyResumeIssue(applyBtn.dataset.issueId, applyBtn);
    });
}

if (resumePriorityFixes) {
    resumePriorityFixes.addEventListener('click', async e => {
        const applyBtn = e.target.closest('.priority-apply-btn');
        const editBtn = e.target.closest('.priority-edit-btn');

        if (editBtn) {
            focusEditorOnIssue(getIssueById(editBtn.dataset.issueId));
            return;
        }

        if (!applyBtn) return;
        await applyResumeIssue(applyBtn.dataset.issueId, applyBtn);
    });
}

// ─── Interview Studio (VOXA-style Chatbot) ───────────────────────────────────
if (resumeNextActionBtn) {
    resumeNextActionBtn.addEventListener('click', async () => {
        const issueId = resumeNextActionBtn.dataset.issueId;
        if (issueId) {
            await applyResumeIssue(issueId, resumeNextActionBtn);
            return;
        }
        if (rescoreResumeBtn && !resumeNextActionBtn.disabled) {
            rescoreResumeBtn.click();
        }
    });
}

if (resumeFixPacks) {
    resumeFixPacks.addEventListener('click', async e => {
        const packBtn = e.target.closest('.fix-pack-apply-btn');
        if (!packBtn) return;
        await applyResumeIssuePack((packBtn.dataset.issueIds || '').split(','), packBtn);
    });
}

if (downloadResumeBtn) {
    downloadResumeBtn.addEventListener('click', () => downloadImprovedResume(downloadResumeBtn));
}

if (resumeStartInterviewBtn) {
    resumeStartInterviewBtn.addEventListener('click', () => {
        startCoachInterview({
            role: resumeTargetRole?.value?.trim() || coachTargetRole?.value?.trim() || 'Software Engineer',
        });
    });
}

if (coachStartInterviewBtn) {
    coachStartInterviewBtn.addEventListener('click', startCoachInterview);
}

if (coachFixResumeBtn) {
    coachFixResumeBtn.addEventListener('click', () => {
        document.querySelector('[data-pane="pane-resume"]')?.click();
        loadResumeLab(false);
    });
}

if (coachRefreshPlanBtn) {
    coachRefreshPlanBtn.addEventListener('click', async () => {
        setButtonLoading(coachRefreshPlanBtn, true, 'Refreshing...');
        try {
            await loadCoachDashboard(true);
            showToast('Coach plan refreshed.', 'success');
        } finally {
            setButtonLoading(coachRefreshPlanBtn, false);
        }
    });
}

if (coachWeakDrill) {
    coachWeakDrill.addEventListener('click', e => {
        const button = e.target.closest('.coach-drill-btn');
        if (!button) return;
        const area = button.dataset.area || '';
        if (coachTrainingMode) coachTrainingMode.value = 'weak_area_only';
        if (coachDomainFocus) coachDomainFocus.value = area;
        startCoachInterview({
            training_mode: 'weak_area_only',
            domain_focus: area,
        });
    });
}

if (coachNextActionBtn) {
    coachNextActionBtn.addEventListener('click', async () => {
        const action = coachNextActionBtn.dataset.action || 'interview';
        const issueId = coachNextActionBtn.dataset.issueId || '';
        if (action === 'resume_fix' && issueId) {
            document.querySelector('[data-pane="pane-resume"]')?.click();
            await loadResumeLab(false);
            await applyResumeIssue(issueId, coachNextActionBtn);
            return;
        }
        startCoachInterview();
    });
}

const startBtn        = document.getElementById('start-interview-btn');
const newInterviewBtn = document.getElementById('new-interview-btn');
const activeDiv       = document.getElementById('studio-active');
const chatMessages    = document.getElementById('interview-chat');
const submitAnswerBtn = document.getElementById('submit-answer-btn');
const answerInput     = document.getElementById('interview-answer-input');
const emptyState      = document.getElementById('chat-empty-state');
const diffSlider      = document.getElementById('interview-diff');
const diffLabel       = document.getElementById('diff-label');
const interviewPersonaSelect = document.getElementById('interview-persona');
const sessionsList    = document.getElementById('sessions-list');
const chatPersonaBadge = document.getElementById('chat-persona-badge');
const chatPressureBadge = document.getElementById('chat-pressure-badge');
const chatFocusBadge = document.getElementById('chat-focus-badge');
const chatTurnCounter = document.getElementById('chat-turn-counter');
const chatLiveNote = document.getElementById('chat-live-note');
const chatAnswerHint = document.getElementById('chat-answer-hint');
const chatFullscreenBtn = document.getElementById('chat-fullscreen-btn');
const voicePlayBtn = document.getElementById('voice-play-btn');
const voicePauseBtn = document.getElementById('voice-pause-btn');
const voiceRepeatBtn = document.getElementById('voice-repeat-btn');
let scores = [];
let activeSidebarItem = null;
let latestInterviewerTurnText = '';
let interviewUtterance = null;

function stopInterviewSpeech() {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    interviewUtterance = null;
}

function speakInterviewText(text, { forceRestart = false } = {}) {
    if (!('speechSynthesis' in window)) return;
    const content = String(text || '').trim();
    if (!content) return;

    if (forceRestart) stopInterviewSpeech();
    if (window.speechSynthesis.speaking && !forceRestart) return;

    const utterance = new SpeechSynthesisUtterance(content);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    interviewUtterance = utterance;
    window.speechSynthesis.speak(utterance);
}

// Diff slider live label
if (diffSlider) {
    diffSlider.addEventListener('input', () => {
        diffLabel.textContent = diffSlider.value;
        const pct = ((diffSlider.value - 1) / 9) * 100;
        diffSlider.style.background = `linear-gradient(to right, var(--primary) ${pct}%, rgba(255,255,255,0.1) ${pct}%)`;
    });
}

if (voicePlayBtn) {
    voicePlayBtn.addEventListener('click', () => {
        const text = latestInterviewerTurnText || 'No active interviewer question yet.';
        speakInterviewText(text, { forceRestart: true });
    });
}

if (voicePauseBtn) {
    voicePauseBtn.addEventListener('click', () => {
        if (!('speechSynthesis' in window)) return;
        if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
            window.speechSynthesis.pause();
            return;
        }
        if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
        }
    });
}

if (voiceRepeatBtn) {
    voiceRepeatBtn.addEventListener('click', () => {
        if (!latestInterviewerTurnText) return;
        speakInterviewText(latestInterviewerTurnText, { forceRestart: true });
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
    const interviewer_persona = interviewPersonaSelect?.value || 'strict';

    setStartBtnLoading(true);
    try {
        requestInterviewFullscreen();
        const data = await apiJSON('/api/interview/start', {
            method: 'POST',
            body: JSON.stringify({ role, difficulty: diff, weak_areas: [], interviewer_persona }),
        });

        interviewSessionId = data.session_id;
        scores = [];

        openChatView(data.role || role, data.difficulty || diff, data);
        if (data.session_intro) {
            appendMsg('ai', data.session_intro, null, false, data);
            await wait(180);
        }
        appendMsg('ai', formatInterviewerTurn(data), null, false, data);
        recordDailyProgress(3, 'Started manual interview session');
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
    if (interviewPersonaSelect) interviewPersonaSelect.value = 'strict';
    updateInterviewStageMeta({ interviewer_persona: 'strict', pressure_level: 'medium', focus_area: 'opening', session_turn: 0 });
    stopInterviewSpeech();
});

// ── Submit answer ────────────────────────────────────────────
submitAnswerBtn.addEventListener('click', async () => {
    const ans = answerInput.value.trim();
    if (!ans || !interviewSessionId) return;

    appendMsg('user', ans);
    answerInput.value = '';
    answerInput.style.height = 'auto';
    submitAnswerBtn.disabled = true;
    let interviewEnded = false;

    const typingId = appendTyping();

    try {
        const data = await apiJSON('/api/interview/answer', {
            method: 'POST',
            body: JSON.stringify({ session_id: interviewSessionId, answer: ans }),
        });

        // Replace typing indicator with animated feedback and typed follow-up
        removeTyping(typingId);

        const score = data.feedback?.score ?? data.evaluation?.score ?? data.score ?? null;
        const feedbackText = formatInterviewFeedbackMessage(data);

        // Animated feedback bubble
        const fbWrap = appendMsg('feedback', '', score, false, { focus_area: data.focus_area });
        const fbBubble = fbWrap.querySelector('.msg-bubble');
        await typeOutMessage(fbBubble, feedbackText, { pressure: data.pressure_level || data.persona?.pressure });

        // Update coach state and UI
        coachState.latestFeedback = data;
        renderCoachFeedback(data);
        loadCoachDashboard(true);
        updateInterviewStageMeta(data);
        recordDailyProgress(Math.max(2, Number(score) || 0), `Completed interview turn ${Number(data.session_turn || scores.length + 1)}`);

        // Animated next question (with possible interruption)
        if (data.next_question) {
            await wait(220 + Math.random() * 240);
            const aiWrap = appendMsg('ai', '', null, false, data);
            const aiBubble = aiWrap.querySelector('.msg-bubble');
            const interviewerTurnText = formatInterviewerTurn(data);
            await typeOutMessage(aiBubble, interviewerTurnText, {
                pressure: data.pressure_level || data.persona?.pressure,
                interruption_text: data.interviewer_signal || 'Be specific about the decision you made.',
                meta: data,
            });
            latestInterviewerTurnText = interviewerTurnText;
            speakInterviewText(interviewerTurnText, { forceRestart: true });
        }

        if (score !== null) {
            scores.push(Number(score));
            const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
            document.getElementById('chat-score-display').textContent = `Avg Score: ${avg.toFixed(1)}/10`;
        }

        if (data.interview_complete && data.final_feedback) {
            const ff = data.final_feedback;
            const summary = [
                `Final Evaluation (${ff.verdict || data.final_verdict || 'Complete'})`,
                `Overall score: ${ff.overall_score ?? data.avg_score ?? '--'}/10`,
                `Strengths: ${(ff.strengths || []).join('; ') || '—'}`,
                `Weaknesses: ${(ff.weaknesses || []).join('; ') || '—'}`,
                `Improvement plan: ${(ff.improvement_plan || []).join('; ') || '—'}`,
            ].join('\n');
            appendMsg('feedback', summary, Math.round(Number(ff.overall_score ?? data.avg_score ?? 0)), false, { focus_area: 'final evaluation' });
            answerInput.value = '';
            answerInput.disabled = true;
            submitAnswerBtn.disabled = true;
            answerInput.placeholder = 'Interview completed. Start a new session for another round.';
            interviewEnded = true;
        }
    } catch (err) {
        removeTyping(typingId);
        showToast(err.message, 'error');
    } finally {
        if (!interviewEnded) {
            submitAnswerBtn.disabled = false;
            answerInput.focus();
        }
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
/* Duplicate `loadSessionHistory` removed — canonical implementation exists later in file. */

// ── UI helpers ───────────────────────────────────────────────
function openChatView(role, diff) {
    emptyState.classList.add('hidden');
    activeDiv.classList.remove('hidden');
    chatMessages.innerHTML = '';
    document.getElementById('chat-role-label').textContent = role;
    document.getElementById('chat-diff-badge').textContent = `Difficulty ${diff}/10`;
    document.getElementById('chat-score-display').textContent = '';
}

// Typing helpers: modern animated typing and safe removal
function appendTyping(meta = {}) {
    const id = 'typing-' + Date.now();
    const wrap = document.createElement('div');
    wrap.className = 'msg ai typing-placeholder';
    wrap.id = id;
    wrap.innerHTML = `
        <span class="msg-sender"><i class="fa-solid fa-user-tie"></i> Interviewer</span>
        <div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTyping(id) { const el = document.getElementById(id); if (el) el.remove(); }

// Type out message with optional interruption and pressure-aware pacing
async function typeOutMessage(bubbleEl, text, options = {}) {
    if (!bubbleEl) return;
    const pressure = String((options.pressure_level || options.pressure || 'medium')).toLowerCase();
    const baseDelay = pressure === 'high' ? 8 : pressure === 'low' ? 26 : 14;
    const charDelay = Math.max(6, Math.min(40, baseDelay));
    const shouldInterrupt = pressure === 'high' && String(text || '').length > 80 && Math.random() < 0.35;

    function findSplitIndex(t, minIdx, maxIdx) {
        const slice = t.slice(minIdx, Math.min(maxIdx, t.length));
        const m = slice.match(/[\.!?]/);
        if (m) return minIdx + slice.indexOf(m[0]) + 1;
        return Math.min(maxIdx, t.length - 1);
    }

    bubbleEl.innerText = '';

    if (shouldInterrupt) {
        const split = findSplitIndex(text, 40, Math.min(120, Math.floor(text.length * 0.6)));
        for (let i = 1; i <= split; i++) { bubbleEl.innerText = text.slice(0, i); await wait(charDelay); }
        // small pause then show interruption
        await wait(220);
        appendMsg('ai', options.interruption_text || 'Hold on — be specific about the exact decision you made.', null);
        await wait(420);
        const secondWrap = appendMsg('ai', '', null, false, options.meta || {});
        const secondBubble = secondWrap.querySelector('.msg-bubble');
        for (let i = split + 1; i <= text.length; i++) { secondBubble.innerText = text.slice(split, i); await wait(charDelay); }
        secondBubble.innerText = text.slice(split);
        return;
    }

    for (let i = 1; i <= (text || '').length; i++) {
        bubbleEl.innerText = text.slice(0, i);
        await wait(charDelay);
    }
    bubbleEl.innerText = text;
}



function setStartBtnLoading(loading) {
    startBtn.disabled = loading;
    startBtn.innerHTML = loading
        ? '<i class="fa-solid fa-spinner fa-spin"></i> Starting...'
        : '<i class="fa-solid fa-play"></i> Start Interview';
}

function requestInterviewFullscreen() {
    const pane = document.getElementById('pane-interview');
    document.body.classList.add('interview-live');
    if (!pane || document.fullscreenElement) return;
    const request = pane.requestFullscreen || pane.webkitRequestFullscreen || pane.msRequestFullscreen;
    if (typeof request === 'function') {
        Promise.resolve(request.call(pane)).catch(() => {});
    }
}

function formatInterviewerTurn(data = {}) {
    const question = String(data.next_question || data.question || 'Walk me through your reasoning.').trim();
    return question;
}

function formatInterviewFeedbackMessage(data = {}) {
    if (data.feedback_message) return String(data.feedback_message).trim();

    // Prefer structured feedback if available
    if (data.feedback && typeof data.feedback === 'object') {
        const f = data.feedback;
        const score = f.score ?? data.evaluation?.score ?? data.score ?? '--';
        const well = Array.isArray(f.what_went_well) ? f.what_went_well.filter(Boolean) : [];
        const missing = Array.isArray(f.missing_concepts) ? f.missing_concepts.filter(Boolean) : [];
        const missingNote = missing.length ? `Missing depth: ${missing.slice(0, 2).join(', ')}` : '';
        const improvement = f.how_to_improve || f.improvement || 'Use one concrete example, your decision, and the outcome.';
        const lines = [
            `Score: ${score}/10`,
            `What went well: ${well[0] || 'You attempted the question directly.'}`,
            `What was missing: ${Array.isArray(f.what_was_missing) && f.what_was_missing[0] ? f.what_was_missing[0] : 'More specifics needed.'}`,
            missingNote,
            `Next focus: ${f.next_focus || data.focus_area || 'specific evidence'}`,
            `How to improve: ${improvement}`,
        ].filter(Boolean);
        return lines.join('\n');
    }

    const evaluation = data.evaluation || {};
    const score = evaluation.score ?? data.score ?? '--';
    const strengths = Array.isArray(evaluation.strengths) ? evaluation.strengths.filter(Boolean) : [];
    const weaknesses = Array.isArray(evaluation.weaknesses) ? evaluation.weaknesses.filter(Boolean) : [];
    const missing = Array.isArray(evaluation.missing_concepts) ? evaluation.missing_concepts.filter(Boolean) : [];
    const improvement = evaluation.improvement || evaluation.improvements || 'Use one concrete example, your decision, and the outcome.';
    const lines = [
        `Score: ${score}/10`,
        `What landed: ${strengths[0] || 'You attempted the question directly.'}`,
        `What felt weak: ${weaknesses[0] || 'The answer still needs clearer specifics.'}`,
        missing.length ? `Missing depth: ${missing.slice(0, 2).join(', ')}` : '',
        `Next target: ${data.focus_area || evaluation.next_answer_focus || 'specific evidence'}`,
        `Upgrade your next answer: ${improvement}`,
    ].filter(Boolean);
    return lines.join('\n');
}

function updateInterviewStageMeta(meta = {}) {
    const personaKey = String(meta.interviewer_persona || meta.persona_key || interviewPersonaSelect?.value || 'balanced')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
    const pressure = String(meta.pressure_level || meta.persona?.pressure || 'medium');
    const focus = String(meta.focus_area || 'opening').trim();
    const phase = String(meta.phase || '').trim();
    const turnCount = Number(meta.session_turn || scores.length || 0);
    const expectation = String(
        meta.answer_expectation || 'Answer in 5-10 lines with context, decisions, tradeoffs, and measurable outcome.'
    ).trim();

    if (chatPersonaBadge) chatPersonaBadge.textContent = personaKey;
    if (chatPressureBadge) chatPressureBadge.textContent = `Pressure: ${pressure}`;
    if (chatFocusBadge) chatFocusBadge.textContent = phase ? `Phase: ${phase} · Focus: ${focus}` : `Focus: ${focus}`;
    if (chatTurnCounter) chatTurnCounter.textContent = `Turn ${turnCount}`;
    if (chatAnswerHint) chatAnswerHint.textContent = `Answer target: ${expectation}`;
    if (chatLiveNote) {
        chatLiveNote.textContent = meta.interviewer_signal
            ? `Live interviewer cue: ${meta.interviewer_signal}`
            : 'Live panel ready. Expect detailed follow-ups and evidence-based pressure.';
    }
}

function renderSessionMessage(message, noScroll = true) {
    if (!message || !message.role) return;
    if (message.role === 'ai') {
        appendMsg('ai', formatInterviewerTurn({
            question: message.content,
            focus_area: message.focus_area,
            interviewer_signal: message.interviewer_signal,
            pressure_level: message.pressure_level,
            answer_expectation: message.answer_expectation,
        }), null, noScroll, message);
        return;
    }
    if (message.role === 'feedback') {
        appendMsg('feedback', message.content, message.score ?? null, noScroll, message);
        return;
    }
    appendMsg(message.role, message.content, message.score ?? null, noScroll, message);
}

function openChatView(role, diff, meta = {}) {
    emptyState.classList.add('hidden');
    activeDiv.classList.remove('hidden');
    chatMessages.innerHTML = '';
    document.getElementById('chat-role-label').textContent = role;
    document.getElementById('chat-diff-badge').textContent = `Difficulty ${diff}/10`;
    document.getElementById('chat-score-display').textContent = '';
    answerInput.disabled = false;
    submitAnswerBtn.disabled = false;
    answerInput.placeholder = 'Answer in 5-10 lines. Use specifics, tradeoffs, and outcomes.';
    updateInterviewStageMeta({ ...meta, difficulty: diff });
}

function appendMsg(role, content, score = null, noScroll = false, meta = {}) {
    const wrap = document.createElement('div');
    wrap.className = `msg ${role}`;

    const senderMap = {
        ai: '<i class="fa-solid fa-user-tie"></i> Interviewer',
        user: 'You',
        feedback: '<i class="fa-solid fa-square-poll-vertical"></i> Coach Debrief',
    };
    const metaBits = [];
    // Keep interviewer bubble clean like a real interview; no meta chips for AI turns.
    if (role === 'feedback' && meta.focus_area) metaBits.push(`Target ${sanitize(String(meta.focus_area))}`);
    // Emotion indicator for feedback
    let emotion = '';
    if (role === 'feedback' && score !== null) {
        const n = Number(score);
        if (!Number.isNaN(n)) emotion = n >= 8 ? '👏' : n >= 5 ? '🤔' : '⚠️';
    }

    wrap.innerHTML = `
        <span class="msg-sender">${senderMap[role] || role} ${emotion ? `<span class="msg-emotion">${emotion}</span>` : ''}</span>
        <div class="msg-bubble">${sanitize(content)}</div>
        ${metaBits.length ? `<div class="msg-meta-row">${metaBits.map(item => `<span class="msg-meta-pill">${item}</span>`).join('')}</div>` : ''}
        ${score !== null && role === 'feedback' ? `<span class="msg-score-pill"><i class="fa-solid fa-star"></i> ${score}/10</span>` : ''}`;

    chatMessages.appendChild(wrap);
    if (!noScroll) chatMessages.scrollTop = chatMessages.scrollHeight;
    if (role === 'ai') {
        latestInterviewerTurnText = String(content || '').trim();
    }
    return wrap;
}

async function loadSessionHistory(sessionDbId, role, difficulty, sidebarEl) {
    try {
        requestInterviewFullscreen();
        const res = await fetch(`/api/interview/sessions/${sessionDbId}`, { headers: getAuthHeaders() });
        if (!res.ok) return;
        const data = await readResponseData(res);

        interviewSessionId = data.session_token || null;
        scores = data.messages
            .filter(message => message.role === 'feedback' && message.score !== undefined)
            .map(message => Number(message.score));

        const lastAi = [...(data.messages || [])].reverse().find(message => message.role === 'ai') || {};
        openChatView(role, difficulty, {
            interviewer_persona: data.interviewer_persona,
            focus_area: lastAi.focus_area || data.personalization_context?.current_focus_area,
            pressure_level: lastAi.pressure_level,
            answer_expectation: lastAi.answer_expectation,
            session_turn: (data.messages || []).filter(message => message.role === 'user').length,
        });
        chatMessages.innerHTML = '';

        (data.messages || []).forEach(message => renderSessionMessage(message, true));
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

function renderJobsFeedSummary(feedMeta = {}) {
    const summary = feedMeta.summary || {};
    const roleMix = Array.isArray(summary.role_mix) ? summary.role_mix : Array.isArray(feedMeta.suggested_roles) ? feedMeta.suggested_roles : [];

    if (jobsFeedHeadline) jobsFeedHeadline.textContent = summary.headline || 'Your best matches are ready.';
    if (jobsFeedNote) jobsFeedNote.textContent = summary.note || 'Each card explains fit, gaps, and next steps.';
    if (jobsRoleMix) {
        jobsRoleMix.innerHTML = roleMix.length
            ? roleMix.slice(0, 4).map(role => `<span class="jobs-role-chip">${sanitize(role)}</span>`).join('')
            : '<span class="jobs-role-chip">Waiting</span>';
    }
    if (jobsGapFocus) jobsGapFocus.textContent = summary.top_gap || '--';
    if (jobsGapNote) jobsGapNote.textContent = summary.top_gap_note || 'Your main gap will show here.';
    if (jobsBestMatch) jobsBestMatch.textContent = summary.best_match || '--';
    if (jobsBestMatchNote) jobsBestMatchNote.textContent = summary.best_match_note || 'Your strongest match will show here.';
}

function renderJobs(jobs, feedMeta = {}) {
    renderJobsFeedSummary(feedMeta);
    latestJobsFeed = Array.isArray(jobs) ? jobs : [];
    jobsContainer.innerHTML = '';
    if (!jobs.length) {
        jobsContainer.innerHTML = '<p class="empty-state">No strong matches found yet. Try again after updating your resume.</p>';
        return;
    }

    jobsContainer.innerHTML = latestJobsFeed.map((job, index) => {
        const title = sanitize(job.role || job.title || 'Unknown Role');
        const company = sanitize(job.company || 'Unknown Company');
        const location = sanitize(job.location || 'Location unavailable');
        const score = Number(job.match_score) || 0;
        const why = sanitize(job.why_match || job.reason || 'This role aligns with your current resume strengths.');
        const gap = sanitize(job.gap_summary || 'No major gap flagged.');
        const improve = sanitize(job.improvement_plan || job.action_plan || 'Keep strengthening your strongest proof points.');
        const link = job.link || job.url || '#';
        const fitBucket = sanitize(String(job.fit_bucket || 'close').replace(/\b\w/g, char => char.toUpperCase()));
        const sourceRole = sanitize(job.source_role || '');
        const matchedSkills = Array.isArray(job.matched_skills) ? job.matched_skills.slice(0, 5) : [];
        const missingSkills = Array.isArray(job.missing_skills) ? job.missing_skills.slice(0, 5) : [];

        return `
            <article class="crm-job-card premium-job-card">
                <div class="job-card-top">
                    <div>
                        <span class="job-fit-bucket">${fitBucket} fit</span>
                        <h3>${title}</h3>
                        <p><i class="fa-solid fa-building"></i> ${company} <span class="job-location-sep">•</span> ${location}</p>
                    </div>
                    <div class="job-match-cluster">
                        <span class="deep-match-badge">Match ${score}%</span>
                        ${sourceRole ? `<span class="job-role-source">Track: ${sourceRole}</span>` : ''}
                    </div>
                </div>
                <div class="job-reason-grid">
                    <div class="job-reason-card">
                        <span class="job-reason-label">Why it fits</span>
                        <p>${why}</p>
                    </div>
                    <div class="job-reason-card">
                        <span class="job-reason-label">Main gap</span>
                        <p>${gap}</p>
                    </div>
                    <div class="job-reason-card">
                        <span class="job-reason-label">How to improve</span>
                        <p>${improve}</p>
                    </div>
                </div>
                <div class="job-chip-group">
                    <span class="job-chip-label">Matched</span>
                    <div class="job-chip-row">
                        ${matchedSkills.length ? matchedSkills.map(skill => `<span class="job-skill-chip matched">${sanitize(skill)}</span>`).join('') : '<span class="job-skill-chip matched">Potential fit</span>'}
                    </div>
                </div>
                <div class="job-chip-group">
                    <span class="job-chip-label">Missing / under-proven</span>
                    <div class="job-chip-row">
                        ${missingSkills.length ? missingSkills.map(skill => `<span class="job-skill-chip missing">${sanitize(skill)}</span>`).join('') : '<span class="job-skill-chip missing">No major gap flagged</span>'}
                    </div>
                </div>
                <div class="card-footer-row job-card-actions">
                    <button class="btn-outline track-btn" data-job-index="${index}">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Save Job &amp; Tailor Resume
                    </button>
                    <a href="${sanitize(link)}" target="_blank" rel="noopener" class="view-link">View Job <i class="fa-solid fa-arrow-right"></i></a>
                </div>
            </article>
        `;
    }).join('');

    jobsContainer.onclick = event => {
        const btn = event.target.closest('.track-btn');
        if (!btn) return;
        const idx = Number(btn.dataset.jobIndex);
        if (!Number.isInteger(idx) || idx < 0 || idx >= latestJobsFeed.length) return;
        const source = latestJobsFeed[idx] || {};
        const company = source.company || 'Unknown Company';
        const title = source.role || source.title || 'Unknown Role';
        const url = source.link || source.url || '#';
        trackJob(company, title, url);
    };
}

async function loadDailyFeed() {
    switchPage('page-loading');
    const loadingText = document.getElementById('loading-text');
    const steps = [
        'Reading your resume...',
        'Finding the best role matches...',
        'Fetching live openings...',
        'Explaining fit, gaps, and next steps...',
        'Finalizing your job matches...'
    ];
    let stepIdx = 0;
    loadingText.innerText = steps[0];
    const stepTimer = setInterval(() => {
        stepIdx = Math.min(stepIdx + 1, steps.length - 1);
        loadingText.innerText = steps[stepIdx];
    }, 6500);

    try {
        const res = await fetch('/api/jobs/feed', { headers: getAuthHeaders() });
        const data = await readResponseData(res);
        clearInterval(stepTimer);
        if (!res.ok) throw new Error(getErrorMessage(data, 'Feed error'));
        renderJobs(data.jobs || [], data);
        switchPage('page-results');
        loadCoachDashboard(false);
        loadTracker();
        return true;
    } catch (err) {
        clearInterval(stepTimer);
        renderJobs([], {});
        switchPage('page-results');
        showToast('Job feed unavailable right now: ' + err.message, 'error');
        return false;
    }
}

function renderResumePreview() {
    if (!resumeDraftPreview) return;

    const showingBefore = resumeCompareView === 'before';
    const previewText = showingBefore
        ? (resumeLabState.original_resume || resumeLabState.current_resume || '')
        : (resumeLabState.current_resume || resumeLabState.original_resume || '');
    const hasParsedResume = resumeLabState.parsed_resume && Object.keys(resumeLabState.parsed_resume).length > 0;
    const parsedResume = showingBefore
        ? parseResumeTextForPreview(previewText)
        : (hasParsedResume ? normalizeParsedResume(resumeLabState.parsed_resume, previewText) : parseResumeTextForPreview(previewText));
    const appliedSet = new Set((resumeLabState.applied_fixes || []).map(fix => repairResumeDisplayText(fix.improved || '')));
    const recentHighlightSet = new Set((resumeLabState.ui?.recentHighlightLines || []).map(line => repairResumeDisplayText(String(line || '')).trim()));
    const sections = [
        ['Summary', parsedResume.summary ? [parsedResume.summary] : []],
        ['Experience', parsedResume.experience || []],
        ['Projects', parsedResume.projects || []],
        ['Skills', parsedResume.skills || []],
    ];

    const sectionMarkup = sections
        .filter(([, items]) => Array.isArray(items) && items.length)
        .map(([label, items]) => {
            if (label === 'Summary') {
                const itemText = repairResumeDisplayText(String(items[0] || ''));
                const isApplied = !showingBefore && appliedSet.has(itemText);
                const isFresh = !showingBefore && recentHighlightSet.has(itemText.trim());
                return `
                    <section class="resume-paper-section">
                        <h4>${sanitize(label)}</h4>
                        <p>${isApplied ? `<span class="updated-line ${isFresh ? 'fresh-highlight' : ''}">${sanitize(itemText)}</span>` : sanitize(itemText)}</p>
                    </section>
                `;
            }

            const isSkills = label === 'Skills';
            const maxItems = isSkills ? 24 : items.length;
            const trimmedItems = items.slice(0, maxItems);
            const overflowCount = Math.max(0, items.length - trimmedItems.length);

            return `
                <section class="resume-paper-section ${isSkills ? 'is-skills' : ''}">
                    <h4>${sanitize(label)}</h4>
                    <ul>
                        ${trimmedItems.map(item => {
                            const itemText = repairResumeDisplayText(String(item || ''));
                            const isApplied = !showingBefore && appliedSet.has(itemText);
                            const isFresh = !showingBefore && recentHighlightSet.has(itemText.trim());
                            return `<li>${isApplied ? `<span class="updated-line ${isFresh ? 'fresh-highlight' : ''}">${sanitize(itemText)}</span>` : sanitize(itemText)}</li>`;
                        }).join('')}
                        ${overflowCount ? `<li class="resume-more">+${overflowCount} more</li>` : ''}
                    </ul>
                </section>
            `;
        }).join('');

    if (resumeCompareToggle) {
        resumeCompareToggle.querySelectorAll('[data-compare-view]').forEach(button => {
            button.classList.toggle('active', button.dataset.compareView === resumeCompareView);
        });
    }

    resumeDraftPreview.innerHTML = `
        <article class="resume-paper ${showingBefore ? 'is-before' : 'is-after'}">
            <div class="resume-paper-head">
                <div>
                    <span class="resume-paper-label">${showingBefore ? 'Original Draft' : 'Improved Draft'}</span>
                    <strong>${showingBefore ? 'Before changes' : 'Readable recruiter view'}</strong>
                </div>
                <span class="resume-paper-status">${showingBefore ? 'Reference copy' : `${getAppliedIssueIds().size} fixes applied`}</span>
            </div>
            ${sectionMarkup || '<p class="empty-state">Your live resume preview will appear here.</p>'}
        </article>
    `;
}

async function startCoachInterview(overrides = {}) {
    if (!authToken) return;
    const role = overrides.role || coachTargetRole?.value?.trim() || resumeTargetRole?.value?.trim() || document.getElementById('interview-role')?.value?.trim() || 'Software Engineer';
    const difficulty = Number(overrides.difficulty || parseInt(diffSlider?.value, 10) || 5);
    const payload = {
        role,
        difficulty,
        training_mode: overrides.training_mode || coachTrainingMode?.value || 'adaptive',
        interviewer_persona: overrides.interviewer_persona || coachPersona?.value || interviewPersonaSelect?.value || 'strict',
        domain_focus: overrides.domain_focus ?? (coachDomainFocus?.value?.trim() || ''),
    };

    setButtonLoading(coachStartInterviewBtn, true, 'Starting...');
    let optimisticBubble = null;
    try {
        document.querySelector('[data-pane="pane-interview"]')?.click();
        requestInterviewFullscreen();
        openChatView(payload.role, payload.difficulty, payload);
        optimisticBubble = appendMsg(
            'ai',
            [
                'Building your live interview panel...',
                `Mode: ${payload.training_mode.replace(/_/g, ' ')}`,
                `Persona: ${payload.interviewer_persona.replace(/_/g, ' ')}`,
                'Pulling in resume evidence, weak areas, and coach memory before the first question.'
            ].join('\n\n'),
            null,
            false,
            payload,
        );
        const data = await apiJSON('/api/interview/start-from-resume', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        optimisticBubble?.remove();
        interviewSessionId = data.session_id;
        scores = [];
        if (document.getElementById('interview-role')) document.getElementById('interview-role').value = data.role || role;
        if (diffSlider) {
            diffSlider.value = String(data.difficulty || difficulty);
            diffLabel.textContent = String(data.difficulty || difficulty);
        }
        if (interviewPersonaSelect) interviewPersonaSelect.value = data.interviewer_persona || payload.interviewer_persona;
        openChatView(data.role || role, data.difficulty || difficulty, data);
        if (data.session_intro) {
            appendMsg('ai', data.session_intro, null, false, data);
            await wait(160);
        }
        appendMsg('ai', formatInterviewerTurn(data), null, false, data);
        recordDailyProgress(5, 'Started personalized interview');
        showToast('Personalized interview started from your Resume Lab.', 'success');
        loadSessionsList();
        await loadCoachDashboard(true);
    } catch (err) {
        optimisticBubble?.remove();
        appendMsg('feedback', 'The personalized interview did not start this time. Try again in a moment and we will rebuild the session.');
        showToast(err.message || 'Could not start personalized interview.', 'error');
    } finally {
        setButtonLoading(coachStartInterviewBtn, false);
    }
}

if (chatFullscreenBtn) {
    chatFullscreenBtn.addEventListener('click', requestInterviewFullscreen);
}

document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement && document.querySelector('.pane.active')?.id !== 'pane-interview') {
        document.body.classList.remove('interview-live');
    }
});

function isTypingTarget(target) {
    if (!target) return false;
    const tagName = String(target.tagName || '').toUpperCase();
    return tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT' || !!target.isContentEditable;
}

document.addEventListener('keydown', event => {
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
    if (isTypingTarget(event.target)) return;

    const key = String(event.key || '').toLowerCase();
    if (key === 'f') {
        event.preventDefault();
        const activePaneId = document.querySelector('.pane.active')?.id;
        document.querySelector('[data-pane="pane-resume"]')?.click();
        loadResumeLab(false);
        if (activePaneId === 'pane-resume' && resumeLabState?.has_resume) {
            toggleFixMode();
        }
        return;
    }
    if (key === 'r') {
        event.preventDefault();
        document.querySelector('[data-pane="pane-resume"]')?.click();
        scheduleResumeRescore();
        return;
    }
    if (key === 'i') {
        event.preventDefault();
        startCoachInterview();
    }
});

// Load sessions list whenever interview tab is clicked
document.querySelector('[data-pane="pane-interview"]')?.addEventListener('click', loadSessionsList, { once: false });

if (coachProgressToggle) {
    coachProgressToggle.addEventListener('click', () => {
        appUIState.panels.progress = !appUIState.panels.progress;
        updateCoachDisclosureUI();
    });
}

if (coachAdvancedToggle) {
    coachAdvancedToggle.addEventListener('click', () => {
        appUIState.panels.advanced = !appUIState.panels.advanced;
        updateCoachDisclosureUI();
    });
}

updateCoachDisclosureUI();
setCurrentView('dashboard');

if (resumeHealthBreakdown) {
    resumeHealthBreakdown.addEventListener('click', event => {
        const row = event.target.closest('[data-health-area]');
        if (!row) return;
        const area = row.dataset.healthArea;
        if (!area) return;
        openResumeLabAndFocusCategory(area);
    });
}



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
            viewport.style.display = (paneId === 'pane-interview') ? 'none' : 'block';
        }
        document.body.classList.toggle('interview-live', paneId === 'pane-interview');
        setCurrentView(
            paneId === 'pane-resume'
                ? 'resume'
                : paneId === 'pane-interview'
                    ? 'interview'
                    : 'dashboard'
        );

        if (paneId === 'pane-resume') {
            loadResumeLab(false);
        }
        if (paneId === 'pane-coach') {
            loadCoachDashboard(false);
        }
    });
});

// ─── Security: XSS sanitizer ─────────────────────────────────────────────────
function sanitize(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
