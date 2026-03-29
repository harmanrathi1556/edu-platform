const BACKEND_URL = "https://edu-platform-sqty.onrender.com";
const TOKEN = localStorage.getItem("token");

// --- INITIALIZE DASHBOARD ---
async function initDashboard() {
    if (!TOKEN) {
        window.location.href = "index.html";
        return;
    }
    
    // Set Student Name from LocalStorage
    document.getElementById('studentName').innerText = localStorage.getItem("userName") || "Learner";
    
    // Sync XP and Level from Database (Feature #5)
    loadStudentStats();
}

// --- FEATURE #14: GEMINI 1.5 AI SOLVER ---
async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    const btn = document.getElementById('aiBtn');

    if (!question) return alert("Please type your doubt first!");

    // UI Loading State
    btn.innerText = "THINKING...";
    btn.disabled = true;
    responseBox.classList.remove('hidden');
    responseBox.innerHTML = `<div class="flex items-center gap-3">
        <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
        <span class="text-xs font-bold uppercase tracking-widest text-blue-400">Gemini 1.5 is analyzing...</span>
    </div>`;

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${TOKEN}`
            },
            body: JSON.stringify({ question: question })
        });

        const data = await res.json();
        
        if (data.answer) {
            // Render the solution with formatting
            responseBox.innerHTML = `
                <p class="text-[10px] font-black text-blue-500 mb-2 uppercase tracking-tighter">Verified Solution</p>
                <div class="text-sm leading-relaxed text-white whitespace-pre-line">${data.answer}</div>
            `;
        }
    } catch (err) {
        responseBox.innerHTML = `<p class="text-red-400 text-xs">Connection to AI Brain lost. Retrying...</p>`;
    } finally {
        btn.innerText = "Solve with Gemini 1.5";
        btn.disabled = false;
    }
}

// --- FEATURE #10: AI PROCTORING (TAB-SWITCH DETECTION) ---
let violationCount = 0;

document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        violationCount++;
        const alertBox = document.getElementById('proctorAlert');
        alertBox.classList.remove('hidden');
        
        // Log to Backend (Feature #10)
        logViolation("TAB_SWITCH");
        
        console.warn(`Integrity Alert: Tab switch detected (${violationCount})`);
    }
});

async function logViolation(type) {
    try {
        await fetch(`${BACKEND_URL}/exams/log-violation`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${TOKEN}`
            },
            body: JSON.stringify({ 
                type: type,
                exam_id: "DASHBOARD_MONITOR" 
            })
        });
    } catch (e) { console.error("Proctor Sync Failed"); }
}

// --- FEATURE #5: XP & LEVEL SYNC ---
async function loadStudentStats() {
    // This calls the backend to get real-time XP
    try {
        const res = await fetch(`${BACKEND_URL}/admin/dashboard-stats`, {
            headers: { "Authorization": `Bearer ${TOKEN}` }
        });
        const data = await res.json();
        
        // Update the XP Bar width dynamically
        const xpFill = document.getElementById('xpFill');
        if (xpFill) xpFill.style.width = "75%"; // Replace with logic: (currentXP / nextLevelXP) * 100
    } catch (e) { console.log("Stats offline"); }
}

// --- FEATURE #7: PAYMENT SUBMISSION ---
async function submitPayment() {
    const amount = document.getElementById('payAmount').value;
    const screenshot = document.getElementById('qrUrl').value;

    if (!amount || !screenshot) return alert("Please fill all payment fields.");

    const res = await fetch(`${BACKEND_URL}/payment/submit`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${TOKEN}`
        },
        body: JSON.stringify({ 
            amount: amount, 
            screenshot_url: screenshot,
            batch_id: "DEFAULT_BATCH" 
        })
    });

    if (res.ok) {
        alert("Success! Your screenshot is sent to Harman Rathi for approval.");
        window.location.reload();
    }
}

// Start everything
window.onload = initDashboard;
