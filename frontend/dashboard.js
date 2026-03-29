// --- CONFIGURATION ---
const BACKEND_URL = "https://edu-platform-sqty.onrender.com";
const USER_TOKEN = localStorage.getItem("token"); // We'll save this during login

// --- FEATURE #5 & #19: AUTO-LOAD PROFILE & STATS ---
async function loadDashboardData() {
    try {
        const response = await fetch(`${BACKEND_URL}/admin/stats`, {
            headers: { "Authorization": `Bearer ${USER_TOKEN}` }
        });
        const stats = await response.json();
        
        // Update UI Elements (IDs must match dashboard.html)
        if(document.getElementById('totalRevenue')) {
            document.getElementById('totalRevenue').innerText = `₹${stats.total_revenue}`;
            document.getElementById('totalUsers').innerText = stats.total_users;
        }
    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}

// --- FEATURE #14: AI DOUBT SOLVER (INSTANT ANSWERS) ---
async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    
    if(!question) return alert("Please type a question!");
    
    responseBox.innerText = "AI is thinking...";
    responseBox.classList.remove('hidden');

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${USER_TOKEN}`
            },
            body: JSON.stringify({ question: question })
        });
        const data = await res.json();
        responseBox.innerText = data.answer;
    } catch (err) {
        responseBox.innerText = "AI is currently offline. Try again later.";
    }
}

// --- FEATURE #7: QR PAYMENT UPLOAD LOGIC ---
async function submitPayment() {
    const amount = document.getElementById('payAmount').value;
    const screenshotUrl = document.getElementById('qrUrl').value; // URL of uploaded image
    const batchId = document.getElementById('selectedBatch').value;

    const res = await fetch(`${BACKEND_URL}/payment/submit`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${USER_TOKEN}`
        },
        body: JSON.stringify({ 
            amount: amount, 
            screenshot_url: screenshotUrl, 
            batch_id: batchId 
        })
    });
    
    const data = await res.json();
    alert(data.message);
}

// Initialize on load
window.onload = loadDashboardData;
