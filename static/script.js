document.addEventListener("DOMContentLoaded", () => {

    /* ── Page refs ──────────────────────────────────────── */
    const pageHome     = document.getElementById("page-home");
    const pagePrefs    = document.getElementById("page-prefs");
    const pageLoading  = document.getElementById("page-loading");
    const pageResults  = document.getElementById("page-results");

    /* ── Home refs ──────────────────────────────────────── */
    const dropZone    = document.getElementById("drop-zone");
    const fileInput   = document.getElementById("file-input");
    const fileInfo    = document.getElementById("file-info");
    const fileNameEl  = document.getElementById("file-name");
    const analyzeBtn  = document.getElementById("analyze-btn");
    const resetBtn    = document.getElementById("reset-btn");

    /* ── Loading refs ───────────────────────────────────── */
    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const steps = [step1, step2, step3];

    /* ── Results refs ───────────────────────────────────── */
    const sumRing      = document.getElementById("sum-ring");
    const sumPct       = document.getElementById("sum-pct");
    const summaryVerd  = document.getElementById("summary-verdict");
    const sRoles       = document.getElementById("s-roles");
    const sJobs        = document.getElementById("s-jobs");
    const rolesContainer = document.getElementById("roles-container");
    const jobsContainer  = document.getElementById("jobs-container");
    const improvList     = document.getElementById("improvements-list");
    const questionsContainer = document.getElementById("questions-container");

    /* ── Interactive Interview refs ─────────────────────── */
    const startInteractiveBtn  = document.getElementById("start-interactive-btn");
    const interviewChat        = document.getElementById("interview-chat");
    const interviewChatLog     = document.getElementById("interview-chat-log");
    const interviewAnswerForm  = document.getElementById("interview-answer-form");
    const interviewAnswerInput = document.getElementById("interview-answer-input");
    const interviewSubmitBtn   = document.getElementById("interview-submit-btn");

    /* ── State ──────────────────────────────────────────── */
    let selectedFile = null;
    let phaseTimers  = [];
    let currentSessionId = null;

    /* ─────────────────────────────────────────────────────
       HELPERS: show/hide pages
    ───────────────────────────────────────────────────── */
    function showPage(page) {
        [pageHome, pagePrefs, pageLoading, pageResults].forEach(p => {
            p.classList.add("hidden");
            p.classList.remove("active");
        });
        page.classList.remove("hidden");
        page.classList.add("active");
        window.scrollTo(0, 0);
    }

    /* ─────────────────────────────────────────────────────
       DRAG & DROP
    ───────────────────────────────────────────────────── */
    dropZone.addEventListener("dragover", e => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));

    dropZone.addEventListener("drop", e => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });

    dropZone.addEventListener("click", e => {
        if (e.target.closest(".btn-outline")) return; // handled by onclick
        fileInput.click();
    });

    fileInput.addEventListener("change", e => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (file.type !== "application/pdf") {
            alert("Please upload a PDF file.");
            return;
        }
        selectedFile = file;
        fileNameEl.textContent = file.name;
        fileInfo.classList.remove("hidden");
        analyzeBtn.disabled = false;
    }

    /* ─────────────────────────────────────────────────────
       PHASE STEPPER
    ───────────────────────────────────────────────────── */
    // These timings match the approximate real backend phases:
    // Phase 1 fires immediately, Phase 2 after ~12s, Phase 3 after ~28s
    const PHASE_DELAYS = [0, 12000, 28000];

    function startSteps() {
        steps.forEach(s => s.classList.remove("active", "done"));
        phaseTimers.forEach(clearTimeout);
        phaseTimers = [];

        PHASE_DELAYS.forEach((delay, i) => {
            const t = setTimeout(() => {
                if (i > 0) {
                    steps[i - 1].classList.remove("active");
                    steps[i - 1].classList.add("done");
                }
                steps[i].classList.add("active");
            }, delay);
            phaseTimers.push(t);
        });
    }

    function finishSteps() {
        phaseTimers.forEach(clearTimeout);
        phaseTimers = [];
        steps.forEach(s => { s.classList.remove("active"); s.classList.add("done"); });
    }

    /* ─────────────────────────────────────────────────────
       TABS
    ───────────────────────────────────────────────────── */
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".pane").forEach(p => p.classList.replace("active", "hidden") || p.classList.add("hidden"));
            tab.classList.add("active");
            const pane = document.getElementById(tab.dataset.pane);
            pane.classList.remove("hidden");
            pane.classList.add("active");
        });
    });

    /* ─────────────────────────────────────────────────────
       ANALYZE
    ───────────────────────────────────────────────────── */
    analyzeBtn.addEventListener("click", () => {
        if (!selectedFile) return;
        showPage(pagePrefs);
    });

    const prefsForm = document.getElementById("prefs-form");
    prefsForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        showPage(pageLoading);
        startSteps();

        const form = new FormData();
        form.append("file", selectedFile);
        form.append("location", document.getElementById("pref-location").value);
        form.append("experience", document.getElementById("pref-exp").value);
        form.append("work_mode", document.getElementById("pref-mode").value);
        form.append("job_type", document.getElementById("pref-type").value);

        try {
            const res  = await fetch("/api/analyze", { method: "POST", body: form });
            const data = await res.json();
            finishSteps();

            if (!res.ok) throw new Error(data.error || "Server error");

            render(data);
            showPage(pageResults);

        } catch (err) {
            finishSteps();
            alert("Error: " + err.message);
            showPage(pageHome);
        }
    });

    /* ─────────────────────────────────────────────────────
       RESET
    ───────────────────────────────────────────────────── */
    resetBtn.addEventListener("click", () => {
        selectedFile = null;
        fileInfo.classList.add("hidden");
        fileInput.value = "";
        analyzeBtn.disabled = true;
        // reset first tab
        document.querySelectorAll(".tab")[0].click();
        
        // reset interactive state
        currentSessionId = null;
        interviewChat.classList.add("hidden");
        startInteractiveBtn.classList.remove("hidden");
        startInteractiveBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Interactive Mock Interview';
        startInteractiveBtn.disabled = false;
        interviewChatLog.innerHTML = "";
        
        showPage(pageHome);
    });

    /* ─────────────────────────────────────────────────────
       INTERACTIVE INTERVIEW
    ───────────────────────────────────────────────────── */
    
    function appendChatMessage(sender, text, type) {
        const msg = document.createElement("div");
        msg.style.padding = "1rem";
        msg.style.borderRadius = "12px";
        msg.style.marginTop = "0.5rem";
        
        if (type === "user") {
            msg.style.background = "var(--purple)";
            msg.style.color = "#fff";
            msg.style.marginLeft = "2rem";
        } else if (type === "coach-eval") {
            msg.style.background = "rgba(167, 139, 250, 0.1)";
            msg.style.border = "1px solid rgba(167, 139, 250, 0.3)";
            msg.style.color = "var(--text)";
        } else {
            msg.style.background = "var(--bg)";
            msg.style.border = "1px solid var(--border)";
            msg.style.color = "var(--text)";
            msg.style.marginRight = "2rem";
        }
        
        msg.innerHTML = `<strong>${sender}</strong> <div style="margin-top:0.4rem; line-height:1.5;">${text}</div>`;
        interviewChatLog.appendChild(msg);
        interviewChatLog.scrollTop = interviewChatLog.scrollHeight;
    }

    startInteractiveBtn.addEventListener("click", async () => {
        const roleEls = document.querySelectorAll(".role-tag");
        const topRole = roleEls.length > 0 ? roleEls[0].textContent : "Software Engineer";

        startInteractiveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Initializing Coach...';
        startInteractiveBtn.disabled = true;

        try {
            const res = await fetch("/interview/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role: topRole, difficulty: 5 })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Failed to start interview");

            currentSessionId = data.session_id;
            
            interviewChatLog.innerHTML = "";
            appendChatMessage("Coach", data.question, "coach");

            startInteractiveBtn.classList.add("hidden");
            interviewChat.classList.remove("hidden");
        } catch (e) {
            alert("Error: " + e.message);
            startInteractiveBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Interactive Mock Interview';
            startInteractiveBtn.disabled = false;
        }
    });

    interviewAnswerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!currentSessionId) return;

        const answer = interviewAnswerInput.value.trim();
        if (!answer) return;

        appendChatMessage("You", answer, "user");
        interviewAnswerInput.value = "";
        interviewSubmitBtn.disabled = true;
        interviewSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const res = await fetch("/interview/answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: currentSessionId, answer: answer })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Failed to process answer");

            const ev = data.evaluation;
            const evalHtml = `
                <div style="margin-bottom:0.8rem;"><strong style="color:var(--amber);">Evaluation Score: ${ev.score}/10</strong></div>
                <div style="display:flex; gap: 1rem; margin-bottom:0.4rem; font-size:0.9rem;">
                   <span><strong>Technical:</strong> ${ev.technical_depth || '-'}/10</span>
                   <span><strong>Communication:</strong> ${ev.communication || '-'}/10</span>
                </div>
                <div style="margin-bottom:0.4rem;"><strong>Missing Concepts:</strong> ${ev.missing_concepts?.join(", ") || 'None'}</div>
                <div><strong>Actionable Feedback:</strong> ${ev.improvement || ev.improvements || ''}</div>
            `;

            appendChatMessage("Coach (Evaluation)", evalHtml, "coach-eval");
            appendChatMessage("Coach", data.next_question, "coach");

        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            interviewSubmitBtn.disabled = false;
            interviewSubmitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
        }
    });

    /* ─────────────────────────────────────────────────────
       SCORE HELPERS
    ───────────────────────────────────────────────────── */
    function tier(pct) {
        if (pct >= 70) return "high";
        if (pct >= 40) return "medium";
        return "low";
    }

    function verdict(avg, goodFits) {
        if (avg >= 70) return `Strong match — ${goodFits} role${goodFits !== 1 ? "s" : ""} are excellent fits`;
        if (avg >= 50) return `Good profile — close to ${goodFits} strong fit${goodFits !== 1 ? "s" : ""}`;
        if (avg >= 30) return `Growing — focus on filling the skill gaps`;
        return "Early stage — build more projects to improve matches";
    }

    function animateRing(circ, pct) {
        const offset = circ - (pct / 100) * circ;
        const color  = pct >= 70 ? "var(--green)" : pct >= 40 ? "var(--amber)" : "var(--red)";
        sumRing.style.stroke = color;
        requestAnimationFrame(() => requestAnimationFrame(() => {
            sumRing.style.strokeDashoffset = offset;
        }));
    }

    /* ─────────────────────────────────────────────────────
       RENDER RESULTS
    ───────────────────────────────────────────────────── */
    function render(data) {
        const jobs   = data.jobs   || [];
        const roles  = data.roles  || [];
        const improv = data.improvements || [];
        const qs     = data.questions    || [];

        /* ── Summary strip ─── */
        const scores  = jobs.map(j => j.match_score || 0);
        const avg     = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
        const goodFit = scores.filter(s => s >= 60).length;
        const circ    = Math.PI * 2 * 16;   // r=16 → circumference ≈ 100.5

        sumPct.textContent        = avg + "%";
        sumRing.style.stroke      = tier(avg) === "high" ? "var(--green)" : tier(avg) === "medium" ? "var(--amber)" : "var(--red)";
        summaryVerd.textContent   = verdict(avg, goodFit);
        sRoles.innerHTML          = `<i class="fa-solid fa-bullseye"></i> ${roles.length} roles`;
        sJobs.innerHTML           = `<i class="fa-solid fa-briefcase"></i> ${jobs.length} matches`;
        animateRing(circ, avg);

        /* ── Roles ─── */
        rolesContainer.innerHTML = "";
        roles.forEach((r, i) => {
            const span = document.createElement("span");
            span.className = "role-tag";
            span.textContent = r;
            span.style.animationDelay = `${i * 60}ms`;
            rolesContainer.appendChild(span);
        });

        /* ── Job cards ─── */
        jobsContainer.innerHTML = "";
        if (!jobs.length) {
            jobsContainer.innerHTML = `<p style="color:var(--muted);padding:.5rem 0">No jobs found. Try a different resume.</p>`;
        } else {
            jobs.forEach((job, i) => {
                const pct  = job.match_score || 0;
                const t    = tier(pct);
                const pri  = (() => {
                    const p = (job.priority || "").toLowerCase();
                    if (p.includes("high") || p.includes("🔥")) return "high";
                    if (p.includes("good") || p.includes("apply") || p.includes("prepare") || p.includes("med") || p.includes("⚡") || p.includes("🧠")) return "medium";
                    return "low";
                })();
                const priLabel = pri === "high" ? "High priority" : pri === "medium" ? "Medium priority" : "Low priority";

                const matchedHtml = (job.matched_skills || []).map(s => `<span class="sk ok">${s}</span>`).join("");
                const missingHtml = (job.missing_skills || []).map(s => `<span class="sk gap">${s}</span>`).join("");
                const barId = `bar-${i}`;

                const card = document.createElement("div");
                card.className = "job-card";
                card.style.animationDelay = `${i * 80}ms`;

                card.innerHTML = `
                    <div class="jc-top">
                        <div class="jc-left">
                            <div class="jc-role">${job.role}</div>
                            <div class="jc-company">
                                <i class="fa-regular fa-building"></i>
                                ${job.company}
                            </div>
                        </div>
                        <span class="jc-priority ${pri}">${priLabel}</span>
                    </div>

                    <div class="jc-score">
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill ${t}" id="${barId}" style="width:0%"></div>
                        </div>
                        <span class="score-val ${t}">${pct}% match</span>
                    </div>

                    <p class="jc-desc">${job.reason || job.description || ""}</p>

                    ${matchedHtml ? `<div class="jc-skills">${matchedHtml}</div>` : ""}
                    ${missingHtml ? `<div class="jc-skills">${missingHtml}</div>` : ""}

                    ${job.action_plan ? `<div class="jc-action">${job.action_plan}</div>` : ""}

                    <div class="jc-footer">
                        <a href="${job.link}" target="_blank" rel="noopener" class="btn-apply">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Apply Now
                        </a>
                    </div>
                `;

                jobsContainer.appendChild(card);

                // Animate progress bar
                setTimeout(() => {
                    const bar = document.getElementById(barId);
                    if (bar) bar.style.width = pct + "%";
                }, 200 + i * 80);
            });
        }

        /* ── Resume tips ─── */
        improvList.innerHTML = "";
        if (!improv.length) {
            improvList.innerHTML = `<li class="tip-item"><span class="tip-icon"><i class="fa-solid fa-circle-check"></i></span> Your resume looks solid — no major improvements flagged!</li>`;
        } else {
            improv.forEach((tip, i) => {
                const li = document.createElement("li");
                li.className = "tip-item";
                li.style.animationDelay = `${i * 55}ms`;
                li.innerHTML = `<span class="tip-icon"><i class="fa-solid fa-circle-check"></i></span> ${tip}`;
                improvList.appendChild(li);
            });
        }

        /* ── Interview questions ─── */
        questionsContainer.innerHTML = "";
        if (!qs.length) {
            questionsContainer.innerHTML = `<p style="color:var(--muted)">No questions generated.</p>`;
        } else {
            qs.forEach((q, i) => {
                const isTech   = (q.type || "").toLowerCase() === "technical";
                const typeClass = isTech ? "tech" : "behav";
                const icon     = isTech ? "fa-code" : "fa-users";
                const copyId   = `cp-${i}`;

                const card = document.createElement("div");
                card.className = "q-card";
                card.style.animationDelay = `${i * 75}ms`;

                card.innerHTML = `
                    <div class="q-type ${typeClass}">
                        <i class="fa-solid ${icon}"></i> ${q.type || "General"}
                    </div>
                    <div class="q-text">${q.question}</div>
                    <div class="q-tip"><strong>Tip:</strong> ${q.tip || ""}</div>
                    <button class="copy-btn" id="${copyId}">
                        <i class="fa-regular fa-copy"></i> Copy
                    </button>
                `;

                questionsContainer.appendChild(card);

                document.getElementById(copyId).addEventListener("click", function () {
                    navigator.clipboard.writeText(q.question).then(() => {
                        this.innerHTML = `<i class="fa-solid fa-check"></i> Copied`;
                        this.classList.add("ok");
                        setTimeout(() => {
                            this.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
                            this.classList.remove("ok");
                        }, 2000);
                    });
                });
            });
        }
    }

});
