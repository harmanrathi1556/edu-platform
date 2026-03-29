const BACKEND_URL = "https://edu-platform-sqty.onrender.com";
const TOKEN = localStorage.getItem("token");

// --- FEATURE #19: FETCH ANALYTICS ---
async function loadDashboardData() {
    try {
        const res = await fetch(`${BACKEND_URL}/admin/stats`, {
            headers: { "Authorization": `Bearer ${TOKEN}` }
        });
        const data = await res.json();
        
        // Update Stats Safely
        const fields = {
            'totalUsers': data.total_users || 0,
            'totalRevenue': `₹${data.total_revenue || 0}`,
            'userXP': `${(data.total_users || 1) * 120} XP`,
            'userNameDisplay': localStorage.getItem("userName") || "Harman Rathi",
            'userRoleDisplay': localStorage.getItem("userRole") || "Super Admin"
        };

        for (const [id, value] of Object.entries(fields)) {
            const el = document.getElementById(id);
            if (el) el.innerText = value;
        }
    } catch(e) {
        console.warn("Backend still waking up... retrying in 5s");
        setTimeout(loadDashboardData, 5000);
    }
}

// --- FEATURE #14: UPGRADED AI SOLVER ---
async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    
    if(!question) return alert("Please type your doubt or attach an image!");
    
    responseBox.classList.remove('hidden');
    responseBox.innerHTML = `<div class="flex items-center gap-3">
        <div class="w-4 h-4 bg-blue-500 rounded-full animate-ping"></div>
        <span class="font-bold">AI Brain is processing your request...</span>
    </div>`;

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "Authorization": `Bearer ${TOKEN}` 
            },
            body: JSON.stringify({ 
                question: question,
                image_url: null // Logic ready for future expansion
            })
        });
        const data = await res.json();
        responseBox.innerHTML = `<p class="text-xs font-black text-blue-400 uppercase mb-2">Solution Found</p>
                                 <p class="text-lg">${data.answer}</p>`;
    } catch(e) {
        responseBox.innerText = "Error: AI Brain Connection Lost. Please try again.";
    }
}

// --- FEATURE #7: QR MODAL CONTROLS ---
function showPayment() { 
    document.getElementById('paymentModal').classList.remove('hidden'); 
}
function hidePayment() { 
    document.getElementById('paymentModal').classList.add('hidden'); 
}

async function submitPayment() {
    const amount = document.getElementById('payAmount').value;
    const screenshot = document.getElementById('qrUrl').value;
    const batch = document.getElementById('selectedBatch').value;

    if(!amount || !screenshot) return alert("Please provide amount and screenshot link!");

    try {
        const res = await fetch(`${BACKEND_URL}/payment/submit`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "Authorization": `Bearer ${TOKEN}` 
            },
            body: JSON.stringify({ amount, screenshot_url: screenshot, batch_id: batch })
        });
        alert("Success! Your payment is being verified by Admin.");
        hidePayment();
    } catch(e) {
        alert("Payment submission failed. Check Render status.");
    }
}

// Run on startup
window.onload = loadDashboardData;
