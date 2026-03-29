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

async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    const btn = document.getElementById('aiBtn');

    if (!question) return alert("Please type your doubt!");

    // Set Loading State
    btn.innerText = "THINKING...";
    btn.disabled = true;
    responseBox.classList.remove('hidden');
    responseBox.innerHTML = `<p class="text-blue-400 animate-pulse font-bold text-xs uppercase tracking-widest">● Gemini 1.5 is analyzing...</p>`;

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${TOKEN}` // Make sure TOKEN is valid
            },
            body: JSON.stringify({ question: question })
        });

        const data = await res.json();
        
        if (res.ok) {
            // Success: Show the answer
            responseBox.innerHTML = `
                <div class="text-sm text-blue-100 whitespace-pre-line leading-relaxed">${data.answer}</div>
            `;
        } else {
            // Backend Error: Show what went wrong
            responseBox.innerHTML = `<p class="text-red-400 font-bold text-xs">❌ ERROR: ${data.answer || "Server Offline"}</p>`;
        }
    } catch (err) {
        // Network Error (CORS or Render Down)
        responseBox.innerHTML = `<p class="text-red-500 font-bold text-xs">📡 NETWORK ERROR: Check if Render is live.</p>`;
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
